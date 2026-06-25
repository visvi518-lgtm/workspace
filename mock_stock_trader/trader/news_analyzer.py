"""
백테스트 결과에서 주요 이벤트(최대 낙폭 / 최고 수익) 날짜를 찾고
그 시점 주변의 뉴스와 기술적 원인을 분석합니다.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import yfinance as yf

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
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
    date: str
    rate: float
    stocks: list[StockSnippet]
    news: list[NewsItem]
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
    news: list[NewsItem]
    summary: str


@dataclass
class EventAnalysis:
    mdd: SectionAnalysis          # 최대 낙폭 이벤트
    peak: SectionAnalysis         # 최고 수익 이벤트
    winners: list[StockAnalysis]  # 수익 상위 종목
    losers: list[StockAnalysis]   # 손실 하위 종목


class NewsAnalyzer:

    # ── 뉴스 수집 ──────────────────────────────────────────────

    def fetch_kr_news(self, stock_name: str, date_str: str, window: int = 7) -> list[NewsItem]:
        """Naver 뉴스에서 특정 기간 주변 기사 검색"""
        try:
            d = datetime.strptime(date_str[:10], "%Y-%m-%d")
            ds = (d - timedelta(days=window)).strftime("%Y.%m.%d")
            de = (d + timedelta(days=window)).strftime("%Y.%m.%d")
            q = requests.utils.quote(f"{stock_name} 주가")
            url = (
                f"https://search.naver.com/search.naver"
                f"?where=news&query={q}&pd=3&ds={ds}&de={de}&sort=1"
            )
            resp = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")

            items = []
            selectors = [
                (".news_area", ".news_tit", ".dsc_wrap", ".info_group .is_time"),
                ("li.bx", "a.news_tit", ".api_txt_lines", "span.date"),
            ]
            for area_sel, title_sel, desc_sel, date_sel in selectors:
                found = soup.select(area_sel)
                if found:
                    for el in found[:7]:
                        t = el.select_one(title_sel)
                        if not t:
                            continue
                        d_el = el.select_one(date_sel)
                        desc_el = el.select_one(desc_sel)
                        items.append(NewsItem(
                            title=t.get_text(strip=True),
                            date=d_el.get_text(strip=True) if d_el else "",
                            desc=desc_el.get_text(strip=True)[:150] if desc_el else "",
                            url=t.get("href", ""),
                            source="Naver",
                        ))
                    break

            # 중복 제거
            seen, unique = set(), []
            for item in items:
                if item.title not in seen:
                    seen.add(item.title)
                    unique.append(item)
            return unique
        except Exception:
            return []

    def fetch_us_news(self, ticker_code: str) -> list[NewsItem]:
        """Yahoo Finance 뉴스 (최근 기사 기반)"""
        try:
            raw = yf.Ticker(ticker_code).news or []
            items = []
            for n in raw[:6]:
                # yfinance 버전에 따라 구조가 다름
                content = n.get("content", {})
                title = n.get("title") or content.get("title", "")
                url = n.get("link") or (content.get("canonicalUrl") or {}).get("url", "")
                pub = n.get("providerPublishTime")
                date_str = ""
                if pub:
                    try:
                        date_str = datetime.fromtimestamp(pub).strftime("%Y.%m.%d")
                    except Exception:
                        pass
                if title:
                    items.append(NewsItem(title=title, date=date_str, url=url, source="Yahoo Finance"))
            return items
        except Exception:
            return []

    # ── 메인 분석 ──────────────────────────────────────────────

    def analyze(self, result) -> EventAnalysis:
        # 핵심 날짜 탐색
        mdd_date, mdd_rate = self._find_mdd_date(result.portfolio_history, result.initial_capital)
        peak_date, peak_rate = self._find_peak_date(result.portfolio_history, result.initial_capital)

        # 해당 날짜 주변 거래 종목
        mdd_stocks = self._stocks_near(mdd_date, result.trades)
        peak_stocks = self._stocks_near(peak_date, result.trades)

        # 뉴스 수집
        mdd_news  = self._gather_news(mdd_stocks,  mdd_date)
        peak_news = self._gather_news(peak_stocks, peak_date)

        # 기술적 요약
        mdd_tech  = self._tech_summary(mdd_date,  result, "낙폭")
        peak_tech = self._tech_summary(peak_date, result, "수익")

        # 종목별 분석
        perfs = sorted(result.stock_performances, key=lambda x: x["profit"])
        winners = self._build_stock_analyses([p for p in reversed(perfs) if p["profit"] > 0][:3], result.trades)
        losers  = self._build_stock_analyses([p for p in perfs            if p["profit"] < 0][:3], result.trades)

        return EventAnalysis(
            mdd=SectionAnalysis(
                date=mdd_date, rate=mdd_rate,
                stocks=mdd_stocks, news=mdd_news, tech_summary=mdd_tech,
            ),
            peak=SectionAnalysis(
                date=peak_date, rate=peak_rate,
                stocks=peak_stocks, news=peak_news, tech_summary=peak_tech,
            ),
            winners=winners,
            losers=losers,
        )

    # ── 헬퍼 ───────────────────────────────────────────────────

    def _gather_news(self, stocks: list, date_str: str) -> list[NewsItem]:
        news, seen = [], set()
        for s in stocks[:3]:
            if s.market == "KR":
                items = self.fetch_kr_news(s.name, date_str)
            else:
                items = self.fetch_us_news(s.code)
            for item in items[:4]:
                if item.title not in seen:
                    seen.add(item.title)
                    news.append(item)
        return news[:8]

    def _build_stock_analyses(self, perfs: list, all_trades: list) -> list[StockAnalysis]:
        result = []
        for p in perfs:
            trades = [t for t in all_trades if t.code == p["code"]]
            buys  = [t for t in trades if t.trade_type == "BUY"]
            sells = [t for t in trades if t.trade_type == "SELL"]

            buy_date  = buys[0].date[:10]  if buys  else ""
            sell_date = sells[-1].date[:10] if sells else ""
            hold_days = 0
            if buy_date and sell_date:
                try:
                    hold_days = (
                        datetime.strptime(sell_date, "%Y-%m-%d") -
                        datetime.strptime(buy_date,  "%Y-%m-%d")
                    ).days
                except Exception:
                    pass

            # 뉴스: 매수 날짜 기준
            ref_date = buy_date if buy_date else sell_date
            if p["market"] == "KR":
                news = self.fetch_kr_news(p["name"], ref_date)
            else:
                news = self.fetch_us_news(p["code"])

            profits = [t.profit for t in sells if t.profit is not None]
            total_pnl = sum(profits)

            if p["profit"] > 0:
                cause = "전략 신호 적중 → 목표 수익 달성 (익절 발동)"
            else:
                cause = "손절 발동 또는 하락 신호 매도"

            summary = (
                f"매수 {buy_date} → 매도 {sell_date} (보유 {hold_days}일) | "
                f"거래 {len(trades)}건 | 실현손익 {total_pnl:+,.0f}원\n"
                f"원인 분석: {cause}"
            )

            result.append(StockAnalysis(
                code=p["code"], name=p["name"], market=p["market"],
                profit=p["profit"], profit_rate=p["profit_rate"],
                trade_count=len(trades),
                buy_date=buy_date, sell_date=sell_date, hold_days=hold_days,
                news=news[:5], summary=summary,
            ))
        return result

    def _find_mdd_date(self, history: list, initial: float) -> tuple[str, float]:
        if not history:
            return "", 0.0
        peak = initial
        mdd_rate, mdd_date = 0.0, history[0]["date"]
        for h in history:
            v = h["value"]
            if v > peak:
                peak = v
            if peak > 0:
                dd = (v - peak) / peak * 100
                if dd < mdd_rate:
                    mdd_rate, mdd_date = dd, h["date"]
        return mdd_date, mdd_rate

    def _find_peak_date(self, history: list, initial: float) -> tuple[str, float]:
        if not history:
            return "", 0.0
        best_rate, best_date = -999.0, history[0]["date"]
        for h in history:
            rate = (h["value"] - initial) / initial * 100
            if rate > best_rate:
                best_rate, best_date = rate, h["date"]
        return best_date, best_rate

    def _stocks_near(self, date_str: str, trades: list, window: int = 5) -> list[StockSnippet]:
        if not date_str:
            return []
        try:
            base = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except Exception:
            return []
        seen, result = set(), []
        for t in trades:
            try:
                td = datetime.strptime(t.date[:10], "%Y-%m-%d")
            except Exception:
                continue
            if abs((td - base).days) <= window:
                key = (t.code, t.market)
                if key not in seen:
                    seen.add(key)
                    result.append(StockSnippet(
                        code=t.code, name=t.name, market=t.market,
                        trade_type=t.trade_type, profit=t.profit or 0.0,
                    ))
        return result[:6]

    def _tech_summary(self, date_str: str, result, label: str) -> str:
        if not date_str:
            return "분석 데이터 없음"
        try:
            base = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except Exception:
            return "날짜 파싱 오류"

        nearby = [
            t for t in result.trades
            if abs((datetime.strptime(t.date[:10], "%Y-%m-%d") - base).days) <= 7
        ]
        sells = [t for t in nearby if t.trade_type == "SELL" and t.profit is not None]
        if not sells:
            return f"해당 날짜 ±7일 이내 매도 거래 없음\n(미청산 포지션 평가로 낙폭/수익 발생)"

        total   = sum(t.profit for t in sells)
        wins    = len([t for t in sells if t.profit >= 0])
        losses  = len([t for t in sells if t.profit < 0])

        if label == "낙폭":
            if losses >= wins:
                cause = "손절 집중 발동 → 시장 전반적 급락 또는 급격한 변동성 확대 구간"
            else:
                cause = "익절 이후 미보유 상태에서 포트폴리오 평가손 확대"
        else:
            if wins >= losses:
                cause = "복수 종목 동시 익절 성공 → 전략 신호 집중 포착 구간"
            else:
                cause = "일부 대형 익절로 포트폴리오 최고치 기록"

        lines = [
            f"기준일: {date_str[:10]}  |  ±7일 거래: {len(nearby)}건",
            f"매도 {len(sells)}건 → 수익 {wins}건 / 손실 {losses}건",
            f"구간 실현손익 합계: {total:+,.0f}원",
            f"원인 분석: {cause}",
        ]
        return "\n".join(lines)
