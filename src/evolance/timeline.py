"""Past-only monthly/quarterly snapshots, retaining traditional evidence."""
import json
import numpy as np
import pandas as pd
from src.portfolio_metrics import calculate_metrics, cumulative_return
from src.portfolio_analysis import validate_weights
from .config import Calibration
from .scoring import score_snapshot, CORE
from .states import classify_state


def window_metrics(prices, assets, weights, benchmark, config):
    returns = prices.pct_change(fill_method=None).iloc[1:]
    p = returns[assets].dot(weights)
    b = returns[benchmark]
    pm = calculate_metrics(p, prices.index[0], prices.index[-1], config.risk_free_rate)
    bm = calculate_metrics(b, prices.index[0], prices.index[-1], config.risk_free_rate)
    pairs = returns[assets].corr().to_numpy()[np.triu_indices(len(assets), 1)]
    correlation = float(pairs.mean()) if len(pairs) and np.isfinite(pairs).all() else None
    dd = abs(pm["Maximum Drawdown"])
    sharpe, bsharpe = pm["Sharpe Ratio"], bm["Sharpe Ratio"]
    return {
        "cagr": pm["CAGR"], "trailing_return": pm["Cumulative Return"],
        "relative_return": pm["Cumulative Return"] - bm["Cumulative Return"],
        "trend": cumulative_return(p.iloc[-config.trend_days:]),
        "volatility": pm["Annualized Volatility"], "drawdown": dd,
        "negative_frequency": float((p < 0).mean()), "correlation": correlation,
        "max_weight": float(max(weights)), "hhi": float(np.square(weights).sum()),
        "effective_holdings": float(1 / np.square(weights).sum()), "holding_count": len(assets),
        "sharpe": sharpe, "return_drawdown": pm["CAGR"] / dd if dd > 1e-12 else None,
        "relative_sharpe": sharpe - bsharpe if sharpe is not None and bsharpe is not None else None,
        "benchmark_return": bm["Cumulative Return"], "benchmark_volatility": bm["Annualized Volatility"],
        "benchmark_sharpe": bsharpe,
    }


def rolling_analysis(prices, weights, benchmark="SPY", config=None, as_of=None):
    """weights is {ticker: weight}; all price dates must be synchronized.

    Only completed calendar months/quarters through as_of are evaluated, at
    their last observed date. as_of defaults to the final supplied date.
    Each window has lookback RETURNS (lookback+1 prices). No forward filling.
    Zero-weight holdings are excluded before correlation/concentration scoring.
    """
    cfg = config or Calibration()
    if not isinstance(prices, pd.DataFrame) or not isinstance(prices.index, pd.DatetimeIndex) or prices.empty:
        raise ValueError("Require a nonempty price DataFrame with DatetimeIndex")
    if prices.index.tz is not None or prices.index.hasnans or prices.index.has_duplicates or not prices.index.is_monotonic_increasing or prices.columns.has_duplicates:
        raise ValueError("Require sorted, unique, timezone-naive dates and unique columns")
    cutoff = pd.Timestamp(as_of) if as_of is not None else prices.index[-1]
    if pd.isna(cutoff) or cutoff.tz is not None:
        raise ValueError("Invalid as_of date")
    assets = list(weights)
    validated = validate_weights(assets, list(weights.values()))
    active = validated > 0
    assets, validated = [a for a, keep in zip(assets, active) if keep], validated[active]
    needed = list(dict.fromkeys(assets + [benchmark]))
    if not set(needed).issubset(prices.columns):
        raise ValueError("Missing asset or benchmark column")
    frame = prices.loc[prices.index <= cutoff, needed].astype(float)
    if len(frame) <= cfg.lookback:
        raise ValueError("Insufficient history: need lookback+1 aligned prices")
    if not np.isfinite(frame.to_numpy()).all() or (frame <= 0).any().any():
        raise ValueError("Missing/nonfinite/nonpositive prices; no silent imputation")
    if frame.index.to_series().diff().dt.days.max() > 7:
        raise ValueError("Price gaps exceed seven calendar days")
    periods = frame.index.to_period("M" if cfg.frequency == "monthly" else "Q")
    rows, previous = [], None
    for period in periods.unique():
        if period.end_time.normalize() > cutoff.normalize():
            continue
        position = np.flatnonzero(periods == period)[-1]
        if position < cfg.lookback:
            continue
        window = frame.iloc[position - cfg.lookback:position + 1]
        metrics = window_metrics(window, assets, validated, benchmark, cfg)
        snapshot = score_snapshot(metrics, previous["metrics"] if previous else None,
                                  previous["scores"] if previous else None, cfg)
        classification = classify_state(snapshot, previous, cfg)
        row = dict(date=window.index[-1], window_start=window.index[0],
                   period_end=period.end_time.normalize(), **metrics, **snapshot["scores"],
                   state=classification["state"], reason=classification["reason"],
                   matches=json.dumps(classification["matches"]),
                   deteriorating=json.dumps(snapshot["deteriorating"]),
                   missing=json.dumps(snapshot["missing"]),
                   components=json.dumps(snapshot["components"], allow_nan=False))
        rows.append(row)
        previous = dict(metrics=metrics, scores=snapshot["scores"], state=classification["state"])
    if not rows:
        raise ValueError("No completed evaluation period with sufficient history")
    result = pd.DataFrame(rows).set_index("date")
    result.attrs.update(lookback=cfg.lookback, frequency=cfg.frequency,
                        loss_proxy="negative daily-return frequency (not forward loss probability)",
                        source_metadata=prices.attrs.get("source_metadata", {}))
    return result


def summarize_timeline(timeline, config=None):
    """Durations are observed spans, not inferred daily state classifications."""
    cfg = config or Calibration()
    if timeline.empty:
        return dict(durations=[], transitions=[], most_common={}, major_deteriorations=[])
    durations, transitions, major = [], [], []
    start, state, count = timeline.index[0], timeline.iloc[0]["state"], 0
    for i, (date, row) in enumerate(timeline.iterrows()):
        if row["state"] != state:
            previous = timeline.iloc[i - 1]
            durations.append(dict(state=state, start=start.isoformat(), end=date.isoformat(),
                                  observations=count, calendar_days=(date - start).days, right_censored=False))
            event = dict(date=date.isoformat(), old=state, new=row["state"])
            transitions.append(event)
            drop = any(pd.notna(row[k]) and pd.notna(previous[k]) and previous[k] - row[k] >= cfg.thresholds["major_score_drop"] for k in CORE)
            if row["state"] == "Stress State" or drop:
                major.append(event)
            start, state, count = date, row["state"], 0
        count += 1
    end = timeline.index[-1]
    durations.append(dict(state=state, start=start.isoformat(), end=end.isoformat(),
                          observations=count, calendar_days=(end - start).days, right_censored=True))
    return dict(durations=durations, transitions=transitions,
                most_common={k: int(v) for k, v in timeline.state.value_counts().items()}, major_deteriorations=major)
