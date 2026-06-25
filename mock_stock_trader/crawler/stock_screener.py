"""
동적 종목 풀 구성
- KR: Naver Finance 시가총액 상위 100 → 최근 거래량 기준 선별
- US: S&P500 + NASDAQ100 유니버스 → 최근 거래량 기준 선별
결과는 당일 캐싱됩니다.
"""
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# S&P500 + NASDAQ100 유니버스 (분기별 수동 갱신)
US_UNIVERSE = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO",
    "JPM","V","MA","BAC","WFC","GS","MS","AXP","BLK","C","USB","PNC",
    "UNH","LLY","JNJ","ABT","TMO","MRK","ABBV","DHR","AMGN","MDT","GILD","VRTX","REGN","ISRG","SYK","BSX","ZTS","EW",
    "HD","MCD","SBUX","NKE","LOW","TJX","COST","WMT","PG","KO","PEP","MDLZ","CL","EL","PM","MO",
    "XOM","CVX","COP","EOG","SLB","PSX","VLO","MPC",
    "CAT","DE","HON","RTX","GE","UPS","BA","LMT","NOC","EMR","ETN","ITW","MMM",
    "ORCL","CRM","ADBE","QCOM","TXN","AMD","INTC","IBM","CSCO","AMAT","ADI","INTU","NOW","SNPS","CDNS","MU","LRCX","KLAC",
    "VZ","T","DIS","NFLX","CMCSA","PARA","WBD",
    "BRK-B","SPGI","MCO","ICE","CME","CB","AON","MMC",
    "NEE","SO","DUK","EXC","SRE","AEP","D",
    "PLD","AMT","EQIX","CCI","PSA","CBRE","ARE","O",
    "SHOP","PYPL","UBER","ABNB","DKNG","PLTR","SNOW","CRWD","PANW","ZS","DDOG","COIN","HOOD","RBLX","ROKU",
]

# KR 고정 fallback (Naver API 실패 시)
KR_FALLBACK = [
    {"code":"005930","name":"삼성전자","yf_code":"005930.KS"},
    {"code":"000660","name":"SK하이닉스","yf_code":"000660.KS"},
    {"code":"373220","name":"LG에너지솔루션","yf_code":"373220.KS"},
    {"code":"207940","name":"삼성바이오로직스","yf_code":"207940.KS"},
    {"code":"005380","name":"현대차","yf_code":"005380.KS"},
    {"code":"035420","name":"NAVER","yf_code":"035420.KS"},
    {"code":"035720","name":"카카오","yf_code":"035720.KS"},
    {"code":"000270","name":"기아","yf_code":"000270.KS"},
    {"code":"005490","name":"POSCO홀딩스","yf_code":"005490.KS"},
    {"code":"068270","name":"셀트리온","yf_code":"068270.KS"},
    {"code":"006400","name":"삼성SDI","yf_code":"006400.KS"},
    {"code":"105560","name":"KB금융","yf_code":"105560.KS"},
    {"code":"055550","name":"신한지주","yf_code":"055550.KS"},
    {"code":"086790","name":"하나금융지주","yf_code":"086790.KS"},
    {"code":"051910","name":"LG화학","yf_code":"051910.KS"},
    {"code":"066570","name":"LG전자","yf_code":"066570.KS"},
    {"code":"096770","name":"SK이노베이션","yf_code":"096770.KS"},
    {"code":"034730","name":"SK","yf_code":"034730.KS"},
    {"code":"015760","name":"한국전력","yf_code":"015760.KS"},
    {"code":"003550","name":"LG","yf_code":"003550.KS"},
    {"code":"032830","name":"삼성생명","yf_code":"032830.KS"},
    {"code":"017670","name":"SK텔레콤","yf_code":"017670.KS"},
    {"code":"030200","name":"KT","yf_code":"030200.KS"},
    {"code":"009150","name":"삼성전기","yf_code":"009150.KS"},
    {"code":"028260","name":"삼성물산","yf_code":"028260.KS"},
    {"code":"010130","name":"고려아연","yf_code":"010130.KS"},
    {"code":"003670","name":"포스코퓨처엠","yf_code":"003670.KS"},
    {"code":"011170","name":"롯데케미칼","yf_code":"011170.KS"},
    {"code":"047050","name":"포스코인터내셔널","yf_code":"047050.KS"},
    {"code":"000810","name":"삼성화재","yf_code":"000810.KS"},
    {"code":"033780","name":"KT&G","yf_code":"033780.KS"},
    {"code":"010950","name":"S-Oil","yf_code":"010950.KS"},
    {"code":"090430","name":"아모레퍼시픽","yf_code":"090430.KS"},
    {"code":"024110","name":"기업은행","yf_code":"024110.KS"},
    {"code":"018260","name":"삼성에스디에스","yf_code":"018260.KS"},
    {"code":"034020","name":"두산에너빌리티","yf_code":"034020.KS"},
    {"code":"000100","name":"유한양행","yf_code":"000100.KS"},
    {"code":"000720","name":"현대건설","yf_code":"000720.KS"},
    {"code":"047810","name":"한국항공우주","yf_code":"047810.KS"},
    {"code":"006800","name":"미래에셋증권","yf_code":"006800.KS"},
]


class StockScreener:
    """당일 캐싱 포함 동적 종목 선별기"""

    def __init__(self):
        self._kr_cache: list | None = None
        self._us_cache: list | None = None
        self._cache_date: object | None = None

    def _cache_valid(self) -> bool:
        return self._cache_date == datetime.now().date()

    # ── KR ──────────────────────────────────────────────────

    def get_kr_universe(self, count: int = 100) -> list[dict]:
        """Naver Finance 시가총액 상위 종목 수집"""
        stocks = []
        try:
            for page in range(1, (count // 50) + 2):
                url = (
                    "https://m.stock.naver.com/api/stocks/market-cap"
                    f"?market=KOSPI&page={page}&pageSize=50"
                )
                r = requests.get(url, headers=HEADERS, timeout=8)
                body = r.json()
                items = body if isinstance(body, list) else body.get("stocks", body.get("data", []))
                if not items:
                    break
                for s in items:
                    code = s.get("itemCode") or s.get("code", "")
                    name = s.get("stockName") or s.get("name", "")
                    if code and name:
                        stocks.append({
                            "code": code.strip(),
                            "name": name.strip(),
                            "yf_code": f"{code.strip()}.KS",
                        })
                if len(stocks) >= count:
                    break
        except Exception:
            pass

        if len(stocks) < 10:
            return KR_FALLBACK[:]
        return stocks[:count]

    def get_kr_by_volume(self, pool_size: int = 100, select_n: int = 40) -> list[dict]:
        """KR 상위 pool_size 중 거래량 상위 select_n 반환"""
        if self._cache_valid() and self._kr_cache:
            return self._kr_cache

        universe = self.get_kr_universe(pool_size)
        tickers = [s["yf_code"] for s in universe]
        vol_map = self._batch_volume(tickers)

        scored = sorted(
            ((vol_map.get(s["yf_code"], 0), s) for s in universe),
            key=lambda x: -x[0],
        )
        result = [s for _, s in scored[:select_n]]
        if not result:
            result = KR_FALLBACK[:select_n]

        self._kr_cache = result
        self._cache_date = datetime.now().date()
        return result

    # ── US ──────────────────────────────────────────────────

    def get_us_by_volume(self, select_n: int = 40) -> list[dict]:
        """US 유니버스 중 거래량 상위 select_n 반환"""
        if self._cache_valid() and self._us_cache:
            return self._us_cache

        vol_map = self._batch_volume(US_UNIVERSE)

        # 종목명 조회 (yfinance fast_info)
        name_map: dict[str, str] = {}
        for code in US_UNIVERSE:
            try:
                fi = yf.Ticker(code).fast_info
                name_map[code] = getattr(fi, "shortName", None) or code
            except Exception:
                name_map[code] = code

        scored = sorted(
            ((vol_map.get(code, 0), code) for code in US_UNIVERSE),
            key=lambda x: -x[0],
        )
        result = [
            {"code": code, "name": name_map.get(code, code), "yf_code": code}
            for _, code in scored[:select_n]
        ]

        self._us_cache = result
        self._cache_date = datetime.now().date()
        return result

    # ── 통합 풀 ─────────────────────────────────────────────

    def get_pool(self, use_kr: bool = True, use_us: bool = True,
                 kr_n: int = 40, us_n: int = 40) -> list[dict]:
        """자동매매 / 백테스트 공용 종목 풀"""
        pool = []
        if use_kr:
            for s in self.get_kr_by_volume(select_n=kr_n):
                pool.append({**s, "market": "KR"})
        if use_us:
            for s in self.get_us_by_volume(select_n=us_n):
                pool.append({**s, "market": "US"})
        return pool

    # ── 내부 헬퍼 ────────────────────────────────────────────

    def _batch_volume(self, tickers: list[str]) -> dict[str, float]:
        """yfinance 배치 다운로드로 최근 5일 평균 거래량 계산"""
        vol_map: dict[str, float] = {}
        if not tickers:
            return vol_map
        try:
            raw = yf.download(
                tickers=tickers,
                period="5d",
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
            if isinstance(raw.columns, pd.MultiIndex):
                # 복수 티커
                for tkr in tickers:
                    try:
                        vol = raw[tkr]["Volume"].mean()
                        if not pd.isna(vol):
                            vol_map[tkr] = float(vol)
                    except Exception:
                        pass
            else:
                # 단일 티커
                vol = raw["Volume"].mean() if "Volume" in raw.columns else 0
                if tickers and not pd.isna(vol):
                    vol_map[tickers[0]] = float(vol)
        except Exception:
            pass
        return vol_map


# 전역 싱글톤
_screener = StockScreener()


def get_pool(use_kr: bool = True, use_us: bool = True,
             kr_n: int = 40, us_n: int = 40) -> list[dict]:
    return _screener.get_pool(use_kr=use_kr, use_us=use_us, kr_n=kr_n, us_n=us_n)
