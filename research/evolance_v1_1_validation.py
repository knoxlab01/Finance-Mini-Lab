"""Frozen v1.1 research runner, no UI/DB/legacy-output mutations.

python -m research.evolance_v1_1_validation
python -m research.evolance_v1_1_validation --try-live
python -m research.evolance_v1_1_validation --csv path.csv --kind real
    --source "user-licensed adjusted history" --price-type adjusted
    --weights "FUND.X:1" --benchmark SPY
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.evolance_validation import regime_fixture
from src.evolance.v1_1.spec import SPEC, SPEC_SHA256, SPEC_VERSION, SPEC_PATH, CORE, load_spec
from src.evolance.v1_1.timeline import walk_forward, state_spells
from src.evolance.v1_1.validation import evaluate_outcomes, summarize
from src.evolance.v1_1.data import approved_real_prices, load_csv

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research" / "evolance_v1_1_results"


def plain(value):
    if isinstance(value, dict) or hasattr(value, 'items'):
        return {k:plain(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [plain(v) for v in value]
    if isinstance(value,np.ndarray):
        return value.tolist()
    return value


def write_json(path,value):
    path.write_text(json.dumps(plain(value),ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def table(columns,rows):
    def fmt(value):
        if value is None:return 'N/A'
        if isinstance(value,float):return f'{value:.4f}'
        return str(value).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*len(columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(x) for x in row)+' |' for row in rows)


def write_spec_document():
    rows=[]
    for dimension,weights in SPEC['dimension_weights'].items():
        for component,weight in weights.items():
            anchor=SPEC['anchors'].get(component,SPEC['anchors']['deterioration'] if dimension=='Structural Resilience' else '100 * normalized ERC breadth')
            rows.append([dimension,component,weight,str(anchor)])
    content=f'''# Evolance v1.1 Frozen Specification

版本 / Version: `{SPEC_VERSION}`

SHA-256 (exact UTF-8 JSON file bytes): `{SPEC_SHA256}`

规范在验证前冻结，运行校验 SHA-256；配置递归只读。不得按历史结果调参。 / Frozen before validation; checked on load and each study. Configuration is recursively read-only. No outcome-driven tuning.

[Machine-readable specification / 机器规范](evolance_v1_1_frozen_spec.json)

## Architecture / 架构

Established Evidence → Five Dimensions → Primary State + Independent Flags → Transition → Forward Distribution → Direction → Confidence + Explanation.

研究目标是 Interpretation Advantage + Decision-Support Advantage，不声称独创金融因子。 / Research targets interpretation and decision support, not new financial factors.

## Dimensions and Anchors / 维度与锚点

固定分段线性插值，区间外端点截断。 / Fixed linear interpolation and endpoint saturation.

{table(['Dimension','Component','Weight','Anchors'],rows)}

## Formula Conventions / 公式约定

- Downside deviation = `sqrt(252 * mean(min(r - daily_rf, 0)^2))`, `daily_rf=(1+0.04)^(1/252)-1`。分母为所有观测，不仅下行观测；目标是日无风险收益。 / All observations enter the denominator.
- Sortino = `(annualized geometric portfolio return - 0.04) / downside deviation`。默认 252 日即尾随累计收益；敏感性窗口用 `product(1+r)^(252/n)-1`。 / Explicit geometric annual-return numerator.
- IR = `mean(r_p-r_b)*252 / (sample_std(r_p-r_b)*sqrt(252))`。Growth 的 Active Return 为两个累计收益之差；IR 分子是日主动收益算术年化，两种含义明确区分。 / Period active return and arithmetic annualized active return serve different documented roles.
- Risk covariance = sample daily covariance ×252；`RC=w*(Sigma*w)/sigma_p`，保留正负号；breadth 使用绝对贡献份额。不是唯一正确的风险分解方法。 / Signed diagnostics retained; absolute-share breadth is a research convention.
- 零下行偏差、零跟踪误差或零组合波动导致相应比率 unavailable，不用无穷大或满分代替。缺失组件不重新分配权重。 / Undefined ratios remain unavailable; no silent reweighting.

## Primary State / 主状态

- Stressed: DS<40 and RE<45, or DS<35 and SR<50.
- Growth-Led: GS≥70 and GS−median(DS,DQ,RE)≥15.
- Defensive: DS≥70 and GS<50.
- Balanced Growth: GS≥60, DS/DQ/RE≥55, neither Growth-Led nor Stressed.
- Otherwise Mixed / Neutral. Precedence: Stressed > Growth-Led > Defensive > Balanced Growth. Missing conditions do not match; availability is disclosed.

## Independent Flags / 独立标签

Risk Breadth<35; DS<40; RE<40; DQ three-evaluation decline≥10; SR<40 with at least two core declines≥10; GS≥70 with DS<45 or DQ<45. All matching flags coexist.

## Transition and Hysteresis / 转化与迟滞

Resilience compares t with t−3 evaluations. `max(0, old-current)` means improvement is never penalized. First three evaluations are unavailable.

Deteriorating: at least two core three-period declines≥5 and SR<55, or DS/DQ decline≥15. Recovering: prior six evaluations include candidate/confirmed Stressed or SR<50; latest two intervals show at least two improvements≥5, with neither DS nor DQ falling more than 5. Deteriorating wins simultaneous matches; otherwise Stable. Availability is separate from the Stable label.

初始化 Confirmed 为 Mixed / Neutral（provisional）。新 Candidate 连续出现两次才确认；DS<30 且 RE<35，或 SR<30，可立即确认 Stressed。退出 Stressed 同时适用普通连续相同候选规则、候选非 Stressed、当前 DS>45。只要求当前 DS>45。严重压力可覆盖确认，但保留原始 Candidate。 / These initialization and stress-exit interpretations resolve unspecified persistence details before testing.

## Forward Direction / 未来方向

严格调用现有一年期引擎，读取第 6/12 月路径；5000 次、seed 20261007、初值100。State 不改变漂移或波动。P10/P50/P90 输出为终值收益率；乘初值可还原终值。 / Same engine, no state-conditioned parameters.

P(up)≥.70 Strong Bullish; [.60,.70) Bullish; (.40,.60) Neutral; (.30,.40] Bearish; ≤.30 Strong Bearish. Median sign must agree; abs(median)<.02 at 6M or <.04 at 12M forces Neutral. Flat outcomes are neither gains nor losses.

Relative bias: active>0 and IR≥.25 -> Likely Outperform; active<0 and IR≤−.25 -> Likely Underperform; otherwise In Line / Uncertain. No relative probability is claimed.

## Confidence / 置信度

Strong agreeing direction starts High, ordinary directional band Moderate, Neutral Low. Each absolute direction/transition contradiction, SR<40, and concentration flag lowers one level; Low floor. Synthetic cap Moderate with explicit notice.

单独输出 relative confidence，避免混淆绝对与相对方向。它从同一基础置信度和共同结构扣减开始，对相对标签与转化冲突再降一级；相对 Neutral 为 Low。缺失 SR 不伪造惩罚，但披露不可用。置信度为有序解释标签，不是准确率。 / Relative confidence is explicitly separate; these implementation conventions were fixed before validation.

## Walk-forward and Baselines / 前向验证与基线

252 returns/253 prices，完成自然月评估，固定非负权重每日再平衡。单期输出先冻结，未来126/252交易日结果独立合并，未完整观察期截尾。Monthly windows overlap; no independent-sample significance claim.

Traditional baseline: trailing return>0 and Sharpe>0 gives Bullish; both<0 gives Bearish; otherwise Neutral. This declared baseline is simple and not all conventional analysis. MC-only uses identical distribution, probability bands and median guardrails, with base confidence and synthetic cap only. Directional equality is expected by construction.

## Reproducibility / 复现

固定配置和随机种子；不以结果优化阈值、权重、状态或方向规则。仅允许记录明确的代码、公式、数据、数值或逻辑错误修复。v1 代码与结论保持原样。 / No empirical tuning; preserve v1 history.
'''
    (ROOT/'docs'/'evolance_v1_1_frozen_spec.md').write_text(content,encoding='utf-8')


def comparison_example(results):
    a=results['fixture_equal']['signals']
    b={row['date']:row for row in results['fixture_concentrated']['signals']}
    for first in a:
        second=b[first['date']]
        if first['scores']['Structural Resilience'] is None:continue
        for months in ('6','12'):
            one,two=first['outlooks'][months],second['outlooks'][months]
            if one['direction']==two['direction'] and one['direction']!='Neutral / Uncertain' and (first['confirmed_state']!=second['confirmed_state'] or first['flags']!=second['flags']):
                return dict(date=first['date'],months=int(months),direction=one['direction'],
                            portfolios={name:dict(state=row['confirmed_state'],flags=row['flags'],transition=row['transition'],
                                                  confidence=row['outlooks'][months]['confidence'],probability_up=row['outlooks'][months]['probability_up'],scores=row['scores'])
                                        for name,row in [('equal',first),('concentrated',second)]})
    return None


def report(summary):
    rows=[]
    confidence_rows=[]
    for name,result in summary['datasets'].items():
        for months,stats in result['statistics'].items():
            e,t,m=stats['evolance'],stats['traditional'],stats['mc_only']
            rows.append([name,months,e['signals'],e['complete'],e['directional_count'],e['directional_hit_rate'],e['neutral_coverage'],t['directional_hit_rate'],m['directional_hit_rate']])
            for level,group in stats['by_confidence'].items():
                confidence_rows.append([name,months,level,group['complete'],group['directional_count'],group['directional_hit_rate'],group['mean_forward_return'],group['mean_forward_drawdown']])
    state_rows=[]
    for name,result in summary['datasets'].items():
        state_rows.append([name,result['state_counts'],result['flag_counts'],result['transition_counts']])
    example=summary['same_direction_example']
    latest=summary['datasets']['fixture_equal']['latest']
    outlook_text=[]
    for months in ('6','12'):
        out=latest['outlooks'][months]
        conclusion=dict(months=int(months),absolute_direction=out['direction'],confidence=out['confidence'],
                        relative_outlook=out['relative_outlook'],relative_confidence=out['relative_confidence'],
                        current_state=latest['confirmed_state'],candidate=latest['candidate_state'],
                        transition=latest['transition'],flags=latest['flags'],probability_up=out['probability_up'],
                        loss_probability=out['loss_probability'],p10=out['p10'],p50=out['p50'],p90=out['p90'])
        outlook_text.append(f"### {months}-Month Outlook / {months}个月展望\n\n```json\n{json.dumps(conclusion,ensure_ascii=False,indent=2)}\n```\n\n{out['explanation']['zh']}\n\n{out['explanation']['en']}\n")
    test_path=OUTPUT/'test_result.txt'
    test_result=test_path.read_text(encoding='utf-8') if test_path.exists() else 'Full suite not yet recorded.'
    content=f'''# Evolance v1.1 Research Report

**Recommendation: Revise and Retest / 修订研究设计并复测，暂不产品化。** 冻结规则不因本轮结果改变；后续修改规范需要另行授权和版本记录。

SPEC_VERSION: `{SPEC_VERSION}`

Frozen specification SHA-256: `{SPEC_SHA256}`

[Frozen rules / 冻结规范](evolance_v1_1_frozen_spec.md) · [JSON](evolance_v1_1_frozen_spec.json) · [Preserved v1 report / v1历史](evolance_v1_research.md)

## Research Objective / 研究目标

一个可解释的动态投资组合状态框架，将成熟金融证据组织为结构状态、风险标签、状态转化与概率化未来展望。
An interpretable dynamic portfolio-state framework that organizes established financial evidence into structural states, risk flags, transitions, and probabilistic forward outlooks.

研究 Interpretation Advantage + Decision-Support Advantage，不声称新金融因子或独立信息优势。 / Established metrics form the evidence layer; original work is their state, transition and explanation architecture.

## Evidence and Data / 证据与数据

Code validation: offline tests. Synthetic validation: original deterministic seven-regime fixture (seed407), four structures; additional seed1701 equal-weight fixture is a synthetic seed check, not a true untouched empirical holdout. Real historical validation: **{summary['real_status']}**.

{chr(10).join('- '+x for x in summary['retrieval_attempts'])}

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

{table(['Dataset','Months','Signals','Complete','Directional N','Evolance hit','Neutral coverage','Traditional hit','MC-only hit'],rows)}

按方向的平均后续收益、按Transition的平均回撤、Primary State/Confidence/各Flag活动与否的计数及表现均在 summary.json 分组表中提供。截尾记录保留于 outcomes.csv，不填零。
Detailed grouped results include mean returns by direction, drawdowns by transition, primary states, confidence and active/inactive flags. Censored outcomes remain missing.

## State / Flags / Transition / 结构结果

{table(['Dataset','Confirmed states','Flags','Transitions'],state_rows)}

同方向、不同结构的首个预定义匹配案例 / First matching same-direction/different-structure example (selected without future outcomes):

```json
{json.dumps(example,ensure_ascii=False,indent=2)}
```

## Baseline Comparison / 基线比较

Traditional baseline 是 return与Sharpe同号规则；透明但有限，不代表完整传统分析。它与Evolance覆盖率不同，hit rate不能单独等价比较。Monte-Carlo-only 与Evolance的方向和命中率完全一致是设计要求：后者未改分布或方向规则。
Directional identity with MC-only is expected, not a failure or a victory. The research contribution is structural context and confidence segmentation, not better simulation mathematics.

High/Low 对比逐组合、期限记录。合成上限导致没有High组，不能据此验证High优于Low；Moderate与Low的差异也是选择后描述性结果，不能视为已校准置信度或因果效果。
No synthetic High group exists. Confidence-group differences cannot establish calibration; overlapping observations and endogenous downgrades confound interpretation.

{table(['Dataset','Months','Confidence','Complete','Directional N','Hit rate','Mean return','Mean drawdown'],confidence_rows)}

完整观测数包含Neutral，但命中率分母只计有方向的观测；Low组可能只有1–2个方向样本，不能将其0%或50%视为稳定估计。 / Complete counts include Neutral; hit-rate denominators do not. Some Low groups have only one or two directional observations.

## Directional Conclusions / 明确方向结论

以下为最新等权合成案例（日期 {latest['date'][:10]}），不代表真实当前市场。
Latest equal-weight synthetic example, not a live-market forecast.

{chr(10).join(outlook_text)}

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
| I Real historical evidence | {summary['real_status']} |

建议 Revise and Retest：当前可作为研究工程成果，不建议接入正式产品。优先取得许可明确的真实数据，在冻结配置下复测并做解释可用性评估；不要求预测优越性，但不能从合成结果声称真实方向准确率。
Recommendation: retain as research, collect permitted real histories and independently evaluate explanation usefulness under the unchanged specification before productization.

## Reproduction / 复现

`python -m research.evolance_v1_1_validation` always runs deterministic fixtures, then reads approved local cache. Add `--try-live` for the existing Yahoo downloader. With `--csv history.csv --kind real --source "declared permitted source" --price-type adjusted --weights "FUND.X:1" --benchmark SPY`, load local data (Date first, then exact ticker columns). Use `--kind synthetic` for demo CSVs; provenance is self-declared, not independently verified. Relative paths are resolved locally; source text is recorded in output and should not contain private data.

v1 files are byte-preserved; v0.3 and UI unchanged. No new dependency/provider, commit, push, merge, tag or release.

## Tests / 测试

```text
{test_result.strip()}
```
'''
    (ROOT/'docs'/'evolance_v1_1_research.md').write_text(content,encoding='utf-8')


def run(args):
    load_spec()
    OUTPUT.mkdir(parents=True,exist_ok=True)
    write_spec_document()
    fixture,_=regime_fixture()
    weights={'AAPL':.3333,'MSFT':.3333,'NVDA':.3334}
    structures={'equal':weights,'concentrated':{'AAPL':.90,'MSFT':.05,'NVDA':.05},'single':{'AAPL':1.},'defensive':{'RESERVE':1.}}
    datasets=[('fixture_'+name,fixture,w,'SPY',dict(kind='synthetic',source='designed regime fixture seed407',price_type='synthetic')) for name,w in structures.items()]
    other,_=regime_fixture(seed=1701)
    datasets.append(('fixture_seed1701',other,weights,'SPY',dict(kind='synthetic',source='seed1701 regime fixture',price_type='synthetic')))
    results={}
    # Complete synthetic validation before attempting current real-data routes.
    def analyze(name,prices,w,benchmark,metadata):
        result=walk_forward(prices,w,benchmark,synthetic=metadata['kind']!='real')
        rows=result['rows']
        outcomes=evaluate_outcomes(prices,w,rows)
        results[name]=dict(signals=rows,statistics=summarize(outcomes),spells=state_spells(rows),
                           metadata=metadata,weights=w,benchmark=benchmark,
                           prices_sha256=hashlib.sha256(prices.to_csv(float_format='%.12f').encode()).hexdigest())
        write_json(OUTPUT/(name+'_signals.json'),rows)
        pd.DataFrame([{**r,'flags':json.dumps(r['flags'])} for r in outcomes]).to_csv(OUTPUT/(name+'_outcomes.csv'),index=False,float_format='%.8f')
        timeline=[]
        for row in rows:
            timeline.append(dict(date=row['date'],available_at=row['available_at'],**row['scores'],
                                 candidate_state=row['candidate_state'],confirmed_state=row['confirmed_state'],
                                 transition=row['transition'],flags=json.dumps(row['flags']),
                                 state_duration_observations=row['state_duration_observations'],
                                 **{k:v for k,v in row['metrics'].items() if not isinstance(v,(list,dict))}))
        pd.DataFrame(timeline).to_csv(OUTPUT/(name+'_timeline.csv'),index=False,float_format='%.8f')
        np.savez_compressed(OUTPUT/(name+'_latest_terminal_returns.npz'),**result['latest_terminal_returns'])
    for item in datasets:analyze(*item)
    attempts=[]
    if args.csv:
        if not args.kind or not args.source or not args.price_type:
            raise ValueError('--csv requires --kind, --source and --price-type')
        prices,metadata=load_csv(args.csv,kind=args.kind,source=args.source,price_type=args.price_type)
        parsed={}
        for item in args.weights.split(','):
            symbol,value=item.split(':')
            if symbol in parsed:raise ValueError('Duplicate holding')
            parsed[symbol]=float(value)
        analyze('local_csv',prices,parsed,args.benchmark,metadata)
        attempts.append('Local CSV supplied; source and real/synthetic status are user-declared')
        real_status='User-declared real CSV evaluated, provenance not independently verified' if metadata['kind']=='real' else 'Unavailable; supplied CSV is synthetic'
    else:
        prices,metadata,attempts=approved_real_prices(ROOT/'data'/'finance_lab.sqlite3',['AAPL','MSFT','NVDA','SPY'],try_live=args.try_live)
        if prices is not None:
            analyze('real_yahoo',prices,weights,'SPY',metadata)
            real_status='Real Yahoo historical validation performed; provider revisions and selection bias remain'
        else:real_status='Unavailable: no adequate real history; no empirical directional claim'
    summary=dict(spec_version=SPEC_VERSION,spec_sha256=SPEC_SHA256,real_status=real_status,retrieval_attempts=attempts,
                 same_direction_example=comparison_example(results),datasets={})
    for name,result in results.items():
        signals=result['signals']
        summary['datasets'][name]={k:v for k,v in result.items() if k!='signals'}
        summary['datasets'][name].update(latest=signals[-1],
            state_counts={state:sum(r['confirmed_state']==state for r in signals) for state in sorted({r['confirmed_state'] for r in signals})},
            flag_counts={flag:sum(flag in r['flags'] for r in signals) for flag in SPEC['flags']},
            transition_counts={t:sum(r['transition']==t for r in signals) for t in ['Deteriorating','Stable','Recovering']},
            confirmed_change_dates=[r['date'] for r in signals if r['state_changed']])
    write_json(OUTPUT/'summary.json',summary)
    report(summary)
    print(json.dumps(dict(spec_sha256=SPEC_SHA256,real_status=real_status,attempts=attempts,
                         fixture_equal=summary['datasets']['fixture_equal']['statistics']),ensure_ascii=False))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--try-live',action='store_true')
    parser.add_argument('--csv')
    parser.add_argument('--kind',choices=['real','synthetic'])
    parser.add_argument('--source')
    parser.add_argument('--price-type',choices=['adjusted','close'])
    parser.add_argument('--weights',default='AAPL:0.3333,MSFT:0.3333,NVDA:0.3334')
    parser.add_argument('--benchmark',default='SPY')
    run(parser.parse_args())
