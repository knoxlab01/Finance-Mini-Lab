"""Independent state/flags/transition, with explicit confirmation persistence."""
from collections.abc import Mapping
import operator
import numpy as np
from .spec import SPEC, CORE

OPS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq}


def matches(rule, values):
    if isinstance(rule, Mapping):
        if "all" in rule:
            return all(matches(item, values) for item in rule["all"])
        return any(matches(item, values) for item in rule["any"])
    key, op, target = rule
    value = values.get(key)
    return value is not None and bool(np.isfinite(value)) and bool(OPS[op](value, target))


def interpret(snapshot, metrics, history=()):
    scores = snapshot["scores"]
    values = dict(scores, risk_breadth_score=metrics.get("risk_breadth_score"))
    support = [scores[k] for k in CORE[1:]]
    values["growth_support_gap"] = scores[CORE[0]] - float(np.median(support)) if scores.get(CORE[0]) is not None and all(v is not None for v in support) else None
    values["is_stressed"] = matches(SPEC["primary_rules"]["Stressed"], values)
    values["is_growth_led"] = matches(SPEC["primary_rules"]["Growth-Led"], values)
    candidates = [name for name in SPEC["primary_precedence"] if matches(SPEC["primary_rules"][name], values)]
    candidate = candidates[0] if candidates else SPEC["primary_default"]
    declines = snapshot["decline3"]
    values.update({"decline3:" + k: v for k, v in declines.items()})
    available = [x for x in declines.values() if x is not None]
    counts = SPEC["change_counts"]
    values["core_declines_ge5"] = sum(v >= counts["minor_decline"] for v in available) if available else None
    values["core_declines_ge10"] = sum(v >= counts["major_decline"] for v in available) if available else None
    flags = [name for name, rule in SPEC["flags"].items() if matches(rule, values)]
    transition_cfg = SPEC["transitions"]
    old = history[-transition_cfg["recovery_intervals"]]["scores"] if len(history) >= transition_cfg["recovery_intervals"] else {}
    improvements = {k: scores[k] - old[k] if scores.get(k) is not None and old.get(k) is not None else None for k in CORE}
    values.update({"improve2:" + k: v for k, v in improvements.items()})
    available_improvements = [x for x in improvements.values() if x is not None]
    values["core_improvements2_ge5"] = sum(v >= counts["recovery_improvement"] for v in available_improvements) if available_improvements else None
    values["prior_adversity"] = any(row["candidate_state"] == "Stressed" or row["confirmed_state"] == "Stressed" or row["scores"].get("Structural Resilience") is not None and row["scores"]["Structural Resilience"] < transition_cfg["prior_adversity_resilience_below"] for row in history[-transition_cfg["prior_evaluations"]:])
    transition = next((name for name in transition_cfg["precedence"] if matches(transition_cfg[name], values)), transition_cfg["default"])
    h = SPEC["hysteresis"]
    previous = history[-1] if history else None
    streak = previous["candidate_streak"] + 1 if previous and previous["candidate_state"] == candidate else 1
    confirmed = previous["confirmed_state"] if previous else h["initial_confirmed"]
    initialized = previous.get("confirmation_initialized", False) if previous else False
    severe = matches(h["severe_stress"], values)
    if severe:
        confirmed, initialized = "Stressed", True
    elif streak >= h["confirm_consecutive"]:
        if confirmed != "Stressed" or candidate == "Stressed" or scores.get("Downside Stability") is not None and scores["Downside Stability"] > h["stress_exit"]["current_downside_stability_above"]:
            confirmed, initialized = candidate, True
    return dict(candidate_state=candidate, confirmed_state=confirmed, candidate_matches=candidates,
                flags=flags, transition=transition, severe_stress=severe, candidate_streak=streak,
                confirmation_initialized=initialized, state_changed=bool(previous and previous["confirmed_state"] != confirmed),
                transition_evidence_available=all(v is not None for v in declines.values()),
                change_evidence=dict(decline3=declines, improvement2=improvements))
