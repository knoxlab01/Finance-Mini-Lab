"""验证月末投入、月度复利和 DCA 输入约束。"""

import unittest

from src.compound_interest import calculate_future_value
from src.dca import calculate_dca


class DCATests(unittest.TestCase):
    def test_standard_case_against_month_end_annuity(self):
        result = calculate_dca(10000, 1000, 0.08, 10)
        monthly_rate = 0.08 / 12
        factor = (1 + monthly_rate) ** 120
        # 独立闭式公式用于验证迭代算法，月末投入的末次款项不产生利息。
        expected = 10000 * factor + 1000 * (factor - 1) / monthly_rate
        self.assertAlmostEqual(result["final_portfolio_value"], expected, places=6)
        self.assertEqual(result["total_contributions"], 130000)
        self.assertAlmostEqual(result["investment_growth"], 75142.4375271555)
        self.assertAlmostEqual(result["total_return"], 0.5780187502088885)

    def test_zero_rate(self):
        result = calculate_dca(10000, 1000, 0, 10)
        self.assertEqual(result["final_portfolio_value"], 130000)
        self.assertEqual(result["investment_growth"], 0)
        for row in result["yearly_data"]:
            self.assertEqual(row["portfolio_value"], 10000 + 12000 * row["year"])
            self.assertEqual(row["investment_growth"], 0)

    def test_no_contribution_monthly_vs_annual_compounding(self):
        result = calculate_dca(10000, 0, 0.08, 10)
        self.assertAlmostEqual(result["final_portfolio_value"], 10000 * (1 + 0.08 / 12) ** 120)
        # 同样的名义年率，月度复利与年度复利并不相同。
        self.assertGreater(result["final_portfolio_value"], calculate_future_value(10000, 0.08, 10))
        effective_annual_rate = (1 + 0.08 / 12) ** 12 - 1
        self.assertAlmostEqual(result["final_portfolio_value"], calculate_future_value(10000, effective_annual_rate, 10))

    def test_zero_initial_principal(self):
        result = calculate_dca(0, 1000, 0.12, 1)
        expected = 1000 * ((1.01 ** 12 - 1) / 0.01)
        self.assertAlmostEqual(result["final_portfolio_value"], expected)
        self.assertEqual(result["total_contributions"], 12000)

    def test_zero_years_and_zero_investment(self):
        result = calculate_dca(10000, 1000, 0.08, 0)
        self.assertEqual(result["final_portfolio_value"], 10000)
        self.assertEqual(result["total_contributions"], 10000)
        self.assertEqual(len(result["yearly_data"]), 1)
        self.assertEqual(result["total_return"], 0)
        empty = calculate_dca(0, 0, 0.08, 10)
        self.assertEqual(empty["final_portfolio_value"], 0)
        self.assertIsNone(empty["total_return"])

    def test_yearly_series(self):
        result = calculate_dca(10000, 1000, 0.08, 10)
        rows = result["yearly_data"]
        self.assertEqual([row["year"] for row in rows], list(range(11)))
        self.assertEqual(rows[0], {"year": 0, "total_contributions": 10000, "portfolio_value": 10000, "investment_growth": 0})
        for row in rows:
            self.assertEqual(row["total_contributions"], 10000 + 12000 * row["year"])
            self.assertAlmostEqual(row["investment_growth"], row["portfolio_value"] - row["total_contributions"])
        self.assertEqual(rows[-1]["portfolio_value"], result["final_portfolio_value"])

    def test_invalid_inputs(self):
        cases = [(-1, 1000, 0.08, 10), (10000, -1, 0.08, 10),
                 (10000, 1000, -1, 10), (10000, 1000, -1.1, 10),
                 (10000, 1000, 0.08, -1), (10000, 1000, 0.08, 1.5),
                 (10000, 1000, 0.08, 1001), (float("nan"), 1000, 0.08, 10),
                 (10000, float("inf"), 0.08, 10), (10000, 1000, float("nan"), 10),
                 (10000, 1000, 0.08, float("inf")), ("abc", 1000, 0.08, 10)]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                calculate_dca(*args)

    def test_negative_rate(self):
        result = calculate_dca(10000, 1000, -0.12, 1)
        self.assertLess(result["final_portfolio_value"], result["total_contributions"])
        self.assertLess(result["investment_growth"], 0)

    def test_overflow(self):
        with self.assertRaises(OverflowError):
            calculate_dca(1e308, 1e308, 0.08, 10)


if __name__ == "__main__":
    unittest.main()
