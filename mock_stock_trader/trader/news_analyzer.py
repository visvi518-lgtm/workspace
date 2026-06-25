"""
백테스트 결과에서 최대 낙폭/최고 수익 이벤트를 찾고
관련 뉴스와 기술적 원인을 분석합니다.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dataclasses import dataclass
import yfinance as yf

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://search.naver.com",
}


@dataclass
class NewsItem:
    title: str
    date: str = ""
    desc: str = ""
    url: str = ""
    source: str = ""


@dataclass
class StockSnippet:
    code: str
    name: str
    market: str
    trade_type: str
    profit: float = 0.0


@dataclass
class SectionAnalysis:
    date: str        # "YYYY-MM-DD" 또는 "YYYY-MM-DD HH:MM"
    rate: float
    stocks: list
    news: list
    tech_summary: str


@dataclass
class StockAnalysis:
    code: str
    name: str
    market: str
    profit: float
    profit_rate: float
    trade_count: int
    buy_date: str
    sell_date: str
    hold_days: int
    news: list
    summary: str


@dataclass
class EventAnalysis:
    mdd: SectionAnalysis
    peak: SectionAnalysis
    winners: list
    losers: list
    used_hourly: bool = False


class NewsAnalyzer:

    # ── 뉴스 수집 ─────────────────────────────────────────────

    def fetch_kr_news(self, stock_name: str, date_str: str, window: int = 7) -> list:
        """Naver 뉴스 검색 (날짜 기준 ±window일)"""
        results = []
        try:
            d = datetime.strptime(date_str[:10], "%Y-%m-%d")
            ds = (d - timedelta(days=window)).strftime("%Y.%m.%d")
            de = (d + timedelta(days=window)).strftime("%Y.%m.%d")
            q = requests.utils.quote(f"{stock_name} 주가")
            url = (
                f"https://search.naver.com/search.naver"
                f"?where=news&query={q}&pd=3&ds={ds}&de={de}&sort=1"
            )
            resp = requests.get(url, headers=HEADERS, timeout=12)
            soup = BeautifulSoup(resp.text, "html.parser")

            # 여러 selector 패턴 시도
            items_found = (
                soup.select("ul.list_news li.bx")
                or soup.select(".news_area")
                or soup.select("div.news_wrap")
                or soup.select("li[id^='sp_nws']")
            )

            for el in items_found[:8]:
                title_el = (
                    el.select_one("a.news_tit")
                    or el.select_one(".news_tit")
                    or el.select_one("a.title")
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                href  = title_el.get("href", "")

                date_el = (
                    el.select_one("span.is_time")
                    or el.select_one(".info_group .date")
                    or el.select_one("span.date")
                    or el.select_one(".time")
                )
                date_val = date_el.get_text(strip=True) if date_el else ""

                desc_el = (
                    el.select_one(".dsc_wrap")
                    or el.select_one(".api_txt_lines")
                    or el.select_one(".news_dsc")
                )
                desc = desc_el.get_text(strip=True)[:160] if desc_el else ""

                if title:
                    results.append(NewsItem(
                        title=title, date=date_val,
                        desc=desc, url=href, source="Naver",
                    ))

            # 중복 제거
            seen, unique = set(), []
            for item in results:
                if item.title not in seen:
                    seen.add(item.title)
                    unique.append(item)
            return unique

        except Exception:
            return []

    def fetch_us_news(self, ticker_code: str) -> list:
        """Yahoo Finance 뉴스 (최근)"""
        try:
            raw = yf.Ticker(ticker_code).news or []
            items = []
            for n in raw[:6]:
                content = n.get("content", {}) or {}
                title   = n.get("title") or content.get("title", "")
                url     = n.get("link") or (content.get("canonicalUrl") or {}).get("url", "")
                pub     = n.get("providerPublishTime")
                date_s  = ""
                if pub:
                    try:
                        date_s = datetime.fromtimestamp(pub).strftime("%Y.%m.%d")
                    except Exception:
                        pass
                if title:
                    items.append(NewsItem(title=title, date=date_s, url=url, source="Yahoo Finance"))
            return items
        except Exception:
            return []

    # ── 메인 분석 ─────────────────────────────────────────────

    def analyze(self, result) -> EventAnalysis:
        used_hourly = getattr(result, "used_hourly", False)

        # 최대 낙폭 / 최고 수익 날짜·시간 탐색
        if used_hourly and result.hourly_history:
            mdd_dt, mdd_rate = self._find_mdd(result.hourly_history, result.initial_capital, key="datetime")
            peak_dt, peak_rate = self._find_peak(result.hourly_history, result.initial_capital, key="datetime")
        else:
            mdd_dt, mdd_rate = self._find_mdd(result.portfolio_history, result.initial_capital, key="date")
            peak_dt, peak_rate = self._find_peak(result.portfolio_history, result.initial_capital, key="date")

        # 해당 시점 주변 거래 종목
        mdd_stocks  = self._stocks_near(mdd_dt,  result.trades)
        peak_stocks = self._stocks_near(peak_dt, result.trades)

        # 뉴스 수집
        mdd_news  = self._gather_news(mdd_stocks,  mdd_dt[:10])
        peak_news = self._gather_news(peak_stocks, peak_dt[:10])

        # 기술적 요약
        mdd_tech  = self._tech_summary(mdd_dt,  result, "낙폭",  used_hourly)
        peak_tech = self._tech_summary(peak_dt, result, "수익",  used_hourly)

        # 종목별 상위/하위
        perfs = sorted(result.stock_performances, key=lambda x: x["profit"])
        n = len(perfs)
        if n == 0:
            winners, losers = [], []
        elif n == 1:
            winners = self._build_stock_analyses(perfs, result.trades)
            losers  = []
        else:
            split   = min(3, max(1, n // 2))
            losers  = self._build_stock_analyses(perfs[:split], result.trades)
            winners = self._build_stock_analyses(list(reversed(perfs))[:split], result.trades)

        return EventAnalysis(
            mdd=SectionAnalysis(
                date=mdd_dt, rate=mdd_rate,
                stocks=mdd_stocks, news=mdd_news, tech_summary=mdd_tech,
            ),
            peak=SectionAnalysis(
                date=peak_dt, rate=peak_rate,
                stocks=peak_stocks, news=peak_news, tech_summary=peak_tech,
            ),
            winners=winners,
            losers=losers,
            used_hourly=used_hourly,
        )

    # ── 헬퍼 ──────────────────────────────────────────────────

    def _find_mdd(self, history, initial, key="date"):
        if not history:
            return "", 0.0
        peak = initial
        mdd_rate, mdd_dt = 0.0, history[0][key]
        for h in history:
            v = h["value"]
            if v > peak:
                peak = v
            if peak > 0:
                dd = (v - peak) / peak * 100
                if dd < mdd_rate:
                    mdd_rate, mdd_dt = dd, h[key]
        return mdd_dt, mdd_rate

    def _find_peak(self, history, initial, key="date"):
        if not history:
            return "", 0.0
        best_rate, best_dt = -999.0, history[0][key]
        for h in history:
            rate = (h["value"] - initial) / initial * 100
            if rate > best_rate:
                best_rate, best_dt = rate, h[key]
        return best_dt, best_rate

    def _stocks_near(self, dt_str: str, trades: list, window_h: int = 6) -> list:
        """dt_str 주변 ±window_h 시간 이내 거래 종목"""
        if not dt_str:
            return []
        try:
            base = datetime.strptime(dt_str[:16], "%Y-%m-%d %H:%M")
        except Exception:
            try:
                base = datetime.strptime(dt_str[:10], "%Y-%m-%d")
            except Exception:
                return []
        seen, result = set(), []
        for t in trades:
            try:
                td = datetime.strptime(f"{t.date} {getattr(t, 'time', '09:00')}", "%Y-%m-%d %H:%M")
            except Exception:
                continue
            diff_h = abs((td - base).total_seconds()) / 3600
            if diff_h <= window_h:
                key = (t.code, t.market)
                if key not in seen:
                    seen.add(key)
                    result.append(StockSnippet(
                        code=t.code, name=t.name, market=t.market,
                        trade_type=t.trade_type, profit=t.profit or 0.0,
                    ))
        return result[:6]

    def _gather_news(self, stocks: list, date_str: str) -> list:
        news, seen = [], set()
        for s in stocks[:3]:
            items = (
                self.fetch_kr_news(s.name, date_str)
                if s.market == "KR"
                else self.fetch_us_news(s.code)
            )
            for item in items[:4]:
                if item.title not in seen:
                    seen.add(item.title)
                    news.append(item)
        return news[:8]

    def _tech_summary(self, dt_str: str, result, label: str, used_hourly: bool) -> str:
        if not dt_str:
            return "분석 데이터 없음"
        try:
            base = datetime.strptime(dt_str[:16], "%Y-%m-%d %H:%M")
        except Exception:
            try:
                base = datetime.strptime(dt_str[:10], "%Y-%m-%d")
            except Exception:
                return "날짜 파싱 오류"

        window_h = 12 if used_hourly else 24 * 5
        nearby = []
        for t in result.trades:
            try:
                td = datetime.strptime(f"{t.date} {getattr(t, 'time', '09:00')}", "%Y-%m-%d %H:%M")
            except Exception:
                continue
            if abs((td - base).total_seconds()) / 3600 <= window_h:
                nearby.append(t)

        sells = [t for t in nearby if t.trade_type == "SELL" and t.profit is not None]
        if not sells:
            window_str = f"±{window_h}시간" if used_hourly else "±5일"
            return f"기준 시점 {window_str} 이내 매도 거래 없음\n(미청산 포지션 평가손익으로 낙폭/수익 발생)"

        total = sum(t.profit for t in sells)
        wins  = len([t for t in sells if t.profit >= 0])
        losses = len(sells) - wins

        if label == "낙폭":
            cause = (
                "손절 집중 발동 → 시장 전반 급락 또는 급격한 변동성 확대"
                if losses >= wins
                else "익절 후 미보유 상태에서 평가손 확대"
            )
        else:
            cause = (
                "복수 종목 동시 익절 → 전략 신호 집중 포착 구간"
                if wins >= losses
                else "일부 종목 대규모 익절로 포트폴리오 최고치 기록"
            )

        time_label = f"±{window_h}시간" if used_hourly else "±5일"
        return (
            f"기준: {dt_str}  |  {time_label} 내 {len(nearby)}건 거래\n"
            f"매도 {len(sells)}건 → 수익 {wins}건 / 손실 {losses}건\n"
            f"구간 실현손익 합계: {total:+,.0f}원\n"
            f"원인 분석: {cause}"
        )

    def _build_stock_analyses(self, perfs: list, all_trades: list) -> list:
        result = []
        for p in perfs:
            trades = [t for t in all_trades if t.code == p["code"]]
            buys   = [t for t in trades if t.trade_type == "BUY"]
            sells  = [t for t in trades if t.trade_type == "SELL"]

            buy_date  = f"{buys[0].date}  {getattr(buys[0], 'time', '')}"  if buys  else ""
            sell_date = f"{sells[-1].date}  {getattr(sells[-1], 'time', '')}" if sells else ""
            hold_days = 0
            if buys and sells:
                try:
                    hold_days = (
                        datetime.strptime(sells[-1].date, "%Y-%m-%d") -
                        datetime.strptime(buys[0].date, "%Y-%m-%d")
                    ).days
                except Exception:
                    pass

            ref_date = buys[0].date if buys else (sells[-1].date if sells else "")
            news = (
                self.fetch_kr_news(p["name"], ref_date)
                if p["market"] == "KR"
                else self.fetch_us_news(p["code"])
            )

            total_pnl = sum(t.profit for t in sells if t.profit is not None)
            cause = (
                "전략 신호 적중 → 목표 수익 달성 (익절 발동)"
                if p["profit"] >= 0
                else "손절 발동 또는 하락 신호 후 매도"
            )

            summary = (
                f"매수: {buy_date.strip()}  →  매도: {sell_date.strip()}  (보유 {hold_days}일)\n"
                f"총 {len(trades)}건 거래  |  실현손익 {total_pnl:+,.0f}원\n"
                f"원인 분석: {cause}"
            )

            result.append(StockAnalysis(
                code=p["code"], name=p["name"], market=p["market"],
                profit=p["profit"], profit_rate=p["profit_rate"],
                trade_count=len(trades),
                buy_date=buy_date.strip(), sell_date=sell_date.strip(),
                hold_days=hold_days, news=news[:5], summary=summary,
            ))
        return result
