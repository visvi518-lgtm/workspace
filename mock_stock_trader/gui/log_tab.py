"""거래 로그 탭"""
import customtkinter as ctk


class LogTab(ctk.CTkFrame):

    def __init__(self, parent, db, auto_trader):
        super().__init__(parent, fg_color="transparent")
        self.db          = db
        self.auto_trader = auto_trader
        self._build()
        self.update()

    def _build(self):
        # 실시간 로그 박스
        top = ctk.CTkFrame(self, corner_radius=10, fg_color=("#1e1e2e", "#13131f"))
        top.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(top, text="실시간 로그",
                     font=("Malgun Gothic", 12, "bold"), text_color="#aaa",
                     ).pack(anchor="w", padx=12, pady=(8, 2))
        self._live_box = ctk.CTkTextbox(
            top, height=120, font=("Consolas", 11),
            fg_color=("#111122", "#0a0a14"), state="disabled",
        )
        self._live_box.pack(fill="x", padx=12, pady=(0, 10))

        # 거래 이력 테이블
        tbl = ctk.CTkFrame(self, corner_radius=10, fg_color=("#1e1e2e", "#13131f"))
        tbl.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        ctk.CTkLabel(tbl, text="거래 이력",
                     font=("Malgun Gothic", 12, "bold"), text_color="#aaa",
                     ).pack(anchor="w", padx=12, pady=(8, 2))

        cols = [("시각", 140), ("종목", 120), ("구분", 50), ("시장", 50),
                ("가격", 100), ("수량", 60), ("금액", 110), ("손익", 100), ("사유", 200)]
        hdr = ctk.CTkFrame(tbl, fg_color=("#252535", "#161626"), height=28)
        hdr.pack(fill="x", padx=12)
        hdr.pack_propagate(False)
        for label, w in cols:
            ctk.CTkLabel(hdr, text=label, width=w,
                         font=("Malgun Gothic", 10, "bold"),
                         text_color="#90caf9", anchor="center").pack(side="left")

        self._scroll = ctk.CTkScrollableFrame(
            tbl, fg_color="transparent", scrollbar_button_color="#3a7bd5"
        )
        self._scroll.pack(fill="both", expand=True, padx=12, pady=(0, 8))

    def append_log(self, msg: str):
        self._live_box.configure(state="normal")
        self._live_box.insert("end", msg + "\n")
        self._live_box.see("end")
        self._live_box.configure(state="disabled")

    def update(self):
        for w in self._scroll.winfo_children():
            w.destroy()

        trades = self.db.get_trades(100)
        cols = [("시각", 140), ("종목", 120), ("구분", 50), ("시장", 50),
                ("가격", 100), ("수량", 60), ("금액", 110), ("손익", 100), ("사유", 200)]

        for i, t in enumerate(trades):
            bg  = "#1e1e2e" if i % 2 == 0 else "#16162a"
            row = ctk.CTkFrame(self._scroll, fg_color=bg, height=26)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            is_buy  = t["trade_type"] == "BUY"
            tc_color = "#64b5f6" if is_buy else "#ef9a9a"
            pnl_color = "#66bb6a" if (t["profit"] or 0) >= 0 else "#e57373"

            vals = [
                (t["timestamp"] or "",          140, "#aaa"),
                (t["name"] or "",               120, "#ddd"),
                (t["trade_type"],                50, tc_color),
                (t["market"] or "",              50, "#aaa"),
                (f'{t["price"]:,.0f}',          100, "#ddd"),
                (f'{t["quantity"]:.0f}',         60, "#ddd"),
                (f'{t["amount"]:,.0f}',         110, "#ddd"),
                (f'{t["profit"]:+,.0f}' if not is_buy else "—",
                                                100, pnl_color),
                (t["reason"] or "",             200, "#888"),
            ]
            for text, width, color in vals:
                ctk.CTkLabel(row, text=text, width=width,
                             font=("Malgun Gothic", 10),
                             text_color=color, anchor="center").pack(side="left")
