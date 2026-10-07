"""Educational, uncalibrated decision-support rules, not suitability advice.

Risk tiers: annual simple volatility <12%/12–25%/>=25%, drawdown magnitude
<15%/15–30%/>=30%, available simulated loss <15%/15–35%/>=35%: 0/1/2 points.
Add 1 each for mean pair correlation >=.75, maximum holding weight >=.50,
and volatility >=1.25x a positive benchmark volatility. Score 0–1/2–3/>=4
maps to Lower/Moderate/Higher Risk. Requires both volatility and drawdown.
Missing optional evidence never means zero risk; coverage is reported.
Thresholds are heuristic UI explanations, not regulatory/empirical ratings.
"""
import math
import numpy as np
import pandas as pd

RISK_LABELS = ["较低风险 / Lower Risk", "中等风险 / Moderate Risk", "较高风险 / Higher Risk"]
PREFERENCES = {"Conservative": 0, "Balanced": 1, "Aggressive": 2}
HORIZONS = {"Short Term": 0, "Medium Term": 1, "Long Term": 2}
GOALS = {"Capital Preservation": 0, "Steady Growth": 1, "Growth Priority": 2}


def _finite(value):
    return isinstance(value, (int, float, np.number)) and not isinstance(value, (bool, np.bool_)) and math.isfinite(value)


def _metric(historical, name, column="Portfolio"):
    metrics = historical.get("metrics")
    try:
        value = metrics[column][name]
    except (KeyError, TypeError, IndexError):
        return None
    return float(value) if _finite(value) else None


def assess_portfolio_risk(historical):
    historical = historical or {}
    vol = _metric(historical, "Annualized Volatility")
    drawdown = _metric(historical, "Maximum Drawdown")
    evidence, missing = [], []
    def add(key, value, points, reason):
        evidence.append(dict(key=key, value=value, points=points, reason=reason))
    valid_core = vol is not None and vol >= 0 and drawdown is not None and -1 <= drawdown <= 0
    if vol is not None and vol >= 0:
        add("volatility", vol, int(vol >= .12) + int(vol >= .25), f"历史年化波动率 / Historical annualized volatility: {vol:.1%}")
    else:
        missing.append("年化波动率 / Annualized volatility")
    if drawdown is not None and -1 <= drawdown <= 0:
        magnitude = abs(drawdown)
        add("drawdown", magnitude, int(magnitude >= .15) + int(magnitude >= .30), f"历史最大回撤 / Historical maximum drawdown: {drawdown:.1%}")
    else:
        missing.append("最大回撤 / Maximum drawdown")
    future = historical.get("future_outlook") or {}
    sim = future.get("simulation") or {}
    loss, horizon = sim.get("loss_probability"), sim.get("horizon")
    if _finite(loss) and 0 <= loss <= 1 and horizon in (1, 3, 5):
        add("loss", loss, int(loss >= .15) + int(loss >= .35), f"{horizon} 年模拟期末亏损概率 / Simulated terminal loss probability ({horizon} years): {loss:.1%}")
    else:
        missing.append("有效模拟亏损概率 / Valid simulated loss probability")
    corr = historical.get("correlation")
    if isinstance(corr, pd.DataFrame) and corr.shape[0] == corr.shape[1] and len(corr) > 1:
        try:
            values = corr.to_numpy(dtype=float)[np.triu_indices(len(corr), 1)]
        except (TypeError, ValueError):
            values = np.array([])
        values = values[np.isfinite(values) & (values >= -1) & (values <= 1)]
        if len(values):
            if len(values) < len(corr) * (len(corr) - 1) // 2:
                missing.append("部分相关系数缺失 / Partial correlation coverage")
            average = float(values.mean())
            add("correlation", average, int(average >= .75), f"可用资产对平均相关系数 / Mean available pairwise correlation: {average:.2f} ({len(values)} pairs)")
        else:
            missing.append("相关性 / Correlation")
    else:
        missing.append("相关性 / Correlation")
    config = historical.get("portfolio_config") or {}
    weights = config.get("weights", [])
    if weights and all(_finite(w) and 0 <= w <= 1 for w in weights) and np.isclose(sum(weights), 1):
        maximum = max(weights)
        add("concentration", maximum, int(maximum >= .5), f"最大单项配置权重 / Largest holding allocation: {maximum:.1%}（不穿透 ETF / no ETF look-through）")
    else:
        missing.append("持仓权重 / Holding weights")
    benchmark_vol = _metric(historical, "Annualized Volatility", "Benchmark")
    if vol is not None and vol >= 0 and benchmark_vol is not None and benchmark_vol > 0:
        relative = vol / benchmark_vol
        add("benchmark_risk", relative, int(relative >= 1.25), f"组合/基准波动率比 / Portfolio-to-benchmark volatility: {relative:.2f}x")
    else:
        missing.append("基准波动比较 / Benchmark volatility comparison")
    score = sum(e["points"] for e in evidence) if valid_core else None
    level = (2 if score >= 4 else 1 if score >= 2 else 0) if score is not None else None
    return dict(level=level, label=RISK_LABELS[level] if level is not None else "数据不足 / Insufficient data",
                score=score, evidence=evidence, missing=missing, context=summarize_rationale(historical),
                demo=any(m.get("provider") == "demo" for m in historical.get("source_metadata", {}).values()))


def summarize_rationale(historical):
    """Read existing results as context; returns do not offset risk points."""
    context = []
    for name in ["Cumulative Return", "CAGR"]:
        value = _metric(historical, name)
        if value is not None:
            context.append(f"历史 {name} / Historical {name}: {value:.1%}")
    value = _metric(historical, "CAGR", "Benchmark")
    if value is not None:
        context.append(f"基准 CAGR / Benchmark CAGR: {value:.1%}")
    future = historical.get("future_outlook") or {}
    parameters = future.get("parameters") or {}
    expected, vol = parameters.get("expected_return"), parameters.get("volatility")
    if _finite(expected) and _finite(vol) and vol >= 0:
        context.append(f"模型年预期收益/对数波动 / Model annual expected return/log volatility: {expected:.1%} / {vol:.1%}（非保证 / not guaranteed）")
    table = (future.get("scenarios") or {}).get("checkpoints")
    if isinstance(table, pd.DataFrame) and not table.empty and all(c in table for c in ["Conservative", "Base", "Optimistic"]):
        values = table.iloc[-1][["Conservative", "Base", "Optimistic"]]
        if all(_finite(value) for value in values):
            context.append(f"{table.index[-1]} 年情景终值 / Scenario values: " + " / ".join(f"{v:,.0f}" for v in values) + "（非分位数 / not percentiles）")
    return context


def assess_profile_fit(assessment, profile):
    profile = profile or {}
    risk, horizon, goal = (profile.get(key) for key in ("risk_preference", "investment_horizon", "primary_goal"))
    if risk not in PREFERENCES or horizon not in HORIZONS or goal not in GOALS:
        return dict(label="请完善偏好 / Complete your profile", target=None, delta=None)
    # Risk tolerance is a ceiling: a long horizon never overrides conservative
    # preference or a capital-preservation goal. Short horizon caps at lower risk.
    target = min(PREFERENCES[risk], HORIZONS[horizon], GOALS[goal])
    if assessment["level"] is None:
        return dict(label="数据不足，暂不判断 / Insufficient data for fit", target=target, delta=None)
    delta = assessment["level"] - target
    label = ("风险明显偏高 / Too Aggressive" if delta >= 2 else
             "略高于偏好 / Slightly Aggressive" if delta == 1 else
             "匹配良好 / Good Fit" if delta == 0 else
             "风险低于目标取向 / Too Conservative (risk only, not a return forecast)")
    return dict(label=label, target=target, delta=delta)


def generate_allocation_direction(fit):
    target = fit.get("target")
    return {0: "可研究以现金/短期储备及防御性类别满足近期用途，再评估股票敞口；这些类别也有通胀、利率或信用风险。 / Explore near-term reserves and defensive categories before equity exposure; these still carry inflation, rate or credit risk.",
            1: "可研究宽基敞口与防御性类别的平衡，增长资产作为补充；不指定比例或证券。 / Explore a balance of broad-market and defensive exposure, with growth assets as a complement; no weights or securities specified.",
            2: "可研究分散化股票/宽基敞口与增长类别，并区分长期投资和短期资金用途。 / Explore diversified equity/broad-market and growth categories while separating near-term funding needs."}.get(target)


def generate_guidance(historical, profile):
    historical = historical or {}
    assessment = assess_portfolio_risk(historical)
    fit = assess_profile_fit(assessment, profile)
    notices = list(assessment["missing"])
    if not historical.get("future_outlook"):
        notices.append("运行 Future Outlook 可补充风险判断。 / Run Future Outlook for a fuller risk assessment.")
    if fit["target"] is None or assessment["level"] is None:
        return dict(assessment=assessment, fit=fit, recommendations=[], allocation=None, notices=notices)
    evidence = {e["key"]: e for e in assessment["evidence"]}
    suggestions = []
    def rec(category, recommendation, reason):
        suggestions.append(dict(category=category, recommendation=recommendation, reason=reason))
    for key, category, advice in [
        ("correlation", "Diversification", "研究相关性更低的资产类别，检验分散效果。 / Explore less-correlated asset categories and evaluate diversification."),
        ("concentration", "Concentration", "复核最大单项配置及底层风险重叠；单只 ETF 不等于单只股票。 / Review the largest allocation and overlapping underlying exposures; one ETF is not one stock."),
        ("drawdown", "Drawdown", "检查是否能承受历史量级回撤及资金需求。 / Review capacity for drawdowns of the observed magnitude and funding needs."),
        ("loss", "Downside Risk", "对照所选模拟期限复核可承受损失。 / Review tolerable losses at the selected simulation horizon."),
        ("benchmark_risk", "Benchmark Risk", "比较承担额外波动是否符合你的目标。 / Compare the additional variability with your objective.")]:
        item = evidence.get(key)
        if item and item["points"]:
            rec(category, advice, item["reason"])
    if not suggestions:
        rec("Risk Budget", "以已观察到的波动和回撤检查风险承受能力，不把低评级理解为安全保证。 / Check risk capacity against observed volatility and drawdown; a lower tier is not a safety guarantee.",
            evidence["volatility"]["reason"] + "; " + evidence["drawdown"]["reason"])
    rec("Profile Alignment", "将临近用途与长期投资分开，按偏好和目标复核风险敞口。 / Separate near-term needs from long-term investing and review exposure against your preference and goal.",
        f"风险偏好/期限/目标 / Preference/horizon/goal: {profile['risk_preference']} / {profile['investment_horizon']} / {profile['primary_goal']}; {fit['label']}")
    sharpe = _metric(historical, "Sharpe Ratio")
    benchmark_sharpe = _metric(historical, "Sharpe Ratio", "Benchmark")
    if sharpe is not None and (sharpe < 0 or benchmark_sharpe is not None and sharpe < benchmark_sharpe):
        rec("Risk-adjusted Quality", "复核所承担波动对应的历史超额收益；不据此推断未来表现。 / Review historical excess return per unit of risk without extrapolating future performance.",
            f"历史 Sharpe / Historical Sharpe: {sharpe:.2f}; benchmark: {benchmark_sharpe if benchmark_sharpe is not None else 'N/A'}")
    future = historical.get("future_outlook") or {}
    sim = future.get("simulation") or {}
    initial, p10, p50, p90 = (sim.get(key) for key in ("initial_value", "p10", "p50", "p90"))
    if all(_finite(v) for v in (initial, p10, p50, p90)) and initial > 0 and 0 < p10 <= p50 <= p90:
        rec("Outcome Uncertainty", "同时查看模拟下行情景和结果分布，不只关注中位数。 / Review the simulated downside and distribution rather than the median alone.",
            f"模拟 P10/P50/P90 / Simulated percentiles: {p10:,.0f} / {p50:,.0f} / {p90:,.0f}; P10–P90 宽度/初值 / width-to-initial: {(p90-p10)/initial:.1%}")
    if len(suggestions) < 3:
        rec("Evidence Coverage", "补充缺失证据并定期对照同一口径，避免把历史风险评级外推为未来保证。 / Fill evidence gaps and compare consistent measures rather than treating this historical tier as a future guarantee.",
            "未提供 / Unavailable: " + "; ".join(notices) if notices else f"规则评分 / Rule score: {assessment['score']}; 波动率 / volatility: {evidence['volatility']['value']:.1%}")
    # Keep profile alignment even when several metric warnings take priority.
    selected = [s for s in suggestions if s["category"] != "Profile Alignment"][:4]
    selected.append(next(s for s in suggestions if s["category"] == "Profile Alignment"))
    return dict(assessment=assessment, fit=fit, recommendations=selected, allocation=generate_allocation_direction(fit), notices=notices)
