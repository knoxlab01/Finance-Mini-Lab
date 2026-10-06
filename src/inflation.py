"""Fixed annual inflation discounting, expressed in starting-year purchasing power."""
from math import isfinite


def adjust_for_inflation(nominal_value: float, inflation_rate: float, years: float) -> dict:
    """Rates use decimals. Negative inflation (> -1) represents deflation.

    Reject unrepresentable results rather than silently showing a false zero.
    This adjusts a terminal balance, not the timing of individual cash flows.
    """
    if not all(isfinite(value) for value in (nominal_value, inflation_rate, years)):
        raise ValueError("通胀调整参数必须为有限数字。")
    if nominal_value < 0 or years < 0:
        raise ValueError("名义金额和投资年限不能为负。")
    if inflation_rate <= -1:
        raise ValueError("通胀率必须大于 -100%。")
    try:
        if nominal_value == 0 or years == 0 or inflation_rate == 0:
            real = nominal_value
        else:
            factor = (1 + inflation_rate) ** years
            if not isfinite(factor) or factor == 0:
                raise OverflowError
            real = nominal_value / factor
            if not isfinite(real) or real == 0:
                raise OverflowError
        loss = nominal_value - real
        if not isfinite(loss):
            raise OverflowError
    except (OverflowError, ZeroDivisionError):
        raise OverflowError("通胀调整结果超出支持范围，请调整通胀率或投资年限。") from None
    return {"nominal_value": nominal_value, "real_value": real, "purchasing_power_loss": loss}
