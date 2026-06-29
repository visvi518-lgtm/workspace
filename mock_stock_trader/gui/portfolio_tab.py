"""포트폴리오 탭 — 보유 종목 목록"""
import customtkinter as ctk


COLS = [
    ("종목명",    160, "name"),
    ("시장",      50,  "market"),
    ("모드",      60,  "mode"),
    ("수량",      60,  "quantity"),
    ("평균단가",  100, "avg_price"),
    ("현재가",    100, "cur_price"),
    ("평가금액",  110, "val"),
    ("손익",      100, "pnl"),
    ("손익률",    80,  "pnl_pct"),
]


class PortfolioTab(ctk.CTkFrame):

    def __init__(self, parent, db, portfolio, auto_trader):
        super().__init__(parent, fg_color="transparent")
        self.db          = db
        self.portfolio   = portfolio
        self.auto_trader = auto_trader
        self._rows: list = []
        self._build()

    def _build(self):
        # 헤더
        hdr = ctk.CTkFrame(self, fg_color=("#252535", "#161626"), height=30)
        hdr.pack(fill="x", padx=10, pady=(10, 0))
        hdr.pack_propagate(False)
        for label, width, _ in COLS:
            ctk.CTkLabel(hdr, text=label, width=width,
                         font=("Malgun Gothic", 10, "bold"),
                         text_color="#90caf9", anchor="center").pack(side="left")

        # 스크롤 목록
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#3a7bd5",
        )
        self._scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def update(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._rows.clear()

        positions = self.portfolio.positions
        if not positions:
            ctk.CTkLabel(self._scroll, text="보유 종목 없음",
                         text_color="#555", font=("Malgun Gothic", 13)).pack(pady=40)
            return

        for i, ((code, market), pos) in enumerate(positions.items()):
            bg  = "#1e1e2e" if i % 2 == 0 else "#16162a"
            row = ctk.CTkFrame(self._scroll, fg_color=bg, height=30)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            cur_price = pos["avg_price"]   # 현재가 없으면 매수가 표시
            val       = cur_price * pos["quantity"]
            pnl       = (cur_price - pos["avg_price"]) * pos["quantity"]
            pnl_pct   = (cur_price - pos["avg_price"]) / pos["avg_price"] * 100 if pos["avg_price"] else 0

            p_color = "#66bb6a" if pnl >= 0 else "#e57373"

            data = {
                "name":      pos["name"],
                "market":    market,
                "mode":      pos.get("mode", "swing"),
                "quantity":  f'{pos["quantity"]:.0f}',
                "avg_price": f'{pos["avg_price"]:,.0f}',
                "cur_price": f'{cur_price:,.0f}',
                "val":       f'{val:,.0f}',
                "pnl":       f'{pnl:+,.0f}',
                "pnl_pct":   f'{pnl_pct:+.2f}%',
            }

            for label, width, key in COLS:
                color = p_color if key in ("pnl", "pnl_pct") else "#ddd"
                ctk.CTkLabel(row, text=data[key], width=width,
                             font=("Malgun Gothic", 11),
                             text_color=color, anchor="center").pack(side="left")
