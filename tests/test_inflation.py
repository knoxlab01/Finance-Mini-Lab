import unittest
from src.inflation import adjust_for_inflation
from src.compound_interest import calculate_future_value
from src.dca import calculate_dca


class InflationTests(unittest.TestCase):
    def test_zero_inflation(self):
        result = adjust_for_inflation(10000, 0, 10)
        self.assertEqual(result["real_value"], 10000)
        self.assertEqual(result["purchasing_power_loss"], 0)

    def test_positive_inflation_and_horizon(self):
        short = adjust_for_inflation(10000, .02, 10)
        long = adjust_for_inflation(10000, .02, 20)
        self.assertLess(short["real_value"], 10000)
        self.assertGreater(long["purchasing_power_loss"], short["purchasing_power_loss"])

    def test_standard_modules(self):
        for nominal in [calculate_future_value(10000, .08, 10), calculate_dca(10000, 1000, .08, 10)["final_portfolio_value"]]:
            result = adjust_for_inflation(nominal, .02, 10)
            self.assertAlmostEqual(result["real_value"], nominal / 1.02 ** 10, delta=1e-8)
            self.assertAlmostEqual(result["purchasing_power_loss"], nominal - result["real_value"])

    def test_zero_value_zero_years_and_deflation(self):
        self.assertEqual(adjust_for_inflation(0, .02, 10)["real_value"], 0)
        self.assertEqual(adjust_for_inflation(10000, .02, 0)["real_value"], 10000)
        self.assertLess(adjust_for_inflation(10000, -.02, 10)["purchasing_power_loss"], 0)

    def test_invalid(self):
        for args in [(10000, -1, 10), (10000, -2, 10), (-1, .02, 10), (10000, .02, -1), (10000, float('nan'), 10), (float('inf'), .02, 10)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                adjust_for_inflation(*args)

    def test_extremes(self):
        for rate in [100, -.9999]:
            with self.subTest(rate=rate), self.assertRaises(OverflowError):
                adjust_for_inflation(10000, rate, 1000)
