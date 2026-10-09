"""Approved research inputs: read-only Yahoo cache, existing downloader, or declared CSV."""
from contextlib import closing
from pathlib import Path
import csv
import hashlib
import sqlite3
import numpy as np
import pandas as pd
from .spec import SPEC


def validate_prices(frame):
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is not None or frame.index.hasnans or frame.index.has_duplicates or not frame.index.is_monotonic_increasing or frame.columns.has_duplicates:
        raise ValueError("Require unique sorted timezone-naive Date index and unique ticker columns")
    values = frame.to_numpy(dtype=float)
    if len(frame) <= SPEC["history"]["lookback"] or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Insufficient/nonfinite/nonpositive prices; require at least 253 complete rows")
    if frame.index.to_series().diff().dt.days.max() > SPEC["history"]["max_gap_days"]:
        raise ValueError("Price gap exceeds seven days")
    return frame.astype(float)


def load_csv(path, *, kind, source, price_type):
    if kind not in ("real", "synthetic") or not source.strip() or price_type not in ("adjusted", "close"):
        raise ValueError("Declare real/synthetic, nonempty source and adjusted/close convention")
    p = Path(path)
    with p.open(encoding="utf-8-sig", newline="") as file:
        header = next(csv.reader(file), [])
    if not header or header[0] != "Date" or len(header) != len(set(header)) or any(not c.strip() or c != c.strip() for c in header):
        raise ValueError("First column must be Date; unique exact ticker headers required")
    frame = pd.read_csv(p, encoding="utf-8-sig", index_col="Date")
    frame.index = pd.to_datetime(frame.index, errors="raise")
    frame = validate_prices(frame)
    metadata = dict(kind=kind, source=source, price_type=price_type,
                    csv_sha256=hashlib.sha256(p.read_bytes()).hexdigest(), provenance="User-declared; not independently authenticated")
    return frame, metadata


def approved_real_prices(database, symbols, start="2016-01-01", end="2026-10-08", try_live=False):
    attempts = []
    path = Path(database)
    if path.exists():
        with closing(sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True)) as db:
            rows = db.execute("SELECT ticker,date,adjusted_close FROM historical_prices WHERE lower(source) IN ('yahoo','yahoo finance / yfinance') AND date>=? AND date<=?", (start,end)).fetchall()
        if rows:
            frame = pd.DataFrame(rows,columns=["ticker","date","price"]).pivot(index="date",columns="ticker",values="price")
            frame.index = pd.to_datetime(frame.index)
            if set(symbols).issubset(frame):
                try:
                    frame = validate_prices(frame[symbols].sort_index())
                    return frame, dict(kind="real",source="existing Yahoo SQLite cache",price_type="adjusted",retrospective_stale_cache=True), attempts
                except ValueError as error:
                    attempts.append("Cache rejected: "+str(error))
        attempts.append("No adequate complete Yahoo cache for requested symbols")
    else:
        attempts.append("No local cache file")
    if try_live:
        from src.market_data import download_prices
        items=[]
        try:
            for symbol in symbols:
                series=download_prices(symbol,start,end,max_attempts=1)
                series.attrs={}
                items.append(series.rename(symbol))
            frame=validate_prices(pd.concat(items,axis=1))
            return frame,dict(kind="real",source="existing Yahoo downloader",price_type="adjusted"),attempts
        except Exception as error:
            attempts.append(f"Yahoo unavailable: {type(error).__name__}; category={getattr(error,'category','data_or_provider_error')}")
    else:
        attempts.append("Live request disabled")
    return None,dict(kind="unavailable",source="no verified real history"),attempts
