"""Frozen anchors and directional resilience; no sample-dependent calibration."""
import numpy as np
from .spec import SPEC, CORE


def normalize(value, key):
    if value is None or not np.isfinite(value):
        return None
    x, y = zip(*SPEC["anchors"][key])
    return float(np.interp(value, x, y))


def score_evidence(metrics, history=()):
    scores, components, missing = {}, {}, []
    for dimension in CORE:
        parts = {}
        for key in SPEC["dimension_weights"][dimension]:
            value = metrics.get(key)
            parts[key] = value if key == "risk_breadth_score" and value is not None and np.isfinite(value) else normalize(value, key) if key != "risk_breadth_score" else None
        components[dimension] = parts
        absent = [key for key, value in parts.items() if value is None]
        missing.extend(absent)
        scores[dimension] = None if absent else float(sum(parts[k] * weight for k, weight in SPEC["dimension_weights"][dimension].items()))
    lag = SPEC["resilience"]["lag_evaluations"]
    old = history[-lag]["scores"] if len(history) >= lag else {}
    declines = {key: max(0., old[key] - scores[key]) if old.get(key) is not None and scores[key] is not None else None for key in CORE}
    parts = {key: normalize(value, "deterioration") for key, value in declines.items()}
    components["Structural Resilience"] = parts
    scores["Structural Resilience"] = None if any(value is None for value in parts.values()) else float(sum(parts[k] * w for k, w in SPEC["dimension_weights"]["Structural Resilience"].items()))
    if scores["Structural Resilience"] is None:
        missing.append("Structural Resilience: requires four complete core scores now and three evaluations earlier")
    if any(v is not None and not 0 <= v <= 100 for v in scores.values()):
        raise ValueError("Scores must lie within 0–100")
    return dict(scores=scores, components=components, decline3=declines, missing=missing)
