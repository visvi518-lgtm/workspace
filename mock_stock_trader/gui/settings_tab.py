import customtkinter as ctk
from tkinter import messagebox
import config


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, db, portfolio, auto_trader):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.portfolio = portfolio
        self.auto_trader = auto_trader
        self._build()
        self._load()

    def _section(self, title: str) -> ctk.CTkFrame:
        box = ctk.CTkFrame(self, corner_radius=10, fg_color=("#2b2b2b", "#1e1e2e"))
        box.pack(fill="x", padx=15, pady=6)
        ctk.CTkLabel(box, text=title, font=("Malgun Gothic", 13, "bold"), text_color="#aaa").pack(anchor="w", padx=12, pady=(10, 4))
        return box

    def _row(self, parent, label: str, widget_factory):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(row, text=label, font=("Malgun Gothic", 11), width=180, anchor="w").pack(side="left")
        w = widget_factory(row)
        w.pack(side="left", padx=(8, 0))
        return w

    def _build(self):
        # ── 자금 설정 ──
        sec1 = self._section("자금 설정")

        self.capital_entry = self._row(
            sec1, "초기 투자금 (원)",
            lambda p: ctk.CTkEntry(p, width=160, placeholder_text="10000000")
        )

        ctk.CTkButton(
            sec1, text="초기 자금 재설정 (포트폴리오 초기화)",
            command=self._reset_capital,
            fg_color="#c62828", hover_color="#b71c1c", width=260,
            font=("Malgun Gothic", 11)
        ).pack(anchor="w", padx=12, pady=(4, 12))

        # ── 매매 파라미터 ──
        sec2 = self._section("매매 파라미터 (스윙 기준 | 스캘핑은 자동 적용)")

        self.stop_entry = self._row(
            sec2, "스윙 손절 기준 (%)",
            lambda p: ctk.CTkEntry(p, width=100, placeholder_text="-2.0")
        )
        self.take_entry = self._row(
            sec2, "스윙 익절 기준 (%)",
            lambda p: ctk.CTkEntry(p, width=100, placeholder_text="3.0")
        )
        self.daily_target_entry = self._row(
            sec2, "일일 목표 수익률 (%)",
            lambda p: ctk.CTkEntry(p, width=100, placeholder_text="2.0")
        )
        self.max_pos_entry = self._row(
            sec2, "최대 보유 종목 수",
            lambda p: ctk.CTkEntry(p, width=100, placeholder_text="8")
        )
        self.interval_entry = self._row(
            sec2, "스캔 주기 (분)",
            lambda p: ctk.CTkEntry(p, width=100, placeholder_text="3")
        )
        self.rate_entry = self._row(
            sec2, "원/달러 환율",
            lambda p: ctk.CTkEntry(p, width=100, placeholder_text="1350")
        )
        ctk.CTkLabel(sec2,
            text="  ℹ  스캘핑: ATR>2% 종목 자동 선별 | KR TP+1.0%/SL-0.5% | US TP+1.5%/SL-0.5%",
            font=("Malgun Gothic", 10), text_color="#607d8b"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # ── 자동매매 옵션 ──
        sec3 = self._section("자동매매 옵션")

        self.force_var = ctk.BooleanVar()
        self._row(
            sec3, "시장 시간 외 강제 매매 (테스트용)",
            lambda p: ctk.CTkCheckBox(p, text="", variable=self.force_var)
        )

        # ── 자동매매 제어 ──
        sec4 = self._section("자동매매 제어")
        ctrl = ctk.CTkFrame(sec4, fg_color="transparent")
        ctrl.pack(fill="x", padx=12, pady=(4, 12))

        self.start_btn = ctk.CTkButton(
            ctrl, text="▶  자동매매 시작", command=self._start_trading,
            fg_color="#2e7d32", hover_color="#1b5e20", width=160, font=("Malgun Gothic", 12, "bold")
        )
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(
            ctrl, text="■  자동매매 중지", command=self._stop_trading,
            fg_color="#6d1f1f", hover_color="#4e342e", width=160, font=("Malgun Gothic", 12, "bold"),
            state="disabled"
        )
        self.stop_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(
            ctrl, text="● 중지됨", text_color="#e57373", font=("Malgun Gothic", 11)
        )
        self.status_label.pack(side="left", padx=20)

        # 저장 버튼
        ctk.CTkButton(
            self, text="설정 저장", command=self._save,
            font=("Malgun Gothic", 12, "bold"), width=160
        ).pack(pady=10)

    def _load(self):
        self.capital_entry.delete(0, "end")
        self.capital_entry.insert(0, self.db.get_setting("initial_capital", str(config.DEFAULT_INITIAL_CAPITAL)))

        sl = float(self.db.get_setting("stop_loss", config.SWING_STOP_LOSS)) * 100
        tp = float(self.db.get_setting("take_profit", config.SWING_TAKE_PROFIT)) * 100
        self.stop_entry.delete(0, "end")
        self.stop_entry.insert(0, str(round(sl, 1)))
        self.take_entry.delete(0, "end")
        self.take_entry.insert(0, str(round(tp, 1)))

        daily_t = float(self.db.get_setting("daily_target", config.DAILY_TARGET_RATE)) * 100
        self.daily_target_entry.delete(0, "end")
        self.daily_target_entry.insert(0, str(round(daily_t, 1)))

        self.max_pos_entry.delete(0, "end")
        self.max_pos_entry.insert(0, self.db.get_setting("max_positions", str(config.MAX_POSITIONS)))

        self.interval_entry.delete(0, "end")
        self.interval_entry.insert(0, self.db.get_setting("scan_interval", str(config.SCAN_INTERVAL_MINUTES)))

        self.rate_entry.delete(0, "end")
        self.rate_entry.insert(0, self.db.get_setting("exchange_rate", str(config.DEFAULT_EXCHANGE_RATE)))

        self.force_var.set(self.db.get_setting("force_trade", "0") == "1")

    def _save(self):
        try:
            capital = float(self.capital_entry.get())
            sl = float(self.stop_entry.get()) / 100
            tp = float(self.take_entry.get()) / 100
            daily_t = float(self.daily_target_entry.get()) / 100
            max_pos = int(self.max_pos_entry.get())
            interval = int(self.interval_entry.get())
            rate = float(self.rate_entry.get())

            self.db.set_setting("stop_loss", sl)
            self.db.set_setting("take_profit", tp)
            self.db.set_setting("daily_target", daily_t)
            self.db.set_setting("max_positions", max_pos)
            self.db.set_setting("scan_interval", interval)
            self.db.set_setting("exchange_rate", rate)
            self.db.set_setting("force_trade", "1" if self.force_var.get() else "0")

            config.SWING_STOP_LOSS = sl
            config.SWING_TAKE_PROFIT = tp
            config.DAILY_TARGET_RATE = daily_t
            config.MAX_POSITIONS = max_pos
            config.SCAN_INTERVAL_MINUTES = interval
            config.DEFAULT_EXCHANGE_RATE = rate

            messagebox.showinfo("저장 완료", "설정이 저장되었습니다.")
        except ValueError:
            messagebox.showerror("입력 오류", "올바른 숫자를 입력하세요.")

    def _reset_capital(self):
        if not messagebox.askyesno("초기화 확인", "포트폴리오를 초기화하면 모든 거래내역과\n보유 종목이 삭제됩니다. 진행하시겠습니까?"):
            return
        try:
            amount = float(self.capital_entry.get())
        except ValueError:
            messagebox.showerror("오류", "올바른 금액을 입력하세요.")
            return
        self.db.conn.execute("DELETE FROM portfolio")
        self.db.conn.execute("DELETE FROM trades")
        self.db.conn.execute("DELETE FROM portfolio_history")
        self.db.conn.commit()
        self.portfolio.set_initial_capital(amount)
        messagebox.showinfo("초기화 완료", f"초기 자금 {amount:,.0f}원으로 리셋되었습니다.")

    def _start_trading(self):
        interval = int(self.db.get_setting("scan_interval", config.SCAN_INTERVAL_MINUTES))
        self.auto_trader.start(interval)
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="● 실행 중", text_color="#66bb6a")

    def _stop_trading(self):
        self.auto_trader.stop()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="● 중지됨", text_color="#e57373")

    def update(self):
        if self.auto_trader.is_running:
            self.status_label.configure(text="● 실행 중", text_color="#66bb6a")
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        else:
            self.status_label.configure(text="● 중지됨", text_color="#e57373")
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
