import threading
from datetime import datetime, timezone, timedelta, date
from apscheduler.schedulers.background import BackgroundScheduler

import config
from trader.strategy import TechnicalStrategy
from trader.portfolio import VirtualPortfolio
from crawler.naver_crawler import NaverCrawler
from crawler.yahoo_crawler import YahooCrawler
from db.database import Database

KST = timezone(timedelta(hours=9))
EST = timezone(timedelta(hours=-5))

# 캐시 유효 시간
_HOURLY_CACHE_SEC  = 1800   # 30분
_DAILY_CACHE_SEC   = 3600 * 6  # 6시간


class AutoTrader:
    def __init__(
        self,
        db: Database,
        portfolio: VirtualPortfolio,
        strategy: TechnicalStrategy,
        naver: NaverCrawler,
        yahoo: YahooCrawler,
        on_trade=None,
        on_log=None,
    ):
        self.db = db
        self.portfolio = portfolio
        self.strategy = strategy
        self.naver = naver
        self.yahoo = yahoo
        self.on_trade = on_trade
        self.on_log = on_log

        self._running = False
        self._scheduler = None
        self._lock = threading.Lock()

        # 실시간 가격 캐시
        self.last_prices: dict = {}

        # 데이터 캐시 {key: (df, timestamp)}
        self._hourly_cache: dict = {}
        self._daily_cache: dict = {}

        # 변동성 분류 캐시 (하루마다 갱신)
        self._classify_cache: dict = {}

        # 일일 수익 추적
        self._daily_pnl: float = 0.0
        self._daily_trades: int = 0
        self._today: date | None = None

    # ─── 시작 / 중지 ───────────────────────────────────

    def start(self, interval_minutes: int = None):
        if self._running:
            return
        mins = interval_minutes or int(self.db.get_setting("scan_interval", config.SCAN_INTERVAL_MINUTES))
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(self._scan_all, "interval", minutes=mins, id="scan")
        self._scheduler.start()
        self._running = True
        self._log("자동매매 시작 (스캘핑/스윙 혼합 전략)")
        threading.Thread(target=self._scan_all, daemon=True).start()

    def stop(self):
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
        self._running = False
        self._log("자동매매 중지됨")

    @property
    def is_running(self) -> bool:
        return self._running

    # ─── 메인 스캔 루프 ────────────────────────────────

    def _scan_all(self):
        with self._lock:
            self._reset_daily_if_needed()
            exchange_rate = float(self.db.get_setting("exchange_rate", config.DEFAULT_EXCHANGE_RATE))

            # 보유 종목 매도 체크 (시장 시간 무관)
            self._check_existing_positions(exchange_rate)

            # 일일 목표 달성 여부
            daily_target = float(self.db.get_setting("daily_target", config.DAILY_TARGET_RATE))
            init_cap = self.portfolio.initial_capital
            daily_pnl_pct = self._daily_pnl / init_cap if init_cap > 0 else 0
            target_reached = daily_pnl_pct >= daily_target

            if target_reached:
                self._log(
                    f"일일 목표 달성! ({daily_pnl_pct*100:.2f}%) "
                    f"신규 진입 보류 — 복리 수익 보존"
                )
            else:
                force = self.db.get_setting("force_trade") == "1"
                if self.is_kr_market_open() or force:
                    self._scan_market(config.DOMESTIC_STOCK_POOL, "KR", exchange_rate)
                if self.is_us_market_open() or force:
                    self._scan_market(config.US_STOCK_POOL, "US", exchange_rate)

            # 포트폴리오 스냅샷
            total = self.portfolio.get_total_value(self.last_prices)
            self.db.add_portfolio_snapshot(total, self.portfolio.cash, total - self.portfolio.cash)
            self._log(
                f"스캔완료 | 총자산:{total:,.0f}원 | "
                f"일일수익:{self._daily_pnl:+,.0f}원({daily_pnl_pct*100:+.2f}%)"
            )

    def _reset_daily_if_needed(self):
        today = datetime.now(KST).date()
        if self._today != today:
            self._today = today
            self._daily_pnl = 0.0
            self._daily_trades = 0
            self._classify_cache.clear()
            self._log(f"새 거래일 시작: {today} — 변동성 재분류")

    # ─── 보유 종목 매도 체크 ───────────────────────────

    def _check_existing_positions(self, exchange_rate: float):
        for pos in self.portfolio.get_positions():
            code   = pos["code"]
            market = pos["market"]
            mode   = pos.get("mode", "swing")

            price_info = self._fetch_price(code, market, exchange_rate)
            if not price_info:
                continue
            price = price_info["price"]
            self.last_prices[(code, market)] = price

            tp, sl = self._get_tp_sl(market, mode)
            df = self._get_data_for_mode(code, market, mode)
            sig = self.strategy.analyze(df, price, pos["avg_price"], sl, tp, mode)

            if sig.action == "SELL":
                # 복리 P&L 계산
                fee_rate = config.KR_SELL_FEE if market == "KR" else config.US_SELL_FEE
                net = price * pos["quantity"] * (1 - fee_rate)
                profit = net - pos["avg_price"] * pos["quantity"]

                ok = self.portfolio.sell(code, market, price, sig.reason)
                if ok:
                    self._daily_pnl += profit
                    self._daily_trades += 1
                    self._log(
                        f"[매도/{mode}] {pos['name']} {price:,.0f} | {sig.reason} | "
                        f"손익:{profit:+,.0f}원 | 일일:{self._daily_pnl:+,.0f}원"
                    )
                    if self.on_trade:
                        self.on_trade("SELL", pos["name"], price, sig.reason)

    # ─── 신규 매수 스캔 ────────────────────────────────

    def _scan_market(self, pool: list, market: str, exchange_rate: float):
        max_pos = int(self.db.get_setting("max_positions", config.MAX_POSITIONS))
        candidates = []

        for stock in pool:
            code = stock["code"]
            if self.portfolio.get_position(code, market):
                continue
            if self.portfolio.count_positions() >= max_pos:
                break

            price_info = self._fetch_price(code, market, exchange_rate)
            if not price_info:
                continue
            price = price_info["price"]
            self.last_prices[(code, market)] = price

            # 변동성 분류 (일봉 기반, 하루 캐시)
            key = (code, market)
            if key not in self._classify_cache:
                df_daily = self._get_daily_cached(code, market)
                self._classify_cache[key] = self.strategy.classify_volatility(df_daily)
            mode = self._classify_cache[key]

            tp, sl = self._get_tp_sl(market, mode)
            df = self._get_data_for_mode(code, market, mode)
            sig = self.strategy.analyze(df, price, None, sl, tp, mode)

            if sig.action == "BUY":
                candidates.append((sig.confidence, stock, price, sig.reason, mode))

        # 신뢰도 높은 순으로 매수
        candidates.sort(key=lambda x: -x[0])
        for conf, stock, price, reason, mode in candidates:
            if self.portfolio.count_positions() >= max_pos:
                break
            ok = self.portfolio.buy(stock["code"], stock["name"], market, price, reason, mode=mode)
            if ok:
                self._log(f"[매수/{mode}] {stock['name']} {price:,.0f} | {reason}")
                if self.on_trade:
                    self.on_trade("BUY", stock["name"], price, reason)

    # ─── 헬퍼 ─────────────────────────────────────────

    def _get_tp_sl(self, market: str, mode: str) -> tuple[float, float]:
        if mode == "scalp":
            tp = config.SCALP_TAKE_PROFIT_KR if market == "KR" else config.SCALP_TAKE_PROFIT_US
            sl = config.SCALP_STOP_LOSS
        else:
            tp = float(self.db.get_setting("take_profit", config.SWING_TAKE_PROFIT))
            sl = float(self.db.get_setting("stop_loss",   config.SWING_STOP_LOSS))
        return tp, sl

    def _get_data_for_mode(self, code: str, market: str, mode: str):
        if mode == "scalp":
            return self._get_hourly_cached(code, market)
        return self._get_daily_cached(code, market)

    def _get_hourly_cached(self, code: str, market: str):
        key = (code, market)
        cached, ts = self._hourly_cache.get(key, (None, None))
        if cached is not None and ts and (datetime.now() - ts).seconds < _HOURLY_CACHE_SEC:
            return cached
        yf_code = (code + ".KS") if market == "KR" else code
        df = self.yahoo.get_hourly_data(yf_code, period="5d")
        self._hourly_cache[key] = (df, datetime.now())
        return df

    def _get_daily_cached(self, code: str, market: str):
        key = (code, market)
        cached, ts = self._daily_cache.get(key, (None, None))
        if cached is not None and ts and (datetime.now() - ts).seconds < _DAILY_CACHE_SEC:
            return cached
        if market == "KR":
            df = self.naver.get_historical_data(code, count=60)
        else:
            df = self.yahoo.get_historical_data(code, period="3mo")
        self._daily_cache[key] = (df, datetime.now())
        return df

    def _fetch_price(self, code: str, market: str, exchange_rate: float) -> dict | None:
        if market == "KR":
            return self.naver.get_current_price(code)
        info = self.yahoo.get_current_price(code)
        if info:
            info["price"] = round(info["price"] * exchange_rate, 0)
        return info

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        if self.on_log:
            self.on_log(f"[{ts}] {msg}")

    # ─── 일일 P&L 공개 속성 ───────────────────────────

    @property
    def daily_pnl(self) -> float:
        return self._daily_pnl

    @property
    def daily_trades(self) -> int:
        return self._daily_trades

    # ─── 시장 시간 ────────────────────────────────────

    @staticmethod
    def is_kr_market_open() -> bool:
        now = datetime.now(KST)
        if now.weekday() >= 5:
            return False
        return now.replace(hour=9, minute=0, second=0, microsecond=0) <= now <= \
               now.replace(hour=15, minute=30, second=0, microsecond=0)

    @staticmethod
    def is_us_market_open() -> bool:
        now = datetime.now(EST)
        if now.weekday() >= 5:
            return False
        return now.replace(hour=9, minute=30, second=0, microsecond=0) <= now <= \
               now.replace(hour=16, minute=0, second=0, microsecond=0)
