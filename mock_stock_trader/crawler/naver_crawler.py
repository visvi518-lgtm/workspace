import requests
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from datetime import datetime
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.naver.com",
}


class NaverCrawler:
    def get_current_price(self, code: str) -> dict | None:
        try:
            url = f"https://m.stock.naver.com/api/stock/{code}/basic"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            price = float(data.get("closePrice", "0").replace(",", ""))
            change = float(data.get("compareToPreviousClosePrice", "0").replace(",", ""))
            change_rate = float(data.get("fluctuationsRatio", "0"))
            name = data.get("stockName", code)
            return {
                "code": code,
                "name": name,
                "price": price,
                "change": change,
                "change_rate": change_rate,
            }
        except Exception:
            return None

    def get_historical_data(self, code: str, count: int = 60) -> pd.DataFrame | None:
        try:
            url = (
                f"https://fchart.stock.naver.com/sise.nhn"
                f"?symbol={code}&timeframe=day&count={count}&requestType=0"
            )
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
            records = []
            for item in root.iter("item"):
                raw = item.get("data", "")
                parts = raw.split("|")
                if len(parts) < 6:
                    continue
                date_str, close, open_, high, low, volume = parts[:6]
                records.append({
                    "date": datetime.strptime(date_str, "%Y%m%d"),
                    "open": float(open_) if open_ else np.nan,
                    "high": float(high) if high else np.nan,
                    "low": float(low) if low else np.nan,
                    "close": float(close) if close else np.nan,
                    "volume": float(volume) if volume else 0,
                })
            if not records:
                return None
            df = pd.DataFrame(records).dropna(subset=["close"])
            df = df.sort_values("date").reset_index(drop=True)
            return df
        except Exception:
            return None

    def get_exchange_rate(self) -> float:
        try:
            url = "https://m.stock.naver.com/api/forex/basic/FX_USDKRW"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            data = resp.json()
            return float(data.get("closePrice", "1350").replace(",", ""))
        except Exception:
            return 1350.0
