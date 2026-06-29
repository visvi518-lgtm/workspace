"""대시보드 탭 — 총 자산, 수익률, 보유 종목, 자산 차트"""
import customtkinter as ctk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import config


class DashboardTab(ctk.CTkFrame):

    def __init__(self, parent, db, portfolio, auto_trader):
        super().__init__(parent, fg_color="transparent")
        self.db          = db
        self.portfolio   = portfolio
        self.auto_trader = auto_trader
        self._fig  = None
        self._ax   = None
        self._canvas = None
        self._build()

    def _build(self):
        # 상단 지표 카드
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=10, pady=(10, 6))

        self.card_total  = self._card(cards, "총 자산",   "—")
        self.card_profit = self._card(cards, "총 손익",   "—")
        self.card_pct    = self._card(cards, "수익률",    "—")
        self.card_cash   = self._card(cards, "가용 현금", "—")
        self.card_pos    = self._card(cards, "보유 종목", "—")

        for c in (self.card_total, self.card_profit, self.card_pct,
                  self.card_cash, self.card_pos):
            c.pack(side="left", expand=True, fill="x", padx=4)

        # 차트
        chart_f = ctk.CTkFrame(self, corner_radius=10, fg_color=("#1e1e2e", "#13131f"))
        chart_f.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        ctk.CTkLabel(chart_f, text="자산 추이",
                     font=("Malgun Gothic", 12, "bold"), text_color="#aaa",
                     ).pack(anchor="w", padx=14, pady=(8, 0))

        self._chart_frame = ctk.CTkFrame(chart_f, fg_color="transparent")
        self._chart_frame.pack(fill="both", expand=True, padx=8, pady=8)
        self._init_chart()

    def _card(self, parent, label: str, value: str) -> ctk.CTkFrame:
        f = ctk.CTkFrame(parent, corner_radius=10, fg_color=("#2b2b2b", "#1e1e2e"))
        ctk.CTkLabel(f, text=label,
                     font=("Malgun Gothic", 10), text_color="#888").pack(pady=(8, 2))
        lbl = ctk.CTkLabel(f, text=value,
                           font=("Malgun Gothic", 15, "bold"), text_color="white")
        lbl.pack(pady=(0, 8))
        f._val_label = lbl
        return f

    def _init_chart(self):
        self._fig, self._ax = plt.subplots(figsize=(8, 3), facecolor="#13131f")
        self._ax.set_facecolor("#13131f")
        self._ax.tick_params(colors="#666", labelsize=8)
        for spine in self._ax.spines.values():
            spine.set_edgecolor("#333")
        self._fig.tight_layout(pad=0.8)
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._chart_frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvas.draw()

    def update(self):
        initial = float(self.db.get_setting("initial_capital",
                        config.DEFAULT_INITIAL_CAPITAL))

        # 현재가 없으면 매수가 기준
        current_prices = {}
        for (code, mkt), pos in self.portfolio.positions.items():
            current_prices[(code, mkt)] = pos["avg_price"]

        total  = self.portfolio.total_value(current_prices)
        profit = total - initial
        pct    = profit / initial * 100 if initial else 0
        cash   = self.portfolio.cash
        n_pos  = self.portfolio.position_count()

        p_color = "#66bb6a" if profit >= 0 else "#e57373"

        self.card_total._val_label.configure(text=f"{total:,.0f}원")
        self.card_profit._val_label.configure(
            text=f"{profit:+,.0f}원", text_color=p_color)
        self.card_pct._val_label.configure(
            text=f"{pct:+.2f}%", text_color=p_color)
        self.card_cash._val_label.configure(text=f"{cash:,.0f}원")
        self.card_pos._val_label.configure(text=f"{n_pos}종목")

        # 차트 갱신
        history = self.db.get_history(200)
        if len(history) >= 2:
            xs = list(range(len(history)))
            ys = [h["value"] for h in history]
            self._ax.clear()
            self._ax.set_facecolor("#13131f")
            self._ax.tick_params(colors="#666", labelsize=8)
            for spine in self._ax.spines.values():
                spine.set_edgecolor("#333")
            color = "#66bb6a" if ys[-1] >= ys[0] else "#e57373"
            self._ax.plot(xs, ys, color=color, linewidth=1.5)
            self._ax.fill_between(xs, ys, alpha=0.15, color=color)
            self._ax.axhline(y=initial, color="#555", linestyle="--", linewidth=0.8)
            self._fig.tight_layout(pad=0.8)
            self._canvas.draw()
