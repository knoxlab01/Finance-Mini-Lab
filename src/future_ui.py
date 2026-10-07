"""Future Outlook presentation only; simulations live in future_simulation."""
import numpy as np
import pandas as pd
import streamlit as st
from src.future_simulation import estimate_parameters, build_scenarios, simulate_monte_carlo, interpret_outcomes


def render_future_outlook(historical):
    st.subheader("Future Outlook / 未来展望")
    demo = any(meta.get("provider") == "demo" for meta in historical.get("source_metadata", {}).values())
    if demo:
        st.caption("Demo-based simulation / 基于演示数据的模拟：仅用于功能展示，不是真实市场预测。 / Future simulation is based on synthetic demo data and is for feature demonstration only.")
    else:
        st.caption("模拟基于所选历史区间的组合收益和波动率估计。 / Simulation is based on historical portfolio return and volatility estimates.")
    st.caption("历史表现不保证未来结果；Monte Carlo 是假设下的模拟，不是预测或保证。 / Historical performance does not guarantee future results; simulations are not forecasts or guarantees.")
    with st.form("future_settings"):
        st.markdown("**Forecast Settings / 模拟设置**")
        left, middle, right = st.columns(3)
        value = left.number_input("Initial Portfolio Value / 当前组合价值", min_value=1., value=100000., key="fo_value")
        horizon = middle.selectbox("Forecast Horizon / 模拟期限", [1, 3, 5], index=2,
                                  format_func=lambda year: f"{year} Years / 年", key="fo_horizon")
        count = right.number_input("Simulations / 模拟次数", min_value=1000, max_value=10000, value=5000, step=1000, key="fo_count")
        run = st.form_submit_button("Run Future Outlook / 运行未来模拟")
    if run:
        historical.pop("future_outlook", None)
        try:
            parameters = estimate_parameters(historical["portfolio_returns"])
            with st.spinner("计算模拟 / Simulating…"):
                scenarios = build_scenarios(parameters, value, horizon)
                simulation = simulate_monte_carlo(parameters, value, horizon, count)
            historical["future_outlook"] = dict(parameters=parameters, scenarios=scenarios, simulation=simulation)
        except ValueError as error:
            st.warning(str(error))
    result = historical.get("future_outlook")
    if result is None:
        return
    parameters, scenarios, simulation = (result[key] for key in ("parameters", "scenarios", "simulation"))
    st.caption(f"本次结果 / Current result: {simulation['horizon']} years · {simulation['simulations']:,} simulations · initial {simulation['initial_value']:,.0f} · seed {simulation['seed']} · {parameters['observations']} historical returns")
    st.caption(f"模型年预期收益 / Model expected annual return: {parameters['expected_return']:.2%} · 年化对数波动率 / Annualized log volatility: {parameters['volatility']:.2%}. 固定种子、恒定参数；不计追加投入、税费、通胀或参数估计误差。 / Fixed seed, constant parameters; no contributions, taxes, fees, inflation or parameter uncertainty.")
    st.markdown("**Scenario Projection / 情景投影**")
    st.caption("连续收益假设 μ−σ / μ / μ+σ；Base 为模型平均财富路径，不是中位数。情景不是置信区间。 / Continuous drift assumptions; scenarios are not confidence intervals.")
    st.line_chart(scenarios["curves"], height=280)
    st.dataframe(scenarios["checkpoints"].style.format("{:,.0f}"), width="stretch")
    st.markdown("**Future Outcome Summary / 未来结果摘要**")
    for column, label, val in zip(st.columns(3), ["P10 Ending Value", "Median / P50", "P90 Ending Value"],
                                  [simulation["p10"], simulation["p50"], simulation["p90"]]):
        column.metric(label, f"{val:,.0f}", border=True)
    left, right = st.columns(2)
    left.metric("Loss Probability / 亏损概率", f"{simulation['loss_probability']:.1%}")
    right.metric("Above Initial / 高于初始价值", f"{simulation['above_probability']:.1%}")
    st.markdown("**Monte Carlo Simulation / 蒙特卡洛模拟**")
    bands = simulation["bands"].reset_index()
    sample = pd.DataFrame(simulation["paths"][:, :50], index=simulation["years"])
    sample.index.name = "Years"
    sample = sample.reset_index().melt(id_vars="Years", var_name="Path", value_name="Value")
    st.vega_lite_chart(spec={"layer": [
        {"data": {"values": bands.to_dict("records")}, "mark": {"type": "area", "opacity": .22},
         "encoding": {"x": {"field": "Years", "type": "quantitative"}, "y": {"field": "P10", "type": "quantitative", "title": "Portfolio Value"}, "y2": {"field": "P90"}}},
        {"data": {"values": sample.to_dict("records")}, "mark": {"type": "line", "opacity": .12, "strokeWidth": 1},
         "encoding": {"x": {"field": "Years", "type": "quantitative"}, "y": {"field": "Value", "type": "quantitative"}, "detail": {"field": "Path"}}},
        {"data": {"values": bands.to_dict("records")}, "mark": {"type": "line", "color": "#f59e0b", "strokeWidth": 3},
         "encoding": {"x": {"field": "Years", "type": "quantitative"}, "y": {"field": "P50", "type": "quantitative"}}}
    ], "height": 320}, width="stretch")
    st.caption("50 条样本路径；阴影为每个时间点 P10–P90，橙线为 P50；不表示 80% 的完整路径始终位于区间内。 / 50 sample paths; pointwise P10–P90 band and P50 line, not simultaneous path coverage.")
    st.markdown("**Ending Value Distribution / 期末价值分布**")
    counts, edges = np.histogram(simulation["ending"], bins=40)
    histogram = pd.DataFrame({"Low": edges[:-1], "High": edges[1:], "Count": counts})
    markers = [{"Label": label, "Value": val} for label, val in zip(["Initial", "P10", "P50", "P90"],
               [simulation["initial_value"], simulation["p10"], simulation["p50"], simulation["p90"]])]
    st.vega_lite_chart(spec={"layer": [
        {"data": {"values": histogram.to_dict("records")}, "mark": "bar",
         "encoding": {"x": {"field": "Low", "type": "quantitative", "bin": "binned", "title": "Ending Value"}, "x2": {"field": "High"}, "y": {"field": "Count", "type": "quantitative"}}},
        {"data": {"values": markers}, "mark": {"type": "rule", "strokeWidth": 2},
         "encoding": {"x": {"field": "Value", "type": "quantitative"}, "color": {"field": "Label", "type": "nominal"}, "tooltip": [{"field": "Label"}, {"field": "Value", "format": ",.0f"}]}}
    ], "height": 260}, width="stretch")
    st.markdown("**What This Means / 结果解读**")
    for insight in interpret_outcomes(simulation):
        st.write("• " + insight)
