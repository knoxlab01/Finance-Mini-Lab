"""Adjusted Yahoo daily prices, bounded retries and SQLite reuse.

UI end date is inclusive; Yahoo end is exclusive. Single-symbol history with
raise_errors preserves errors which download() otherwise hides in empty frames.
Fresh covering requests are reusable; expired prices never silently substitute
for fresh prices. Failed downloads are not cached. After Yahoo fails, the
deterministic synthetic demo dataset is used. Kibot is never called.
"""
from datetime import timedelta
from json import JSONDecodeError
import re
import threading
import time
import warnings
from urllib.error import URLError

import numpy as np
import pandas as pd

from src.portfolio_analysis import align_prices

_retrieval_lock = threading.RLock()
_rate_limited_until = 0.0
RATE_LIMIT_COOLDOWN = 60


class MarketDataError(ValueError):
    """Public failure category, suitable for UI messages and tests."""
    def __init__(self, message, category="provider_error"):
        super().__init__(message)
        self.category = category


def _error(ticker, category):
    messages = {
        "rate_limit": "Yahoo Finance 限流，不能据此判断 ticker 无效；请至少等待 60 秒后重试，持续限流请稍后再试。 / Yahoo Finance rate limit; this does not mean an invalid ticker. Wait at least 60 seconds; persistent limits may take longer.",
        "network": "行情服务暂时无法连接或响应异常，请稍后重试。 / Temporary network/provider connection failure; retry later.",
        "invalid_ticker": "资产代码格式无效或 Yahoo 未识别该代码，请检查拼写及交易所后缀。 / Invalid ticker format or Yahoo did not recognize this symbol; check spelling and exchange suffix.",
        "symbol_unavailable": "Yahoo 未提供该资产的市场信息，代码可能无效、已退市或服务暂时异常，不能确定代码无效。 / Yahoo could not identify the market; symbol may be invalid, delisted or temporarily unavailable.",
        "empty_range": "所选日期区间没有可用价格，不代表 ticker 无效；请调整区间。 / No prices in the selected date range; this does not establish an invalid ticker. Change the date range.",
        "insufficient_data": "有效历史价格不足或异常，至少需要三个价格观测值。 / Insufficient or invalid history; at least three valid prices are required.",
        "provider_error": "行情服务返回了无法使用的响应，请稍后重试。 / Market provider returned an unusable response; retry later.",
    }
    return MarketDataError(f"{ticker}: {messages[category]}", category)


def _classify(error):
    from yfinance.exceptions import YFPricesMissingError, YFRateLimitError, YFTzMissingError
    from curl_cffi.requests.exceptions import RequestException
    if isinstance(error, MarketDataError):
        return error.category
    status = getattr(getattr(error, "response", None), "status_code", None)
    if isinstance(error, YFRateLimitError) or status == 429:
        return "rate_limit"
    if (isinstance(status, int) and status >= 500) or isinstance(error, (ConnectionError, TimeoutError, RequestException, JSONDecodeError, URLError)):
        return "network"
    if isinstance(error, YFTzMissingError):
        return "symbol_unavailable"
    if isinstance(error, YFPricesMissingError):
        # yfinance's speculative 'possibly delisted' is not proof of invalidity.
        reason = str(getattr(error, "yahoo_reason", "") or "").lower()
        if "symbol" in reason and ("not found" in reason or "delisted" in reason):
            return "invalid_ticker"
        return "empty_range"
    return "provider_error"


def _close_series(data, ticker):
    """Flat or either MultiIndex orientation; never take another symbol's close."""
    if data is None or data.empty:
        raise _error(ticker, "empty_range")
    if isinstance(data, pd.Series):
        return data.copy()
    if isinstance(data.columns, pd.MultiIndex):
        matches = [column for column in data.columns if "Close" in column and ticker in column]
        if len(matches) != 1:
            raise _error(ticker, "provider_error")
        return data[matches[0]].copy()
    if "Close" not in data.columns or not isinstance(data["Close"], pd.Series):
        raise _error(ticker, "provider_error")
    return data["Close"].copy()


def download_prices(ticker, start, end, *, max_attempts=3, sleeper=None):
    """Retry transient failures only, with 2s/4s backoff and a 60s cooldown.

    raise_errors is supported in installed 1.7.0 and minimum 0.2.66. Suppress
    its deprecation notice only; never mutate yfinance's global debug settings.
    """
    import yfinance as yf
    global _rate_limited_until
    sleeper = sleeper or time.sleep
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    with _retrieval_lock:
        if time.monotonic() < _rate_limited_until:
            raise _error(ticker, "rate_limit")
        exclusive_end = (pd.Timestamp(end).date() + timedelta(days=1)).isoformat()
        for attempt in range(max_attempts):
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message="'raise_errors' deprecated.*", category=DeprecationWarning)
                    data = yf.Ticker(ticker).history(start=start, end=exclusive_end, interval="1d",
                                                   auto_adjust=True, actions=False, timeout=15, raise_errors=True)
                result = _close_series(data, ticker)
                result.attrs.update(ticker=ticker, provider="yahoo", price_type="split_dividend_adjusted", retrieval="yahoo")
                return result
            except Exception as error:
                category = _classify(error)
                if category in {"network", "rate_limit"} and attempt < max_attempts - 1:
                    sleeper(2 ** (attempt + 1))
                    continue
                if category == "rate_limit":
                    _rate_limited_until = time.monotonic() + RATE_LIMIT_COOLDOWN
                raise _error(ticker, category) from error


DEMO_SYMBOLS = {"AAPL": (100., .00035, .012), "MSFT": (120., .0003, .010),
                "NVDA": (80., .00045, .020), "SPY": (100., .0002, .007)}


def demo_prices(ticker, start, end):
    """Version 1 synthetic business-day prices, 2000–2100 (not exchange holidays).

    Fixed seeded common and asset shocks model correlation and drawdowns. The
    epoch never depends on requested dates. These are not real asset histories,
    adjusted market prices, predictions or a calibrated market simulation.
    """
    if ticker not in DEMO_SYMBOLS:
        raise MarketDataError("演示数据仅支持 AAPL, MSFT, NVDA, SPY；请调整代码后重试。 / Demo data supports AAPL, MSFT, NVDA, SPY only; change symbols and retry.", "unsupported_symbol")
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if start < pd.Timestamp("2000-01-01") or end > pd.Timestamp("2100-12-31"):
        raise MarketDataError("演示日期须在 2000–2100 年内。 / Demo dates must be within 2000–2100.", "empty_range")
    index = pd.bdate_range("2000-01-01", end)
    base, drift, volatility = DEMO_SYMBOLS[ticker]
    common = np.random.default_rng(3100).standard_normal(len(index))
    seed = 4100 + list(DEMO_SYMBOLS).index(ticker)
    asset = np.random.default_rng(seed).standard_normal(len(index))
    log_returns = drift + volatility * (.7 * common + np.sqrt(1 - .7 ** 2) * asset)
    result = pd.Series(base * np.exp(np.cumsum(log_returns)), index=index, name=ticker).loc[start:end]
    result.attrs.update(ticker=ticker, provider="demo", retrieval="demo",
                        price_type="synthetic", dataset_version="synthetic-v1")
    return _validated_prices(result, ticker, start.date().isoformat(), end.date().isoformat(), "demo")


def _validated_prices(data, ticker, start, end, provider):
    cached = data.copy() if isinstance(data, pd.Series) else _close_series(data, ticker)
    cached.index = pd.DatetimeIndex(cached.index).tz_localize(None).normalize()
    cached = cached.sort_index().loc[start:end].dropna().astype(float)
    if cached.empty:
        raise _error(ticker, "empty_range")
    if len(cached) < 3 or cached.index.has_duplicates or cached.index.hasnans or not np.isfinite(cached.to_numpy()).all() or (cached <= 0).any():
        raise _error(ticker, "insufficient_data")
    cached.name = ticker
    cached.attrs.setdefault("provider", provider)
    cached.attrs.setdefault("price_type", "split_dividend_adjusted")
    cached.attrs.update(ticker=ticker, retrieval=cached.attrs["provider"])
    return cached


def _fetch_with_fallback(ticker, start, end, primary, fallback):
    try:
        return _validated_prices(primary(ticker, start, end), ticker, start, end, "yahoo")
    except Exception as error:
        primary_error = error if isinstance(error, MarketDataError) else _error(ticker, _classify(error))
        if fallback is None:
            raise primary_error from error
        # Formatting errors have already been rejected before reaching providers.
        # Known demo labels remain usable when Yahoo cannot identify a symbol.
        # Synthetic data does not establish whether a real ticker exists.
        if primary_error.category not in {"rate_limit", "network", "provider_error", "empty_range", "symbol_unavailable", "invalid_ticker"}:
            raise primary_error from error
    try:
        result = _validated_prices(fallback(ticker, start, end), ticker, start, end, "demo")
        result.attrs["fallback_reason"] = primary_error.category
        return result
    except Exception as error:
        fallback_category = _classify(error)
        raise MarketDataError(
            f"{ticker}: 实时行情不可用，演示数据也无法支持该输入。 / Live data unavailable and demo cannot support this input. "
            f"Yahoo={primary_error.category}; Demo={fallback_category}. {error}", fallback_category) from error



def get_historical_prices(tickers, start, end, database, downloader=None, now=None, *, fallback_downloader=None):
    # Cache check + download + store are serialized across sessions, preventing
    # identical concurrent requests from downloading the same prices twice.
    with _retrieval_lock:
        # Injected downloaders remain offline/isolated unless a fallback is also
        # explicitly injected. Public runtime uses Yahoo followed by synthetic demo data.
        fallback = fallback_downloader or (demo_prices if downloader is None else None)
        return _get_historical_prices(tickers, start, end, database, downloader, now, fallback)


def _get_historical_prices(tickers, start, end, database, downloader, now, fallback):
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if pd.isna(start) or pd.isna(end) or start >= end:
        raise MarketDataError("日期区间无效。 / Invalid date range.", "empty_range")
    start, end = start.date().isoformat(), end.date().isoformat()
    if isinstance(tickers, str):
        tickers = [tickers]
    symbols = list(dict.fromkeys(str(ticker).strip().upper() for ticker in tickers))
    for ticker in symbols:
        if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=-]{0,19}", ticker):
            raise _error(ticker, "invalid_ticker")
    downloader = downloader or download_prices
    now = time.time() if now is None else now
    series = []
    metadata = {}
    for ticker in symbols:
        cached = database.cached_prices(ticker, start, end, now)
        if cached is not None and cached.attrs.get("provider") not in {"yahoo"}:
            cached = None
        if cached is None:
            cached = _fetch_with_fallback(ticker, start, end, downloader, fallback)
            if cached.attrs.get("provider") == "yahoo":
                database.store_prices(ticker, start, end, cached, now)
        metadata[ticker] = dict(cached.attrs)
        clean = cached.rename(ticker).copy()
        clean.attrs = {}
        series.append(clean)
    if not series:
        raise MarketDataError("至少输入一个 ticker。 / Enter at least one ticker.", "invalid_ticker")
    if any(meta.get("provider") == "demo" for meta in metadata.values()):
        # Never compare synthetic portfolio returns against a real benchmark.
        reasons = {ticker: meta.get("fallback_reason") for ticker, meta in metadata.items()}
        series = [demo_prices(ticker, start, end) for ticker in symbols]
        metadata = {ticker: dict(prices.attrs, fallback_reason=reasons[ticker] or "consistent_demo_analysis")
                    for ticker, prices in zip(symbols, series)}
    result = align_prices(pd.concat(series, axis=1))
    result.attrs["source_metadata"] = metadata
    return result
