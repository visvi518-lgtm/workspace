import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Signal:
    action: str         # 'BUY' | 'SELL' | 'HOLD'
    reason: str
    confidence: float
    mode: str = "swing" # 'scalp' | 'swing'
    indicators: dict = field(default_factory=dict)


class TechnicalStrategy:

    SCALP_ATR_THRESHOLD   = 0.020
    SCALP_RANGE_THRESHOLD = 0.025

    # ──────────────────────────────────────────────────
    # 변동성 분류: 일봉 ATR/가격 비율 기반
    # ──────────────────────────────────────────────────
    def classify_volatility(self, df_daily: pd.DataFrame) -> str:
        if df_daily is None or len(df_daily) < 10:
            return "swing"
        closes = df_daily["close"].values[-20:].astype(float)
        highs  = df_daily["high"].values[-20:].astype(float)
        lows   = df_daily["low"].values[-20:].astype(float)

        tr_list = []
        for i in range(1, len(closes)):
            h, l, pc = highs[i], lows[i], closes[i - 1]
            tr_list.append(max(h - l, abs(h - pc), abs(l - pc)))

        if not tr_list or closes[-1] == 0:
            return "swing"

        atr_ratio   = np.mean(tr_list) / closes[-1]
        daily_range = np.mean(np.where(closes > 0, (highs - lows) / closes, 0))

        if atr_ratio >= self.SCALP_ATR_THRESHOLD or daily_range >= self.SCALP_RANGE_THRESHOLD:
            return "scalp"
        return "swing"

    # ──────────────────────────────────────────────────
    # 통합 진입점
    # ──────────────────────────────────────────────────
    def analyze(
        self,
        df: pd.DataFrame,
        current_price: float,
        avg_price: Optional[float] = None,
        stop_loss: float = -0.03,
        take_profit: float = 0.025,
        mode: str = "swing",
    ) -> Signal:
        if mode == "scalp":
            return self._analyze_scalp(df, current_price, avg_price, stop_loss, take_profit)
        return self._analyze_swing(df, current_price, avg_price, stop_loss, take_profit)

    # ──────────────────────────────────────────────────
    # 스캘핑 전략  (1시간봉 / 빠른 지표)
    # 목표: 단타 수익 반복으로 복리 극대화
    #   KR: TP +1.0% → 수수료 후 순수익 ~0.75%
    #   US: TP +1.5% → 수수료 후 순수익 ~1.0%
    # ──────────────────────────────────────────────────
    def _analyze_scalp(self, df, price, avg_price, stop_loss, take_profit) -> Signal:
        if df is None or len(df) < 15:
            return Signal("HOLD", "데이터 부족", 0.0, "scalp")

        c = df["close"].values.astype(float)
        v = df["volume"].values.astype(float)
        h = df["high"].values.astype(float)
        lo = df["low"].values.astype(float)

        rsi          = self._calc_rsi(c, 9)          # 빠른 RSI(9)
        _, _, hist   = self._calc_macd(c, 5, 13, 5)  # 빠른 MACD(5,13,5)
        upper, mid, lower = self._calc_bollinger(c, 10, 2)

        avg_v = np.mean(v[-20:]) if len(v) >= 20 else (np.mean(v) or 1)
        vol_r = v[-1] / avg_v if avg_v > 0 else 1.0

        up3   = len(c) >= 3 and c[-1] > c[-2] > c[-3]
        down3 = len(c) >= 3 and c[-1] < c[-2] < c[-3]
        chg1  = (c[-1] - c[-2]) / c[-2] if c[-2] > 0 else 0
        chg3  = (c[-1] - c[-4]) / c[-4] if len(c) >= 4 and c[-4] > 0 else 0

        inds = {
            "rsi": round(float(rsi[-1]), 2),
            "macd_hist": round(float(hist[-1]), 4),
            "vol_ratio": round(float(vol_r), 2),
            "chg_1h": round(chg1 * 100, 3),
            "chg_3h": round(chg3 * 100, 3),
        }

        # ① 손절 / 익절 (최우선)
        if avg_price and avg_price > 0:
            r = (price - avg_price) / avg_price
            if r <= stop_loss:
                return Signal("SELL", f"[스캘핑] 손절 ({r*100:.2f}%)", 1.0, "scalp", inds)
            if r >= take_profit:
                return Signal("SELL", f"[스캘핑] 익절 달성 ({r*100:.2f}%)", 1.0, "scalp", inds)

        # ② 매도 신호 (보유 중)
        if avg_price:
            sell_r = []
            if rsi[-1] > 72:
                sell_r.append(f"RSI 단기과매수({rsi[-1]:.1f})")
            if len(hist) >= 2 and hist[-2] > 0 and hist[-1] < 0:
                sell_r.append("단기MACD 하락반전")
            if price > upper[-1] * 1.004 and down3:
                sell_r.append("볼린저상단이탈+하락모멘텀")
            if vol_r > 3.0 and chg1 < -0.008:
                sell_r.append(f"거래량폭증+급락({chg1*100:.2f}%)")
            if sell_r:
                return Signal("SELL", "[스캘핑] " + " + ".join(sell_r), 0.9, "scalp", inds)

        # ③ 매수 신호 (2개 이상 조건 충족)
        buy_r = []

        # 조건A: RSI(9) 과매도 회복
        if rsi[-1] < 33 and len(rsi) >= 2 and rsi[-1] > rsi[-2]:
            buy_r.append(f"RSI단기과매도반등({rsi[-1]:.1f}↑)")

        # 조건B: 빠른 MACD 골든크로스
        if len(hist) >= 2 and hist[-2] < 0 and hist[-1] > 0:
            buy_r.append("단기MACD골든크로스")

        # 조건C: 볼린저 하단 반등 + 상승 모멘텀
        if price <= lower[-1] * 1.006 and up3:
            buy_r.append("볼린저하단반등")

        # 조건D: 거래량 폭증 + 급등 (강한 매수세)
        if vol_r > 2.5 and chg1 > 0.004:
            buy_r.append(f"거래량폭증({vol_r:.1f}배)+급등({chg1*100:.2f}%)")

        # 조건E: 단기 낙폭과대 후 반전 (V자 반등)
        if chg3 < -0.018 and chg1 > 0.006 and rsi[-1] < 48:
            buy_r.append(f"V자반등({chg3*100:.1f}%→+{chg1*100:.2f}%)")

        # 조건F: 볼린저 중심선 상향 돌파 + 거래량
        if len(c) >= 2 and c[-2] < mid[-2] and c[-1] > mid[-1] and vol_r > 1.5:
            buy_r.append("중심선돌파+거래량확인")

        if len(buy_r) >= 2:
            conf = min(len(buy_r) * 0.25, 1.0)
            return Signal("BUY", "[스캘핑] " + " + ".join(buy_r), conf, "scalp", inds)

        return Signal("HOLD", "[스캘핑] 진입조건 미충족", 0.0, "scalp", inds)

    # ──────────────────────────────────────────────────
    # 스윙 전략  (일봉 / 표준 지표)
    # 목표: 3% 이상 수익 구간 포착 후 보유
    # ──────────────────────────────────────────────────
    def _analyze_swing(self, df, price, avg_price, stop_loss, take_profit) -> Signal:
        if df is None or len(df) < 30:
            return Signal("HOLD", "데이터 부족", 0.0, "swing")

        c = df["close"].values.astype(float)
        v = df["volume"].values.astype(float)

        rsi          = self._calc_rsi(c, 14)
        _, _, hist   = self._calc_macd(c)
        upper, mid, lower = self._calc_bollinger(c, 20, 2)
        avg_v = np.mean(v[-20:]) or 1
        vol_r = v[-1] / avg_v

        inds = {
            "rsi": round(float(rsi[-1]), 2),
            "macd_hist": round(float(hist[-1]), 4),
            "vol_ratio": round(vol_r, 2),
        }

        if avg_price and avg_price > 0:
            r = (price - avg_price) / avg_price
            if r <= stop_loss:
                return Signal("SELL", f"[스윙] 손절 ({r*100:.1f}%)", 1.0, "swing", inds)
            if r >= take_profit:
                return Signal("SELL", f"[스윙] 익절 달성 ({r*100:.1f}%)", 1.0, "swing", inds)

        sell_r = []
        if rsi[-1] > 70:
            sell_r.append(f"RSI 과매수({rsi[-1]:.1f})")
        if len(hist) >= 2 and hist[-2] > 0 and hist[-1] < 0:
            sell_r.append("MACD 하락전환")
        if price > upper[-1]:
            sell_r.append("볼린저 상단이탈")

        if sell_r and avg_price:
            return Signal("SELL", "[스윙] " + " + ".join(sell_r), 0.85, "swing", inds)

        buy_r = []
        if rsi[-1] < 35 and len(rsi) >= 2 and rsi[-1] > rsi[-2]:
            buy_r.append(f"RSI 과매도회복({rsi[-1]:.1f}↑)")
        if len(hist) >= 2 and hist[-2] < 0 and hist[-1] > 0:
            buy_r.append("MACD 골든크로스")
        if price <= lower[-1] * 1.012:
            buy_r.append("볼린저 하단반등")
        if vol_r > 1.5 and c[-1] > c[-2]:
            buy_r.append(f"거래량급증({vol_r:.1f}배)+상승")
        if len(rsi) >= 3 and rsi[-3] < rsi[-2] < rsi[-1] and rsi[-1] < 50:
            buy_r.append(f"RSI 상승추세({rsi[-1]:.1f})")

        if len(buy_r) >= 2:
            conf = min(len(buy_r) * 0.28, 1.0)
            return Signal("BUY", "[스윙] " + " + ".join(buy_r), conf, "swing", inds)

        return Signal("HOLD", "[스윙] 매매조건 미충족", 0.0, "swing", inds)

    # ─── 지표 계산 ────────────────────────────────────

    def _calc_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        deltas = np.diff(prices)
        gains  = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        ag = np.convolve(gains,  np.ones(period) / period, "valid")
        al = np.convolve(losses, np.ones(period) / period, "valid")
        with np.errstate(divide="ignore", invalid="ignore"):
            rs = np.where(al == 0, 100.0, ag / al)
        return np.concatenate([np.full(period, np.nan), 100 - (100 / (1 + rs))])

    def _calc_macd(self, prices: np.ndarray, fast=12, slow=26, signal=9):
        ef = self._ema(prices, fast)
        es = self._ema(prices, slow)
        ml = ef - es
        sl = self._ema(ml, signal)
        return ml, sl, ml - sl

    def _calc_bollinger(self, prices: np.ndarray, period=20, std_mult=2):
        n = len(prices)
        mid = np.array([np.mean(prices[max(0, i - period + 1):i + 1]) for i in range(n)])
        std = np.array([np.std(prices[max(0, i - period + 1):i + 1])  for i in range(n)])
        return mid + std_mult * std, mid, mid - std_mult * std

    def _ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        k = 2 / (period + 1)
        ema = np.empty(len(prices))
        ema[0] = prices[0]
        for i in range(1, len(prices)):
            ema[i] = prices[i] * k + ema[i - 1] * (1 - k)
        return ema
