"""Finance Mini Lab 的 Streamlit 网页入口。"""

from math import isfinite

import streamlit as st

from src.compound_interest import calculate_future_value


def main() -> None:
    st.set_page_config(page_title="Finance Mini Lab v0.1", page_icon="📈")
    st.title("Finance Mini Lab v0.1")
    st.caption("输入本金、年化收益率和投资年限，观察资产逐年变化。")

    with st.form("compound_interest"):
        principal = st.number_input("principal 本金 (¥)", value=10000.0, step=100.0, format="%.2f")
        rate_percent = st.number_input("annual return rate (%) 年化收益率", value=8.0, step=0.1, format="%.2f")
        years = st.number_input(
            "years 投资年限", value=10, step=1, max_value=1000,
            help="输入 0–1000 的整数年；0 年表示尚未开始投资。",
        )
        submitted = st.form_submit_button("Calculate", type="primary")

    if not submitted:
        st.info("填写参数后点击 Calculate。收益率输入 8 表示 8%。")
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

    st.subheader("Calculation Results")
    left, right = st.columns(2)
    left.metric("Initial Investment", f"¥{principal:,.2f}")
    right.metric("Annual Return", f"{rate_percent:.2f}%")
    left.metric("Investment Period", f"{years} years")
    right.metric("Future Value", f"¥{future_value:,.2f}")

    st.subheader("Growth Chart")
    data = {"Year": chart_years, "Portfolio Value": values}
    if years == 0:
        # 只有一个数据点时，散点图可明确显示第 0 年本金。
        st.scatter_chart(data, x="Year", y="Portfolio Value", x_label="Year", y_label="Portfolio Value")
        st.caption("投资期限为 0 年，图中仅显示起始本金。")
    else:
        st.line_chart(data, x="Year", y="Portfolio Value", x_label="Year", y_label="Portfolio Value")
    st.caption("假设收益率固定、每年复利、不追加投入或取款，不计税费和通胀。")


if __name__ == "__main__":
    main()
