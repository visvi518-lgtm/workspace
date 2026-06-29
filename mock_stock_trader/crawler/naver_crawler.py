"""Naver 증권 — 현재가 조회"""
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


class NaverCrawler:

    def get_price(self, code: str) -> float | None:
        """종목 코드에서 .KS / .KQ 제거 후 Naver API 조회"""
        raw_code = code.replace(".KS", "").replace(".KQ", "").replace(".KR", "")
        try:
            url  = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{raw_code}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            data = resp.json()
            price = data.get("datas", [{}])[0].get("closePrice") or \
                    data.get("datas", [{}])[0].get("currentPrice")
            if price:
                return float(str(price).replace(",", ""))
        except Exception:
            pass

        # fallback: 시세 API
        try:
            url  = f"https://m.stock.naver.com/api/stock/{raw_code}/price"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            data = resp.json()
            p    = data.get("closePrice") or data.get("currentPrice")
            if p:
                return float(str(p).replace(",", ""))
        except Exception:
            pass
        return None

    def get_prices(self, codes: list[str]) -> dict[str, float]:
        result = {}
        for code in codes:
            price = self.get_price(code)
            if price:
                result[code] = price
        return result
