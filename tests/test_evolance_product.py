"""Offline product mapping/UI tests; synthetic inputs only."""
import copy
import hashlib
import subprocess
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
from src.evolance_product import build_comparison,comparison_for,conclusion,latest_outlooks
from src.evolance.v1_1.timeline import walk_forward
from src.benchmark import analyze_portfolio
from src.i18n import CATALOG,tr
from src.future_simulation import estimate_parameters,simulate_monte_carlo
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def fixture(n=650):
    rng=np.random.default_rng(42)
    prices=pd.DataFrame(100*np.exp(np.cumsum(rng.normal(.0005,.01,(n,3)),axis=0)),index=pd.bdate_range('2021-01-01',periods=n),columns=['AAPL','MSFT','SPY'])
    cfg=dict(tickers=['AAPL','MSFT'],weights=[.5,.5],benchmark='SPY',risk_free_rate=.04)
    h=analyze_portfolio(prices,cfg['tickers'],cfg['weights'])
    h.update(evolance_prices=prices,portfolio_config=cfg,source_metadata={'AAPL':{'provider':'demo'}})
    return prices,cfg,h


class ProductTests(unittest.TestCase):
    def test_frozen_tree_and_spec_unchanged(self):
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only','97bf730','src/evolance/v1_1','docs/evolance_v1_1_frozen_spec.json'],cwd=ROOT,text=True).splitlines()
        for p in paths:self.assertEqual((ROOT/p).read_bytes(),subprocess.check_output(['git','show','97bf730:'+p],cwd=ROOT))

    def test_matches_frozen_latest_real_and_demo(self):
        p,c,_=fixture()
        for demo in [False,True]:
            result=build_comparison(p,c,demo)['latest'];reference=walk_forward(p,dict(zip(c['tickers'],c['weights'])),synthetic=demo)['rows'][-1]
            for key in ['scores','confirmed_state','candidate_state','flags','transition','metrics']:
                self.assertEqual(result[key],reference[key])
            for m in ['6','12']:
                for key in ['direction','confidence']:self.assertEqual(result['outlooks'][m][key],reference['outlooks'][m][key])
                if demo:self.assertNotEqual(result['outlooks'][m]['confidence'],'High')

    def test_insufficient_and_quality(self):
        p,c,h=fixture(100)
        self.assertEqual(build_comparison(p,c)['status'],'insufficient')
        p,c,h=fixture();p.iloc[30,0]=np.nan
        self.assertEqual(build_comparison(p,c)['status'],'quality')

    def test_snapshot_window_matches_evidence(self):
        from src.evolance.v1_1.metrics import evidence
        p,c,h=fixture();row=build_comparison(p,c)['latest']
        window=p.loc[row['window_start']:row['date']]
        self.assertEqual(len(window),253)
        metrics,_=evidence(window,dict(zip(c['tickers'],c['weights'])),c['benchmark'])
        self.assertEqual(row['metrics'],metrics)
        self.assertNotAlmostEqual(metrics['absolute_return'],h['metrics'].loc['Cumulative Return','Portfolio'])

    def test_cached_no_redownload_or_duplicate_simulation(self):
        p,c,h=fixture();comparison_for(h)
        with patch('src.evolance_product.build_comparison',side_effect=AssertionError('duplicate')):
            comparison_for(h);conclusion(h['_evolance_result']['latest'],'中文')

    def test_reuse_exact_simulation_and_reject_mismatch(self):
        p,c,h=fixture();returns=h['portfolio_returns'].iloc[-252:]
        params=estimate_parameters(returns);existing=dict(parameters=params,simulation=simulate_monte_carlo(params,100,1,5000,20261007))
        with patch('src.evolance_product.forward_distributions',side_effect=AssertionError('duplicate')):self.assertIn(12,latest_outlooks(returns,existing))
        existing['simulation']['horizon']=5
        with patch('src.evolance_product.forward_distributions',return_value={}) as call:latest_outlooks(returns,existing);call.assert_called_once()

    def test_translations_and_conclusion_flags(self):
        p,c,h=fixture();row=build_comparison(p,c)['latest']
        for flags in [[],['High Risk Concentration','Unsupported Growth']]:
            row['flags']=flags
            for lang in ['English','中文']:
                text=conclusion(row,lang)
                self.assertIn(tr('ev_'+row['outlooks']['12']['direction'],lang),text)
                if not flags:self.assertIn(tr('ev_no_flags',lang),text)
                for f in flags:self.assertIn(tr('ev_'+f,lang),text)
        for key,pair in CATALOG.items():
            if key.startswith('ev_'):
                self.assertNotRegex(pair[0],r'[\u4e00-\u9fff]')
                self.assertRegex(pair[1],r'[\u4e00-\u9fff]')


class ComparisonUITests(unittest.TestCase):
    def app(self,h,language):
        app=AppTest.from_string("from src.evolance_ui import render_evolance_comparison\nimport streamlit as st\nrender_evolance_comparison(st.session_state['history'],st.session_state['lang'])",default_timeout=30)
        app.session_state['history']=h;app.session_state['lang']=language
        return app.run()

    def test_english_chinese_demo_and_details(self):
        for lang in ['English','中文']:
            _,_,h=fixture();app=self.app(h,lang)
            self.assertFalse(app.exception)
            text=' '.join(str(x.value) for kind in ['markdown','caption','info','subheader'] for x in app.get(kind))
            self.assertIn(tr('ev_demo',lang),text);self.assertIn(tr('ev_research_text',lang),text)
            self.assertIn(tr('ev_12m',lang),text);self.assertIn(tr('ev_6m',lang),text)
            self.assertIn(tr('ev_disclaimer',lang),text)
            if lang=='English':self.assertNotRegex(text,r'[\u4e00-\u9fff]')
            else:
                for word in ['Strong Bullish','Stable','Confidence','Traditional Analytics']:self.assertNotIn(word,text)
            self.assertTrue(all(not e.proto.expanded for e in app.expander))

    def test_insufficient_keeps_traditional(self):
        _,_,h=fixture(20);app=self.app(h,'English')
        self.assertFalse(app.exception)
        self.assertIn(tr('ev_insufficient'),[x.value for x in app.caption])
        self.assertTrue(any('Total Return' in x.value for x in app.markdown))

    def test_real_mode_no_demo_notice(self):
        _,_,h=fixture();h['source_metadata']={'AAPL':{'provider':'yahoo','retrieval':'cache'}}
        app=self.app(h,'English');self.assertFalse(app.exception)
        self.assertNotIn(tr('ev_demo'),[x.value for x in app.info])

    def test_positioning_and_percentage_point_units_in_both_languages(self):
        for language in ['English','中文']:
            _,_,h=fixture();app=self.app(h,language)
            self.assertFalse(app.exception)
            self.assertIn(tr('ev_intro_title',language),[x.value for x in app.subheader])
            text=' '.join(x.value for x in app.markdown)
            for key in ['intro_subtitle','intro_text','intro_meaning']:
                self.assertIn(tr('ev_'+key,language),text)
            self.assertIn(tr('ev_intro_side_by_side',language),[x.value for x in app.caption])
            relative=h['_evolance_result']['latest']['metrics']['active_return']
            expected=tr('ev_relative',language,value=f'{relative * 100:+.2f}')
            element=next(x for x in app.markdown if x.value==expected)
            self.assertEqual(element.proto.help,tr('ev_relative_help',language))
            self.assertNotIn('%',element.value)

    def test_shared_snapshot_compact_takeaway_and_disclosures(self):
        _,_,h=fixture();app=self.app(h,'English')
        row=h['_evolance_result']['latest']
        text=' '.join(x.value for x in app.markdown)
        self.assertIn(f"{row['metrics']['absolute_return']:.2%}",text)
        self.assertIn(f"{row['metrics']['cagr']:.2%}",text)
        self.assertIn(tr('ev_takeaway'),text)
        self.assertIn(tr('ev_snapshot_title'),[x.value for x in app.caption])
        self.assertIn(row['window_start'],' '.join(x.value for x in app.caption))
        self.assertEqual([e.label for e in app.expander],[tr('ev_detail'),tr('ev_method_validation')])
        # Five compact evidence rows expose help without five explanatory paragraphs.
        for dimension in row['scores']:
            element=next(x for x in app.markdown if x.value.startswith('**'+tr('ev_'+dimension)+':**'))
            self.assertEqual(element.proto.help,tr('ev_'+dimension+'_help'))
            self.assertNotIn(tr('ev_'+dimension+'_help'),[x.value for x in app.caption])

    def test_page_render_order_preserves_surrounding_sections(self):
        from src.portfolio_ui import render_portfolio_analytics
        calls=[]
        _,_,h=fixture()
        with patch('src.portfolio_ui.render_future_outlook',side_effect=lambda *a:calls.append('future')), patch('src.portfolio_ui.render_evolance_comparison',side_effect=lambda *a:calls.append('comparison')), patch('src.portfolio_ui.render_portfolio_guidance',side_effect=lambda *a:calls.append('guidance')):
            app=AppTest.from_string("from src.portfolio_ui import render_portfolio_analytics\nrender_portfolio_analytics()",default_timeout=30)
            app.session_state['pa_result']=h
            app.run()
        self.assertFalse(app.exception)
        self.assertEqual(calls,['future','comparison','guidance'])
