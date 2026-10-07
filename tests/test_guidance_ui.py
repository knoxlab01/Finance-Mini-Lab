"""Offline form, source notices and integrated guidance flow."""
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def source(demo=True):
    provider = "demo" if demo else "yahoo"
    return f"""import streamlit as st
import pandas as pd
from src.guidance_ui import render_portfolio_guidance
if 'historical' not in st.session_state:
    st.session_state.historical = {{'metrics': pd.DataFrame({{'Portfolio': {{'Annualized Volatility': .3, 'Maximum Drawdown': -.4, 'Sharpe Ratio': .5}}}}),
                                   'source_metadata': {{'AAPL': {{'provider': '{provider}'}}}}}}
render_portfolio_guidance(st.session_state.historical)
"""


class GuidanceUITests(unittest.TestCase):
    def test_demo_profile_and_basic_guidance(self):
        app = AppTest.from_string(source(), default_timeout=30).run()
        self.assertTrue(any("synthetic demo analysis" in c.value for c in app.caption))
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Run Future Outlook" in c.value for c in app.caption))
        self.assertTrue(any("Too Aggressive" in m.value or "Slightly Aggressive" in m.value for m in app.markdown))
        self.assertTrue(any("Illustrative Allocation" in m.value for m in app.markdown))

    def test_live_no_demo_label(self):
        app = AppTest.from_string(source(False), default_timeout=30).run()
        self.assertFalse(any("Demo-based guidance" in c.value for c in app.caption))

    def test_missing_historical(self):
        app = AppTest.from_string("from src.guidance_ui import render_portfolio_guidance\nrender_portfolio_guidance(None)").run()
        self.assertFalse(app.exception)
        self.assertTrue(app.info)

    def test_full_demo_flow_reuses_analysis_and_refreshes_future(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as folder:
            with patch.dict(os.environ, {"FINANCE_LAB_DB": str(Path(folder) / "test.sqlite3")}):
                app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
                with patch("src.market_data.download_prices", side_effect=TimeoutError()):
                    app.button(key="pa_analyze").click().run()
                with patch("src.portfolio_ui.get_historical_prices") as download, patch("src.future_ui.simulate_monte_carlo") as simulate:
                    app.button(key="pg_run").click().run()
                download.assert_not_called()
                simulate.assert_not_called()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.tabs), 4)
                with patch("src.portfolio_ui.get_historical_prices") as download:
                    app.button(key="fo_run").click().run()
                download.assert_not_called()
                self.assertFalse(app.exception)
                self.assertFalse(app.error)
                self.assertTrue(any("Simulated terminal loss" in m.value for m in app.markdown))
                self.assertTrue(any("Demo-based guidance" in c.value for c in app.caption))
