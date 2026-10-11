# Vexa Methodology / 方法说明

Vexa is the public product developed in Finance Mini Lab; Evolance is its structured interpretation framework. This document connects product methods to existing research records without replacing the frozen specification or rewriting historical reports.

本文连接产品计算方法与既有研究记录。冻结规范与历史报告保留为原始依据；本文适用于 Vexa v0.4.0 候选版本，正式发布与部署仍需单独批准。

## 1. Scope and evidence status

Vexa combines planning, historical portfolio analytics, probabilistic simulation and educational guidance. Evolance supplements conventional measurements with state, pressure, transition and confidence interpretation. It does not introduce new financial factors or establish market-beating predictions.

| Status | Meaning in this project |
| --- | --- |
| **Designed / 设计** | Explicit architecture or behavior, such as independent flags alongside a primary state. |
| **Heuristic / 启发式** | Fixed scoring anchors, thresholds, persistence and confidence deductions; conventions, not learned or empirically optimal parameters. |
| **Observed / 观察** | Descriptive associations in the limited historical sample. |
| **Validated / 已验证** | Tested implementation/reproducibility or execution of the stated walk-forward protocol; this does not certify predictive skill. |
| **Not validated / 未验证** | Predictive superiority, calibrated confidence, trading profitability, causal advantage, broader out-of-sample generalization and user-comprehension benefits. |

## 2. Historical portfolio construction

Implementation: [portfolio_analysis.py](../src/portfolio_analysis.py), [market_data.py](../src/market_data.py), [benchmark.py](../src/benchmark.py).

- Tickers are unique. Finite, nonnegative weights total 100% within 0.01 percentage point, then normalize. This is long-only.
- Positive, date-indexed prices use the intersection of asset/benchmark observations. No forward/back filling; gaps over seven calendar days are rejected.
- Simple returns: `r_i,t = P_i,t / P_i,t-1 - 1`. Portfolio: `r_p,t = sum(w_i * r_i,t)`. Fixed target weights imply idealized **daily rebalancing**, not buy-and-hold.
- Portfolio and benchmark growth both start at 100, including initial wealth. Pearson correlations use aligned asset returns; undefined correlations remain unavailable.
- Fees, taxes, slippage, currency conversion and real rebalancing constraints are excluded. Calendar intersection does not authenticate exchange sessions or corporate actions.

聚合、比较及相关性使用相同区间。每日再平衡是模型假设，不能把结果当作免成本的真实交易记录。

## 3. Traditional analytics

Implementation: [portfolio_metrics.py](../src/portfolio_metrics.py). Product risk-free rate is editable; Evolance research separately fixes 4%.

| Metric | Definition |
| --- | --- |
| Total / cumulative return | `product(1 + r_t) - 1` |
| CAGR | `product(1 + r_t) ** (1 / years) - 1`; years is actual elapsed calendar time divided by 365.25 days |
| Annualized volatility | Sample standard deviation, `ddof=1`, multiplied by `sqrt(252)` |
| Sharpe ratio | `mean(r_t - daily_rf) / sample_std(r_t) * sqrt(252)`; `daily_rf = (1 + annual_rf) ** (1/252) - 1` |
| Drawdown | Wealth divided by running peak minus one, including initial wealth in the peak |
| Maximum drawdown | Minimum drawdown, reported as a negative fraction |

252 sessions per year is an annualization convention, not complete-calendar certification. Calendar CAGR and session-based risk intentionally use different clocks. Invalid returns/date periods, NaN and insufficient history are validated. Undefined zero-volatility ratios are unavailable, not infinite or perfect scores.

风险按 252 日年化，CAGR 按实际日历时长计算；无定义指标不能伪造成优秀结果。

## 4. Future simulation

Implementation: [future_simulation.py](../src/future_simulation.py). At least 60 historical returns are required. With `l_t = log(1 + r_t)`:

```text
g     = mean(l_t) * 252
sigma = sample_std(l_t) * sqrt(252)
mu    = g + sigma^2 / 2
V_next = V * exp(g / 12 + sigma / sqrt(12) * Z), Z ~ N(0,1)
```

Monthly paths implement the exact GBM transition with constant estimated parameters. Product horizons are 1, 3 or 5 years, with 1,000–10,000 simulations and deterministic seeds. Conservative/Base/Optimistic curves use continuous drifts `mu-sigma`, `mu`, `mu+sigma`; these illustrative scenarios are not confidence bounds. Base follows model expected wealth, not median wealth.

P10/P50/P90 are pointwise simulated wealth percentiles, not confidence intervals for accuracy. Loss probability is the fraction of terminal values below starting wealth; flat outcomes are neither gains nor losses. Results are conditional on assumptions and historical inputs. Parameter uncertainty is not modeled.

模拟假设独立正态对数收益及固定参数，不充分覆盖厚尾、制度变化或极端事件；模型内概率不代表已验证的真实未来概率。

## 5. Evolance v1.1 evidence and dimensions

Authoritative rules: [frozen specification](evolance_v1_1_frozen_spec.md), [JSON specification](evolance_v1_1_frozen_spec.json). Implementation: [frozen modules](../src/evolance/v1_1), product adapter [evolance_product.py](../src/evolance_product.py).

Primary lookback: 252 returns / 253 prices at completed calendar-month evaluations. Sensitivity studies use 126/504 returns. Risk-free rate remains frozen at 4%; changing the product's traditional Sharpe input does not change this convention. The latest eligible completed-month snapshot can differ from the full user-selected historical period. Traditional comparison evidence and Evolance interpretation share that snapshot.

| Dimension | Evidence and role |
| --- | --- |
| **Growth Strength** | Trailing compounded absolute return (60%) and portfolio-minus-benchmark period return (40%) |
| **Downside Stability** | Downside deviation (50%) and drawdown magnitude (50%) |
| **Diversification Quality** | Diversification ratio (40%) and risk-contribution breadth (60%) |
| **Return Efficiency** | Information ratio (60%) and Sortino (40%) |
| **Structural Resilience** | Three-evaluation deterioration in Growth Strength (15%), Downside Stability (35%), Diversification Quality (30%) and Return Efficiency (20%) |

Values map to 0–100 through frozen piecewise-linear anchors with endpoint saturation. Anchors are **heuristic**, not fitted from validation. Resilience measures `max(0, previous-current)` declines, never penalizing improvement; first three evaluations are unavailable.

Financial conventions:

- Downside deviation: `sqrt(252 * mean(min(r-daily_rf, 0)^2))`, using **all** observations in the denominator. Sortino uses geometric annual return minus 4% over downside deviation.
- Information ratio: `252 * mean(r_p-r_b) / (sqrt(252) * sample_std(r_p-r_b))`. This arithmetic annualized active-return numerator differs from Growth's difference between compounded returns.
- Annualized sample covariance is `Sigma`. Signed contributions: `RC_i = w_i * (Sigma*w)_i / sigma_p`. Breadth uses absolute contribution shares `q_i`; effective number `1/sum(q_i^2)` is normalized from 1 to the number of positive-weight holdings. Single-holding breadth is zero: asset-level concentration, not ETF look-through.
- Diversification ratio: `sum(w_i*sigma_i) / sigma_p`. Zero portfolio volatility, downside deviation or tracking error makes affected ratios unavailable. Missing components are not silently reweighted.

维度组织既有金融证据。证据不足时产品保留传统分析，明确提示 Evolance 不可用或部分不可用。

## 6. State, flags, transition and hysteresis

GS, DS, DQ, RE and SR abbreviate the five scores. Candidate precedence: **Stressed → Growth-Led → Defensive → Balanced Growth**, otherwise Mixed / Neutral.

| Candidate | Frozen condition |
| --- | --- |
| Stressed | `DS<40 and RE<45`, or `DS<35 and SR<50` |
| Growth-Led | `GS>=70` and `GS-median(DS,DQ,RE)>=15` |
| Defensive | `DS>=70` and `GS<50` |
| Balanced Growth | `GS>=60`, `DS/DQ/RE>=55`, neither Growth-Led nor Stressed |

Unavailable evidence does not satisfy a condition. Independent flags coexist: High Risk Concentration (`breadth<35`), Weak Downside Stability (`DS<40`), Low Return Efficiency (`RE<40`), Diversification Erosion (three-evaluation DQ decline at least 10), Rapid Structural Deterioration (`SR<40` and at least two core declines at least 10), Unsupported Growth (`GS>=70` with `DS<45` or `DQ<45`). Flags are not independent statistical factors.

**Transition:** Deteriorating requires at least two three-evaluation core declines of 5 or more with `SR<55`, or DS/DQ decline of 15 or more. Recovering requires stress evidence in the prior six evaluations, at least two core improvements of 5 or more over the latest two evaluation intervals, and no DS/DQ decline over 5. Deteriorating wins simultaneous matches; otherwise Stable. Availability is separate: Stable does not mean safety.

**Hysteresis:** Initial confirmed state is provisional Mixed / Neutral. A new candidate normally needs two consecutive occurrences. Severe stress (`DS<30 and RE<35`, or `SR<30`) can immediately confirm Stressed. Exit requires the same non-Stressed candidate twice and current `DS>45`. Raw candidate and confirmed state are retained separately.

阈值与迟滞在验证前冻结，用于减少跳变，不是调优后的最优预警规则。

## 7. Directional outlook and confidence

Frozen Evolance uses the existing one-year GBM engine: **5,000 paths, seed 20261007, starting value 100**, reading months 6/12. Compatible simulations are reused; state does not change drift or volatility. Research P10/P50/P90 are terminal **returns**, distinct from product wealth values.

| Probability of gain | Initial direction |
| --- | --- |
| `>=0.70` | Strong Bullish |
| `>=0.60, <0.70` | Bullish |
| `>0.40, <0.60` | Neutral / Uncertain |
| `>0.30, <=0.40` | Bearish |
| `<=0.30` | Strong Bearish |

Median sign must agree. Absolute median return below 2% at 6M or 4% at 12M forces Neutral. Relative bias: positive active return with IR at least 0.25 gives Likely Outperform; negative with IR at most -0.25 gives Likely Underperform; otherwise In Line / Uncertain. No relative probability is claimed.

**Confidence is ordinal, not a calibrated probability.** Strong agreeing directions start High, ordinary directions Moderate, Neutral Low. Direction/transition contradiction, `SR<40`, and concentration each lower one level, with Low as a floor. Synthetic evidence caps confidence at Moderate. Relative confidence is separate, applies shared structural deductions and its own transition contradiction; relative Neutral is Low. Missing resilience is disclosed, not turned into a fabricated penalty.

方向是模型下的概率判断；状态改变解读与置信度，不改变参数。High 不是已验证准确率或投资保证。

## 8. Real historical validation

Records: [pre-evaluation method](evolance_v1_1_real_method.md), [historical report](evolance_v1_1_real_validation.md), [derived summary](../research/evolance_v1_1_real_results/summary.json).

- AAPL/MSFT/NVDA/SPY intersection: **2005-02-25 to 2017-11-10**, 3,201 prices.
- Five portfolios: equal 33.33/33.33/33.34; concentrated 70/15/15; each stock at 100%, all with SPY benchmark.
- Completed-month signals use only trailing evidence. Signals are generated before future outcomes are independently attached at 126/252 sessions. Incomplete outcomes remain censored, never zero-filled.
- Per portfolio: 141 signals, 135 complete 6M outcomes, 129 complete 12M outcomes. Pooled portfolio-months are correlated and horizons overlap, not independent market episodes.
- Traditional baseline: trailing return and Sharpe both positive gives Bullish, both negative Bearish, otherwise Neutral. This declared simple rule is not all conventional analysis.
- MC-only and Evolance use identical distributions/directions; equality is expected by construction. Evolance adds interpretation and confidence deductions.
- Hits exclude Neutral/incomplete outcomes; zero return is a miss. Both issued and complete Neutral coverage are reported. Different coverage prevents treating raw hit comparisons as superiority.

**Observed:** Deteriorating had deeper mean subsequent drawdowns than Stable; state groups differed descriptively. Pooled confidence hits ordered High > Moderate > Low, but composition confounds this: concentration deductions exclude every single-asset record from High. Moderate also had higher mean raw returns than High.

**Not established:** Predictive superiority, independently calibrated confidence, profitable timing, risk-adjusted alpha or robust generalization. Recommendation B is interpretation/decision-support productization only.

完成指定协议不等于机构级样本外认证；原报告保留分组、覆盖率、截尾与样本量，本文不挑选命中率作营销结论。

## 9. Failure audit and limitations

[All failure cases](../research/evolance_v1_1_real_results/failure_cases.csv) are retained: bullish losses, bearish gains, High-confidence misses, Recovering losses and deterioration proxies. Categories overlap; counts are not precision/recall for independent events.

Examples include a Strong Bullish/High/Stable equal-weight signal in February 2006 followed by roughly 30% six-month drawdown despite an ending gain, a High-confidence bullish loss in 2007, and Strong Bearish/High in 2008 followed by an ending gain after deep drawdown. Ending return and path risk answer different questions.

The audit retains 386 non-Deteriorating records with future drawdown at or below -20%, and 60 High-confidence failures across portfolio/horizon records. Zero cases under the strict false-alarm proxy (Deteriorating and future drawdown better than -5%) does **not** establish zero false alarms generally. Audit thresholds do not change framework rules.

Limitations: three retrospectively selected surviving technology winners, one benchmark, history ending in 2017, no untouched empirical holdout, overlapping horizons, correlated portfolios, tiny/empty groups, endogenous confidence, no causal isolation or user-comprehension study, and no multiplicity adjustment. Modern adjusted histories may incorporate later corporate actions; calendar-gap explanations were not independently authenticated. GBM, daily rebalancing and cost exclusions also apply. No IID significance or institutional-grade validation is claimed.

失败记录是方法的一部分；Stable、Recovering、High 或看涨都不保证安全、恢复或收益。

## 10. Data provenance and strategy

### Product runtime

**SQLite cache → Yahoo Finance / yfinance → deterministic synthetic Demo Data.** Yahoo uses `auto_adjust=True` and adjusted `Close`; inclusive user end dates become exclusive provider boundaries. Cache coverage/source metadata are checked first, with bounded retries/cooldown for provider failures.

Any synthetic fallback switches all assets and benchmark to Demo Data. The UI labels sources with a non-blocking notice. Fixed seeds/date basis make AAPL/MSFT/NVDA/SPY repeatable without APIs or restricted real-history redistribution. Demo is not historical, live or a current prediction, and is not stored as real prices. Kibot is excluded from public runtime.

Python `sqlite3` stores `historical_prices` (provider cache), `portfolio_configs` (saved configuration) and `analysis_runs` (metadata/provenance). Parameterized SQL and UPSERT serve actual retrieval/persistence. Runtime DB/cache files are ignored. Cloud-local storage can reset and is shared within an instance; this is not an account system or durable private vault.

### Historical research

The existing report identifies **Kaggle Huge Stock Market Dataset by Boris Marjanovic**, manually supplied as local/private files, cutoff around 2017. The manifest declares source-adjusted Close and dividend/split treatment based on user-supplied documentation. Source rights, licensing and adjustment claims are **not independently authenticated**. This records declarations without expanding or reinterpreting redistribution rights.

[Research input requirements](../research/REAL_DATA_INPUT.md) require provenance/opt-in for source-adjusted Close; explicit Adjusted Close takes priority. Raw prices/private manifests are excluded from Git/public exports. Reviewed derived metrics, classifications and audits remain separate from raw histories. Synthetic research simulation artifacts are also distinct from private inputs.

公开产品不调用私有研究入口。来源声明不是许可或复权准确性的独立认证；原始行情不随文档发布。

## 11. Reproducibility and freeze discipline

Frozen Spec SHA-256, over exact JSON bytes:

```text
bea9d81702d4afe70a2d65d3fd1beb33c410eeefa0298cc2e5fe5d06e521e0b7
```

The specification is checked on load and recursively read-only. Rules, weights, anchors, thresholds and direction bands freeze before evaluation; outcomes do not tune them. Only documented corrections to genuine code/formula/data/numerical errors are permissible. Preserve original v1 findings and v1.1 artifacts rather than rewriting history.

Milestone `97bf73022e598d9f297ca8b4084e85e58f11bf88` contains 82 changed files, including research source/results/tests, frozen docs and Git protection files. All 80 research files match its exact bytes. The two Git protection files (`.gitattributes`, `.gitignore`) match its Git-normalized content; their Windows working copies use CRLF instead of the stored LF. This is a checkout line-ending difference, not a research change. This scope differs from narrower frozen-module counts.

Offline tests cover formulas, seeds, provider mocks, SQL, future-perturbation/prefix invariance, windows, censoring, grouping and export schemas. Pre-documentation checkpoint `82dba4966b144392733f3d0c40a0b0bab2944955` had a reported **324 passed / 207 subtests passed** baseline. This records a milestone, not an immutable count or a claim of rerunning the suite for documentation.

Windows, from repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

The [research entry](../research/README.md) documents separate readiness, study and report commands. Reproducing the real study needs authorized private files/manifest; offline tests do not. Do not rerun studies to rewrite preserved artifacts or force counts to agree.

## 12. Guidance and interpretation boundaries

[Portfolio guidance](../src/portfolio_guidance.py) uses disclosed rules on historical/simulated risk and preference, horizon and goal. Missing evidence is disclosed. There is no trading execution, optimization or regulated suitability assessment. Planning remains separate from Evolance. Interpretation supports questions/comparisons without authorizing investment action.

**For educational and research purposes only. Not investment advice. Historical performance and model outputs do not guarantee future results.**

**仅供教育与研究，不构成投资建议。历史表现、结构标签、方向及置信度均不保证未来结果。**
