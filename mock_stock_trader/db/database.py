"""SQLite 기반 영구 저장소"""
import sqlite3
import threading
from pathlib import Path


class Database:
    def __init__(self, path: str = "mock_stock_trader.db"):
        self.path = path
        self._lock = threading.Lock()
        self.conn  = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        with self._lock:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                );

                CREATE TABLE IF NOT EXISTS portfolio (
                    code       TEXT,
                    market     TEXT,
                    name       TEXT,
                    quantity   REAL,
                    avg_price  REAL,
                    mode       TEXT DEFAULT 'swing',
                    PRIMARY KEY (code, market)
                );

                CREATE TABLE IF NOT EXISTS trades (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    code        TEXT,
                    market      TEXT,
                    name        TEXT,
                    trade_type  TEXT,
                    price       REAL,
                    quantity    REAL,
                    amount      REAL,
                    fee         REAL,
                    profit      REAL DEFAULT 0,
                    reason      TEXT,
                    timestamp   TEXT
                );

                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    value     REAL
                );
            """)
            self.conn.commit()

    # ── 설정 ─────────────────────────────────────────────────

    def get_setting(self, key: str, default=None):
        with self._lock:
            row = self.conn.execute(
                "SELECT value FROM settings WHERE key=?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value):
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)",
                (key, str(value))
            )
            self.conn.commit()

    # ── 포트폴리오 ────────────────────────────────────────────

    def get_positions(self) -> list[dict]:
        with self._lock:
            rows = self.conn.execute("SELECT * FROM portfolio").fetchall()
            return [dict(r) for r in rows]

    def upsert_position(self, code, market, name, quantity, avg_price, mode="swing"):
        with self._lock:
            self.conn.execute(
                """INSERT OR REPLACE INTO portfolio
                   (code, market, name, quantity, avg_price, mode)
                   VALUES (?,?,?,?,?,?)""",
                (code, market, name, quantity, avg_price, mode)
            )
            self.conn.commit()

    def delete_position(self, code, market):
        with self._lock:
            self.conn.execute(
                "DELETE FROM portfolio WHERE code=? AND market=?", (code, market)
            )
            self.conn.commit()

    # ── 거래 기록 ─────────────────────────────────────────────

    def save_trade(self, code, market, name, trade_type, price,
                   quantity, amount, fee, profit, reason, timestamp):
        with self._lock:
            self.conn.execute(
                """INSERT INTO trades
                   (code,market,name,trade_type,price,quantity,amount,fee,profit,reason,timestamp)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (code, market, name, trade_type, price,
                 quantity, amount, fee, profit, reason, timestamp)
            )
            self.conn.commit()

    def get_trades(self, limit: int = 200) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ── 포트폴리오 히스토리 ───────────────────────────────────

    def save_history(self, timestamp: str, value: float):
        with self._lock:
            self.conn.execute(
                "INSERT INTO portfolio_history(timestamp, value) VALUES(?,?)",
                (timestamp, value)
            )
            self.conn.commit()

    def get_history(self, limit: int = 500) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM portfolio_history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in reversed(rows)]

    def close(self):
        self.conn.close()
