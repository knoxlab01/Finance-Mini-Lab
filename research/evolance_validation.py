"""Run: python -m research.evolance_validation [--try-live]. No UI or DB writes.

Outputs derived fixture tables and an honest research report. Real raw market
prices are never exported. SQLite is opened read-only, ignoring expiry only for
retrospective research; only explicit Yahoo adjusted-price rows are accepted.
"""
import argparse
from contextlib import closing
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

from src.evolance import Calibration, rolling_analysis, summarize_timeline
from src.evolance.validation import find_cases, subsequent_outcomes

ROOT = Path(__file__).resolve().parents[1]
SYMBOLS = ["AAPL", "MSFT", "NVDA", "SPY"]


def regime_fixture(seed=407):
    """Designed code-validation regimes, not reconstructed security history."""
    rng = np.random.default_rng(seed)
    regimes = [
        ("stable", 252, .00030, .004, .004, .20, .20),
        ("bull", 252, .00120, .006, .006, .25, .25),
        ("volatility expansion", 126, .00100, .006, .025, .25, .95),
        ("stress", 126, -.00200, .030, .030, .97, .97),
        ("recovery", 252, .00150, .009, .009, .40, .40),
        ("low-growth stable", 252, .00004, .001, .001, .10, .10),
        ("renewed growth", 252, .00100, .008, .008, .35, .35),
    ]
    blocks, labels = [], []
    for name, n, drift, v0, v1, c0, c1 in regimes:
        common = rng.standard_normal(n)
        vol, corr = np.linspace(v0, v1, n), np.linspace(c0, c1, n)
        assets = np.column_stack([drift * beta + vol * (np.sqrt(corr) * common + np.sqrt(1 - corr) * rng.standard_normal(n)) * beta for beta in (.9, 1., 1.25)])
        benchmark = drift * .7 + vol * .75 * (.6 * common + .8 * rng.standard_normal(n))
        reserve = .000025 + .00015 * rng.standard_normal(n)
        blocks.append(np.column_stack([assets, benchmark, reserve]))
        labels.extend([name] * n)
    log_returns = np.vstack(blocks)
    dates = pd.bdate_range("2010-01-01", periods=len(log_returns) + 1)
    prices = pd.DataFrame(np.vstack([np.ones(5), np.exp(np.cumsum(log_returns, axis=0))]) * 100,
                          index=dates, columns=SYMBOLS + ["RESERVE"])
    prices.attrs["source_metadata"] = {s: {"provider": "synthetic_research_fixture", "seed": seed} for s in prices}
    phase = pd.Series(["baseline"] + labels, index=dates, name="designed_regime")
    return prices, phase


def load_real_prices(try_live=False):
    attempts = []
    path = ROOT / "data" / "finance_lab.sqlite3"
    if path.exists():
        with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
            rows = db.execute("SELECT ticker,date,adjusted_close FROM historical_prices WHERE lower(source) IN ('yahoo','yahoo finance / yfinance') AND date BETWEEN ? AND ?", ("2016-01-01", "2026-10-08")).fetchall()
        if rows:
            frame = pd.DataFrame(rows, columns=["ticker", "date", "price"]).pivot(index="date", columns="ticker", values="price")
            frame.index = pd.to_datetime(frame.index)
            if set(SYMBOLS).issubset(frame):
                frame = frame[SYMBOLS].sort_index().dropna()
                if len(frame) >= 505 and frame.index.to_series().diff().dt.days.max() <= 7:
                    attempts.append("Read-only Yahoo cache accepted; retrospective cache freshness not enforced")
                    return frame, "real_yahoo_cache", attempts
        attempts.append("No adequate aligned Yahoo cache for all four tickers (minimum 505 prices)")
    else:
        attempts.append("No local SQLite price cache")
    if try_live:
        from src.market_data import download_prices
        series = []
        try:
            for symbol in SYMBOLS:
                item = download_prices(symbol, "2016-01-01", "2026-10-08", max_attempts=1)
                item.attrs = {}
                series.append(item.rename(symbol))
            frame = pd.concat(series, axis=1).dropna()
            if len(frame) < 505:
                raise ValueError("Insufficient aligned real prices")
            attempts.append("Yahoo adjusted-price download succeeded")
            return frame, "real_yahoo_download", attempts
        except Exception as exc:
            attempts.append(f"Yahoo stopped at {SYMBOLS[len(series)] if len(series) < 4 else 'alignment'}: {type(exc).__name__}; category={getattr(exc, 'category', 'unavailable')}")
    else:
        attempts.append("Live request not enabled; use --try-live for an explicit attempt")
    return None, "unavailable", attempts


def _table(frame):
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return "N/A" if not np.isfinite(v) else f"{v:.3f}"
        return str(v).replace("|", "/").replace("\n", " ")
    return "| " + " | ".join(map(str, frame.columns)) + " |\n| " + " | ".join(["---"] * len(frame.columns)) + " |\n" + "\n".join("| " + " | ".join(fmt(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None))


def write_report(results, summary, cfg, output):
    primary = results["fixture_equal"]
    test_path = ROOT / "research" / "evolance_results" / "test_result.txt"
    test_evidence = test_path.read_text(encoding="utf-8").strip() if test_path.exists() else "Full-suite result not yet recorded."
    case_lines = []
    interpretations = {
        "A": "多指标结构解释更集中，但风险变化已存在于原始指标中；非新增独立证据。 / Clearer consolidation; deterioration already exists in underlying metrics.",
        "B": "低波动与低增长/低超额收益并存，可解释防御取向；不等于持有者过度防守。 / Explains defensive posture, not personal unsuitability.",
        "C": "与传统指标同时恶化，主要是重复确认。 / Concurrent deterioration is largely redundant confirmation.",
        "D": "只相对预设弱基线作时间比较；不能推断领先分析师或预测未来。 / Timing comparison against a weak declared baseline only, not predictive evidence.",
    }
    for name in "ABCD":
        found = next(((label, r["cases"][name]) for label, r in results.items() if r["cases"][name] is not None), None)
        if not found:
            case_lines.append(f"### Case {name}\n\n未找到符合预设条件且未来窗口完整的案例。 / No qualifying case with a complete forward window.\n")
            continue
        label, case = found
        data = dict(dataset=label, **case)
        case_lines.append(f"### Case {name}\n\n{interpretations[name]}\n\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```\n")
    calibration = []
    for dimension, weights in cfg.weights.items():
        for component, weight in weights.items():
            calibration.append([dimension, component, weight, str(cfg.anchors[component])])
    summary_rows = [[name, len(r["timeline"]), len(r["summary"]["most_common"]), len(r["summary"]["transitions"]), str(r["summary"]["most_common"])] for name, r in results.items()]
    phases = primary["timeline"].groupby("designed_regime")[["Growth", "Stability", "Diversification", "Efficiency", "Adaptability"]].mean().reset_index()
    observed_d = []
    for name, result in results.items():
        case = result["cases"]["D"]
        if case:
            observed_d.append([name, case["date"][:10], case["state"],
                               case["lead_calendar_days"], case["forward_return"], case["forward_drawdown"]])
    observed_d_table = _table(pd.DataFrame(observed_d, columns=["Dataset", "Case D date", "State", "Baseline lead days", "Forward return", "Forward drawdown"])) if observed_d else "No Case D found."
    absent = [state for state in cfg.precedence if state not in primary["summary"]["most_common"]]
    cutoff_sensitivity = {k: v for k, v in summary["sensitivities"].items() if k.startswith("cutoffs")}
    report = f'''# Evolance Research Prototype v1

研究定位 / Research positioning: **Dynamic Multi-Factor State Framework**

## 1. Research Question / 研究问题

一个动态多因素状态框架，能否在传统投资组合指标之外提供有价值的结构性增量信息？
Can a dynamic multi-factor state framework provide useful structural insight beyond conventional portfolio metrics?

## 2. Evidence Status / 证据状态

本报告由研究脚本生成。合成数据仅用于 code validation；真实 historical validation 单独记录。没有声称预测能力。
Generated by the research runner. Synthetic fixtures validate code and behavior, not actual securities or market episodes. Real historical validation is reported separately.

真实数据状态 / Real-data status: **{summary['real_source']}**

{chr(10).join('- ' + x for x in summary['retrieval_attempts'])}

Fixture seed: 407; SHA-256: `{summary['fixture_sha256']}`. 资产标签 AAPL/MSFT/NVDA/SPY 仅标识合成列，RESERVE 为低波动合成储备。 / Labels identify synthetic columns, not actual security histories.

## 3. Framework and Five Dimensions / 框架与五维度

- Growth = 40% CAGR + 35% trailing relative return + 25% 126-session return。最近趋势直接影响评分，长期 CAGR 不能单独决定结果。
- Stability = 35% inverse volatility + 40% inverse drawdown magnitude + 25% inverse negative-day frequency。负日比例是历史代理，不是 Monte Carlo 期末亏损概率；忽略亏损幅度的缺陷须与回撤一起看。
- Diversification = 45% inverse mean pair correlation + 35% inverse maximum weight + 20% effective holdings `1/HHI`。只计正权重；单资产相关性原始值 N/A，但评分明确采用最保守端点。不可把多只 ETF 当作穿透后分散化。
- Efficiency = 45% Sharpe + 30% CAGR/absolute max drawdown + 25% (portfolio Sharpe − benchmark Sharpe)。承担更多波动而未获得足够超额收益会压低相对 Sharpe；但它不是 alpha 模型。
- Adaptability = 30% volatility change + 25% correlation change + 25% drawdown deterioration + 20% score persistence。相邻评估的变化；persistence 为四个基础分数的平均绝对变化，恶化和快速改善均可能降低该子项。第一期无前值时明确 N/A，不用未来填补。

各维度提供组件评分、权重、缺失证据和规则匹配，未定义的关键组件不重分配权重。
Components, weights, missing evidence and all matching rules are retained; undefined components do not trigger silent reweighting.

## 4. Scoring Rules / 集中校准规则

固定锚点间线性插值、区间外端点截断到 0–100。阈值是未经经验验证的原型参数；无机器学习、全样本分位数或未来信息。收益/波动为小数，Sharpe/相关性为比率。
Linear interpolation between fixed anchors, saturated outside their range. These are unvalidated research calibrations, not theoretical or regulatory cutoffs. Returns/volatility are decimal units.

{_table(pd.DataFrame(calibration, columns=['Dimension', 'Component', 'Weight', '(raw value, score) anchors']))}

## 5. State Rules / 状态规则

确定性优先级 / Precedence: {' > '.join(cfg.precedence)}.

- Stress: Adaptability <40, Stability <40, at least two core scores fall ≥5 points.
- Fragile Growth: Growth ≥65 and (Stability <40 or Diversification <40).
- Concentration Pressure: Diversification <30 (also captures correlated exposures, not only holding count).
- Inefficient Risk: Stability <40 and Efficiency <40.
- Transitional Recovery: prior Stress/Recovery, Stability ≥40; Stability, Efficiency and Adaptability each improve ≥5; Growth improves.
- Growth-Dominant: Growth ≥80 and exceeds the weakest of Stability/Diversification/Efficiency by ≥20.
- Defensive Imbalance: Stability ≥75 and (Growth <40 or Efficiency <40).
- Balanced Growth: Growth ≥65, Stability/Efficiency ≥55, Diversification ≥45.
- No match: Mixed / Unclassified. Undefined core score: Insufficient Evidence. Adaptability unavailable means stress/recovery cannot be assessed, while static rules remain available.

重叠状态保留全部 matches，首个为主状态；Balanced 与 Growth-Dominant 可能重叠，优先级是人为解释选择。
All matches are retained; priority resolves overlap. State labels are heuristic summaries, not diagnoses.

## 6. Historical Methodology / 历史滚动方法

默认 252 个日收益需 253 个价格，月度评估；另运行 126/504 及季度敏感性验证。只在已完成自然月/季度的最后观测日评估，as_of 控制信息截止；不使用未完成期。连续窗口重叠，观察并非独立样本。
Default: 252 return observations, monthly completed periods. Each snapshot uses only its trailing window; quarterly and 126/504-window variants are also run. Overlapping observations are not independent.

固定非负权重每日再平衡、共同日期、无现金流/交易成本。CAGR 复用 v0.3 日历年化，波动/Sharpe 252 交易日年化，rf=4%。Recent Trend 126 个交易日。相关性为未加权资产对均值。要求同步有限正价格，不填充 NaN，不接受 >7 天空档。日期及权重校验失败会明确报错。
Reuse existing v0.3 financial metric functions without modification. Daily target-weight rebalancing, aligned prices, 4% risk-free rate, no fees or flows. Invalid/missing prices are rejected.

未来 63 个观测的实际累计收益与最大回撤在独立 ex-post 模块计算，T 当日收益不进入 forward window。尾部窗口不完整显示 unavailable，不当作零。状态持续时间为离散评估间观察跨度，最后一段 right-censored；不推断每日实际转化日。
Forward outcomes are separate from state generation; terminal incomplete windows are censored. State durations describe sampled observations, with the last spell right-censored.

## 7. Cases Tested / 案例集

合成 fixture 顺序：stable → bull → volatility expansion → stress → recovery → low-growth stable → renewed growth。阶段是人为设置，不对应相同日期的真实市场事件。
Designed regimes are synthetic, not reconstructions of actual events on those dates.

组合：等权 33.33/33.33/33.34、集中 90/5/5、单资产、低波动 RESERVE；SPY 为基准。真实数据若可用，仅等权证券组使用真实来源；不混合合成 RESERVE。
Compare equal-weight, concentrated, single-holding and defensive synthetic structures. Any real dataset is evaluated separately.

{_table(pd.DataFrame(summary_rows, columns=['Dataset', 'Evaluations', 'Distinct states', 'Transitions', 'State counts']))}

等权 fixture 按设计阶段的平均分 / Mean fixture scores by designed regime:

{_table(phases)}

## 8. Traditional vs Evolance / 传统指标比较

每个 timeline 同时输出 CAGR、trailing return、volatility、Sharpe、drawdown magnitude、relative return、mean correlation、maximum weight、HHI/effective holdings 与五维评分。原始指标来自同一过去窗口；评分不增加信息源。
Traditional metrics and state interpretations share identical historical inputs; the framework introduces no independent information source.

案例条件在代码中显式定义，选择第一个符合条件且未来窗口完整的观测，不按未来收益筛选最漂亮结果。D 基线只使用 CAGR≤0 或 Sharpe≤0 或 volatility≥25%；此弱基线不代表熟练分析师或完整传统分析。
Cases use first qualifying observations, not best future outcomes. D's weak declared baseline is not a claim of superiority over conventional analysis.

{chr(10).join(case_lines)}

## 9. Incremental Insight Findings / 增量解释发现

状态能将相对强增长、弱支撑与风险恶化组合为一条可审查解释；最大权重与有效持仓明确指出表面分散；动态变化提示能减少逐项比较负担。若 D 找到更早转化，也只是比预设静态阈值更早；原始相关性、回撤和变化率已经包含该信息。
Potential value is structured interpretation and fewer manual comparisons. Any earlier transition is relative to a chosen static rule; correlation, drawdown and metric changes already contain the evidence.

## 10. Failure / Redundancy Cases / 失败与重复

本次等权 fixture 没出现的规则状态 / States absent from this equal-weight run: **{', '.join(absent)}**。设计阶段包含 stress/recovery，但规则未必识别；未为得到这些标签而调整阈值。针对 Stress/Recovery 的构造评分测试通过，不等于历史识别有效。

低波动 RESERVE 的主状态始终为 Concentration Pressure，虽然部分评估也匹配 Defensive Imbalance：优先级掩盖了防御解释；这说明标签对资产类别和目的缺乏上下文。 / The single reserve is always classified as Concentration Pressure; precedence masks its defensive posture and lacks asset-purpose context.

等权与 90/5/5 的平均 Diversification 差 / Mean equal-weight minus concentrated score: **{summary['diversification_equal_minus_concentrated']:.2f}**。由于公式显式包含权重，这首先是机械差异，不是增量预测证据。

所有结构组合的 Case D 同时公开，避免只展示随后下跌的一例。其他组合即使早于弱基线，随后仍可能上涨；长期 lead 也不等于有效提前预警。 / All Case D matches are shown, including subsequent positive returns; a long lead is not an actionable warning.

{observed_d_table}

阈值 ±5 分敏感性 / Cutoff-shift sensitivity: `{json.dumps(cutoff_sensitivity)}`。状态改变表明校准影响结论，不能赋予标签客观真理的地位。

C 为直接重复传统风险恶化。Stability 与 Efficiency 共用风险信息；Concentration 与 effective holdings 双重体现集中；组合均值相关性忽略权重大小。固定阈值有边界跳变、分数饱和及优先级掩盖次要状态的问题。
C largely restates traditional deterioration. Dimensions overlap; concentration is counted twice. Unweighted correlation and fixed thresholds can distort interpretation.

恢复规则很严格，若未出现 Transitional Recovery 不代表没有恢复；持续低迷但不继续恶化也可能从 Stress 退出到 Inefficient Risk。Adaptability 首期不可得，且改善时较大分数变动也会扣分。没有强制每个历史日期套入一个有吸引力的状态。
Strict recovery criteria may miss recoveries; sustained stress can become Inefficient Risk once deterioration stops. Rapid improvement can penalize persistence. Mixed and missing-evidence states are deliberate.

## 11. Limitations / 限制

真实历史证据不足时只能判断代码行为。设计 fixture、事后检查与少数组合可能产生确认偏差；未做独立盲评、完整样本外研究、状态预测准确率或多重比较校正。rf 固定，日再平衡理想化；现今可获得复权数据可能含事后修订，非严格 point-in-time corporate-action 数据。即使真实数据可用也不能完全排除幸存者偏差。
Fixtures cannot establish empirical validity. No independent user study, held-out research, predictive evaluation or multiple-testing correction is provided. Adjusted histories may contain later revisions; survivor selection remains a limitation.

评分阈值敏感性检查只用于展示稳定程度，不按结果调参。详见 summary.json；无新增 API、ML 或公开页面。
Sensitivity checks describe fragility without optimizing cutoffs. No new data provider, ML or public UI is introduced.

## 12. Kill Criteria Evaluation / 四项门槛

{_table(pd.DataFrame(summary['kill_criteria'], columns=['Criterion', 'Code evidence', 'Historical/product evidence']))}

## 13. Recommendation / 建议

**Revise and retest — Do not productize yet. / 修订并复测，暂不产品化。**

fixture 仅能支持行为差异与可解释实现，不能把这两项当成两条已满足的历史产品化门槛。真实不同阶段、不同结构的增量价值尚需验证；解释更容易理解也需要用户研究。下一步先取得可合法使用的真实数据、固定校准，在未参与设计的时期/组合与更强多指标基线比较，允许否定结论。
Code-level variation does not satisfy two historical productization gates. Obtain usable real histories, freeze calibration, test held-out periods/portfolios and stronger baselines, and assess explanation usefulness independently.

## Reproduction / 复现

`python -m research.evolance_validation` reads existing Yahoo cache if adequate and always runs fixtures. `--try-live` enables one attempt per ticker until a provider failure. Raw real prices are not exported. Derived fixture CSVs, summaries and this report are reproducible with the stated seed/calibration. Live-cache availability can change real-data results.

自动化测试结果记录在 `research/evolance_results/test_result.txt`，不由研究脚本编造。 / Actual test results are recorded separately in `research/evolance_results/test_result.txt`.

```text
{test_evidence}
```
'''
    output.write_text(report, encoding="utf-8")


def run(try_live=False):
    cfg = Calibration()
    output = ROOT / "research" / "evolance_results"
    output.mkdir(parents=True, exist_ok=True)
    fixture, phase = regime_fixture()
    portfolios = {"equal": dict(AAPL=.3333, MSFT=.3333, NVDA=.3334),
                  "concentrated": dict(AAPL=.90, MSFT=.05, NVDA=.05),
                  "single": dict(AAPL=1.), "defensive": dict(RESERVE=1.)}
    results = {}
    real, source, attempts = load_real_prices(try_live)
    datasets = [("fixture_" + name, fixture, weights) for name, weights in portfolios.items()]
    if real is not None:
        datasets.append(("real_equal", real, portfolios["equal"]))
    for name, prices, weights in datasets:
        timeline = rolling_analysis(prices, weights, config=cfg)
        if name.startswith("fixture"):
            timeline["designed_regime"] = phase.reindex(timeline.index)
        outcomes = subsequent_outcomes(prices, weights, timeline, cfg.forward_days)
        results[name] = dict(timeline=timeline, summary=summarize_timeline(timeline, cfg), cases=find_cases(timeline, outcomes, cfg))
        # Derived fixture values only; no raw price redistribution.
        if name.startswith("fixture"):
            timeline.drop(columns=["components"]).join(outcomes).to_csv(output / (name + "_timeline.csv"), float_format="%.8f")
    sensitivity = {}
    for lookback, frequency in [(126, "monthly"), (504, "monthly"), (252, "quarterly")]:
        c = Calibration(lookback=lookback, frequency=frequency)
        series = rolling_analysis(fixture, portfolios["equal"], config=c)
        sensitivity[f"{lookback}_{frequency}"] = summarize_timeline(series, c)
    for shift in [-5, 5]:
        c = Calibration()
        for key in ["growth_high", "growth_very_high", "low", "high", "div_very_low", "support_min", "div_min", "adapt_low"]:
            c.thresholds[key] += shift
        series = rolling_analysis(fixture, portfolios["equal"], config=c)
        sensitivity[f"cutoffs_{shift:+}"] = dict(state_disagreement=float((series.state != results["fixture_equal"]["timeline"].state).mean()))
    difference = (results["fixture_equal"]["timeline"].Diversification - results["fixture_concentrated"]["timeline"].Diversification).mean()
    summary = dict(real_source=source, retrieval_attempts=attempts,
                   fixture_sha256=hashlib.sha256(fixture.to_csv(float_format="%.12f").encode()).hexdigest(),
                   calibration=asdict(cfg), sensitivities=sensitivity,
                   diversification_equal_minus_concentrated=float(difference),
                   results={k: {"summary": r["summary"], "cases": r["cases"]} for k, r in results.items()},
                   kill_criteria=[
                       ["1. Distinct periods / 不同阶段", f"Fixture distinct states: {len(results['fixture_equal']['summary']['most_common'])}", "Unverified; synthetic variation is not historical validation"],
                       ["2. Earlier/clearer deterioration / 更早或更清楚", "Declared weak-baseline Case D search; no predictive test", "Unverified against a strong traditional baseline"],
                       ["3. Easier explanation / 更易理解", "Auditable components, rule matches and missing-evidence explanations", "Unverified without independent reader/user assessment"],
                       ["4. Different structures / 不同结构", f"Fixture diversification mean gap: {difference:.2f} points", "Mechanically demonstrated; real historical usefulness unverified"],
                   ], recommendation="Revise and retest; do not productize yet")
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_report(results, summary, cfg, ROOT / "docs" / "evolance_v1_research.md")
    print(json.dumps(dict(real_source=source, attempts=attempts, evaluations={k:len(r['timeline']) for k,r in results.items()}, states=results['fixture_equal']['summary']['most_common'], recommendation=summary['recommendation']), ensure_ascii=False))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--try-live", action="store_true")
    run(parser.parse_args().try_live)
