"""Offline guidance scenarios, missing evidence and profile constraints."""
from copy import deepcopy
import unittest
import numpy as np
import pandas as pd
from src.portfolio_guidance import assess_portfolio_risk, assess_profile_fit, generate_guidance


def profile(risk="Balanced", horizon="Long Term", goal="Steady Growth"):
    return dict(risk_preference=risk, investment_horizon=horizon, primary_goal=goal)


def history(vol=.18, dd=-.2, correlation=.3, loss=.2):
    result = dict(metrics=pd.DataFrame({"Portfolio": {"Annualized Volatility": vol, "Maximum Drawdown": dd, "CAGR": .1, "Cumulative Return": .2, "Sharpe Ratio": .5},
                                     "Benchmark": {"Annualized Volatility": .2, "Maximum Drawdown": -.2, "CAGR": .08, "Sharpe Ratio": .6}}),
                  correlation=pd.DataFrame([[1., correlation], [correlation, 1.]], columns=["A", "B"], index=["A", "B"]),
                  portfolio_config={"weights": [.4, .3, .3]}, source_metadata={"A": {"provider": "yahoo"}})
    if loss is not None:
        result["future_outlook"] = dict(simulation=dict(loss_probability=loss, horizon=5, initial_value=100000, p10=80000, p50=120000, p90=200000),
                                       parameters=dict(expected_return=.1, volatility=.2),
                                       scenarios=dict(checkpoints=pd.DataFrame({"Conservative": [80000], "Base": [120000], "Optimistic": [180000]}, index=[5])))
    return result


class GuidanceTests(unittest.TestCase):
    def test_conservative_high_risk(self):
        result = generate_guidance(history(.35, -.4, .9, .4), profile("Conservative"))
        self.assertEqual(result["assessment"]["level"], 2)
        self.assertIn("Too Aggressive", result["fit"]["label"])

    def test_aggressive_high_risk(self):
        result = generate_guidance(history(.35, -.4, .9, .4), profile("Aggressive", "Long Term", "Growth Priority"))
        self.assertIn("Good Fit", result["fit"]["label"])
        self.assertTrue(result["recommendations"])

    def test_balanced_moderate_good_fit(self):
        result = generate_guidance(history(), profile())
        self.assertEqual(result["assessment"]["level"], 1)
        self.assertIn("Good Fit", result["fit"]["label"])

    def test_short_horizon_caps_risk(self):
        result = generate_guidance(history(.35, -.4), profile("Aggressive", "Short Term", "Growth Priority"))
        self.assertEqual(result["fit"]["target"], 0)
        self.assertIn("Too Aggressive", result["fit"]["label"])

    def test_long_growth_allocation(self):
        result = generate_guidance(history(), profile("Aggressive", "Long Term", "Growth Priority"))
        self.assertEqual(result["fit"]["target"], 2)
        self.assertIn("growth categories", result["allocation"])

    def test_preservation_overrides_growth_tolerance(self):
        result = generate_guidance(history(), profile("Aggressive", "Long Term", "Capital Preservation"))
        self.assertEqual(result["fit"]["target"], 0)

    def test_conservative_not_overridden_by_long_growth(self):
        result = generate_guidance(history(), profile("Conservative", "Long Term", "Growth Priority"))
        self.assertEqual(result["fit"]["target"], 0)

    def test_metric_warning_reasons(self):
        for key, kwargs, category, text in [("correlation", {"correlation": .9}, "Diversification", "0.90"),
                                           ("drawdown", {"dd": -.4}, "Drawdown", "-40.0%"),
                                           ("loss", {"loss": .5}, "Downside Risk", "50.0%")]:
            with self.subTest(key=key):
                result = generate_guidance(history(**kwargs), profile())
                item = next(r for r in result["recommendations"] if r["category"] == category)
                self.assertIn(text, item["reason"])

    def test_concentration_and_benchmark(self):
        result = history(vol=.3)
        result["portfolio_config"]["weights"] = [.7, .3]
        assessment = assess_portfolio_risk(result)
        self.assertEqual(next(e for e in assessment["evidence"] if e["key"] == "concentration")["points"], 1)
        self.assertEqual(next(e for e in assessment["evidence"] if e["key"] == "benchmark_risk")["points"], 1)

    def test_missing_future_basic_guidance(self):
        result = generate_guidance(history(loss=None), profile())
        self.assertIsNotNone(result["assessment"]["level"])
        self.assertTrue(any("Run Future Outlook" in n for n in result["notices"]))
        self.assertTrue(3 <= len(result["recommendations"]) <= 5)

    def test_missing_historical_no_rating(self):
        result = generate_guidance(None, profile())
        self.assertIsNone(result["assessment"]["level"])
        self.assertFalse(result["recommendations"])
        self.assertIsNone(result["allocation"])

    def test_incomplete_profile(self):
        result = generate_guidance(history(), {})
        self.assertIsNone(result["fit"]["target"])
        self.assertFalse(result["recommendations"])

    def test_zero_volatility(self):
        result = generate_guidance(history(0, 0, loss=0), profile("Conservative"))
        self.assertEqual(result["assessment"]["level"], 0)
        self.assertIn("Good Fit", result["fit"]["label"])

    def test_missing_correlation_benchmark_mc(self):
        data = history(loss=None)
        data["correlation"] = pd.DataFrame([[np.nan]])
        data["metrics"].drop(columns="Benchmark", inplace=True)
        result = generate_guidance(data, profile())
        self.assertTrue(any("Correlation" in n for n in result["notices"]))
        self.assertTrue(any("Benchmark" in n for n in result["notices"]))
        self.assertTrue(result["recommendations"])

    def test_invalid_core_withholds_fit(self):
        for value in [None, np.nan, np.inf, -.1]:
            data = history(vol=value)
            result = generate_guidance(data, profile())
            self.assertIsNone(result["assessment"]["level"])
            self.assertFalse(result["recommendations"])

    def test_partial_correlation_is_disclosed(self):
        data = history()
        data["correlation"] = pd.DataFrame([[1., .9, np.nan], [.9, 1., np.nan], [np.nan, np.nan, 1.]])
        self.assertTrue(any("Partial" in n for n in assess_portfolio_risk(data)["missing"]))

    def test_recommendation_count_and_no_mutation(self):
        data = history(.4, -.5, .9, .5)
        original = deepcopy(data)
        result = generate_guidance(data, profile())
        self.assertTrue(3 <= len(result["recommendations"]) <= 5)
        self.assertTrue(all(r["reason"] and r["recommendation"] for r in result["recommendations"]))
        self.assertTrue(any(r["category"] == "Profile Alignment" for r in result["recommendations"]))
        pd.testing.assert_frame_equal(data["metrics"], original["metrics"])

    def test_demo_provenance(self):
        data = history()
        data["source_metadata"]["A"]["provider"] = "demo"
        self.assertTrue(generate_guidance(data, profile())["assessment"]["demo"])

    def test_lower_risk_growth_mismatch(self):
        result = generate_guidance(history(.05, -.05, loss=0), profile("Aggressive", "Long Term", "Growth Priority"))
        self.assertIn("Too Conservative", result["fit"]["label"])

    def test_context_reuses_existing_outputs(self):
        context = generate_guidance(history(), profile())["assessment"]["context"]
        self.assertTrue(any("Historical CAGR" in c for c in context))
        self.assertTrue(any("Model annual" in c for c in context))
        self.assertTrue(any("Scenario values" in c for c in context))

    def test_slightly_aggressive_fit(self):
        result = generate_guidance(history(), profile("Conservative"))
        self.assertIn("Slightly Aggressive", result["fit"]["label"])

    def test_threshold_boundaries(self):
        assessment = assess_portfolio_risk(history(vol=.25, dd=-.30, correlation=.75, loss=.35))
        points = {e["key"]: e["points"] for e in assessment["evidence"]}
        self.assertEqual(points["volatility"], 2)
        self.assertEqual(points["drawdown"], 2)
        self.assertEqual(points["loss"], 2)
        self.assertEqual(points["correlation"], 1)

    def test_invalid_optional_data_is_disclosed(self):
        data = history(loss=2.)
        data["correlation"] = pd.DataFrame([["bad", "bad"], ["bad", "bad"]])
        result = generate_guidance(data, profile())
        self.assertTrue(any("Valid simulated" in n for n in result["notices"]))
        self.assertTrue(any("Correlation" in n for n in result["notices"]))
        self.assertFalse(any(e["key"] == "loss" for e in result["assessment"]["evidence"]))

    def test_high_return_does_not_offset_risk(self):
        data = history(.4, -.5, .9, .5)
        before = assess_portfolio_risk(data)["score"]
        data["metrics"].loc["CAGR", "Portfolio"] = 9.
        self.assertEqual(assess_portfolio_risk(data)["score"], before)
