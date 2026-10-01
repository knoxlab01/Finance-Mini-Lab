"""目标规划：固定收益率、月末投入模拟，并非真实市场回报预测。"""

from math import isclose, isfinite

from src.dca import calculate_dca

# 回算验收：允许 max(目标值 × 1e-9, 0.000001) 的浮点误差。
REL_TOLERANCE = 1e-9
ABS_TOLERANCE = 1e-6


def calculate_goal_plan(
    target_value: float,
    initial_principal: float,
    annual_rate: float,
    years: int,
) -> dict:
    """求每月所需投入，返回 DCA 回算结果和目标差额。

    annual_rate 为小数；1–1000 整数年。复用 DCA 的月度复利、
    每月先增长后投入及输入校验。月投入保留完整精度，仅展示时舍入。
    若本金在期末已足够，则返回零月投入及真实模拟资产（可超过目标）。
    """
    try:
        finite = all(isfinite(v) for v in (target_value, initial_principal, annual_rate, years))
    except (TypeError, OverflowError):
        raise ValueError("请输入有效的有限数字。") from None
    if not finite:
        raise ValueError("请输入有限数字，不能使用 nan 或 inf。")
    if target_value <= 0:
        raise ValueError("目标资产必须大于 0。")
    if years <= 0:
        raise ValueError("投资年限必须大于 0。")

    baseline = calculate_dca(initial_principal, 0, annual_rate, years)
    baseline_value = baseline["final_portfolio_value"]
    if baseline_value >= target_value:
        monthly = 0.0
        projection = baseline
    else:
        # 线性叠加：每月投入 1 元的期末价值就是月投入的增长系数。
        # 零收益率时系数为总月数，与简单线性分摊完全一致。
        factor = (int(years) * 12 if annual_rate == 0 else
                  calculate_dca(0, 1, annual_rate, years)["final_portfolio_value"])
        monthly = (target_value - baseline_value) / factor
        if not isfinite(monthly):
            raise OverflowError("每月投入超出计算范围，请调整输入。")
        projection = calculate_dca(initial_principal, monthly, annual_rate, years)
        if not isclose(projection["final_portfolio_value"], target_value,
                       rel_tol=REL_TOLERANCE, abs_tol=ABS_TOLERANCE):
            raise ValueError("当前参数无法在允许的数值误差内完成规划，请调整输入。")

    return {
        **projection,
        "target_value": target_value,
        "required_monthly_contribution": monthly,
        "yearly_data": [
            {**row, "remaining_gap": max(0.0, target_value - row["portfolio_value"])}
            for row in projection["yearly_data"]
        ],
    }
