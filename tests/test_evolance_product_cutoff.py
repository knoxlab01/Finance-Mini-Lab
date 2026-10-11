"""Selected calendar cutoff regressions; no live data or frozen-rule changes."""
import unittest

import numpy as np
import pandas as pd

from src.evolance_product import build_comparison, comparison_for
from src.evolance.v1_1.timeline import walk_forward
from src.market_data import demo_prices
from src.portfolio_analysis import parse_config


class ProductCutoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        index = pd.bdate_range('2024-01-01', '2026-06-30')
        rng = np.random.default_rng(91)
        cls.prices = pd.DataFrame(
            100 * np.exp(np.cumsum(rng.normal(.0003, .01, (len(index), 3)), axis=0)),
            index=index, columns=['AAPL', 'MSFT', 'SPY'])

    def config(self, end):
        return parse_config('AAPL,MSFT', '50,50', '2024-01-01', end)

    def latest(self, end, prices=None):
        result = build_comparison(self.prices if prices is None else prices,
                                  self.config(end), synthetic=True)
        self.assertEqual(result['status'], 'ready')
        return result['latest']

    def test_weekend_month_end_matches_frozen_explicit_as_of(self):
        prices = self.prices.loc[:'2026-05-31']
        self.assertEqual(prices.index[-1], pd.Timestamp('2026-05-29'))
        row = self.latest('2026-05-31', prices)
        self.assertEqual(row['date'], '2026-05-29')
        self.assertEqual(row['available_at'], '2026-05-31')
        reference = walk_forward(prices, {'AAPL': .5, 'MSFT': .5}, 'SPY',
                                 synthetic=True, as_of='2026-05-31')['rows'][-1]
        for key in ['metrics', 'scores', 'confirmed_state', 'flags', 'transition']:
            self.assertEqual(row[key], reference[key])
        for horizon in ['6', '12']:
            for key in ['direction', 'confidence']:
                self.assertEqual(row['outlooks'][horizon][key], reference['outlooks'][horizon][key])

    def test_following_month_first_trading_day(self):
        row = self.latest('2026-06-01', self.prices.loc[:'2026-06-01'])
        self.assertEqual(row['date'], '2026-05-29')
        self.assertEqual(row['available_at'], '2026-05-31')

    def test_mid_month_does_not_complete_current_month(self):
        self.assertEqual(self.latest('2026-05-15')['date'], '2026-04-30')

    def test_non_trading_holiday_fixture_month_end(self):
        # Simulate a month-end closure, without claiming an actual exchange holiday.
        prices = self.prices.loc[:'2026-04-30'].drop(pd.Timestamp('2026-04-30'))
        row = self.latest('2026-04-30', prices)
        self.assertEqual(row['date'], '2026-04-29')
        self.assertEqual(row['available_at'], '2026-04-30')

    def test_normal_trading_day_month_end(self):
        row = self.latest('2026-04-30', self.prices.loc[:'2026-04-30'])
        self.assertEqual(row['date'], '2026-04-30')

    def test_prices_beyond_selected_end_cannot_change_result(self):
        expected = build_comparison(self.prices.loc[:'2026-05-31'],
                                    self.config('2026-05-31'), synthetic=True)
        changed = self.prices.copy()
        changed.loc[changed.index > '2026-05-31'] = np.nan
        actual = build_comparison(changed, self.config('2026-05-31'), synthetic=True)
        self.assertEqual(actual, expected)
        self.assertLessEqual(actual['latest']['date'], '2026-05-31')

    def test_cutoff_leaves_insufficient_history(self):
        result = build_comparison(self.prices, self.config('2024-06-30'), synthetic=True)
        self.assertEqual(result['status'], 'insufficient')

    def test_demo_baseline_and_end_date_audit(self):
        expected = {'2026-10-11': '2026-09-30',
                    '2026-05-31': '2026-05-29',
                    '2026-06-01': '2026-05-29'}
        for end, date in expected.items():
            with self.subTest(end=end):
                config = parse_config('AAPL,MSFT,NVDA', '40,30,30', '2021-01-01', end)
                prices = pd.concat([demo_prices(ticker, config['start_date'], end)
                                    .rename(ticker) for ticker in ['AAPL', 'MSFT', 'NVDA', 'SPY']], axis=1)
                row = build_comparison(prices, config, synthetic=True)['latest']
                self.assertEqual(row['date'], date)
                self.assertEqual(len(prices.loc[row['window_start']:row['date']]), 253)

    def test_end_date_changes_invalidate_product_cache(self):
        historical = dict(evolance_prices=self.prices, portfolio_config=self.config('2026-05-15'))
        self.assertEqual(comparison_for(historical)['latest']['date'], '2026-04-30')
        old_key = historical['_evolance_key']
        historical['portfolio_config'] = self.config('2026-05-31')
        self.assertEqual(comparison_for(historical)['latest']['date'], '2026-05-29')
        self.assertNotEqual(historical['_evolance_key'], old_key)

    def test_invalid_selected_cutoff_is_unavailable(self):
        for value in ['not-a-date', None, '2026-05-31T00:00:00+00:00']:
            with self.subTest(value=value):
                config = self.config('2026-05-31')
                config['end_date'] = value
                self.assertEqual(build_comparison(self.prices, config)['status'], 'quality')


if __name__ == '__main__':
    unittest.main()
