import threading
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import date
from dateutil.relativedelta import relativedelta
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime

from trader.backtester import Backtester, validate_period
from trader.strategy import TechnicalStrategy
import config


def _fmt_krw(v: float) -> str:
    return f"{v:,.0f}원"

def _sign_fmt(v: float, unit: str = "원") -> str:
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:,.0f}{unit}"

def _color(v: float) -> str:
    return "#ef5350" if v >= 0 else "#42a5f5"


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, width: int = 160):
        super().__init__(parent, corner_radius=10, width=width, fg_color=("#252535", "#1a1a2a"))
        self.configure(width=width)
        ctk.CTkLabel(self, text=title, font=("Malgun Gothic", 10), text_color="gray").pack(pady=(8, 1))
        self.val = ctk.CTkLabel(self, text="—", font=("Malgun Gothic", 15, "bold"))
        self.val.pack(pady=(0, 8))

    def set(self, text: str, color: str = "white"):
        self.val.configure(text=text, text_color=color)


class BacktestTab(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.strategy = TechnicalStrategy()
        self.backtester = Backtester(self.strategy)
        self._result = None
        self._running = False
        self._build()

    def _build(self):
        # ── 상단 레이아웃: 입력 패널(좌) + 요약 결과(우) ──
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(10, 5))
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=2)
        top.rowconfigure(0, weight=1)

        self._build_input(top)
        self._build_summary(top)

        # ── 차트 ──
        chart_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("#252535", "#1a1a2a"))
        chart_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(chart_frame, text="포트폴리오 수익률 추이  (2년 이내: 시간봉 / 초과: 일봉)",
                     font=("Malgun Gothic", 11, "bold")).pack(anchor="w", padx=12, pady=(8, 0))
        self.fig = Figure(figsize=(10, 2.8), dpi=96, facecolor="#1a1a2a")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#1a1a2a")
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="x", padx=10, pady=(0, 10))

        # ── 하단 탭: 거래내역 + 종목별 성과 ──
        self.sub_tab = ctk.CTkTabview(self, height=230,
                                       fg_color=("#252535", "#1a1a2a"),
                                       segmented_button_selected_color="#3a7bd5",
                                       text_color="white")
        self.sub_tab.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.sub_tab.add("거래 내역")
        self.sub_tab.add("종목별 성과")
        self.sub_tab.add("이벤트 분석")

        self._build_trade_table(self.sub_tab.tab("거래 내역"))
        self._build_perf_table(self.sub_tab.tab("종목별 성과"))
        self._build_event_tab(self.sub_tab.tab("이벤트 분석"))

    def _build_input(self, parent):
        box = ctk.CTkFrame(parent, corner_radius=12, fg_color=("#252535", "#1a1a2a"))
        box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(box, text="과거 수익 시뮬레이션",
                     font=("Malgun Gothic", 14, "bold"), text_color="#90caf9").pack(padx=14, pady=(12, 6), anchor="w")

        def row(label, widget_cb):
            f = ctk.CTkFrame(box, fg_color="transparent")
            f.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(f, text=label, font=("Malgun Gothic", 11), width=110, anchor="w").pack(side="left")
            w = widget_cb(f)
            w.pack(side="left", padx=(6, 0))
            return w

        # 시작 연도
        self.year_entry = row("시작 연도",
            lambda p: ctk.CTkEntry(p, width=90, placeholder_text="예: 2020"))
        self.year_entry.insert(0, "2022")

        # 시작 월
        self.month_var = ctk.StringVar(value="01")
        self.month_menu = row("시작 월",
            lambda p: ctk.CTkOptionMenu(p, width=80, variable=self.month_var,
                values=[f"{m:02d}" for m in range(1, 13)]))

        # 기간
        self.duration_entry = row("기간 (개월)",
            lambda p: ctk.CTkEntry(p, width=90, placeholder_text="예: 3"))
        self.duration_entry.insert(0, "3")

        # 초기 자금
        self.capital_entry = row("초기 자금 (원)",
            lambda p: ctk.CTkEntry(p, width=120, placeholder_text="10000000"))
        init_cap = self.db.get_setting("initial_capital", str(config.DEFAULT_INITIAL_CAPITAL))
        self.capital_entry.insert(0, init_cap)

        # 환율
        self.rate_entry = row("원/달러 환율",
            lambda p: ctk.CTkEntry(p, width=90, placeholder_text="1350"))
        self.rate_entry.insert(0, self.db.get_setting("exchange_rate", "1350"))

        # 시장 선택
        mf = ctk.CTkFrame(box, fg_color="transparent")
        mf.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(mf, text="시장 선택", font=("Malgun Gothic", 11), width=110, anchor="w").pack(side="left")
        self.kr_var = ctk.BooleanVar(value=True)
        self.us_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(mf, text="국내", variable=self.kr_var, width=70).pack(side="left", padx=(6, 0))
        ctk.CTkCheckBox(mf, text="해외", variable=self.us_var, width=70).pack(side="left", padx=(4, 0))

        # 진행 상태
        self.progress_label = ctk.CTkLabel(box, text="", font=("Consolas", 10), text_color="#aaa")
        self.progress_label.pack(padx=14, pady=(6, 0), anchor="w")
        self.progress_bar = ctk.CTkProgressBar(box, width=260)
        self.progress_bar.set(0)
        self.progress_bar.pack(padx=14, pady=(2, 6))

        # 실행/취소 버튼
        btn_frame = ctk.CTkFrame(box, fg_color="transparent")
        btn_frame.pack(padx=14, pady=(2, 14))
        self.run_btn = ctk.CTkButton(
            btn_frame, text="▶  시뮬레이션 실행", command=self._run,
            fg_color="#1565c0", hover_color="#0d47a1",
            font=("Malgun Gothic", 12, "bold"), width=165
        )
        self.run_btn.pack(side="left", padx=(0, 6))
        self.cancel_btn = ctk.CTkButton(
            btn_frame, text="중지", command=self._cancel,
            fg_color="#5d1a1a", hover_color="#4e342e",
            width=70, state="disabled"
        )
        self.cancel_btn.pack(side="left")

    def _build_summary(self, parent):
        box = ctk.CTkFrame(parent, corner_radius=12, fg_color=("#252535", "#1a1a2a"))
        box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ctk.CTkLabel(box, text="시뮬레이션 결과",
                     font=("Malgun Gothic", 14, "bold"), text_color="#90caf9").pack(padx=14, pady=(12, 6), anchor="w")

        # 카드 그리드
        card_frame = ctk.CTkFrame(box, fg_color="transparent")
        card_frame.pack(fill="x", padx=10)
        for c in range(4):
            card_frame.columnconfigure(c, weight=1)

        self.c_init = StatCard(card_frame, "초기 자금")
        self.c_init.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        self.c_final = StatCard(card_frame, "최종 자산")
        self.c_final.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        self.c_profit = StatCard(card_frame, "총 손익")
        self.c_profit.grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        self.c_rate = StatCard(card_frame, "수익률")
        self.c_rate.grid(row=0, column=3, padx=3, pady=3, sticky="ew")

        self.c_trades = StatCard(card_frame, "총 거래")
        self.c_trades.grid(row=1, column=0, padx=3, pady=3, sticky="ew")
        self.c_win = StatCard(card_frame, "승률")
        self.c_win.grid(row=1, column=1, padx=3, pady=3, sticky="ew")
        self.c_mdd = StatCard(card_frame, "최대 낙폭")
        self.c_mdd.grid(row=1, column=2, padx=3, pady=3, sticky="ew")
        self.c_period = StatCard(card_frame, "분석 기간")
        self.c_period.grid(row=1, column=3, padx=3, pady=3, sticky="ew")

        # 메시지 라벨
        self.result_msg = ctk.CTkLabel(box, text="시뮬레이션을 실행하면 결과가 표시됩니다.",
                                        font=("Malgun Gothic", 11), text_color="#666")
        self.result_msg.pack(padx=14, pady=(8, 12))

    def _build_trade_table(self, parent):
        style = ttk.Style()
        style.configure("BT.Treeview",
            background="#1a1a2a", foreground="white",
            rowheight=26, fieldbackground="#1a1a2a", font=("Malgun Gothic", 10))
        style.configure("BT.Treeview.Heading",
            background="#252535", foreground="#aaa", font=("Malgun Gothic", 10, "bold"))
        style.map("BT.Treeview", background=[("selected", "#3a3a5c")])

        cols = ("date", "time", "market", "type", "name", "price", "qty", "amount", "fee", "profit", "rate", "reason")
        hdrs = [
            ("date", "날짜", 90), ("time", "시간", 60), ("market", "시장", 50), ("type", "구분", 55),
            ("name", "종목", 100), ("price", "단가", 90), ("qty", "수량", 55),
            ("amount", "거래금액", 100), ("fee", "수수료", 70),
            ("profit", "손익", 90), ("rate", "수익률", 70), ("reason", "매매 이유", 300),
        ]
        self.trade_tree = ttk.Treeview(parent, style="BT.Treeview", show="headings", columns=cols)
        for col, hdr, w in hdrs:
            self.trade_tree.heading(col, text=hdr)
            self.trade_tree.column(col, width=w, anchor="center")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.trade_tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.trade_tree.xview)
        self.trade_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.trade_tree.pack(fill="both", expand=True)

    def _build_perf_table(self, parent):
        style = ttk.Style()
        style.configure("BTP.Treeview",
            background="#1a1a2a", foreground="white",
            rowheight=26, fieldbackground="#1a1a2a", font=("Malgun Gothic", 10))
        style.configure("BTP.Treeview.Heading",
            background="#252535", foreground="#aaa", font=("Malgun Gothic", 10, "bold"))
        style.map("BTP.Treeview", background=[("selected", "#3a3a5c")])

        cols = ("market", "name", "code", "trades", "profit", "profit_rate")
        hdrs = [
            ("market", "시장", 60), ("name", "종목명", 140), ("code", "코드", 90),
            ("trades", "거래 수", 70), ("profit", "실현손익", 120), ("profit_rate", "수익률", 90),
        ]
        self.perf_tree = ttk.Treeview(parent, style="BTP.Treeview", show="headings", columns=cols)
        for col, hdr, w in hdrs:
            self.perf_tree.heading(col, text=hdr)
            self.perf_tree.column(col, width=w, anchor="center")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.perf_tree.yview)
        self.perf_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.perf_tree.pack(fill="both", expand=True)

    # ── 실행 ──

    def _run(self):
        if self._running:
            return

        # 입력값 파싱
        try:
            year = int(self.year_entry.get())
            month = int(self.month_var.get())
            duration = int(self.duration_entry.get())
            capital = float(self.capital_entry.get().replace(",", ""))
            exchange_rate = float(self.rate_entry.get())
        except ValueError:
            messagebox.showerror("입력 오류", "연도, 기간, 자금, 환율을 올바르게 입력해 주세요.", parent=self)
            return

        use_kr = self.kr_var.get()
        use_us = self.us_var.get()

        # 날짜 유효성 검사
        ok, msg = validate_period(year, month, duration, use_kr, use_us)
        if not ok:
            messagebox.showwarning("날짜 오류", msg, parent=self)
            return

        stop_loss = float(self.db.get_setting("stop_loss", config.STOP_LOSS_RATE))
        take_profit = float(self.db.get_setting("take_profit", config.TAKE_PROFIT_RATE))
        max_pos = int(self.db.get_setting("max_positions", config.MAX_POSITIONS))

        self._running = True
        self.run_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.set(0)
        self.backtester._cancelled = False

        def worker():
            total_stocks = (len(config.DOMESTIC_STOCK_POOL) if use_kr else 0) + \
                           (len(config.US_STOCK_POOL) if use_us else 0)
            loaded = [0]

            def on_progress(msg: str):
                if "데이터 로드" in msg:
                    loaded[0] += 1
                    frac = loaded[0] / total_stocks if total_stocks else 0
                    self.after(0, lambda f=frac, m=msg: self._update_progress(f * 0.8, m))
                elif "시뮬레이션" in msg:
                    self.after(0, lambda: self._update_progress(0.9, msg))
                elif "완료" in msg:
                    self.after(0, lambda: self._update_progress(1.0, msg))
                else:
                    self.after(0, lambda m=msg: self._update_progress(None, m))

            result = self.backtester.run(
                start_year=year, start_month=month, duration_months=duration,
                initial_capital=capital, use_kr=use_kr, use_us=use_us,
                exchange_rate=exchange_rate, stop_loss=stop_loss,
                take_profit=take_profit, max_positions=max_pos,
                progress_callback=on_progress,
            )
            self.after(0, lambda: self._on_done(result))

        threading.Thread(target=worker, daemon=True).start()

    def _cancel(self):
        self.backtester.cancel()
        self.progress_label.configure(text="취소됨")
        self._set_idle()

    def _update_progress(self, frac, msg: str):
        self.progress_label.configure(text=msg)
        if frac is not None:
            self.progress_bar.set(frac)

    def _on_done(self, result):
        self._set_idle()
        if result is None:
            self.result_msg.configure(text="시뮬레이션이 취소되었거나 데이터를 가져올 수 없습니다.", text_color="#e57373")
            return
        self._result = result
        self._show_result(result)
        self._run_event_analysis(result)

    def _set_idle(self):
        self._running = False
        self.run_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")

    def _show_result(self, r):
        # 요약 카드
        color = _color(r.profit)
        self.c_init.set(_fmt_krw(r.initial_capital))
        self.c_final.set(_fmt_krw(r.final_value), color)
        sign = "+" if r.profit >= 0 else ""
        self.c_profit.set(f"{sign}{r.profit:,.0f}원", color)
        self.c_rate.set(f"{sign}{r.profit_rate:.2f}%", color)

        win_rate = r.win_trades / r.sell_trades * 100 if r.sell_trades > 0 else 0
        self.c_trades.set(f"{r.total_trades}건\n(매수{r.buy_trades}/매도{r.sell_trades})")
        self.c_win.set(f"{win_rate:.1f}%\n({r.win_trades}승 {r.loss_trades}패)", _color(win_rate - 50))
        self.c_mdd.set(f"{r.max_drawdown:.2f}%", "#42a5f5" if r.max_drawdown < 0 else "white")
        start_s = r.start_date[:7].replace("-", ".")
        end_s = r.end_date[:7].replace("-", ".")
        self.c_period.set(f"{start_s}\n~ {end_s}")

        verdict = "수익 전략" if r.profit >= 0 else "손실 전략"
        self.result_msg.configure(
            text=f"분석 완료 | {r.total_trades}건 거래, {r.win_trades}승 {r.loss_trades}패 → {verdict}",
            text_color=color
        )

        # 차트 (1h 데이터 있으면 시간봉, 없으면 일봉)
        self.ax.clear()
        self.ax.set_facecolor("#1a1a2a")
        use_hourly = getattr(r, "used_hourly", False) and bool(getattr(r, "hourly_history", []))
        if use_hourly:
            history = r.hourly_history
            dates = [datetime.strptime(d["datetime"], "%Y-%m-%d %H:%M") for d in history]
            fmt = "%m/%d %H:%M"
            chart_title = "포트폴리오 수익률 추이 (시간봉)"
        elif r.portfolio_history:
            history = r.portfolio_history
            dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in history]
            fmt = "%y/%m/%d"
            chart_title = "포트폴리오 수익률 추이 (일봉)"
        else:
            history = []
            dates = []
            chart_title = "포트폴리오 수익률 추이"

        if dates:
            vals  = [d["value"] for d in history]
            rates = [(v - r.initial_capital) / r.initial_capital * 100 for v in vals]
            c = _color(rates[-1] if rates else 0)
            self.ax.plot(dates, rates, color=c, linewidth=1.2)
            self.ax.axhline(0, color="gray", linewidth=0.6, linestyle="--")
            self.ax.fill_between(dates, 0, rates, alpha=0.10, color=c)
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
            self.fig.autofmt_xdate(rotation=30, ha="right")
        self.ax.tick_params(colors="gray", labelsize=8)
        self.ax.spines[:].set_color("#444")
        self.ax.set_ylabel("수익률(%)", color="gray", fontsize=8, fontname="Malgun Gothic")
        self.ax.set_title(chart_title, color="#90caf9", fontsize=9, fontname="Malgun Gothic")
        self.fig.tight_layout(pad=1.0)
        self.canvas.draw()

        # 거래 내역 테이블 (날짜 + 시간 컬럼)
        self.trade_tree.delete(*self.trade_tree.get_children())
        for t in r.trades:
            typ = "▲매수" if t.trade_type == "BUY" else "▼매도"
            pft = ""
            rt  = ""
            if t.profit is not None:
                sg  = "+" if t.profit >= 0 else ""
                pft = f"{sg}{t.profit:,.0f}"
                rt  = f"{sg}{t.profit_rate:.2f}%"
            tag = "buy" if t.trade_type == "BUY" else ("pos" if (t.profit or 0) >= 0 else "neg")
            trade_time = getattr(t, "time", "")
            self.trade_tree.insert("", "end", tags=(tag,), values=(
                t.date, trade_time, t.market, typ, t.name,
                f"{t.price:,.0f}", t.quantity, f"{t.amount:,.0f}",
                f"{t.fee:,.0f}", pft, rt, t.reason,
            ))
        self.trade_tree.tag_configure("buy", foreground="#29b6f6")
        self.trade_tree.tag_configure("pos", foreground="#ef5350")
        self.trade_tree.tag_configure("neg", foreground="#42a5f5")

        # 종목별 성과 테이블
        self.perf_tree.delete(*self.perf_tree.get_children())
        for p in r.stock_performances:
            sg = "+" if p["profit"] >= 0 else ""
            tag = "pos" if p["profit"] >= 0 else "neg"
            self.perf_tree.insert("", "end", tags=(tag,), values=(
                p["market"], p["name"], p["code"], p["trades"],
                f"{sg}{p['profit']:,.0f}원",
                f"{sg}{p['profit_rate']:.2f}%",
            ))
        self.perf_tree.tag_configure("pos", foreground="#ef5350")
        self.perf_tree.tag_configure("neg", foreground="#42a5f5")

    # ── 이벤트 분석 탭 ──

    def _build_event_tab(self, parent):
        self.event_scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color="#3a7bd5",
            scrollbar_button_hover_color="#5a9bf5",
        )
        self.event_scroll.pack(fill="both", expand=True)
        # 내용을 담는 wrapper frame — destroy/recreate로 초기화
        self._evt_wrapper = ctk.CTkFrame(self.event_scroll, fg_color="transparent")
        self._evt_wrapper.pack(fill="x", expand=True)
        ctk.CTkLabel(
            self._evt_wrapper,
            text="백테스트를 실행하면 최대 낙폭 / 최고 수익 이벤트 분석과 관련 뉴스가 자동으로 표시됩니다.",
            font=("Malgun Gothic", 11), text_color="#607d8b",
        ).pack(pady=30)

    def _reset_evt(self):
        """이벤트 탭 내용 초기화 후 새 wrapper 반환"""
        if hasattr(self, "_evt_wrapper") and self._evt_wrapper.winfo_exists():
            self._evt_wrapper.destroy()
        self._evt_wrapper = ctk.CTkFrame(self.event_scroll, fg_color="transparent")
        self._evt_wrapper.pack(fill="x", expand=True)
        return self._evt_wrapper

    def _run_event_analysis(self, result):
        w = self._reset_evt()
        ctk.CTkLabel(
            w,
            text="이벤트 분석 + 뉴스 수집 중... (최대 30초 소요)",
            font=("Malgun Gothic", 11), text_color="#90caf9",
        ).pack(pady=(20, 6))
        prog = ctk.CTkProgressBar(w, width=320, mode="indeterminate")
        prog.pack()
        prog.start()

        def worker():
            from trader.news_analyzer import NewsAnalyzer
            try:
                analysis = NewsAnalyzer().analyze(result)
            except Exception:
                analysis = None
            self.after(0, lambda: self._show_event_analysis(analysis))

        threading.Thread(target=worker, daemon=True).start()

    def _show_event_analysis(self, analysis):
        self._reset_evt()

        if analysis is None:
            ctk.CTkLabel(
                self._evt_wrapper,
                text="이벤트 분석 중 오류가 발생했습니다.",
                font=("Malgun Gothic", 11), text_color="#ef5350",
            ).pack(pady=20)
            return

        # 최대 낙폭 이벤트
        if analysis.mdd.date:
            self._evt_section(
                title=f"최대 낙폭 이벤트    날짜: {analysis.mdd.date[:10]}   낙폭: {analysis.mdd.rate:+.2f}%",
                hdr_color="#1a237e",
                section=analysis.mdd,
            )

        # 최고 수익 이벤트
        if analysis.peak.date:
            self._evt_section(
                title=f"최고 수익 이벤트    날짜: {analysis.peak.date[:10]}   최고: {analysis.peak.rate:+.2f}%",
                hdr_color="#1b5e20",
                section=analysis.peak,
            )

        # 하위 성과 종목 (손절/손실 多)
        if analysis.losers:
            self._evt_group_header(
                f"하위 성과 종목 분석 ({len(analysis.losers)}종목)", "#4a1515"
            )
            for sa in analysis.losers:
                self._evt_stock_card(sa)

        # 상위 성과 종목 (익절/수익 多)
        if analysis.winners:
            self._evt_group_header(
                f"상위 성과 종목 분석 ({len(analysis.winners)}종목)", "#0d3321"
            )
            for sa in analysis.winners:
                self._evt_stock_card(sa)

        if not analysis.losers and not analysis.winners:
            ctk.CTkLabel(
                self._evt_wrapper,
                text="종목별 성과 데이터가 부족합니다. (매도 거래 없음)",
                font=("Malgun Gothic", 11), text_color="#607d8b",
            ).pack(pady=10)

        ctk.CTkLabel(
            self._evt_wrapper,
            text=(
                "※ 뉴스는 네이버 뉴스 검색 및 Yahoo Finance에서 수집됩니다.  "
                "오래된 날짜(~3년 이상)는 검색 결과가 제한될 수 있습니다."
            ),
            font=("Malgun Gothic", 9), text_color="#455a64",
        ).pack(anchor="w", padx=12, pady=(6, 12))

    def _evt_section(self, title: str, hdr_color: str, section):
        card = ctk.CTkFrame(self._evt_wrapper, corner_radius=10, fg_color=("#1c1c2c", "#131320"))
        card.pack(fill="x", padx=10, pady=6)

        hdr = ctk.CTkFrame(card, corner_radius=0, fg_color=hdr_color, height=30)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text=f"  {title}",
            font=("Malgun Gothic", 11, "bold"), text_color="white",
        ).pack(side="left", padx=6, pady=4)

        if section.stocks:
            stock_text = "  |  ".join(
                f"{s.name} ({'+' if s.profit >= 0 else ''}{s.profit:,.0f}원)"
                for s in section.stocks[:4]
            )
            rw = ctk.CTkFrame(card, fg_color="transparent")
            rw.pack(fill="x", padx=10, pady=(8, 2))
            ctk.CTkLabel(rw, text="관련 종목", font=("Malgun Gothic", 10), text_color="#90caf9", width=70, anchor="w").pack(side="left")
            ctk.CTkLabel(rw, text=stock_text, font=("Malgun Gothic", 10), text_color="#ccc").pack(side="left", padx=6)

        ctk.CTkLabel(card, text="기술적 분석", font=("Malgun Gothic", 10, "bold"), text_color="#90caf9", anchor="w").pack(fill="x", padx=10, pady=(6, 2))
        tb = ctk.CTkTextbox(card, height=80, font=("Malgun Gothic", 10), fg_color="#0d1117", text_color="#cdd6e0")
        tb.pack(fill="x", padx=10, pady=(0, 4))
        tb.insert("1.0", section.tech_summary or "데이터 없음")
        tb.configure(state="disabled")

        ctk.CTkLabel(card, text="관련 뉴스", font=("Malgun Gothic", 10, "bold"), text_color="#90caf9", anchor="w").pack(fill="x", padx=10, pady=(4, 2))
        if section.news:
            lines = []
            for item in section.news:
                prefix = f"[{item.date}] " if item.date else ""
                src = f"  ({item.source})" if item.source else ""
                lines.append(f"▸ {prefix}{item.title}{src}")
                if item.desc:
                    lines.append(f"   └ {item.desc}")
            nb = ctk.CTkTextbox(card, height=max(70, len(section.news) * 22 + 10),
                                font=("Malgun Gothic", 10), fg_color="#0d1117", text_color="#e8eaf6")
            nb.pack(fill="x", padx=10, pady=(0, 12))
            nb.insert("1.0", "\n".join(lines))
            nb.configure(state="disabled")
        else:
            ctk.CTkLabel(
                card, anchor="w",
                text="  뉴스 검색 결과 없음 (해당 날짜 아카이브 제한 또는 네트워크 오류)",
                font=("Malgun Gothic", 10), text_color="#607d8b",
            ).pack(fill="x", padx=10, pady=(0, 12))

    def _evt_group_header(self, text: str, color: str):
        h = ctk.CTkFrame(self._evt_wrapper, corner_radius=0, fg_color=color, height=26)
        h.pack(fill="x", padx=10, pady=(10, 2))
        h.pack_propagate(False)
        ctk.CTkLabel(h, text=f"  {text}", font=("Malgun Gothic", 11, "bold"), text_color="white").pack(side="left", pady=3, padx=6)

    def _evt_stock_card(self, sa):
        sign = "+" if sa.profit >= 0 else ""
        pft_col = "#ef5350" if sa.profit >= 0 else "#42a5f5"
        arrow = "▲" if sa.profit >= 0 else "▼"

        card = ctk.CTkFrame(self._evt_wrapper, corner_radius=8, fg_color=("#1c1c2c", "#131320"))
        card.pack(fill="x", padx=10, pady=3)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(
            top,
            text=f"  {arrow}  {sa.name}  ({sa.market})",
            font=("Malgun Gothic", 12, "bold"), text_color="white",
        ).pack(side="left")
        ctk.CTkLabel(
            top,
            text=f"손익: {sign}{sa.profit:,.0f}원 ({sign}{sa.profit_rate:.2f}%)",
            font=("Malgun Gothic", 11, "bold"), text_color=pft_col,
        ).pack(side="right")

        sb = ctk.CTkTextbox(card, height=46, font=("Malgun Gothic", 10), fg_color="#0d1117", text_color="#cdd6e0")
        sb.pack(fill="x", padx=10, pady=(2, 4))
        sb.insert("1.0", sa.summary)
        sb.configure(state="disabled")

        if sa.news:
            ctk.CTkLabel(card, text="  관련 뉴스:", font=("Malgun Gothic", 10), text_color="#90caf9", anchor="w").pack(fill="x", padx=10)
            nb = ctk.CTkTextbox(card, height=max(48, len(sa.news) * 20),
                                font=("Malgun Gothic", 10), fg_color="#0d1117", text_color="#e8eaf6")
            nb.pack(fill="x", padx=10, pady=(0, 10))
            for item in sa.news:
                prefix = f"[{item.date}] " if item.date else ""
                nb.insert("end", f"  ▸ {prefix}{item.title}\n")
            nb.configure(state="disabled")
        else:
            ctk.CTkLabel(
                card, anchor="w", text="  뉴스 검색 결과 없음",
                font=("Malgun Gothic", 10), text_color="#607d8b",
            ).pack(fill="x", padx=10, pady=(0, 10))
