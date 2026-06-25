import yfinance as yf
import pandas as pd


def _normalize(df: pd.DataFrame) -> pd.DataFrame | None:
    if df is None or df.empty:
        return None
    df = df.reset_index()
    df.columns = [str(c).lower() for c in df.columns]
    for alias in ("datetime", "index"):
        if alias in df.columns and "date" not in df.columns:
            df = df.rename(columns={alias: "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    cols = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in df.columns]
    return df[cols].dropna(subset=["close"])


class YahooCrawler:
    def get_current_price(self, code: str) -> dict | None:
        try:
            ticker = yf.Ticker(code)
            info = ticker.fast_info
            price = info.last_price
            prev_close = info.previous_close
            if not price or not prev_close:
                return None
            change = price - prev_close
            change_rate = (change / prev_close) * 100
            return {
                "code": code,
                "name": code,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_rate": round(change_rate, 2),
            }
        except Exception:
            return None

    def get_historical_data(self, code: str, period: str = "3mo") -> pd.DataFrame | None:
        try:
            df = yf.Ticker(code).history(period=period)
            return _normalize(df)
        except Exception:
            return None

    def get_hourly_data(self, code: str, period: str = "5d") -> pd.DataFrame | None:
        """1시간봉 데이터 (스캘핑 신호 계산용, 최대 730일)"""
        try:
            df = yf.Ticker(code).history(period=period, interval="1h")
            return _normalize(df)
        except Exception:
            return None

    def get_range_data(self, code: str, start: str, end: str,
                       interval: str = "1d") -> pd.DataFrame | None:
        """백테스트용 날짜 범위 데이터"""
        try:
            df = yf.Ticker(code).history(start=start, end=end, interval=interval)
            return _normalize(df)
        except Exception:
            return None
