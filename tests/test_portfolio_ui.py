"""Offline Streamlit interactions with isolated SQLite and mocked prices."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.database import Database

ROOT = Path(__file__).resolve().parents[1]


class PortfolioUITests(unittest.TestCase):
    def setUp(self):
        (ROOT / "data").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / "ui.sqlite3")
        env = patch.dict(os.environ, {"FINANCE_LAB_DB": self.path})
        env.start()
        self.addCleanup(env.stop)

    def app(self):
        return AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()

    def prices(self):
        return pd.DataFrame({"AAPL": [100, 90, 99, 108], "MSFT": [100, 101, 102, 103],
                             "NVDA": [100, 110, 100, 120], "SPY": [100, 101, 100, 102]},
                            index=pd.bdate_range("2024-01-02", periods=4))

    def test_successful_analysis_and_metadata(self):
        app = self.app()
        with patch("src.portfolio_ui.get_historical_prices", return_value=self.prices()):
            app.button(key="FormSubmitter:portfolio_setup-Analyze Portfolio").click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertEqual([metric.label for metric in app.metric],
                         ["Total Return", "CAGR", "Volatility", "Sharpe Ratio", "Max Drawdown"])
        self.assertEqual(len(app.dataframe), 2)
        self.assertEqual(app.dataframe[0].value.shape, (5, 2))
        with Database(self.path).connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM analysis_runs").fetchone()[0], 1)

    def test_invalid_weights_no_download(self):
        app = self.app()
        app.text_input(key="pa_weights").set_value("30,30,30")
        with patch("src.portfolio_ui.get_historical_prices") as download:
            app.button(key="FormSubmitter:portfolio_setup-Analyze Portfolio").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)
        download.assert_not_called()

    def test_network_failure_is_friendly(self):
        app = self.app()
        with patch("src.portfolio_ui.get_historical_prices", side_effect=ValueError("行情获取失败 / Data unavailable")):
            app.button(key="FormSubmitter:portfolio_setup-Analyze Portfolio").click().run()
        self.assertFalse(app.exception)
        self.assertIn("Data unavailable", app.error[0].value)
        self.assertEqual(len(app.metric), 0)

    def test_save_and_load(self):
        app = self.app()
        app.text_input(key="pa_name").set_value("My Portfolio")
        app.text_input(key="pa_weights").set_value("50,25,25")
        app.button(key="FormSubmitter:portfolio_setup-Save Portfolio / 保存组合").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(Database(self.path).list_portfolios(), ["My Portfolio"])
        app.text_input(key="pa_weights").set_value("40,30,30")
        app.selectbox(key="pa_saved").select("My Portfolio")
        app.button(key="pa_load").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_input(key="pa_weights").value, "50, 25, 25")

    def test_save_requires_name(self):
        app = self.app()
        app.button(key="FormSubmitter:portfolio_setup-Save Portfolio / 保存组合").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)

    def test_actual_sources_displayed_and_recorded(self):
        app = self.app()
        fixture = self.prices()
        fixture.attrs["source_metadata"] = {"AAPL": {"provider": "demo", "retrieval": "demo", "price_type": "synthetic"}}
        with patch("src.portfolio_ui.get_historical_prices", return_value=fixture):
            app.button(key="FormSubmitter:portfolio_setup-Analyze Portfolio").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("AAPL: Demo Data" in item.value for item in app.caption))
        self.assertTrue(any("Demo Data" in item.value for item in app.warning))
        self.assertTrue(any("temporarily unavailable" in item.value for item in app.info))
        self.assertFalse(app.error)
        self.assertEqual(len(app.metric), 5)
        with Database(self.path).connect() as db:
            self.assertIn('"provider": "demo"', db.execute("SELECT source_metadata_json FROM analysis_runs").fetchone()[0])


if __name__ == "__main__":
    unittest.main()


class SourceStatusTests(unittest.TestCase):
    setUp = PortfolioUITests.setUp
    app = PortfolioUITests.app
    prices = PortfolioUITests.prices
    def test_yahoo_and_cache_status(self):
        for retrieval, label in [("yahoo", "Yahoo Finance"), ("cache", "SQLite Cache")]:
            app = self.app()
            fixture = self.prices()
            fixture.attrs["source_metadata"] = {"AAPL": {"provider": "yahoo", "retrieval": retrieval}}
            with patch("src.portfolio_ui.get_historical_prices", return_value=fixture):
                app.button(key="FormSubmitter:portfolio_setup-Analyze Portfolio").click().run()
            self.assertTrue(any(label in item.value for item in app.caption))
            self.assertFalse(app.info)

    def test_real_layer_failure_completes_demo_page(self):
        app = self.app()
        with patch("src.market_data.download_prices", side_effect=TimeoutError()):
            app.button(key="FormSubmitter:portfolio_setup-Analyze Portfolio").click().run()
        self.assertFalse(app.error)
        self.assertFalse(app.exception)
        self.assertEqual([metric.label for metric in app.metric],
                         ["Total Return", "CAGR", "Volatility", "Sharpe Ratio", "Max Drawdown"])
        self.assertEqual(len(app.dataframe), 2)
        self.assertTrue(any("Demo Data" in item.value for item in app.warning))
