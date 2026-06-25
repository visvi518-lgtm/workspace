from datetime import datetime
from db.database import Database
import config


class VirtualPortfolio:
    def __init__(self, db: Database, initial_capital: float):
        self.db = db
        if not db.get_setting("cash"):
            db.set_setting("cash", initial_capital)
            db.set_setting("initial_capital", initial_capital)

    @property
    def cash(self) -> float:
        return float(self.db.get_setting("cash", 0))

    @property
    def initial_capital(self) -> float:
        return float(self.db.get_setting("initial_capital", 0))

    def set_initial_capital(self, amount: float):
        self.db.set_setting("initial_capital", amount)
        self.db.set_setting("cash", amount)

    def get_positions(self) -> list[dict]:
        return self.db.get_portfolio()

    def count_positions(self) -> int:
        return self.db.count_positions()

    def get_position(self, code: str, market: str) -> dict | None:
        return self.db.get_position(code, market)

    def buy(self, code: str, name: str, market: str, price: float, reason: str, mode: str = "swing") -> bool:
        if self.count_positions() >= config.MAX_POSITIONS:
            return False

        cash = self.cash
        # 복리 효과: 현재 보유 현금의 MAX_POSITION_RATIO% 사용
        max_amount = cash * config.MAX_POSITION_RATIO
        fee_rate = config.KR_BUY_FEE if market == "KR" else config.US_BUY_FEE

        invest = min(max_amount, cash * 0.9)
        gross = invest / (1 + fee_rate)
        quantity = int(gross / price)
        if quantity <= 0:
            return False

        amount = price * quantity
        fee = amount * fee_rate
        total_cost = amount + fee

        if total_cost > cash:
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing = self.get_position(code, market)
        if existing:
            total_qty = existing["quantity"] + quantity
            avg = (existing["avg_price"] * existing["quantity"] + price * quantity) / total_qty
            self.db.upsert_position(code, name, market, total_qty, avg, existing["buy_date"], existing["buy_reason"], mode)
        else:
            self.db.upsert_position(code, name, market, quantity, price, now, reason, mode)

        self.db.set_setting("cash", cash - total_cost)
        self.db.add_trade({
            "timestamp": now,
            "code": code,
            "name": name,
            "market": market,
            "trade_type": "BUY",
            "price": price,
            "quantity": quantity,
            "amount": amount,
            "fee": fee,
            "profit": None,
            "profit_rate": None,
            "reason": f"[{mode.upper()}] {reason}",
        })
        return True

    def sell(self, code: str, market: str, price: float, reason: str) -> bool:
        pos = self.get_position(code, market)
        if not pos:
            return False

        quantity = pos["quantity"]
        avg_price = pos["avg_price"]
        name = pos["name"]

        amount = price * quantity
        if market == "KR":
            fee_rate = config.KR_SELL_FEE
        else:
            fee_rate = config.US_SELL_FEE

        fee = amount * fee_rate
        net = amount - fee
        profit = net - (avg_price * quantity)
        profit_rate = profit / (avg_price * quantity) * 100

        self.db.remove_position(code, market)
        cash = self.cash
        self.db.set_setting("cash", cash + net)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.add_trade({
            "timestamp": now,
            "code": code,
            "name": name,
            "market": market,
            "trade_type": "SELL",
            "price": price,
            "quantity": quantity,
            "amount": amount,
            "fee": fee,
            "profit": round(profit, 2),
            "profit_rate": round(profit_rate, 2),
            "reason": reason,
        })
        return True

    def get_total_value(self, prices: dict) -> float:
        """prices: {(code, market): price}"""
        total = self.cash
        for pos in self.get_positions():
            key = (pos["code"], pos["market"])
            price = prices.get(key, pos["avg_price"])
            total += price * pos["quantity"]
        return total

    def get_pnl(self, prices: dict) -> dict:
        total = self.get_total_value(prices)
        init = self.initial_capital
        profit = total - init
        rate = profit / init * 100 if init > 0 else 0
        return {
            "total_value": total,
            "initial_capital": init,
            "profit": profit,
            "profit_rate": rate,
            "cash": self.cash,
        }
