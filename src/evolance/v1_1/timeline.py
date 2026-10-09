"""Signal generation only. Forward realized observations never enter this module."""
import numpy as np
import pandas as pd
from src.portfolio_analysis import validate_weights
from .spec import SPEC, SPEC_SHA256, SPEC_VERSION, load_spec
from .metrics import evidence
from .scoring import score_evidence
from .states import interpret
from .outlook import forward_distributions, interpret_outlook


def walk_forward(prices, weights, benchmark="SPY", *, synthetic=True, as_of=None, lookback=252):
    load_spec()  # Detect any on-disk change before every study, not only import.
    allowed = (SPEC["history"]["lookback"], *SPEC["history"]["sensitivity_lookbacks"])
    if isinstance(lookback, bool) or lookback not in allowed:
        raise ValueError("Only frozen 252 or explicitly labeled 126/504 sensitivity windows supported")
    if not isinstance(prices, pd.DataFrame) or not isinstance(prices.index, pd.DatetimeIndex) or prices.empty:
        raise ValueError("Nonempty price DataFrame with dates required")
    if prices.index.tz is not None or prices.index.hasnans or prices.index.has_duplicates or not prices.index.is_monotonic_increasing or prices.columns.has_duplicates:
        raise ValueError("Sorted unique timezone-naive dates and unique columns required")
    validate_weights(list(weights), list(weights.values()))
    active_weights = {k:v for k,v in weights.items() if v > 0}
    needed = list(dict.fromkeys(list(active_weights) + [benchmark]))
    if not set(needed).issubset(prices.columns):
        raise ValueError("Missing holding or benchmark")
    cutoff = pd.Timestamp(as_of) if as_of is not None else prices.index[-1]
    if pd.isna(cutoff) or cutoff.tz is not None:
        raise ValueError("Invalid as_of")
    frame = prices.loc[prices.index <= cutoff, needed].astype(float)
    if len(frame) <= lookback:
        raise ValueError("Insufficient history: lookback+1 prices required")
    if not np.isfinite(frame.to_numpy()).all() or (frame <= 0).any().any():
        raise ValueError("NaN/nonfinite/nonpositive prices; no filling")
    if frame.index.to_series().diff().dt.days.max() > SPEC["history"]["max_gap_days"]:
        raise ValueError("Data gap exceeds seven days")
    periods = frame.index.to_period("M")
    rows = []
    for period in periods.unique():
        end = period.end_time.normalize()
        if end > cutoff.normalize():
            continue
        pos = np.flatnonzero(periods == period)[-1]
        if pos < lookback:
            continue
        window = frame.iloc[pos-lookback:pos+1]
        metrics, returns = evidence(window, active_weights, benchmark)
        scored = score_evidence(metrics, rows)
        interpretation = interpret(scored, metrics, rows)
        distributions = forward_distributions(returns)
        outlooks = {}
        for months, distribution in distributions.items():
            outlooks[str(months)] = {k:v for k,v in distribution.items() if k != "terminal_returns"}
            outlooks[str(months)].update(interpret_outlook(distribution, metrics, scored["scores"], interpretation, synthetic))
        row = dict(date=window.index[-1].isoformat(), available_at=end.isoformat(), window_start=window.index[0].isoformat(),
                   lookback=lookback, synthetic=synthetic, spec_version=SPEC_VERSION, spec_sha256=SPEC_SHA256,
                   metrics=metrics, **scored, **interpretation, outlooks=outlooks)
        previous = rows[-1] if rows else None
        row["state_start"] = row["date"] if not previous or row["state_changed"] else previous["state_start"]
        row["state_duration_observations"] = 1 if not previous or row["state_changed"] else previous["state_duration_observations"] + 1
        rows.append(row)
    if not rows:
        raise ValueError("No completed month with sufficient history")
    # Only final distributions retained; regenerate any historical distribution
    # from its window, seed and immutable spec rather than storing huge arrays.
    return dict(rows=rows, latest_terminal_returns={str(m):d["terminal_returns"] for m,d in distributions.items()},
                spec_sha256=SPEC_SHA256, lookback=lookback)


def state_spells(rows):
    spells = []
    for row in rows:
        if not spells or row["confirmed_state"] != spells[-1]["state"]:
            if spells:
                spells[-1].update(end=row["date"], right_censored=False)
            spells.append(dict(state=row["confirmed_state"], start=row["date"], end=row["date"], observations=0, right_censored=True))
        spells[-1]["observations"] += 1
        spells[-1]["end"] = row["date"]
    for spell in spells:
        spell["calendar_days"] = (pd.Timestamp(spell["end"]) - pd.Timestamp(spell["start"])).days
    return spells
