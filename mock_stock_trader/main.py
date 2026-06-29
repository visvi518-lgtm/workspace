"""모의주식 자동매매 시스템 진입점"""
import os
import sys
import customtkinter as ctk

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(__file__))

import config
from db.database         import Database
from trader.portfolio    import Portfolio
from trader.strategy     import TechnicalStrategy
from crawler.naver_crawler import NaverCrawler
from crawler.yahoo_crawler import YahooCrawler
from gui.main_window     import MainWindow


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    db        = Database("mock_stock_trader.db")
    portfolio = Portfolio(db)

    # 초기 자금 DB 기록 (최초 실행 시)
    if not db.get_setting("initial_capital"):
        db.set_setting("initial_capital", config.DEFAULT_INITIAL_CAPITAL)

    strategy = TechnicalStrategy()
    naver    = NaverCrawler()
    yahoo    = YahooCrawler()

    app = MainWindow(
        db=db,
        portfolio=portfolio,
        naver=naver,
        yahoo=yahoo,
        strategy=strategy,
    )
    app.mainloop()
    db.close()


if __name__ == "__main__":
    main()
