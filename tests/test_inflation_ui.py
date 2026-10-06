import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.compound_interest import calculate_future_value
from src.dca import calculate_dca


class InflationUITests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "streamlit_app.py"), default_timeout=15).run()

    def test_standard_modules(self):
        for button, key, nominal in [(0, "compound_inflation", calculate_future_value(10000, .08, 10)), (1, "dca_inflation", calculate_dca(10000, 1000, .08, 10)["final_portfolio_value"])]:
            with self.subTest(key=key):
                app = self.app()
                self.assertEqual(app.number_input(key=key).value, 2.0)
                app.button[button].click().run()
                self.assertFalse(app.exception)
                self.assertFalse(app.error)
                metrics = {m.label: m.value for m in app.metric}
                self.assertEqual(metrics["Nominal Future Value / 名义未来价值"], f"¥{nominal:,.2f}")
                self.assertEqual(metrics["Real Future Value / 实际购买力"], f"¥{nominal / 1.02 ** 10:,.2f}")
                self.assertEqual(metrics["Purchasing Power Loss / 购买力损失"], f"¥{nominal - nominal / 1.02 ** 10:,.2f}")
                self.assertTrue(any("不代表未来实际通胀预测" in c.value for c in app.caption))

    def test_validation_and_recovery(self):
        for button, key in [(0, "compound_inflation"), (1, "dca_inflation")]:
            app = self.app()
            for rate in [-100.0, -101.0]:
                app.number_input(key=key).set_value(rate)
                app.button[button].click().run()
                self.assertFalse(app.exception)
                self.assertIn("通胀率必须大于 -100%", app.error[0].value)
            app.number_input(key=key).set_value(0.0)
            app.button[button].click().run()
            self.assertFalse(app.error)
            metrics = {m.label: m.value for m in app.metric}
            self.assertEqual(metrics["Real Future Value / 实际购买力"], metrics["Nominal Future Value / 名义未来价值"])

    def test_extreme_inflation_preserves_nominal(self):
        for button, key in [(0, "compound_inflation"), (1, "dca_inflation")]:
            app = self.app()
            app.number_input(key=key).set_value(1e100)
            app.button[button].click().run()
            self.assertFalse(app.exception)
            self.assertIn("通胀调整结果超出支持范围", app.error[0].value)
            self.assertIn("Future Value / 未来价值", [m.label for m in app.metric])

    def test_goal_unchanged(self):
        app = self.app()
        app.button[2].click().run()
        self.assertFalse(app.exception)
        self.assertNotIn("Real Future Value / 实际购买力", [m.label for m in app.metric])
