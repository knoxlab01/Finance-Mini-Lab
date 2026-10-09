"""Separate ex-post evaluator and transparent baselines; never tunes the spec."""
import numpy as np
import pandas as pd
from src.portfolio_analysis import validate_weights
from src.portfolio_metrics import cumulative_return, maximum_drawdown
from .spec import SPEC


def traditional_direction(metrics):
    r, sharpe = metrics["absolute_return"], metrics["sharpe"]
    if sharpe is not None:
        if r > 0 and sharpe > 0:
            return "Bullish"
        if r < 0 and sharpe < 0:
            return "Bearish"
    return "Neutral / Uncertain"


def evaluate_outcomes(prices, weights, signals):
    w = validate_weights(list(weights), list(weights.values()))
    returns = prices[list(weights)].pct_change(fill_method=None).iloc[1:].dot(w)
    records = []
    for row in signals:
        for months, forecast in row["outlooks"].items():
            horizon = SPEC["forward"]["outcome_sessions"][months]
            future = returns.loc[returns.index > pd.Timestamp(row["available_at"])].iloc[:horizon]
            complete = len(future) == horizon
            records.append(dict(date=row["date"], months=int(months), complete=complete, observations=len(future),
                                direction=forecast["direction"], confidence=forecast["confidence"],
                                mc_only_direction=forecast["direction"], mc_only_confidence=forecast["mc_only_confidence"],
                                traditional_direction=traditional_direction(row["metrics"]),
                                state=row["confirmed_state"], transition=row["transition"], flags=row["flags"],
                                forward_return=cumulative_return(future) if complete else None,
                                forward_drawdown=maximum_drawdown(future) if complete else None,
                                probability_up=forecast["probability_up"], p10=forecast["p10"], p50=forecast["p50"], p90=forecast["p90"]))
    return records


def _stats(records, direction_key="direction"):
    complete = [r for r in records if r["complete"]]
    directional = [r for r in complete if r[direction_key] != "Neutral / Uncertain"]
    hits = sum(("Bullish" in r[direction_key] and r["forward_return"] > 0) or ("Bearish" in r[direction_key] and r["forward_return"] < 0) for r in directional)
    def mean(key):
        return float(np.mean([r[key] for r in complete])) if complete else None
    return dict(signals=len(records), complete=len(complete), censored=len(records)-len(complete),
                directional_count=len(directional), directional_hits=hits,
                directional_hit_rate=hits/len(directional) if directional else None,
                neutral_coverage=sum(r[direction_key] == "Neutral / Uncertain" for r in records)/len(records) if records else None,
                complete_neutral_coverage=sum(r[direction_key] == "Neutral / Uncertain" for r in complete)/len(complete) if complete else None,
                mean_forward_return=mean("forward_return"), mean_forward_drawdown=mean("forward_drawdown"))


def summarize(records):
    output = {}
    for months in SPEC["forward"]["horizons_months"]:
        data = [r for r in records if r["months"] == months]
        result = dict(evolance=_stats(data), traditional=_stats(data,"traditional_direction"), mc_only=_stats(data,"mc_only_direction"))
        for field in ["direction", "state", "transition", "confidence", "mc_only_confidence"]:
            keys = SPEC["confidence"]["levels"] if "confidence" in field else sorted({r[field] for r in data})
            result["by_"+field] = {key:_stats([r for r in data if r[field]==key]) for key in keys}
        result["by_flag"] = {flag:{"active":_stats([r for r in data if flag in r["flags"]]),
                                  "inactive":_stats([r for r in data if flag not in r["flags"]])} for flag in SPEC["flags"]}
        high, low = result["by_confidence"]["High"], result["by_confidence"]["Low"]
        result["high_vs_low"] = dict(high_complete=high["complete"], low_complete=low["complete"],
                                      hit_rate_difference=high["directional_hit_rate"]-low["directional_hit_rate"] if high["directional_hit_rate"] is not None and low["directional_hit_rate"] is not None else None,
                                      conclusion="Descriptive only; unavailable groups cannot establish confidence calibration")
        output[str(months)] = result
    return output
