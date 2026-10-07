"""Offline numerical checks for future scenario analytics."""
import unittest
import numpy as np
import pandas as pd
from src.future_simulation import estimate_parameters, build_scenarios, simulate_monte_carlo, interpret_outcomes
from src.market_data import demo_prices


class FutureSimulationTests(unittest.TestCase):
    def parameters(self):
        return estimate_parameters(pd.Series(np.tile([.01, -.008, .003, -.002], 63)))

    def test_estimation(self):
        returns = pd.Series(np.tile([.01, -.008], 60))
        p = estimate_parameters(returns)
        logs = np.log1p(returns)
        self.assertAlmostEqual(p["log_drift"], logs.mean() * 252)
        self.assertAlmostEqual(p["volatility"], logs.std(ddof=1) * np.sqrt(252))
        self.assertAlmostEqual(p["expected_return"], np.expm1(p["log_drift"] + .5 * p["volatility"]**2))

    def test_short_history(self):
        with self.assertRaisesRegex(ValueError, "60"):
            estimate_parameters([.01] * 59)

    def test_invalid_returns(self):
        for returns in [[], [np.nan]*60, [np.inf]*60, [-1]*60, [-2]*60]:
            with self.subTest(returns=returns[:1]), self.assertRaises(ValueError):
                estimate_parameters(returns)

    def test_scenario_order_and_horizon(self):
        for horizon in [1, 3, 5]:
            result = build_scenarios(self.parameters(), 100000, horizon)
            frame = result["curves"]
            self.assertTrue((frame.Conservative <= frame.Base).all())
            self.assertTrue((frame.Base <= frame.Optimistic).all())
            self.assertEqual(frame.index[-1], horizon)
            self.assertTrue((frame.iloc[0] == 100000).all())
            self.assertEqual(result["checkpoints"].index.tolist(), [y for y in [1, 3, 5] if y <= horizon])
            self.assertAlmostEqual(frame.Base.iloc[-1], 100000*np.exp(self.parameters()["drift"]*horizon))

    def test_fixed_seed_and_dimensions(self):
        a = simulate_monte_carlo(self.parameters(), 100000, 3, 1000, seed=9)
        b = simulate_monte_carlo(self.parameters(), 100000, 3, 1000, seed=9)
        np.testing.assert_array_equal(a["paths"], b["paths"])
        self.assertEqual(a["paths"].shape, (37, 1000))
        self.assertEqual(a["bands"].shape, (37, 3))
        self.assertTrue((a["paths"][0] == 100000).all())
        self.assertLessEqual(a["p10"], a["p50"])
        self.assertLessEqual(a["p50"], a["p90"])
        self.assertTrue(0 <= a["loss_probability"] <= 1)
        self.assertTrue(0 <= a["above_probability"] <= 1)
        self.assertEqual(a["loss_probability"], np.mean(a["ending"] < 100000))
        self.assertEqual(a["above_probability"], np.mean(a["ending"] > 100000))

    def test_zero_volatility(self):
        for daily, loss in [(0., 0.), (.001, 0.), (-.001, 1.)]:
            p = estimate_parameters([daily] * 60)
            self.assertEqual(p["volatility"], 0.)
            result = simulate_monte_carlo(p, 100000, 1, 1000)
            self.assertAlmostEqual(result["p10"], 100000*np.exp(252*np.log1p(daily)))
            self.assertEqual(result["p10"], result["p90"])
            self.assertEqual(result["loss_probability"], loss)
            if daily == 0:
                self.assertEqual(result["above_probability"], 0.)

    def test_invalid_horizon(self):
        for horizon in [0, -1, 2, 1.5, True, np.nan]:
            with self.subTest(horizon=horizon), self.assertRaises(ValueError):
                simulate_monte_carlo(self.parameters(), 100000, horizon)

    def test_invalid_count(self):
        for count in [0, 999, 10001, 1000.5, True]:
            with self.subTest(count=count), self.assertRaises(ValueError):
                simulate_monte_carlo(self.parameters(), 100000, 1, count)

    def test_invalid_value(self):
        for value in [0, -1, np.nan, np.inf, True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                simulate_monte_carlo(self.parameters(), value, 1)

    def test_high_volatility_overflow_is_explicit(self):
        p = dict(log_drift=1000., volatility=100., drift=6000.)
        for fn in [build_scenarios, simulate_monte_carlo]:
            with self.assertRaises(ValueError):
                fn(p, 100000, 5)

    def test_nonfinite_parameters(self):
        p = self.parameters()
        p["volatility"] = np.nan
        with self.assertRaises(ValueError):
            simulate_monte_carlo(p, 100000, 1)

    def test_demo_and_interpretation(self):
        returns = demo_prices("AAPL", "2025-01-01", "2026-01-01").pct_change().dropna()
        result = simulate_monte_carlo(estimate_parameters(returns), 100000, 5)
        self.assertEqual(result["paths"].shape, (61, 5000))
        self.assertEqual(len(interpret_outcomes(result)), 3)

    def test_model_mean_matches_theory(self):
        p = self.parameters()
        result = simulate_monte_carlo(p, 100000, 5, 10000)
        theoretical = 100000*np.exp(p["drift"]*5)
        se = result["ending"].std(ddof=1) / 100
        self.assertLess(abs(result["ending"].mean()-theoretical), 4*se)

    def test_high_but_finite_volatility(self):
        p = dict(log_drift=-.2, volatility=2., drift=1.8)
        result = simulate_monte_carlo(p, 100000, 5, 1000)
        self.assertTrue(np.isfinite(result["paths"]).all())
        self.assertTrue((result["paths"] > 0).all())
        self.assertLessEqual(result["p10"], result["p90"])
