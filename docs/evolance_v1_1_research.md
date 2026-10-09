# Evolance v1.1 Research Report

**Recommendation: Revise and Retest / 修订研究设计并复测，暂不产品化。** 冻结规则不因本轮结果改变；后续修改规范需要另行授权和版本记录。

SPEC_VERSION: `1.1-frozen`

Frozen specification SHA-256: `bea9d81702d4afe70a2d65d3fd1beb33c410eeefa0298cc2e5fe5d06e521e0b7`

[Frozen rules / 冻结规范](evolance_v1_1_frozen_spec.md) · [JSON](evolance_v1_1_frozen_spec.json) · [Preserved v1 report / v1历史](evolance_v1_research.md)

## Research Objective / 研究目标

一个可解释的动态投资组合状态框架，将成熟金融证据组织为结构状态、风险标签、状态转化与概率化未来展望。
An interpretable dynamic portfolio-state framework that organizes established financial evidence into structural states, risk flags, transitions, and probabilistic forward outlooks.

研究 Interpretation Advantage + Decision-Support Advantage，不声称新金融因子或独立信息优势。 / Established metrics form the evidence layer; original work is their state, transition and explanation architecture.

## Evidence and Data / 证据与数据

Code validation: offline tests. Synthetic validation: original deterministic seven-regime fixture (seed407), four structures; additional seed1701 equal-weight fixture is a synthetic seed check, not a true untouched empirical holdout. Real historical validation: **Unavailable: no adequate real history; no empirical directional claim**.

- No adequate complete Yahoo cache for requested symbols
- Yahoo unavailable: MarketDataError; category=rate_limit

合成资产标签不代表真实证券历史；数据指纹和声明来源逐组合记录于 summary.json。没有新增行情提供方；只读缓存不更新价格，Yahoo 仅使用已有下载器，原始真实行情不导出。
Synthetic ticker labels are not real histories. Input fingerprints and provenance are retained. No additional provider or raw real-price redistribution.

## Frozen Implementation / 冻结实现

- Growth Strength: 60% 252-session return +40% active return. No repeated CAGR/trend input.
- Downside Stability: 50% downside deviation +50% drawdown magnitude. Downside target is the daily equivalent of 4% annual risk-free return, denominator all observations.
- Diversification Quality: 60% normalized effective absolute risk contributors +40% diversification ratio. Signed RC retained; maximum weight/HHI/correlation diagnostic only.
- Return Efficiency: 40% Sortino +60% information ratio. Sortino numerator is annual geometric portfolio return minus 4%; IR uses arithmetic annualized daily active return. Sharpe remains baseline evidence only.
- Structural Resilience: three-evaluation declines only, weights15/35/30/20; improvements never penalized. Three-evaluation warmup is unavailable.

Primary states are Balanced Growth, Growth-Led, Defensive, Stressed, Mixed / Neutral. Six independent flags coexist. Transition is Deteriorating/Stable/Recovering. Candidate/Confirmed are separate, with two-month persistence, severe entry and guarded stress exit. Exact rules and clarification decisions are in the frozen specification.

未定义 Sortino/IR 不填满分，分数不可用仍披露；未匹配条件默认 Mixed / Neutral，不声称完整证据。初始化确认状态 provisional，不能当作经过两期确认。
Undefined metrics remain unavailable, with missingness disclosed; provisional initialization is distinct from confirmation.

## Forward Model / 未来模型

重用 v0.3 的 exact monthly GBM，一年5000条路径，读取第6/12月。固定种子用于复现和跨时点共同随机数；不加入状态条件漂移/波动。P(up)统计终值>初值；亏损统计<，平值单独保留。完整终值收益数组可由函数取得，文件保存每组最新分布，其余可按窗口与种子再生。
No model redesign: exact existing paths at months6/12. Identical data produces identical distributions regardless of state. These are conditional model probabilities, not empirically calibrated event probabilities.

方向使用冻结概率区间与2%/4%中位数幅度约束；相对基准是 active return/IR 启发式标签，不是跑赢概率。置信度为 High/Moderate/Low，按转化矛盾、低韧性、集中风险降级；合成数据上限 Moderate。
Absolute direction stays quantitative; structure changes confidence/explanation only. Relative confidence is reported separately. Neutral confidence is Low.

## Walk-forward Method / 前向方法

默认每个完成月末只用252收益/253价格。评估日期为最后观测交易日，available_at 是月末；不读未来价格来估计参数、状态、标签或方向。未来126/252交易日收益与最大回撤在独立 evaluator 中计算，不足期截尾。固定权重每日再平衡，忽略交易成本、税费及现金流。
Monthly overlapping forward windows are not independent. Pseudo-out-of-sample time ordering does not imply independent empirical calibration. Modern adjusted prices can include later revisions; real point-in-time corporate actions and survivor selection remain limitations.

## 6M / 12M Results / 结果

比率为0–1；hit rate排除Neutral且只计完整未来窗口；Neutral coverage基于全部已发信号。 / Rates are fractions. Directional hit rates use complete non-neutral observations only; neutral coverage uses all issued signals. Counts matter when comparing baselines with different coverage.

| Dataset | Months | Signals | Complete | Directional N | Evolance hit | Neutral coverage | Traditional hit | MC-only hit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixture_equal | 6 | 58 | 52 | 43 | 0.5581 | 0.1552 | 0.5745 | 0.5581 |
| fixture_equal | 12 | 58 | 47 | 40 | 0.5000 | 0.1207 | 0.5000 | 0.5000 |
| fixture_concentrated | 6 | 58 | 52 | 39 | 0.6667 | 0.2241 | 0.6087 | 0.6667 |
| fixture_concentrated | 12 | 58 | 47 | 41 | 0.5366 | 0.1379 | 0.5349 | 0.5366 |
| fixture_single | 6 | 58 | 52 | 39 | 0.6667 | 0.2241 | 0.5957 | 0.6667 |
| fixture_single | 12 | 58 | 47 | 40 | 0.5750 | 0.1552 | 0.5349 | 0.5750 |
| fixture_defensive | 6 | 58 | 52 | 0 | N/A | 1.0000 | N/A | N/A |
| fixture_defensive | 12 | 58 | 47 | 0 | N/A | 1.0000 | N/A | N/A |
| fixture_seed1701 | 6 | 58 | 52 | 38 | 0.5000 | 0.2586 | 0.4583 | 0.5000 |
| fixture_seed1701 | 12 | 58 | 47 | 40 | 0.6000 | 0.2241 | 0.6304 | 0.6000 |

按方向的平均后续收益、按Transition的平均回撤、Primary State/Confidence/各Flag活动与否的计数及表现均在 summary.json 分组表中提供。截尾记录保留于 outcomes.csv，不填零。
Detailed grouped results include mean returns by direction, drawdowns by transition, primary states, confidence and active/inactive flags. Censored outcomes remain missing.

## State / Flags / Transition / 结构结果

| Dataset | Confirmed states | Flags | Transitions |
| --- | --- | --- | --- |
| fixture_equal | {'Balanced Growth': 34, 'Mixed / Neutral': 10, 'Stressed': 14} | {'Diversification Erosion': 1, 'High Risk Concentration': 0, 'Low Return Efficiency': 16, 'Rapid Structural Deterioration': 3, 'Unsupported Growth': 0, 'Weak Downside Stability': 13} | {'Deteriorating': 5, 'Stable': 47, 'Recovering': 6} |
| fixture_concentrated | {'Defensive': 4, 'Growth-Led': 4, 'Mixed / Neutral': 37, 'Stressed': 13} | {'Diversification Erosion': 0, 'High Risk Concentration': 58, 'Low Return Efficiency': 13, 'Rapid Structural Deterioration': 3, 'Unsupported Growth': 36, 'Weak Downside Stability': 9} | {'Deteriorating': 5, 'Stable': 45, 'Recovering': 8} |
| fixture_single | {'Defensive': 4, 'Growth-Led': 5, 'Mixed / Neutral': 40, 'Stressed': 9} | {'Diversification Erosion': 0, 'High Risk Concentration': 58, 'Low Return Efficiency': 13, 'Rapid Structural Deterioration': 3, 'Unsupported Growth': 36, 'Weak Downside Stability': 9} | {'Deteriorating': 5, 'Stable': 44, 'Recovering': 9} |
| fixture_defensive | {'Defensive': 45, 'Mixed / Neutral': 13} | {'Diversification Erosion': 0, 'High Risk Concentration': 58, 'Low Return Efficiency': 54, 'Rapid Structural Deterioration': 0, 'Unsupported Growth': 0, 'Weak Downside Stability': 0} | {'Deteriorating': 0, 'Stable': 58, 'Recovering': 0} |
| fixture_seed1701 | {'Balanced Growth': 25, 'Defensive': 8, 'Mixed / Neutral': 9, 'Stressed': 16} | {'Diversification Erosion': 3, 'High Risk Concentration': 0, 'Low Return Efficiency': 10, 'Rapid Structural Deterioration': 3, 'Unsupported Growth': 5, 'Weak Downside Stability': 13} | {'Deteriorating': 4, 'Stable': 47, 'Recovering': 7} |

同方向、不同结构的首个预定义匹配案例 / First matching same-direction/different-structure example (selected without future outcomes):

```json
{
  "date": "2011-03-31T00:00:00",
  "months": 6,
  "direction": "Strong Bullish",
  "portfolios": {
    "equal": {
      "state": "Mixed / Neutral",
      "flags": [],
      "transition": "Stable",
      "confidence": "Moderate",
      "probability_up": 0.8996,
      "scores": {
        "Growth Strength": 74.75967249138492,
        "Downside Stability": 94.78497256675973,
        "Diversification Quality": 78.46062290576208,
        "Return Efficiency": 98.77966947062767,
        "Structural Resilience": 95.66439587578208
      }
    },
    "concentrated": {
      "state": "Mixed / Neutral",
      "flags": [
        "High Risk Concentration"
      ],
      "transition": "Stable",
      "confidence": "Moderate",
      "probability_up": 0.8322,
      "scores": {
        "Growth Strength": 68.54188018369712,
        "Downside Stability": 94.0193194663483,
        "Diversification Quality": 15.214536476240756,
        "Return Efficiency": 89.72468187421082,
        "Structural Resilience": 99.78238471583518
      }
    }
  }
}
```

## Baseline Comparison / 基线比较

Traditional baseline 是 return与Sharpe同号规则；透明但有限，不代表完整传统分析。它与Evolance覆盖率不同，hit rate不能单独等价比较。Monte-Carlo-only 与Evolance的方向和命中率完全一致是设计要求：后者未改分布或方向规则。
Directional identity with MC-only is expected, not a failure or a victory. The research contribution is structural context and confidence segmentation, not better simulation mathematics.

High/Low 对比逐组合、期限记录。合成上限导致没有High组，不能据此验证High优于Low；Moderate与Low的差异也是选择后描述性结果，不能视为已校准置信度或因果效果。
No synthetic High group exists. Confidence-group differences cannot establish calibration; overlapping observations and endogenous downgrades confound interpretation.

| Dataset | Months | Confidence | Complete | Directional N | Hit rate | Mean return | Mean drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fixture_equal | 6 | Low | 10 | 1 | 0.0000 | 0.1222 | -0.1109 |
| fixture_equal | 6 | Moderate | 42 | 42 | 0.5714 | 0.0731 | -0.0953 |
| fixture_equal | 6 | High | 0 | 0 | N/A | N/A | N/A |
| fixture_equal | 12 | Low | 9 | 2 | 0.5000 | 0.2656 | -0.1212 |
| fixture_equal | 12 | Moderate | 38 | 38 | 0.5000 | 0.1104 | -0.1786 |
| fixture_equal | 12 | High | 0 | 0 | N/A | N/A | N/A |
| fixture_concentrated | 6 | Low | 19 | 6 | 0.1667 | 0.1846 | -0.0913 |
| fixture_concentrated | 6 | Moderate | 33 | 33 | 0.7576 | 0.0812 | -0.0799 |
| fixture_concentrated | 6 | High | 0 | 0 | N/A | N/A | N/A |
| fixture_concentrated | 12 | Low | 16 | 10 | 0.3000 | 0.3685 | -0.1025 |
| fixture_concentrated | 12 | Moderate | 31 | 31 | 0.6129 | 0.1357 | -0.1577 |
| fixture_concentrated | 12 | High | 0 | 0 | N/A | N/A | N/A |
| fixture_single | 6 | Low | 19 | 6 | 0.1667 | 0.1979 | -0.0907 |
| fixture_single | 6 | Moderate | 33 | 33 | 0.7576 | 0.0839 | -0.0798 |
| fixture_single | 6 | High | 0 | 0 | N/A | N/A | N/A |
| fixture_single | 12 | Low | 17 | 10 | 0.4000 | 0.3913 | -0.0992 |
| fixture_single | 12 | Moderate | 30 | 30 | 0.6333 | 0.1364 | -0.1578 |
| fixture_single | 12 | High | 0 | 0 | N/A | N/A | N/A |
| fixture_defensive | 6 | Low | 52 | 0 | N/A | 0.0027 | -0.0011 |
| fixture_defensive | 6 | Moderate | 0 | 0 | N/A | N/A | N/A |
| fixture_defensive | 6 | High | 0 | 0 | N/A | N/A | N/A |
| fixture_defensive | 12 | Low | 47 | 0 | N/A | 0.0053 | -0.0014 |
| fixture_defensive | 12 | Moderate | 0 | 0 | N/A | N/A | N/A |
| fixture_defensive | 12 | High | 0 | 0 | N/A | N/A | N/A |
| fixture_seed1701 | 6 | Low | 18 | 4 | 0.0000 | 0.0749 | -0.1186 |
| fixture_seed1701 | 6 | Moderate | 34 | 34 | 0.5588 | 0.0698 | -0.0909 |
| fixture_seed1701 | 6 | High | 0 | 0 | N/A | N/A | N/A |
| fixture_seed1701 | 12 | Low | 8 | 1 | 0.0000 | 0.1525 | -0.1822 |
| fixture_seed1701 | 12 | Moderate | 39 | 39 | 0.6154 | 0.1316 | -0.1530 |
| fixture_seed1701 | 12 | High | 0 | 0 | N/A | N/A | N/A |

完整观测数包含Neutral，但命中率分母只计有方向的观测；Low组可能只有1–2个方向样本，不能将其0%或50%视为稳定估计。 / Complete counts include Neutral; hit-rate denominators do not. Some Low groups have only one or two directional observations.

## Directional Conclusions / 明确方向结论

以下为最新等权合成案例（日期 2015-09-30），不代表真实当前市场。
Latest equal-weight synthetic example, not a live-market forecast.

### 6-Month Outlook / 6个月展望

```json
{
  "months": 6,
  "absolute_direction": "Strong Bullish",
  "confidence": "Moderate",
  "relative_outlook": "Likely Outperform",
  "relative_confidence": "Moderate",
  "current_state": "Balanced Growth",
  "candidate": "Balanced Growth",
  "transition": "Stable",
  "flags": [],
  "probability_up": 0.9738,
  "loss_probability": 0.0262,
  "p10": 0.0494064009705189,
  "p50": 0.1521530117245986,
  "p90": 0.26599773386407716
}
```

模型判断未来 6 个月上涨概率高于下跌概率。 结构支撑相对平衡，未触发恶化转化。 置信度：Moderate。 基于合成/演示数据。 概率依赖既有 GBM 假设，不代表已校准的预测准确率。本结果仅用于研究与教育目的，不构成任何投资建议。

The model assigns a higher probability to a rise than a fall over 6 months. Structural support is relatively balanced with no active deterioration transition. Confidence: Moderate. Based on synthetic/demo data. Probabilities are conditional on the unchanged GBM assumptions, not calibrated forecast accuracy. For educational and research purposes only. Not investment advice.

### 12-Month Outlook / 12个月展望

```json
{
  "months": 12,
  "absolute_direction": "Strong Bullish",
  "confidence": "Moderate",
  "relative_outlook": "Likely Outperform",
  "relative_confidence": "Moderate",
  "current_state": "Balanced Growth",
  "candidate": "Balanced Growth",
  "transition": "Stable",
  "flags": [],
  "probability_up": 0.9966,
  "loss_probability": 0.0034,
  "p10": 0.16385869479827872,
  "p50": 0.327417326221919,
  "p90": 0.5123479792850676
}
```

模型判断未来 12 个月上涨概率高于下跌概率。 结构支撑相对平衡，未触发恶化转化。 置信度：Moderate。 基于合成/演示数据。 概率依赖既有 GBM 假设，不代表已校准的预测准确率。本结果仅用于研究与教育目的，不构成任何投资建议。

The model assigns a higher probability to a rise than a fall over 12 months. Structural support is relatively balanced with no active deterioration transition. Confidence: Moderate. Based on synthetic/demo data. Probabilities are conditional on the unchanged GBM assumptions, not calibrated forecast accuracy. For educational and research purposes only. Not investment advice.


## Interpretation Value and Redundancy / 解释价值与重复

State与Flags分离解决v1集中标签覆盖防御/增长叙事的问题；三期单向衰减不再惩罚改善；候选/确认迟滞记录减少即时翻转。相同概率方向下，结构和置信度可不同，并有可追溯证据。
Architecture provides a clearer separation of dominant state, specific weaknesses, changes and conditional direction. It does not add an independent evidence source or prove reader usefulness without a user study.

重复计数减少，但未消除：Sortino仍使用下行偏差；Growth相对收益与IR相关；Resilience显式由前四维衍生，并不是独立第五因子。绝对风险贡献份额是约定，而非唯一风险分解。
Overlap is reduced, not eliminated. Resilience is a directional summary of existing dimensions.

重要冻结规则局限：两只等权、完全相同的资产可得到Risk Breadth100、DR分数0，最终DQ60；effective contributors并不等于独立风险来源。没有因该结果修改60/40权重。单资产集中标签不等于ETF底层不分散，未做ETF穿透。
Identical equal-weight exposures can score DQ60: equal risk contributions do not imply independent factors. This limitation is retained and explicitly tested, not tuned away.

普通确认规则和SR严重压力覆盖可能使Candidate与Confirmed不同；退出Stressed要求同一非压力候选连续两次及当前DS>45。这些预先声明的选择会延迟转化。
Hysteresis can lag genuine changes, and severe-resilience confirmation can differ from the raw candidate. Missing ratios/flat histories limit classification.

## Evaluation A–I / 研究评价

| Criterion | Assessment |
|---|---|
| A Financial grounding | Established transparent formulas implemented; conventions documented |
| B Interpretation architecture | State + independent flags + transitions + conditional direction implemented |
| C Reduced double counting | Improved versus v1, residual overlaps disclosed |
| D Structural differentiation | Demonstrated synthetically; real usefulness not established |
| E Useful explanation | Auditable examples, no independent user evaluation |
| F Probabilistic direction | Concrete 6M/12M labels, distributions and confidence available |
| G No look-ahead | Prefix/future-perturbation tests; outcomes kept separate |
| H Honest uncertainty | Conditional probabilities, censoring, synthetic cap, unavailable groups explicit |
| I Real historical evidence | Unavailable: no adequate real history; no empirical directional claim |

建议 Revise and Retest：当前可作为研究工程成果，不建议接入正式产品。优先取得许可明确的真实数据，在冻结配置下复测并做解释可用性评估；不要求预测优越性，但不能从合成结果声称真实方向准确率。
Recommendation: retain as research, collect permitted real histories and independently evaluate explanation usefulness under the unchanged specification before productization.

## Reproduction / 复现

`python -m research.evolance_v1_1_validation` always runs deterministic fixtures, then reads approved local cache. Add `--try-live` for the existing Yahoo downloader. With `--csv history.csv --kind real --source "declared permitted source" --price-type adjusted --weights "FUND.X:1" --benchmark SPY`, load local data (Date first, then exact ticker columns). Use `--kind synthetic` for demo CSVs; provenance is self-declared, not independently verified. Relative paths are resolved locally; source text is recorded in output and should not contain private data.

v1 files are byte-preserved; v0.3 and UI unchanged. No new dependency/provider, commit, push, merge, tag or release.

## Tests / 测试

```text
2026-10-09
Command: python -m pytest -q
257 passed, 186 subtests passed in 19.19s
189 v0.3 +31 preserved v1 +37 new v1.1 tests. Offline suite.
```
