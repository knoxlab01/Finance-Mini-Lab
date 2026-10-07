"""Portfolio-only presentation catalog; never changes engine inputs or results."""
import json
from pathlib import Path
import re

LANGUAGES = ("English", "中文")
CATALOG = json.loads(Path(__file__).with_name("translations.json").read_text(encoding="utf-8"))
ENGINE_MESSAGES = json.loads(Path(__file__).with_name("engine_messages.json").read_text(encoding="utf-8"))


def tr(key, language="English", **values):
    if language not in LANGUAGES:
        raise ValueError("Unsupported language")
    return CATALOG[key][0 if language == "English" else 1].format(**values)


def metric_help(key, language="English"):
    return tr("help_" + key, language)


# Dynamic engine evidence uses explicit patterns, not runtime machine
# translation or arbitrary splitting. Static legacy messages are mapped above.
EVIDENCE = [
    (r"历史年化波动率 / Historical annualized volatility: (.+)", "Historical annualized volatility: {0}", "历史年化波动率：{0}"),
    (r"历史最大回撤 / Historical maximum drawdown: (.+)", "Historical maximum drawdown: {0}", "历史最大回撤：{0}"),
    (r"(\d+) 年模拟期末亏损概率 / Simulated terminal loss probability \((\d+) years\): (.+)", "Simulated terminal loss probability ({1} years): {2}", "{0} 年模拟期末亏损概率：{2}"),
    (r"可用资产对平均相关系数 / Mean available pairwise correlation: (.+) \((.+) pairs\)", "Mean available pairwise correlation: {0} ({1} pairs)", "可用资产对平均相关系数：{0}（{1} 对）"),
    (r"最大单项配置权重 / Largest holding allocation: (.+)（不穿透 ETF / no ETF look-through）", "Largest holding allocation: {0} (no ETF look-through)", "最大单项配置权重：{0}（不穿透 ETF）"),
    (r"组合/基准波动率比 / Portfolio-to-benchmark volatility: (.+)", "Portfolio-to-benchmark volatility: {0}", "组合/基准波动率比：{0}"),
    (r"历史 (.+) / Historical (.+): (.+)", "Historical {1}: {2}", "历史{0}：{2}"),
    (r"基准 CAGR / Benchmark CAGR: (.+)", "Benchmark CAGR: {0}", "基准 CAGR：{0}"),
    (r"模型年预期收益/对数波动 / Model annual expected return/log volatility: (.+)（非保证 / not guaranteed）", "Model annual expected return/log volatility: {0} (not guaranteed)", "模型年预期收益/对数波动：{0}（非保证）"),
    (r"(.+) 年情景终值 / Scenario values: (.+)（非分位数 / not percentiles）", "Scenario values ({0} years): {1} (not percentiles)", "{0} 年情景终值：{1}（非分位数）"),
    (r"风险偏好/期限/目标 / Preference/horizon/goal: (.+)", "Preference/horizon/goal: {0}", "风险偏好/期限/目标：{0}"),
    (r"历史 Sharpe / Historical Sharpe: (.+); benchmark: (.+)", "Historical Sharpe: {0}; benchmark: {1}", "历史 Sharpe：{0}；基准：{1}"),
    (r"模拟 P10/P50/P90 / Simulated percentiles: (.+); P10–P90 宽度/初值 / width-to-initial: (.+)", "Simulated P10/P50/P90: {0}; width-to-initial: {1}", "模拟 P10/P50/P90：{0}；区间宽度/初值：{1}"),
    (r"规则评分 / Rule score: (.+); 波动率 / volatility: (.+)", "Rule score: {0}; volatility: {1}", "规则评分：{0}；波动率：{1}"),
    (r"P10–P90 区间(.+)（宽度为初始价值的 (.+)）；仅反映模型内的不确定性。 / The interval reflects uncertainty within this model only.", "The P10–P90 interval is {0} ({1} of initial value); it reflects uncertainty within this model only.", "P10–P90 区间{0}（宽度为初始价值的 {1}）；仅反映模型内的不确定性。"),
    (r"在当前假设下，(.+) 的模拟在 (.+) 年后低于初始价值。 / Under these assumptions, this fraction of simulations ends below initial value.", "Under these assumptions, {0} of simulations end below initial value after {1} years.", "在当前假设下，{0} 的模拟在 {1} 年后低于初始价值。"),
]


def localize_message(message, language="English"):
    """Localize known engine messages and evidence without touching calculations."""
    if language not in LANGUAGES:
        raise ValueError("Unsupported language")
    text = str(message)
    slot = 0 if language == "English" else 1
    for pattern, en, zh in EVIDENCE:
        match = re.fullmatch(pattern, text)
        if match:
            text = (en, zh)[slot].format(*match.groups())
            break
    # Composite reasons join complete pieces with '; '. Longest first avoids
    # replacing an inner label before its complete recommendation.
    for original in sorted(ENGINE_MESSAGES, key=len, reverse=True):
        text = text.replace(original, ENGINE_MESSAGES[original][slot])
    if language == "中文":
        for key in ["Cumulative Return", "Conservative", "Balanced", "Aggressive", "Short Term", "Medium Term", "Long Term", "Capital Preservation", "Steady Growth", "Growth Priority"]:
            text = text.replace(key, tr(key, language))
    return text
