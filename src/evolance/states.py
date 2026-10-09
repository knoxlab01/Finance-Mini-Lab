"""Ordered, deterministic rules; all matches and evidence are retained."""
import math
from .config import Calibration

LABELS_ZH = {
    "Balanced Growth": "平衡增长", "Growth-Dominant": "增长主导", "Fragile Growth": "脆弱增长",
    "Concentration Pressure": "集中压力", "Defensive Imbalance": "防御失衡",
    "Inefficient Risk": "低效风险", "Stress State": "压力状态", "Transitional Recovery": "转化恢复",
    "Mixed / Unclassified": "混合 / 未分类", "Insufficient Evidence": "证据不足",
}


def classify_state(snapshot, previous=None, config=None):
    cfg = config or Calibration()
    t, s = cfg.thresholds, snapshot["scores"]
    if any(s.get(k) is None or not math.isfinite(s[k]) for k in ("Growth", "Stability", "Diversification", "Efficiency")):
        return dict(state="Insufficient Evidence", matches=[], reason="Undefined core dimension; no imputation")
    if any(v is not None and (not math.isfinite(v) or not 0 <= v <= 100) for v in s.values()):
        raise ValueError("Scores must be finite and in [0,100], or None")
    g, st, d, e = (s[k] for k in ("Growth", "Stability", "Diversification", "Efficiency"))
    a = s.get("Adaptability")
    recovery = False
    if previous and previous.get("state") in ("Stress State", "Transitional Recovery") and a is not None:
        old = previous["scores"]
        recovery = st >= t["recovery_stability"] and all(old.get(k) is not None and s[k] - old[k] >= t["recovery_gain"] for k in ("Stability", "Efficiency", "Adaptability")) and g > old["Growth"]
    rules = {
        "Stress State": a is not None and a < t["adapt_low"] and st < t["low"] and len(snapshot.get("deteriorating", [])) >= t["stress_count"],
        "Fragile Growth": g >= t["growth_high"] and (st < t["low"] or d < t["low"]),
        "Concentration Pressure": d < t["div_very_low"],
        "Inefficient Risk": st < t["low"] and e < t["low"],
        "Transitional Recovery": recovery,
        "Growth-Dominant": g >= t["growth_very_high"] and g - min(st, d, e) >= t["growth_gap"],
        "Defensive Imbalance": st >= t["high"] and (g < t["low"] or e < t["low"]),
        "Balanced Growth": g >= t["growth_high"] and st >= t["support_min"] and e >= t["support_min"] and d >= t["div_min"],
    }
    matches = [name for name in cfg.precedence if rules[name]]
    state = matches[0] if matches else "Mixed / Unclassified"
    reason = "; ".join(f"{k}={v:.1f}" if v is not None else f"{k}=N/A" for k, v in s.items())
    reason += "; deteriorating=" + ",".join(snapshot.get("deteriorating", []))
    return dict(state=state, matches=matches, reason=reason)
