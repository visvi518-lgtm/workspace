"""
전략 자동 최적화 탭 — 유전 알고리즘으로 최적 매매 파라미터 탐색
"""
from __future__ import annotations

import threading
import customtkinter as ctk
from tkinter import messagebox

import config

# 차트
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ─────────────────────────────────────────────────────────────────
class OptimizerTab(ctk.CTkFrame):

    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self._optimizer = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._all_results: list = []
        self._best: object | None = None
        self._scores_over_time: list[float] = []   # 각 이터레이션별 누적 최고 점수
        self._chart_canvas = None
        self._chart_fig    = None
        self._chart_ax     = None

        self._build()

    # ── UI 구성 ──────────────────────────────────────────────────

    def _build(self):
        # 좌우 2분할
        left  = ctk.CTkFrame(self, fg_color="transparent", width=340)
        right = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(8, 4), pady=8)
        right.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=8)
        left.pack_propagate(False)

        self._build_left(left)
        self._build_right(right)

    # ── 왼쪽 패널: 설정 + 진행 ──────────────────────────────────

    def _build_left(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        def sec(title):
            f = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("#2b2b2b", "#1e1e2e"))
            f.pack(fill="x", pady=6)
            ctk.CTkLabel(f, text=title, font=("Malgun Gothic", 12, "bold"),
                         text_color="#aaa").pack(anchor="w", padx=12, pady=(8, 3))
            return f

        def row(parent, label, widget_cb, label_width=110):
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(r, text=label, font=("Malgun Gothic", 11),
                         width=label_width, anchor="w").pack(side="left")
            w = widget_cb(r)
            w.pack(side="left", padx=(6, 0))
            return w

        # ── 기간 설정 ──
        sec1 = sec("백테스트 기간")
        self.year_e  = row(sec1, "시작 연도", lambda p: ctk.CTkEntry(p, width=70, placeholder_text="2023"))
        self.month_e = row(sec1, "시작 월",   lambda p: ctk.CTkEntry(p, width=50, placeholder_text="1"))
        self.dur_e   = row(sec1, "기간 (개월)", lambda p: ctk.CTkEntry(p, width=50, placeholder_text="3"))

        # ── 자금 설정 ──
        sec2 = sec("자금")
        self.cap_e  = row(sec2, "초기 자금 (원)", lambda p: ctk.CTkEntry(p, width=110, placeholder_text="10000000"))
        self.rate_e = row(sec2, "원/달러 환율",   lambda p: ctk.CTkEntry(p, width=70, placeholder_text="1350"))

        # ── 시장 선택 ──
        sec3 = sec("시장")
        self.kr_var = ctk.BooleanVar(value=True)
        self.us_var = ctk.BooleanVar(value=True)
        mf = ctk.CTkFrame(sec3, fg_color="transparent")
        mf.pack(fill="x", padx=12, pady=(2, 8))
        ctk.CTkCheckBox(mf, text="국내 (KR)", variable=self.kr_var,
                        font=("Malgun Gothic", 11)).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(mf, text="미국 (US)", variable=self.us_var,
                        font=("Malgun Gothic", 11)).pack(side="left")

        # ── GA 설정 ──
        sec4 = sec("최적화 설정")
        self.gen_e = row(sec4, "세대 수 (3~10)",
                         lambda p: ctk.CTkEntry(p, width=50, placeholder_text="5"))
        self.pop_e = row(sec4, "세대당 시도 (4~16)",
                         lambda p: ctk.CTkEntry(p, width=50, placeholder_text="8"))
        ctk.CTkLabel(sec4,
            text="  총 시도 횟수 = 세대 수 × 세대당 시도\n  권장: 5세대 × 8 = 40회 (약 5~10분)",
            font=("Malgun Gothic", 10), text_color="#607d8b",
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # ── 시작/중지 ──
        btn_f = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_f.pack(fill="x", pady=4)

        self.start_btn = ctk.CTkButton(
            btn_f, text="▶  최적화 시작", command=self._start,
            fg_color="#1565c0", hover_color="#0d47a1",
            font=("Malgun Gothic", 12, "bold"), width=150,
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            btn_f, text="■  중지", command=self._stop,
            fg_color="#6d1f1f", hover_color="#4e342e",
            font=("Malgun Gothic", 12, "bold"), width=80,
            state="disabled",
        )
        self.stop_btn.pack(side="left")

        # ── 진행 상황 ──
        sec5 = sec("진행 현황")

        self.prog_bar = ctk.CTkProgressBar(sec5, height=14)
        self.prog_bar.pack(fill="x", padx=12, pady=(4, 2))
        self.prog_bar.set(0)

        self.iter_label = ctk.CTkLabel(sec5, text="대기 중",
            font=("Malgun Gothic", 10), text_color="#aaa")
        self.iter_label.pack(anchor="w", padx=12, pady=(0, 2))

        self.status_label = ctk.CTkLabel(sec5, text="",
            font=("Malgun Gothic", 10), text_color="#90caf9",
            wraplength=290, justify="left")
        self.status_label.pack(anchor="w", padx=12, pady=(0, 4))

        self.best_label = ctk.CTkLabel(sec5, text="",
            font=("Malgun Gothic", 11, "bold"), text_color="#66bb6a",
            wraplength=290, justify="left")
        self.best_label.pack(anchor="w", padx=12, pady=(0, 10))

        # ── 최적 파라미터 적용 ──
        sec6 = sec("최적 파라미터")

        self.best_param_box = ctk.CTkTextbox(
            sec6, height=160, font=("Consolas", 10),
            fg_color=("#1a1a2e", "#0f0f1a"), state="disabled",
        )
        self.best_param_box.pack(fill="x", padx=12, pady=(4, 6))

        apply_f = ctk.CTkFrame(sec6, fg_color="transparent")
        apply_f.pack(fill="x", padx=12, pady=(0, 10))

        self.apply_btn = ctk.CTkButton(
            apply_f, text="이 설정을 프로그램에 적용",
            command=self._apply_best,
            fg_color="#2e7d32", hover_color="#1b5e20",
            font=("Malgun Gothic", 11, "bold"),
            state="disabled",
        )
        self.apply_btn.pack(fill="x")

        ctk.CTkLabel(apply_f,
            text="적용 시 설정 탭의 값도 덮어씁니다.",
            font=("Malgun Gothic", 9), text_color="#607d8b",
        ).pack(pady=(3, 0))

    # ── 오른쪽 패널: 수렴 차트 + 결과표 ────────────────────────

    def _build_right(self, parent):
        # 차트 영역
        chart_f = ctk.CTkFrame(parent, corner_radius=10, fg_color=("#1e1e2e", "#13131f"))
        chart_f.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(chart_f, text="수렴 그래프  (이터레이션별 누적 최고 점수)",
                     font=("Malgun Gothic", 12, "bold"), text_color="#aaa",
                     ).pack(anchor="w", padx=12, pady=(8, 0))

        self._chart_container = ctk.CTkFrame(chart_f, fg_color="transparent", height=200)
        self._chart_container.pack(fill="x", padx=10, pady=(4, 10))
        self._chart_container.pack_propagate(False)
        self._init_chart()

        # 결과표
        tbl_f = ctk.CTkFrame(parent, corner_radius=10, fg_color=("#1e1e2e", "#13131f"))
        tbl_f.pack(fill="both", expand=True)

        ctk.CTkLabel(tbl_f, text="전체 결과 (점수 순 정렬)",
                     font=("Malgun Gothic", 12, "bold"), text_color="#aaa",
                     ).pack(anchor="w", padx=12, pady=(8, 0))

        # 헤더
        hdr = ctk.CTkFrame(tbl_f, fg_color=("#252535", "#161626"))
        hdr.pack(fill="x", padx=12, pady=(4, 0))
        for col, w in [("순위", 40), ("수익률", 70), ("낙폭", 60), ("승률", 60),
                       ("거래", 45), ("점수", 60),
                       ("스윙TP", 60), ("스윙SL", 60),
                       ("스캘KR", 62), ("스캘US", 62), ("스캘SL", 62),
                       ("포지션", 62), ("비중%", 50)]:
            ctk.CTkLabel(hdr, text=col, width=w, font=("Malgun Gothic", 10, "bold"),
                         text_color="#90caf9", anchor="center").pack(side="left")

        self._table_scroll = ctk.CTkScrollableFrame(
            tbl_f, fg_color="transparent",
            scrollbar_button_color="#3a7bd5",
        )
        self._table_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self._table_wrapper = ctk.CTkFrame(self._table_scroll, fg_color="transparent")
        self._table_wrapper.pack(fill="x")

    # ── 차트 ─────────────────────────────────────────────────────

    def _init_chart(self):
        if self._chart_canvas:
            self._chart_canvas.get_tk_widget().destroy()
        self._chart_fig, self._chart_ax = plt.subplots(figsize=(7, 2.0), facecolor="#13131f")
        self._chart_ax.set_facecolor("#13131f")
        self._chart_ax.tick_params(colors="#888", labelsize=8)
        for spine in self._chart_ax.spines.values():
            spine.set_edgecolor("#333")
        self._chart_ax.set_xlabel("이터레이션", color="#888", fontsize=8)
        self._chart_ax.set_ylabel("최고 점수", color="#888", fontsize=8)
        self._chart_fig.tight_layout(pad=0.8)
        self._chart_canvas = FigureCanvasTkAgg(self._chart_fig, master=self._chart_container)
        self._chart_canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvas.draw()

    def _update_chart(self):
        if not self._scores_over_time:
            return
        self._chart_ax.clear()
        self._chart_ax.set_facecolor("#13131f")
        self._chart_ax.tick_params(colors="#888", labelsize=8)
        for spine in self._chart_ax.spines.values():
            spine.set_edgecolor("#333")
        self._chart_ax.set_xlabel("이터레이션", color="#888", fontsize=8)
        self._chart_ax.set_ylabel("누적 최고 점수", color="#888", fontsize=8)

        xs = list(range(1, len(self._scores_over_time) + 1))
        self._chart_ax.plot(xs, self._scores_over_time,
                            color="#3a7bd5", linewidth=1.5, marker="o", markersize=3)
        self._chart_ax.fill_between(xs, self._scores_over_time, alpha=0.15, color="#3a7bd5")
        self._chart_fig.tight_layout(pad=0.8)
        self._chart_canvas.draw()

    # ── 결과표 갱신 ──────────────────────────────────────────────

    def _rebuild_table(self):
        for w in self._table_wrapper.winfo_children():
            w.destroy()

        sorted_res = sorted(self._all_results, key=lambda x: -x.score)
        for rank, r in enumerate(sorted_res[:50], 1):
            bg = "#1a2a1a" if rank == 1 else ("#1e1e2e" if rank % 2 == 0 else "#16162a")
            row_f = ctk.CTkFrame(self._table_wrapper, fg_color=bg, height=26)
            row_f.pack(fill="x", pady=1)
            row_f.pack_propagate(False)

            pr_color = "#66bb6a" if r.profit_rate >= 0 else "#e57373"
            sc_color = "#ffd54f" if r.score >= 0 else "#e57373"

            def cell(text, w, color="#ccc"):
                ctk.CTkLabel(row_f, text=text, width=w, font=("Malgun Gothic", 10),
                             text_color=color, anchor="center").pack(side="left")

            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}")
            cell(medal,                         40)
            cell(f"{r.profit_rate:+.1f}%",      70, pr_color)
            cell(f"{r.max_drawdown:+.1f}%",     60, "#e57373")
            cell(f"{r.win_rate:.1f}%",          60)
            cell(str(r.total_trades),            45)
            cell(f"{r.score:.1f}",              60, sc_color)
            cell(f"{r.params.swing_tp*100:.1f}%",  60, "#80cbc4")
            cell(f"{r.params.swing_sl*100:.1f}%",  60, "#ef9a9a")
            cell(f"{r.params.scalp_tp_kr*100:.1f}%", 62, "#80cbc4")
            cell(f"{r.params.scalp_tp_us*100:.1f}%", 62, "#80cbc4")
            cell(f"{r.params.scalp_sl*100:.1f}%",    62, "#ef9a9a")
            cell(str(r.params.max_positions),        62)
            cell(f"{r.params.position_ratio*100:.0f}%", 50)

    # ── 최적 파라미터 표시 ───────────────────────────────────────

    def _show_best(self, r):
        p = r.params
        text = (
            f"[1위 파라미터]  점수: {r.score:.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"스윙  익절: {p.swing_tp*100:.1f}%   손절: {p.swing_sl*100:.1f}%\n"
            f"스캘핑  KR익절: {p.scalp_tp_kr*100:.1f}%\n"
            f"       US익절: {p.scalp_tp_us*100:.1f}%\n"
            f"       손절:  {p.scalp_sl*100:.1f}%\n"
            f"최대 보유 종목: {p.max_positions}개\n"
            f"종목당 비중:   {p.position_ratio*100:.0f}%\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"수익률: {r.profit_rate:+.2f}%   낙폭: {r.max_drawdown:+.2f}%\n"
            f"승률: {r.win_rate:.1f}%   거래: {r.total_trades}건\n"
            f"발견: {r.generation}세대 {r.iteration}번째 ({r.phase})"
        )
        self.best_param_box.configure(state="normal")
        self.best_param_box.delete("1.0", "end")
        self.best_param_box.insert("end", text)
        self.best_param_box.configure(state="disabled")

    # ── 최적 파라미터 적용 ───────────────────────────────────────

    def _apply_best(self):
        if not self._best:
            return
        p = self._best.params
        if not messagebox.askyesno("파라미터 적용",
            f"1위 파라미터를 적용하시겠습니까?\n\n"
            f"스윙 익절 {p.swing_tp*100:.1f}%  /  손절 {p.swing_sl*100:.1f}%\n"
            f"스캘핑 KR {p.scalp_tp_kr*100:.1f}% / US {p.scalp_tp_us*100:.1f}% / SL {p.scalp_sl*100:.1f}%\n"
            f"최대종목 {p.max_positions}개  /  비중 {p.position_ratio*100:.0f}%"
        ):
            return

        # config 적용
        config.SWING_TAKE_PROFIT    = p.swing_tp
        config.SWING_STOP_LOSS      = p.swing_sl
        config.SCALP_TAKE_PROFIT_KR = p.scalp_tp_kr
        config.SCALP_TAKE_PROFIT_US = p.scalp_tp_us
        config.SCALP_STOP_LOSS      = p.scalp_sl
        config.MAX_POSITIONS        = p.max_positions
        config.MAX_POSITION_RATIO   = p.position_ratio

        # DB 저장
        try:
            self.db.set_setting("take_profit",       p.swing_tp)
            self.db.set_setting("stop_loss",         p.swing_sl)
            self.db.set_setting("max_positions",     p.max_positions)
        except Exception:
            pass

        messagebox.showinfo("적용 완료",
            "최적 파라미터가 현재 세션에 적용되었습니다.\n"
            "설정 탭에서 저장하면 DB에도 영구 반영됩니다.")

    # ── 최적화 실행 ──────────────────────────────────────────────

    def _start(self):
        try:
            year  = int(self.year_e.get())
            month = int(self.month_e.get())
            dur   = int(self.dur_e.get())
            cap   = float(self.cap_e.get().replace(",", ""))
            rate  = float(self.rate_e.get())
            gens  = int(self.gen_e.get() or 5)
            pops  = int(self.pop_e.get() or 8)
        except ValueError:
            messagebox.showerror("입력 오류", "모든 수치 항목을 올바르게 입력하세요.")
            return

        if not self.kr_var.get() and not self.us_var.get():
            messagebox.showerror("시장 선택", "국내 또는 미국 중 하나 이상 선택하세요.")
            return

        gens = max(2, min(gens, 20))
        pops = max(4, min(pops, 20))
        total = gens * pops

        self._all_results.clear()
        self._scores_over_time.clear()
        self._best = None
        self._rebuild_table()
        self._init_chart()

        self.prog_bar.set(0)
        self.iter_label.configure(text=f"0 / {total}  (데이터 로드 중...)")
        self.status_label.configure(text="")
        self.best_label.configure(text="")
        self.best_param_box.configure(state="normal")
        self.best_param_box.delete("1.0", "end")
        self.best_param_box.configure(state="disabled")
        self.apply_btn.configure(state="disabled")

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._running = True

        def _run():
            from trader.optimizer import StrategyOptimizer
            self._optimizer = StrategyOptimizer()

            self._optimizer.run(
                start_year=year, start_month=month, duration_months=dur,
                initial_capital=cap, use_kr=self.kr_var.get(), use_us=self.us_var.get(),
                exchange_rate=rate, n_generations=gens, pop_size=pops,
                on_progress=self._on_progress,
                on_result=self._on_result,
                on_data_ready=self._on_data_ready,
            )
            self.after(0, self._on_done)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def _stop(self):
        if self._optimizer:
            self._optimizer.cancel()
        self._running = False
        self.stop_btn.configure(state="disabled")
        self.iter_label.configure(text=self.iter_label.cget("text") + "  [중지 요청]")

    # ── 콜백 (백그라운드 → GUI 스레드) ──────────────────────────

    def _on_data_ready(self):
        self.after(0, lambda: self.status_label.configure(
            text="데이터 로드 완료 — 최적화 시작"))

    def _on_progress(self, current: int, total: int, msg: str, params):
        def _update():
            frac = current / total if total > 0 else 0
            self.prog_bar.set(frac)
            self.iter_label.configure(text=f"{current} / {total}")
            self.status_label.configure(text=msg[:80])
        self.after(0, _update)

    def _on_result(self, opt_r, all_so_far: list):
        def _update():
            self._all_results = list(all_so_far)

            # 누적 최고 점수 추적
            best_score = max(r.score for r in all_so_far)
            self._scores_over_time.append(best_score)

            # 1위 갱신
            sorted_r = sorted(all_so_far, key=lambda x: -x.score)
            new_best  = sorted_r[0]
            if self._best is None or new_best.score > self._best.score:
                self._best = new_best
                self.best_label.configure(
                    text=f"현재 1위: 수익률 {new_best.profit_rate:+.1f}%  점수 {new_best.score:.1f}")
                self._show_best(new_best)

            self._update_chart()
            self._rebuild_table()

        self.after(0, _update)

    def _on_done(self):
        self._running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

        if self._best:
            self.apply_btn.configure(state="normal")
            self.iter_label.configure(
                text=f"완료  —  총 {len(self._all_results)}회 시도")
            self.status_label.configure(
                text=f"최고 수익률: {self._best.profit_rate:+.2f}%  "
                     f"점수: {self._best.score:.2f}  "
                     f"({self._best.generation}세대/{self._best.iteration}번째)")
        else:
            self.iter_label.configure(text="중단됨")
            self.status_label.configure(text="")
