"""Goal Planner 页面、目标线及原模块回归。"""
import unittest
from pathlib import Path
from unittest.mock import patch
import streamlit as st
from streamlit.testing.v1 import AppTest


class GoalPlannerUITests(unittest.TestCase):
    def calculate(self, target=1000000.0, principal=100000.0, rate=8.0, years=10):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit_app.py'), default_timeout=15).run()
        for key, value in [('goal_target', target), ('goal_principal', principal), ('goal_rate', rate), ('goal_years', years)]:
            app.number_input(key=key).set_value(value)
        app.button[2].click().run()
        self.assertFalse(app.exception)
        return app

    def test_standard_chart_table_and_insight(self):
        with patch('streamlit.line_chart', wraps=st.line_chart) as chart:
            app = self.calculate()
        self.assertEqual([t.label for t in app.tabs], ['Compound Interest / 复利计算', 'DCA Simulator / 定投模拟', 'Goal Planner / 目标规划', 'Portfolio Analytics / 组合分析'])
        metrics = {m.label: m.value for m in app.metric}
        self.assertEqual(metrics['Required Monthly Contribution / 每月所需投入'], '¥4,252.82')
        self.assertEqual(metrics['Total Contributions / 累计投入'], '¥610,338.02')
        self.assertEqual(metrics['Investment Growth / 投资增长'], '¥389,661.98')
        data = chart.call_args.args[0]
        self.assertEqual(data['Year'], list(range(11)))
        self.assertEqual(data['Target Value'], [1000000] * 11)
        self.assertAlmostEqual(data['Portfolio Value'][-1], 1000000, delta=0.001)
        table = app.dataframe[0].value
        self.assertEqual(table.iloc[0]['Remaining Gap to Target'], '¥900,000.00')
        self.assertEqual(table.iloc[-1]['Remaining Gap to Target'], '¥0.00')
        self.assertTrue(any('在当前假设下' in m.value for m in app.markdown))

    def test_sufficient_principal(self):
        app = self.calculate(target=10000.0, principal=20000.0, rate=0.0)
        self.assertEqual({m.label:m.value for m in app.metric}['Required Monthly Contribution / 每月所需投入'], '¥0.00')
        self.assertTrue(any('无需额外月投入' in m.value for m in app.markdown))

    def test_invalid_and_recovery(self):
        for args, text in [({'target':0.0}, '目标资产必须大于 0'), ({'principal':-1.0}, '初始本金不能为负'), ({'rate':-100.0}, '年化收益率必须大于 -100%'), ({'years':0}, '投资年限必须大于 0')]:
            with self.subTest(args=args):
                app = self.calculate(**args)
                self.assertIn(text, app.error[0].value)
        app.number_input(key='goal_years').set_value(10)
        app.button[2].click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)

    def test_existing_modules_after_goal(self):
        app = self.calculate()
        app.button[1].click().run()
        self.assertFalse(app.exception)
        self.assertEqual({m.label:m.value for m in app.metric}['Future Value / 未来价值'], '¥205,142.44')
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual({m.label:m.value for m in app.metric}['Future Value / 未来价值'], '¥21,589.25')


if __name__ == '__main__':
    unittest.main()
