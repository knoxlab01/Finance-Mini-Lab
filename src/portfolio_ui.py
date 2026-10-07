"""Historical analytics UI; all financial calculations stay in core modules."""
from datetime import date
import sqlite3

import pandas as pd
import streamlit as st

from src.database import Database
from src.market_data import get_historical_prices
from src.portfolio_analysis import parse_config
from src.benchmark import analyze_portfolio


def render_portfolio_analytics():
    st.caption("v0.3 Phase 1 development / 开发中 · Historical performance does not guarantee future results / 历史表现不保证未来收益。")
    st.subheader("Portfolio Setup / 组合设置")
    st.caption("仅支持同币种股票/ETF；权重为非负百分比，每日恢复目标权重，不计税费。 / Same-currency stocks/ETFs, daily target-weight rebalancing, no taxes or fees.")
    try:
        database = Database()
        saved = database.list_portfolios()
    except (OSError, sqlite3.Error):
        st.error("SQLite 无法打开，请检查数据目录权限。 / Cannot open SQLite; check data directory permissions.")
        return
    with st.expander("Saved Portfolios / 已保存组合"):
        selection = st.selectbox("Load Saved Portfolio / 选择已保存组合", saved, index=None, key="pa_saved")
        if st.button("Load Portfolio / 加载组合", key="pa_load", disabled=not saved):
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
                    st.error("无法加载组合。 / Cannot load portfolio.")
    with st.form("portfolio_setup"):
        tickers = st.text_input("Tickers / 资产代码", "AAPL, MSFT, NVDA", key="pa_tickers")
        weights = st.text_input("Weights (%) / 权重", "40, 30, 30", key="pa_weights")
        left, right = st.columns(2)
        start = left.date_input("Start Date / 开始日期", date(2021, 1, 1), key="pa_start")
        end = right.date_input("End Date / 结束日期（含）", date.today(), key="pa_end")
        benchmark = st.text_input("Benchmark / 基准", "SPY", key="pa_benchmark")
        rf = st.number_input("Risk-free Rate (%) / 无风险年利率", value=4.0, step=0.1, key="pa_rf",
                             help="可编辑的固定年有效利率假设，并非实时国债报价。 / Editable constant effective annual assumption, not a live Treasury quote.")
        name = st.text_input("Portfolio Name (optional) / 组合名称（可选）", key="pa_name")
        analyze = st.form_submit_button("Analyze Portfolio", type="primary")
        save = st.form_submit_button("Save Portfolio / 保存组合")
    if analyze or save:
        st.session_state.pop("pa_result", None)
        try:
            config = parse_config(tickers, weights, start, end, benchmark, rf / 100)
            if save:
                database.save_portfolio(name, config)
                st.session_state["pa_saved_notice"] = True
                st.rerun()
            else:
                with st.spinner("获取历史行情并分析 / Loading historical prices…"):
                    prices = get_historical_prices(config["tickers"] + [config["benchmark"]], start, end, database)
                    result = analyze_portfolio(prices, config["tickers"], config["weights"], config["benchmark"], config["risk_free_rate"])
                    result["source_metadata"] = prices.attrs.get("source_metadata", {})
                try:
                    database.record_analysis(config, result["start"], result["end"], result["source_metadata"])
                except sqlite3.Error:
                    st.warning("分析完成，但分析记录保存失败。 / Analysis completed; metadata could not be saved.")
                st.session_state["pa_result"] = result
        except (ValueError, OverflowError, OSError, sqlite3.Error) as error:
            st.error(str(error))
    if st.session_state.pop("pa_saved_notice", False):
        st.success("组合已保存，同名配置会更新。 / Portfolio saved; an existing name updates its configuration.")
    result = st.session_state.get("pa_result")
    if result is None:
        return
    st.subheader("Performance Overview / 表现概览")
    sources = result.get("source_metadata", {})
    if sources:
        labels = {"yahoo": "Yahoo Finance", "cache": "SQLite Cache", "demo": "Demo Data / 演示数据"}
        st.caption("数据源 / Data Source: " + " · ".join(
            f"{ticker}: {labels.get(meta.get('retrieval'), 'Unknown')} ({meta.get('provider', 'unknown')})"
            for ticker, meta in sources.items()))
    if any(meta.get("provider") == "demo" for meta in sources.values()):
        st.info("实时行情暂不可用，本次整个分析使用演示数据。 / Live market data is temporarily unavailable. Demo data is being used for analysis.")
        st.warning("Demo Data / 演示数据：固定可重复的合成价格，不代表 AAPL、MSFT、NVDA 或 SPY 的真实历史或实时行情，也不是预测，仅用于展示组合分析功能。 / Deterministic synthetic prices for demonstrating Portfolio Analytics only; not actual historical/live market data or predictions.")
    st.caption(f"实际共同区间 / Actual common period: {result['start'].date()} – {result['end'].date()} · {result['observations']} return observations / 收益观测值")
    st.caption("252 交易日年化；CAGR 按实际日历天数；Sharpe 使用年有效无风险利率换算的日利率。N/A 表示样本不足或零波动。 / 252 sessions/year; calendar CAGR; effective annual risk-free rate converted daily. N/A means insufficient history or zero volatility.")
    st.caption("仅使用共同观测日，不填补缺失价格；跨市场假日或缺失报价可能使相邻观测覆盖多个交易日，年化风险指标因此是近似值。 / Common observations only, no fills; holidays or missing quotes can span multiple sessions, making annualized risk approximate.")
    metric_labels = {"Cumulative Return": "Total Return", "Annualized Volatility": "Volatility",
                     "Maximum Drawdown": "Max Drawdown"}
    metric_help = {"Cumulative Return": "累计收益率 / Cumulative Return",
                   "Annualized Volatility": "年化波动率 / Annualized Volatility (252 sessions/year)",
                   "Maximum Drawdown": "最大回撤 / Maximum Drawdown"}
    for column, (metric, value) in zip(st.columns(5), result["metrics"]["Portfolio"].items()):
        display = "N/A" if pd.isna(value) else (f"{value:.2f}" if metric == "Sharpe Ratio" else f"{value:.2%}")
        column.metric(metric_labels.get(metric, metric), display, border=True, help=metric_help.get(metric))
    st.subheader("Portfolio vs Benchmark / 组合与基准对比")
    st.line_chart(result["growth"], height=360, width="stretch")
    comparison = result["metrics"].copy().astype(object)
    for metric in comparison.index:
        for column in comparison.columns:
            value = comparison.loc[metric, column]
            comparison.loc[metric, column] = "N/A" if pd.isna(value) else (f"{value:.2f}" if metric == "Sharpe Ratio" else f"{value:.2%}")
    st.dataframe(comparison, width="stretch")
    st.subheader("Risk & Diversification / 风险与分散化")
    st.line_chart(result["drawdown"], height=300, width="stretch")
    st.caption("回撤为小数，0 为历史高点。 / Drawdown is a decimal; zero marks a running peak.")
    st.markdown("**Correlation Matrix / 相关性矩阵**")
    st.dataframe(result["correlation"].style.format("{:.2f}", na_rep="N/A"), width="stretch")
    st.caption("常数收益资产的相关系数未定义，显示 N/A。 / Correlations for constant-return assets are undefined and shown as N/A.")
