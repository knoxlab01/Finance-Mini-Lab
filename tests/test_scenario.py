"""Scenario calculations and boundaries, without changing existing regressions."""
import math
import unittest
from src.compound_interest import calculate_future_value
from src.scenario import calculate_scenarios


class ScenarioTests(unittest.TestCase):
    def test_standard_rates_and_growth(self):
        rows = calculate_scenarios(10000, 0.08, 10)
        for row, rate in zip(rows, [0.05, 0.08, 0.11]):
            self.assertAlmostEqual(row["annual_rate"], rate)
            self.assertEqual(row["years"], list(range(11)))
            self.assertEqual(row["values"][0], 10000)
            self.assertAlmostEqual(row["future_value"], calculate_future_value(10000, rate, 10))
            self.assertAlmostEqual(row["investment_growth"], row["future_value"] - 10000)
        self.assertLess(rows[0]["annual_rate"], rows[1]["annual_rate"])
        self.assertLess(rows[1]["annual_rate"], rows[2]["annual_rate"])
        self.assertLess(rows[0]["future_value"], rows[1]["future_value"])
        self.assertLess(rows[1]["future_value"], rows[2]["future_value"])
        self.assertAlmostEqual(rows[1]["future_value"], 21589.24997272788)

    def test_lower_boundary(self):
        for rate in [-0.97, -0.99, math.nextafter(-1.0, 0.0)]:
            rows = calculate_scenarios(10000, rate, 10)
            self.assertTrue(rows[0]["adjusted"])
            self.assertGreater(rows[0]["annual_rate"], -1)
            self.assertLessEqual(rows[0]["annual_rate"], rate)
            self.assertTrue(all(math.isfinite(row["future_value"]) for row in rows))
        self.assertAlmostEqual(calculate_scenarios(10000, -0.99, 10)[0]["annual_rate"], -0.995)

    def test_zero_principal_and_zero_years(self):
        for row in calculate_scenarios(0, 0.08, 10):
            self.assertEqual(row["future_value"], 0)
        for row in calculate_scenarios(10000, 0.08, 0):
            self.assertEqual(row["values"], [10000])
            self.assertEqual(row["investment_growth"], 0)

    def test_overflow_preserves_base(self):
        rows = calculate_scenarios(1e300, 0, 1000)
        self.assertEqual(rows[1]["future_value"], 1e300)
        self.assertIsNone(rows[2]["future_value"])
        self.assertIsNone(rows[2]["values"])

    def test_invalid_inputs(self):
        for args in [(-1, .08, 10), (10000, -1, 10), (10000, .08, -1),
                     (10000, .08, 1.5), (10000, .08, 1001),
                     (float("inf"), .08, 10), (10000, float("nan"), 10)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                calculate_scenarios(*args)
