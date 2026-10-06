"""Annual-compounding sensitivity analysis; educational simulation, not a forecast."""

from math import isfinite, nextafter

from src.compound_interest import calculate_future_value


def calculate_scenarios(principal: float, base_rate: float, years: int) -> list[dict]:
    """Return three named scenarios. Rates are decimals; contributions are absent.

    Normally use +/- 0.03 (three percentage points). If the conservative rate
    reaches -1, use the midpoint between -1 and the base rate instead. Each
    overflowing scenario is unavailable independently of the other scenarios.
    """
    if not all(isfinite(value) for value in (principal, base_rate, years)):
        raise ValueError("请输入有限数字。")
    if isinstance(years, bool) or not isinstance(years, int) or not 0 <= years <= 1000:
        raise ValueError("投资年限须为 0–1000 的整数。")
    calculate_future_value(principal, base_rate, 0)  # Reuse core validation.
    conservative = base_rate - 0.03
    adjusted = conservative <= -1
    if adjusted:
        conservative = max(nextafter(-1.0, 0.0), -1 + (base_rate + 1) / 2)
    scenarios = []
    for name, rate in [
        ("Conservative / 保守", conservative),
        ("Base / 基准", base_rate),
        ("Optimistic / 乐观", base_rate + 0.03),
    ]:
        row = {"name": name, "annual_rate": rate, "adjusted": adjusted and not scenarios,
               "years": list(range(years + 1)), "values": None,
               "future_value": None, "investment_growth": None}
        try:
            values = [calculate_future_value(principal, rate, year) for year in row["years"]]
            if not all(isfinite(value) for value in values):
                raise OverflowError
            row.update(values=values, future_value=values[-1], investment_growth=values[-1] - principal)
        except OverflowError:
            pass  # UI displays unavailable results, never fabricated zero values.
        scenarios.append(row)
    return scenarios
