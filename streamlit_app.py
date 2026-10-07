"""Finance Mini Lab 的 Streamlit 网页入口。"""

from math import isfinite

import streamlit as st

from src.compound_interest import calculate_future_value
from src.dca import calculate_dca
from src.goal_planner import calculate_goal_plan
from src.scenario import calculate_scenarios
from src.inflation import adjust_for_inflation
from src.sensitivity import calculate_goal_sensitivity
from src.portfolio_ui import render_portfolio_analytics


def render_inflation(nominal_value: float, inflation_percent: float, years: int) -> None:
    st.subheader("Inflation-adjusted Value / 通胀调整后的实际购买力")
    st.caption(f"固定年通胀率假设：{inflation_percent:.2f}%。实际购买力以投资起点的货币购买力计价。仅用于教育模拟，不代表未来实际通胀预测，不构成投资建议。")
    try:
        adjusted = adjust_for_inflation(nominal_value, inflation_percent / 100, years)
    except (ValueError, OverflowError) as error:
        st.error(str(error))
        return
    st.metric("Nominal Future Value / 名义未来价值", f"¥{adjusted['nominal_value']:,.2f}", border=True)
    st.metric("Real Future Value / 实际购买力", f"¥{adjusted['real_value']:,.2f}", border=True)
    st.metric("Purchasing Power Loss / 购买力损失", f"¥{adjusted['purchasing_power_loss']:,.2f}", border=True)
    st.caption("购买力损失 = 名义未来价值 − 实际购买力；负值表示通缩下购买力增加。原有收益、图表与表格仍为名义金额。")


def render_compound_interest() -> None:
    st.caption("Estimate how an investment grows through annual compounding.")

    st.subheader("Investment Inputs / 投资参数")
    with st.form("compound_interest"):
        principal = st.number_input("Initial Principal / 初始本金 (¥)", value=10000.0, step=100.0, format="%.2f")
        rate_percent = st.number_input("Annual Return / 年化收益率 (%)", value=8.0, step=0.1, format="%.2f")
        years = st.number_input(
            "Investment Period / 投资年限 (Years)", value=10, step=1, max_value=1000,
            help="输入 0–1000 的整数年；0 年表示尚未开始投资。",
        )
        inflation_percent = st.number_input("Inflation Rate / 通胀率 (%)", value=2.0, step=0.1, format="%.2f", key="compound_inflation", help="固定年通胀率，须大于 -100%；负值表示通缩。")
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

    st.subheader("Calculation Results / 计算结果")
    left, right = st.columns(2)
    left.metric("Initial Principal / 初始本金", f"¥{principal:,.2f}", border=True)
    right.metric("Future Value / 未来价值", f"¥{future_value:,.2f}", border=True)
    left.metric("Investment Growth / 投资增长", f"¥{total_profit:,.2f}", border=True)
    return_label = f"{total_return:,.2f}%" if total_return is not None and isfinite(total_return) else "N/A"
    right.metric("Total Return / 总收益率", return_label, border=True)
    left.metric("Investment Period / 投资年限", f"{years} years", border=True)
    right.metric("Annual Return / 年化收益率", f"{rate_percent:.2f}%", border=True)
    if principal == 0:
        st.caption("初始本金为 0，总收益率和资产倍数不适用。")

    render_inflation(future_value, inflation_percent, years)

    st.subheader("Portfolio Growth / 资产增长")
    data = {"Year": chart_years, "Portfolio Value": values}
    if years == 0:
        st.scatter_chart(data, x="Year", y="Portfolio Value", x_label="Year", y_label="Value (¥)", color="#0F766E", height=360, width="stretch")
        st.caption("投资期限为 0 年，图中仅显示起始本金。")
    else:
        st.line_chart(data, x="Year", y="Portfolio Value", x_label="Year", y_label="Value (¥)", color="#0F766E", height=360, width="stretch")

    table_tab, breakdown_tab, scenario_tab = st.tabs([
        "Year-by-Year Table / 逐年明细", "Growth Breakdown / 增长构成", "Scenario Analysis / 情景分析",
    ])
    with table_tab:
        st.dataframe({
            "Year": chart_years,
            "Portfolio Value": [f"¥{value:,.2f}" for value in values],
            "Investment Growth": [f"¥{value - principal:,.2f}" for value in values],
        }, hide_index=True, width="stretch")
    with breakdown_tab:
        st.bar_chart({
            "Component": ["Initial Principal", "Investment Growth"],
            "Amount": [principal, total_profit],
        }, x="Component", y="Amount", x_label="Component", y_label="Value (¥)", color="#0F766E", height=360, width="stretch")
        st.caption(f"Initial Principal: ¥{principal:,.2f} · Investment Growth: ¥{total_profit:,.2f}")
        if total_profit < 0:
            st.caption("Investment Growth 为负，表示相对初始本金的累计亏损。")

    with scenario_tab:
        st.subheader("Scenario Analysis / 情景分析")
        st.caption("相同本金与期限：Conservative = Base − 3 个百分点；Optimistic = Base + 3 个百分点。")
        scenarios = calculate_scenarios(principal, annual_rate, years)
        if scenarios[0]["adjusted"]:
            st.info("保守收益率已调整为基准与 -100% 之间的中点，以保持大于 -100%；极近边界时受浮点精度限制。")
        st.dataframe({
            "Scenario / 情景": [row["name"] for row in scenarios],
            "Annual Return / 年化收益率": [f"{row['annual_rate'] * 100:.2f}%" for row in scenarios],
            "Future Value / 未来价值": [f"¥{row['future_value']:,.2f}" if row["future_value"] is not None else "N/A" for row in scenarios],
            "Investment Growth / 投资增长": [f"¥{row['investment_growth']:,.2f}" if row["investment_growth"] is not None else "N/A" for row in scenarios],
        }, hide_index=True, width="stretch")
        comparison = []
        for row in scenarios:
            if row["values"] is None:
                st.warning(f"{row['name']} 情景超出计算范围，已省略该曲线；基准计算结果不受影响。")
            else:
                label = f"{row['name']} ({row['annual_rate'] * 100:.2f}%)"
                comparison.extend({"Year": year, "Portfolio Value": value, "Scenario": label}
                                  for year, value in zip(row["years"], row["values"]))
        # Explicit domain and no scale-bound pan/zoom: never show negative years.
        # A zero-year horizon uses a single categorical point rather than a
        # degenerate continuous domain, which renderers can expand below zero.
        tick_step = max(1, (years + 9) // 10)
        ticks = sorted(set(range(0, years + 1, tick_step)) | {years})
        st.vega_lite_chart(spec={
            "data": {"values": comparison},
            "mark": {"type": "point" if years == 0 else "line", "clip": True},
            "encoding": {
                "x": {"field": "Year", "type": "ordinal" if years == 0 else "quantitative",
                      "title": "Year", "scale": {"domain": [0] if years == 0 else [0, years], "nice": False},
                      "axis": {"values": ticks, "format": "d"}},
                "y": {"field": "Portfolio Value", "type": "quantitative", "title": "Portfolio Value (¥)"},
                "color": {"field": "Scenario", "type": "nominal", "legend": {"orient": "bottom"}},
                "tooltip": [{"field": "Scenario", "type": "nominal"},
                            {"field": "Year", "type": "quantitative", "format": "d"},
                            {"field": "Portfolio Value", "type": "quantitative", "format": ",.2f"}],
            },
            "height": 360,
        }, width="stretch")
        st.caption("该情景分析仅用于教育模拟和敏感性比较，不代表未来收益预测。")


    st.subheader("Rule of 72 / 翻倍估算")
    if doubling_years is not None and isfinite(doubling_years):
        st.metric("Estimated Doubling Time / 估算翻倍年限", f"{doubling_years:,.2f} years")
        st.caption("近似估算：72 ÷ 年化收益率百分数，并非精确翻倍时间；极端收益率下偏差较大。")
    elif rate_percent <= 0:
        st.caption("Rule of 72 仅适用于正收益率；当前收益率下不展示翻倍估算。")
    else:
        st.caption("收益率过小，翻倍估算超出显示范围。")

    st.subheader("Financial Insight / 结果解读")
    insights = []
    if multiple is not None and isfinite(multiple):
        insights.append(f"最终资产约为初始本金的 {multiple:,.2f} 倍。")
    insights.append(f"累计收益约为 ¥{total_profit:,.2f}。")
    if principal > 0 and doubling_years is not None and isfinite(doubling_years):
        insights.append(f"按 Rule of 72 近似估算，约需 {doubling_years:,.2f} 年翻倍，并非精确结果。")
    elif principal == 0:
        insights.append("本金为零且没有额外投入时，资产保持为零。")
    st.write(" ".join(insights))

    with st.expander("Module Assumptions / 模块假设", expanded=True):
        st.caption("Annual compounding / 每年复利；一次性本金，无额外投入或取款。")


def render_dca() -> None:
    st.caption("Simulate an initial investment with fixed monthly contributions.")
    st.subheader("Investment Inputs / 投资参数")
    with st.form("dca"):
        principal = st.number_input("Initial Principal / 初始本金 (¥)", value=10000.0, step=100.0, format="%.2f", key="dca_principal")
        contribution = st.number_input("Monthly Contribution / 每月投入 (¥)", value=1000.0, step=100.0, format="%.2f", key="dca_contribution")
        rate_percent = st.number_input("Annual Return / 年化收益率 (%)", value=8.0, step=0.1, format="%.2f", key="dca_rate")
        years = st.number_input("Investment Period / 投资年限 (Years)", value=10, step=1, max_value=1000, key="dca_years", help="输入 0–1000 的整数年。每月先增长，再投入。")
        inflation_percent = st.number_input("Inflation Rate / 通胀率 (%)", value=2.0, step=0.1, format="%.2f", key="dca_inflation", help="固定年通胀率，须大于 -100%；负值表示通缩。")
        submitted = st.form_submit_button("Calculate", type="primary")
    if not submitted:
        return

    try:
        result = calculate_dca(principal, contribution, rate_percent / 100, years)
    except (ValueError, OverflowError) as error:
        st.error(str(error))
        return

    st.subheader("Calculation Results / 计算结果")
    left, right = st.columns(2)
    left.metric("Future Value / 未来价值", f"¥{result['final_portfolio_value']:,.2f}", border=True)
    right.metric("Total Contributions / 累计投入", f"¥{result['total_contributions']:,.2f}", border=True)
    left.metric("Investment Growth / 投资增长", f"¥{result['investment_growth']:,.2f}", border=True)
    total_return = result["total_return"]
    right.metric("Total Return / 总收益率", f"{total_return * 100:,.2f}%" if total_return is not None else "N/A", border=True)
    left.metric("Investment Period / 投资年限", f"{years} years", border=True)
    st.caption("Total Return = 投资收益 ÷ 累计投入，不是年化收益率，也未衡量各笔投入的持有时间。累计投入为 0 时不适用。")

    render_inflation(result["final_portfolio_value"], inflation_percent, years)
    st.caption("每月投入保持固定名义金额；通胀调整仅折现最终资产，不改变定投现金流。")

    rows = result["yearly_data"]
    st.subheader("Portfolio Growth / 资产增长")
    data = {
        "Year": [row["year"] for row in rows],
        "Total Contributions": [row["total_contributions"] for row in rows],
        "Portfolio Value": [row["portfolio_value"] for row in rows],
    }
    chart = st.scatter_chart if years == 0 else st.line_chart
    chart(data, x="Year", y=["Total Contributions", "Portfolio Value"], x_label="Year", y_label="Value (¥)", height=360, width="stretch")
    st.subheader("Year-by-Year Table / 逐年明细")
    st.dataframe({
        "Year": data["Year"],
        "Total Contributions": [f"¥{row['total_contributions']:,.2f}" for row in rows],
        "Portfolio Value": [f"¥{row['portfolio_value']:,.2f}" for row in rows],
        "Investment Growth": [f"¥{row['investment_growth']:,.2f}" for row in rows],
    }, hide_index=True, width="stretch")
    with st.expander("Module Assumptions / 模块假设", expanded=True):
        st.caption("Monthly compounding / 月度复利；月收益率 = 年化收益率 ÷ 12，每月先增长再投入。累计投入含初始本金。")


def render_goal_sensitivity(target: float, principal: float, annual_rate: float, years: int) -> None:
    st.subheader("Goal Sensitivity / 目标敏感性分析")
    st.caption("基于固定收益率假设，仅用于教育和规划模拟，不代表未来收益预测，不构成投资建议。差额 = 情景月投入 − 基准月投入；负值表示所需投入减少。")
    try:
        analysis = calculate_goal_sensitivity(target, principal, annual_rate, years)
    except (ValueError, OverflowError) as error:
        st.warning(f"敏感性分析暂不可用：{error}")
        return
    for title, rows, field, axis_title in [
        ("Time Sensitivity / 时间敏感性", analysis["time"], "years", "Investment Period (Years)"),
        ("Return Sensitivity / 收益率敏感性", analysis["return"], "annual_rate", "Annual Return (%)"),
    ]:
        st.subheader(title)
        if field == "years":
            st.caption("比较当前期限 ±5 年，限制在 1–1000 年并去重；Base 为当前期限。")
            table = {"Investment Period / 投资年限": [f"{row['years']} years" + (" (Base)" if row["is_base"] else "") for row in rows]}
        else:
            st.caption("保守 / 基准 / 乐观：当前年化收益率 −3 / 0 / +3 个百分点。")
            if rows[0]["adjusted"]:
                st.info("保守收益率已按 Scenario Analysis 规则调整为基准与 -100% 之间的中点；极近边界时受浮点精度限制。")
            table = {"Scenario / 情景": [row["name"] for row in rows],
                     "Annual Return / 年化收益率": [f"{row['annual_rate'] * 100:.2f}%" for row in rows]}
        table["Required Monthly Contribution / 每月所需投入"] = [f"¥{row['monthly']:,.2f}" if row["monthly"] is not None else "N/A" for row in rows]
        table["Difference vs Base / 较基准差额"] = [f"¥{row['difference']:+,.2f}" if row["difference"] is not None else "N/A" for row in rows]
        st.dataframe(table, hide_index=True, width="stretch")
        points = []
        for row in rows:
            if row["error"]:
                label = f"{row['years']} years" if field == "years" else row["name"]
                st.warning(f"{label} 不可用：{row['error']}；基准结果不受影响。")
            points.append({"Assumption": row[field] * (100 if field == "annual_rate" else 1),
                           "Monthly": row["monthly"]})
        st.vega_lite_chart(spec={
            "data": {"values": points}, "mark": {"type": "line", "point": True, "invalid": "break-paths-show-domains"},
            "encoding": {
                "x": {"field": "Assumption", "type": "quantitative", "title": axis_title,
                      "scale": {"zero": False, "nice": False},
                      "axis": {"values": [p["Assumption"] for p in points], "format": ".2f" if field == "annual_rate" else "d"}},
                "y": {"field": "Monthly", "type": "quantitative", "title": "Required Monthly Contribution (¥)"},
                "tooltip": [{"field": "Assumption", "title": axis_title, "format": ".2f"},
                            {"field": "Monthly", "title": "Monthly Contribution (¥)", "format": ",.2f"}],
            }, "height": 300,
        }, width="stretch")
    st.caption("通常，更长的期限或更高的假设收益率可降低月投入；负收益率、本金已足够等情况下可能出现不同趋势。")


def render_goal_planner() -> None:
    st.caption("Estimate the monthly contribution needed to reach a target.")
    st.subheader("Investment Inputs / 投资参数")
    with st.form("goal_planner"):
        target = st.number_input("Target Portfolio Value / 目标资产 (¥)", value=1000000.0, step=10000.0, format="%.2f", key="goal_target")
        principal = st.number_input("Initial Principal / 初始本金 (¥)", value=100000.0, step=1000.0, format="%.2f", key="goal_principal")
        rate_percent = st.number_input("Annual Return / 年化收益率 (%)", value=8.0, step=0.1, format="%.2f", key="goal_rate")
        years = st.number_input("Investment Period / 投资年限 (Years)", value=10, step=1, max_value=1000, key="goal_years", help="输入 1–1000 的整数年。")
        submitted = st.form_submit_button("Calculate", type="primary")
    if not submitted:
        return
    try:
        result = calculate_goal_plan(target, principal, rate_percent / 100, years)
    except (ValueError, OverflowError) as error:
        st.error(str(error))
        return

    monthly = result["required_monthly_contribution"]
    st.subheader("Calculation Results / 计算结果")
    left, right = st.columns(2)
    left.metric("Target Portfolio Value / 目标资产", f"¥{target:,.2f}", border=True)
    right.metric("Required Monthly Contribution / 每月所需投入", f"¥{monthly:,.2f}", border=True)
    left.metric("Total Contributions / 累计投入", f"¥{result['total_contributions']:,.2f}", border=True)
    right.metric("Investment Growth / 投资增长", f"¥{result['investment_growth']:,.2f}", border=True)
    left.metric("Investment Period / 投资年限", f"{years} years", border=True)
    st.caption("模拟使用未舍入的月投入；显示金额保留两位小数，按显示金额实际投入可能产生少量差额。")

    rows = result["yearly_data"]
    st.subheader("Portfolio Growth / 资产增长")
    st.line_chart({
        "Year": [row["year"] for row in rows],
        "Total Contributions": [row["total_contributions"] for row in rows],
        "Portfolio Value": [row["portfolio_value"] for row in rows],
        "Target Value": [target for row in rows],
    }, x="Year", y=["Total Contributions", "Portfolio Value", "Target Value"],
        x_label="Year", y_label="Value (¥)", height=360, width="stretch")
    st.subheader("Year-by-Year Table / 逐年明细")
    st.dataframe({
        "Year": [row["year"] for row in rows],
        "Total Contributions": [f"¥{row['total_contributions']:,.2f}" for row in rows],
        "Portfolio Value": [f"¥{row['portfolio_value']:,.2f}" for row in rows],
        "Remaining Gap to Target": [f"¥{row['remaining_gap']:,.2f}" for row in rows],
    }, hide_index=True, width="stretch")
    st.subheader("Financial Insight / 结果解读")
    if monthly == 0:
        st.write(f"在当前假设下，初始本金 ¥{principal:,.2f} 在 {years} 年后的模拟资产为 ¥{result['final_portfolio_value']:,.2f}，已达到或超过目标 ¥{target:,.2f}，无需额外月投入。")
    else:
        st.write(f"在当前假设下，要在 {years} 年后达到 ¥{target:,.2f}，初始本金 ¥{principal:,.2f} 时，每月大约需要投入 ¥{monthly:,.2f}。")
    render_goal_sensitivity(target, principal, rate_percent / 100, years)

    with st.expander("Module Assumptions / 模块假设", expanded=True):
        st.caption("Monthly compounding / 月度复利；与 DCA 一致，月收益率 = 年化收益率 ÷ 12，每月先增长再投入。")


def main() -> None:
    st.set_page_config(page_title="Finance Mini Lab v0.3.0", page_icon="📈")
    st.title("Finance Mini Lab v0.3.0")
    st.write("A lightweight financial planning, portfolio analytics, and scenario simulation toolkit built with Python and Streamlit.")
    st.caption("一个基于 Python 与 Streamlit 构建的轻量级金融规划、投资组合分析与情景模拟工具。仅用于教育和模拟，不构成投资建议。")

    st.subheader("Explore the Modules")
    overview = [
        ("Compound Interest", "复利计算", "模拟一次性本金增长。"),
        ("DCA Simulator", "定投模拟", "模拟每月定投积累。"),
        ("Goal Planner", "目标规划", "反推目标所需月投入。"),
        ("Portfolio Analytics", "组合分析", "历史表现与基准对比、风险分散化、未来情景与组合建议。"),
    ]
    for offset in (0, 2):
        for column, (title, subtitle, description) in zip(st.columns(2), overview[offset:offset + 2]):
            with column:
                with st.container(border=True, height=160):
                    st.markdown(f"**{title}**")
                    st.caption(subtitle)
                    st.write(description)
    st.caption("Portfolio Analytics: Monte Carlo · Explainable analytics · SQLite cache & persistence · English / 中文。选择下方标签页开始。")
    compound_tab, dca_tab, goal_tab, portfolio_tab = st.tabs([
        "Compound Interest / 复利计算", "DCA Simulator / 定投模拟", "Goal Planner / 目标规划",
        "Portfolio Analytics / 组合分析",
    ])
    with compound_tab:
        render_compound_interest()
    with dca_tab:
        render_dca()
    with goal_tab:
        render_goal_planner()
    with portfolio_tab:
        render_portfolio_analytics()

    st.divider()
    with st.expander("About / Assumptions · 关于与假设", expanded=True):
        st.markdown(
            "- Fixed return assumption / 固定收益率假设，不保证实际收益。\n"
            "- Annual or monthly compounding depends on module / 按模块采用年度或月度复利。\n"
            "- No tax or fees; planning modules use fixed returns / 不计税费；规划模块使用固定收益，组合分析使用历史行情。\n"
            "- Inflation adjustment applies to Compound Interest and DCA only / 复利与定投另列通胀调整结果；目标规划保持名义金额。\n"
            "- Educational use only · Not investment advice / 仅用于教育演示，不构成投资建议。"
        )


if __name__ == "__main__":
    main()
