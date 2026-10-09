"""Offline research checks, including adversarial future-data perturbations."""
import copy
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from research.evolance_validation import regime_fixture, load_real_prices
from src.evolance import Calibration, classify_state, rolling_analysis, score_snapshot, summarize_timeline
from src.evolance.scoring import normalize
from src.evolance.validation import subsequent_outcomes, find_cases


def evidence(**updates):
    values = dict(cagr=.15, relative_return=.05, trend=.08, volatility=.15, drawdown=.12,
                  negative_frequency=.45, correlation=.40, max_weight=.34, effective_holdings=3,
                  holding_count=3, sharpe=1., return_drawdown=1.25, relative_sharpe=.25)
    values.update(updates)
    return values


def snapshot(g=70, s=70, d=70, e=70, a=70, falling=()):
    return dict(scores=dict(Growth=g, Stability=s, Diversification=d, Efficiency=e, Adaptability=a),
                deteriorating=list(falling))


class EvolanceScoreTests(unittest.TestCase):
    def test_all_piecewise_endpoints_and_clipping(self):
        for points in Calibration().anchors.values():
            for x, y in points:
                self.assertAlmostEqual(normalize(x, points), y)
            self.assertEqual(normalize(-1e9, points), points[0][1])
            self.assertEqual(normalize(1e9, points), points[-1][1])

    def test_all_scores_in_range(self):
        rng = np.random.default_rng(1)
        cfg = Calibration()
        for _ in range(100):
            m = {key: rng.uniform(points[0][0] - 1, points[-1][0] + 1) for key, points in cfg.anchors.items()}
            m['holding_count'] = 3
            prior = score_snapshot(evidence())['scores']
            result = score_snapshot(m, evidence(), prior)
            self.assertTrue(all(v is not None and 0 <= v <= 100 for v in result['scores'].values()))

    def test_sharpe_improves_efficiency(self):
        low = score_snapshot(evidence(sharpe=0))
        high = score_snapshot(evidence(sharpe=1.5))
        self.assertGreater(high['scores']['Efficiency'], low['scores']['Efficiency'])

    def test_benchmark_relative_efficiency_penalty(self):
        self.assertLess(score_snapshot(evidence(relative_sharpe=-.5))['scores']['Efficiency'],
                        score_snapshot(evidence(relative_sharpe=.5))['scores']['Efficiency'])

    def test_drawdown_lowers_stability(self):
        self.assertGreater(score_snapshot(evidence(drawdown=.05))['scores']['Stability'], score_snapshot(evidence(drawdown=.40))['scores']['Stability'])

    def test_correlation_lowers_diversification(self):
        self.assertGreater(score_snapshot(evidence(correlation=.10))['scores']['Diversification'], score_snapshot(evidence(correlation=.90))['scores']['Diversification'])

    def test_concentration_lowers_diversification(self):
        self.assertGreater(score_snapshot(evidence(max_weight=.34, effective_holdings=3))['scores']['Diversification'], score_snapshot(evidence(max_weight=.90, effective_holdings=1.227))['scores']['Diversification'])

    def test_volatility_deterioration_lowers_adaptability(self):
        old = evidence()
        scores = score_snapshot(old)['scores']
        stable = score_snapshot(old, old, scores)['scores']['Adaptability']
        worse = score_snapshot(evidence(volatility=.30), old, scores)['scores']['Adaptability']
        self.assertLess(worse, stable)

    def test_recent_negative_trend_reduces_growth(self):
        self.assertLess(score_snapshot(evidence(trend=-.15))['scores']['Growth'], score_snapshot(evidence(trend=.15))['scores']['Growth'])

    def test_missing_is_not_reweighted(self):
        result = score_snapshot(evidence(sharpe=np.nan))
        self.assertIsNone(result['scores']['Efficiency'])
        self.assertIsNone(result['scores']['Adaptability'])
        self.assertIn('sharpe', result['missing'])
        self.assertEqual(classify_state(result)['state'], 'Insufficient Evidence')

    def test_calibration_validation(self):
        for kw in [dict(lookback=5),dict(frequency='daily'),dict(trend_days=300),dict(risk_free_rate=float('nan'))]:
            with self.assertRaises(ValueError):Calibration(**kw)
        bad = Calibration().anchors
        bad['cagr'] = ((1, 0), (0, 100))
        with self.assertRaises(ValueError):Calibration(anchors=bad)

    def test_score_evidence_not_mutated(self):
        m = evidence(); before=copy.deepcopy(m)
        score_snapshot(m)
        self.assertEqual(m, before)


class EvolanceStateTests(unittest.TestCase):
    def test_all_static_states(self):
        cases = [
            (snapshot(), 'Balanced Growth'),
            (snapshot(g=90, s=60, d=50), 'Growth-Dominant'),
            (snapshot(g=75, s=30), 'Fragile Growth'),
            (snapshot(g=40, d=20), 'Concentration Pressure'),
            (snapshot(g=25, s=90, e=20), 'Defensive Imbalance'),
            (snapshot(g=20, s=20, e=20), 'Inefficient Risk'),
            (snapshot(g=50, s=50, d=50, e=50), 'Mixed / Unclassified'),
        ]
        for case, state in cases:
            with self.subTest(state=state):self.assertEqual(classify_state(case)['state'], state)

    def test_priority_and_determinism(self):
        case = snapshot(g=90,s=20,d=20,e=20,a=10,falling=['Stability','Efficiency'])
        first = classify_state(case)
        self.assertEqual(first['state'], 'Stress State')
        self.assertIn('Fragile Growth', first['matches'])
        self.assertIn('Concentration Pressure', first['matches'])
        for _ in range(10):self.assertEqual(classify_state(case), first)

    def test_stress_requires_multiple_declining_dimensions(self):
        self.assertNotEqual(classify_state(snapshot(g=20,s=20,e=20,a=10,falling=['Stability']))['state'], 'Stress State')

    def test_recovery_requires_previous_stress_and_improvement(self):
        prior = dict(state='Stress State', scores=snapshot(g=20,s=25,e=20,a=10)['scores'])
        now = snapshot(g=45,s=45,e=45,a=60)
        self.assertEqual(classify_state(now,prior)['state'], 'Transitional Recovery')
        self.assertNotEqual(classify_state(now)['state'], 'Transitional Recovery')
        now['scores']['Efficiency']=19
        self.assertNotEqual(classify_state(now,prior)['state'], 'Transitional Recovery')

    def test_initial_adaptability_does_not_invent_stress(self):
        self.assertNotEqual(classify_state(snapshot(g=20,s=20,e=20,a=None,falling=['Growth','Efficiency']))['state'], 'Stress State')


class EvolanceRollingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices,cls.phase=regime_fixture()
        cls.weights=dict(AAPL=.3333,MSFT=.3333,NVDA=.3334)
        cls.timeline=rolling_analysis(cls.prices,cls.weights)

    def test_fixture_deterministic_and_distinct_states(self):
        pd.testing.assert_frame_equal(self.prices,regime_fixture()[0])
        self.assertGreater(self.timeline.state.nunique(),2)

    def test_no_lookahead_future_perturbation(self):
        cutoff=pd.Timestamp('2013-06-30')
        changed=self.prices.copy()
        future=changed.index>cutoff
        changed.loc[future]=changed.loc[future].mul(np.linspace(.5,3,future.sum()),axis=0)
        before=rolling_analysis(self.prices,self.weights,as_of=cutoff)
        altered=rolling_analysis(changed,self.weights,as_of=cutoff)
        pd.testing.assert_frame_equal(before,altered)
        full_altered=rolling_analysis(changed,self.weights)
        pd.testing.assert_frame_equal(before,full_altered.loc[before.index])
        prefix=rolling_analysis(self.prices.loc[:cutoff],self.weights,as_of=cutoff)
        pd.testing.assert_frame_equal(before,prefix)
        pd.testing.assert_frame_equal(before,self.timeline.loc[before.index])

    def test_completed_period_and_window_length(self):
        timeline=rolling_analysis(self.prices,self.weights,as_of='2013-06-15')
        self.assertLess(timeline.index[-1],pd.Timestamp('2013-06-01'))
        for date,row in timeline.iterrows():
            self.assertEqual(len(self.prices.loc[row.window_start:date]),253)
            self.assertLessEqual(date,row.period_end)

    def test_quarterly_and_alternative_lookback(self):
        quarterly=rolling_analysis(self.prices,self.weights,config=Calibration(lookback=126,frequency='quarterly'))
        self.assertTrue(all(d.month in (3,6,9,12) for d in quarterly.period_end))
        self.assertLess(len(quarterly),len(self.timeline))

    def test_insufficient_history(self):
        with self.assertRaisesRegex(ValueError,'Insufficient history'):
            rolling_analysis(self.prices.iloc[:252],self.weights)

    def test_nan_and_invalid_dates(self):
        bad=self.prices.copy();bad.iloc[200,0]=np.nan
        with self.assertRaisesRegex(ValueError,'Missing'):
            rolling_analysis(bad,self.weights)
        with self.assertRaises(ValueError):rolling_analysis(self.prices.iloc[::-1],self.weights)

    def test_zero_variance_undefined_not_perfect_efficiency(self):
        prices=self.prices.iloc[:600].copy();prices.loc[:,:]=100.
        timeline=rolling_analysis(prices,self.weights)
        self.assertTrue(timeline.Efficiency.isna().all())
        self.assertTrue((timeline.state=='Insufficient Evidence').all())

    def test_negative_period_and_stress_risk(self):
        stressed=self.timeline[self.timeline.cagr<0]
        self.assertFalse(stressed.empty)
        self.assertLess(stressed.Growth.mean(),self.timeline[self.timeline.cagr>.20].Growth.mean())
        self.assertTrue(self.timeline.state.isin(['Stress State','Inefficient Risk']).any())

    def test_zero_weight_does_not_add_diversification(self):
        a=rolling_analysis(self.prices,dict(AAPL=1.))
        b=rolling_analysis(self.prices,dict(AAPL=1.,MSFT=0.))
        pd.testing.assert_frame_equal(a,b)
        self.assertTrue(a.correlation.isna().all())
        self.assertTrue((a.Diversification==0).all())

    def test_transitions_durations_and_censoring(self):
        summary=summarize_timeline(self.timeline)
        self.assertEqual(sum(x['observations'] for x in summary['durations']),len(self.timeline))
        self.assertEqual(len(summary['transitions']),len(summary['durations'])-1)
        self.assertTrue(summary['durations'][-1]['right_censored'])
        for event in summary['transitions']:
            self.assertNotEqual(event['old'],event['new'])

    def test_forward_window_excludes_today_and_censors_tail(self):
        outcomes=subsequent_outcomes(self.prices,self.weights,self.timeline)
        date=self.timeline.index[0]
        returns=self.prices[list(self.weights)].pct_change(fill_method=None).dot(list(self.weights.values()))
        expected=(1+returns[returns.index>date].iloc[:63]).prod()-1
        self.assertAlmostEqual(outcomes.loc[date,'forward_return'],expected)
        self.assertFalse(outcomes.iloc[-1].forward_complete)
        self.assertTrue(pd.isna(outcomes.iloc[-1].forward_return))

    def test_case_selection_cannot_select_best_forward_return(self):
        outcomes=subsequent_outcomes(self.prices,self.weights,self.timeline)
        a=find_cases(self.timeline,outcomes)
        altered=outcomes.copy();altered.forward_return=-.90
        b=find_cases(self.timeline,altered)
        self.assertEqual({k:v['date'] if v else None for k,v in a.items()}, {k:v['date'] if v else None for k,v in b.items()})

    def test_recovery_metrics_improve_without_forcing_recovery_label(self):
        phases=self.phase.reindex(self.timeline.index)
        stress=self.timeline.loc[phases=='stress']
        recovery=self.timeline.loc[phases=='recovery']
        self.assertGreater(recovery.iloc[-1].Stability,stress.iloc[-1].Stability)
        self.assertGreater(recovery.iloc[-1].Efficiency,stress.iloc[-1].Efficiency)


class EvolanceCacheTests(unittest.TestCase):
    def test_read_only_yahoo_cache_and_excluded_provider(self):
        prices,_=regime_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir()
            path=root/'data'/'finance_lab.sqlite3'
            # Research loader has an explicit 2016+ requested date range.
            sample=prices.iloc[:600].copy();sample.index=pd.bdate_range('2016-01-01',periods=600)
            with closing(sqlite3.connect(path)) as db:
                db.execute('CREATE TABLE historical_prices (ticker TEXT,date TEXT,adjusted_close REAL,source TEXT)')
                db.executemany('INSERT INTO historical_prices VALUES (?,?,?,?)',
                    [(symbol,date.date().isoformat(),float(value),'yahoo') for symbol in ['AAPL','MSFT','NVDA','SPY'] for date,value in sample[symbol].items()])
                db.commit()
            original=path.read_bytes()
            with patch('research.evolance_validation.ROOT',root):
                actual,source,_=load_real_prices()
                self.assertEqual(source,'real_yahoo_cache')
                self.assertEqual(len(actual),600)
                self.assertEqual(path.read_bytes(),original)
                with closing(sqlite3.connect(path)) as db:
                    db.execute("UPDATE historical_prices SET source='kibot'")
                    db.commit()
                actual,source,_=load_real_prices()
                self.assertIsNone(actual)
                self.assertEqual(source,'unavailable')


if __name__=='__main__':
    unittest.main()
