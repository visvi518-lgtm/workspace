"""
백테스터 — 인트라데이(1시간봉) 시뮬레이션 지원
- 2년 이내 기간: 실제 1h 캔들로 시간대별 거래 시뮬레이션
- 2년 초과 기간: 일봉 + 합성 시간 스탬프
- 스캘핑/스윙 자동 분리
- 거래 로그에 날짜+시간 기록
"""
from dataclasses import dataclass, field
from datetime import date, timedelta, datetime
import pandas as pd
import numpy as np
import yfinance as yf
from dateutil.relativedelta import relativedelta

import config
from trader.strategy import TechnicalStrategy

MIN_KR_DATE = date(2000, 1, 1)
MIN_US_DATE = date(1990, 1, 1)
KRX_FOUNDED = date(1956, 3, 3)
NYSE_FOUNDED = date(1792, 5, 17)

# 1h 데이터를 yfinance에서 가져올 수 있는 최대 일수
MAX_HOURLY_DAYS = 720


@dataclass
class TradeRecord:
    date: str
    time: str          # "HH:MM"
    code: str
    name: str
    market: str
    trade_type: str
    price: float
    quantity: int
    amount: float
    fee: float
    profit: float | None
    profit_rate: float | None
    reason: str

    @property
    def datetime_str(self) -> str:
        return f"{self.date} {self.time}"


@dataclass
class BacktestResult:
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    profit: float
    profit_rate: float
    total_trades: int
    buy_trades: int
    sell_trades: int
    win_trades: int
    loss_trades: int
    portfolio_history: list   # [{"date": "YYYY-MM-DD", "value": float}]
    hourly_history: list      # [{"datetime": "YYYY-MM-DD HH:MM", "value": float}]
    trades: list              # list[TradeRecord]
    stock_performances: list
    max_drawdown: float
    used_hourly: bool = False  # 1h 시뮬레이션 여부


def validate_period(start_year, start_month, duration_months, use_kr, use_us):
    today = date.today()
    try:
        start_d = date(start_year, start_month, 1)
    except ValueError:
        return False, "올바른 연도/월을 입력해 주세요."

    if duration_months < 1:
        return False, "기간은 최소 1개월 이상이어야 합니다."

    end_d = start_d + relativedelta(months=duration_months)
    one_month_ago = today - relativedelta(months=1)

    if use_kr and start_d < KRX_FOUNDED:
        return False, (
            f"한국거래소(KRX)는 {KRX_FOUNDED.strftime('%Y년 %m월 %d일')} 개설되었습니다.\n"
            f"그 이전 날짜는 선택할 수 없습니다."
        )
    if use_us and start_d < NYSE_FOUNDED:
        return False, (
            f"뉴욕증권거래소(NYSE)는 {NYSE_FOUNDED.strftime('%Y년 %m월 %d일')} 개설되었습니다.\n"
            f"그 이전 날짜는 선택할 수 없습니다."
        )
    if use_kr and start_d < MIN_KR_DATE:
        return False, f"한국 주식 신뢰 데이터는 {MIN_KR_DATE.strftime('%Y년 %m월')} 이후부터 제공됩니다."
    if use_us and start_d < MIN_US_DATE:
        return False, f"미국 주식 신뢰 데이터는 {MIN_US_DATE.strftime('%Y년 %m월')} 이후부터 제공됩니다."

    if end_d > one_month_ago:
        if start_d > one_month_ago:
            return False, (
                f"시작 날짜({start_d.strftime('%Y년 %m월')})가 현재로부터 1개월 이내입니다.\n"
                f"백테스트 시작일은 {one_month_ago.strftime('%Y년 %m월')} 이전이어야 합니다."
            )
        return False, (
            f"종료일({end_d.strftime('%Y년 %m월')})이 현재 날짜로부터 1개월 이내입니다.\n"
            f"기간을 줄이거나 더 과거 날짜를 선택해 주세요."
        )

    if not use_kr and not use_us:
        return False, "국내 또는 해외 시장 중 하나 이상 선택해 주세요."

    return True, ""


class Backtester:
    def __init__(self, strategy: TechnicalStrategy):
        self.strategy = strategy
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(
        self,
        start_year: int,
        start_month: int,
        duration_months: int,
        initial_capital: float,
        use_kr: bool = True,
        use_us: bool = True,
        exchange_rate: float = 1350,
        stop_loss: float = -0.02,
        take_profit: float = 0.03,
        max_positions: int = 8,
        progress_callback=None,
    ) -> "BacktestResult | None":
        self._cancelled = False

        start_d = date(start_year, start_month, 1)
        end_d   = start_d + relativedelta(months=duration_months)
        fetch_start = start_d - timedelta(days=90)
        fetch_end   = end_d + timedelta(days=2)

        # ── 종목 풀: 동적 스크리너 우선, 실패 시 config fallback ──
        try:
            from crawler.stock_screener import get_pool
            pool = get_pool(
                use_kr=use_kr, use_us=use_us,
                kr_n=40, us_n=40,
            )
            if not pool:
                raise ValueError("empty pool")
            if progress_callback:
                progress_callback(f"종목 선별 완료: {len(pool)}개 (거래량 상위)")
        except Exception:
            pool = []
            if use_kr:
                for s in config.DOMESTIC_STOCK_POOL:
                    pool.append({**s, "market": "KR"})
            if use_us:
                for s in config.US_STOCK_POOL:
                    pool.append({**s, "yf_code": s["code"], "market": "US"})

        # ── 일봉 데이터 다운로드 ──
        daily_data: dict[tuple, tuple] = {}
        for i, stock in enumerate(pool):
            if self._cancelled:
                return None
            yf_code = stock.get("yf_code", stock["code"])
            if progress_callback:
                progress_callback(f"데이터 로드: {stock['name']} ({i+1}/{len(pool)})")
            try:
                df = yf.Ticker(yf_code).history(
                    start=fetch_start.strftime("%Y-%m-%d"),
                    end=fetch_end.strftime("%Y-%m-%d"),
                )
                if df.empty or len(df) < 15:
                    continue
                df = _clean_df(df)
                daily_data[(stock["code"], stock["market"])] = (df, stock["name"])
            except Exception:
                continue

        if not daily_data:
            if progress_callback:
                progress_callback("오류: 데이터를 가져올 수 없습니다.")
            return None

        # ── 1h 데이터 (기간 ≤ 2년) ──
        use_hourly = (end_d - start_d).days <= MAX_HOURLY_DAYS
        hourly_data: dict[tuple, tuple] = {}

        if use_hourly:
            if progress_callback:
                progress_callback("시간봉 데이터 다운로드 중... (실시간 시뮬레이션)")

            # 배치 다운로드 (속도 향상)
            all_yf_codes = [
                (stock.get("yf_code", stock["code"]), stock["code"], stock["market"])
                for stock in pool
                if (stock["code"], stock["market"]) in daily_data
            ]
            tickers_str = [yfc for yfc, _, _ in all_yf_codes]
            try:
                raw_h = yf.download(
                    tickers=tickers_str,
                    start=fetch_start.strftime("%Y-%m-%d"),
                    end=fetch_end.strftime("%Y-%m-%d"),
                    interval="1h",
                    group_by="ticker",
                    auto_adjust=True,
                    progress=False,
                    threads=True,
                )
                for yfc, code, market in all_yf_codes:
                    try:
                        if isinstance(raw_h.columns, pd.MultiIndex):
                            sub = raw_h[yfc].dropna(how="all")
                        else:
                            sub = raw_h.dropna(how="all")
                        if sub.empty:
                            continue
                        hdf = _clean_df(sub, is_hourly=True)
                        if not hdf.empty:
                            name = daily_data[(code, market)][1]
                            hourly_data[(code, market)] = (hdf, name)
                    except Exception:
                        pass
            except Exception:
                pass

            if progress_callback:
                progress_callback(
                    f"시간봉 로드: {len(hourly_data)}/{len(daily_data)}개 종목 완료"
                )

        if progress_callback:
            mode_str = "시간봉(인트라데이)" if use_hourly else "일봉"
            progress_callback(f"시뮬레이션 실행 중... ({len(daily_data)}종목, {mode_str})")

        if use_hourly and hourly_data:
            result = self._simulate_intraday(
                daily_data, hourly_data, start_d, end_d,
                initial_capital, exchange_rate, stop_loss, take_profit, max_positions,
            )
        else:
            result = self._simulate_daily(
                daily_data, start_d, end_d,
                initial_capital, exchange_rate, stop_loss, take_profit, max_positions,
            )

        if result and progress_callback:
            progress_callback("시뮬레이션 완료!")
        return result

    # ── 인트라데이 시뮬레이션 (1h 캔들) ──────────────────────

    def _simulate_intraday(
        self, daily_data, hourly_data, start_d, end_d,
        initial_capital, exchange_rate, stop_loss, take_profit, max_positions,
    ) -> BacktestResult:
        cash = initial_capital
        positions: dict = {}
        all_trades: list[TradeRecord] = []
        hourly_history: list[dict] = []
        daily_history: list[dict] = []
        last_prices: dict = {}

        # 전체 시간 타임라인 구성
        all_hours: set = set()
        for (code, market), (hdf, _) in hourly_data.items():
            mask = (hdf["date"].dt.date >= start_d) & (hdf["date"].dt.date <= end_d)
            all_hours.update(hdf.loc[mask, "date"].tolist())
        timeline = sorted(all_hours)

        # 변동성 분류 캐시 (하루 단위 재계산)
        classify_cache: dict = {}
        current_day: date | None = None

        for hour_dt in timeline:
            if self._cancelled:
                return None

            trading_day = hour_dt.date()
            hour_str = hour_dt.strftime("%H:%M")

            # 날짜 바뀔 때 분류 캐시 초기화 + 스윙 신호 (전일 종가)
            if trading_day != current_day:
                classify_cache.clear()
                current_day = trading_day
                # 스윙 매도 체크 (이전 일봉 종가 기준)
                for (code, market) in list(positions.keys()):
                    pos = positions[(code, market)]
                    if pos.get("mode") != "swing":
                        continue
                    if (code, market) not in daily_data:
                        continue
                    ddf, _ = daily_data[(code, market)]
                    hist = ddf[ddf["date"].dt.date < trading_day].tail(65).copy()
                    if hist.empty:
                        continue
                    raw_price = float(hist.iloc[-1]["close"])
                    price = raw_price * exchange_rate if market == "US" else raw_price
                    tp_use = float(self._db_get("take_profit", take_profit))
                    sl_use = float(self._db_get("stop_loss",   stop_loss))
                    sig = self.strategy.analyze(hist, price, pos["avg_price"], sl_use, tp_use, "swing")
                    if sig.action == "SELL":
                        rec = self._mk_sell(code, market, pos, price, sig.reason,
                                            str(trading_day), "09:00", exchange_rate)
                        cash += rec.amount - rec.fee
                        all_trades.append(rec)
                        del positions[(code, market)]
                        last_prices[(code, market)] = price

            # 시간봉 가격 수집
            hour_prices: dict = {}
            for (code, market), (hdf, name) in hourly_data.items():
                rows = hdf[hdf["date"] == hour_dt]
                if rows.empty:
                    continue
                raw = float(rows.iloc[-1]["close"])
                price = raw * exchange_rate if market == "US" else raw
                hour_prices[(code, market)] = (price, name)
                last_prices[(code, market)] = price

            # ── 스캘핑 포지션 매도 체크 ──
            for (code, market) in list(positions.keys()):
                if positions[(code, market)].get("mode") != "scalp":
                    continue
                if (code, market) not in hour_prices or (code, market) not in hourly_data:
                    continue
                price, _ = hour_prices[(code, market)]
                pos = positions[(code, market)]
                hdf, _ = hourly_data[(code, market)]
                hist = hdf[hdf["date"] <= hour_dt].tail(50).copy()
                if market == "US":
                    hist = hist.copy(); hist["close"] = hist["close"] * exchange_rate
                tp_s = config.SCALP_TAKE_PROFIT_KR if market == "KR" else config.SCALP_TAKE_PROFIT_US
                sig = self.strategy.analyze(hist, price, pos["avg_price"],
                                            config.SCALP_STOP_LOSS, tp_s, "scalp")
                if sig.action == "SELL":
                    rec = self._mk_sell(code, market, pos, price, sig.reason,
                                        str(trading_day), hour_str, exchange_rate)
                    cash += rec.amount - rec.fee
                    all_trades.append(rec)
                    del positions[(code, market)]

            # ── 신규 매수 (스캘핑 우선, 빈 슬롯 있을 때) ──
            if len(positions) < max_positions:
                candidates = []
                for (code, market), (price, name) in hour_prices.items():
                    if (code, market) in positions:
                        continue
                    if (code, market) not in hourly_data:
                        continue

                    # 변동성 분류
                    ck = (code, market)
                    if ck not in classify_cache:
                        ddf, _ = daily_data.get(ck, (None, None))
                        if ddf is not None:
                            hist_d = ddf[ddf["date"].dt.date <= trading_day].tail(30)
                            classify_cache[ck] = self.strategy.classify_volatility(hist_d)
                        else:
                            classify_cache[ck] = "swing"
                    mode = classify_cache[ck]

                    hdf, _ = hourly_data[(code, market)]
                    hist_h = hdf[hdf["date"] <= hour_dt].tail(50).copy()
                    if len(hist_h) < 15:
                        continue
                    if market == "US":
                        hist_h = hist_h.copy(); hist_h["close"] = hist_h["close"] * exchange_rate

                    if mode == "scalp":
                        tp_s = config.SCALP_TAKE_PROFIT_KR if market == "KR" else config.SCALP_TAKE_PROFIT_US
                        sig = self.strategy.analyze(hist_h, price, None,
                                                    config.SCALP_STOP_LOSS, tp_s, "scalp")
                    else:
                        # 스윙 매수는 일봉 기반, 하루 1회 (시장 열릴 때 첫 캔들)
                        if hour_str not in ("09:00", "09:30", "10:00"):
                            continue
                        ddf, _ = daily_data.get(ck, (None, None))
                        if ddf is None:
                            continue
                        hist_d = ddf[ddf["date"].dt.date <= trading_day].tail(65).copy()
                        if len(hist_d) < 30:
                            continue
                        if market == "US":
                            hist_d = hist_d.copy(); hist_d["close"] = hist_d["close"] * exchange_rate
                        tp_w = float(self._db_get("take_profit", take_profit))
                        sl_w = float(self._db_get("stop_loss",   stop_loss))
                        sig = self.strategy.analyze(hist_d, price, None, sl_w, tp_w, "swing")

                    if sig.action == "BUY":
                        candidates.append((sig.confidence, code, market, price, name, sig.reason, mode))

                candidates.sort(key=lambda x: -x[0])
                for _, code, market, price, name, reason, mode in candidates:
                    if len(positions) >= max_positions:
                        break
                    rec = self._mk_buy(code, market, name, price, reason,
                                       str(trading_day), hour_str, cash, exchange_rate)
                    if rec:
                        cash -= rec.amount + rec.fee
                        positions[(code, market)] = {
                            "name": name, "quantity": rec.quantity,
                            "avg_price": price, "mode": mode,
                        }
                        all_trades.append(rec)

            # 시간별 포트폴리오 스냅샷
            holdings_val = sum(
                last_prices.get((c, m), pos["avg_price"]) * pos["quantity"]
                for (c, m), pos in positions.items()
            )
            snap_val = round(cash + holdings_val, 0)
            dt_str = hour_dt.strftime("%Y-%m-%d %H:%M")
            hourly_history.append({"datetime": dt_str, "value": snap_val})

            # 일별 스냅샷 (마지막 시간 기준)
            if (not daily_history or daily_history[-1]["date"] != str(trading_day)):
                daily_history.append({"date": str(trading_day), "value": snap_val})
            else:
                daily_history[-1]["value"] = snap_val

        # 기간 종료 강제 청산
        last_day_str = str(end_d)
        for (code, market), pos in list(positions.items()):
            fb_price = last_prices.get((code, market), pos["avg_price"])
            rec = self._mk_sell(code, market, pos, fb_price, "백테스트 기간 종료 청산",
                                last_day_str, "15:30", exchange_rate)
            cash += rec.amount - rec.fee
            all_trades.append(rec)

        return self._build_result(
            all_trades, daily_history, hourly_history,
            start_d, end_d, initial_capital, cash, used_hourly=True,
        )

    # ── 일봉 시뮬레이션 (폴백) ───────────────────────────────

    def _simulate_daily(
        self, daily_data, start_d, end_d,
        initial_capital, exchange_rate, stop_loss, take_profit, max_positions,
    ) -> BacktestResult:
        cash = initial_capital
        positions: dict = {}
        all_trades: list[TradeRecord] = []
        daily_history: list[dict] = []
        last_prices: dict = {}

        all_dates: set = set()
        for (code, market), (df, _) in daily_data.items():
            mask = (df["date"].dt.date >= start_d) & (df["date"].dt.date <= end_d)
            all_dates.update(df.loc[mask, "date"].dt.date.tolist())
        trading_days = sorted(all_dates)

        for trading_day in trading_days:
            if self._cancelled:
                return None

            day_prices: dict = {}
            for (code, market), (df, name) in daily_data.items():
                rows = df[df["date"].dt.date == trading_day]
                if rows.empty:
                    continue
                raw = float(rows.iloc[-1]["close"])
                price = raw * exchange_rate if market == "US" else raw
                day_prices[(code, market)] = (price, name)
                last_prices[(code, market)] = price

            for (code, market) in list(positions.keys()):
                if (code, market) not in day_prices:
                    continue
                pos = positions[(code, market)]
                price, _ = day_prices[(code, market)]
                ddf, _ = daily_data[(code, market)]
                hist = ddf[ddf["date"].dt.date <= trading_day].tail(65).copy()
                if market == "US":
                    hist = hist.copy(); hist["close"] = hist["close"] * exchange_rate
                mode = pos.get("mode", "swing")
                if mode == "scalp":
                    tp_s = config.SCALP_TAKE_PROFIT_KR if market == "KR" else config.SCALP_TAKE_PROFIT_US
                    sig = self.strategy.analyze(hist, price, pos["avg_price"],
                                                config.SCALP_STOP_LOSS, tp_s, "scalp")
                else:
                    tp_w = float(self._db_get("take_profit", take_profit))
                    sl_w = float(self._db_get("stop_loss",   stop_loss))
                    sig = self.strategy.analyze(hist, price, pos["avg_price"], sl_w, tp_w, "swing")
                if sig.action == "SELL":
                    rec = self._mk_sell(code, market, pos, price, sig.reason,
                                        str(trading_day), "15:30", exchange_rate)
                    cash += rec.amount - rec.fee
                    all_trades.append(rec)
                    del positions[(code, market)]

            if len(positions) < max_positions:
                candidates = []
                for (code, market), (df, name) in daily_data.items():
                    if (code, market) in positions or (code, market) not in day_prices:
                        continue
                    price, _ = day_prices[(code, market)]
                    hist = df[df["date"].dt.date <= trading_day].tail(65).copy()
                    if market == "US":
                        hist = hist.copy(); hist["close"] = hist["close"] * exchange_rate
                    if len(hist) < 30:
                        continue
                    mode = self.strategy.classify_volatility(hist.tail(30))
                    if mode == "scalp":
                        tp_s = config.SCALP_TAKE_PROFIT_KR if market == "KR" else config.SCALP_TAKE_PROFIT_US
                        sig = self.strategy.analyze(hist, price, None,
                                                    config.SCALP_STOP_LOSS, tp_s, "scalp")
                    else:
                        tp_w = float(self._db_get("take_profit", take_profit))
                        sl_w = float(self._db_get("stop_loss",   stop_loss))
                        sig = self.strategy.analyze(hist, price, None, sl_w, tp_w, "swing")
                    if sig.action == "BUY":
                        candidates.append((sig.confidence, code, market, price, name, sig.reason, mode))

                candidates.sort(key=lambda x: -x[0])
                for _, code, market, price, name, reason, mode in candidates:
                    if len(positions) >= max_positions:
                        break
                    rec = self._mk_buy(code, market, name, price, reason,
                                       str(trading_day), "09:00", cash, exchange_rate)
                    if rec:
                        cash -= rec.amount + rec.fee
                        positions[(code, market)] = {
                            "name": name, "quantity": rec.quantity,
                            "avg_price": price, "mode": mode,
                        }
                        all_trades.append(rec)

            holdings_val = sum(
                last_prices.get((c, m), pos["avg_price"]) * pos["quantity"]
                for (c, m), pos in positions.items()
            )
            daily_history.append({"date": str(trading_day), "value": round(cash + holdings_val, 0)})

        last_day_str = str(end_d)
        for (code, market), pos in list(positions.items()):
            fb_price = last_prices.get((code, market), pos["avg_price"])
            rec = self._mk_sell(code, market, pos, fb_price, "백테스트 기간 종료 청산",
                                last_day_str, "15:30", exchange_rate)
            cash += rec.amount - rec.fee
            all_trades.append(rec)

        return self._build_result(
            all_trades, daily_history, [],
            start_d, end_d, initial_capital, cash, used_hourly=False,
        )

    # ── 헬퍼 ─────────────────────────────────────────────────

    def _mk_buy(self, code, market, name, price, reason,
                trade_date, trade_time, cash, exchange_rate) -> "TradeRecord | None":
        fee_rate = config.KR_BUY_FEE if market == "KR" else config.US_BUY_FEE
        invest = min(cash * config.MAX_POSITION_RATIO, cash * 0.9)
        quantity = int((invest / (1 + fee_rate)) / price)
        if quantity <= 0:
            return None
        amount = price * quantity
        fee = amount * fee_rate
        if amount + fee > cash:
            return None
        return TradeRecord(trade_date, trade_time, code, name, market,
                           "BUY", price, quantity, amount, fee, None, None, reason)

    def _mk_sell(self, code, market, pos, price, reason,
                 trade_date, trade_time, exchange_rate) -> TradeRecord:
        fee_rate = config.KR_SELL_FEE if market == "KR" else config.US_SELL_FEE
        qty   = pos["quantity"]
        amount = price * qty
        fee   = amount * fee_rate
        net   = amount - fee
        cost  = pos["avg_price"] * qty
        profit = net - cost
        profit_rate = profit / cost * 100 if cost > 0 else 0
        return TradeRecord(trade_date, trade_time, code, pos["name"], market,
                           "SELL", price, qty, amount, fee, profit, profit_rate, reason)

    @staticmethod
    def _db_get(key, default):
        return default

    def _build_result(self, all_trades, daily_history, hourly_history,
                      start_d, end_d, initial_capital, final_cash,
                      used_hourly: bool = False) -> BacktestResult:
        final_value = final_cash
        profit = final_value - initial_capital
        profit_rate = profit / initial_capital * 100 if initial_capital > 0 else 0

        sell_trades = [t for t in all_trades if t.trade_type == "SELL"]
        win  = [t for t in sell_trades if (t.profit or 0) >= 0]
        loss = [t for t in sell_trades if (t.profit or 0) < 0]

        # MDD
        history_vals = hourly_history if used_hourly and hourly_history else daily_history
        max_dd = 0.0
        if history_vals:
            peak = history_vals[0]["value"]
            for h in history_vals:
                v = h["value"]
                if v > peak:
                    peak = v
                if peak > 0:
                    dd = (v - peak) / peak * 100
                    if dd < max_dd:
                        max_dd = dd

        # 종목별 성과
        perf: dict = {}
        for t in all_trades:
            k = (t.code, t.market)
            if k not in perf:
                perf[k] = {"code": t.code, "name": t.name, "market": t.market,
                            "trades": 0, "profit": 0.0, "invested": 0.0}
            perf[k]["trades"] += 1
            if t.profit is not None:
                perf[k]["profit"] += t.profit
            if t.trade_type == "BUY":
                perf[k]["invested"] += t.amount

        perf_list = []
        for p in perf.values():
            rate = p["profit"] / p["invested"] * 100 if p["invested"] > 0 else 0
            perf_list.append({**p, "profit_rate": rate})
        perf_list.sort(key=lambda x: -x["profit"])

        return BacktestResult(
            start_date=str(start_d),
            end_date=str(end_d),
            initial_capital=initial_capital,
            final_value=final_value,
            profit=profit,
            profit_rate=profit_rate,
            total_trades=len(all_trades),
            buy_trades=len([t for t in all_trades if t.trade_type == "BUY"]),
            sell_trades=len(sell_trades),
            win_trades=len(win),
            loss_trades=len(loss),
            portfolio_history=daily_history,
            hourly_history=hourly_history,
            trades=all_trades,
            stock_performances=perf_list,
            max_drawdown=max_dd,
            used_hourly=used_hourly,
        )


# ── 유틸 ──────────────────────────────────────────────────────

def _clean_df(df: pd.DataFrame, is_hourly: bool = False) -> pd.DataFrame:
    df = df.reset_index()
    df.columns = [str(c).lower().split(".")[-1].strip() for c in df.columns]

    # datetime 컬럼 이름 정규화
    for alias in ("datetime", "date", "index", "timestamp"):
        if alias in df.columns:
            df = df.rename(columns={alias: "date"})
            break

    if "date" not in df.columns:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert(None)

    needed = ["date", "open", "high", "low", "close", "volume"]
    for col in needed[1:]:
        if col not in df.columns:
            return pd.DataFrame()

    df = df[needed].dropna(subset=["close", "volume"])
    df = df[df["close"] > 0]
    return df.reset_index(drop=True)
