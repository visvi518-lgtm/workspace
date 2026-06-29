"""백테스트 탭 — 과거 기간 시뮬레이션 + 결과 표시"""
from __future__ import annotations
import threading
import customtkinter as ctk
from tkinter import messagebox
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class BacktestTab(ctk.CTkFrame):

    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self._thread: threading.Thread | None = None
        self._build()

    # ── UI 구성 ──────────────────────────────────────────────

    def _build(self):
        # 입력 패널 (상단)
        input_f = ctk.CTkFrame(self, corner_radius=10, fg_color=("#1e1e2e", "#13131f"))
        input_f.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(input_f, text="백테스트 설정",
                     font=("Malgun Gothic", 13, "bold"), text_color="#aaa",
                     ).pack(anchor="w", padx=14, pady=(10, 6))

        row1 = ctk.CTkFrame(input_f, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(0, 4))

        def lbl(parent, text):
            ctk.CTkLabel(parent, text=text, font=("Malgun Gothic", 11),
                         text_color="#aaa").pack(side="left", padx=(0, 4))

        def entry(parent, w, ph):
            e = ctk.CTkEntry(parent, width=w, placeholder_text=ph)
            e.pack(side="left", padx=(0, 16))
            return e

        lbl(row1, "시작 연도")
        self.year_e  = entry(row1, 70, "2023")
        lbl(row1, "월")
        self.month_e = entry(row1, 50, "1")
        lbl(row1, "기간 (개월)")
        self.dur_e   = entry(row1, 50, "3")
        lbl(row1, "초기 자금 (원)")
        self.cap_e   = entry(row1, 120, "10000000")
        lbl(row1, "환율")
        self.rate_e  = entry(row1, 70, "1350")

        row2 = ctk.CTkFrame(input_f, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(0, 10))

        self.kr_var = ctk.BooleanVar(value=True)
        self.us_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(row2, text="국내 주식 (KR)", variable=self.kr_var,
                        font=("Malgun Gothic", 11)).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(row2, text="미국 주식 (US)", variable=self.us_var,
                        font=("Malgun Gothic", 11)).pack(side="left", padx=(0, 30))

        self.run_btn = ctk.CTkButton(
            row2, text="▶  백테스트 실행", command=self._run,
            fg_color="#1565c0", hover_color="#0d47a1",
            font=("Malgun Gothic", 12, "bold"), width=160,
        )
        self.run_btn.pack(side="left")

        self.prog_bar = ctk.CTkProgressBar(row2, width=200, height=14)
        self.prog_bar.pack(side="left", padx=(16, 0))
        self.prog_bar.set(0)

        self.prog_lbl = ctk.CTkLabel(row2, text="", font=("Malgun Gothic", 10),
                                     text_color="#aaa")
        self.prog_lbl.pack(side="left", padx=8)

        # 결과 탭뷰
        self._tabs = ctk.CTkTabview(
            self,
            fg_color=("#1e1e2e", "#13131f"),
            segmented_button_fg_color=("#2b2b2b", "#1a1a2a"),
            segmented_button_selected_color="#3a7bd5",
            text_color="white",
        )
        self._tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        for name in ("요약", "거래 로그", "자산 차트"):
            self._tabs.add(name)

        self._build_summary_tab()
        self._build_log_tab()
        self._build_chart_tab()

    def _build_summary_tab(self):
        f = self._tabs.tab("요약")
        self._summary_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        self._summary_scroll.pack(fill="both", expand=True)

    def _build_log_tab(self):
        f = self._tabs.tab("거래 로그")

        # 헤더
        cols = [("날짜", 100), ("종목", 130), ("구분", 55), ("시장", 55),
                ("모드", 60), ("가격", 100), ("수량", 55), ("손익", 100), ("사유", 200)]
        hdr = ctk.CTkFrame(f, fg_color=("#252535", "#161626"), height=28)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        for lbl, w in cols:
            ctk.CTkLabel(hdr, text=lbl, width=w,
                         font=("Malgun Gothic", 10, "bold"),
                         text_color="#90caf9", anchor="center").pack(side="left")

        self._log_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent",
                                                   scrollbar_button_color="#3a7bd5")
        self._log_scroll.pack(fill="both", expand=True)

    def _build_chart_tab(self):
        f = self._tabs.tab("자산 차트")
        self._chart_frame = ctk.CTkFrame(f, fg_color="transparent")
        self._chart_frame.pack(fill="both", expand=True)

    # ── 백테스트 실행 ─────────────────────────────────────────

    def _run(self):
        try:
            year  = int(self.year_e.get())
            month = int(self.month_e.get())
            dur   = int(self.dur_e.get())
            cap   = float(self.cap_e.get().replace(",", ""))
            rate  = float(self.rate_e.get())
        except ValueError:
            messagebox.showerror("입력 오류", "숫자를 올바르게 입력하세요.")
            return

        if not self.kr_var.get() and not self.us_var.get():
            messagebox.showerror("시장 선택", "국내 또는 미국 중 하나 이상 선택하세요.")
            return

        self.run_btn.configure(state="disabled")
        self.prog_bar.set(0)
        self._clear_results()

        def _task():
            from trader.backtester import Backtester
            from trader.strategy import TechnicalStrategy
            bt = Backtester(TechnicalStrategy())

            def _prog(msg):
                self.after(0, lambda m=msg: self.prog_lbl.configure(text=m[:50]))
                self.after(0, lambda: self.prog_bar.set(
                    min(self.prog_bar.get() + 0.05, 0.95)))

            result = bt.run(
                start_year=year, start_month=month, duration_months=dur,
                initial_capital=cap, use_kr=self.kr_var.get(), use_us=self.us_var.get(),
                exchange_rate=rate,
                progress_callback=_prog,
            )
            self.after(0, lambda r=result: self._show_results(r))

        self._thread = threading.Thread(target=_task, daemon=True)
        self._thread.start()

    def _clear_results(self):
        for w in self._summary_scroll.winfo_children():
            w.destroy()
        for w in self._log_scroll.winfo_children():
            w.destroy()
        for w in self._chart_frame.winfo_children():
            w.destroy()

    # ── 결과 표시 ─────────────────────────────────────────────

    def _show_results(self, result):
        self.run_btn.configure(state="normal")
        self.prog_bar.set(1.0)

        if result is None:
            messagebox.showerror("오류", "백테스트 실행 중 오류가 발생했습니다.")
            return

        self._show_summary(result)
        self._show_log(result)
        self._show_chart(result)

    def _show_summary(self, r):
        f = self._summary_scroll

        def card(label, value, color="#ddd"):
            b = ctk.CTkFrame(f, corner_radius=8, fg_color=("#2b2b2b", "#1e1e2e"))
            b.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(b, text=label, font=("Malgun Gothic", 10),
                         text_color="#888").pack(anchor="w", padx=12, pady=(6, 0))
            ctk.CTkLabel(b, text=value, font=("Malgun Gothic", 14, "bold"),
                         text_color=color).pack(anchor="w", padx=12, pady=(0, 6))

        p_color = "#66bb6a" if r.profit_rate >= 0 else "#e57373"
        d_color = "#e57373"

        card("최종 수익률",       f"{r.profit_rate:+.2f}%",            p_color)
        card("최종 자산",         f"{r.final_value:,.0f}원")
        card("실현 손익",         f"{r.final_value - r.initial_capital:+,.0f}원", p_color)
        card("최대 낙폭 (MDD)",   f"{r.max_drawdown:+.2f}%",           d_color)
        card("총 거래 횟수",      f"{r.total_trades}건")
        card("승률",             f"{r.win_trades}/{r.sell_trades}건  "
             f"({r.win_trades/r.sell_trades*100:.1f}%)"
             if r.sell_trades > 0 else "—")
        card("백테스트 기간",
             f"{r.start_date} ~ {r.end_date}  ({r.duration_days}일)")

    def _show_log(self, r):
        cols = [("날짜", 100), ("종목", 130), ("구분", 55), ("시장", 55),
                ("모드", 60), ("가격", 100), ("수량", 55), ("손익", 100), ("사유", 200)]

        for i, t in enumerate(r.trades):
            bg  = "#1e1e2e" if i % 2 == 0 else "#16162a"
            row = ctk.CTkFrame(self._log_scroll, fg_color=bg, height=26)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            is_buy   = t.trade_type == "BUY"
            tc_color = "#64b5f6" if is_buy else "#ef9a9a"
            p_color  = "#66bb6a" if (t.profit or 0) >= 0 else "#e57373"

            vals = [
                (t.date,                               100, "#aaa"),
                (t.name,                               130, "#ddd"),
                (t.trade_type,                          55, tc_color),
                (t.market,                              55, "#aaa"),
                (getattr(t, "mode", "—"),               60, "#aaa"),
                (f"{t.price:,.0f}",                    100, "#ddd"),
                (f"{t.quantity:.0f}",                   55, "#ddd"),
                (f"{t.profit:+,.0f}" if not is_buy else "—", 100, p_color),
                (t.reason[:40] if t.reason else "",    200, "#888"),
            ]
            for text, width, color in vals:
                ctk.CTkLabel(row, text=text, width=width,
                             font=("Malgun Gothic", 10),
                             text_color=color, anchor="center").pack(side="left")

    def _show_chart(self, r):
        if len(r.portfolio_history) < 2:
            ctk.CTkLabel(self._chart_frame, text="차트 데이터 없음",
                         text_color="#555").pack(pady=40)
            return

        fig, ax = plt.subplots(figsize=(8, 3.5), facecolor="#13131f")
        ax.set_facecolor("#13131f")
        ax.tick_params(colors="#666", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333")

        dates = [h["date"] for h in r.portfolio_history]
        vals  = [h["value"] for h in r.portfolio_history]
        color = "#66bb6a" if vals[-1] >= vals[0] else "#e57373"

        ax.plot(range(len(vals)), vals, color=color, linewidth=1.5)
        ax.fill_between(range(len(vals)), vals, alpha=0.15, color=color)
        ax.axhline(y=r.initial_capital, color="#555", linestyle="--", linewidth=0.8,
                   label="초기자금")

        step = max(1, len(dates) // 6)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels([dates[i][:7] for i in range(0, len(dates), step)],
                           rotation=20, ha="right", fontsize=7)
        ax.set_title(f"자산 추이  (수익률 {r.profit_rate:+.2f}%)",
                     color="#aaa", fontsize=10, pad=6)
        fig.tight_layout(pad=0.8)

        canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()
