"""Compact, language-specific Evolance comparison; frozen logic stays outside UI."""
import pandas as pd
import streamlit as st
from src.i18n import tr
from src.evolance_product import comparison_for, conclusion


def render_evolance_comparison(historical, language='English'):
    t = lambda k, **v: tr('ev_' + k, language, **v)
    colon = tr('copy_separator', language).rstrip()
    st.subheader(t('intro_title'))
    st.markdown('**' + t('intro_subtitle') + '**')
    st.write(t('intro_text'))
    st.write(t('intro_meaning'))
    st.caption(t('intro_side_by_side'))
    st.subheader(t('title'))
    result = comparison_for(historical)
    ready = result['status'] == 'ready'
    if result['synthetic']:
        st.info(t('demo'))
    if ready:
        row = result['latest']
        st.caption(t('snapshot_period', start=row['window_start'], date=row['date']))
    left, right = st.columns(2)
    with left.container(border=True):
        st.markdown('### ' + t('traditional'))
        st.caption(t('snapshot_title') if ready else t('selected_period'))
        if ready:
            metrics = row['metrics']
            values = [('Cumulative Return', metrics['absolute_return']), ('CAGR', metrics['cagr']),
                      ('Annualized Volatility', metrics['volatility']), ('Sharpe Ratio', metrics['sharpe']),
                      ('Maximum Drawdown', -metrics['drawdown'])]
            relative = metrics['active_return']
        else:
            # No qualifying monthly snapshot: retain the existing historical overview,
            # explicitly labelled as the full period rather than a matching window.
            values = list(historical['metrics']['Portfolio'].items())
            relative = historical['metrics'].loc['Cumulative Return', 'Portfolio'] - historical['metrics'].loc['Cumulative Return', 'Benchmark']
        for key, value in values:
            formatted = t('unavailable') if pd.isna(value) else f'{value:.2f}' if key == 'Sharpe Ratio' else f'{value:.2%}'
            st.markdown(f"**{tr(key, language)}{colon}** {formatted}")
        st.markdown(t('relative', value=f'{relative * 100:+.2f}'), help=t('relative_help'))
    with right.container(border=True):
        st.markdown('### Evolance')
        st.caption(t('structural_subtitle'))
        if not ready:
            st.caption(t(result['status']))
            st.caption(t('required'))
        else:
            out = row['outlooks']['12']
            st.markdown('**' + t('state') + colon + '** ' + t(row['confirmed_state']), help=t(row['confirmed_state'] + '_help'))
            st.markdown('**' + t('transition') + colon + '** ' + t(row['transition']), help=t(row['transition'] + '_help'))
            st.markdown('**' + t('12m') + colon + '** ' + t(out['direction']))
            st.markdown('**' + t('confidence') + colon + '** ' + t(out['confidence']), help=t('confidence_help'))
            short = row['outlooks']['6']
            st.markdown('**' + t('6m') + colon + '** ' + t(short['direction']) + ' · ' + t(short['confidence']))
            flags = ', '.join(t(flag) for flag in row['flags']) if row['flags'] else t('no_flags')
            st.markdown('**' + t('flags') + colon + '** ' + flags)
    if ready:
        with st.container(border=True):
            st.markdown('### ' + t('takeaway'))
            st.markdown('**' + t('copy_takeaway_summary', direction=t(out['direction']), confidence=t(out['confidence']), confidence_label=t('confidence')) + '**')
            st.write(conclusion(row, language))
            st.caption(t('disclaimer'))
        with st.expander(t('detail'), expanded=False):
            for dimension, score in row['scores'].items():
                band = 'unavailable' if score is None else 'strong' if score >= 80 else 'healthy' if score >= 60 else 'mixed' if score >= 40 else 'weak' if score >= 20 else 'very_weak'
                display = t('unavailable') if score is None else f'{score:.0f} · {t(band)}'
                st.markdown('**' + t(dimension) + colon + '** ' + display, help=t(dimension + '_help'))
            if not row['transition_evidence_available'] or not row['confirmation_initialized']:
                st.caption(t('warmup'))
            st.caption(t('bands_note'))
    with st.expander(t('method_validation'), expanded=False):
        st.markdown('**' + t('how_it_works') + '**')
        st.write(t('methodology_text'))
        st.markdown('**' + t('historical_evidence') + '**')
        st.write(t('research_text'))
