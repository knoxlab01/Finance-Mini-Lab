"""验证 DCA 页面、图表及双模块独立运行。"""

import unittest
from pathlib import Path
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest


class DCAUITests(unittest.TestCase):
    def calculate(self, principal=10000.0, contribution=1000.0, rate=8.0, years=10):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "streamlit_app.py"), default_timeout=15).run()
        app.number_input(key="dca_principal").set_value(principal)
        app.number_input(key="dca_contribution").set_value(contribution)
        app.number_input(key="dca_rate").set_value(rate)
        app.number_input(key="dca_years").set_value(years)
        app.button[1].click().run()
        self.assertFalse(app.exception)
        return app

    def test_standard_result_chart_and_table(self):
        with patch("streamlit.line_chart", wraps=st.line_chart) as chart:
            app = self.calculate()
        self.assertEqual([tab.label for tab in app.tabs], ["Compound Interest / 复利计算", "DCA Simulator / 定投模拟", "Goal Planner / 目标规划"])
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics["Final Portfolio Value / 最终资产"], "¥205,142.44")
        self.assertEqual(metrics["Total Contributions / 累计投入"], "¥130,000.00")
        self.assertEqual(metrics["Investment Growth / 投资收益"], "¥75,142.44")
        self.assertEqual(metrics["Total Return / 总收益率"], "57.80%")
        data = chart.call_args.args[0]
        self.assertEqual(data["Year"], list(range(11)))
        self.assertEqual(data["Total Contributions"][-1], 130000)
        self.assertAlmostEqual(data["Portfolio Value"][-1], 205142.4375271555)
        table = app.dataframe[0].value
        self.assertEqual(table.iloc[0]["Portfolio Value"], "¥10,000.00")
        self.assertEqual(table.iloc[-1]["Investment Growth"], "¥75,142.44")

    def test_invalid_inputs(self):
        for args, message in [({"principal": -1.0}, "初始本金不能为负"),
                              ({"contribution": -1.0}, "每月投入不能为负"),
                              ({"rate": -100.0}, "年化收益率必须大于 -100%"),
                              ({"years": -1}, "投资年限不能为负")]:
            with self.subTest(args=args):
                app = self.calculate(**args)
                self.assertIn(message, app.error[0].value)

    def test_zero_investment_and_zero_years(self):
        app = self.calculate(principal=0.0, contribution=0.0, years=0)
        self.assertFalse(app.error)
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics["Final Portfolio Value / 最终资产"], "¥0.00")
        self.assertEqual(metrics["Total Return / 总收益率"], "N/A")
        self.assertEqual(len(app.dataframe[0].value), 1)

    def test_compound_still_works_after_dca(self):
        app = self.calculate()
        app.button[0].click().run()
        self.assertFalse(app.exception)
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics["Future Value / 未来价值"], "¥21,589.25")


if __name__ == "__main__":
    unittest.main()
