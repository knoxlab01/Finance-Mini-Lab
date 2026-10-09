"""Unvalidated research calibrations; every scoring/classification cutoff lives here."""
from dataclasses import dataclass, field
import math


def _anchors():
    return {
        "cagr": ((-.30, 0), (-.10, 20), (0, 40), (.08, 60), (.15, 80), (.30, 100)),
        "relative_return": ((-.20, 0), (-.05, 25), (0, 50), (.05, 75), (.20, 100)),
        "trend": ((-.25, 0), (-.05, 25), (0, 40), (.05, 60), (.15, 85), (.30, 100)),
        "volatility": ((0, 100), (.10, 85), (.20, 60), (.30, 35), (.50, 0)),
        "drawdown": ((0, 100), (.10, 90), (.20, 70), (.30, 50), (.40, 30), (.60, 0)),
        "negative_frequency": ((0, 100), (.30, 85), (.45, 60), (.50, 40), (.60, 10), (1, 0)),
        "correlation": ((-1, 100), (0, 100), (.30, 85), (.60, 55), (.80, 25), (1, 0)),
        "max_weight": ((0, 100), (.20, 100), (.34, 85), (.50, 60), (.75, 25), (1, 0)),
        "effective_holdings": ((1, 0), (2, 40), (3, 65), (5, 85), (10, 100)),
        "sharpe": ((-1, 0), (0, 25), (.50, 50), (1, 75), (1.50, 90), (2, 100)),
        "return_drawdown": ((-2, 0), (-1, 10), (0, 30), (.50, 55), (1, 75), (2, 90), (3, 100)),
        "relative_sharpe": ((-1, 0), (-.50, 25), (0, 50), (.50, 75), (1, 100)),
        "vol_change": ((-.10, 100), (0, 90), (.02, 65), (.05, 30), (.10, 0)),
        "corr_change": ((-.20, 100), (0, 90), (.05, 65), (.15, 30), (.30, 0)),
        "dd_change": ((-.20, 100), (0, 90), (.05, 65), (.10, 30), (.20, 0)),
        "score_instability": ((0, 100), (5, 85), (10, 60), (20, 25), (35, 0)),
    }


def _weights():
    return {
        "Growth": {"cagr": .40, "relative_return": .35, "trend": .25},
        "Stability": {"volatility": .35, "drawdown": .40, "negative_frequency": .25},
        "Diversification": {"correlation": .45, "max_weight": .35, "effective_holdings": .20},
        "Efficiency": {"sharpe": .45, "return_drawdown": .30, "relative_sharpe": .25},
        "Adaptability": {"vol_change": .30, "corr_change": .25, "dd_change": .25, "score_instability": .20},
    }


@dataclass
class Calibration:
    lookback: int = 252
    trend_days: int = 126
    frequency: str = "monthly"
    risk_free_rate: float = .04
    annual_sessions: int = 252
    forward_days: int = 63
    anchors: dict = field(default_factory=_anchors)
    weights: dict = field(default_factory=_weights)
    thresholds: dict = field(default_factory=lambda: {
        "growth_high": 65, "growth_very_high": 80, "low": 40, "high": 75,
        "div_very_low": 30, "support_min": 55, "div_min": 45,
        "growth_gap": 20, "deterioration": 5, "stress_count": 2,
        "adapt_low": 40, "recovery_gain": 5, "recovery_stability": 40,
        "major_score_drop": 15, "case_return_strong": .10,
        "case_low_vol": .10, "case_weak_growth": 45,
        "baseline_cagr": 0, "baseline_sharpe": 0, "baseline_vol": .25,
        "profile_difference": 10,
    })
    precedence: tuple = (
        "Stress State", "Fragile Growth", "Concentration Pressure", "Inefficient Risk",
        "Transitional Recovery", "Growth-Dominant", "Defensive Imbalance", "Balanced Growth",
    )

    def __post_init__(self):
        if self.lookback not in (126, 252, 504) or not 2 <= self.trend_days <= self.lookback:
            raise ValueError("Use a 126/252/504-return window and a trend no longer than the window")
        if self.frequency not in ("monthly", "quarterly") or self.annual_sessions != 252:
            raise ValueError("Frequency must be monthly/quarterly; prototype uses 252 sessions")
        if not math.isfinite(self.risk_free_rate) or self.risk_free_rate <= -1 or self.forward_days < 1:
            raise ValueError("Invalid risk-free rate or forward horizon")
        if set(self.weights) != set(_weights()) or set(self.anchors) != set(_anchors()):
            raise ValueError("Calibration must retain all dimensions and components")
        if set(self.thresholds) != set(Calibration.__dataclass_fields__["thresholds"].default_factory()):
            raise ValueError("Missing state/validation thresholds")
        if not all(math.isfinite(x) for x in self.thresholds.values()):
            raise ValueError("Thresholds must be finite")
        if set(self.precedence) != set(Calibration.__dataclass_fields__["precedence"].default) or len(self.precedence) != 8:
            raise ValueError("Each state must occur once in precedence")
        for dimension, parts in self.weights.items():
            if set(parts) != set(_weights()[dimension]) or any(not math.isfinite(v) or v < 0 for v in parts.values()) or not math.isclose(sum(parts.values()), 1):
                raise ValueError("Component weights must be nonnegative and sum to one")
        for points in self.anchors.values():
            if len(points) < 2 or any(not math.isfinite(x) or not math.isfinite(y) or not 0 <= y <= 100 for x, y in points):
                raise ValueError("Invalid piecewise anchors")
            if any(a[0] >= b[0] for a, b in zip(points, points[1:])):
                raise ValueError("Anchor x values must strictly increase")
