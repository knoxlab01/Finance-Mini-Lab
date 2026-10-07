"""Future Outlook presentation only; simulations live in future_simulation."""
import numpy as np
import pandas as pd
import streamlit as st
from src.i18n import tr, localize_message, metric_help
from src.future_simulation import estimate_parameters, build_scenarios, simulate_monte_carlo, interpret_outcomes


def render_future_outlook(historical, language="English"):
    t = lambda key, **values: tr(key, language, **values)
    st.subheader(t('Future Outlook'))
    demo = any(meta.get("provider") == "demo" for meta in historical.get("source_metadata", {}).values())
    if demo:
        st.caption(t('future_demo'))
    else:
        st.caption(t('future_live'))
    st.caption(t('future_disclaimer'))
    with st.form("future_settings"):
        st.markdown("**" + t('Forecast Settings') + "**")
        left, middle, right = st.columns(3)
        value = left.number_input(t('Initial Value'), min_value=1., value=100000., key="fo_value")
        horizon = middle.selectbox(t('Forecast Horizon'), [1, 3, 5], index=2,
                                  format_func=lambda year: t("years", years=year), key="fo_horizon")
        count = right.number_input(t('Simulations'), min_value=1000, max_value=10000, value=5000, step=1000, key="fo_count")
        run = st.form_submit_button(t('Run Future Outlook'), key="fo_run")
    if run:
        historical.pop("future_outlook", None)
        try:
            parameters = estimate_parameters(historical["portfolio_returns"])
            with st.spinner(t('simulating')):
                scenarios = build_scenarios(parameters, value, horizon)
                simulation = simulate_monte_carlo(parameters, value, horizon, count)
            historical["future_outlook"] = dict(parameters=parameters, scenarios=scenarios, simulation=simulation)
        except ValueError as error:
            st.warning(localize_message(error, language))
    result = historical.get("future_outlook")
    if result is None:
        return
    parameters, scenarios, simulation = (result[key] for key in ("parameters", "scenarios", "simulation"))
    st.caption(t("current_result", years=simulation["horizon"], count=f"{simulation['simulations']:,}",
                 initial=f"{simulation['initial_value']:,.0f}", seed=simulation["seed"], observations=parameters["observations"]))
    st.caption(t("parameters", expected=f"{parameters['expected_return']:.2%}", volatility=f"{parameters['volatility']:.2%}"))
    with st.expander(t("model_help")):
        st.caption(t("model_note"))
    st.markdown("**" + t('Scenario Projection') + "**")
    st.caption(metric_help("scenarios", language))
    st.line_chart(scenarios["curves"].rename(columns={key: t(key) for key in scenarios["curves"].columns}).rename_axis(t("Years")), height=280)
    checkpoints = scenarios["checkpoints"].rename(columns={key: t(key) for key in scenarios["curves"].columns}).rename_axis(t("Year"))
    st.dataframe(checkpoints.style.format("{:,.0f}"), width="stretch")
    st.markdown("**" + t('Future Outcome Summary') + "**")
    for column, label, val in zip(st.columns(3), ["P10 Ending Value", "Median / P50", "P90 Ending Value"],
                                  [simulation["p10"], simulation["p50"], simulation["p90"]]):
        column.metric(t(label), f"{val:,.0f}", border=True, help=metric_help("percentiles", language))
    left, right = st.columns(2)
    left.metric(t('Loss Probability'), f"{simulation['loss_probability']:.1%}", help=metric_help("loss", language))
    right.metric(t('Above Initial'), f"{simulation['above_probability']:.1%}", help=t("above_help"))
    st.markdown("**" + t('Monte Carlo Simulation') + "**")
    st.caption(t("monte_help"))
    bands = simulation["bands"].reset_index()
    sample = pd.DataFrame(simulation["paths"][:, :50], index=simulation["years"])
    sample.index.name = "Years"
    sample = sample.reset_index().melt(id_vars="Years", var_name="Path", value_name="Value")
    st.vega_lite_chart(spec={"layer": [
        {"data": {"values": bands.to_dict("records")}, "mark": {"type": "area", "opacity": .22},
         "encoding": {"x": {"field": "Years", "type": "quantitative", "title": t("Years")}, "y": {"field": "P10", "type": "quantitative", "title": t("Portfolio Value")}, "y2": {"field": "P90"}}},
        {"data": {"values": sample.to_dict("records")}, "mark": {"type": "line", "opacity": .12, "strokeWidth": 1},
         "encoding": {"x": {"field": "Years", "type": "quantitative", "title": t("Years")}, "y": {"field": "Value", "type": "quantitative", "title": t("Portfolio Value")}, "detail": {"field": "Path"}}},
        {"data": {"values": bands.to_dict("records")}, "mark": {"type": "line", "color": "#f59e0b", "strokeWidth": 3},
         "encoding": {"x": {"field": "Years", "type": "quantitative", "title": t("Years")}, "y": {"field": "P50", "type": "quantitative"}}}
    ], "height": 320}, width="stretch")
    st.caption(t('band_note'))
    st.markdown("**" + t('Ending Value Distribution') + "**")
    counts, edges = np.histogram(simulation["ending"], bins=40)
    histogram = pd.DataFrame({"Low": edges[:-1], "High": edges[1:], "Count": counts})
    markers = [{"Label": t(label) if label == "Initial" else label, "Value": val} for label, val in zip(["Initial", "P10", "P50", "P90"],
               [simulation["initial_value"], simulation["p10"], simulation["p50"], simulation["p90"]])]
    st.vega_lite_chart(spec={"layer": [
        {"data": {"values": histogram.to_dict("records")}, "mark": "bar",
         "encoding": {"x": {"field": "Low", "type": "quantitative", "bin": "binned", "title": t("Ending Value")}, "x2": {"field": "High"}, "y": {"field": "Count", "type": "quantitative", "title": t("Count")}}},
        {"data": {"values": markers}, "mark": {"type": "rule", "strokeWidth": 2},
         "encoding": {"x": {"field": "Value", "type": "quantitative", "title": t("Portfolio Value")}, "color": {"field": "Label", "type": "nominal", "title": None}, "tooltip": [{"field": "Label", "title": t("Ending Value")}, {"field": "Value", "format": ",.0f", "title": t("Ending Value")}]}}
    ], "height": 260}, width="stretch")
    st.markdown("**" + t('What This Means') + "**")
    for insight in interpret_outcomes(simulation):
        st.write("• " + localize_message(insight, language))
