"""Chinese presentation polish: protect English copy and all internal codes."""
import hashlib
import itertools
import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
import test_portfolio_ui as portfolio_fixtures
from src.evolance_product import conclusion
from src.i18n import CATALOG, tr


APPROVED_ENGLISH_DIGEST = '4dab84501e7588d510b2081f9b209476a80f0ea2877cb55a926db6c556dee193'
APPROVED_VERSION_FIELDS = {
    'development': ' · Historical performance does not guarantee future results.',
    'app_development': ' · Developed in Finance Mini Lab · Program One',
}


def protected_english_digest(catalog):
    existing = {key: pair[0] for key, pair in catalog.items()
                if not key.startswith('ev_copy_') and key != 'copy_separator'}
    # Normalize only the exact approved release values, including their suffixes.
    # Unknown versions and any wording drift still change the original checksum.
    for key, suffix in APPROVED_VERSION_FIELDS.items():
        if existing.get(key) == 'v0.4.0' + suffix:
            existing[key] = 'v0.4 development' + suffix
    return hashlib.sha256(json.dumps(existing, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class ChineseLocalizationTests(unittest.TestCase):
    setUp = portfolio_fixtures.PortfolioUITests.setUp

    def test_approved_english_catalog_is_unchanged(self):
        self.assertEqual(protected_english_digest(CATALOG), APPROVED_ENGLISH_DIGEST)

    def test_english_guard_accepts_only_approved_version_values(self):
        historical = deepcopy(CATALOG)
        for key, suffix in APPROVED_VERSION_FIELDS.items():
            historical[key][0] = 'v0.4 development' + suffix
        self.assertEqual(protected_english_digest(historical), APPROVED_ENGLISH_DIGEST)
        for key, suffix in APPROVED_VERSION_FIELDS.items():
            historical[key][0] = 'v0.4.0' + suffix
            self.assertEqual(protected_english_digest(historical), APPROVED_ENGLISH_DIGEST)

    def test_english_guard_rejects_unapproved_versions_and_wording(self):
        mutations = [
            ('development', 'v0.4.1' + APPROVED_VERSION_FIELDS['development']),
            ('app_development', 'v0.5.0' + APPROVED_VERSION_FIELDS['app_development']),
            ('development', CATALOG['development'][0] + ' Changed wording.'),
            ('app_development', CATALOG['app_development'][0].replace('Program One', 'Program Two')),
            ('app_tagline', CATALOG['app_tagline'][0] + ' Changed wording.'),
        ]
        for key, value in mutations:
            changed = deepcopy(CATALOG)
            changed[key][0] = value
            self.assertNotEqual(protected_english_digest(changed), APPROVED_ENGLISH_DIGEST)

    def test_key_chinese_copy_and_terminology(self):
        expected = {'app_tagline': '让投资组合判断，更清晰。',
                    'ev_intro_title': '从指标到洞察',
                    'ev_intro_subtitle': 'Evolance 结构化解读',
                    'ev_state': '当前状态', 'ev_transition': '变化趋势',
                    'ev_flags': '结构提示', 'ev_how_it_works': '分析方法',
                    'ev_historical_evidence': '历史验证',
                    'Scenario Projection': '情景预测', 'Capital Preservation': '资产保值',
                    'legacy:Total Return / 总收益率': '累计收益率'}
        for key, value in expected.items():
            self.assertEqual(tr(key, '中文'), value)
        self.assertIn('可重复生成的模拟数据', tr('demo_combined', '中文'))
        self.assertEqual(tr('ev_intro_text', '中文').split('\n\n'), [
            '同一组指标，换一个视角理解组合。',
            '传统分析可以告诉你收益、风险和模拟结果，但这些数字放在一起意味着什么，往往还需要进一步判断。',
            'Vexa 通过 Evolance 把分散的金融信号整理到一起，从组合当前状态、结构压力、变化趋势和未来方向等角度，提供一套更完整的结构化解读。'])
        self.assertEqual(tr('ev_intro_meaning', '中文'),
                         '传统分析告诉你‘数字是什么’，Evolance 进一步帮助解释‘这些数字放在一起意味着什么’。')
        self.assertEqual(tr('ev_intro_side_by_side', '中文'),
                         '两种视角并列呈现：既保留传统金融指标，也提供 Vexa 特有的结构化解读。')
        self.assertIn('模型固定的 4% 年化无风险利率',
                      tr('ev_snapshot_period', '中文', start='2025-01-01', date='2025-12-31'))

    def test_dynamic_takeaways_preserve_codes_and_english(self):
        combinations = itertools.product(
            ['Balanced Growth', 'Growth-Led', 'Defensive', 'Stressed', 'Mixed / Neutral'],
            ['Stable', 'Deteriorating', 'Recovering'],
            ['Strong Bullish', 'Bullish', 'Neutral / Uncertain', 'Bearish', 'Strong Bearish'],
            ['High', 'Moderate', 'Low'],
            [[], ['Low Return Efficiency'], ['High Risk Concentration', 'Weak Downside Stability']])
        for state, transition, direction, confidence, flags in combinations:
            row = {'confirmed_state': state, 'transition': transition, 'flags': flags,
                   'outlooks': {'12': {'direction': direction, 'confidence': confidence}}}
            original = deepcopy(row)
            text = conclusion(row, '中文')
            self.assertIn(tr('ev_' + state, '中文') + '状态', text)
            self.assertIn(tr('ev_copy_transition_' + transition, '中文'), text)
            self.assertIn(tr('ev_' + direction, '中文') + '展望', text)
            self.assertIn('置信度评为' + tr('ev_' + confidence, '中文'), text)
            if not flags:
                self.assertIn('暂未识别到明显的结构提示', text)
            else:
                for flag in flags:
                    self.assertIn(tr('ev_' + flag, '中文'), text)
                if len(flags) > 1:
                    self.assertIn('、', text)
            flag_text = ', '.join(flags) if flags else tr('ev_no_flags')
            expected = (f'At this historical snapshot, structure is {state} and transition is {transition}; '
                        f'active evidence: {flag_text}. The {direction} outlook comes from the simulation, '
                        'with structural evidence informing confidence.')
            self.assertEqual(conclusion(row, 'English'), expected)
            self.assertEqual(row, original)

    def test_chinese_runtime_copy_and_stable_profile(self):
        app = AppTest.from_file(str(portfolio_fixtures.ROOT / 'streamlit_app.py'), default_timeout=30).run()
        app.selectbox(key='global_language').select('中文').run()
        with patch('src.market_data.download_prices', side_effect=TimeoutError()):
            app.button(key='pa_analyze').click().run()
        app.button(key='pg_run').click().run()
        self.assertFalse(app.exception)
        text = '\n'.join(str(item.value) for kind in ['markdown', 'caption', 'warning', 'info']
                         for item in app.get(kind))
        for phrase in ['让投资组合判断，更清晰。', '可重复生成的模拟数据',
                       '当前状态', '变化趋势', '结构提示', '置信度评为',
                       '分析方法', '历史验证', '请结合自身情况独立判断']:
            self.assertIn(phrase, text)
        for old in ['组合结构意味着什么', '转化状态', '确定性合成数据', '252 个收益交易日']:
            self.assertNotIn(old, text)
        self.assertEqual(app.session_state['pg_risk'], 'Balanced')
        self.assertEqual(app.session_state['pa_result']['guidance_profile']['risk_preference'], 'Balanced')
