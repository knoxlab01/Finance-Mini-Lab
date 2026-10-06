import unittest
from pathlib import Path
from unittest.mock import patch
import streamlit as st
from streamlit.testing.v1 import AppTest


class SensitivityUITests(unittest.TestCase):
    def calculate(self, **inputs):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "streamlit_app.py"), default_timeout=15).run()
        for key, value in inputs.items():
            app.number_input(key=key).set_value(value)
        app.button[2].click().run()
        self.assertFalse(app.exception)
        return app

    def test_sections_tables_and_charts(self):
        with patch("streamlit.vega_lite_chart", wraps=st.vega_lite_chart) as charts:
            app = self.calculate()
        self.assertFalse(app.error)
        headings = [s.value for s in app.subheader]
        self.assertIn("Time Sensitivity / 时间敏感性", headings)
        self.assertIn("Return Sensitivity / 收益率敏感性", headings)
        self.assertEqual(len(app.dataframe), 3)
        time, returns = app.dataframe[1].value, app.dataframe[2].value
        self.assertEqual(time.iloc[1]["Required Monthly Contribution / 每月所需投入"], "¥4,252.82")
        self.assertEqual(returns["Annual Return / 年化收益率"].tolist(), ["5.00%", "8.00%", "11.00%"])
        self.assertEqual(charts.call_count, 2)
        for call in charts.call_args_list:
            spec = call.kwargs["spec"]
            self.assertEqual(len(spec["data"]["values"]), 3)
            self.assertEqual(spec["encoding"]["y"]["title"], "Required Monthly Contribution (¥)")

    def test_short_low_rate_and_zero(self):
        for inputs in [{"goal_years": 1}, {"goal_rate": -99.0}, {"goal_target": 100.0}]:
            app = self.calculate(**inputs)
            self.assertFalse(app.error)
            self.assertEqual(len(app.dataframe), 3)

    def test_overflow_preserves_base(self):
        app = self.calculate(goal_target=1e301, goal_principal=1e300, goal_rate=0.0, goal_years=1000)
        self.assertFalse(app.error)
        self.assertTrue(app.warning)
        self.assertEqual(app.dataframe[2].value.iloc[2]["Required Monthly Contribution / 每月所需投入"], "N/A")
        self.assertIn("Required Monthly Contribution / 每月所需投入", [m.label for m in app.metric])
