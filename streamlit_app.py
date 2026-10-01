"""Finance Mini Lab 的 Streamlit 网页入口。"""

from math import isfinite

import streamlit as st

from src.compound_interest import calculate_future_value


def main() -> None:
    st.set_page_config(page_title="Finance Mini Lab v0.1", page_icon="📈")
    st.title("Finance Mini Lab v0.1")
    st.caption("Estimate how an investment grows through annual compounding.")

    st.subheader("Investment Inputs")
    with st.form("compound_interest"):
        principal = st.number_input("Principal / 本金 (¥)", value=10000.0, step=100.0, format="%.2f")
        rate_percent = st.number_input("Annual Return / 年化收益率 (%)", value=8.0, step=0.1, format="%.2f")
        years = st.number_input(
            "Investment Period / 投资年限 (Years)", value=10, step=1, max_value=1000,
            help="输入 0–1000 的整数年；0 年表示尚未开始投资。",
        )
        submitted = st.form_submit_button("Calculate", type="primary")

    if not submitted:
        st.caption("填写参数后点击 Calculate · 收益率输入 8 表示 8%。")
        return

    try:
        if not all(isfinite(value) for value in (principal, rate_percent, years)):
            raise ValueError("请输入有限数字，不能使用 nan 或 inf。")
        annual_rate = rate_percent / 100
        # 所有年份均复用同一核心函数，不在界面中重复实现金融公式。
        future_value = calculate_future_value(principal, annual_rate, years)
        chart_years = list(range(years + 1))
        values = [calculate_future_value(principal, annual_rate, year) for year in chart_years]
        if not isfinite(future_value) or not all(isfinite(value) for value in values):
            raise OverflowError
    except ValueError as error:
        messages = {
            "principal 不能为负": "本金不能为负，请输入大于或等于 0 的数值。",
            "annual_rate 必须大于 -1": "年化收益率必须大于 -100%。",
            "years 不能为负": "投资年限不能为负。",
        }
        st.error(messages.get(str(error), str(error)))
        return
    except OverflowError:
        st.error("计算结果超出支持范围，请减小本金、收益率或投资年限。")
        return

    total_profit = future_value - principal
    total_return = total_profit / principal * 100 if principal > 0 else None
    multiple = future_value / principal if principal > 0 else None
    doubling_years = 72 / rate_percent if rate_percent > 0 else None

    st.subheader("Calculation Results")
    left, right = st.columns(2)
    left.metric("Initial Investment / 初始本金", f"¥{principal:,.2f}", border=True)
    right.metric("Future Value / 未来价值", f"¥{future_value:,.2f}", border=True)
    left.metric("Total Profit / 累计收益", f"¥{total_profit:,.2f}", border=True)
    return_label = f"{total_return:,.2f}%" if total_return is not None and isfinite(total_return) else "N/A"
    right.metric("Total Return / 总收益率", return_label, border=True)
    left.metric("Investment Period / 投资年限", f"{years} years", border=True)
    right.metric("Annual Return / 年化收益率", f"{rate_percent:.2f}%", border=True)
    if principal == 0:
        st.caption("初始本金为 0，总收益率和资产倍数不适用。")

    st.subheader("Portfolio Growth Over Time")
    data = {"Year": chart_years, "Portfolio Value": values}
    if years == 0:
        st.scatter_chart(data, x="Year", y="Portfolio Value", x_label="Year", y_label="Portfolio Value (¥)", color="#0F766E", height=360)
        st.caption("投资期限为 0 年，图中仅显示起始本金。")
    else:
        st.line_chart(data, x="Year", y="Portfolio Value", x_label="Year", y_label="Portfolio Value (¥)", color="#0F766E", height=360)

    table_tab, breakdown_tab, scenario_tab = st.tabs([
        "Year-by-Year Table", "Growth Breakdown", "Scenario Comparison",
    ])
    with table_tab:
        st.dataframe({
            "Year": chart_years,
            "Portfolio Value": [f"¥{value:,.2f}" for value in values],
            "Profit vs Initial": [f"¥{value - principal:,.2f}" for value in values],
        }, hide_index=True)
    with breakdown_tab:
        st.bar_chart({
            "Component": ["Initial Principal", "Compound Growth"],
            "Amount": [principal, total_profit],
        }, x="Component", y="Amount", x_label="Component", y_label="Amount (¥)", color="#0F766E", height=280)
        st.caption(f"Initial Principal: ¥{principal:,.2f} · Compound Growth: ¥{total_profit:,.2f}")
        if total_profit < 0:
            st.caption("Compound Growth 为负，表示相对初始本金的累计亏损。")

    with scenario_tab:
        # 去除重复收益率；各情景仍逐年复用核心函数。
        scenario_rates = list(dict.fromkeys([4.0, rate_percent, 12.0]))
        scenario_data = {"Year": chart_years}
        for scenario_rate in scenario_rates:
            label = f"{scenario_rate}%" + (" (Current)" if scenario_rate == rate_percent else "")
            try:
                scenario_values = [
                    calculate_future_value(principal, scenario_rate / 100, year)
                    for year in chart_years
                ]
                if not all(isfinite(value) for value in scenario_values):
                    raise OverflowError
            except OverflowError:
                st.warning(f"{label} 情景超出计算范围，已省略该曲线；当前计算结果不受影响。")
                continue
            scenario_data[label] = scenario_values
        series = list(scenario_data)[1:]
        chart = st.scatter_chart if years == 0 else st.line_chart
        chart(scenario_data, x="Year", y=series, x_label="Year", y_label="Portfolio Value (¥)", height=320)
        st.caption("相同本金和投资期限下的假设收益率对比，Current 表示当前输入。")

    st.subheader("Rule of 72")
    if doubling_years is not None and isfinite(doubling_years):
        st.metric("Estimated Doubling Time / 估算翻倍年限", f"{doubling_years:,.2f} years")
        st.caption("近似估算：72 ÷ 年化收益率百分数，并非精确翻倍时间；极端收益率下偏差较大。")
    elif rate_percent <= 0:
        st.caption("Rule of 72 仅适用于正收益率；当前收益率下不展示翻倍估算。")
    else:
        st.caption("收益率过小，翻倍估算超出显示范围。")

    st.subheader("Financial Insight")
    insights = []
    if multiple is not None and isfinite(multiple):
        insights.append(f"最终资产约为初始本金的 {multiple:,.2f} 倍。")
    insights.append(f"累计收益约为 ¥{total_profit:,.2f}。")
    if principal > 0 and doubling_years is not None and isfinite(doubling_years):
        insights.append(f"按 Rule of 72 近似估算，约需 {doubling_years:,.2f} 年翻倍，并非精确结果。")
    elif principal == 0:
        insights.append("本金为零且没有额外投入时，资产保持为零。")
    st.write(" ".join(insights))

    with st.expander("Assumptions / 假设说明", expanded=True):
        st.caption("年化收益率固定；每年复利；不考虑额外投入或取款；不考虑税费、通胀和手续费。仅用于教育和演示，不构成投资建议。")


if __name__ == "__main__":
    main()
