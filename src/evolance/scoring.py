"""Fixed piecewise mappings; unavailable evidence is never silently reweighted."""
import numpy as np
from .config import Calibration

CORE = ("Growth", "Stability", "Diversification", "Efficiency")


def normalize(value, points):
    if value is None or not np.isfinite(value):
        return None
    x, y = zip(*points)
    return float(np.interp(value, x, y))


def score_snapshot(metrics, previous_metrics=None, previous_scores=None, config=None):
    cfg = config or Calibration()
    values = dict(metrics)
    # One holding has no pair correlation: conservative explicit convention,
    # not an empirical correlation estimate. Constant multi-asset series stay N/A.
    if values.get("holding_count") == 1:
        values["correlation"] = 1.0
    components, scores, missing = {}, {}, []
    for dimension in CORE:
        parts = {key: normalize(values.get(key), cfg.anchors[key]) for key in cfg.weights[dimension]}
        components[dimension] = parts
        absent = [key for key, value in parts.items() if value is None]
        missing.extend(absent)
        scores[dimension] = None if absent else sum(parts[k] * w for k, w in cfg.weights[dimension].items())
    changes = {}
    deteriorating = []
    if previous_metrics is not None and previous_scores is not None:
        for component, key in [("vol_change", "volatility"), ("corr_change", "correlation"), ("dd_change", "drawdown")]:
            current, old = values.get(key), previous_metrics.get(key)
            if key == "correlation" and values.get("holding_count") == previous_metrics.get("holding_count") == 1:
                current = old = 1.0
            changes[component] = current - old if current is not None and old is not None and np.isfinite([current, old]).all() else None
        deltas = [scores[k] - previous_scores[k] for k in CORE if scores[k] is not None and previous_scores.get(k) is not None]
        changes["score_instability"] = float(np.mean(np.abs(deltas))) if len(deltas) == len(CORE) else None
        deteriorating = [k for k in CORE if scores[k] is not None and previous_scores.get(k) is not None and scores[k] - previous_scores[k] <= -cfg.thresholds["deterioration"]]
    parts = {key: normalize(changes.get(key), cfg.anchors[key]) for key in cfg.weights["Adaptability"]}
    components["Adaptability"] = parts
    scores["Adaptability"] = None if any(v is None for v in parts.values()) else sum(parts[k] * w for k, w in cfg.weights["Adaptability"].items())
    if scores["Adaptability"] is None:
        missing.append("Adaptability: prior complete evaluation required")
    return dict(scores=scores, components=components, changes=changes, missing=missing, deteriorating=deteriorating)
