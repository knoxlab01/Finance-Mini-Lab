"""Offline public demo fallback and provenance checks."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import pandas as pd
from src.database import Database
from src.market_data import demo_prices, get_historical_prices, MarketDataError


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / "data")
        self.addCleanup(self.temp.cleanup)
        self.db = Database(Path(self.temp.name) / "test.sqlite3")

    def fetch(self, symbols=None):
        return get_historical_prices(symbols or ["AAPL", "SPY"], "2025-01-01", "2026-01-01", self.db, now=100)

    def test_deterministic_and_subrange_stable(self):
        a = demo_prices("AAPL", "2025-01-01", "2026-01-01")
        pd.testing.assert_series_equal(a, demo_prices("AAPL", "2025-01-01", "2026-01-01"))
        pd.testing.assert_series_equal(a.loc["2025-06-01":"2025-12-01"], demo_prices("AAPL", "2025-06-01", "2025-12-01"))
        self.assertTrue((a > 0).all())
        self.assertGreater(a.pct_change().std(), 0)

    def test_yahoo_success(self):
        fixture = demo_prices("AAPL", "2025-01-01", "2026-01-01")
        fixture.attrs = {"provider": "yahoo", "retrieval": "yahoo", "price_type": "split_dividend_adjusted"}
        with patch("src.market_data.download_prices", return_value=fixture), patch("src.market_data.demo_prices") as demo:
            result = self.fetch()
        demo.assert_not_called()
        self.assertEqual(result.attrs["source_metadata"]["AAPL"]["provider"], "yahoo")
        with patch("src.market_data.download_prices") as yahoo:
            cached = self.fetch()
        yahoo.assert_not_called()
        self.assertEqual(cached.attrs["source_metadata"]["SPY"]["retrieval"], "cache")

    def test_yahoo_failure_demo_not_cached(self):
        for category in ["rate_limit", "network", "empty_range", "provider_error", "invalid_ticker"]:
            with self.subTest(category=category), patch("src.market_data.download_prices", side_effect=MarketDataError("failure", category)):
                result = self.fetch()
            for meta in result.attrs["source_metadata"].values():
                self.assertEqual(meta["provider"], "demo")
                self.assertEqual(meta["price_type"], "synthetic")
                self.assertEqual(meta["fallback_reason"], category)
        with self.db.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM historical_prices").fetchone()[0], 0)

    def test_no_mixing_real_and_demo(self):
        fixture = demo_prices("AAPL", "2025-01-01", "2026-01-01")
        fixture.attrs = {"provider": "yahoo"}
        with patch("src.market_data.download_prices", side_effect=[fixture, TimeoutError()]):
            result = self.fetch()
        self.assertTrue(all(meta["provider"] == "demo" for meta in result.attrs["source_metadata"].values()))
        pd.testing.assert_series_equal(result["AAPL"], demo_prices("AAPL", "2025-01-01", "2026-01-01"), check_freq=False, check_names=False)

    def test_kibot_cache_excluded_even_with_old_env(self):
        fixture = demo_prices("AAPL", "2025-01-01", "2026-01-01")
        fixture.attrs = {"provider": "kibot"}
        self.db.store_prices("AAPL", "2025-01-01", "2026-01-01", fixture, 100)
        with patch.dict("os.environ", {"FINANCE_LAB_FALLBACK": "kibot"}), patch("src.market_data.download_prices", side_effect=TimeoutError()) as yahoo:
            result = self.fetch(["AAPL"])
        yahoo.assert_called_once()
        self.assertEqual(result.attrs["source_metadata"]["AAPL"]["provider"], "demo")

    def test_invalid_format_no_network(self):
        with patch("src.market_data.download_prices") as yahoo:
            with self.assertRaises(MarketDataError):
                self.fetch(["BAD!"])
        yahoo.assert_not_called()

    def test_unknown_demo_symbol_not_invented(self):
        with patch("src.market_data.download_prices", side_effect=TimeoutError()):
            with self.assertRaises(MarketDataError):
                self.fetch(["UNKNOWN"])

    def test_demo_date_limits(self):
        with self.assertRaises(MarketDataError):
            demo_prices("AAPL", "1999-01-01", "2025-01-01")
        with self.assertRaises(MarketDataError):
            demo_prices("AAPL", "2025-01-04", "2025-01-05")

    def test_analysis_metadata(self):
        with patch("src.market_data.download_prices", side_effect=TimeoutError()):
            result = self.fetch()
        self.db.record_analysis({"benchmark": "SPY"}, "2025-01-01", "2026-01-01", result.attrs["source_metadata"])
        with self.db.connect() as db:
            self.assertIn('"provider": "demo"', db.execute("SELECT source_metadata_json FROM analysis_runs").fetchone()[0])
