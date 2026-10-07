"""Lightweight SQLite persistence. Connections are short-lived and transactional."""
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

import pandas as pd

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "finance_lab.sqlite3"


class Database:
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get("FINANCE_LAB_DB", DEFAULT_PATH))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS historical_prices (
                    ticker TEXT NOT NULL, date TEXT NOT NULL,
                    adjusted_close REAL NOT NULL CHECK(adjusted_close > 0),
                    source TEXT NOT NULL DEFAULT 'Yahoo Finance / yfinance', updated_at TEXT NOT NULL,
                    PRIMARY KEY(ticker, date));
                CREATE TABLE IF NOT EXISTS price_requests (
                    ticker TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL,
                    updated_at REAL NOT NULL, PRIMARY KEY(ticker, start_date, end_date));
                CREATE TABLE IF NOT EXISTS portfolio_configs (
                    portfolio_name TEXT PRIMARY KEY, config_json TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT, config_json TEXT NOT NULL,
                    analysis_timestamp TEXT NOT NULL, benchmark TEXT NOT NULL,
                    start_date TEXT NOT NULL, end_date TEXT NOT NULL);
            """)
            # Additive migration preserves existing v0.3 development databases.
            for table, column in [("price_requests", "metadata_json"), ("analysis_runs", "source_metadata_json")]:
                columns = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
                if column not in columns:
                    db.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT NOT NULL DEFAULT '{{}}'")

    def connect(self):
        # sqlite3's context manager commits/rolls back but does not close.
        from contextlib import contextmanager

        @contextmanager
        def connection():
            db = sqlite3.connect(self.path, timeout=10)
            try:
                with db:
                    yield db
            finally:
                db.close()
        return connection()

    def cached_prices(self, ticker, start, end, now, ttl=86400):
        with self.connect() as db:
            # Successful wider requests cover subranges, including holidays.
            # Never infer coverage from first/last stored price observations.
            request = db.execute("""SELECT updated_at,metadata_json FROM price_requests
                WHERE ticker=? AND start_date<=? AND end_date>=?
                AND updated_at<=? AND updated_at>? ORDER BY updated_at DESC LIMIT 1""",
                                 (ticker, start, end, now, now - ttl)).fetchone()
            if request is None or not 0 <= now - request[0] < ttl:
                return None
            rows = db.execute("SELECT date, adjusted_close,source FROM historical_prices WHERE ticker=? AND date>=? AND date<=? ORDER BY date",
                              (ticker, start, end)).fetchall()
        if not rows:
            return None
        series = pd.Series([r[1] for r in rows], index=pd.to_datetime([r[0] for r in rows]), name=ticker)
        metadata = json.loads(request[1])
        legacy_source = "yahoo" if "yahoo" in rows[0][2].lower() else rows[0][2]
        metadata.setdefault("provider", legacy_source)
        metadata.setdefault("price_type", "split_dividend_adjusted")
        metadata.update(ticker=ticker, retrieval="cache", cached_at=request[0])
        series.attrs = metadata
        return series

    def store_prices(self, ticker, start, end, prices, now):
        timestamp = datetime.now(timezone.utc).isoformat()
        metadata = dict(prices.attrs)
        metadata.setdefault("provider", "yahoo")
        metadata.setdefault("price_type", "split_dividend_adjusted")
        metadata.update(ticker=ticker, cached_at=now)
        with self.connect() as db:
            # Adjusted histories can be revised by corporate actions. Invalidate
            # overlapping request markers and replace the entire requested range.
            db.execute("DELETE FROM price_requests WHERE ticker=? AND start_date<=? AND end_date>=?", (ticker, end, start))
            db.execute("DELETE FROM historical_prices WHERE ticker=? AND date>=? AND date<=?", (ticker, start, end))
            db.executemany("INSERT INTO historical_prices(ticker,date,adjusted_close,source,updated_at) VALUES(?,?,?,?,?)",
                           [(ticker, day.date().isoformat(), float(value), metadata["provider"], timestamp) for day, value in prices.items()])
            db.execute("INSERT OR REPLACE INTO price_requests(ticker,start_date,end_date,updated_at,metadata_json) VALUES(?,?,?,?,?)",
                       (ticker, start, end, now, json.dumps(metadata, allow_nan=False)))

    def save_portfolio(self, name, config):
        name = name.strip()
        if not name:
            raise ValueError("请输入组合名称。 / Enter a portfolio name.")
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute("""INSERT INTO portfolio_configs VALUES(?,?,?,?)
                ON CONFLICT(portfolio_name) DO UPDATE SET config_json=excluded.config_json, updated_at=excluded.updated_at""",
                       (name, json.dumps(config, allow_nan=False), now, now))

    def list_portfolios(self):
        with self.connect() as db:
            return [row[0] for row in db.execute("SELECT portfolio_name FROM portfolio_configs ORDER BY portfolio_name")]

    def load_portfolio(self, name):
        with self.connect() as db:
            row = db.execute("SELECT config_json FROM portfolio_configs WHERE portfolio_name=?", (name,)).fetchone()
        if row is None:
            raise ValueError("组合不存在。 / Portfolio not found.")
        return json.loads(row[0])

    def record_analysis(self, config, start, end, source_metadata=None):
        with self.connect() as db:
            cursor = db.execute("INSERT INTO analysis_runs(config_json,analysis_timestamp,benchmark,start_date,end_date,source_metadata_json) VALUES(?,?,?,?,?,?)",
                                (json.dumps(config, allow_nan=False), datetime.now(timezone.utc).isoformat(),
                                 config["benchmark"], str(start), str(end), json.dumps(source_metadata or {}, allow_nan=False)))
            return cursor.lastrowid
