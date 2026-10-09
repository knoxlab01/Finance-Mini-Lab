"""Render the derived study outputs into a bilingual, auditable research report."""
import json
from pathlib import Path
import pandas as pd
from research.evolance_v1_1_real_validation import OUTPUT, ROOT, stats


def table(frame, columns):
    def cell(v):
        if pd.isna(v):return 'N/A'
        if isinstance(v,float):return f'{v:.4f}'
        return str(v).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'+'\n'.join('| '+' | '.join(cell(r[c]) for c in columns)+' |' for _,r in frame.iterrows())


def run():
    s=json.loads((OUTPUT/'summary.json').read_text())
    def read(name):return pd.read_csv(OUTPUT/(name+'.csv'))
    comparisons=read('comparison_summary');confidence=read('confidence_calibration');states=read('state_outcomes');transitions=read('transition_outcomes');flags=read('flag_outcomes')
    cases=read('interpretation_cases');failures=read('failure_cases')
    timelines=pd.concat([read(name+'_timeline') for name in s['portfolios']],ignore_index=True)
    records=timelines.to_dict('records')
    mc=[]
    for months in [6,12]:
        for level in ['High','Moderate','Low']:
            selected=[r for r in records if r['months']==months and r['mc_only_confidence']==level and r['direction']!='Neutral / Uncertain']
            mc.append(dict(months=months,confidence=level,**stats(selected)))
    pd.DataFrame(mc).to_csv(OUTPUT/'mc_confidence_calibration.csv',index=False)
    # No hand-picked historical event labels: rank signals by contemporaneous evidence.
    issued=timelines[timelines.months==6]
    episodes=pd.concat([issued.nlargest(3,'Growth Strength').assign(selection='highest contemporaneous Growth Strength'),
                        issued.nsmallest(3,'Downside Stability').assign(selection='lowest contemporaneous Downside Stability'),
                        issued[issued.transition=='Recovering'].sort_values(['date','portfolio']).head(3).assign(selection='earliest Recovering')])
    episodes.to_csv(OUTPUT/'episode_examples.csv',index=False)
    testlog=ROOT/'real_validation_tests.log'
    testresult=testlog.read_text(encoding='utf-8-sig').strip().splitlines()[-1] if testlog.exists() else 'Not recorded'
    (OUTPUT/'test_result.txt').write_text(testresult+'\n',encoding='utf-8')
    text=f'''# Evolance v1.1 — Real Historical Validation / 真实历史验证

**Recommendation B: Productize as Interpretation / Decision-Support Layer, without predictive-superiority claims. / 建议 B：仅作为解释与决策辅助层产品化，不声称预测优势。**

本轮完成真实数据的冻结规则回溯验证；不是交易策略、市场预测认证或 UI 上线授权。建议限于透明展示风险结构与不确定性，Confidence 不可作为已校准成功概率。实际用户可理解性仍需验证。
This is frozen-rule empirical research, not a trading-strategy approval or deployment. Structural context has descriptive value; user comprehension remains untested. Confidence is an ordinal explanation label, not a calibrated success probability.

## Integrity and provenance / 完整性与来源

Frozen Spec SHA-256: `{s['spec_sha256']}`

Pre-evaluation method SHA-256: `{s['method_sha256']}`. [Registered method](evolance_v1_1_real_method.md).

Kaggle Huge Stock Market Dataset, Boris Marjanovic; user-declared source-adjusted Close, including dividends/splits per supplied documentation. Local manifest/source rights and adjustment claims are not independently authenticated. No online access, new provider, raw exports, source modification, frozen-parameter changes or empirical tuning.
数据来自本地私有文件，复权语义为来源声明而非独立验证。原始价格不随本报告发布。

Aligned history: **{s['period'][0]} — {s['period'][1]}, {s['aligned_rows']} prices**. No fill/backfill. SPY's common start truncates earlier asset history. Five portfolios share this exact calendar; 141 completed-month signals each, 135 complete 6M and 129 complete 12M outcomes each. Pooled: 705 signals/horizon; 675/645 complete outcomes; 30/60 censored. Pooled counts are correlated portfolio-month observations, not independent market episodes.

Two five-day gaps: 2006-12-29 → 2007-01-03; 2012-10-26 → 2012-10-31. All four assets agree. They are consistent with New Year/Ford mourning closure and Hurricane Sandy. No authoritative local calendar or internet verification was available; calendar attribution remains explicitly uncertain and non-blocking. No source rows changed. Readiness remains READY_WITH_WARNINGS, not forcibly upgraded.

## Method and baselines / 方法与基线

等权33.33/33.33/33.34；集中70/15/15；AAPL/MSFT/NVDA各100%；基准SPY。固定权重每日再平衡，不计税费/交易成本。252收益/253价格回溯，完成自然月末发布；先生成全部信号，再独立计算126/252交易日真实结果。不完整结果保留缺失，绝不填0。

Traditional exact rule: trailing portfolio cumulative return >0 AND Sharpe >0 ⇒ Bullish; both <0 ⇒ Bearish; otherwise Neutral / Uncertain. This rule was recorded before calculating comparative performance and already existed in frozen research. It represents a simple baseline, not all traditional analysis.

MC-only uses the existing monthly GBM engine, frozen 5000 paths/seed/1-year horizon, probability bands and 6M/12M median guardrails. Evolance uses exactly the same distributions/directions; structural evidence only changes confidence/explanation. Therefore identical MC-only and Evolance directional performance is required, not an empirical improvement.

Hit rate excludes Neutral and incomplete outcomes; zero return is a directional miss. `neutral_coverage` uses all issued signals; `complete_neutral_coverage` uses complete outcomes. Confidence moments below use directional outcomes only. State/transition/flag moments include Neutral. Standard deviation uses ddof=1. Rates/returns/drawdowns in tables are fractions, not percent. Every CSV contains portfolio-specific and pooled groups, censor counts, medians, dispersion and bullish/bearish subgroups.

## Three-way directional results / 三方方向比较

{table(comparisons[comparisons.portfolio=='ALL'],['months','system','signals','complete','directional_n','neutral_n','hit_rate','neutral_coverage','complete_neutral_coverage','bullish_mean_return','bullish_mean_drawdown','bearish_mean_return','bearish_mean_drawdown'])}

Evolance/MC 6M 62.83% (565 directional), 12M 62.19% (566), versus Traditional 61.09% (663), 60.35% (633). Different coverage and dependence prevent superiority claims. The overall positive-return frequencies are 73.78%/77.36%; thus >50% hits alone are not impressive in this selected growth-heavy universe. Bearish signals are frequently followed by positive returns (mean +26.09%/+48.70%). No profitable trading strategy, risk-adjusted alpha, or predictive superiority is established.
方向有历史描述信息，但看空信号常错过反弹；未确立预测优势，更不能把略高于传统基线的比例当显著胜出。

{table(comparisons[comparisons.portfolio!='ALL'],['portfolio','months','system','directional_n','hit_rate','neutral_coverage','bullish_n','bearish_n'])}

## Confidence discrimination / 置信度分层

{table(confidence[confidence.portfolio=='ALL'],['months','confidence','directional_n','hit_rate','mean_return','median_return','mean_drawdown','std_return'])}

Pooled High > Moderate > Low hit rates at both horizons. High also has less return dispersion and milder mean drawdown. However, Moderate has higher mean raw returns than High; dispersion is not monotonic across Moderate/Low. **Discrimination is descriptive; empirical probability calibration is not established.** High comes only from multi-asset portfolios: the concentration downgrade prevents all single-asset High signals. Low samples in equal-weight/concentrated portfolios are small. Portfolio composition, bullish/bearish mix, overlap and selection confound pooled ordering.
汇总命中率分层有用，但并非独立校准；High 组完全不含单资产样本，不能把组间差异全归因于结构降级。

{table(confidence[confidence.portfolio!='ALL'],['portfolio','months','confidence','directional_n','hit_rate','mean_drawdown','evidence'])}

Pure MC-only confidence segmentation (no structural deductions), for context; no matched causal improvement claim:

{table(pd.DataFrame(mc),['months','confidence','directional_n','hit_rate','mean_drawdown','std_return'])}

## Primary States / 主状态

{table(states[states.portfolio=='ALL'],['months','group','signals','complete','mean_return','median_return','mean_drawdown','positive_frequency','std_return'])}

12M Balanced Growth has 28 observations, mean return 41.62% and mean drawdown -13.24%; Growth-Led has 341, 30.01%, -26.40%; Stressed has 129, 35.72%, -28.94%; Mixed has 147, 23.73%, -17.70%. Defensive has no observations: no conclusion. Stressed can precede large rebounds AND deep drawdowns; it is a risk-context label, not a sell instruction. These conditional associations are not causal.
Stressed 并不等于未来负收益；高收益与深回撤可以并存。Defensive 无样本，不做外推。

## Transitions / 转化

{table(transitions[transitions.portfolio=='ALL'],['months','group','signals','complete','mean_return','median_return','mean_drawdown','positive_frequency','std_return'])}

Deteriorating has worse mean future drawdowns than Stable: 6M -23.92% (64) vs -17.53% (530); 12M -33.91% (63) vs -23.20% (501). This supports risk differentiation in this sample, not reliable advance-warning accuracy.
Recovering has higher 6M mean return (20.77%,81) than Deteriorating (13.02%,64), with milder drawdown. At 12M its return (30.29%) is below Stable (31.31%); compared with Stressed it also does not consistently improve returns. Recovery evidence is partial, with 35 negative-return records across horizons.
Deteriorating 与较深回撤相关；Recovering 只有部分改善证据，不能承诺恢复。

## Structural flags / 结构标签

{table(flags[(flags.portfolio=='ALL') & flags.active],['months','flag','signals','complete','mean_return','median_return','mean_drawdown','directional_n','hit_rate','evidence'])}

Weak Downside Stability: 12M mean drawdown -34.95% (180). Unsupported Growth + Deteriorating: -41.92% (20), an exploratory small joint sample, not a validated trading rule. Rapid Structural Deterioration has only 12 complete 12M observations. Diversification Erosion has no complete 12M outcomes, so no forward claim; terminal signals are not zero-valued outcomes. Inactive flag comparators are in flag_outcomes.csv. Flags overlap and are not independent factors.

## Portfolio structure / 组合结构

Per 141 signal dates: concentrated has 79 High Risk Concentration flags vs equal-weight 0, and 90 Unsupported Growth vs 8. Diversification Erosion is 0 vs 4, so the concentrated portfolio does NOT have more of every weakness. Capital weights and risk-contribution breadth are distinct; equal weights do not guarantee independent exposures.
Single assets have concentration flags at all 141 dates and no High confidence; this is sensible as asset-level concentration but limits differentiation and is not ETF look-through. 12M hit rates: AAPL 52.50% (120), MSFT 59.80% (102), NVDA 62.39% (109); equal-weight 72.41% (116), concentrated 63.87% (119). Do not infer equal weighting is universally superior from these selected assets.

## Interpretation advantage, redundancy and failures / 解释优势、重复与失败

Predeclared matching: same date/horizon, same MC direction, P(up) difference <=5 percentage points, differing structure. All 476 pairs retained: **226 useful drawdown associations, 168 redundant, 82 misleading** by the predeclared audit convention. These categories measure a simple flag-count/state severity association, not user benefit or framework accuracy. They are highly dependent. No selective success-only export.
Earliest example in each category (not chosen for attractive returns):

{table(cases.groupby('category',sort=False).head(1),['date','months','category','direction','higher_severity_portfolio','higher_severity_state','higher_severity_flags','higher_severity_forward_return','higher_severity_forward_drawdown','other_portfolio','other_forward_return','other_forward_drawdown'])}

2006-02-28: similar Strong Bullish MC signals, NVDA's concentration/unsupported-growth flags accompany a -43.51% subsequent 6M drawdown versus equal-weight -30.08%; both earn positive terminal returns. Structure clarifies path risk, not the sign prediction. The same date concentrated/equal-weight has near-identical drawdowns despite different flags (redundant). 2006-04-28 12M: more-flagged AAPL has milder drawdown than NVDA (misleading).
方向层完全重复 MC；新增解释来自风险集中、下行脆弱性和状态转化的可追溯组合。没有新增独立信息源，未做用户理解实验。

## Failure Cases / 失败案例

Counts across portfolio/horizon records (categories overlap): {json.dumps(s['failure_counts'])}. False-alarm proxy (Deteriorating and future drawdown >-5%) has **0** cases under this strict definition; this does not establish zero false alarms generally. An ending gain is not itself a false risk warning if the path draws down substantially.
All 386 missed-deterioration proxy records (non-Deteriorating with <=-20% future drawdown) and all 60 High-confidence misses are retained. A Stable label is not a guarantee of safety. These are operational audits, not precision/recall for uniquely defined market events.

{table(failures.groupby('kind',sort=False).head(1),['kind','date','months','portfolio','direction','confidence','state','transition','forward_return','forward_drawdown'])}

Notable failures: equal-weight 2006-02-28 Strong Bullish/High/Stable precedes -30.08% 6M drawdown despite a positive terminal return; 2007-06-29 Strong Bullish/High loses over the following year; 2008-07-31 Strong Bearish/High ends positive after a deep drawdown. Recovering 2009-08-31 ends slightly negative at 12M. All such observations remain in failure_cases.csv.

## Timeline-selected episodes / 时间线自然识别片段

No famous-event labels were hard-coded into signals. The following selects highest contemporaneous Growth Strength, lowest Downside Stability, and earliest Recovering observations; ties use existing deterministic row order. This is descriptive context, not independent validation.

{table(episodes,['selection','date','portfolio','Growth Strength','Downside Stability','state','transition','direction','forward_return','forward_drawdown'])}

## Limits and product decision / 局限与产品建议

**B — Productize as Interpretation / Decision-Support Layer; do not claim predictive superiority.** Distinct structural summaries and descriptive downside differentiation justify an educational interpretation layer. Display its limitations and retain the research identity; this recommendation is not an instruction to change UI or deploy. Claims of calibrated confidence or investment timing remain unsupported.

Limitations: three retrospectively chosen surviving US technology winners; SPY benchmark; sample ends in 2017 and excludes later regimes; no untouched empirical holdout; overlapping horizons and correlated portfolios; modern adjusted-data revisions may use later corporate actions; user-declared license/adjustment; unverified holiday attribution; constant 4% risk-free convention; daily rebalancing without costs; frozen GBM limitations; tiny/empty states and flags; endogenous confidence groups; no causal isolation, human usability study or multiplicity adjustment. No IID bootstrap CIs are presented because they would overstate precision; robust time-block and cross-asset evaluation remains future work, not a reason to tune current rules.

Portfolio/resume assessment: **yes, a reasonable finance/data research-engineering portfolio standard is met**, separately from predictive skill. Financial grounding, independent state/flag/transition architecture, frozen-spec discipline, reproducible real walk-forward evaluation, ordinal confidence, explicit censoring, failure audit and private-data boundaries are concrete contributions. Present as an explainable portfolio research framework evaluated on historical data, not a market-beating prediction engine.
简历创新标准基本满足；贡献在工程与解释框架、研究纪律和失败分析，而非新金融因子或预测优势。

## Reproduction and validation / 复现与检查

```powershell
.\\.venv\\Scripts\\python.exe -m research.evolance_v1_1_real_validation
.\\.venv\\Scripts\\python.exe -m pytest -q
.\\.venv\\Scripts\\python.exe -m research.evolance_v1_1_real_report
```

Requires authorized local private files/manifest. New datasets/calendar gaps need review; no network fallback. The study writes only its separate real-results directory. Report generation reads derived outputs only. Timeline CSVs have two rows/date (6M/12M), traditional metrics, all five dimensions, candidate/confirmed state, flags, transition, absolute/relative confidence, distribution summaries and censored outcomes. No raw price rows or manifest free text are exported.

Tests: **{testresult}**. Offline tests cover future-perturbation/prefix invariance, 126/252 windows, drawdown, censoring, hits/Neutral, grouping, pair audits and explicit export schema. Frozen source/previous research/raw-input SHA checks are performed separately before/after this run. No commit/push/merge/tag/release, UI change or frozen-rule changes.
'''
    (ROOT/'docs/evolance_v1_1_real_validation.md').write_text(text,encoding='utf-8')


if __name__=='__main__':run()
