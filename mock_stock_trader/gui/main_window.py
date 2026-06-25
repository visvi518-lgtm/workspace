import customtkinter as ctk
from gui.dashboard_tab import DashboardTab
from gui.portfolio_tab import PortfolioTab
from gui.log_tab import LogTab
from gui.settings_tab import SettingsTab
from gui.backtest_tab import BacktestTab

UPDATE_INTERVAL_MS = 10_000  # 10초마다 UI 갱신


class MainWindow(ctk.CTk):
    def __init__(self, db, portfolio, naver, yahoo, strategy):
        super().__init__()
        self.db = db
        self.portfolio = portfolio

        self.title("모의주식 자동매매 시스템")
        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.configure(fg_color=("#1a1a2e", "#0f0f1a"))

        # AutoTrader 생성 (GUI 콜백 포함)
        from trader.auto_trader import AutoTrader
        self.auto_trader = AutoTrader(
            db=db,
            portfolio=portfolio,
            strategy=strategy,
            naver=naver,
            yahoo=yahoo,
            on_trade=self._on_trade,
            on_log=self._on_log,
        )

        self._build_header()
        self._build_tabs()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._schedule_update()

    def _build_header(self):
        header = ctk.CTkFrame(self, height=50, fg_color=("#16213e", "#0d0d1a"), corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="  📈  모의주식 자동매매",
            font=("Malgun Gothic", 16, "bold"),
            text_color="#90caf9",
        ).pack(side="left", padx=15)

        self.market_label = ctk.CTkLabel(
            header,
            text="",
            font=("Malgun Gothic", 11),
            text_color="gray",
        )
        self.market_label.pack(side="right", padx=20)
        self._update_market_status()

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=("#1e1e2e", "#13131f"),
            segmented_button_fg_color=("#2b2b3b", "#1a1a2a"),
            segmented_button_selected_color="#3a7bd5",
            segmented_button_unselected_color=("#2b2b3b", "#1a1a2a"),
            text_color="white",
        )
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        for name in ("대시보드", "포트폴리오", "거래 로그", "백테스트", "설정"):
            self.tabview.add(name)

        self.tab_dashboard = DashboardTab(
            self.tabview.tab("대시보드"), self.db, self.portfolio, self.auto_trader
        )
        self.tab_dashboard.pack(fill="both", expand=True)

        self.tab_portfolio = PortfolioTab(
            self.tabview.tab("포트폴리오"), self.db, self.portfolio, self.auto_trader
        )
        self.tab_portfolio.pack(fill="both", expand=True)

        self.tab_log = LogTab(
            self.tabview.tab("거래 로그"), self.db, self.auto_trader
        )
        self.tab_log.pack(fill="both", expand=True)

        self.tab_backtest = BacktestTab(
            self.tabview.tab("백테스트"), self.db
        )
        self.tab_backtest.pack(fill="both", expand=True)

        self.tab_settings = SettingsTab(
            self.tabview.tab("설정"), self.db, self.portfolio, self.auto_trader
        )
        self.tab_settings.pack(fill="both", expand=True)

    def _schedule_update(self):
        self._update_all()
        self.after(UPDATE_INTERVAL_MS, self._schedule_update)

    def _update_all(self):
        try:
            self.tab_dashboard.update()
            self.tab_portfolio.update()
            self.tab_log.update()
            self.tab_settings.update()
            self._update_market_status()
        except Exception as e:
            print(f"UI 갱신 오류: {e}")

    def _update_market_status(self):
        from trader.auto_trader import AutoTrader
        kr = "🟢 국내장 운영중" if AutoTrader.is_kr_market_open() else "🔴 국내장 마감"
        us = "🟢 미국장 운영중" if AutoTrader.is_us_market_open() else "🔴 미국장 마감"
        self.market_label.configure(text=f"{kr}   {us}")

    def _on_trade(self, trade_type: str, name: str, price: float, reason: str):
        self.after(0, self._update_all)

    def _on_log(self, msg: str):
        self.after(0, lambda: self.tab_log.append_log(msg))

    def _on_close(self):
        if self.auto_trader.is_running:
            self.auto_trader.stop()
        self.destroy()
