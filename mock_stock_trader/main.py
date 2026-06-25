import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from db.database import Database
from crawler.naver_crawler import NaverCrawler
from crawler.yahoo_crawler import YahooCrawler
from trader.strategy import TechnicalStrategy
from trader.portfolio import VirtualPortfolio
from gui.main_window import MainWindow
import config


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    db = Database()
    initial_capital = float(db.get_setting("initial_capital", config.DEFAULT_INITIAL_CAPITAL))

    naver = NaverCrawler()
    yahoo = YahooCrawler()
    strategy = TechnicalStrategy()
    portfolio = VirtualPortfolio(db, initial_capital)

    app = MainWindow(db, portfolio, naver, yahoo, strategy)
    app.mainloop()


if __name__ == "__main__":
    main()
