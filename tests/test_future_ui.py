"""Offline Future Outlook form and provenance smoke tests."""
from unittest.mock import patch
import unittest
from streamlit.testing.v1 import AppTest


def app_source():
    return """import streamlit as st
import pandas as pd
import numpy as np
from src.future_ui import render_future_outlook
if 'historical' not in st.session_state:
    st.session_state.historical = {'portfolio_returns': pd.Series(np.tile([.01, -.008], 126)),
                                   'source_metadata': {'AAPL': {'provider': 'demo'}}}
render_future_outlook(st.session_state.historical)
"""


class FutureUITests(unittest.TestCase):
    def test_demo_render_and_no_recompute_on_rerun(self):
        app = AppTest.from_string(app_source(), default_timeout=30).run()
        self.assertTrue(any("Demo-based" in c.value for c in app.caption))
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 5)
        self.assertEqual(len(app.dataframe), 1)
        self.assertEqual(len(app.get("vega_lite_chart")), 3)
        with patch("src.future_ui.simulate_monte_carlo") as simulate:
            app.run()
        simulate.assert_not_called()
        self.assertEqual(len(app.metric), 5)

    def test_live_source_status(self):
        app = AppTest.from_string(app_source().replace("'provider': 'demo'", "'provider': 'yahoo'"), default_timeout=30).run()
        self.assertTrue(any("historical portfolio return" in c.value for c in app.caption))
        self.assertFalse(any("Demo-based" in c.value for c in app.caption))

    def test_short_history_warning(self):
        app = AppTest.from_string(app_source().replace("126", "2"), default_timeout=30).run()
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("60" in w.value for w in app.warning))
        self.assertEqual(len(app.metric), 0)

    def test_one_year_does_not_project_further(self):
        app = AppTest.from_string(app_source(), default_timeout=30).run()
        app.selectbox(key="fo_horizon").select(1)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.dataframe[0].value.index.tolist(), [1])


    def test_full_portfolio_demo_workflow(self):
        import os
        import tempfile
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root / "data") as folder:
            with patch.dict(os.environ, {"FINANCE_LAB_DB": str(Path(folder) / "test.sqlite3")}):
                app = AppTest.from_file(str(root / "streamlit_app.py"), default_timeout=30).run()
                with patch("src.market_data.download_prices", side_effect=TimeoutError()):
                    app.button(key="pa_analyze").click().run()
                with patch("src.portfolio_ui.get_historical_prices") as download:
                    app.button(key="fo_run").click().run()
                download.assert_not_called()
                self.assertFalse(app.exception)
                self.assertFalse(app.error)
                self.assertEqual(len(app.metric), 10)
                self.assertTrue(any("Demo-based simulation" in c.value for c in app.caption))
                self.assertEqual(len(app.tabs), 4)
