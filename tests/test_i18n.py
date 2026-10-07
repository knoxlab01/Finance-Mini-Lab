"""Translation completeness, numerical invariance and portfolio-only scope."""
import re
import unittest
from copy import deepcopy
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import test_portfolio_ui as portfolio_fixtures
ROOT = portfolio_fixtures.ROOT
from test_portfolio_guidance import history, profile
from src.i18n import CATALOG, tr, metric_help, localize_message
from src.portfolio_guidance import generate_guidance


def contains_chinese(text):
    return bool(re.search(r"[\u4e00-\u9fff]", text))


class TranslationTests(unittest.TestCase):
    def test_catalog_pairs_and_default(self):
        for key, pair in CATALOG.items():
            self.assertEqual(len(pair), 2)
            self.assertTrue(all(pair))
            self.assertFalse(contains_chinese(pair[0]), key)
        self.assertEqual(tr("Portfolio Setup"), "Portfolio Setup")
        self.assertEqual(tr("CAGR", "中文"), "年化复合收益率")

    def test_all_metric_explanations(self):
        for key in ["return", "cagr", "volatility", "sharpe", "drawdown", "correlation", "benchmark", "percentiles", "loss", "scenarios"]:
            self.assertTrue(metric_help(key))
            self.assertTrue(contains_chinese(metric_help(key, "中文")))

    def test_guidance_evidence_translates_without_changes(self):
        for data in [history(), history(.4, -.5, .9, .5), history(0, 0, loss=None), {}]:
            result = generate_guidance(data, profile())
            original = deepcopy(result)
            strings = [result["assessment"]["label"], result["fit"]["label"]] + result["assessment"]["context"] + result["notices"]
            strings += [e["reason"] for e in result["assessment"]["evidence"]]
            strings += [r[key] for r in result["recommendations"] for key in ["recommendation", "reason"]]
            if result["allocation"]:
                strings.append(result["allocation"])
            for value in strings:
                english = localize_message(value)
                chinese = localize_message(value, "中文")
                self.assertFalse(contains_chinese(english), english)
                self.assertNotIn("Historical", chinese)
                self.assertNotIn(" / Review", chinese)
                self.assertNotIn(" / Explore", chinese)
            self.assertEqual(result, original)


class LanguageUITests(unittest.TestCase):
    setUp = portfolio_fixtures.PortfolioUITests.setUp

    def full_app(self):
        app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
        with patch("src.market_data.download_prices", side_effect=TimeoutError()):
            app.button(key="pa_analyze").click().run()
        app.button(key="fo_run").click().run()
        app.button(key="pg_run").click().run()
        self.assertFalse(app.exception)
        return app

    def portfolio_strings(self, app):
        tab = app.tabs[3]
        return [str(node.value) for kind in ["caption", "markdown", "subheader", "info", "warning", "error"] for node in tab.get(kind)]

    def test_default_english_complete_page_and_tooltips(self):
        app = self.full_app()
        self.assertEqual(app.selectbox(key="pa_language").value, "English")
        for text in self.portfolio_strings(app):
            self.assertFalse(contains_chinese(text), text)
        self.assertTrue(all(metric.proto.help for metric in app.metric[:5]))
        self.assertTrue(any("synthetic" in text for text in self.portfolio_strings(app)))
        self.assertTrue(any("Recommendation:" in text for text in self.portfolio_strings(app)))

    def test_switch_preserves_numbers_profile_and_results_without_calls(self):
        app = self.full_app()
        values = [metric.value for metric in app.metric]
        historical = app.session_state["pa_result"]
        paths = historical["future_outlook"]["simulation"]["paths"].copy()
        fit = generate_guidance(historical, historical["guidance_profile"])["fit"]
        with patch("src.portfolio_ui.get_historical_prices") as download, patch("src.future_ui.simulate_monte_carlo") as simulate:
            app.selectbox(key="pa_language").select("中文").run()
        download.assert_not_called()
        simulate.assert_not_called()
        self.assertFalse(app.exception)
        self.assertEqual(values, [metric.value for metric in app.metric])
        import numpy as np
        np.testing.assert_array_equal(paths, app.session_state["pa_result"]["future_outlook"]["simulation"]["paths"])
        self.assertEqual(fit, generate_guidance(app.session_state["pa_result"], historical["guidance_profile"])["fit"])
        text = "\n".join(self.portfolio_strings(app))
        for english in ["Recommendation:", "Historical maximum drawdown", "Simulated terminal loss", "The interval reflects", "Under these assumptions", "feature demonstration", "Share of simulations"]:
            self.assertNotIn(english, text)
        self.assertFalse(re.search(r"[A-Za-z]{3,}(?: [A-Za-z]{3,}){2,}", text), text)
        self.assertIn("合成", text)
        self.assertEqual(app.metric[0].label, "累计收益率")
        self.assertEqual(app.button(key="pa_analyze").label, "分析组合")
        self.assertTrue(any("最大跌幅" in metric.proto.help for metric in app.metric[:5]))
        self.assertEqual(app.tabs[0].label, "Compound Interest / 复利计算")
        app.selectbox(key="pa_language").select("English").run()
        self.assertEqual(values, [metric.value for metric in app.metric])

    def test_validation_message_language(self):
        app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
        app.selectbox(key="pa_language").select("中文").run()
        app.text_input(key="pa_weights").set_value("30,30,30")
        app.button(key="pa_analyze").click().run()
        self.assertFalse(app.exception)
        self.assertNotIn("Nonnegative", app.error[0].value)
        self.assertIn("权重", app.error[0].value)
