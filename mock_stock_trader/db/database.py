import sqlite3
import threading
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "portfolio.db"


class Database:
    def __init__(self):
        DB_PATH.parent.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        with self._lock:
            cur = self.conn.cursor()
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );

                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    market TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    buy_date TEXT NOT NULL,
                    buy_reason TEXT,
                    mode TEXT DEFAULT 'swing',
                    UNIQUE(code, market)
                );

                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    market TEXT NOT NULL,
                    trade_type TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    fee REAL NOT NULL,
                    profit REAL,
                    profit_rate REAL,
                    reason TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_value REAL NOT NULL,
                    cash REAL NOT NULL,
                    holdings_value REAL NOT NULL
                );
            """)
            self.conn.commit()
            self._migrate()

    def _migrate(self):
        """기존 DB에 mode 컬럼 추가 (호환성)"""
        cur = self.conn.execute("PRAGMA table_info(portfolio)")
        existing_cols = {row["name"] for row in cur.fetchall()}
        if "mode" not in existing_cols:
            self.conn.execute("ALTER TABLE portfolio ADD COLUMN mode TEXT DEFAULT 'swing'")
            self.conn.commit()

    def get_setting(self, key, default=None):
        with self._lock:
            cur = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cur.fetchone()
            return row["value"] if row else default

    def set_setting(self, key, value):
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
                (key, str(value))
            )
            self.conn.commit()

    def add_trade(self, trade: dict):
        with self._lock:
            self.conn.execute("""
                INSERT INTO trades
                (timestamp, code, name, market, trade_type, price, quantity, amount, fee, profit, profit_rate, reason)
                VALUES (:timestamp, :code, :name, :market, :trade_type, :price, :quantity, :amount, :fee, :profit, :profit_rate, :reason)
            """, trade)
            self.conn.commit()

    def get_trades(self, limit=200):
        with self._lock:
            cur = self.conn.execute(
                "SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
            return [dict(r) for r in cur.fetchall()]

    def get_portfolio(self):
        with self._lock:
            cur = self.conn.execute("SELECT * FROM portfolio")
            return [dict(r) for r in cur.fetchall()]

    def get_position(self, code, market):
        with self._lock:
            cur = self.conn.execute(
                "SELECT * FROM portfolio WHERE code=? AND market=?", (code, market)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def upsert_position(self, code, name, market, quantity, avg_price, buy_date, buy_reason, mode="swing"):
        with self._lock:
            self.conn.execute("""
                INSERT INTO portfolio (code, name, market, quantity, avg_price, buy_date, buy_reason, mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(code, market) DO UPDATE SET
                    quantity=excluded.quantity,
                    avg_price=excluded.avg_price,
                    mode=excluded.mode
            """, (code, name, market, quantity, avg_price, buy_date, buy_reason, mode))
            self.conn.commit()

    def remove_position(self, code, market):
        with self._lock:
            self.conn.execute(
                "DELETE FROM portfolio WHERE code=? AND market=?", (code, market)
            )
            self.conn.commit()

    def add_portfolio_snapshot(self, total_value, cash, holdings_value):
        with self._lock:
            self.conn.execute("""
                INSERT INTO portfolio_history (timestamp, total_value, cash, holdings_value)
                VALUES (?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total_value, cash, holdings_value))
            self.conn.commit()

    def get_portfolio_history(self, limit=288):
        with self._lock:
            cur = self.conn.execute(
                "SELECT * FROM portfolio_history ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
            rows = [dict(r) for r in cur.fetchall()]
            return list(reversed(rows))

    def count_positions(self):
        with self._lock:
            cur = self.conn.execute("SELECT COUNT(*) as cnt FROM portfolio")
            return cur.fetchone()["cnt"]

    def today_trade_count(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with self._lock:
            cur = self.conn.execute(
                "SELECT COUNT(*) as cnt FROM trades WHERE timestamp LIKE ?", (f"{today}%",)
            )
            return cur.fetchone()["cnt"]
