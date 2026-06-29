"""백테스트 엔진 — 과거 데이터로 전략 시뮬레이션"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable

import pandas as pd
import yfinance as yf
from dateutil.relativedelta import relativedelta

import config
from trader.strategy import TechnicalStrategy


@dataclass
class TradeRecord:
    date:       str
    code:       str
    market:     str
    name:       str
    trade_type: str   # BUY | SELL
    price:      float
    quantity:   float
    amount:     float
    fee:        float
    profit:     float
    reason:     str
    mode:       str = "swing"


@dataclass
class BacktestResult:
    start_date:        str
    end_date:          str
    duration_days:     int
    initial_capital:   float
    final_value:       float
    profit_rate:       float
    max_drawdown:      float
    total_trades:      int
    win_trades:        int
    sell_trades:       int
    trades:            list = field(default_factory=list)
    portfolio_history: list = field(default_factory=list)
    stock_performances: list = field(default_factory=list)


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame 컬럼 정규화 및 날짜 처리"""
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    # MultiIndex 처리 (yfinance batch download)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = {"open", "high", "low", "close"}
    if not required.issubset(set(df.columns)):
        return pd.DataFrame()

    # 타임존 제거
    if hasattr(df.index, "tz") and df.index.tz is not None:
        df.index = df.index.tz_convert(None)

    df["date"] = pd.to_datetime(df.index)
    df = df.dropna(subset=["close"])
    df = df[df["close"] > 0]
    return df.reset_index(drop=True)


class Backtester:

    def __init__(self, strategy: TechnicalStrategy):
        self.strategy  = strategy
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
        stop_loss: float = None,
        take_profit: float = None,
        max_positions: int = None,
        progress_callback: Callable | None = None,
    ) -> BacktestResult | None:
        self._cancelled = False

        stop_loss    = stop_loss    or config.SWING_STOP_LOSS
        take_profit  = take_profit  or config.SWING_TAKE_PROFIT
        max_positions = max_positions or config.MAX_POSITIONS

        start_d  = date(start_year, start_month, 1)
        end_d    = start_d + relativedelta(months=duration_months)
        fetch_s  = (start_d - timedelta(days=90)).strftime("%Y-%m-%d")
        fetch_e  = (end_d   + timedelta(days=2)).strftime("%Y-%m-%d")

        # 종목 풀
        pool = []
        if use_kr:
            pool += config.DOMESTIC_STOCK_POOL
        if use_us:
            pool += [{**s, "yf_code": s["code"]} for s in config.US_STOCK_POOL]

        if progress_callback:
            progress_callback(f"데이터 다운로드 중... ({len(pool)}종목)")

        # 데이터 수집
        daily_data: dict = {}
        for i, stock in enumerate(pool):
            if self._cancelled:
                return None
            yf_code = stock.get("yf_code", stock["code"])
            if progress_callback:
                progress_callback(f"[{i+1}/{len(pool)}] {stock['name']} 로드 중")
            try:
                df = yf.Ticker(yf_code).history(start=fetch_s, end=fetch_e)
                if df.empty or len(df) < 10:
                    continue
                df = _clean_df(df)
                if df.empty:
                    continue
                daily_data[(stock["code"], stock["market"])] = (df, stock["name"])
            except Exception:
                continue

        if not daily_data:
            return None

        if progress_callback:
            progress_callback(f"시뮬레이션 실행 중... ({len(daily_data)}종목)")

        return self._simulate(
            daily_data, start_d, end_d,
            initial_capital, exchange_rate,
            stop_loss, take_profit, max_positions,
        )

    def _simulate(
        self, daily_data, start_d, end_d,
        initial_capital, exchange_rate, stop_loss, take_profit, max_positions,
    ) -> BacktestResult:
        cash       = initial_capital
        positions  = {}
        all_trades = []
        history    = []

        # 거래일 목록
        all_dates = set()
        for (code, market), (df, _) in daily_data.items():
            mask = (df["date"].dt.date >= start_d) & (df["date"].dt.date <= end_d)
            all_dates.update(df.loc[mask, "date"].dt.date.tolist())
        trading_days = sorted(all_dates)

        peak_value = initial_capital
        max_dd     = 0.0

        for day in trading_days:
            if self._cancelled:
                return None

            # 당일 가격 수집
            day_prices = {}
            for (code, market), (df, name) in daily_data.items():
                rows = df[df["date"].dt.date == day]
                if rows.empty:
                    continue
                raw   = float(rows.iloc[-1]["close"])
                price = raw * exchange_rate if market == "US" else raw
                day_prices[(code, market)] = (price, name)

            # 매도 체크
            for (code, market) in list(positions.keys()):
                if (code, market) not in day_prices:
                    continue
                pos   = positions[(code, market)]
                price, _ = day_prices[(code, market)]
                hist  = daily_data[(code, market)][0]
                hist  = hist[hist["date"].dt.date <= day].tail(65).copy()
                if market == "US":
                    hist = hist.copy()
                    for col in ["open", "high", "low", "close"]:
                        if col in hist.columns:
                            hist[col] *= exchange_rate
                mode = pos["mode"]
                sl   = config.SCALP_STOP_LOSS if mode == "scalp" else stop_loss
                tp   = (config.SCALP_TAKE_PROFIT_KR if market == "KR"
                        else config.SCALP_TAKE_PROFIT_US) if mode == "scalp" else take_profit

                sig = self.strategy.analyze(hist, price, pos["avg_price"], sl, tp, mode)
                if sig.action == "SELL":
                    rec = self._mk_sell(code, market, pos, price, sig.reason,
                                        str(day), exchange_rate)
                    cash += rec.amount - rec.fee
                    all_trades.append(rec)
                    del positions[(code, market)]

            # 매수 체크
            if len(positions) < max_positions:
                candidates = []
                for (code, market), (df, name) in daily_data.items():
                    if (code, market) in positions or (code, market) not in day_prices:
                        continue
                    price, _ = day_prices[(code, market)]
                    hist  = df[df["date"].dt.date <= day].tail(65).copy()
                    if len(hist) < 20:
                        continue
                    if market == "US":
                        hist = hist.copy()
                        for col in ["open", "high", "low", "close"]:
                            if col in hist.columns:
                                hist[col] *= exchange_rate
                    mode = self.strategy.classify_volatility(hist.tail(20))
                    sl   = config.SCALP_STOP_LOSS if mode == "scalp" else stop_loss
                    tp   = (config.SCALP_TAKE_PROFIT_KR if market == "KR"
                            else config.SCALP_TAKE_PROFIT_US) if mode == "scalp" else take_profit
                    sig  = self.strategy.analyze(hist, price, None, sl, tp, mode)
                    if sig.action == "BUY":
                        candidates.append((sig.confidence, code, market, price, name, sig.reason, mode))

                candidates.sort(key=lambda x: -x[0])
                for (conf, code, market, price, name, reason, mode) in candidates:
                    if len(positions) >= max_positions:
                        break
                    budget   = cash * config.MAX_POSITION_RATIO
                    quantity = max(1, int(budget / price))
                    cost     = price * quantity
                    fee_rate = config.KR_FEE_RATE if market == "KR" else config.US_FEE_RATE
                    fee      = cost * fee_rate
                    if cash < cost + fee:
                        continue
                    cash -= (cost + fee)
                    positions[(code, market)] = {
                        "name": name, "quantity": quantity,
                        "avg_price": price, "mode": mode,
                    }
                    all_trades.append(self._mk_buy(
                        code, market, name, price, quantity, reason, str(day), mode))

            # 포트폴리오 평가
            total = cash + sum(
                positions[(c, m)]["quantity"] *
                day_prices.get((c, m), (positions[(c, m)]["avg_price"], ""))[0]
                for (c, m) in positions
            )
            history.append({"date": str(day), "value": total})

            if total > peak_value:
                peak_value = total
            if peak_value > 0:
                dd = (total - peak_value) / peak_value * 100
                if dd < max_dd:
                    max_dd = dd

        # 잔여 포지션 청산
        for (code, market), pos in list(positions.items()):
            last_prices = {}
            for (c, m), (df, _) in daily_data.items():
                row = df[df["date"].dt.date <= end_d]
                if not row.empty:
                    raw = float(row.iloc[-1]["close"])
                    last_prices[(c, m)] = raw * exchange_rate if m == "US" else raw

            price = last_prices.get((code, market), pos["avg_price"])
            rec   = self._mk_sell(code, market, pos, price, "기간만료", str(end_d), exchange_rate)
            cash += rec.amount - rec.fee
            all_trades.append(rec)

        final_value  = cash
        profit_rate  = (final_value - initial_capital) / initial_capital * 100
        sell_trades  = [t for t in all_trades if t.trade_type == "SELL"]
        win_trades   = [t for t in sell_trades if t.profit >= 0]

        # 종목별 성과
        stock_perf = self._calc_stock_perf(all_trades)

        return BacktestResult(
            start_date=str(start_d), end_date=str(end_d),
            duration_days=(end_d - start_d).days,
            initial_capital=initial_capital,
            final_value=final_value,
            profit_rate=profit_rate,
            max_drawdown=max_dd,
            total_trades=len(all_trades),
            win_trades=len(win_trades),
            sell_trades=len(sell_trades),
            trades=all_trades,
            portfolio_history=history,
            stock_performances=stock_perf,
        )

    # ── 거래 레코드 생성 ──────────────────────────────────────

    def _mk_buy(self, code, market, name, price, quantity, reason, trade_date, mode):
        fee_rate = config.KR_FEE_RATE if market == "KR" else config.US_FEE_RATE
        amount   = price * quantity
        return TradeRecord(
            date=trade_date, code=code, market=market, name=name,
            trade_type="BUY", price=price, quantity=quantity,
            amount=amount, fee=amount * fee_rate, profit=0,
            reason=reason, mode=mode,
        )

    def _mk_sell(self, code, market, pos, price, reason, trade_date, exchange_rate):
        fee_rate = config.KR_FEE_RATE if market == "KR" else config.US_FEE_RATE
        quantity = pos["quantity"]
        amount   = price * quantity
        fee      = amount * fee_rate
        profit   = (price - pos["avg_price"]) * quantity - fee
        return TradeRecord(
            date=trade_date, code=code, market=market, name=pos["name"],
            trade_type="SELL", price=price, quantity=quantity,
            amount=amount, fee=fee, profit=profit,
            reason=reason, mode=pos.get("mode", "swing"),
        )

    def _calc_stock_perf(self, trades: list) -> list:
        summary = {}
        for t in trades:
            key = (t.code, t.market)
            if key not in summary:
                summary[key] = {"code": t.code, "market": t.market,
                                 "name": t.name, "profit": 0.0}
            if t.trade_type == "SELL":
                summary[key]["profit"] += t.profit

        result = list(summary.values())
        total_profit = sum(abs(r["profit"]) for r in result) or 1
        for r in result:
            r["profit_rate"] = r["profit"] / total_profit * 100
        return sorted(result, key=lambda x: x["profit"])
