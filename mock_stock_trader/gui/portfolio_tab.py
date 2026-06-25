import customtkinter as ctk
from tkinter import ttk
from datetime import datetime


class PortfolioTab(ctk.CTkFrame):
    def __init__(self, parent, db, portfolio, auto_trader):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.portfolio = portfolio
        self.auto_trader = auto_trader
        self._build()

    def _build(self):
        style = ttk.Style()
        style.configure("Port.Treeview",
            background="#1e1e2e", foreground="white",
            rowheight=30, fieldbackground="#1e1e2e", font=("Malgun Gothic", 11))
        style.configure("Port.Treeview.Heading",
            background="#2b2b2b", foreground="#aaa", font=("Malgun Gothic", 11, "bold"))
        style.map("Port.Treeview", background=[("selected", "#3a3a5c")])

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 5))
        ctk.CTkLabel(header, text="보유 포트폴리오", font=("Malgun Gothic", 16, "bold")).pack(side="left")

        table_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("#2b2b2b", "#1e1e2e"))
        table_frame.pack(fill="both", expand=True, padx=15, pady=5)

        cols = ("market", "name", "code", "qty", "avg", "current", "value", "pnl", "pnl_rate", "buy_date", "reason")
        hdrs = [
            ("market", "시장", 50),
            ("name", "종목명", 120),
            ("code", "코드", 80),
            ("qty", "수량", 60),
            ("avg", "평균단가", 90),
            ("current", "현재가", 90),
            ("value", "평가금액", 100),
            ("pnl", "평가손익", 100),
            ("pnl_rate", "수익률", 70),
            ("buy_date", "매수일", 110),
            ("reason", "매수 이유", 250),
        ]
        self.tree = ttk.Treeview(table_frame, style="Port.Treeview", show="headings", columns=cols)
        for col, hdr, w in hdrs:
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w, anchor="center")

        sb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=sb.set)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        sb.pack(fill="x", padx=5)

        # 합계 바
        self.summary_label = ctk.CTkLabel(
            self, text="", font=("Malgun Gothic", 12), text_color="gray"
        )
        self.summary_label.pack(pady=5)

    def update(self):
        self.tree.delete(*self.tree.get_children())
        prices = self.auto_trader.last_prices if self.auto_trader else {}

        total_invest = 0
        total_value = 0

        for pos in self.portfolio.get_positions():
            key = (pos["code"], pos["market"])
            cur = prices.get(key, pos["avg_price"])
            invest = pos["avg_price"] * pos["quantity"]
            val = cur * pos["quantity"]
            pnl = val - invest
            pnl_rate = pnl / invest * 100 if invest > 0 else 0
            sign = "+" if pnl >= 0 else ""
            tag = "up" if pnl >= 0 else "dn"
            buy_date = pos["buy_date"][:16] if pos["buy_date"] else ""
            self.tree.insert("", "end", tags=(tag,), values=(
                pos["market"],
                pos["name"],
                pos["code"],
                pos["quantity"],
                f"{pos['avg_price']:,.0f}",
                f"{cur:,.0f}",
                f"{val:,.0f}",
                f"{sign}{pnl:,.0f}",
                f"{sign}{pnl_rate:.2f}%",
                buy_date,
                pos.get("buy_reason", ""),
            ))
            total_invest += invest
            total_value += val

        self.tree.tag_configure("up", foreground="#ef5350")
        self.tree.tag_configure("dn", foreground="#42a5f5")

        total_pnl = total_value - total_invest
        total_rate = total_pnl / total_invest * 100 if total_invest > 0 else 0
        sign = "+" if total_pnl >= 0 else ""
        color = "#ef5350" if total_pnl >= 0 else "#42a5f5"
        self.summary_label.configure(
            text=f"총 투자금: {total_invest:,.0f}원  |  총 평가금액: {total_value:,.0f}원  |  총 손익: {sign}{total_pnl:,.0f}원 ({sign}{total_rate:.2f}%)",
            text_color=color,
        )
