"""Whole-product offline language and session-state regression checks."""
import re
import unittest
from unittest.mock import patch
import numpy as np
from streamlit.testing.v1 import AppTest
import test_portfolio_ui as portfolio_fixtures
from src.i18n import tr


class GlobalLanguageTests(unittest.TestCase):
    setUp = portfolio_fixtures.PortfolioUITests.setUp

    def app(self):
        return AppTest.from_file(str(portfolio_fixtures.ROOT / 'streamlit_app.py'), default_timeout=30).run()

    def populated(self):
        app = self.app()
        for button in [0, 1, 2]:
            app.button[button].click().run()
        with patch('src.market_data.download_prices', side_effect=TimeoutError()):
            app.button(key='pa_analyze').click().run()
        app.button(key='fo_run').click().run()
        app.button(key='pg_run').click().run()
        self.assertFalse(app.exception)
        return app

    def strings(self, app):
        texts=[]
        for kind in ['title','subheader','caption','markdown','info','warning','error']:
            texts += [str(x.value) for x in app.get(kind)]
        for kind in ['number_input','date_input','text_input','selectbox','button','metric','expander','tab']:
            for x in app.get(kind):
                texts.append(x.label)
                help_text=getattr(x.proto, 'help', '')
                if help_text: texts.append(help_text)
                if kind=='selectbox' and x.key!='global_language':texts.extend(x.options)
        for table in app.dataframe:
            frame=table.value
            texts.extend(map(str,frame.columns))
            for col in frame.columns:texts.extend(map(str,frame[col]))
        return texts

    def test_default_and_single_global_selector(self):
        app=self.app()
        self.assertEqual(app.selectbox(key='global_language').value,'English')
        self.assertNotIn('pa_language',[s.key for s in app.selectbox])
        self.assertEqual(app.selectbox(key='global_language').label,'🌐 Language')
        self.assertEqual([x.label for x in app.tabs],['Compound Interest','DCA Simulator','Goal Planner','Portfolio Analytics'])
        self.assertEqual(app.title[0].value,'Vexa')

    def test_whole_product_language_audit_with_all_results(self):
        app=self.populated()
        for historical_name in ['Finance Mini Lab', 'Program One']:
            self.assertNotIn(historical_name, '\n'.join(self.strings(app)))
        self.assertIn('v0.4.0 · Independent Product', [x.value for x in app.caption])
        self.assertFalse(any(re.search(r'[\u4e00-\u9fff]',text) for text in self.strings(app)))
        app.selectbox(key='global_language').select('中文').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key='global_language').label,'🌐 语言')
        text='\n'.join(self.strings(app))
        for historical_name in ['Finance Mini Lab', 'Program One']:
            self.assertNotIn(historical_name, text)
        self.assertIn('v0.4.0 · 独立开发产品', [x.value for x in app.caption])
        # Proper names and standard numerical/technical labels are allowed.
        for proper in ['Vexa','Evolance','Yahoo Finance','SQLite','ETF','AAPL','MSFT','NVDA','SPY','CAGR','Sharpe','Sortino','N/A','P10','P50','P90']:
            text=text.replace(proper,'')
        self.assertFalse(re.search(r'[A-Za-z]{3,}(?: [A-Za-z]{3,})+',text),text)
        for phrase in ['让投资组合判断，更清晰。','复利计算','定投模拟','目标规划','投资组合分析','从指标到洞察','演示数据']:
            self.assertIn(phrase,'\n'.join(self.strings(app)))

    def test_switch_preserves_inputs_results_profiles_and_module_identity(self):
        app=self.populated()
        app.number_input(key='compound_principal').set_value(12345)
        app.button[0].click().run()
        app.selectbox(key='pg_risk_English').select('Aggressive')
        app.button(key='pg_run').click().run()
        app.session_state['module_tabs']='Goal Planner'
        app.run()
        paths=app.session_state['pa_result']['future_outlook']['simulation']['paths'].copy()
        values=[x.value for x in app.metric]
        with patch('src.market_data.download_prices',side_effect=AssertionError('redownload')), patch('src.future_ui.simulate_monte_carlo',side_effect=AssertionError('resimulation')), patch('src.compound_interest.calculate_future_value',side_effect=AssertionError('recalculation')) as calculate:
            calculate.__name__='calculate_future_value'
            app.selectbox(key='global_language').select('中文').run()
            calculate.assert_not_called()
        self.assertFalse(app.exception)
        self.assertEqual(app.number_input(key='compound_principal').value,12345)
        self.assertEqual(app.text_input(key='pa_tickers').value,'AAPL, MSFT, NVDA')
        self.assertEqual(app.session_state['pg_risk'],'Aggressive')
        self.assertEqual(app.selectbox(key='pg_risk_中文').value,'Aggressive')
        self.assertEqual(app.selectbox(key='pg_risk_中文').options,['稳健型','均衡型','进取型'])
        self.assertEqual(app.session_state['selected_module'],'goal_planner')
        self.assertEqual(app.session_state['module_tabs'],'目标规划')
        numeric_text = lambda value: re.sub(r'[^0-9.,%+-]', '', value)
        self.assertEqual(list(map(numeric_text, values)),
                         [numeric_text(x.value) for x in app.metric])
        np.testing.assert_array_equal(paths,app.session_state['pa_result']['future_outlook']['simulation']['paths'])
        app.selectbox(key='pg_risk_中文').select('Conservative')
        app.selectbox(key='fo_horizon_中文').select(1)
        app.button(key='pg_run').click().run()
        app.selectbox(key='global_language').select('English').run()
        self.assertEqual(app.selectbox(key='pg_risk_English').value, 'Conservative')
        self.assertEqual(app.selectbox(key='fo_horizon_English').value, 1)

    def test_errors_in_each_language(self):
        for language in ['English','中文']:
            app=self.app()
            app.selectbox(key='global_language').select(language).run()
            for key,button in [('compound_principal',0),('dca_contribution',1),('goal_target',2)]:
                app.number_input(key=key).set_value(-1)
                app.button[button].click().run()
            self.assertFalse(app.exception)
            for error in app.error:
                self.assertEqual(bool(re.search(r'[\u4e00-\u9fff]',error.value)),language=='中文')
