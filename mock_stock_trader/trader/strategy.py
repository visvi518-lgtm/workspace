"""기술적 분석 전략 — 스윙 / 스캘핑 신호 생성"""
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass


@dataclass
class Signal:
    action:     str    # "BUY" | "SELL" | "HOLD"
    confidence: float  # 0.0 ~ 1.0
    reason:     str


class TechnicalStrategy:

    # ── 변동성 분류 ───────────────────────────────────────────

    def classify_volatility(self, df: pd.DataFrame) -> str:
        """ATR/종가 > 2% 또는 일중변동폭 > 2.5% → 'scalp', 아니면 'swing'"""
        if len(df) < 14:
            return "swing"
        try:
            hl  = df["high"] - df["low"]
            atr = float(hl.tail(14).mean())
            price = float(df["close"].iloc[-1])
            if atr / price > 0.02:
                return "scalp"
            range_pct = float(((df["high"] - df["low"]) / df["close"]).tail(10).mean())
            if range_pct > 0.025:
                return "scalp"
        except Exception:
            pass
        return "swing"

    # ── 메인 신호 분석 ────────────────────────────────────────

    def analyze(
        self,
        df: pd.DataFrame,
        current_price: float,
        avg_price: float | None,
        stop_loss: float,
        take_profit: float,
        mode: str = "swing",
    ) -> Signal:
        if len(df) < 20:
            return Signal("HOLD", 0.0, "데이터 부족")

        if mode == "scalp":
            return self._scalp_signal(df, current_price, avg_price, stop_loss, take_profit)
        return self._swing_signal(df, current_price, avg_price, stop_loss, take_profit)

    # ── 스윙 신호 ─────────────────────────────────────────────

    def _swing_signal(self, df, price, avg_price, sl, tp) -> Signal:
        rsi  = self._rsi(df["close"], 14)
        macd, signal_line = self._macd(df["close"], 12, 26, 9)
        upper, lower = self._bb(df["close"], 20, 2.0)

        score = 0
        reasons = []

        # ── 매도 조건 (포지션 보유 시) ──
        if avg_price is not None:
            pnl_rate = (price - avg_price) / avg_price
            if pnl_rate <= sl:
                return Signal("SELL", 1.0, f"손절 ({pnl_rate*100:.1f}%)")
            if pnl_rate >= tp:
                return Signal("SELL", 1.0, f"익절 ({pnl_rate*100:.1f}%)")
            if rsi > 70:
                score += 1; reasons.append("RSI과매수")
            if macd < signal_line and macd < 0:
                score += 1; reasons.append("MACD하락")
            if price >= upper:
                score += 1; reasons.append("BB상단")
            if score >= 2:
                return Signal("SELL", score / 3, " | ".join(reasons))
            return Signal("HOLD", 0.0, "유지")

        # ── 매수 조건 ──
        if rsi < 35:
            score += 2; reasons.append("RSI과매도")
        elif rsi < 45:
            score += 1; reasons.append("RSI중립하")
        if macd > signal_line and macd > 0:
            score += 1; reasons.append("MACD상승")
        if price <= lower:
            score += 2; reasons.append("BB하단")
        elif price <= lower * 1.01:
            score += 1; reasons.append("BB하단근접")

        if score >= 3:
            return Signal("BUY", min(score / 5, 1.0), " | ".join(reasons))
        return Signal("HOLD", 0.0, "신호없음")

    # ── 스캘핑 신호 ───────────────────────────────────────────

    def _scalp_signal(self, df, price, avg_price, sl, tp) -> Signal:
        rsi   = self._rsi(df["close"], 9)
        macd, signal_line = self._macd(df["close"], 5, 13, 5)
        upper, lower = self._bb(df["close"], 10, 2.0)

        score = 0
        reasons = []

        if avg_price is not None:
            pnl_rate = (price - avg_price) / avg_price
            if pnl_rate <= sl:
                return Signal("SELL", 1.0, f"스캘손절 ({pnl_rate*100:.1f}%)")
            if pnl_rate >= tp:
                return Signal("SELL", 1.0, f"스캘익절 ({pnl_rate*100:.1f}%)")
            if rsi > 65:
                score += 1; reasons.append("RSI단기과매수")
            if macd < signal_line:
                score += 1; reasons.append("MACD단기하락")
            if score >= 2:
                return Signal("SELL", 0.8, " | ".join(reasons))
            return Signal("HOLD", 0.0, "유지")

        if rsi < 30:
            score += 2; reasons.append("RSI단기과매도")
        elif rsi < 40:
            score += 1; reasons.append("RSI단기중립하")
        if macd > signal_line:
            score += 1; reasons.append("MACD단기상승")
        if price <= lower:
            score += 2; reasons.append("BB단기하단")

        if score >= 3:
            return Signal("BUY", min(score / 4, 1.0), " | ".join(reasons))
        return Signal("HOLD", 0.0, "신호없음")

    # ── 보조지표 계산 ─────────────────────────────────────────

    @staticmethod
    def _rsi(series: pd.Series, period: int) -> float:
        delta = series.diff()
        gain  = delta.clip(lower=0)
        loss  = (-delta).clip(lower=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            avg_gain = gain.ewm(com=period - 1, min_periods=period).mean().iloc[-1]
            avg_loss = loss.ewm(com=period - 1, min_periods=period).mean().iloc[-1]
            if avg_loss == 0:
                return 100.0
            rs  = avg_gain / avg_loss
            return float(100 - 100 / (1 + rs))

    @staticmethod
    def _macd(series: pd.Series, fast, slow, signal) -> tuple[float, float]:
        ema_f = series.ewm(span=fast, adjust=False).mean()
        ema_s = series.ewm(span=slow, adjust=False).mean()
        macd  = ema_f - ema_s
        sig   = macd.ewm(span=signal, adjust=False).mean()
        return float(macd.iloc[-1]), float(sig.iloc[-1])

    @staticmethod
    def _bb(series: pd.Series, period: int, std_mul: float) -> tuple[float, float]:
        ma    = series.rolling(period).mean()
        std   = series.rolling(period).std()
        upper = float((ma + std_mul * std).iloc[-1])
        lower = float((ma - std_mul * std).iloc[-1])
        return upper, lower
