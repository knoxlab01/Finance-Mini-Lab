"""Keep brand CSS local and protect accessible semantic result text."""
import re
import unittest
from streamlit.testing.v1 import AppTest
from src.visual_polish import CSS, direction_tone


class VisualPolishTests(unittest.TestCase):
    def test_css_is_opt_in_and_excludes_rendering_controls(self):
        rules = re.findall(r'([^{}]+)\{([^{}]+)\}', CSS)
        self.assertTrue(rules)
        for selector, declarations in rules:
            self.assertTrue(selector.strip().startswith(('.st-key-vexa_polish_', '[class*="st-key-vexa_polish_')))
            self.assertNotRegex(selector.lower(), r'canvas|svg|plotly|vega|chart|metric|selectbox|input')
            self.assertNotRegex(declarations.lower(), r'opacity|filter|transform|stroke|zoom|shadow|animation|font-family')

    def test_semantic_text_retains_content_help_and_direction(self):
        app = AppTest.from_string('''
from src.visual_polish import semantic_text
semantic_text("**12-Month Outlook:** Strong Bearish", "direction", tone="negative", help="Historical evidence")
semantic_text("**12 个月展望：** 强看跌", "chinese", tone="negative")
''').run()
        self.assertFalse(app.exception)
        self.assertEqual([x.value for x in app.markdown],
                         ['**12-Month Outlook:** Strong Bearish', '**12 个月展望：** 强看跌'])
        self.assertEqual(app.markdown[0].proto.help, 'Historical evidence')
        self.assertEqual(direction_tone('Strong Bearish'), 'negative')
        self.assertEqual(direction_tone('Bullish'), 'positive')
        self.assertEqual(direction_tone('Neutral / Uncertain'), 'neutral')
