"""Ex-post outcomes and case search: never fed back into states or calibration."""
import numpy as np
import pandas as pd
from src.portfolio_metrics import cumulative_return, maximum_drawdown
from .config import Calibration


def subsequent_outcomes(prices, weights, timeline, horizon=63):
    if not isinstance(horizon, int) or horizon < 1:
        raise ValueError("Positive integer horizon required")
    returns = prices[list(weights)].pct_change(fill_method=None).iloc[1:].dot(list(weights.values()))
    rows = []
    for date in timeline.index:
        future = returns.loc[returns.index > date].iloc[:horizon]
        complete = len(future) == horizon
        rows.append(dict(date=date, forward_return=cumulative_return(future) if complete else np.nan,
                         forward_drawdown=maximum_drawdown(future) if complete else np.nan,
                         forward_observations=len(future), forward_complete=complete))
    return pd.DataFrame(rows).set_index("date")


def find_cases(timeline, outcomes, config=None):
    """Deterministic first qualifying COMPLETE outcome, not the best future result.

    Case D compares with a deliberately simple baseline: CAGR<=0 OR Sharpe<=0
    OR volatility>=25%. This is not a strong analyst/multivariate benchmark.
    A date earlier than this baseline is not evidence of predictive accuracy.
    """
    cfg = config or Calibration()
    t = cfg.thresholds
    table = timeline.join(outcomes)
    deteriorating = (table[["Stability", "Diversification", "Adaptability"]].diff() <= -t["deterioration"]).any(axis=1)
    baseline = (table.cagr <= t["baseline_cagr"]) | (table.sharpe <= t["baseline_sharpe"]) | (table.volatility >= t["baseline_vol"])
    structural = table.state.isin(["Fragile Growth", "Concentration Pressure", "Stress State", "Growth-Dominant"])
    new_structural = structural & (table.state != table.state.shift()) & table.state.shift().notna()
    masks = {
        "A": (table.trailing_return >= t["case_return_strong"]) & deteriorating,
        "B": (table.volatility < t["case_low_vol"]) & (table.Growth < t["case_weak_growth"]) & (table.state == "Defensive Imbalance"),
        "C": baseline & table.state.isin(["Stress State", "Inefficient Risk"]),
        "D": new_structural & ~baseline,
    }
    cases = {}
    for name, mask in masks.items():
        selected = table.loc[mask & table.forward_complete]
        if selected.empty:
            cases[name] = None
            continue
        date, row = selected.index[0], selected.iloc[0]
        case = dict(date=date.isoformat(), state=row.state,
                    metrics={k: float(row[k]) if pd.notna(row[k]) else None for k in ["cagr", "trailing_return", "volatility", "sharpe", "drawdown", "relative_return", "correlation", "max_weight"]},
                    scores={k: float(row[k]) if pd.notna(row[k]) else None for k in cfg.weights},
                    forward_return=float(row.forward_return), forward_drawdown=float(row.forward_drawdown),
                    forward_days=cfg.forward_days)
        if name == "D":
            later = table.loc[(table.index > date) & baseline]
            case["later_baseline_date"] = later.index[0].isoformat() if not later.empty else None
            case["lead_calendar_days"] = (later.index[0] - date).days if not later.empty else None
        cases[name] = case
    return cases
