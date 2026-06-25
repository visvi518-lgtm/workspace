import customtkinter as ctk
from tkinter import ttk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime


def _fmt_krw(v: float) -> str:
    return f"{v:,.0f}원"

def _fmt_pct(v: float) -> str:
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"

def _color(v: float) -> str:
    return "#ef5350" if v >= 0 else "#42a5f5"


class SummaryCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, corner_radius=10, **kwargs)
        self.configure(fg_color=("#2b2b2b", "#1e1e2e"))
        ctk.CTkLabel(self, text=title, font=("Malgun Gothic", 11), text_color="gray").pack(pady=(10, 2))
        self.value_label = ctk.CTkLabel(self, text="—", font=("Malgun Gothic", 18, "bold"))
        self.value_label.pack(pady=(0, 10))

    def set(self, text: str, color: str = "white"):
        self.value_label.configure(text=text, text_color=color)


class DashboardTab(ctk.CTkFrame):
    def __init__(self, parent, db, portfolio, auto_trader):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.portfolio = portfolio
        self.auto_trader = auto_trader
        self._build()

    def _build(self):
        # 상단 요약 카드 (6개)
        card_frame = ctk.CTkFrame(self, fg_color="transparent")
        card_frame.pack(fill="x", padx=15, pady=(10, 5))
        for i in range(6):
            card_frame.columnconfigure(i, weight=1)

        self.card_total = SummaryCard(card_frame, "총 자산")
        self.card_total.grid(row=0, column=0, padx=4, sticky="ew")
        self.card_profit = SummaryCard(card_frame, "누적 손익")
        self.card_profit.grid(row=0, column=1, padx=4, sticky="ew")
        self.card_rate = SummaryCard(card_frame, "누적 수익률")
        self.card_rate.grid(row=0, column=2, padx=4, sticky="ew")
        self.card_daily = SummaryCard(card_frame, "일일 손익 (2% 목표)")
        self.card_daily.grid(row=0, column=3, padx=4, sticky="ew")
        self.card_cash = SummaryCard(card_frame, "가용 현금")
        self.card_cash.grid(row=0, column=4, padx=4, sticky="ew")
        self.card_trades = SummaryCard(card_frame, "오늘 거래")
        self.card_trades.grid(row=0, column=5, padx=4, sticky="ew")

        # 중단: 보유종목 + 차트
        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="both", expand=True, padx=15, pady=5)
        mid.columnconfigure(0, weight=1)
        mid.columnconfigure(1, weight=3)
        mid.rowconfigure(0, weight=1)

        # 보유 종목 패널
        left = ctk.CTkFrame(mid, corner_radius=10, fg_color=("#2b2b2b", "#1e1e2e"))
        left.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        ctk.CTkLabel(left, text="보유 종목", font=("Malgun Gothic", 13, "bold")).pack(pady=(10, 5))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview",
            background="#1e1e2e", foreground="white",
            rowheight=28, fieldbackground="#1e1e2e", font=("Malgun Gothic", 10))
        style.configure("Dark.Treeview.Heading",
            background="#2b2b2b", foreground="gray", font=("Malgun Gothic", 10, "bold"))
        style.map("Dark.Treeview", background=[("selected", "#3a3a5c")])

        self.holdings_tree = ttk.Treeview(
            left, style="Dark.Treeview", show="headings",
            columns=("name", "price", "rate"), height=8
        )
        for col, hdr, w in [("name", "종목", 80), ("price", "현재가", 80), ("rate", "손익률", 70)]:
            self.holdings_tree.heading(col, text=hdr)
            self.holdings_tree.column(col, width=w, anchor="center")
        self.holdings_tree.pack(fill="both", expand=True, padx=8, pady=(0, 10))

        # 수익률 차트
        right = ctk.CTkFrame(mid, corner_radius=10, fg_color=("#2b2b2b", "#1e1e2e"))
        right.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        ctk.CTkLabel(right, text="포트폴리오 수익률 추이", font=("Malgun Gothic", 13, "bold")).pack(pady=(10, 0))

        self.fig = Figure(figsize=(5, 3), dpi=96, facecolor="#1e1e2e")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#1e1e2e")
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 10))

        # 최근 거래 로그
        bottom = ctk.CTkFrame(self, corner_radius=10, fg_color=("#2b2b2b", "#1e1e2e"))
        bottom.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(bottom, text="최근 거래", font=("Malgun Gothic", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 3))

        self.recent_tree = ttk.Treeview(
            bottom, style="Dark.Treeview", show="headings",
            columns=("time", "type", "name", "price", "profit", "reason"), height=5
        )
        hdrs = [("time", "시간", 80), ("type", "구분", 50), ("name", "종목", 90),
                ("price", "가격", 90), ("profit", "손익", 80), ("reason", "매매 이유", 300)]
        for col, hdr, w in hdrs:
            self.recent_tree.heading(col, text=hdr)
            self.recent_tree.column(col, width=w, anchor="center")
        self.recent_tree.pack(fill="x", padx=8, pady=(0, 8))

    def update(self):
        prices = self.auto_trader.last_prices if self.auto_trader else {}
        pnl = self.portfolio.get_pnl(prices)

        self.card_total.set(_fmt_krw(pnl["total_value"]))
        self.card_profit.set(_fmt_krw(pnl["profit"]), _color(pnl["profit"]))
        self.card_rate.set(_fmt_pct(pnl["profit_rate"]), _color(pnl["profit_rate"]))
        self.card_cash.set(_fmt_krw(pnl["cash"]))
        self.card_trades.set(f"{self.db.today_trade_count()}건")

        # 일일 손익 카드 (복리 목표 2%)
        daily_pnl = self.auto_trader.daily_pnl if self.auto_trader else 0.0
        init_cap  = self.portfolio.initial_capital
        daily_pct = daily_pnl / init_cap * 100 if init_cap > 0 else 0
        target    = float(self.db.get_setting("daily_target", "0.02"))
        sign = "+" if daily_pnl >= 0 else ""
        daily_txt = f"{sign}{daily_pnl:,.0f}원\n{sign}{daily_pct:.2f}% / {target*100:.0f}%목표"
        daily_color = "#66bb6a" if daily_pct >= target * 100 else _color(daily_pnl)
        self.card_daily.set(daily_txt, daily_color)

        # 보유 종목 갱신 (스캘핑/스윙 표시)
        self.holdings_tree.delete(*self.holdings_tree.get_children())
        for pos in self.portfolio.get_positions():
            key = (pos["code"], pos["market"])
            cur = prices.get(key, pos["avg_price"])
            rate = (cur - pos["avg_price"]) / pos["avg_price"] * 100
            sign = "+" if rate >= 0 else ""
            mode_tag = "S" if pos.get("mode") == "scalp" else "W"
            tag = "up" if rate >= 0 else "dn"
            self.holdings_tree.insert("", "end", values=(
                f"[{mode_tag}]{pos['name']}", f"{cur:,.0f}", f"{sign}{rate:.2f}%"
            ), tags=(tag,))
        self.holdings_tree.tag_configure("up", foreground="#ef5350")
        self.holdings_tree.tag_configure("dn", foreground="#42a5f5")

        # 차트 갱신
        history = self.db.get_portfolio_history(288)
        self.ax.clear()
        self.ax.set_facecolor("#1e1e2e")
        if len(history) >= 2:
            init = self.portfolio.initial_capital
            times = [datetime.strptime(h["timestamp"], "%Y-%m-%d %H:%M:%S") for h in history]
            rates = [(h["total_value"] - init) / init * 100 for h in history]
            color = "#ef5350" if rates[-1] >= 0 else "#42a5f5"
            self.ax.plot(times, rates, color=color, linewidth=1.5)
            self.ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
            self.ax.fill_between(times, 0, rates, alpha=0.15, color=color)
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
            self.fig.autofmt_xdate(rotation=30, ha="right")
        self.ax.tick_params(colors="gray", labelsize=8)
        self.ax.spines[:].set_color("#444")
        self.ax.set_ylabel("수익률(%)", color="gray", fontsize=8, fontname="Malgun Gothic")
        self.fig.tight_layout(pad=1.0)
        self.canvas.draw()

        # 최근 거래 갱신
        self.recent_tree.delete(*self.recent_tree.get_children())
        for t in self.db.get_trades(limit=10):
            ts = t["timestamp"][11:16]
            typ = "▲매수" if t["trade_type"] == "BUY" else "▼매도"
            pft = ""
            if t["profit"] is not None:
                sign = "+" if t["profit"] >= 0 else ""
                pft = f"{sign}{t['profit']:,.0f}({sign}{t['profit_rate']:.1f}%)"
            tag = "buy" if t["trade_type"] == "BUY" else ("profit" if (t["profit"] or 0) >= 0 else "loss")
            self.recent_tree.insert("", "end", values=(
                ts, typ, t["name"], f"{t['price']:,.0f}", pft, t["reason"]
            ), tags=(tag,))
        self.recent_tree.tag_configure("buy", foreground="#29b6f6")
        self.recent_tree.tag_configure("profit", foreground="#ef5350")
        self.recent_tree.tag_configure("loss", foreground="#42a5f5")
