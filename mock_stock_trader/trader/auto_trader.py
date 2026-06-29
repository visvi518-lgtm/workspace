"""자동매매 엔진 — APScheduler 기반 주기적 스캔"""
from __future__ import annotations
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

import config
from db.database import Database
from trader.portfolio import Portfolio
from trader.strategy import TechnicalStrategy
from crawler.naver_crawler import NaverCrawler
from crawler.yahoo_crawler import YahooCrawler


KST = timezone(timedelta(hours=9))
EST = timezone(timedelta(hours=-5))


class AutoTrader:

    def __init__(
        self,
        db: Database,
        portfolio: Portfolio,
        strategy: TechnicalStrategy,
        naver: NaverCrawler,
        yahoo: YahooCrawler,
        on_trade=None,
        on_log=None,
    ):
        self.db        = db
        self.portfolio = portfolio
        self.strategy  = strategy
        self.naver     = naver
        self.yahoo     = yahoo
        self.on_trade  = on_trade
        self.on_log    = on_log
        self._scheduler = BackgroundScheduler(timezone="Asia/Seoul")
        self.is_running = False

    # ── 시장 시간 ─────────────────────────────────────────────

    @staticmethod
    def is_kr_market_open() -> bool:
        now = datetime.now(KST)
        if now.weekday() >= 5:
            return False
        return (9, 0) <= (now.hour, now.minute) <= (15, 30)

    @staticmethod
    def is_us_market_open() -> bool:
        now = datetime.now(EST)
        if now.weekday() >= 5:
            return False
        return (9, 30) <= (now.hour, now.minute) <= (16, 0)

    # ── 스케줄러 제어 ─────────────────────────────────────────

    def start(self, interval_minutes: int = 3):
        if self.is_running:
            return
        self._scheduler.add_job(
            self._scan, "interval", minutes=interval_minutes,
            id="scan", replace_existing=True,
        )
        self._scheduler.start()
        self.is_running = True
        self._log("자동매매 시작")

    def stop(self):
        if not self.is_running:
            return
        self._scheduler.shutdown(wait=False)
        self._scheduler = BackgroundScheduler(timezone="Asia/Seoul")
        self.is_running  = False
        self._log("자동매매 중지")

    # ── 메인 스캔 루프 ────────────────────────────────────────

    def _scan(self):
        force = self.db.get_setting("force_trade", "0") == "1"
        kr_open = self.is_kr_market_open() or force
        us_open = self.is_us_market_open() or force

        if not kr_open and not us_open:
            return

        pool = self._get_pool(kr_open, us_open)
        stop_loss   = float(self.db.get_setting("stop_loss",   config.SWING_STOP_LOSS))
        take_profit = float(self.db.get_setting("take_profit", config.SWING_TAKE_PROFIT))
        max_pos     = int(self.db.get_setting("max_positions", config.MAX_POSITIONS))
        exc_rate    = float(self.db.get_setting("exchange_rate", config.DEFAULT_EXCHANGE_RATE))

        current_prices = self._fetch_prices(pool, exc_rate)
        self._save_history(current_prices)

        # 매도 먼저
        for (code, market), pos in list(self.portfolio.positions.items()):
            if (code, market) not in current_prices:
                continue
            price = current_prices[(code, market)]
            hist  = self._fetch_history(code, market, exc_rate)
            if hist is None:
                continue
            mode  = pos.get("mode", "swing")
            sl    = config.SCALP_STOP_LOSS if mode == "scalp" else stop_loss
            tp    = (config.SCALP_TAKE_PROFIT_KR if market == "KR"
                     else config.SCALP_TAKE_PROFIT_US) if mode == "scalp" else take_profit
            sig   = self.strategy.analyze(hist, price, pos["avg_price"], sl, tp, mode)
            if sig.action == "SELL":
                result = self.portfolio.sell(code, market, price, sig.reason)
                if result:
                    self._log(f"[매도] {pos['name']} {price:,.0f}원 | {sig.reason} | 손익 {result['profit']:+,.0f}원")
                    if self.on_trade:
                        self.on_trade("SELL", pos["name"], price, sig.reason)

        # 매수
        if self.portfolio.position_count() >= max_pos:
            return

        for stock in pool:
            if self.portfolio.position_count() >= max_pos:
                break
            code, market, name = stock["code"], stock["market"], stock["name"]
            yf_code = stock.get("yf_code", code)
            if self.portfolio.has_position(code, market):
                continue
            price = current_prices.get((code, market))
            if not price:
                continue
            hist = self._fetch_history(yf_code, market, exc_rate)
            if hist is None or len(hist) < 20:
                continue

            mode = self.strategy.classify_volatility(hist.tail(20))
            sl   = config.SCALP_STOP_LOSS if mode == "scalp" else stop_loss
            tp   = (config.SCALP_TAKE_PROFIT_KR if market == "KR"
                    else config.SCALP_TAKE_PROFIT_US) if mode == "scalp" else take_profit
            sig  = self.strategy.analyze(hist, price, None, sl, tp, mode)

            if sig.action == "BUY":
                cap_ratio = float(self.db.get_setting("position_ratio", config.MAX_POSITION_RATIO))
                total_val = self.portfolio.total_value(current_prices)
                budget    = total_val * cap_ratio
                quantity  = max(1, int(budget / price))
                result    = self.portfolio.buy(code, market, name, price, quantity, mode)
                if result:
                    self._log(f"[매수] {name} {price:,.0f}원 ×{quantity} | {sig.reason} | 모드:{mode}")
                    if self.on_trade:
                        self.on_trade("BUY", name, price, sig.reason)

    # ── 보조 메서드 ───────────────────────────────────────────

    def _get_pool(self, kr_open, us_open) -> list:
        pool = []
        if kr_open:
            pool += config.DOMESTIC_STOCK_POOL
        if us_open:
            for s in config.US_STOCK_POOL:
                pool.append({**s, "yf_code": s["code"]})
        return pool

    def _fetch_prices(self, pool, exc_rate) -> dict:
        prices = {}
        kr_codes = [s["code"] for s in pool if s["market"] == "KR"]
        us_codes = [s["code"] for s in pool if s["market"] == "US"]

        kr_p = self.naver.get_prices(kr_codes)
        for code, price in kr_p.items():
            prices[(code, "KR")] = price

        us_p = self.yahoo.get_prices(us_codes)
        for code, price in us_p.items():
            prices[(code, "US")] = price * exc_rate

        return prices

    def _fetch_history(self, code: str, market: str, exc_rate: float) -> pd.DataFrame | None:
        try:
            df = yf.Ticker(code).history(period="3mo", interval="1d")
            if df.empty:
                return None
            df.columns = [c.lower() for c in df.columns]
            if "close" not in df.columns:
                return None
            if hasattr(df.index, "tz") and df.index.tz is not None:
                df.index = df.index.tz_convert(None)
            if market == "US":
                for col in ["open", "high", "low", "close"]:
                    if col in df.columns:
                        df[col] = df[col] * exc_rate
            df["date"] = pd.to_datetime(df.index)
            return df.reset_index(drop=True)
        except Exception:
            return None

    def _save_history(self, prices: dict):
        total = self.portfolio.total_value(prices)
        ts    = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.db.save_history(ts, total)

    def _log(self, msg: str):
        print(f"[AutoTrader] {msg}")
        if self.on_log:
            self.on_log(msg)
