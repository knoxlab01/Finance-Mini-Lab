"""Historical analytics UI; all financial calculations stay in core modules."""
from datetime import date
import sqlite3

import pandas as pd
import streamlit as st

from src.database import Database
from src.market_data import get_historical_prices
from src.portfolio_analysis import parse_config
from src.benchmark import analyze_portfolio
from src.future_ui import render_future_outlook
from src.guidance_ui import render_portfolio_guidance
from src.i18n import tr, localize_message, metric_help


def render_portfolio_analytics():
    language = st.selectbox("Language / 语言", ["English", "中文"], key="pa_language")
    t = lambda key, **values: tr(key, language, **values)
    st.caption(t('development'))
    st.subheader(t('Portfolio Setup'))
    st.caption(t('setup_note'))
    try:
        database = Database()
        saved = database.list_portfolios()
    except (OSError, sqlite3.Error):
        st.error(t('db_error'))
        return
    with st.expander(t('Saved Portfolios')):
        selection = st.selectbox(t('Load Saved Portfolio'), saved, index=None, key="pa_saved")
        if st.button(t('Load Portfolio'), key="pa_load", disabled=not saved):
            if selection:
                try:
                    config = database.load_portfolio(selection)
                    st.session_state.update(pa_tickers=", ".join(config["tickers"]),
                                            pa_weights=", ".join(f"{w * 100:g}" for w in config["weights"]),
                                            pa_start=date.fromisoformat(config["start_date"]),
                                            pa_end=date.fromisoformat(config["end_date"]),
                                            pa_benchmark=config["benchmark"], pa_rf=config["risk_free_rate"] * 100,
                                            pa_name=selection)
                    st.session_state.pop("pa_result", None)
                except (ValueError, KeyError, sqlite3.Error):
                    st.error(t('load_error'))
    with st.form("portfolio_setup"):
        tickers = st.text_input(t('Tickers'), "AAPL, MSFT, NVDA", key="pa_tickers")
        weights = st.text_input(t('Weights'), "40, 30, 30", key="pa_weights")
        left, right = st.columns(2)
        start = left.date_input(t('Start Date'), date(2021, 1, 1), key="pa_start")
        end = right.date_input(t('End Date'), date.today(), key="pa_end")
        benchmark = st.text_input(t('Benchmark'), "SPY", key="pa_benchmark", help=metric_help("benchmark", language))
        rf = st.number_input(t('Risk-free Rate'), value=4.0, step=0.1, key="pa_rf",
                             help=t('rf_help'))
        name = st.text_input(t('Portfolio Name'), key="pa_name")
        analyze = st.form_submit_button(t('Analyze Portfolio'), type="primary", key="pa_analyze")
        save = st.form_submit_button(t('Save Portfolio'), key="pa_save")
    if analyze or save:
        st.session_state.pop("pa_result", None)
        try:
            config = parse_config(tickers, weights, start, end, benchmark, rf / 100)
            if save:
                database.save_portfolio(name, config)
                st.session_state["pa_saved_notice"] = True
                st.rerun()
            else:
                with st.spinner(t('loading')):
                    prices = get_historical_prices(config["tickers"] + [config["benchmark"]], start, end, database)
                    result = analyze_portfolio(prices, config["tickers"], config["weights"], config["benchmark"], config["risk_free_rate"])
                    result["source_metadata"] = prices.attrs.get("source_metadata", {})
                    result["portfolio_config"] = config
                try:
                    database.record_analysis(config, result["start"], result["end"], result["source_metadata"])
                except sqlite3.Error:
                    st.warning(t('record_error'))
                st.session_state["pa_result"] = result
        except (ValueError, OverflowError, OSError, sqlite3.Error) as error:
            st.error(localize_message(error, language))
    if st.session_state.pop("pa_saved_notice", False):
        st.success(t('saved'))
    result = st.session_state.get("pa_result")
    if result is None:
        return
    st.subheader(t('Performance Overview'))
    sources = result.get("source_metadata", {})
    if sources:
        labels = {"yahoo": t("Yahoo Finance"), "cache": t("SQLite Cache"), "demo": t("Demo Data")}
        st.caption(t("Data Source") + ": " + " · ".join(
            f"{ticker}: {labels.get(meta.get('retrieval'), t('Unknown'))}" for ticker, meta in sources.items()))
    if any(meta.get("provider") == "demo" for meta in sources.values()):
        st.info(t('demo_notice'))
        st.warning(t('demo_warning'))
    st.caption(t("period", start=result["start"].date(), end=result["end"].date(), count=result["observations"]))
    st.caption(t('annualization'))
    st.caption(t('alignment'))
    explanations = {"Cumulative Return": "return", "CAGR": "cagr", "Annualized Volatility": "volatility",
                    "Sharpe Ratio": "sharpe", "Maximum Drawdown": "drawdown"}
    metrics = list(result["metrics"]["Portfolio"].items())
    for row in (metrics[:3], metrics[3:]):
        for column, (metric, value) in zip(st.columns(len(row)), row):
            display = "N/A" if pd.isna(value) else (f"{value:.2f}" if metric == "Sharpe Ratio" else f"{value:.2%}")
            column.metric(t(metric), display, border=True, help=metric_help(explanations[metric], language))
    st.subheader(t('Portfolio vs Benchmark'))
    st.line_chart(result["growth"].rename(columns={"Portfolio": t("Portfolio"), "Benchmark": t("Benchmark")}), height=360, width="stretch")
    comparison = result["metrics"].copy().astype(object)
    for metric in comparison.index:
        for column in comparison.columns:
            value = comparison.loc[metric, column]
            comparison.loc[metric, column] = "N/A" if pd.isna(value) else (f"{value:.2f}" if metric == "Sharpe Ratio" else f"{value:.2%}")
    st.dataframe(comparison.rename(index={key: t(key) for key in explanations}, columns={"Portfolio": t("Portfolio"), "Benchmark": t("Benchmark")}), width="stretch")
    st.subheader(t('Risk & Diversification'))
    st.line_chart(result["drawdown"].rename(columns={"Portfolio": t("Portfolio"), "Benchmark": t("Benchmark")}), height=300, width="stretch")
    st.caption(t('drawdown_note'))
    st.markdown("**" + t("Correlation Matrix") + "**")
    st.caption(metric_help("correlation", language))
    st.dataframe(result["correlation"].style.format("{:.2f}", na_rep="N/A"), width="stretch")
    st.caption(t('correlation_na'))

    with st.expander(t("metric_explanations")):
        for metric, key in explanations.items():
            st.write(t(metric) + ": " + metric_help(key, language))
        for label, key in [("Benchmark", "benchmark"), ("Correlation Matrix", "correlation")]:
            st.write(t(label) + ": " + metric_help(key, language))
    render_future_outlook(result, language)
    render_portfolio_guidance(result, language)
