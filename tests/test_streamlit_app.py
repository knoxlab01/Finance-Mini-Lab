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

    def test_product_intro_and_module_overview(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "streamlit_app.py"), default_timeout=15).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "Finance Mini Lab v0.1")
        self.assertIn("A lightweight financial planning toolkit for exploring long-term investment growth.", [m.value for m in app.markdown])
        self.assertTrue(any("仅用于教育和模拟，不构成投资建议" in c.value for c in app.caption))
        for name in ["Compound Interest", "DCA Simulator", "Goal Planner"]:
            self.assertIn(f"**{name}**", [m.value for m in app.markdown])
        self.assertEqual([tab.label for tab in app.tabs], [
            "Compound Interest / 复利计算", "DCA Simulator / 定投模拟", "Goal Planner / 目标规划",
        ])
        self.assertEqual([item.value for item in app.number_input], [
            10000.0, 8.0, 10, 2.0, 10000.0, 1000.0, 8.0, 10, 2.0, 1000000.0, 100000.0, 8.0, 10,
        ])
        self.assertEqual(len(app.button), 3)

    def test_default_result_and_growth_data(self):
        with patch("streamlit.line_chart", wraps=st.line_chart) as chart:
            app = self.calculate()
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics["Future Value / 未来价值"], "¥21,589.25")
        self.assertEqual(metrics["Initial Principal / 初始本金"], "¥10,000.00")
        self.assertEqual(metrics["Annual Return / 年化收益率"], "8.00%")
        self.assertEqual(metrics["Investment Period / 投资年限"], "10 years")
        data = chart.call_args_list[0].args[0]
        self.assertEqual(data["Year"], list(range(11)))
        self.assertEqual(data["Portfolio Value"][0], 10000)
        self.assertAlmostEqual(data["Portfolio Value"][-1], 21589.24997272788)
        for previous, current in zip(data["Portfolio Value"], data["Portfolio Value"][1:]):
            self.assertAlmostEqual(current, previous * 1.08)
        self.assertEqual(chart.call_args_list[0].kwargs["x_label"], "Year")
        self.assertEqual(chart.call_args_list[0].kwargs["y_label"], "Value (¥)")

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
        self.assertEqual(metrics["Investment Growth / 投资增长"], "¥11,589.25")
        self.assertEqual(metrics["Total Return / 总收益率"], "115.89%")
        self.assertEqual(metrics["Estimated Doubling Time / 估算翻倍年限"], "9.00 years")
        table = app.dataframe[0].value
        self.assertEqual(table["Year"].tolist(), list(range(11)))
        self.assertEqual(table.iloc[0]["Portfolio Value"], "¥10,000.00")
        self.assertEqual(table.iloc[0]["Investment Growth"], "¥0.00")
        self.assertEqual(table.iloc[-1]["Portfolio Value"], "¥21,589.25")
        self.assertEqual(table.iloc[-1]["Investment Growth"], "¥11,589.25")
        self.assertTrue(any("近似" in item.value and "精确" in item.value for item in app.caption))

    def test_single_scenario_chart_and_year_domain(self):
        for years in [0, 1, 10, 37, 1000]:
            with self.subTest(years=years), patch("streamlit.vega_lite_chart", wraps=st.vega_lite_chart) as chart, patch("streamlit.line_chart", wraps=st.line_chart) as base_chart:
                self.calculate(years=years, rate=0.0)
                self.assertEqual(chart.call_count, 1)
                self.assertEqual(base_chart.call_count, 0 if years == 0 else 1)
                spec = chart.call_args.kwargs["spec"]
                axis = spec["encoding"]["x"]
                self.assertEqual(axis["scale"]["domain"], [0] if years == 0 else [0, years])
                self.assertFalse(axis["scale"]["nice"])
                self.assertEqual(axis["axis"]["values"][0], 0)
                self.assertEqual(axis["axis"]["values"][-1], years)
                self.assertNotIn("params", spec)
                self.assertTrue(all(0 <= row["Year"] <= years for row in spec["data"]["values"]))
                self.assertEqual(spec["mark"]["type"], "point" if years == 0 else "line")

    def test_named_scenario_analysis(self):
        with patch("streamlit.vega_lite_chart", wraps=st.vega_lite_chart) as chart:
            app = self.calculate()
        self.assertIn("Scenario Analysis / 情景分析", [item.value for item in app.subheader])
        table = app.dataframe[1].value
        self.assertEqual(table["Scenario / 情景"].tolist(), ["Conservative / 保守", "Base / 基准", "Optimistic / 乐观"])
        self.assertEqual(table["Annual Return / 年化收益率"].tolist(), ["5.00%", "8.00%", "11.00%"])
        self.assertEqual(table["Future Value / 未来价值"].tolist(), ["¥16,288.95", "¥21,589.25", "¥28,394.21"])
        spec = chart.call_args.kwargs["spec"]
        data = spec["data"]["values"]
        self.assertEqual(len(set(row["Scenario"] for row in data)), 3)
        base = [row for row in data if row["Scenario"] == "Base / 基准 (8.00%)"]
        self.assertEqual([row["Year"] for row in base], list(range(11)))
        self.assertAlmostEqual(base[-1]["Portfolio Value"], 21589.24997272788)
        self.assertEqual(spec["encoding"]["y"]["title"], "Portfolio Value (¥)")
        self.assertTrue(any("不代表未来收益预测" in item.value for item in app.caption))

    def test_named_scenario_boundaries(self):
        app = self.calculate(rate=-99.0)
        self.assertFalse(app.error)
        self.assertTrue(app.info)
        self.assertEqual(app.dataframe[1].value.iloc[0]["Annual Return / 年化收益率"], "-99.50%")
        app = self.calculate(principal=1e300, rate=0.0, years=1000)
        self.assertFalse(app.error)
        self.assertEqual(app.dataframe[1].value.iloc[2]["Future Value / 未来价值"], "N/A")

    def test_breakdown(self):
        with patch("streamlit.bar_chart", wraps=st.bar_chart) as chart:
            self.calculate()
        data = chart.call_args.args[0]
        self.assertEqual(data["Component"], ["Initial Principal", "Investment Growth"])
        self.assertEqual(data["Amount"][0], 10000)
        self.assertAlmostEqual(data["Amount"][1], 11589.24997272788)

    def test_zero_principal(self):
        app = self.calculate(principal=0.0)
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics["Total Return / 总收益率"], "N/A")
        self.assertEqual(metrics["Investment Growth / 投资增长"], "¥0.00")
        self.assertTrue(any("资产保持为零" in item.value for item in app.markdown))

    def test_nonpositive_rate_insights(self):
        for rate, profit, total_return in [(0.0, "¥0.00", "0.00%"), (-10.0, "¥-1,000.00", "-10.00%")]:
            with self.subTest(rate=rate):
                app = self.calculate(rate=rate, years=1)
                metrics = {item.label: item.value for item in app.metric}
                self.assertEqual(metrics["Investment Growth / 投资增长"], profit)
                self.assertEqual(metrics["Total Return / 总收益率"], total_return)
                self.assertNotIn("Estimated Doubling Time / 估算翻倍年限", metrics)

    def test_scenario_overflow_preserves_current_result(self):
        app = self.calculate(principal=1e300, rate=0.0, years=1000)
        self.assertFalse(app.error)
        self.assertTrue(app.warning)
        self.assertEqual({item.label: item.value for item in app.metric}["Total Return / 总收益率"], "0.00%")


if __name__ == "__main__":
    unittest.main()
