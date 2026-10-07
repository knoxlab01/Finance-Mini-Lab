"""Deterministic analytics and SQLite tests: no network required."""
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from src.portfolio_metrics import (cumulative_return, cagr, annualized_volatility,
                                   sharpe_ratio, maximum_drawdown, drawdown_series, calculate_metrics)
from src.portfolio_analysis import (parse_config, validate_weights, align_prices,
                                    prices_to_returns, portfolio_returns, normalized_growth, correlation_matrix)
from src.benchmark import analyze_portfolio
from src.database import Database
from src.market_data import get_historical_prices, download_prices, MarketDataError


def sample_prices():
    return pd.DataFrame({"AAPL": [100, 110, 99, 108.9], "MSFT": [100, 100, 110, 121],
                         "SPY": [100, 102, 101, 103]}, index=pd.bdate_range("2024-01-02", periods=4))


class MetricsTests(unittest.TestCase):
    def test_cumulative_return(self):
        self.assertAlmostEqual(cumulative_return([0.1, -0.1]), -0.01)

    def test_calendar_cagr(self):
        self.assertAlmostEqual(cagr([0.1], "2023-01-01", "2024-01-01"), 1.1 ** (365.25 / 365) - 1)

    def test_volatility(self):
        self.assertAlmostEqual(annualized_volatility([0.1, -0.1]), np.std([0.1, -0.1], ddof=1) * np.sqrt(252))

    def test_sharpe_effective_risk_free(self):
        values = [0.01, -0.005, 0.003]
        expected = (np.mean(values) - (1.04 ** (1 / 252) - 1)) / np.std(values, ddof=1) * np.sqrt(252)
        self.assertAlmostEqual(sharpe_ratio(values, 0.04), expected)
        self.assertGreater(sharpe_ratio(values, 0), sharpe_ratio(values, 0.04))

    def test_drawdown_includes_first_loss(self):
        self.assertAlmostEqual(maximum_drawdown([-0.2, 0.1, -0.5]), -0.56)
        self.assertAlmostEqual(maximum_drawdown([0.1, 0.1]), 0)

    def test_drawdown_running_peak(self):
        np.testing.assert_allclose(drawdown_series([100, 80, 120, 90]), [0, -0.2, 0, -0.25])

    def test_zero_volatility(self):
        self.assertEqual(annualized_volatility([0, 0]), 0)
        self.assertIsNone(sharpe_ratio([0.01, 0.01]))

    def test_short_history(self):
        self.assertIsNone(annualized_volatility([0.1]))
        self.assertIsNone(sharpe_ratio([0.1]))
        self.assertAlmostEqual(cumulative_return([0.1]), 0.1)

    def test_invalid_returns(self):
        for values in [[], [np.nan], [np.inf], [-1], [-1.1]]:
            for function in [cumulative_return, annualized_volatility, sharpe_ratio, maximum_drawdown]:
                with self.subTest(values=values, function=function), self.assertRaises(ValueError):
                    function(values)

    def test_invalid_dates(self):
        for start, end in [("2024-01-01", "2024-01-01"), ("2025-01-01", "2024-01-01"), (pd.NaT, "2024-01-01")]:
            with self.assertRaises(ValueError):
                cagr([0.1], start, end)

    def test_invalid_risk_free(self):
        for rate in [float("nan"), float("inf"), -1]:
            with self.assertRaises(ValueError):
                sharpe_ratio([0.1, 0.2], rate)

    def test_growth_overflow(self):
        with self.assertRaises(ValueError):
            cagr([100], "2024-01-01", "2024-01-02")


class PortfolioTests(unittest.TestCase):
    def test_config_percent_and_tickers(self):
        config = parse_config(" aapl, msft ", "40%, 60", "2024-01-01", "2024-02-01")
        self.assertEqual(config["tickers"], ["AAPL", "MSFT"])
        self.assertEqual(config["weights"], [0.4, 0.6])

    def test_invalid_configs(self):
        for tickers, weights in [("", "100"), ("AAPL,", "50,50"), ("AAPL,AAPL", "50,50"),
                                  ("AAPL", "word"), ("AAPL,MSFT", "100"), ("AAPL", "99"),
                                  ("AAPL,MSFT", "-1,101"), ("AAPL", "nan"), ("AAPL", "inf")]:
            with self.subTest(tickers=tickers, weights=weights), self.assertRaises(ValueError):
                parse_config(tickers, weights, "2024-01-01", "2024-02-01")

    def test_weight_rounding_tolerance(self):
        self.assertAlmostEqual(sum(validate_weights(["A", "B", "C"], [0.3333] * 3)), 1)

    def test_config_invalid_period_and_rate(self):
        for start, end, rf in [("2024-02-01", "2024-01-01", 0.04), ("2024-01-01", "2024-02-01", -1)]:
            with self.assertRaises(ValueError):
                parse_config("AAPL", "100", start, end, risk_free_rate=rf)

    def test_weighted_returns(self):
        result = portfolio_returns(prices_to_returns(sample_prices())[["AAPL", "MSFT"]], [0.4, 0.6])
        np.testing.assert_allclose(result, [0.04, 0.02, 0.1])

    def test_missing_prices_not_filled(self):
        prices = sample_prices()
        prices.loc[prices.index[1], "AAPL"] = np.nan
        aligned = align_prices(prices)
        self.assertEqual(len(aligned), 3)
        self.assertAlmostEqual(prices_to_returns(prices).iloc[0]["AAPL"], -0.01)

    def test_bad_price_history(self):
        examples = [sample_prices().iloc[:2], sample_prices().assign(AAPL=0), sample_prices().assign(AAPL=np.inf)]
        duplicate = sample_prices()
        duplicate.index = [duplicate.index[0]] * 4
        examples.append(duplicate)
        for prices in examples:
            with self.assertRaises(ValueError):
                align_prices(prices)

    def test_long_data_gap(self):
        prices = sample_prices()
        prices.index = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-02-01", "2024-02-02"])
        with self.assertRaises(ValueError):
            align_prices(prices)

    def test_benchmark_growth_and_metrics(self):
        result = analyze_portfolio(sample_prices(), ["AAPL", "MSFT"], [0.4, 0.6])
        np.testing.assert_allclose(result["growth"].iloc[0], [100, 100])
        self.assertAlmostEqual(result["growth"].iloc[-1]["Portfolio"], 100 * 1.04 * 1.02 * 1.1)
        self.assertAlmostEqual(result["growth"].iloc[-1]["Benchmark"], 103)
        self.assertEqual(result["metrics"].shape, (5, 2))
        self.assertEqual(result["observations"], 3)
        self.assertEqual(result["drawdown"].iloc[0].tolist(), [0, 0])

    def test_benchmark_can_be_portfolio_asset(self):
        result = analyze_portfolio(sample_prices(), ["SPY"], [1])
        np.testing.assert_allclose(result["growth"]["Portfolio"], result["growth"]["Benchmark"])

    def test_correlation(self):
        returns = pd.DataFrame({"A": [0.1, 0.2, -0.1], "B": [0.2, 0.4, -0.2], "C": [0, 0, 0]})
        result = correlation_matrix(returns)
        self.assertAlmostEqual(result.loc["A", "B"], 1)
        self.assertTrue(pd.isna(result.loc["C", "C"]))
        self.assertEqual(correlation_matrix(returns[["A"]]).iloc[0, 0], 1)

    def test_normalization_invalid_base(self):
        with self.assertRaises(ValueError):
            normalized_growth(prices_to_returns(sample_prices())["SPY"], "2024-01-02", base=0)


class DatabaseAndMarketTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "data"
        root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temp.cleanup)
        self.db = Database(Path(self.temp.name) / "test.sqlite3")
        self.config = parse_config("AAPL", "100", "2024-01-02", "2024-01-05")

    def test_schema(self):
        with self.db.connect() as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"historical_prices", "portfolio_configs", "analysis_runs", "price_requests"} <= tables)

    def test_save_load_update(self):
        self.db.save_portfolio("Test ' portfolio", self.config)
        loaded = self.db.load_portfolio("Test ' portfolio")
        self.assertEqual(loaded, self.config)
        loaded["risk_free_rate"] = 0.02
        self.db.save_portfolio("Test ' portfolio", loaded)
        self.assertEqual(self.db.list_portfolios(), ["Test ' portfolio"])
        self.assertEqual(self.db.load_portfolio("Test ' portfolio")["risk_free_rate"], 0.02)
        with self.assertRaises(ValueError):
            self.db.save_portfolio(" ", self.config)
        with self.assertRaises(ValueError):
            self.db.load_portfolio("missing")

    def test_analysis_record(self):
        identifier = self.db.record_analysis(self.config, "2024-01-02", "2024-01-05")
        with self.db.connect() as db:
            row = db.execute("SELECT benchmark,start_date FROM analysis_runs WHERE run_id=?", (identifier,)).fetchone()
        self.assertEqual(row, ("SPY", "2024-01-02"))

    def test_cache_hit_and_expiry(self):
        downloader = Mock(return_value=sample_prices()["AAPL"])
        first = get_historical_prices(["AAPL"], "2024-01-02", "2024-01-05", self.db, downloader, now=100)
        second = get_historical_prices(["AAPL"], "2024-01-02", "2024-01-05", self.db, downloader, now=200)
        pd.testing.assert_frame_equal(first, second, check_freq=False)
        self.assertEqual(downloader.call_count, 1)
        get_historical_prices(["AAPL"], "2024-01-02", "2024-01-05", self.db, downloader, now=90000)
        self.assertEqual(downloader.call_count, 2)

    def test_cache_replaces_revised_prices(self):
        series = sample_prices()["AAPL"]
        self.db.store_prices("AAPL", "2024-01-02", "2024-01-05", series, 100)
        self.db.store_prices("AAPL", "2024-01-02", "2024-01-05", series * 2, 200)
        cached = self.db.cached_prices("AAPL", "2024-01-02", "2024-01-05", 201)
        self.assertEqual(cached.iloc[0], 200)
        with self.db.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM historical_prices").fetchone()[0], 4)

    def test_overlapping_cache_invalidated(self):
        series = sample_prices()["AAPL"]
        self.db.store_prices("AAPL", "2024-01-02", "2024-01-05", series, 100)
        self.db.store_prices("AAPL", "2024-01-03", "2024-01-05", series.iloc[1:] * 2, 200)
        self.assertIsNone(self.db.cached_prices("AAPL", "2024-01-02", "2024-01-05", 201))

    def test_failed_download_not_cached(self):
        downloader = Mock(side_effect=RuntimeError("offline"))
        for _ in range(2):
            with self.assertRaises(MarketDataError):
                get_historical_prices(["BAD"], "2024-01-02", "2024-01-05", self.db, downloader, now=100)
        self.assertEqual(downloader.call_count, 2)
        self.assertIsNone(self.db.cached_prices("BAD", "2024-01-02", "2024-01-05", 101))

    def test_empty_and_invalid_downloads(self):
        for series in [pd.Series(dtype=float), sample_prices()["AAPL"] * -1, sample_prices()["AAPL"].iloc[:2]]:
            with self.assertRaises(MarketDataError):
                get_historical_prices(["BAD"], "2024-01-02", "2024-01-05", self.db, Mock(return_value=series), now=100)

    def test_provider_adjustment_and_inclusive_end(self):
        with patch("yfinance.Ticker.history", return_value=sample_prices().rename(columns={"AAPL": "Close"})) as provider:
            series = download_prices("AAPL", "2024-01-02", "2024-01-05")
        self.assertEqual(len(series), 4)
        self.assertTrue(provider.call_args.kwargs["auto_adjust"])
        self.assertEqual(provider.call_args.kwargs["end"], "2024-01-06")

    def test_database_rollback(self):
        with self.assertRaises(RuntimeError):
            with self.db.connect() as db:
                db.execute("INSERT INTO portfolio_configs VALUES('rollback','{}','now','now')")
                raise RuntimeError("rollback")
        self.assertEqual(self.db.list_portfolios(), [])


if __name__ == "__main__":
    unittest.main()
