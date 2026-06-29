"""가상 포트폴리오 — 현금·포지션·손익 관리"""
import config
from db.database import Database
from datetime import datetime


class Portfolio:
    def __init__(self, db: Database):
        self.db   = db
        self._cash = float(db.get_setting("cash", config.DEFAULT_INITIAL_CAPITAL))
        # {(code, market): {"name","quantity","avg_price","mode"}}
        self._positions: dict = {}
        self._load_positions()

    # ── 초기화 ───────────────────────────────────────────────

    def _load_positions(self):
        for row in self.db.get_positions():
            key = (row["code"], row["market"])
            self._positions[key] = {
                "name":      row["name"],
                "quantity":  row["quantity"],
                "avg_price": row["avg_price"],
                "mode":      row.get("mode", "swing"),
            }

    def set_initial_capital(self, amount: float):
        self._cash = amount
        self._positions.clear()
        self.db.set_setting("cash", amount)

    # ── 현금 ─────────────────────────────────────────────────

    @property
    def cash(self) -> float:
        return self._cash

    def _save_cash(self):
        self.db.set_setting("cash", self._cash)

    # ── 포지션 조회 ───────────────────────────────────────────

    @property
    def positions(self) -> dict:
        return self._positions

    def has_position(self, code: str, market: str) -> bool:
        return (code, market) in self._positions

    def position_count(self) -> int:
        return len(self._positions)

    # ── 매수 ─────────────────────────────────────────────────

    def buy(self, code, market, name, price, quantity, mode="swing") -> dict | None:
        fee_rate = config.KR_FEE_RATE if market == "KR" else config.US_FEE_RATE
        amount   = price * quantity
        fee      = amount * fee_rate

        if self._cash < amount + fee:
            return None

        self._cash -= (amount + fee)

        key = (code, market)
        if key in self._positions:
            pos = self._positions[key]
            total_qty   = pos["quantity"] + quantity
            total_cost  = pos["avg_price"] * pos["quantity"] + amount
            pos["avg_price"] = total_cost / total_qty
            pos["quantity"]  = total_qty
        else:
            self._positions[key] = {
                "name":      name,
                "quantity":  quantity,
                "avg_price": price,
                "mode":      mode,
            }

        self.db.upsert_position(
            code, market, name,
            self._positions[key]["quantity"],
            self._positions[key]["avg_price"],
            mode,
        )
        self._save_cash()

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.save_trade(
            code, market, name, "BUY", price, quantity, amount, fee, 0, "매수", ts
        )

        return {"amount": amount, "fee": fee, "timestamp": ts}

    # ── 매도 ─────────────────────────────────────────────────

    def sell(self, code, market, price, reason="") -> dict | None:
        key = (code, market)
        if key not in self._positions:
            return None

        pos      = self._positions[key]
        quantity = pos["quantity"]
        name     = pos["name"]

        fee_rate = config.KR_FEE_RATE if market == "KR" else config.US_FEE_RATE
        amount   = price * quantity
        fee      = amount * fee_rate
        profit   = (price - pos["avg_price"]) * quantity - fee

        self._cash += amount - fee
        del self._positions[key]
        self.db.delete_position(code, market)
        self._save_cash()

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.save_trade(
            code, market, name, "SELL", price, quantity, amount, fee, profit, reason, ts
        )

        return {"profit": profit, "amount": amount, "fee": fee, "timestamp": ts}

    # ── 평가 ─────────────────────────────────────────────────

    def total_value(self, current_prices: dict) -> float:
        """현금 + 보유 종목 평가금액 합계"""
        val = self._cash
        for (code, market), pos in self._positions.items():
            price = current_prices.get((code, market), pos["avg_price"])
            val  += price * pos["quantity"]
        return val

    def unrealized_pnl(self, current_prices: dict) -> float:
        pnl = 0.0
        for (code, market), pos in self._positions.items():
            price = current_prices.get((code, market), pos["avg_price"])
            pnl  += (price - pos["avg_price"]) * pos["quantity"]
        return pnl

    def initial_capital(self) -> float:
        return float(self.db.get_setting("initial_capital",
                     self.db.get_setting("cash", config.DEFAULT_INITIAL_CAPITAL)))
