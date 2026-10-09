# Evolance v1.1 Frozen Specification

版本 / Version: `1.1-frozen`

SHA-256 (exact UTF-8 JSON file bytes): `bea9d81702d4afe70a2d65d3fd1beb33c410eeefa0298cc2e5fe5d06e521e0b7`

规范在验证前冻结，运行校验 SHA-256；配置递归只读。不得按历史结果调参。 / Frozen before validation; checked on load and each study. Configuration is recursively read-only. No outcome-driven tuning.

[Machine-readable specification / 机器规范](evolance_v1_1_frozen_spec.json)

## Architecture / 架构

Established Evidence → Five Dimensions → Primary State + Independent Flags → Transition → Forward Distribution → Direction → Confidence + Explanation.

研究目标是 Interpretation Advantage + Decision-Support Advantage，不声称独创金融因子。 / Research targets interpretation and decision support, not new financial factors.

## Dimensions and Anchors / 维度与锚点

固定分段线性插值，区间外端点截断。 / Fixed linear interpolation and endpoint saturation.

| Dimension | Component | Weight | Anchors |
| --- | --- | --- | --- |
| Diversification Quality | diversification_ratio | 0.4000 | ((1, 0), (1.1, 30), (1.25, 55), (1.5, 80), (2, 100)) |
| Diversification Quality | risk_breadth_score | 0.6000 | 100 * normalized ERC breadth |
| Downside Stability | downside_deviation | 0.5000 | ((0, 100), (0.05, 90), (0.1, 75), (0.15, 55), (0.25, 25), (0.4, 0)) |
| Downside Stability | drawdown | 0.5000 | ((0, 100), (0.1, 90), (0.2, 70), (0.3, 50), (0.4, 30), (0.6, 0)) |
| Growth Strength | absolute_return | 0.6000 | ((-0.3, 0), (-0.1, 20), (0, 40), (0.08, 60), (0.15, 80), (0.3, 100)) |
| Growth Strength | active_return | 0.4000 | ((-0.2, 0), (-0.05, 25), (0, 50), (0.05, 70), (0.1, 85), (0.2, 100)) |
| Return Efficiency | information_ratio | 0.6000 | ((-1, 0), (-0.5, 15), (0, 40), (0.25, 55), (0.5, 70), (0.75, 85), (1, 100)) |
| Return Efficiency | sortino | 0.4000 | ((-1, 0), (0, 25), (0.5, 50), (1, 70), (1.5, 85), (2, 100)) |
| Structural Resilience | Diversification Quality | 0.3000 | ((0, 100), (5, 85), (10, 65), (20, 30), (30, 0)) |
| Structural Resilience | Downside Stability | 0.3500 | ((0, 100), (5, 85), (10, 65), (20, 30), (30, 0)) |
| Structural Resilience | Growth Strength | 0.1500 | ((0, 100), (5, 85), (10, 65), (20, 30), (30, 0)) |
| Structural Resilience | Return Efficiency | 0.2000 | ((0, 100), (5, 85), (10, 65), (20, 30), (30, 0)) |

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
