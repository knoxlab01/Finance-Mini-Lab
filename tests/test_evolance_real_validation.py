"""Offline tests with synthetic inputs only; never read private market prices."""
import copy
import unittest
import numpy as np
import pandas as pd
from research.evolance_v1_1_real_validation import (hit,stats,group_tables,failure_cases,interpretation_cases,derived_timeline)
from src.evolance.v1_1.timeline import walk_forward
from src.evolance.v1_1.validation import evaluate_outcomes,traditional_direction


def record(**overrides):
    row=dict(date='2015-01-30',months=6,complete=True,direction='Bullish',confidence='High',
             mc_only_direction='Bullish',traditional_direction='Bullish',state='Growth-Led',
             transition='Stable',flags=[],forward_return=.1,forward_drawdown=-.1,probability_up=.7,portfolio='equal_weight')
    row.update(overrides)
    return row


class RealStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dates=pd.bdate_range('2010-01-01',periods=800)
        rng=np.random.default_rng(427)
        cls.prices=pd.DataFrame(100*np.exp(np.cumsum(rng.normal(.0003,.012,(800,2)),axis=0)),index=dates,columns=['AAPL','SPY'])
        cls.weights={'AAPL':1.}
        cls.signals=walk_forward(cls.prices,cls.weights,synthetic=False)['rows']

    def test_no_lookahead_future_perturbation_and_same_date(self):
        cutoff=pd.Timestamp(self.signals[5]['available_at'])
        changed=self.prices.copy()
        changed.loc[changed.index>cutoff,'AAPL']*=3
        original=walk_forward(self.prices,self.weights,synthetic=False,as_of=cutoff)['rows']
        perturbed=walk_forward(changed,self.weights,synthetic=False,as_of=cutoff)['rows']
        self.assertEqual(original,perturbed)
        self.assertEqual(original,self.signals[:6])
        for s in original:
            self.assertLessEqual(pd.Timestamp(s['date']),pd.Timestamp(s['available_at']))
            self.assertEqual(traditional_direction(s['metrics']),evaluate_outcomes(self.prices,self.weights,[s])[0]['traditional_direction'])

    def test_exact_forward_windows_and_terminal_censoring(self):
        rows=evaluate_outcomes(self.prices,self.weights,[self.signals[0],self.signals[-1]])
        returns=self.prices.AAPL.pct_change().dropna()
        for r in rows[:2]:
            horizon={6:126,12:252}[r['months']]
            future=returns.loc[returns.index>pd.Timestamp(self.signals[0]['available_at'])].iloc[:horizon]
            self.assertEqual(r['observations'],horizon)
            self.assertAlmostEqual(r['forward_return'],float((1+future).prod()-1))
            curve=np.r_[1.,(1+future).cumprod().to_numpy()]
            self.assertAlmostEqual(r['forward_drawdown'],float((curve/np.maximum.accumulate(curve)-1).min()))
        for r in rows[2:]:
            self.assertFalse(r['complete']);self.assertIsNone(r['forward_return']);self.assertIsNone(r['forward_drawdown'])

    def test_hits_neutral_zero_and_censoring(self):
        self.assertTrue(hit('Strong Bullish',.1));self.assertTrue(hit('Bearish',-.1))
        self.assertFalse(hit('Bullish',0));self.assertIsNone(hit('Neutral / Uncertain',.1))
        rows=[record(),record(direction='Bearish',forward_return=.2),record(direction='Neutral / Uncertain'),record(complete=False,forward_return=None)]
        result=stats(rows)
        self.assertEqual(result['directional_n'],2);self.assertEqual(result['hit_rate'],.5)
        self.assertEqual(result['complete'],3);self.assertEqual(result['censored'],1)

    def test_confidence_state_transition_flag_groups(self):
        rows=[record(),record(confidence='Low',state='Stressed',transition='Deteriorating',flags=['Unsupported Growth'],forward_return=-.2),record(confidence='Low',direction='Neutral / Uncertain')]
        t=group_tables(rows)
        def get(name,**keys):return next(r for r in t[name] if r['portfolio']=='ALL' and r['months']==6 and all(r[k]==v for k,v in keys.items()))
        self.assertEqual(get('confidence_calibration',confidence='Low')['complete'],1)
        self.assertEqual(get('state_outcomes',group='Stressed')['mean_return'],-.2)
        self.assertEqual(get('transition_outcomes',group='Deteriorating')['complete'],1)
        self.assertEqual(get('flag_outcomes',flag='Unsupported Growth',active=True)['complete'],1)
        self.assertEqual(get('state_outcomes',group='Defensive')['complete'],0)
        self.assertIsNone(get('state_outcomes',group='Defensive')['mean_return'])

    def test_failure_audit_keeps_unfavorable_cases(self):
        rows=[record(forward_return=-.3,forward_drawdown=-.4),record(transition='Recovering',forward_return=-.1),record(transition='Deteriorating',forward_drawdown=-.01)]
        kinds={r['kind'] for r in failure_cases(rows)}
        self.assertTrue({'bullish_loss','high_confidence_failure','recovering_loss','false_alarm_proxy','missed_deterioration_proxy'}.issubset(kinds))

    def test_pair_audit_includes_useful_redundant_misleading(self):
        for dd,expected in [(-.3,'useful'),(-.11,'redundant'),(-.01,'misleading')]:
            rows=[record(),record(portfolio='concentrated',flags=['High Risk Concentration'],forward_drawdown=dd)]
            self.assertEqual(interpretation_cases(rows)[0]['category'],expected)

    def test_export_allowlist_blocks_raw_data_and_private_metadata(self):
        signals=copy.deepcopy(self.signals[:1])
        signals[0]['raw_prices']='PRIVATE_MARKER';signals[0]['metrics']['Close']='PRIVATE_MARKER'
        outcomes=evaluate_outcomes(self.prices,self.weights,signals)
        outcomes[0]['raw_prices']='PRIVATE_MARKER'
        exported=derived_timeline(signals,outcomes,'aapl')
        self.assertNotIn('PRIVATE_MARKER',str(exported))
        self.assertFalse({'Open','High','Low','Close','Volume','raw_prices'} & set(exported[0]))

    def test_mc_and_evolance_same_date_distribution(self):
        outcomes=evaluate_outcomes(self.prices,self.weights,self.signals)
        exported=derived_timeline(self.signals,outcomes,'aapl')
        for row in exported:
            self.assertEqual(row['direction'],row['mc_only_direction'])
            signal=next(s for s in self.signals if s['date']==row['date'])
            self.assertEqual(row['probability_up'],signal['outlooks'][str(row['months'])]['probability_up'])

if __name__=='__main__':unittest.main()
