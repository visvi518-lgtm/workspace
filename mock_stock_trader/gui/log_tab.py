import customtkinter as ctk
from tkinter import ttk
import tkinter as tk


class LogTab(ctk.CTkFrame):
    def __init__(self, parent, db, auto_trader):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.auto_trader = auto_trader
        self._build()

    def _build(self):
        style = ttk.Style()
        style.configure("Log.Treeview",
            background="#1e1e2e", foreground="white",
            rowheight=28, fieldbackground="#1e1e2e", font=("Malgun Gothic", 10))
        style.configure("Log.Treeview.Heading",
            background="#2b2b2b", foreground="#aaa", font=("Malgun Gothic", 10, "bold"))
        style.map("Log.Treeview", background=[("selected", "#3a3a5c")])

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(10, 5))
        ctk.CTkLabel(top, text="거래 내역", font=("Malgun Gothic", 16, "bold")).pack(side="left")

        cols = ("time", "market", "type", "name", "price", "qty", "amount", "fee", "profit", "rate", "reason")
        hdrs = [
            ("time", "시간", 130),
            ("market", "시장", 50),
            ("type", "구분", 55),
            ("name", "종목", 110),
            ("price", "단가", 90),
            ("qty", "수량", 60),
            ("amount", "거래금액", 110),
            ("fee", "수수료", 80),
            ("profit", "실현손익", 100),
            ("rate", "수익률", 70),
            ("reason", "매매 이유", 350),
        ]

        frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("#2b2b2b", "#1e1e2e"))
        frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.tree = ttk.Treeview(frame, style="Log.Treeview", show="headings", columns=cols)
        for col, hdr, w in hdrs:
            self.tree.heading(col, text=hdr, command=lambda c=col: self._sort(c))
            self.tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # 시스템 로그
        log_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("#2b2b2b", "#1e1e2e"))
        log_frame.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(log_frame, text="시스템 로그", font=("Malgun Gothic", 11, "bold")).pack(anchor="w", padx=10, pady=(6, 2))
        self.log_text = ctk.CTkTextbox(log_frame, height=100, font=("Consolas", 10), fg_color="#111122")
        self.log_text.pack(fill="x", padx=8, pady=(0, 8))

        self._sort_col = "time"
        self._sort_rev = True

    def _sort(self, col):
        self._sort_rev = not self._sort_rev if self._sort_col == col else False
        self._sort_col = col
        self.update()

    def update(self):
        self.tree.delete(*self.tree.get_children())
        trades = self.db.get_trades(limit=500)

        for t in trades:
            typ = "▲매수" if t["trade_type"] == "BUY" else "▼매도"
            pft = ""
            rate = ""
            if t["profit"] is not None:
                sign = "+" if t["profit"] >= 0 else ""
                pft = f"{sign}{t['profit']:,.0f}"
                rate = f"{sign}{t['profit_rate']:.2f}%"
            tag = "buy" if t["trade_type"] == "BUY" else ("pos" if (t["profit"] or 0) >= 0 else "neg")
            self.tree.insert("", "end", tags=(tag,), values=(
                t["timestamp"],
                t["market"],
                typ,
                t["name"],
                f"{t['price']:,.0f}",
                t["quantity"],
                f"{t['amount']:,.0f}",
                f"{t['fee']:,.0f}",
                pft,
                rate,
                t["reason"],
            ))

        self.tree.tag_configure("buy", foreground="#29b6f6")
        self.tree.tag_configure("pos", foreground="#ef5350")
        self.tree.tag_configure("neg", foreground="#42a5f5")

    def append_log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
