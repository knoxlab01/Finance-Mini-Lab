"""Small, opt-in brand accents. Native controls, metrics and charts stay untouched."""
import streamlit as st


CSS = """
.st-key-vexa_polish_hero { background: #0F172A; border-radius: 8px; padding: 1.25rem 1.5rem; margin-bottom: .5rem; }
.st-key-vexa_polish_hero h1 { color: #FFFFFF; padding-top: 0; padding-bottom: 0; }
.st-key-vexa_polish_hero [data-testid="stMarkdownContainer"] { color: #E2E8F0; }
.st-key-vexa_polish_hero [data-testid="stMarkdownContainer"] strong { color: #FFFFFF; }
[class*="st-key-vexa_polish_module_"] { min-height: 160px; }
.st-key-vexa_polish_portfolio { min-height: 160px; border-top: 2px solid #2563EB; }
.st-key-vexa_polish_featured [data-testid="stMarkdownContainer"] { color: #1D4ED8; font-size: .8rem; font-weight: 600; }
.st-key-vexa_polish_signature [data-testid="stMarkdownContainer"] { color: #0F766E; }
.st-key-vexa_polish_takeaway { border-left: 2px solid #0F766E; }
[class*="st-key-vexa_polish_negative_"] [data-testid="stMarkdownContainer"] { color: #991B1B; }
[class*="st-key-vexa_polish_positive_"] [data-testid="stMarkdownContainer"] { color: #166534; }
[class*="st-key-vexa_polish_caution_"] [data-testid="stMarkdownContainer"] { color: #92400E; }
[class*="st-key-vexa_polish_neutral_"] [data-testid="stMarkdownContainer"] { color: #475569; }
"""


def apply_polish():
    st.html("<style>" + CSS + "</style>")


def semantic_text(text, key, tone="neutral", help=None):
    """Only color existing text; preserve accessible content and its explanation."""
    with st.container(key=f"vexa_polish_{tone}_{key}"):
        st.markdown(text, help=help)


def direction_tone(direction):
    """Presentation mapping of already-computed direction; no model inference."""
    return {"Strong Bearish": "negative", "Bearish": "negative",
            "Strong Bullish": "positive", "Bullish": "positive"}.get(direction, "neutral")
