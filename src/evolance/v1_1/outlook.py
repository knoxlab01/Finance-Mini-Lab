"""Quantitative direction from unchanged v0.3 paths; states affect explanation only."""
import numpy as np
from src.future_simulation import estimate_parameters, simulate_monte_carlo
from .spec import SPEC


def forward_distributions(returns):
    cfg = SPEC["forward"]
    parameters = estimate_parameters(returns)
    simulation = simulate_monte_carlo(parameters, cfg["initial_value"], 1, cfg["simulations"], cfg["seed"])
    results = {}
    for months in cfg["horizons_months"]:
        terminal = simulation["paths"][months] / cfg["initial_value"] - 1
        p10, p50, p90 = np.percentile(terminal, [10, 50, 90])
        results[months] = dict(months=months, p10=float(p10), p50=float(p50), p90=float(p90),
                               probability_up=float(np.mean(terminal > 0)), loss_probability=float(np.mean(terminal < 0)),
                               tie_probability=float(np.mean(terminal == 0)), terminal_returns=terminal,
                               parameters=parameters, simulations=cfg["simulations"], seed=cfg["seed"])
    return results


def directional_label(probability_up, median_return, months):
    if months not in SPEC["forward"]["horizons_months"] or not np.isfinite([probability_up, median_return]).all() or not 0 <= probability_up <= 1:
        raise ValueError("Valid probability, median and 6/12-month horizon required")
    c = SPEC["direction"]
    if abs(median_return) < c["median_abs_min"][str(months)]:
        return "Neutral / Uncertain"
    if median_return > 0:
        if probability_up >= c["strong_bullish_min"]:
            return "Strong Bullish"
        if probability_up >= c["bullish_min"]:
            return "Bullish"
    elif median_return < 0:
        if probability_up <= c["strong_bearish_max"]:
            return "Strong Bearish"
        if probability_up <= c["bearish_max"]:
            return "Bearish"
    return "Neutral / Uncertain"


def relative_outlook(metrics):
    active, ir = metrics.get("active_return"), metrics.get("information_ratio")
    c = SPEC["relative"]
    if active is not None and ir is not None and np.isfinite([active, ir]).all():
        if active > c["outperform_active_gt"] and ir >= c["outperform_ir_ge"]:
            return "Likely Outperform"
        if active < c["underperform_active_lt"] and ir <= c["underperform_ir_le"]:
            return "Likely Underperform"
    return "In Line / Uncertain"


def confidence(direction, relative, scores, interpretation, synthetic):
    c = SPEC["confidence"]
    levels = c["levels"]
    base = 2 if direction.startswith("Strong ") else 1 if direction in ("Bullish", "Bearish") else 0
    common = []
    if scores.get("Structural Resilience") is not None and scores["Structural Resilience"] < c["resilience_below"]:
        common.append("Structural Resilience <40")
    if c["concentration_flag"] in interpretation["flags"]:
        common.append(c["concentration_flag"])
    absolute_reasons = list(common)
    sign = "bullish" if "Bullish" in direction else "bearish" if "Bearish" in direction else "neutral"
    if (sign, interpretation["transition"]) in c["absolute_contradictions"]:
        absolute_reasons.append("Direction conflicts with transition")
    relative_reasons = list(common)
    if (relative, interpretation["transition"]) in c["relative_contradictions"]:
        relative_reasons.append("Relative outlook conflicts with transition")
    cap = levels.index(c["synthetic_cap"]) if synthetic else 2
    absolute_level = min(cap, max(0, base - len(absolute_reasons)))
    relative_level = 0 if relative == "In Line / Uncertain" else min(cap, max(0, base - len(relative_reasons)))
    if synthetic:
        absolute_reasons.append("Based on synthetic/demo data; confidence capped at Moderate")
        relative_reasons.append("Based on synthetic/demo data; confidence capped at Moderate")
    return dict(confidence=levels[absolute_level], relative_confidence=levels[relative_level],
                confidence_reasons=absolute_reasons, relative_confidence_reasons=relative_reasons,
                mc_only_confidence=levels[min(cap, base)])


def explain(direction, result, interpretation, conf, synthetic):
    months, state, transition = result["months"], interpretation["confirmed_state"], interpretation["transition"]
    if "Bullish" in direction:
        en = f"The model assigns a higher probability to a rise than a fall over {months} months."
        zh = f"模型判断未来 {months} 个月上涨概率高于下跌概率。"
    elif "Bearish" in direction:
        en = f"The model assigns a higher probability to a fall than a rise over {months} months."
        zh = f"模型判断未来 {months} 个月下跌概率高于上涨概率。"
    else:
        en = f"The {months}-month evidence does not support a material directional conclusion under the frozen guardrails."
        zh = f"按冻结规则，未来 {months} 个月证据不足以支持明确且有幅度的方向判断。"
    state_text = {
        ("Balanced Growth", "Stable"): ("Structural support is relatively balanced with no active deterioration transition.", "结构支撑相对平衡，未触发恶化转化。"),
        ("Growth-Led", "Deteriorating"): ("Growth remains strong while weakening support reduces confidence in bullish interpretation.", "增长较强，但结构支撑恶化降低看涨解释的置信度。"),
        ("Stressed", "Deteriorating"): ("Weak downside stability or resilience makes adverse outcomes a particular concern.", "下行稳定性或韧性较弱，应特别关注不利结果。"),
        ("Stressed", "Recovering"): ("Structure is improving from stress; persistent improvement remains unconfirmed.", "结构正在从压力中改善，仍需观察改善能否持续。"),
        ("Defensive", "Stable"): ("Downside conditions are relatively controlled, with limited observed growth strength.", "下行条件相对受控，已观察到的增长强度有限。"),
    }.get((state, transition), (f"Confirmed state: {state}; transition: {transition}.", f"已确认状态：{state}；转化：{transition}。"))
    en += " " + state_text[0] + f" Confidence: {conf['confidence']}."
    zh += " " + state_text[1] + f" 置信度：{conf['confidence']}。"
    if synthetic:
        en += " Based on synthetic/demo data."
        zh += " 基于合成/演示数据。"
    en += " Probabilities are conditional on the unchanged GBM assumptions, not calibrated forecast accuracy. For educational and research purposes only. Not investment advice."
    zh += " 概率依赖既有 GBM 假设，不代表已校准的预测准确率。本结果仅用于研究与教育目的，不构成任何投资建议。"
    return dict(en=en, zh=zh)


def interpret_outlook(result, metrics, scores, interpretation, synthetic):
    direction = directional_label(result["probability_up"], result["p50"], result["months"])
    relative = relative_outlook(metrics)
    conf = confidence(direction, relative, scores, interpretation, synthetic)
    return dict(direction=direction, relative_outlook=relative, **conf,
                explanation=explain(direction, result, interpretation, conf, synthetic))
