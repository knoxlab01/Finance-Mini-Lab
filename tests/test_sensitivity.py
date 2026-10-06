import unittest
from src.sensitivity import calculate_goal_sensitivity
from src.goal_planner import calculate_goal_plan
from src.scenario import calculate_scenarios


class SensitivityTests(unittest.TestCase):
    def test_standard_time(self):
        result = calculate_goal_sensitivity(1e6, 1e5, .08, 10)
        rows = result["time"]
        self.assertEqual([r["years"] for r in rows], [5, 10, 15])
        self.assertGreater(rows[0]["monthly"], rows[1]["monthly"])
        self.assertGreater(rows[1]["monthly"], rows[2]["monthly"])
        self.assertEqual(rows[1]["monthly"], calculate_goal_plan(1e6, 1e5, .08, 10)["required_monthly_contribution"])
        self.assertEqual(rows[1]["difference"], 0)
        for row in rows:
            self.assertAlmostEqual(row["difference"], row["monthly"] - result["base_monthly"])

    def test_standard_return(self):
        rows = calculate_goal_sensitivity(1e6, 1e5, .08, 10)["return"]
        for row, rate in zip(rows, [.05, .08, .11]):
            self.assertAlmostEqual(row["annual_rate"], rate)
        self.assertGreater(rows[0]["monthly"], rows[1]["monthly"])
        self.assertGreater(rows[1]["monthly"], rows[2]["monthly"])
        self.assertEqual(rows[1]["monthly"], calculate_goal_plan(1e6, 1e5, .08, 10)["required_monthly_contribution"])
        self.assertEqual(rows[1]["difference"], 0)

    def test_horizon_boundaries(self):
        for years, expected in [(1, [1, 6]), (3, [1, 3, 8]), (5, [1, 5, 10]), (1000, [995, 1000])]:
            result = calculate_goal_sensitivity(10000, 0, 0, years)
            self.assertEqual([r["years"] for r in result["time"]], expected)
            self.assertTrue(all(0 < r["years"] <= 1000 for r in result["time"]))

    def test_low_return_matches_scenario_policy(self):
        for rate in [-.99, 0]:
            rows = calculate_goal_sensitivity(10000, 0, rate, 2)["return"]
            reference = calculate_scenarios(0, rate, 0)
            self.assertEqual([r["annual_rate"] for r in rows], [r["annual_rate"] for r in reference])
            self.assertTrue(all(r["monthly"] is not None for r in rows))

    def test_zero_and_near_zero(self):
        result = calculate_goal_sensitivity(100, 10000, .08, 10)
        self.assertTrue(all(r["monthly"] == 0 for r in result["time"] + result["return"]))
        result = calculate_goal_sensitivity(10000.000001, 10000, 0, 1)
        self.assertGreater(result["base_monthly"], 0)
        self.assertLess(result["base_monthly"], .01)

    def test_alternate_overflow_isolated(self):
        result = calculate_goal_sensitivity(1e301, 1e300, 0, 1000)
        self.assertIsNotNone(result["return"][1]["monthly"])
        self.assertIsNone(result["return"][2]["monthly"])
        self.assertTrue(result["return"][2]["error"])

    def test_invalid_base(self):
        for args in [(0, 100, .08, 10), (10000, -1, .08, 10), (10000, 0, -1, 10), (10000, 0, .08, 0)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                calculate_goal_sensitivity(*args)
