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
        self.assertEqual(app.title[0].value, "Vexa")
        self.assertIn("**Portfolio Intelligence, Made Clear.**", [m.value for m in app.markdown])
        self.assertIn("Vexa combines traditional portfolio analytics, probabilistic forward simulation, and the Evolance interpretation framework to turn complex financial signals into clearer decision support.", [m.value for m in app.markdown])
        self.assertTrue(any("Not investment advice" in c.value for c in app.caption))
        self.assertIn("v0.4 development · Developed in Finance Mini Lab · Program One", [c.value for c in app.caption])
        for name in ["Compound Interest", "DCA Simulator", "Goal Planner", "Portfolio Analytics"]:
            self.assertIn(f"**{name}**", [m.value for m in app.markdown])
        self.assertEqual([tab.label for tab in app.tabs], [
            'Compound Interest', 'DCA Simulator', 'Goal Planner',
            'Portfolio Analytics',
        ])
        self.assertEqual([item.value for item in app.number_input], [
            10000.0, 8.0, 10, 2.0, 10000.0, 1000.0, 8.0, 10, 2.0, 1000000.0, 100000.0, 8.0, 10, 4.0,
        ])
        self.assertEqual(len(app.button), 6)

    def test_browser_title_is_product_facing_without_release_claim(self):
        with patch("streamlit.set_page_config", wraps=st.set_page_config) as page_config:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "streamlit_app.py"), default_timeout=15).run()
        self.assertFalse(app.exception)
        self.assertEqual(page_config.call_args.kwargs["page_title"], "Vexa — Portfolio Intelligence, Made Clear")
        self.assertNotIn("v0.3.0", app.title[0].value)

    def test_default_result_and_growth_data(self):
        with patch("streamlit.line_chart", wraps=st.line_chart) as chart:
            app = self.calculate()
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics['Future Value'], "¥21,589.25")
        self.assertEqual(metrics['Initial Principal'], "¥10,000.00")
        self.assertEqual(metrics['Annual Return'], "8.00%")
        self.assertEqual(metrics['Investment Period'], "10 years")
        data = chart.call_args_list[0].args[0]
        self.assertEqual(data['Year'], list(range(11)))
        self.assertEqual(data['Portfolio Value'][0], 10000)
        self.assertAlmostEqual(data['Portfolio Value'][-1], 21589.24997272788)
        for previous, current in zip(data['Portfolio Value'], data['Portfolio Value'][1:]):
            self.assertAlmostEqual(current, previous * 1.08)
        self.assertEqual(chart.call_args_list[0].kwargs["x_label"], 'Year')
        self.assertEqual(chart.call_args_list[0].kwargs["y_label"], 'Value (¥)')

    def test_zero_rate(self):
        app = self.calculate(rate=0.0)
        self.assertEqual({item.label: item.value for item in app.metric}['Future Value'], "¥10,000.00")

    def test_zero_years(self):
        with patch("streamlit.scatter_chart", wraps=st.scatter_chart) as chart:
            app = self.calculate(years=0)
        self.assertFalse(app.error)
        self.assertEqual(chart.call_args_list[0].args[0], {'Year': [0], 'Portfolio Value': [10000.0]})

    def test_invalid_inputs(self):
        for principal, rate, years, message in [
            (-1.0, 8.0, 10, 'Principal cannot be negative'),
            (10000.0, -100.0, 10, 'Annual return must be above -100%'),
            (10000.0, -101.0, 10, 'Annual return must be above -100%'),
            (10000.0, 8.0, -1, 'Investment period cannot be negative'),
        ]:
            with self.subTest(principal=principal, rate=rate, years=years):
                app = self.calculate(principal, rate, years)
                self.assertIn(message, app.error[0].value)
                self.assertEqual(len(app.metric), 0)

    def test_overflow(self):
        app = self.calculate(rate=10000.0, years=1000)
        self.assertIn("exceeds the supported range", app.error[0].value)

    def test_valid_after_error(self):
        app = self.calculate(principal=-1.0)
        app.number_input[0].set_value(10000.0)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertEqual({item.label: item.value for item in app.metric}['Future Value'], "¥21,589.25")


    def test_profit_return_table_and_rule72(self):
        app = self.calculate()
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics['Investment Growth'], "¥11,589.25")
        self.assertEqual(metrics['Total Return'], "115.89%")
        self.assertEqual(metrics['Estimated Doubling Time'], "9.00 years")
        table = app.dataframe[0].value
        self.assertEqual(table['Year'].tolist(), list(range(11)))
        self.assertEqual(table.iloc[0]['Portfolio Value'], "¥10,000.00")
        self.assertEqual(table.iloc[0]['Investment Growth'], "¥0.00")
        self.assertEqual(table.iloc[-1]['Portfolio Value'], "¥21,589.25")
        self.assertEqual(table.iloc[-1]['Investment Growth'], "¥11,589.25")
        self.assertTrue(any("Approximation" in item.value and "exact" in item.value for item in app.caption))

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
                self.assertTrue(all(0 <= row['Year'] <= years for row in spec["data"]["values"]))
                self.assertEqual(spec["mark"]["type"], "point" if years == 0 else "line")

    def test_named_scenario_analysis(self):
        with patch("streamlit.vega_lite_chart", wraps=st.vega_lite_chart) as chart:
            app = self.calculate()
        self.assertIn('Scenario Analysis', [item.value for item in app.subheader])
        table = app.dataframe[1].value
        self.assertEqual(table['Scenario'].tolist(), ['Conservative', 'Base', 'Optimistic'])
        self.assertEqual(table['Annual Return'].tolist(), ["5.00%", "8.00%", "11.00%"])
        self.assertEqual(table['Future Value'].tolist(), ["¥16,288.95", "¥21,589.25", "¥28,394.21"])
        spec = chart.call_args.kwargs["spec"]
        data = spec["data"]["values"]
        self.assertEqual(len(set(row['Scenario'] for row in data)), 3)
        base = [row for row in data if row['Scenario'] == "Base (8.00%)"]
        self.assertEqual([row['Year'] for row in base], list(range(11)))
        self.assertAlmostEqual(base[-1]['Portfolio Value'], 21589.24997272788)
        self.assertEqual(spec["encoding"]["y"]["title"], 'Portfolio Value (¥)')
        self.assertTrue(any("not future-return predictions" in item.value for item in app.caption))

    def test_named_scenario_boundaries(self):
        app = self.calculate(rate=-99.0)
        self.assertFalse(app.error)
        self.assertTrue(app.info)
        self.assertEqual(app.dataframe[1].value.iloc[0]['Annual Return'], "-99.50%")
        app = self.calculate(principal=1e300, rate=0.0, years=1000)
        self.assertFalse(app.error)
        self.assertEqual(app.dataframe[1].value.iloc[2]['Future Value'], "N/A")

    def test_breakdown(self):
        with patch("streamlit.bar_chart", wraps=st.bar_chart) as chart:
            self.calculate()
        data = chart.call_args.args[0]
        self.assertEqual(data['Component'], ['Initial Principal', 'Investment Growth'])
        self.assertEqual(data['Amount'][0], 10000)
        self.assertAlmostEqual(data['Amount'][1], 11589.24997272788)

    def test_zero_principal(self):
        app = self.calculate(principal=0.0)
        metrics = {item.label: item.value for item in app.metric}
        self.assertEqual(metrics['Total Return'], "N/A")
        self.assertEqual(metrics['Investment Growth'], "¥0.00")
        self.assertTrue(any("assets remain zero" in item.value for item in app.markdown))

    def test_nonpositive_rate_insights(self):
        for rate, profit, total_return in [(0.0, "¥0.00", "0.00%"), (-10.0, "¥-1,000.00", "-10.00%")]:
            with self.subTest(rate=rate):
                app = self.calculate(rate=rate, years=1)
                metrics = {item.label: item.value for item in app.metric}
                self.assertEqual(metrics['Investment Growth'], profit)
                self.assertEqual(metrics['Total Return'], total_return)
                self.assertNotIn('Estimated Doubling Time', metrics)

    def test_scenario_overflow_preserves_current_result(self):
        app = self.calculate(principal=1e300, rate=0.0, years=1000)
        self.assertFalse(app.error)
        self.assertTrue(app.warning)
        self.assertEqual({item.label: item.value for item in app.metric}['Total Return'], "0.00%")


if __name__ == "__main__":
    unittest.main()
