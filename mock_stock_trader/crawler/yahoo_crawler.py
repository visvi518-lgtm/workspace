"""Yahoo Finance — 미국 주식 현재가 조회"""
import yfinance as yf


class YahooCrawler:

    def get_price(self, code: str) -> float | None:
        try:
            ticker = yf.Ticker(code)
            data   = ticker.fast_info
            price  = getattr(data, "last_price", None) or getattr(data, "regularMarketPrice", None)
            if price:
                return float(price)
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
