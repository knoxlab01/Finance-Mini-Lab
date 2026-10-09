"""Frozen-rule checks; synthetic fixtures and all network paths remain offline."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from research.evolance_validation import regime_fixture
from src.evolance.v1_1.spec import SPEC, SPEC_PATH, SPEC_SHA256, CORE, load_spec
from src.evolance.v1_1.metrics import evidence, risk_contributions
from src.evolance.v1_1.scoring import normalize, score_evidence
from src.evolance.v1_1.states import interpret
from src.evolance.v1_1.outlook import forward_distributions, directional_label, relative_outlook, confidence, interpret_outlook
from src.evolance.v1_1.timeline import walk_forward, state_spells
from src.evolance.v1_1.validation import evaluate_outcomes, summarize
from src.evolance.v1_1.data import load_csv
from src.future_simulation import estimate_parameters, simulate_monte_carlo


def scores(g=65,d=65,q=65,e=65,r=80):
    return dict(zip((*CORE,'Structural Resilience'),(g,d,q,e,r)))


def snapshot(s=None,decline=None):
    return dict(scores=s or scores(),decline3=decline or dict.fromkeys(CORE,0.))


def prior(s=None,candidate='Mixed / Neutral',confirmed='Mixed / Neutral',streak=1):
    return dict(scores=s or scores(),candidate_state=candidate,confirmed_state=confirmed,
                candidate_streak=streak,confirmation_initialized=True)


def metrics():
    return dict(absolute_return=.15,active_return=.05,downside_deviation=.10,drawdown=.10,
                risk_breadth_score=80.,diversification_ratio=1.5,sortino=1.,information_ratio=.5)


class FrozenScoreTests(unittest.TestCase):
    def test_spec_hash_and_immutable(self):
        self.assertEqual(hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest(),SPEC_SHA256)
        with self.assertRaises(TypeError):SPEC['anchors']['sortino']=()
        self.assertEqual(SPEC['version'],'1.1-frozen')

    def test_modified_spec_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'spec.json';path.write_bytes(SPEC_PATH.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):load_spec(path)

    def test_all_anchors_and_endpoint_saturation(self):
        for key,points in SPEC['anchors'].items():
            for raw,expected in points:
                with self.subTest(key=key,raw=raw):self.assertAlmostEqual(normalize(raw,key),expected)
            self.assertEqual(normalize(-1e8,key),points[0][1])
            self.assertEqual(normalize(1e8,key),points[-1][1])

    def test_growth_uses_only_two_frozen_components(self):
        m=metrics();m.update(cagr=-.9,trend=-.9,sharpe=-10.)
        self.assertEqual(score_evidence(m)['scores']['Growth Strength'],.6*80+.4*70)
        m.update(cagr=9.,trend=9.,sharpe=100.)
        self.assertEqual(score_evidence(m)['scores']['Growth Strength'],76.)

    def test_downside_and_drawdown_scoring(self):
        m=metrics();m.update(downside_deviation=.15,drawdown=.3)
        self.assertEqual(score_evidence(m)['scores']['Downside Stability'],52.5)
        m.update(volatility=1e6)
        self.assertEqual(score_evidence(m)['scores']['Downside Stability'],52.5)

    def test_efficiency_weights_and_no_sharpe(self):
        m=metrics();m.update(sortino=1.,information_ratio=.5,sharpe=-999)
        self.assertEqual(score_evidence(m)['scores']['Return Efficiency'],70.)

    def test_resilience_improvement_not_penalized(self):
        history=[prior(scores(40,40,40,40)) for _ in range(3)]
        result=score_evidence(metrics(),history)
        self.assertEqual(result['scores']['Structural Resilience'],100.)
        self.assertTrue(all(v==0 for v in result['decline3'].values()))

    def test_resilience_decline_and_three_period_lag(self):
        history=[prior(scores(100,100,100,100)),prior(scores(0,0,0,0)),prior(scores(0,0,0,0))]
        result=score_evidence(metrics(),history)
        self.assertLess(result['scores']['Structural Resilience'],40)
        self.assertIsNone(score_evidence(metrics(),history[:2])['scores']['Structural Resilience'])

    def test_missing_component_is_not_reweighted(self):
        m=metrics();m['information_ratio']=None
        self.assertIsNone(score_evidence(m)['scores']['Return Efficiency'])
        self.assertIsNone(normalize(np.nan,'sortino'))


class EvidenceTests(unittest.TestCase):
    def test_orthogonal_risk_contributors(self):
        x=np.array([[.01,0],[-.01,0],[0,.01],[0,-.01]])
        r=risk_contributions(x,[.5,.5])
        self.assertAlmostEqual(sum(r['signed_rc']),r['portfolio_volatility'])
        self.assertAlmostEqual(r['effective_risk_contributors'],2)
        self.assertAlmostEqual(r['risk_breadth_score'],100)
        self.assertAlmostEqual(r['diversification_ratio'],np.sqrt(2))

    def test_negative_risk_contributions_retained(self):
        x=np.array([.01,-.01,.02,-.02])
        r=risk_contributions(np.column_stack([x,-.5*x]),[.8,.2])
        self.assertLess(r['signed_rc'][1],0)
        self.assertTrue(all(v>=0 for v in r['absolute_rc_shares']))
        self.assertAlmostEqual(sum(r['absolute_rc_shares']),1)

    def test_single_asset_and_zero_risk(self):
        r=risk_contributions(np.array([[.01],[-.01],[.005]]),[1])
        self.assertEqual(r['risk_breadth_score'],0)
        self.assertAlmostEqual(r['diversification_ratio'],1)
        zero=risk_contributions(np.zeros((3,1)),[1])
        self.assertIsNone(zero['signed_rc'])
        self.assertIsNone(zero['diversification_ratio'])

    def test_duplicate_exposure_limitation_kept_frozen(self):
        x=np.array([.01,-.01,.02,-.02])
        risk=risk_contributions(np.column_stack([x,x]),[.5,.5])
        m=metrics();m.update(risk)
        self.assertAlmostEqual(score_evidence(m)['scores']['Diversification Quality'],60.)

    def test_downside_sortino_and_ir_numerically(self):
        p=np.tile([.01,-.008,.002,-.001],63)
        b=np.tile([.006,-.004,.001,-.0005],63)
        prices=pd.DataFrame(np.vstack([np.ones(2),np.cumprod(1+np.column_stack([p,b]),axis=0)])*100,
                            index=pd.bdate_range('2020-01-01',periods=253),columns=['ETF.X','BENCH'])
        m,_=evidence(prices,{'ETF.X':1},'BENCH')
        rf=.04;target=(1+rf)**(1/252)-1
        downside=np.sqrt(np.mean(np.minimum(p-target,0)**2)*252)
        self.assertAlmostEqual(m['downside_deviation'],downside)
        self.assertAlmostEqual(m['sortino'],((1+p).prod()-1-rf)/downside)
        self.assertAlmostEqual(m['information_ratio'],np.mean(p-b)/np.std(p-b,ddof=1)*np.sqrt(252))

    def test_zero_tracking_error_unavailable(self):
        prices,_=regime_fixture()
        m,_=evidence(prices.iloc[:253],{'SPY':1},'SPY')
        self.assertIsNone(m['information_ratio'])
        self.assertIsNone(score_evidence(m)['scores']['Return Efficiency'])


class StructuralRulesTests(unittest.TestCase):
    def test_primary_candidates_and_determinism(self):
        for s,state in [(scores(),'Balanced Growth'),(scores(g=85,d=60,q=40,e=45),'Growth-Led'),
                        (scores(g=30,d=80),'Defensive'),(scores(d=39,e=44),'Stressed'),
                        (scores(g=55,d=50,q=50,e=50),'Mixed / Neutral')]:
            a=interpret(snapshot(s),{'risk_breadth_score':60})
            self.assertEqual(a['candidate_state'],state)
            self.assertEqual(a,interpret(snapshot(s),{'risk_breadth_score':60}))

    def test_flags_coexist(self):
        s=scores(g=75,d=30,q=30,e=30,r=20)
        result=interpret(snapshot(s,dict.fromkeys(CORE,20)),{'risk_breadth_score':20})
        self.assertEqual(set(result['flags']),set(SPEC['flags']))

    def test_growth_and_defensive_do_not_get_masked_by_concentration(self):
        for s,expected in [(scores(g=90,d=60,q=10,e=50),'Growth-Led'),(scores(g=30,d=80,q=0,e=30),'Defensive')]:
            result=interpret(snapshot(s),{'risk_breadth_score':0},[prior(s,candidate=expected)])
            self.assertEqual(result['confirmed_state'],expected)
            self.assertIn('High Risk Concentration',result['flags'])

    def test_normal_hysteresis(self):
        first=interpret(snapshot(),{'risk_breadth_score':60})
        self.assertEqual(first['confirmed_state'],'Mixed / Neutral')
        second=interpret(snapshot(),{'risk_breadth_score':60},[dict(first,scores=scores())])
        self.assertEqual(second['confirmed_state'],'Balanced Growth')
        third=interpret(snapshot(scores(g=30,d=80)),{'risk_breadth_score':60},[dict(second,scores=scores())])
        self.assertEqual(third['confirmed_state'],'Balanced Growth')

    def test_severe_stress_immediate_and_resilience_override(self):
        self.assertEqual(interpret(snapshot(scores(d=29,e=34)),{})['confirmed_state'],'Stressed')
        result=interpret(snapshot(scores(r=29)),{})
        self.assertEqual(result['confirmed_state'],'Stressed')
        self.assertEqual(result['candidate_state'],'Balanced Growth')

    def test_stress_exit_requires_persistence_and_stability_above45(self):
        h=[prior(scores(),candidate='Mixed / Neutral',confirmed='Stressed')]
        at_boundary=interpret(snapshot(scores(g=55,d=45,q=50,e=50)),{},h)
        self.assertEqual(at_boundary['confirmed_state'],'Stressed')
        above=interpret(snapshot(scores(g=55,d=46,q=50,e=50)),{},h)
        self.assertEqual(above['confirmed_state'],'Mixed / Neutral')
        different=interpret(snapshot(scores(g=30,d=80)),{},h)
        self.assertEqual(different['confirmed_state'],'Stressed')

    def test_deteriorating_and_recovering(self):
        decline=dict.fromkeys(CORE,0);decline['Downside Stability']=15
        self.assertEqual(interpret(snapshot(decline=decline),{})['transition'],'Deteriorating')
        history=[prior(scores(40,40,40,40,r=20),confirmed='Stressed'),prior(scores(45,45,45,45))]
        self.assertEqual(interpret(snapshot(scores(50,50,50,50)),{},history)['transition'],'Recovering')
        history=[prior(scores(40,40,40,40)),prior(scores(45,45,45,45))]
        self.assertEqual(interpret(snapshot(scores(50,50,50,50)),{},history)['transition'],'Stable')

    def test_transition_precedence_and_recovery_guardrail(self):
        history=[prior(scores(40,60,40,40,r=20)),prior(scores())]
        result=interpret(snapshot(scores(60,54,60,60)),{},history)
        self.assertNotEqual(result['transition'],'Recovering')
        history[0]=prior(scores(40,40,40,40,r=20))
        decline=dict.fromkeys(CORE,0);decline['Downside Stability']=15
        result=interpret(snapshot(scores(60,60,60,60),decline),{},history)
        self.assertEqual(result['transition'],'Deteriorating')


class ForwardTests(unittest.TestCase):
    def test_existing_engine_equivalence_for_both_horizons(self):
        returns=np.tile([.01,-.008,.003,-.001],63)
        result=forward_distributions(returns)
        old=simulate_monte_carlo(estimate_parameters(returns),100,1,5000,20261007)
        for months in (6,12):
            terminal=old['paths'][months]/100-1
            np.testing.assert_array_equal(result[months]['terminal_returns'],terminal)
            self.assertEqual(result[months]['probability_up'],np.mean(terminal>0))
            self.assertEqual(result[months]['loss_probability'],np.mean(terminal<0))
            self.assertAlmostEqual(sum(result[months][k] for k in ['probability_up','loss_probability','tie_probability']),1)

    def test_direction_probability_boundaries(self):
        for p,m,label in [(.7,.10,'Strong Bullish'),(.6,.10,'Bullish'),(.599,.10,'Neutral / Uncertain'),
                          (.401,-.10,'Neutral / Uncertain'),(.4,-.10,'Bearish'),(.3,-.10,'Strong Bearish')]:
            self.assertEqual(directional_label(p,m,12),label)

    def test_guardrails_and_ties(self):
        for p,m,months in [(.9,-.10,12),(.1,.10,12),(.9,.019,6),(.9,.039,12),(.1,0,6)]:
            self.assertEqual(directional_label(p,m,months),'Neutral / Uncertain')
        self.assertEqual(directional_label(.9,.02,6),'Strong Bullish')
        self.assertEqual(directional_label(.9,.04,12),'Strong Bullish')

    def test_relative_outlook(self):
        for active,ir,label in [(.01,.25,'Likely Outperform'),(-.01,-.25,'Likely Underperform'),(0,1,'In Line / Uncertain'),(.01,None,'In Line / Uncertain')]:
            self.assertEqual(relative_outlook(dict(active_return=active,information_ratio=ir)),label)

    def test_confidence_downgrades_are_independent_and_capped(self):
        state=dict(transition='Deteriorating',flags=[])
        result=confidence('Strong Bullish','Likely Outperform',scores(),state,False)
        self.assertEqual(result['confidence'],'Moderate')
        self.assertEqual(result['relative_confidence'],'Moderate')
        state['flags']=['High Risk Concentration']
        result=confidence('Strong Bullish','Likely Outperform',scores(r=20),state,False)
        self.assertEqual(result['confidence'],'Low')
        self.assertEqual(len(result['confidence_reasons']),3)

    def test_synthetic_confidence_cap_and_neutral_low(self):
        state=dict(transition='Stable',flags=[])
        self.assertEqual(confidence('Strong Bullish','Likely Outperform',scores(),state,True)['confidence'],'Moderate')
        self.assertEqual(confidence('Neutral / Uncertain','In Line / Uncertain',scores(),state,False)['confidence'],'Low')

    def test_state_never_changes_quantitative_direction(self):
        distribution=dict(months=12,p10=-.2,p50=.1,p90=.5,probability_up=.65,loss_probability=.35)
        metric=dict(active_return=.05,information_ratio=.5)
        a=interpret_outlook(distribution,metric,scores(),dict(confirmed_state='Balanced Growth',transition='Stable',flags=[]),True)
        b=interpret_outlook(distribution,metric,scores(r=20),dict(confirmed_state='Stressed',transition='Deteriorating',flags=['High Risk Concentration']),True)
        self.assertEqual(a['direction'],b['direction'])
        self.assertNotEqual(a['confidence'],b['confidence'])
        self.assertIn('Based on synthetic/demo data.',a['explanation']['en'])


class WalkForwardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prices=regime_fixture()[0].iloc[:850]
        cls.weights={'AAPL':.3333,'MSFT':.3333,'NVDA':.3334}
        cls.result=walk_forward(cls.prices,cls.weights)

    def test_both_horizons_have_no_lookahead(self):
        cutoff=pd.Timestamp('2012-01-31')
        changed=self.prices.copy()
        mask=changed.index>cutoff
        changed.loc[mask]=changed.loc[mask].mul(np.linspace(.5,2,mask.sum()),axis=0)
        original=[r for r in self.result['rows'] if pd.Timestamp(r['available_at'])<=cutoff]
        altered=walk_forward(changed,self.weights)
        past=[r for r in altered['rows'] if pd.Timestamp(r['available_at'])<=cutoff]
        self.assertEqual(original,past)
        prefix=walk_forward(self.prices.loc[:cutoff],self.weights,as_of=cutoff)
        self.assertEqual(original,prefix['rows'])
        for row in original:self.assertEqual(set(row['outlooks']),{'6','12'})

    def test_incomplete_forward_windows_censored(self):
        outcome=evaluate_outcomes(self.prices,self.weights,self.result['rows'])
        for months in (6,12):
            rows=[r for r in outcome if r['months']==months]
            self.assertTrue(rows[0]['complete'])
            self.assertFalse(rows[-1]['complete'])
            self.assertIsNone(rows[-1]['forward_return'])
            self.assertIsNone(rows[-1]['forward_drawdown'])
        stats=summarize(outcome)
        for months in ('6','12'):
            self.assertEqual(stats[months]['evolance'],stats[months]['mc_only'])
            self.assertEqual(stats[months]['by_confidence']['High']['signals'],0)

    def test_completed_months_and_warmup(self):
        for i,row in enumerate(self.result['rows']):
            self.assertEqual(len(self.prices.loc[row['window_start']:row['date']]),253)
            self.assertLessEqual(pd.Timestamp(row['date']),pd.Timestamp(row['available_at']))
            if i<3:self.assertIsNone(row['scores']['Structural Resilience'])
        self.assertTrue(state_spells(self.result['rows'])[-1]['right_censored'])

    def test_invalid_history_and_nan(self):
        with self.assertRaisesRegex(ValueError,'Insufficient'):walk_forward(self.prices.iloc[:252],self.weights)
        bad=self.prices.copy();bad.iloc[100,0]=np.nan
        with self.assertRaisesRegex(ValueError,'NaN'):walk_forward(bad,self.weights)

    def test_generic_single_fund_ticker(self):
        frame=self.prices.rename(columns={'AAPL':'FUND.X','SPY':'INDEX-1'})
        result=walk_forward(frame,{'FUND.X':1},benchmark='INDEX-1')
        for row in result['rows']:
            self.assertEqual(row['scores']['Diversification Quality'],0)
            self.assertIn('High Risk Concentration',row['flags'])

    def test_forward_outcomes_cannot_change_signals(self):
        before=copy.deepcopy(self.result['rows'])
        outcomes=evaluate_outcomes(self.prices,self.weights,self.result['rows'])
        for r in outcomes:r['forward_return']=-.99
        summarize(outcomes)
        self.assertEqual(before,self.result['rows'])


class LocalCsvTests(unittest.TestCase):
    def test_declared_csv_and_duplicate_header_validation(self):
        prices=regime_fixture()[0].iloc[:300];prices.index.name='Date'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'history.csv';prices.to_csv(p)
            frame,meta=load_csv(p,kind='synthetic',source='test fixture',price_type='close')
            self.assertEqual(len(frame),300)
            self.assertEqual(meta['kind'],'synthetic')
            p.write_text('Date,AAPL,AAPL\n2020-01-01,1,1\n',encoding='utf-8')
            with self.assertRaises(ValueError):load_csv(p,kind='real',source='declared',price_type='adjusted')


if __name__=='__main__':
    unittest.main()
