"""DCA 固定收益率模拟：Finance Mini Lab v0.2.0，并非真实市场回报预测。"""

from math import isfinite


def calculate_dca(
    initial_principal: float,
    monthly_contribution: float,
    annual_rate: float,
    years: int,
) -> dict:
    """模拟月末定投，返回汇总及包含 Year 0 的逐年数据。

    annual_rate 使用小数（8% = 0.08），月收益率 = annual_rate / 12。
    每月先增长，再加入当月投入；输入年限为 0–1000 的整数。
    total_contributions 包括初始本金和所有月末投入。
    total_return 是投资收益 / 累计投入的小数值，不是年化或资金加权收益率；
    累计投入为 0 时返回 None。不计税费、通胀、手续费或市场波动。
    """
    try:
        finite = all(isfinite(value) for value in (
            initial_principal, monthly_contribution, annual_rate, years,
        ))
    except (TypeError, OverflowError):
        raise ValueError("请输入有效的有限数字。") from None
    if not finite:
        raise ValueError("请输入有限数字，不能使用 nan 或 inf。")
    if initial_principal < 0:
        raise ValueError("初始本金不能为负。")
    if monthly_contribution < 0:
        raise ValueError("每月投入不能为负。")
    if annual_rate <= -1:
        raise ValueError("年化收益率必须大于 -100%。")
    if years < 0:
        raise ValueError("投资年限不能为负。")
    if years != int(years) or years > 1000:
        raise ValueError("投资年限必须为 0–1000 的整数年。")

    years = int(years)
    monthly_rate = annual_rate / 12
    portfolio_value = initial_principal
    total_contributions = initial_principal
    yearly_data = [{
        "year": 0,
        "total_contributions": total_contributions,
        "portfolio_value": portfolio_value,
        "investment_growth": 0.0,
    }]
    for month in range(1, years * 12 + 1):
        # 固定月收益率模拟：先增长，后加入当月投入（月末投入）。
        portfolio_value = portfolio_value * (1 + monthly_rate) + monthly_contribution
        total_contributions = initial_principal + monthly_contribution * month
        if not isfinite(portfolio_value) or not isfinite(total_contributions):
            raise OverflowError("计算结果超出支持范围，请减小输入数值。")
        if month % 12 == 0:
            yearly_data.append({
                "year": month // 12,
                "total_contributions": total_contributions,
                "portfolio_value": portfolio_value,
                "investment_growth": portfolio_value - total_contributions,
            })

    growth = portfolio_value - total_contributions
    total_return = growth / total_contributions if total_contributions > 0 else None
    if total_return is not None and not isfinite(total_return):
        raise OverflowError("收益率超出支持范围，请调整输入数值。")
    return {
        "final_portfolio_value": portfolio_value,
        "total_contributions": total_contributions,
        "investment_growth": growth,
        "total_return": total_return,
        "yearly_data": yearly_data,
    }
