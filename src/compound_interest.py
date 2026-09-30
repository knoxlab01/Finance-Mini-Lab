"""复利计算：假设收益按年复投，期间没有追加投入或取款。"""


def calculate_future_value(
    principal: float, annual_rate: float, years: float
) -> float:
    """返回未来价值；annual_rate 使用小数形式，例如 8% 写作 0.08。

    本金和年限必须非负，年化收益率必须大于 -1。
    参数违反这些约束时抛出 ValueError。
    """
    if principal < 0:
        raise ValueError("principal 不能为负")
    if annual_rate <= -1:
        raise ValueError("annual_rate 必须大于 -1")
    if years < 0:
        raise ValueError("years 不能为负")

    return principal * (1 + annual_rate) ** years
