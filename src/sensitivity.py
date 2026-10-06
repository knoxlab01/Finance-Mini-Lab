"""Goal sensitivity under fixed monthly-compounding assumptions."""
from src.goal_planner import calculate_goal_plan
from src.scenario import calculate_scenarios


def calculate_goal_sensitivity(target_value, initial_principal, annual_rate, years):
    """Reuse Goal Planner unchanged; deltas are scenario minus base monthly input.

    Clamp horizons to 1–1000 years and deduplicate. Obtain rate assumptions from
    Scenario Analysis with a zero-year dummy projection, without changing it.
    Each alternate plan can fail independently without hiding the base plan.
    """
    base = calculate_goal_plan(target_value, initial_principal, annual_rate, years)
    base_monthly = base["required_monthly_contribution"]
    years = int(years)

    def evaluate(period, rate):
        try:
            monthly = (base_monthly if period == years and rate == annual_rate else
                       calculate_goal_plan(target_value, initial_principal, rate, period)["required_monthly_contribution"])
            return {"monthly": monthly, "difference": monthly - base_monthly, "error": None}
        except (ValueError, OverflowError) as error:
            return {"monthly": None, "difference": None, "error": str(error)}

    time_rows = [{"years": period, "is_base": period == years, **evaluate(period, annual_rate)}
                 for period in sorted({max(1, years - 5), years, min(1000, years + 5)})]
    rate_rows = [{"name": row["name"], "annual_rate": row["annual_rate"],
                  "adjusted": row["adjusted"], **evaluate(years, row["annual_rate"])}
                 for row in calculate_scenarios(0, annual_rate, 0)]
    return {"base_monthly": base_monthly, "time": time_rows, "return": rate_rows}
