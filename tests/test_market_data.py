"""Offline retrieval reliability, response layouts, and covering-cache tests."""
from concurrent.futures import ThreadPoolExecutor
from json import JSONDecodeError
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch, call

import pandas as pd
from yfinance.exceptions import YFRateLimitError, YFPricesMissingError, YFTzMissingError

from src.database import Database
from src.market_data import download_prices, get_historical_prices, MarketDataError, _close_series


def history():
    return pd.DataFrame({"Close": [100., 101., 102., 103.]}, index=pd.bdate_range("2025-01-02", periods=4))


class DownloadTests(unittest.TestCase):
    def setUp(self):
        cooldown = patch("src.market_data._rate_limited_until", 0.)
        cooldown.start()
        self.addCleanup(cooldown.stop)

    def test_network_retry_recovers(self):
        sleeper = Mock()
        with patch("yfinance.Ticker.history", side_effect=[TimeoutError(), ConnectionError(), history()]) as provider:
            result = download_prices("AAPL", "2025-01-01", "2026-01-01", sleeper=sleeper)
        self.assertEqual(len(result), 4)
        self.assertEqual(provider.call_count, 3)
        self.assertEqual(sleeper.call_args_list, [call(2), call(4)])

    def test_rate_limit_retries_then_cooldown(self):
        sleeper = Mock()
        with patch("yfinance.Ticker.history", side_effect=YFRateLimitError()) as provider:
            with self.assertRaises(MarketDataError) as first:
                download_prices("AAPL", "2025-01-01", "2026-01-01", sleeper=sleeper)
            with self.assertRaises(MarketDataError) as second:
                download_prices("SPY", "2025-01-01", "2026-01-01", sleeper=sleeper)
        self.assertEqual(provider.call_count, 3)
        self.assertEqual(first.exception.category, "rate_limit")
        self.assertEqual(second.exception.category, "rate_limit")
        self.assertIn("60", str(first.exception))

    def test_network_exhaustion_distinct(self):
        with patch("yfinance.Ticker.history", side_effect=TimeoutError()) as provider:
            with self.assertRaises(MarketDataError) as caught:
                download_prices("AAPL", "2025-01-01", "2026-01-01", sleeper=Mock())
        self.assertEqual(provider.call_count, 3)
        self.assertEqual(caught.exception.category, "network")

    def test_empty_frame_no_retries(self):
        with patch("yfinance.Ticker.history", return_value=pd.DataFrame()) as provider:
            with self.assertRaises(MarketDataError) as caught:
                download_prices("AAPL", "2025-01-01", "2026-01-01", sleeper=Mock())
        self.assertEqual(provider.call_count, 1)
        self.assertEqual(caught.exception.category, "empty_range")

    def test_missing_prices_not_automatically_invalid(self):
        with patch("yfinance.Ticker.history", side_effect=YFPricesMissingError("AAPL", "period")):
            with self.assertRaises(MarketDataError) as caught:
                download_prices("AAPL", "2025-01-01", "2026-01-01")
        self.assertEqual(caught.exception.category, "empty_range")

    def test_missing_timezone_is_ambiguous(self):
        with patch("yfinance.Ticker.history", side_effect=YFTzMissingError("AAPL")):
            with self.assertRaises(MarketDataError) as caught:
                download_prices("AAPL", "2025-01-01", "2026-01-01")
        self.assertEqual(caught.exception.category, "symbol_unavailable")

    def test_explicit_unknown_symbol_no_retry(self):
        error = YFPricesMissingError("UNKNOWN", "")
        error.yahoo_reason = "No data found, symbol may be delisted"
        with patch("yfinance.Ticker.history", side_effect=error) as provider:
            with self.assertRaises(MarketDataError) as caught:
                download_prices("UNKNOWN", "2025-01-01", "2026-01-01")
        self.assertEqual(caught.exception.category, "invalid_ticker")
        provider.assert_called_once()

    def test_malformed_provider_json_retries(self):
        with patch("yfinance.Ticker.history", side_effect=[JSONDecodeError("invalid", "", 0), history()]) as provider:
            result = download_prices("AAPL", "2025-01-01", "2026-01-01", sleeper=Mock())
        self.assertEqual(len(result), 4)
        self.assertEqual(provider.call_count, 2)

    def test_flat_close(self):
        pd.testing.assert_series_equal(_close_series(history(), "AAPL"), history()["Close"])

    def test_multiindex_both_orientations(self):
        for columns in [[("Close", "AAPL"), ("Close", "SPY")], [("AAPL", "Close"), ("SPY", "Close")]]:
            frame = pd.DataFrame([[100, 200], [101, 202]], columns=pd.MultiIndex.from_tuples(columns))
            self.assertEqual(_close_series(frame, "SPY").tolist(), [200, 202])

    def test_wrong_symbol_rejected(self):
        frame = history()
        frame.columns = pd.MultiIndex.from_tuples([("Close", "MSFT")])
        with self.assertRaises(MarketDataError):
            _close_series(frame, "AAPL")

    def test_adjusted_close_not_required(self):
        with patch("yfinance.Ticker.history", return_value=history()) as provider:
            result = download_prices("AAPL", "2021-01-01", "2026-10-07")
        self.assertEqual(len(result), 4)
        self.assertTrue(provider.call_args.kwargs["auto_adjust"])
        self.assertTrue(provider.call_args.kwargs["raise_errors"])
        self.assertEqual(provider.call_args.kwargs["end"], "2026-10-08")
        self.assertEqual(provider.call_args.kwargs["interval"], "1d")


class RetrievalCacheTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "data"
        root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temp.cleanup)
        self.db = Database(Path(self.temp.name) / "cache.sqlite3")

    def test_covering_cache_avoids_network(self):
        self.db.store_prices("AAPL", "2025-01-01", "2026-01-01", history()["Close"], 100)
        downloader = Mock(side_effect=AssertionError("must use cache"))
        result = get_historical_prices(["AAPL"], "2025-01-02", "2025-01-07", self.db, downloader, now=101)
        self.assertEqual(len(result), 4)
        downloader.assert_not_called()

    def test_partial_cache_not_used_as_full_range(self):
        self.db.store_prices("AAPL", "2025-01-02", "2025-01-07", history()["Close"], 100)
        downloader = Mock(return_value=history()["Close"])
        get_historical_prices(["AAPL"], "2025-01-01", "2026-01-01", self.db, downloader, now=101)
        downloader.assert_called_once()

    def test_expired_cache_refresh_failure_preserves_cache(self):
        self.db.store_prices("AAPL", "2025-01-01", "2026-01-01", history()["Close"], 100)
        with self.assertRaises(MarketDataError):
            get_historical_prices(["AAPL"], "2025-01-01", "2026-01-01", self.db,
                                  Mock(side_effect=MarketDataError("rate limited", "rate_limit")), now=90000)
        with self.db.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM historical_prices").fetchone()[0], 4)
            self.assertEqual(db.execute("SELECT updated_at FROM price_requests").fetchone()[0], 100)

    def test_duplicate_symbols_and_benchmark_reused(self):
        downloader = Mock(return_value=history()["Close"])
        result = get_historical_prices([" aapl ", "AAPL", "spy", "SPY"], "2025-01-01", "2026-01-01", self.db, downloader, now=100)
        self.assertEqual(result.columns.tolist(), ["AAPL", "SPY"])
        self.assertEqual(downloader.call_count, 2)

    def test_cached_data_bypasses_rate_limit_cooldown(self):
        self.db.store_prices("SPY", "2025-01-01", "2026-01-01", history()["Close"], 100)
        with patch("src.market_data._rate_limited_until", float("inf")), patch("yfinance.Ticker.history") as provider:
            result = get_historical_prices(["SPY"], "2025-01-01", "2026-01-01", self.db, now=101)
        self.assertEqual(len(result), 4)
        provider.assert_not_called()

    def test_invalid_ticker_format_no_request(self):
        downloader = Mock()
        with self.assertRaises(MarketDataError) as caught:
            get_historical_prices(["INVALID !"], "2025-01-01", "2026-01-01", self.db, downloader, now=100)
        self.assertEqual(caught.exception.category, "invalid_ticker")
        downloader.assert_not_called()

    def test_string_single_ticker(self):
        downloader = Mock(return_value=history()["Close"])
        result = get_historical_prices("AAPL", "2025-01-01", "2026-01-01", self.db, downloader, now=100)
        self.assertEqual(result.columns.tolist(), ["AAPL"])

    def test_concurrent_requests_share_download(self):
        downloader = Mock(return_value=history()["Close"])
        def retrieve(_):
            return get_historical_prices(["AAPL"], "2025-01-01", "2026-01-01", self.db, downloader, now=100)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(retrieve, range(2)))
        self.assertEqual(len(results), 2)
        downloader.assert_called_once()


if __name__ == "__main__":
    unittest.main()
