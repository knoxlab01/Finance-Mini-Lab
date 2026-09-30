"""使用 Streamlit AppTest 验证页面计算、校验和图表数据。"""

import unittest
from pathlib import Path
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest


class StreamlitAppTests(unittest.TestCase):
    def calculate(self, principal=10000.0, rate=8.0, years=10):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "streamlit_app.py"), default_timeout=15).run()
        app.number_input[0].set_value(principal)
        app.number_input[1].set_value(rate)
        app.number_input[2].set_value(years)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        return app

    def test_default_result_and_growth_data(self):
        with patch("streamlit.line_chart", wraps=st.line_chart) as chart:
            app = self.calculate()
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics["Future Value"], "¥21,589.25")
        self.assertEqual(metrics["Initial Investment"], "¥10,000.00")
        self.assertEqual(metrics["Annual Return"], "8.00%")
        self.assertEqual(metrics["Investment Period"], "10 years")
        data = chart.call_args.args[0]
        self.assertEqual(data["Year"], list(range(11)))
        self.assertEqual(data["Portfolio Value"][0], 10000)
        self.assertAlmostEqual(data["Portfolio Value"][-1], 21589.24997272788)
        for previous, current in zip(data["Portfolio Value"], data["Portfolio Value"][1:]):
            self.assertAlmostEqual(current, previous * 1.08)
        self.assertEqual(chart.call_args.kwargs["x_label"], "Year")
        self.assertEqual(chart.call_args.kwargs["y_label"], "Portfolio Value")

    def test_zero_rate(self):
        app = self.calculate(rate=0.0)
        self.assertEqual({item.label: item.value for item in app.metric}["Future Value"], "¥10,000.00")

    def test_zero_years(self):
        with patch("streamlit.scatter_chart", wraps=st.scatter_chart) as chart:
            app = self.calculate(years=0)
        self.assertFalse(app.error)
        self.assertEqual(chart.call_args.args[0], {"Year": [0], "Portfolio Value": [10000.0]})

    def test_invalid_inputs(self):
        for principal, rate, years, message in [
            (-1.0, 8.0, 10, "本金不能为负"),
            (10000.0, -100.0, 10, "年化收益率必须大于 -100%"),
            (10000.0, -101.0, 10, "年化收益率必须大于 -100%"),
            (10000.0, 8.0, -1, "投资年限不能为负"),
        ]:
            with self.subTest(principal=principal, rate=rate, years=years):
                app = self.calculate(principal, rate, years)
                self.assertIn(message, app.error[0].value)
                self.assertEqual(len(app.metric), 0)

    def test_overflow(self):
        app = self.calculate(rate=10000.0, years=1000)
        self.assertIn("超出支持范围", app.error[0].value)

    def test_valid_after_error(self):
        app = self.calculate(principal=-1.0)
        app.number_input[0].set_value(10000.0)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertEqual({item.label: item.value for item in app.metric}["Future Value"], "¥21,589.25")


if __name__ == "__main__":
    unittest.main()
