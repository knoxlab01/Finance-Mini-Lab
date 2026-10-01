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
        self.assertEqual(metrics["Future Value / 未来价值"], "¥21,589.25")
        self.assertEqual(metrics["Initial Investment / 初始本金"], "¥10,000.00")
        self.assertEqual(metrics["Annual Return / 年化收益率"], "8.00%")
        self.assertEqual(metrics["Investment Period / 投资年限"], "10 years")
        data = chart.call_args_list[0].args[0]
        self.assertEqual(data["Year"], list(range(11)))
        self.assertEqual(data["Portfolio Value"][0], 10000)
        self.assertAlmostEqual(data["Portfolio Value"][-1], 21589.24997272788)
        for previous, current in zip(data["Portfolio Value"], data["Portfolio Value"][1:]):
            self.assertAlmostEqual(current, previous * 1.08)
        self.assertEqual(chart.call_args_list[0].kwargs["x_label"], "Year")
        self.assertEqual(chart.call_args_list[0].kwargs["y_label"], "Portfolio Value (¥)")

    def test_zero_rate(self):
        app = self.calculate(rate=0.0)
        self.assertEqual({item.label: item.value for item in app.metric}["Future Value / 未来价值"], "¥10,000.00")

    def test_zero_years(self):
        with patch("streamlit.scatter_chart", wraps=st.scatter_chart) as chart:
            app = self.calculate(years=0)
        self.assertFalse(app.error)
        self.assertEqual(chart.call_args_list[0].args[0], {"Year": [0], "Portfolio Value": [10000.0]})

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
        self.assertEqual({item.label: item.value for item in app.metric}["Future Value / 未来价值"], "¥21,589.25")


    def test_profit_return_table_and_rule72(self):
        app = self.calculate()
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics["Total Profit / 累计收益"], "¥11,589.25")
        self.assertEqual(metrics["Total Return / 总收益率"], "115.89%")
        self.assertEqual(metrics["Estimated Doubling Time / 估算翻倍年限"], "9.00 years")
        table = app.dataframe[0].value
        self.assertEqual(table["Year"].tolist(), list(range(11)))
        self.assertEqual(table.iloc[0]["Portfolio Value"], "¥10,000.00")
        self.assertEqual(table.iloc[0]["Profit vs Initial"], "¥0.00")
        self.assertEqual(table.iloc[-1]["Portfolio Value"], "¥21,589.25")
        self.assertEqual(table.iloc[-1]["Profit vs Initial"], "¥11,589.25")
        self.assertTrue(any("近似" in item.value and "精确" in item.value for item in app.caption))

    def test_scenario_comparison_and_deduplication(self):
        for rate, expected_rates in [(8.0, [4.0, 8.0, 12.0]), (4.0, [4.0, 12.0]), (12.0, [4.0, 12.0])]:
            with self.subTest(rate=rate), patch("streamlit.line_chart", wraps=st.line_chart) as chart:
                self.calculate(rate=rate)
                data = chart.call_args_list[1].args[0]
                labels = list(data)[1:]
                self.assertEqual(len(labels), len(expected_rates))
                self.assertEqual(sum("Current" in label for label in labels), 1)
                for label, scenario_rate in zip(labels, expected_rates):
                    self.assertEqual(data[label][0], 10000)
                    self.assertAlmostEqual(data[label][-1], 10000 * (1 + scenario_rate / 100) ** 10)

    def test_breakdown(self):
        with patch("streamlit.bar_chart", wraps=st.bar_chart) as chart:
            self.calculate()
        data = chart.call_args.args[0]
        self.assertEqual(data["Component"], ["Initial Principal", "Compound Growth"])
        self.assertEqual(data["Amount"][0], 10000)
        self.assertAlmostEqual(data["Amount"][1], 11589.24997272788)

    def test_zero_principal(self):
        app = self.calculate(principal=0.0)
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics["Total Return / 总收益率"], "N/A")
        self.assertEqual(metrics["Total Profit / 累计收益"], "¥0.00")
        self.assertTrue(any("资产保持为零" in item.value for item in app.markdown))

    def test_nonpositive_rate_insights(self):
        for rate, profit, total_return in [(0.0, "¥0.00", "0.00%"), (-10.0, "¥-1,000.00", "-10.00%")]:
            with self.subTest(rate=rate):
                app = self.calculate(rate=rate, years=1)
                metrics = {item.label: item.value for item in app.metric}
                self.assertEqual(metrics["Total Profit / 累计收益"], profit)
                self.assertEqual(metrics["Total Return / 总收益率"], total_return)
                self.assertNotIn("Estimated Doubling Time / 估算翻倍年限", metrics)

    def test_scenario_overflow_preserves_current_result(self):
        app = self.calculate(principal=1e300, rate=0.0, years=1000)
        self.assertFalse(app.error)
        self.assertTrue(app.warning)
        self.assertEqual({item.label: item.value for item in app.metric}["Total Return / 总收益率"], "0.00%")


if __name__ == "__main__":
    unittest.main()
