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
from src.i18n import tr, localize_message, current_language
from src.visual_polish import apply_polish

def L(text, **values):
    return tr("legacy:" + text, current_language(), **values)

def message(value):
    return localize_message(value, current_language())

def cached_calculation(function, *args):
    cache = st.session_state.setdefault("calculator_cache", {})
    key = (function.__name__, args)
    if key not in cache:
        cache[key] = function(*args)
    return cache[key]



def render_inflation(nominal_value: float, inflation_percent: float, years: int) -> None:
    st.subheader(L('Inflation-adjusted Value / 通胀调整后的实际购买力'))
    st.caption(L('固定年通胀率假设：{v0:.2f}%。实际购买力以投资起点的货币购买力计价。仅用于教育模拟，不代表未来实际通胀预测，不构成投资建议。', v0=inflation_percent))
    try:
        adjusted = cached_calculation(adjust_for_inflation, nominal_value, inflation_percent / 100, years)
    except (ValueError, OverflowError) as error:
        st.error(message(error))
        return
    st.metric(L('Nominal Future Value / 名义未来价值'), f"¥{adjusted['nominal_value']:,.2f}", border=True)
    st.metric(L('Real Future Value / 实际购买力'), f"¥{adjusted['real_value']:,.2f}", border=True)
    st.metric(L('Purchasing Power Loss / 购买力损失'), f"¥{adjusted['purchasing_power_loss']:,.2f}", border=True)
    st.caption(L('购买力损失 = 名义未来价值 − 实际购买力；负值表示通缩下购买力增加。原有收益、图表与表格仍为名义金额。'))


def render_compound_interest() -> None:
    st.caption(L('Estimate how an investment grows through annual compounding.'))

    st.subheader(L('Investment Inputs / 投资参数'))
    with st.form("compound_interest"):
        principal = st.number_input(L('Initial Principal / 初始本金 (¥)'), value=10000.0, step=100.0, format="%.2f", key="compound_principal")
        rate_percent = st.number_input(L('Annual Return / 年化收益率 (%)'), value=8.0, step=0.1, format="%.2f", key="compound_rate")
        years = st.number_input(
            L('Investment Period / 投资年限 (Years)'), value=10, step=1, max_value=1000, key="compound_years",
            help=L('输入 0–1000 的整数年；0 年表示尚未开始投资。'),
        )
        inflation_percent = st.number_input(L('Inflation Rate / 通胀率 (%)'), value=2.0, step=0.1, format="%.2f", key="compound_inflation", help=L('固定年通胀率，须大于 -100%；负值表示通缩。'))
        submitted = st.form_submit_button(L('Calculate'), type="primary")

    if submitted:
        st.session_state["compound_result_inputs"] = (principal, rate_percent, years, inflation_percent)
    if "compound_result_inputs" not in st.session_state:
        st.caption(L('填写参数后点击 Calculate · 收益率输入 8 表示 8%。'))
        return

    principal, rate_percent, years, inflation_percent = st.session_state["compound_result_inputs"]
    try:
        if not all(isfinite(value) for value in (principal, rate_percent, years)):
            raise ValueError(L('请输入有限数字，不能使用 nan 或 inf。'))
        annual_rate = rate_percent / 100
        # 所有年份均复用同一核心函数，不在界面中重复实现金融公式。
        future_value = cached_calculation(calculate_future_value, principal, annual_rate, years)
        chart_years = list(range(years + 1))
        values = [cached_calculation(calculate_future_value, principal, annual_rate, year) for year in chart_years]
        if not isfinite(future_value) or not all(isfinite(value) for value in values):
            raise OverflowError
    except ValueError as error:
        messages = {
            "principal 不能为负": L('本金不能为负，请输入大于或等于 0 的数值。'),
            "annual_rate 必须大于 -1": L('年化收益率必须大于 -100%。'),
            "years 不能为负": L('投资年限不能为负。'),
        }
        st.error(message(messages.get(str(error), str(error))))
        return
    except OverflowError:
        st.error(L('计算结果超出支持范围，请减小本金、收益率或投资年限。'))
        return

    total_profit = future_value - principal
    total_return = total_profit / principal * 100 if principal > 0 else None
    multiple = future_value / principal if principal > 0 else None
    doubling_years = 72 / rate_percent if rate_percent > 0 else None

    st.subheader(L('Calculation Results / 计算结果'))
    left, right = st.columns(2)
    left.metric(L('Initial Principal / 初始本金'), f"¥{principal:,.2f}", border=True)
    right.metric(L('Future Value / 未来价值'), f"¥{future_value:,.2f}", border=True)
    left.metric(L('Investment Growth / 投资增长'), f"¥{total_profit:,.2f}", border=True)
    return_label = f"{total_return:,.2f}%" if total_return is not None and isfinite(total_return) else "N/A"
    right.metric(L('Total Return / 总收益率'), return_label, border=True)
    left.metric(L('Investment Period / 投资年限'), L('{v0} years', v0=years), border=True)
    right.metric(L('Annual Return / 年化收益率'), f"{rate_percent:.2f}%", border=True)
    if principal == 0:
        st.caption(L('初始本金为 0，总收益率和资产倍数不适用。'))

    render_inflation(future_value, inflation_percent, years)

    st.subheader(L('Portfolio Growth / 资产增长'))
    data = {L('Year'): chart_years, L('Portfolio Value'): values}
    if years == 0:
        st.scatter_chart(data, x=L('Year'), y=L('Portfolio Value'), x_label=L('Year'), y_label=L('Value (¥)'), color="#0F766E", height=360, width="stretch")
        st.caption(L('投资期限为 0 年，图中仅显示起始本金。'))
    else:
        st.line_chart(data, x=L('Year'), y=L('Portfolio Value'), x_label=L('Year'), y_label=L('Value (¥)'), color="#0F766E", height=360, width="stretch")

    table_tab, breakdown_tab, scenario_tab = st.tabs([
        L('Year-by-Year Table / 逐年明细'), L('Growth Breakdown / 增长构成'), L('Scenario Analysis / 情景分析'),
    ])
    with table_tab:
        st.dataframe({
            L('Year'): chart_years,
            L('Portfolio Value'): [f"¥{value:,.2f}" for value in values],
            L('Investment Growth'): [f"¥{value - principal:,.2f}" for value in values],
        }, hide_index=True, width="stretch")
    with breakdown_tab:
        st.bar_chart({
            L('Component'): [L('Initial Principal'), L('Investment Growth')],
            L('Amount'): [principal, total_profit],
        }, x=L('Component'), y=L('Amount'), x_label=L('Component'), y_label=L('Value (¥)'), color="#0F766E", height=360, width="stretch")
        st.caption(L('Initial Principal: ¥{v0:,.2f} · Investment Growth: ¥{v1:,.2f}', v0=principal, v1=total_profit))
        if total_profit < 0:
            st.caption(L('Investment Growth 为负，表示相对初始本金的累计亏损。'))

    with scenario_tab:
        st.subheader(L('Scenario Analysis / 情景分析'))
        st.caption(L('相同本金与期限：Conservative = Base − 3 个百分点；Optimistic = Base + 3 个百分点。'))
        scenarios = cached_calculation(calculate_scenarios, principal, annual_rate, years)
        if scenarios[0]["adjusted"]:
            st.info(L('保守收益率已调整为基准与 -100% 之间的中点，以保持大于 -100%；极近边界时受浮点精度限制。'))
        st.dataframe({
            L('Scenario / 情景'): [message(row["name"]) for row in scenarios],
            L('Annual Return / 年化收益率'): [f"{row['annual_rate'] * 100:.2f}%" for row in scenarios],
            L('Future Value / 未来价值'): [f"¥{row['future_value']:,.2f}" if row["future_value"] is not None else "N/A" for row in scenarios],
            L('Investment Growth / 投资增长'): [f"¥{row['investment_growth']:,.2f}" if row["investment_growth"] is not None else "N/A" for row in scenarios],
        }, hide_index=True, width="stretch")
        comparison = []
        for row in scenarios:
            if row["values"] is None:
                st.warning(L('{v0} 情景超出计算范围，已省略该曲线；基准计算结果不受影响。', v0=message(row['name'])))
            else:
                label = f"{message(row['name'])} ({row['annual_rate'] * 100:.2f}%)"
                comparison.extend({L('Year'): year, L('Portfolio Value'): value, L('Scenario'): label}
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
                "x": {"field": L('Year'), "type": "ordinal" if years == 0 else "quantitative",
                      "title": L('Year'), "scale": {"domain": [0] if years == 0 else [0, years], "nice": False},
                      "axis": {"values": ticks, "format": "d"}},
                "y": {"field": L('Portfolio Value'), "type": "quantitative", "title": L('Portfolio Value (¥)')},
                "color": {"field": L('Scenario'), "type": "nominal", "legend": {"orient": "bottom"}},
                "tooltip": [{"field": L('Scenario'), "type": "nominal"},
                            {"field": L('Year'), "type": "quantitative", "format": "d"},
                            {"field": L('Portfolio Value'), "type": "quantitative", "format": ",.2f"}],
            },
            "height": 360,
        }, width="stretch")
        st.caption(L('该情景分析仅用于教育模拟和敏感性比较，不代表未来收益预测。'))


    st.subheader(L('Rule of 72 / 翻倍估算'))
    if doubling_years is not None and isfinite(doubling_years):
        st.metric(L('Estimated Doubling Time / 估算翻倍年限'), L('{v0:,.2f} years', v0=doubling_years))
        st.caption(L('近似估算：72 ÷ 年化收益率百分数，并非精确翻倍时间；极端收益率下偏差较大。'))
    elif rate_percent <= 0:
        st.caption(L('Rule of 72 仅适用于正收益率；当前收益率下不展示翻倍估算。'))
    else:
        st.caption(L('收益率过小，翻倍估算超出显示范围。'))

    st.subheader(L('Financial Insight / 结果解读'))
    insights = []
    if multiple is not None and isfinite(multiple):
        insights.append(L('最终资产约为初始本金的 {v0:,.2f} 倍。', v0=multiple))
    insights.append(L('累计收益约为 ¥{v0:,.2f}。', v0=total_profit))
    if principal > 0 and doubling_years is not None and isfinite(doubling_years):
        insights.append(L('按 Rule of 72 近似估算，约需 {v0:,.2f} 年翻倍，并非精确结果。', v0=doubling_years))
    elif principal == 0:
        insights.append(L('本金为零且没有额外投入时，资产保持为零。'))
    st.write(" ".join(insights))

    with st.expander(L('Module Assumptions / 模块假设'), expanded=True):
        st.caption(L('Annual compounding / 每年复利；一次性本金，无额外投入或取款。'))


def render_dca() -> None:
    st.caption(L('Simulate an initial investment with fixed monthly contributions.'))
    st.subheader(L('Investment Inputs / 投资参数'))
    with st.form("dca"):
        principal = st.number_input(L('Initial Principal / 初始本金 (¥)'), value=10000.0, step=100.0, format="%.2f", key="dca_principal")
        contribution = st.number_input(L('Monthly Contribution / 每月投入 (¥)'), value=1000.0, step=100.0, format="%.2f", key="dca_contribution")
        rate_percent = st.number_input(L('Annual Return / 年化收益率 (%)'), value=8.0, step=0.1, format="%.2f", key="dca_rate")
        years = st.number_input(L('Investment Period / 投资年限 (Years)'), value=10, step=1, max_value=1000, key="dca_years", help=L('输入 0–1000 的整数年。每月先增长，再投入。'))
        inflation_percent = st.number_input(L('Inflation Rate / 通胀率 (%)'), value=2.0, step=0.1, format="%.2f", key="dca_inflation", help=L('固定年通胀率，须大于 -100%；负值表示通缩。'))
        submitted = st.form_submit_button(L('Calculate'), type="primary")
    if submitted:
        st.session_state["dca_result_inputs"] = (principal, contribution, rate_percent, years, inflation_percent)
    if "dca_result_inputs" not in st.session_state:
        return
    principal, contribution, rate_percent, years, inflation_percent = st.session_state["dca_result_inputs"]

    try:
        result = cached_calculation(calculate_dca, principal, contribution, rate_percent / 100, years)
    except (ValueError, OverflowError) as error:
        st.error(message(error))
        return

    st.subheader(L('Calculation Results / 计算结果'))
    left, right = st.columns(2)
    left.metric(L('Future Value / 未来价值'), f"¥{result['final_portfolio_value']:,.2f}", border=True)
    right.metric(L('Total Contributions / 累计投入'), f"¥{result['total_contributions']:,.2f}", border=True)
    left.metric(L('Investment Growth / 投资增长'), f"¥{result['investment_growth']:,.2f}", border=True)
    total_return = result["total_return"]
    right.metric(L('Total Return / 总收益率'), f"{total_return * 100:,.2f}%" if total_return is not None else "N/A", border=True)
    left.metric(L('Investment Period / 投资年限'), L('{v0} years', v0=years), border=True)
    st.caption(L('Total Return = 投资收益 ÷ 累计投入，不是年化收益率，也未衡量各笔投入的持有时间。累计投入为 0 时不适用。'))

    render_inflation(result["final_portfolio_value"], inflation_percent, years)
    st.caption(L('每月投入保持固定名义金额；通胀调整仅折现最终资产，不改变定投现金流。'))

    rows = result["yearly_data"]
    st.subheader(L('Portfolio Growth / 资产增长'))
    data = {
        L('Year'): [row["year"] for row in rows],
        L('Total Contributions'): [row["total_contributions"] for row in rows],
        L('Portfolio Value'): [row["portfolio_value"] for row in rows],
    }
    chart = st.scatter_chart if years == 0 else st.line_chart
    chart(data, x=L('Year'), y=[L('Total Contributions'), L('Portfolio Value')], x_label=L('Year'), y_label=L('Value (¥)'), height=360, width="stretch")
    st.subheader(L('Year-by-Year Table / 逐年明细'))
    st.dataframe({
        L('Year'): data[L('Year')],
        L('Total Contributions'): [f"¥{row['total_contributions']:,.2f}" for row in rows],
        L('Portfolio Value'): [f"¥{row['portfolio_value']:,.2f}" for row in rows],
        L('Investment Growth'): [f"¥{row['investment_growth']:,.2f}" for row in rows],
    }, hide_index=True, width="stretch")
    with st.expander(L('Module Assumptions / 模块假设'), expanded=True):
        st.caption(L('Monthly compounding / 月度复利；月收益率 = 年化收益率 ÷ 12，每月先增长再投入。累计投入含初始本金。'))


def render_goal_sensitivity(target: float, principal: float, annual_rate: float, years: int) -> None:
    st.subheader(L('Goal Sensitivity / 目标敏感性分析'))
    st.caption(L('基于固定收益率假设，仅用于教育和规划模拟，不代表未来收益预测，不构成投资建议。差额 = 情景月投入 − 基准月投入；负值表示所需投入减少。'))
    try:
        analysis = cached_calculation(calculate_goal_sensitivity, target, principal, annual_rate, years)
    except (ValueError, OverflowError) as error:
        st.warning(L('敏感性分析暂不可用：{v0}', v0=message(error)))
        return
    for title, rows, field, axis_title in [
        (L('Time Sensitivity / 时间敏感性'), analysis["time"], "years", L('Investment Period (Years)')),
        (L('Return Sensitivity / 收益率敏感性'), analysis["return"], "annual_rate", L('Annual Return (%)')),
    ]:
        st.subheader(title)
        if field == "years":
            st.caption(L('比较当前期限 ±5 年，限制在 1–1000 年并去重；Base 为当前期限。'))
            table = {L('Investment Period / 投资年限'): [L('{v0} years', v0=row['years']) + (L(' (Base)') if row["is_base"] else "") for row in rows]}
        else:
            st.caption(L('保守 / 基准 / 乐观：当前年化收益率 −3 / 0 / +3 个百分点。'))
            if rows[0]["adjusted"]:
                st.info(L('保守收益率已按 Scenario Analysis 规则调整为基准与 -100% 之间的中点；极近边界时受浮点精度限制。'))
            table = {L('Scenario / 情景'): [message(row["name"]) for row in rows],
                     L('Annual Return / 年化收益率'): [f"{row['annual_rate'] * 100:.2f}%" for row in rows]}
        table[L('Required Monthly Contribution / 每月所需投入')] = [f"¥{row['monthly']:,.2f}" if row["monthly"] is not None else "N/A" for row in rows]
        table[L('Difference vs Base / 较基准差额')] = [f"¥{row['difference']:+,.2f}" if row["difference"] is not None else "N/A" for row in rows]
        st.dataframe(table, hide_index=True, width="stretch")
        points = []
        for row in rows:
            if row["error"]:
                label = L('{v0} years', v0=row['years']) if field == "years" else message(row["name"])
                st.warning(L('{v0} 不可用：{v1}；基准结果不受影响。', v0=label, v1=message(row['error'])))
            points.append({"Assumption": row[field] * (100 if field == "annual_rate" else 1),
                           "Monthly": row["monthly"]})
        st.vega_lite_chart(spec={
            "data": {"values": points}, "mark": {"type": "line", "point": True, "invalid": "break-paths-show-domains"},
            "encoding": {
                "x": {"field": "Assumption", "type": "quantitative", "title": axis_title,
                      "scale": {"zero": False, "nice": False},
                      "axis": {"values": [p["Assumption"] for p in points], "format": ".2f" if field == "annual_rate" else "d"}},
                "y": {"field": "Monthly", "type": "quantitative", "title": L('Required Monthly Contribution (¥)')},
                "tooltip": [{"field": "Assumption", "title": axis_title, "format": ".2f"},
                            {"field": "Monthly", "title": L('Monthly Contribution (¥)'), "format": ",.2f"}],
            }, "height": 300,
        }, width="stretch")
    st.caption(L('通常，更长的期限或更高的假设收益率可降低月投入；负收益率、本金已足够等情况下可能出现不同趋势。'))


def render_goal_planner() -> None:
    st.caption(L('Estimate the monthly contribution needed to reach a target.'))
    st.subheader(L('Investment Inputs / 投资参数'))
    with st.form("goal_planner"):
        target = st.number_input(L('Target Portfolio Value / 目标资产 (¥)'), value=1000000.0, step=10000.0, format="%.2f", key="goal_target")
        principal = st.number_input(L('Initial Principal / 初始本金 (¥)'), value=100000.0, step=1000.0, format="%.2f", key="goal_principal")
        rate_percent = st.number_input(L('Annual Return / 年化收益率 (%)'), value=8.0, step=0.1, format="%.2f", key="goal_rate")
        years = st.number_input(L('Investment Period / 投资年限 (Years)'), value=10, step=1, max_value=1000, key="goal_years", help=L('输入 1–1000 的整数年。'))
        submitted = st.form_submit_button(L('Calculate'), type="primary")
    if submitted:
        st.session_state["goal_result_inputs"] = (target, principal, rate_percent, years)
    if "goal_result_inputs" not in st.session_state:
        return
    target, principal, rate_percent, years = st.session_state["goal_result_inputs"]
    try:
        result = cached_calculation(calculate_goal_plan, target, principal, rate_percent / 100, years)
    except (ValueError, OverflowError) as error:
        st.error(message(error))
        return

    monthly = result["required_monthly_contribution"]
    st.subheader(L('Calculation Results / 计算结果'))
    left, right = st.columns(2)
    left.metric(L('Target Portfolio Value / 目标资产'), f"¥{target:,.2f}", border=True)
    right.metric(L('Required Monthly Contribution / 每月所需投入'), f"¥{monthly:,.2f}", border=True)
    left.metric(L('Total Contributions / 累计投入'), f"¥{result['total_contributions']:,.2f}", border=True)
    right.metric(L('Investment Growth / 投资增长'), f"¥{result['investment_growth']:,.2f}", border=True)
    left.metric(L('Investment Period / 投资年限'), L('{v0} years', v0=years), border=True)
    st.caption(L('模拟使用未舍入的月投入；显示金额保留两位小数，按显示金额实际投入可能产生少量差额。'))

    rows = result["yearly_data"]
    st.subheader(L('Portfolio Growth / 资产增长'))
    st.line_chart({
        L('Year'): [row["year"] for row in rows],
        L('Total Contributions'): [row["total_contributions"] for row in rows],
        L('Portfolio Value'): [row["portfolio_value"] for row in rows],
        L('Target Value'): [target for row in rows],
    }, x=L('Year'), y=[L('Total Contributions'), L('Portfolio Value'), L('Target Value')],
        x_label=L('Year'), y_label=L('Value (¥)'), height=360, width="stretch")
    st.subheader(L('Year-by-Year Table / 逐年明细'))
    st.dataframe({
        L('Year'): [row["year"] for row in rows],
        L('Total Contributions'): [f"¥{row['total_contributions']:,.2f}" for row in rows],
        L('Portfolio Value'): [f"¥{row['portfolio_value']:,.2f}" for row in rows],
        L('Remaining Gap to Target'): [f"¥{row['remaining_gap']:,.2f}" for row in rows],
    }, hide_index=True, width="stretch")
    st.subheader(L('Financial Insight / 结果解读'))
    if monthly == 0:
        st.write(L('在当前假设下，初始本金 ¥{v0:,.2f} 在 {v1} 年后的模拟资产为 ¥{v2:,.2f}，已达到或超过目标 ¥{v3:,.2f}，无需额外月投入。', v0=principal, v1=years, v2=result['final_portfolio_value'], v3=target))
    else:
        st.write(L('在当前假设下，要在 {v0} 年后达到 ¥{v1:,.2f}，初始本金 ¥{v2:,.2f} 时，每月大约需要投入 ¥{v3:,.2f}。', v0=years, v1=target, v2=principal, v3=monthly))
    render_goal_sensitivity(target, principal, rate_percent / 100, years)

    with st.expander(L('Module Assumptions / 模块假设'), expanded=True):
        st.caption(L('Monthly compounding / 月度复利；与 DCA 一致，月收益率 = 年化收益率 ÷ 12，每月先增长再投入。'))


def main() -> None:
    st.set_page_config(page_title="Vexa — Intelligent Financial Analysis & Decision Support Platform", page_icon="📈")
    apply_polish()
    language = st.selectbox(tr("app_language", current_language()), ["English", "中文"], key="global_language")
    t = lambda key: tr(key, language)
    with st.container(key="vexa_polish_hero"):
        st.title("Vexa")
        st.markdown("**" + t("app_tagline") + "**")
        st.write(t("app_description"))
    st.caption(t("app_development"))
    st.caption(t("ev_disclaimer"))
    st.subheader(t("app_modules"))
    module_ids = ["compound_interest", "dca", "goal_planner", "portfolio_analytics"]
    for offset in (0, 2):
        for column, module in zip(st.columns(2), module_ids[offset:offset + 2]):
            with column.container(border=True, key="vexa_polish_portfolio" if module == "portfolio_analytics" else "vexa_polish_module_" + module):
                if module == "portfolio_analytics":
                    with st.container(key="vexa_polish_featured"):
                        st.markdown("核心模块" if language == "中文" else "Featured")
                st.markdown("**" + t("module_" + module) + "**")
                st.write(t("module_" + module + "_description"))
    st.caption(t("app_portfolio_note"))
    # Tab display labels change; the selected module identity does not.
    selected = st.session_state.get("module_tabs")
    for module in module_ids:
        if selected in [tr("module_" + module, lang) for lang in ("English", "中文")]:
            st.session_state["selected_module"] = module
    module = st.session_state.get("selected_module", "compound_interest")
    labels = [t("module_" + key) for key in module_ids]
    st.session_state["module_tabs"] = t("module_" + module)
    tabs = st.tabs(labels, default=t("module_" + module), key="module_tabs", on_change="rerun")
    for tab, render in zip(tabs, [render_compound_interest, render_dca, render_goal_planner, render_portfolio_analytics]):
        with tab:
            render()
    st.divider()
    with st.expander(t("app_assumptions_title"), expanded=True):
        st.markdown(t("app_assumptions"))


if __name__ == "__main__":
    main()
