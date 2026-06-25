from dataclasses import dataclass
from datetime import date, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from dateutil.relativedelta import relativedelta

import config
from trader.strategy import TechnicalStrategy

# 데이터가 신뢰할 수 있는 최소 날짜
MIN_KR_DATE = date(2000, 1, 1)
MIN_US_DATE = date(1990, 1, 1)
# 거래소 개설 이전 (경고용)
KRX_FOUNDED = date(1956, 3, 3)
NYSE_FOUNDED = date(1792, 5, 17)


@dataclass
class TradeRecord:
    date: str
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
    portfolio_history: list
    trades: list
    stock_performances: list
    max_drawdown: float


def validate_period(start_year: int, start_month: int, duration_months: int,
                    use_kr: bool, use_us: bool) -> tuple[bool, str]:
    today = date.today()

    try:
        start_d = date(start_year, start_month, 1)
    except ValueError:
        return False, "올바른 연도/월을 입력해 주세요."

    if duration_months < 1:
        return False, "기간은 최소 1개월 이상이어야 합니다."

    end_d = start_d + relativedelta(months=duration_months)
    one_month_ago = today - relativedelta(months=1)

    # 주식 시장 개설 이전 체크 (거래소 개설 역사)
    if use_kr and start_d < KRX_FOUNDED:
        return False, (
            f"한국거래소(KRX)는 {KRX_FOUNDED.strftime('%Y년 %m월 %d일')} 개설되었습니다.\n"
            f"그 이전 날짜는 선택할 수 없습니다.\n"
            f"(선택: {start_d.strftime('%Y년 %m월')})"
        )
    if use_us and start_d < NYSE_FOUNDED:
        return False, (
            f"뉴욕증권거래소(NYSE)는 {NYSE_FOUNDED.strftime('%Y년 %m월 %d일')} 개설되었습니다.\n"
            f"그 이전 날짜는 선택할 수 없습니다.\n"
            f"(선택: {start_d.strftime('%Y년 %m월')})"
        )

    # 데이터 가용 범위 체크
    if use_kr and start_d < MIN_KR_DATE:
        return False, (
            f"한국 주식 시장의 신뢰할 수 있는 데이터는\n"
            f"{MIN_KR_DATE.strftime('%Y년 %m월')} 이후부터 제공됩니다.\n"
            f"(선택: {start_d.strftime('%Y년 %m월')})"
        )
    if use_us and start_d < MIN_US_DATE:
        return False, (
            f"미국 주식 시장의 신뢰할 수 있는 데이터는\n"
            f"{MIN_US_DATE.strftime('%Y년 %m월')} 이후부터 제공됩니다.\n"
            f"(선택: {start_d.strftime('%Y년 %m월')})"
        )

    # 현재 시점으로부터 1개월 미만 체크
    if end_d > one_month_ago:
        if start_d > one_month_ago:
            return False, (
                f"시작 날짜({start_d.strftime('%Y년 %m월')})가 현재로부터 1개월 이내입니다.\n"
                f"백테스트 시작일은 {one_month_ago.strftime('%Y년 %m월')} 이전이어야 합니다."
            )
        return False, (
            f"선택한 기간의 종료일({end_d.strftime('%Y년 %m월')})이\n"
            f"현재 날짜로부터 1개월 이내입니다.\n"
            f"기간을 줄이거나 더 과거 날짜를 선택해 주세요.\n"
            f"(허용 종료일: {one_month_ago.strftime('%Y년 %m월')} 이전)"
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
        stop_loss: float = -0.03,
        take_profit: float = 0.025,
        max_positions: int = 5,
        progress_callback=None,
    ) -> "BacktestResult | None":
        self._cancelled = False

        start_d = date(start_year, start_month, 1)
        end_d = start_d + relativedelta(months=duration_months)

        # 지표 계산을 위해 시작 90일 전부터 데이터 수집
        fetch_start = start_d - timedelta(days=90)
        fetch_end = end_d + timedelta(days=2)

        pool = []
        if use_kr:
            for s in config.DOMESTIC_STOCK_POOL:
                pool.append({**s, "market": "KR"})
        if use_us:
            for s in config.US_STOCK_POOL:
                pool.append({**s, "yf_code": s["code"], "market": "US"})

        # 데이터 다운로드
        stock_data: dict[tuple, tuple] = {}
        for i, stock in enumerate(pool):
            if self._cancelled:
                return None
            yf_code = stock.get("yf_code", stock["code"])
            if progress_callback:
                progress_callback(f"데이터 로드: {stock['name']} ({i + 1}/{len(pool)})")
            try:
                ticker = yf.Ticker(yf_code)
                df = ticker.history(
                    start=fetch_start.strftime("%Y-%m-%d"),
                    end=fetch_end.strftime("%Y-%m-%d"),
                )
                if df.empty or len(df) < 15:
                    continue
                df = df.reset_index()
                df.columns = [c.lower() if isinstance(c, str) else c for c in df.columns]
                if "date" not in df.columns and "datetime" in df.columns:
                    df = df.rename(columns={"datetime": "date"})
                df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
                df = df[["date", "open", "high", "low", "close", "volume"]].dropna()
                stock_data[(stock["code"], stock["market"])] = (df, stock["name"])
            except Exception:
                continue

        if not stock_data:
            if progress_callback:
                progress_callback("오류: 데이터를 가져올 수 없습니다.")
            return None

        if progress_callback:
            progress_callback(f"시뮬레이션 실행 중... ({len(stock_data)}개 종목)")

        result = self._simulate(
            stock_data, start_d, end_d, initial_capital,
            exchange_rate, stop_loss, take_profit, max_positions,
        )

        if progress_callback and result:
            progress_callback("시뮬레이션 완료!")

        return result

    def _simulate(self, stock_data, start_d, end_d, initial_capital,
                  exchange_rate, stop_loss, take_profit, max_positions):
        cash = initial_capital
        positions: dict = {}
        all_trades: list[TradeRecord] = []
        daily_values: list[dict] = []

        # 시뮬레이션 기간의 모든 거래일 수집
        all_dates: set = set()
        for (code, market), (df, _) in stock_data.items():
            dates_in_period = df[
                (df["date"].dt.date >= start_d) & (df["date"].dt.date <= end_d)
            ]["date"].dt.date.tolist()
            all_dates.update(dates_in_period)

        trading_days = sorted(all_dates)

        last_prices: dict = {}

        for trading_day in trading_days:
            if self._cancelled:
                return None

            # 당일 가격 수집
            day_prices: dict = {}
            for (code, market), (df, name) in stock_data.items():
                rows = df[df["date"].dt.date == trading_day]
                if rows.empty:
                    continue
                raw_price = float(rows.iloc[-1]["close"])
                price = raw_price * exchange_rate if market == "US" else raw_price
                day_prices[(code, market)] = (price, name)
                last_prices[(code, market)] = (price, name)

            # 보유 종목 매도 체크 (손절/익절/매도신호)
            for (code, market) in list(positions.keys()):
                if (code, market) not in day_prices:
                    continue
                pos = positions[(code, market)]
                price, _ = day_prices[(code, market)]

                df, _ = stock_data[(code, market)]
                hist = df[df["date"].dt.date <= trading_day].tail(65).copy()
                if market == "US":
                    hist = hist.copy()
                    hist["close"] = hist["close"] * exchange_rate

                sig = self.strategy.analyze(hist, price, pos["avg_price"], stop_loss, take_profit)

                if sig.action == "SELL":
                    rec = self._do_sell(code, market, pos, price, sig.reason, str(trading_day))
                    cash += rec.amount - rec.fee
                    all_trades.append(rec)
                    del positions[(code, market)]

            # 신규 매수 체크
            if len(positions) < max_positions:
                candidates = []
                for (code, market), (df, name) in stock_data.items():
                    if (code, market) in positions:
                        continue
                    if (code, market) not in day_prices:
                        continue
                    price, _ = day_prices[(code, market)]
                    hist = df[df["date"].dt.date <= trading_day].tail(65).copy()
                    if market == "US":
                        hist = hist.copy()
                        hist["close"] = hist["close"] * exchange_rate
                    if len(hist) < 30:
                        continue
                    sig = self.strategy.analyze(hist, price, None, stop_loss, take_profit)
                    if sig.action == "BUY":
                        candidates.append((sig.confidence, code, market, price, name, sig.reason))

                candidates.sort(key=lambda x: -x[0])
                for _, code, market, price, name, reason in candidates:
                    if len(positions) >= max_positions:
                        break
                    rec = self._do_buy(code, market, name, price, reason, str(trading_day), cash)
                    if rec:
                        fee_rate = config.KR_BUY_FEE if market == "KR" else config.US_BUY_FEE
                        total_cost = rec.amount + rec.fee
                        cash -= total_cost
                        positions[(code, market)] = {
                            "name": name,
                            "quantity": rec.quantity,
                            "avg_price": price,
                        }
                        all_trades.append(rec)

            # 일별 포트폴리오 가치 기록
            holdings_val = sum(
                day_prices.get((c, m), last_prices.get((c, m), (pos["avg_price"], "")))[0]
                * pos["quantity"]
                for (c, m), pos in positions.items()
            )
            daily_values.append({"date": str(trading_day), "value": round(cash + holdings_val, 0)})

        # 기간 종료 후 미청산 포지션 강제 청산
        for (code, market), pos in list(positions.items()):
            fallback_price = last_prices.get((code, market), (pos["avg_price"], ""))[0]
            rec = self._do_sell(code, market, pos, fallback_price, "백테스트 기간 종료 청산", str(end_d))
            cash += rec.amount - rec.fee
            all_trades.append(rec)

        return self._build_result(all_trades, daily_values, start_d, end_d, initial_capital, cash)

    def _do_buy(self, code, market, name, price, reason, trade_date, cash) -> "TradeRecord | None":
        fee_rate = config.KR_BUY_FEE if market == "KR" else config.US_BUY_FEE
        invest = min(cash * config.MAX_POSITION_RATIO, cash * 0.9)
        quantity = int((invest / (1 + fee_rate)) / price)
        if quantity <= 0:
            return None
        amount = price * quantity
        fee = amount * fee_rate
        if amount + fee > cash:
            return None
        return TradeRecord(trade_date, code, name, market, "BUY", price, quantity, amount, fee, None, None, reason)

    def _do_sell(self, code, market, pos, price, reason, trade_date) -> TradeRecord:
        fee_rate = config.KR_SELL_FEE if market == "KR" else config.US_SELL_FEE
        quantity = pos["quantity"]
        amount = price * quantity
        fee = amount * fee_rate
        net = amount - fee
        buy_cost = pos["avg_price"] * quantity
        profit = net - buy_cost
        profit_rate = profit / buy_cost * 100 if buy_cost > 0 else 0
        return TradeRecord(trade_date, code, pos["name"], market, "SELL",
                           price, quantity, amount, fee, profit, profit_rate, reason)

    def _build_result(self, all_trades, daily_values, start_d, end_d,
                      initial_capital, final_cash) -> BacktestResult:
        final_value = final_cash
        profit = final_value - initial_capital
        profit_rate = profit / initial_capital * 100 if initial_capital > 0 else 0

        sell_trades = [t for t in all_trades if t.trade_type == "SELL"]
        win = [t for t in sell_trades if (t.profit or 0) >= 0]
        loss = [t for t in sell_trades if (t.profit or 0) < 0]

        # 최대 낙폭 (MDD)
        max_dd = 0.0
        if daily_values:
            vals = [d["value"] for d in daily_values]
            peak = vals[0]
            for v in vals:
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
            portfolio_history=daily_values,
            trades=all_trades,
            stock_performances=perf_list,
            max_drawdown=max_dd,
        )
