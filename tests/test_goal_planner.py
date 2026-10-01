"""目标规划核心测试；回算允许 max(target * 1e-9, 1e-6) 误差。"""
import unittest
from src.dca import calculate_dca
from src.goal_planner import calculate_goal_plan, REL_TOLERANCE, ABS_TOLERANCE


class GoalPlannerTests(unittest.TestCase):
    def assert_target(self, result, target):
        self.assertAlmostEqual(result["final_portfolio_value"], target,
                               delta=max(target * REL_TOLERANCE, ABS_TOLERANCE))

    def test_zero_rate(self):
        result = calculate_goal_plan(130000, 10000, 0, 10)
        self.assertEqual(result["required_monthly_contribution"], 1000)
        self.assertEqual(result["total_contributions"], 130000)
        self.assertEqual(result["investment_growth"], 0)
        self.assert_target(result, 130000)

    def test_principal_sufficient(self):
        for target, principal, rate in [(10000, 10000, 0), (20000, 10000, 0.08), (10000, 20000, 0)]:
            with self.subTest(target=target):
                result = calculate_goal_plan(target, principal, rate, 10)
                self.assertEqual(result["required_monthly_contribution"], 0)
                self.assertGreaterEqual(result["final_portfolio_value"], target)
                self.assertTrue(all(row["remaining_gap"] >= 0 for row in result["yearly_data"]))

    def test_zero_principal(self):
        result = calculate_goal_plan(120000, 0, 0, 10)
        self.assertEqual(result["required_monthly_contribution"], 1000)
        result = calculate_goal_plan(1000000, 0, 0.08, 10)
        self.assertGreater(result["required_monthly_contribution"], 0)
        self.assert_target(result, 1000000)

    def test_standard_round_trip(self):
        result = calculate_goal_plan(1000000, 100000, 0.08, 10)
        self.assertAlmostEqual(result["required_monthly_contribution"], 4252.816825315485, places=7)
        back = calculate_dca(100000, result["required_monthly_contribution"], 0.08, 10)
        self.assert_target(back, 1000000)
        rows = result["yearly_data"]
        self.assertEqual([r["year"] for r in rows], list(range(11)))
        self.assertEqual(rows[0]["remaining_gap"], 900000)
        self.assertTrue(all(r["remaining_gap"] >= 0 for r in rows))
        self.assertLessEqual(rows[-1]["remaining_gap"], 0.001)

    def test_negative_rate_requires_replacement_of_losses(self):
        result = calculate_goal_plan(10000, 10000, -0.12, 10)
        self.assertGreater(result["required_monthly_contribution"], 0)
        self.assert_target(result, 10000)

    def test_round_trip_varied_rates(self):
        for rate in [-0.99, -0.05, 1e-12, 0.04, 0.12]:
            with self.subTest(rate=rate):
                result = calculate_goal_plan(500000, 1000, rate, 20)
                self.assert_target(calculate_dca(1000, result["required_monthly_contribution"], rate, 20), 500000)

    def test_invalid_inputs(self):
        cases = [(0, 100, 0.08, 10), (-1, 100, 0.08, 10), (10000, -1, 0.08, 10),
                 (10000, 100, -1, 10), (10000, 100, -1.1, 10),
                 (10000, 100, 0.08, 0), (10000, 100, 0.08, -1),
                 (10000, 100, 0.08, 1.5), (10000, 100, 0.08, 1001),
                 (float('inf'), 100, 0.08, 10), (10000, float('nan'), 0.08, 10),
                 (10000, 100, float('nan'), 10), (10000, 100, 0.08, float('inf')),
                 ('abc', 100, 0.08, 10)]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                calculate_goal_plan(*args)

    def test_overflow(self):
        with self.assertRaises(OverflowError):
            calculate_goal_plan(1e308, 1e308, 1, 1000)


if __name__ == '__main__':
    unittest.main()
