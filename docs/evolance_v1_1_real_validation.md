# Evolance v1.1 — Real Historical Validation / 真实历史验证

**Recommendation B: Productize as Interpretation / Decision-Support Layer, without predictive-superiority claims. / 建议 B：仅作为解释与决策辅助层产品化，不声称预测优势。**

本轮完成真实数据的冻结规则回溯验证；不是交易策略、市场预测认证或 UI 上线授权。建议限于透明展示风险结构与不确定性，Confidence 不可作为已校准成功概率。实际用户可理解性仍需验证。
This is frozen-rule empirical research, not a trading-strategy approval or deployment. Structural context has descriptive value; user comprehension remains untested. Confidence is an ordinal explanation label, not a calibrated success probability.

## Integrity and provenance / 完整性与来源

Frozen Spec SHA-256: `bea9d81702d4afe70a2d65d3fd1beb33c410eeefa0298cc2e5fe5d06e521e0b7`

Pre-evaluation method SHA-256: `d90bb0bce897cd25aa7a49a361416fa47e5d8d9942293a33ed3ec40e8f2fa5bb`. [Registered method](evolance_v1_1_real_method.md).

Kaggle Huge Stock Market Dataset, Boris Marjanovic; user-declared source-adjusted Close, including dividends/splits per supplied documentation. Local manifest/source rights and adjustment claims are not independently authenticated. No online access, new provider, raw exports, source modification, frozen-parameter changes or empirical tuning.
数据来自本地私有文件，复权语义为来源声明而非独立验证。原始价格不随本报告发布。

Aligned history: **2005-02-25 — 2017-11-10, 3201 prices**. No fill/backfill. SPY's common start truncates earlier asset history. Five portfolios share this exact calendar; 141 completed-month signals each, 135 complete 6M and 129 complete 12M outcomes each. Pooled: 705 signals/horizon; 675/645 complete outcomes; 30/60 censored. Pooled counts are correlated portfolio-month observations, not independent market episodes.

Two five-day gaps: 2006-12-29 → 2007-01-03; 2012-10-26 → 2012-10-31. All four assets agree. They are consistent with New Year/Ford mourning closure and Hurricane Sandy. No authoritative local calendar or internet verification was available; calendar attribution remains explicitly uncertain and non-blocking. No source rows changed. Readiness remains READY_WITH_WARNINGS, not forcibly upgraded.

## Method and baselines / 方法与基线

等权33.33/33.33/33.34；集中70/15/15；AAPL/MSFT/NVDA各100%；基准SPY。固定权重每日再平衡，不计税费/交易成本。252收益/253价格回溯，完成自然月末发布；先生成全部信号，再独立计算126/252交易日真实结果。不完整结果保留缺失，绝不填0。

Traditional exact rule: trailing portfolio cumulative return >0 AND Sharpe >0 ⇒ Bullish; both <0 ⇒ Bearish; otherwise Neutral / Uncertain. This rule was recorded before calculating comparative performance and already existed in frozen research. It represents a simple baseline, not all traditional analysis.

MC-only uses the existing monthly GBM engine, frozen 5000 paths/seed/1-year horizon, probability bands and 6M/12M median guardrails. Evolance uses exactly the same distributions/directions; structural evidence only changes confidence/explanation. Therefore identical MC-only and Evolance directional performance is required, not an empirical improvement.

Hit rate excludes Neutral and incomplete outcomes; zero return is a directional miss. `neutral_coverage` uses all issued signals; `complete_neutral_coverage` uses complete outcomes. Confidence moments below use directional outcomes only. State/transition/flag moments include Neutral. Standard deviation uses ddof=1. Rates/returns/drawdowns in tables are fractions, not percent. Every CSV contains portfolio-specific and pooled groups, censor counts, medians, dispersion and bullish/bearish subgroups.

## Three-way directional results / 三方方向比较

| months | system | signals | complete | directional_n | neutral_n | hit_rate | neutral_coverage | complete_neutral_coverage | bullish_mean_return | bullish_mean_drawdown | bearish_mean_return | bearish_mean_drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | Traditional | 705 | 675 | 663 | 12 | 0.6109 | 0.0170 | 0.0178 | 0.1305 | -0.1801 | 0.2226 | -0.1812 |
| 6 | MC-only | 705 | 675 | 565 | 110 | 0.6283 | 0.1560 | 0.1630 | 0.1357 | -0.1773 | 0.2609 | -0.1950 |
| 6 | Evolance | 705 | 675 | 565 | 110 | 0.6283 | 0.1560 | 0.1630 | 0.1357 | -0.1773 | 0.2609 | -0.1950 |
| 12 | Traditional | 705 | 645 | 633 | 12 | 0.6035 | 0.0170 | 0.0186 | 0.2684 | -0.2506 | 0.4364 | -0.2122 |
| 12 | MC-only | 705 | 645 | 566 | 79 | 0.6219 | 0.1135 | 0.1225 | 0.2859 | -0.2462 | 0.4870 | -0.2170 |
| 12 | Evolance | 705 | 645 | 566 | 79 | 0.6219 | 0.1135 | 0.1225 | 0.2859 | -0.2462 | 0.4870 | -0.2170 |

Evolance/MC 6M 62.83% (565 directional), 12M 62.19% (566), versus Traditional 61.09% (663), 60.35% (633). Different coverage and dependence prevent superiority claims. The overall positive-return frequencies are 73.78%/77.36%; thus >50% hits alone are not impressive in this selected growth-heavy universe. Bearish signals are frequently followed by positive returns (mean +26.09%/+48.70%). No profitable trading strategy, risk-adjusted alpha, or predictive superiority is established.
方向有历史描述信息，但看空信号常错过反弹；未确立预测优势，更不能把略高于传统基线的比例当显著胜出。

| portfolio | months | system | directional_n | hit_rate | neutral_coverage | bullish_n | bearish_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| equal_weight | 6 | Traditional | 133 | 0.6466 | 0.0142 | 113 | 20 |
| equal_weight | 6 | MC-only | 119 | 0.6555 | 0.1135 | 105 | 14 |
| equal_weight | 6 | Evolance | 119 | 0.6555 | 0.1135 | 105 | 14 |
| equal_weight | 12 | Traditional | 127 | 0.7008 | 0.0142 | 107 | 20 |
| equal_weight | 12 | MC-only | 116 | 0.7241 | 0.0922 | 102 | 14 |
| equal_weight | 12 | Evolance | 116 | 0.7241 | 0.0922 | 102 | 14 |
| concentrated | 6 | Traditional | 134 | 0.6343 | 0.0071 | 110 | 24 |
| concentrated | 6 | MC-only | 124 | 0.6532 | 0.0780 | 105 | 19 |
| concentrated | 6 | Evolance | 124 | 0.6532 | 0.0780 | 105 | 19 |
| concentrated | 12 | Traditional | 128 | 0.6328 | 0.0071 | 104 | 24 |
| concentrated | 12 | MC-only | 119 | 0.6387 | 0.0709 | 99 | 20 |
| concentrated | 12 | Evolance | 119 | 0.6387 | 0.0709 | 99 | 20 |
| aapl | 6 | Traditional | 133 | 0.5865 | 0.0142 | 103 | 30 |
| aapl | 6 | MC-only | 120 | 0.6000 | 0.1064 | 96 | 24 |
| aapl | 6 | Evolance | 120 | 0.6000 | 0.1064 | 96 | 24 |
| aapl | 12 | Traditional | 127 | 0.5197 | 0.0142 | 98 | 29 |
| aapl | 12 | MC-only | 120 | 0.5250 | 0.0709 | 94 | 26 |
| aapl | 12 | Evolance | 120 | 0.5250 | 0.0709 | 94 | 26 |
| msft | 6 | Traditional | 131 | 0.5573 | 0.0284 | 93 | 38 |
| msft | 6 | MC-only | 94 | 0.5638 | 0.2908 | 77 | 17 |
| msft | 6 | Evolance | 94 | 0.5638 | 0.2908 | 77 | 17 |
| msft | 12 | Traditional | 125 | 0.5680 | 0.0284 | 87 | 38 |
| msft | 12 | MC-only | 102 | 0.5980 | 0.1915 | 78 | 24 |
| msft | 12 | Evolance | 102 | 0.5980 | 0.1915 | 78 | 24 |
| nvda | 6 | Traditional | 132 | 0.6288 | 0.0213 | 101 | 31 |
| nvda | 6 | MC-only | 108 | 0.6574 | 0.1915 | 81 | 27 |
| nvda | 6 | Evolance | 108 | 0.6574 | 0.1915 | 81 | 27 |
| nvda | 12 | Traditional | 126 | 0.5952 | 0.0213 | 95 | 31 |
| nvda | 12 | MC-only | 109 | 0.6239 | 0.1418 | 80 | 29 |
| nvda | 12 | Evolance | 109 | 0.6239 | 0.1418 | 80 | 29 |

## Confidence discrimination / 置信度分层

| months | confidence | directional_n | hit_rate | mean_return | median_return | mean_drawdown | std_return |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | High | 119 | 0.7479 | 0.1446 | 0.1389 | -0.1468 | 0.1824 |
| 6 | Moderate | 317 | 0.6404 | 0.1707 | 0.1527 | -0.1884 | 0.3055 |
| 6 | Low | 129 | 0.4884 | 0.1393 | 0.1585 | -0.1919 | 0.2705 |
| 12 | High | 127 | 0.7638 | 0.3051 | 0.3025 | -0.2052 | 0.3168 |
| 12 | Moderate | 338 | 0.6065 | 0.3433 | 0.2753 | -0.2501 | 0.5374 |
| 12 | Low | 101 | 0.4950 | 0.2946 | 0.2453 | -0.2520 | 0.4425 |

Pooled High > Moderate > Low hit rates at both horizons. High also has less return dispersion and milder mean drawdown. However, Moderate has higher mean raw returns than High; dispersion is not monotonic across Moderate/Low. **Discrimination is descriptive; empirical probability calibration is not established.** High comes only from multi-asset portfolios: the concentration downgrade prevents all single-asset High signals. Low samples in equal-weight/concentrated portfolios are small. Portfolio composition, bullish/bearish mix, overlap and selection confound pooled ordering.
汇总命中率分层有用，但并非独立校准；High 组完全不含单资产样本，不能把组间差异全归因于结构降级。

| portfolio | months | confidence | directional_n | hit_rate | mean_drawdown | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| equal_weight | 6 | High | 81 | 0.6914 | -0.1530 | descriptive; overlapping observations |
| equal_weight | 6 | Moderate | 33 | 0.6364 | -0.1676 | descriptive; overlapping observations |
| equal_weight | 6 | Low | 5 | 0.2000 | -0.3101 | insufficient evidence |
| equal_weight | 12 | High | 89 | 0.7753 | -0.2118 | descriptive; overlapping observations |
| equal_weight | 12 | Moderate | 23 | 0.5652 | -0.2164 | descriptive; overlapping observations |
| equal_weight | 12 | Low | 4 | 0.5000 | -0.3927 | insufficient evidence |
| concentrated | 6 | High | 38 | 0.8684 | -0.1336 | descriptive; overlapping observations |
| concentrated | 6 | Moderate | 65 | 0.6000 | -0.1775 | descriptive; overlapping observations |
| concentrated | 6 | Low | 21 | 0.4286 | -0.1655 | descriptive; overlapping observations |
| concentrated | 12 | High | 38 | 0.7368 | -0.1898 | descriptive; overlapping observations |
| concentrated | 12 | Moderate | 67 | 0.6269 | -0.2265 | descriptive; overlapping observations |
| concentrated | 12 | Low | 14 | 0.4286 | -0.2654 | insufficient evidence |
| aapl | 6 | High | 0 | N/A | N/A | insufficient evidence |
| aapl | 6 | Moderate | 95 | 0.6737 | -0.1805 | descriptive; overlapping observations |
| aapl | 6 | Low | 25 | 0.3200 | -0.1999 | descriptive; overlapping observations |
| aapl | 12 | High | 0 | N/A | N/A | insufficient evidence |
| aapl | 12 | Moderate | 97 | 0.5773 | -0.2438 | descriptive; overlapping observations |
| aapl | 12 | Low | 23 | 0.3043 | -0.2721 | descriptive; overlapping observations |
| msft | 6 | High | 0 | N/A | N/A | insufficient evidence |
| msft | 6 | Moderate | 48 | 0.5417 | -0.1452 | descriptive; overlapping observations |
| msft | 6 | Low | 46 | 0.5870 | -0.1418 | descriptive; overlapping observations |
| msft | 12 | High | 0 | N/A | N/A | insufficient evidence |
| msft | 12 | Moderate | 64 | 0.6094 | -0.1846 | descriptive; overlapping observations |
| msft | 12 | Low | 38 | 0.5789 | -0.1918 | descriptive; overlapping observations |
| nvda | 6 | High | 0 | N/A | N/A | insufficient evidence |
| nvda | 6 | Moderate | 76 | 0.6974 | -0.2438 | descriptive; overlapping observations |
| nvda | 6 | Low | 32 | 0.5625 | -0.2566 | descriptive; overlapping observations |
| nvda | 12 | High | 0 | N/A | N/A | insufficient evidence |
| nvda | 12 | Moderate | 87 | 0.6322 | -0.3323 | descriptive; overlapping observations |
| nvda | 12 | Low | 22 | 0.5909 | -0.3007 | descriptive; overlapping observations |

Pure MC-only confidence segmentation (no structural deductions), for context; no matched causal improvement claim:

| months | confidence | directional_n | hit_rate | mean_drawdown | std_return |
| --- | --- | --- | --- | --- | --- |
| 6 | High | 422 | 0.6588 | -0.1803 | 0.2780 |
| 6 | Moderate | 143 | 0.5385 | -0.1808 | 0.2684 |
| 6 | Low | 0 | N/A | N/A | N/A |
| 12 | High | 476 | 0.6261 | -0.2424 | 0.4949 |
| 12 | Moderate | 90 | 0.6000 | -0.2295 | 0.3755 |
| 12 | Low | 0 | N/A | N/A | N/A |

## Primary States / 主状态

| months | group | signals | complete | mean_return | median_return | mean_drawdown | positive_frequency | std_return |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | Balanced Growth | 28 | 28 | 0.1682 | 0.1666 | -0.1081 | 0.8929 | 0.1247 |
| 6 | Growth-Led | 391 | 365 | 0.1490 | 0.1492 | -0.1860 | 0.7151 | 0.2860 |
| 6 | Defensive | 0 | 0 | N/A | N/A | N/A | N/A | N/A |
| 6 | Stressed | 129 | 129 | 0.1868 | 0.2022 | -0.2387 | 0.6977 | 0.3649 |
| 6 | Mixed / Neutral | 157 | 153 | 0.1114 | 0.1370 | -0.1368 | 0.7974 | 0.1608 |
| 12 | Balanced Growth | 28 | 28 | 0.4162 | 0.3332 | -0.1324 | 0.9643 | 0.2666 |
| 12 | Growth-Led | 391 | 341 | 0.3001 | 0.2269 | -0.2640 | 0.7419 | 0.5420 |
| 12 | Defensive | 0 | 0 | N/A | N/A | N/A | N/A | N/A |
| 12 | Stressed | 129 | 129 | 0.3572 | 0.3447 | -0.2894 | 0.7674 | 0.4564 |
| 12 | Mixed / Neutral | 157 | 147 | 0.2373 | 0.2711 | -0.1770 | 0.8163 | 0.2592 |

12M Balanced Growth has 28 observations, mean return 41.62% and mean drawdown -13.24%; Growth-Led has 341, 30.01%, -26.40%; Stressed has 129, 35.72%, -28.94%; Mixed has 147, 23.73%, -17.70%. Defensive has no observations: no conclusion. Stressed can precede large rebounds AND deep drawdowns; it is a risk-context label, not a sell instruction. These conditional associations are not causal.
Stressed 并不等于未来负收益；高收益与深回撤可以并存。Defensive 无样本，不做外推。

## Transitions / 转化

| months | group | signals | complete | mean_return | median_return | mean_drawdown | positive_frequency | std_return |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | Deteriorating | 64 | 64 | 0.1302 | 0.1158 | -0.2392 | 0.6875 | 0.3572 |
| 6 | Stable | 560 | 530 | 0.1417 | 0.1481 | -0.1753 | 0.7358 | 0.2615 |
| 6 | Recovering | 81 | 81 | 0.2077 | 0.2161 | -0.1779 | 0.7901 | 0.2964 |
| 12 | Deteriorating | 64 | 63 | 0.2147 | 0.2487 | -0.3391 | 0.6984 | 0.4667 |
| 12 | Stable | 560 | 501 | 0.3131 | 0.2711 | -0.2320 | 0.7824 | 0.4719 |
| 12 | Recovering | 81 | 81 | 0.3029 | 0.2313 | -0.2406 | 0.7778 | 0.4223 |

Deteriorating has worse mean future drawdowns than Stable: 6M -23.92% (64) vs -17.53% (530); 12M -33.91% (63) vs -23.20% (501). This supports risk differentiation in this sample, not reliable advance-warning accuracy.
Recovering has higher 6M mean return (20.77%,81) than Deteriorating (13.02%,64), with milder drawdown. At 12M its return (30.29%) is below Stable (31.31%); compared with Stressed it also does not consistently improve returns. Recovery evidence is partial, with 35 negative-return records across horizons.
Deteriorating 与较深回撤相关；Recovering 只有部分改善证据，不能承诺恢复。

## Structural flags / 结构标签

| months | flag | signals | complete | mean_return | median_return | mean_drawdown | directional_n | hit_rate | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | Diversification Erosion | 4 | 4 | 0.3150 | 0.3111 | -0.0772 | 4 | 1.0000 | insufficient evidence |
| 6 | High Risk Concentration | 502 | 484 | 0.1394 | 0.1457 | -0.1940 | 397 | 0.6045 | descriptive; overlapping observations |
| 6 | Low Return Efficiency | 172 | 172 | 0.1823 | 0.1704 | -0.1706 | 103 | 0.3301 | descriptive; overlapping observations |
| 6 | Rapid Structural Deterioration | 12 | 12 | 0.1032 | 0.1200 | -0.2590 | 7 | 0.0000 | insufficient evidence |
| 6 | Unsupported Growth | 353 | 335 | 0.1250 | 0.1370 | -0.1982 | 323 | 0.6997 | descriptive; overlapping observations |
| 6 | Weak Downside Stability | 180 | 180 | 0.1292 | 0.1701 | -0.2711 | 137 | 0.3504 | descriptive; overlapping observations |
| 6 | Unsupported Growth + Deteriorating | 20 | 20 | 0.0374 | 0.0105 | -0.2707 | 19 | 0.5789 | descriptive; overlapping observations |
| 6 | High Risk Concentration + Growth-Led | 275 | 261 | 0.1553 | 0.1510 | -0.1937 | 247 | 0.7085 | descriptive; overlapping observations |
| 12 | Diversification Erosion | 4 | 0 | N/A | N/A | N/A | 0 | N/A | insufficient evidence |
| 12 | High Risk Concentration | 502 | 466 | 0.2936 | 0.2363 | -0.2585 | 406 | 0.5911 | descriptive; overlapping observations |
| 12 | Low Return Efficiency | 172 | 171 | 0.3571 | 0.3657 | -0.2045 | 121 | 0.2645 | descriptive; overlapping observations |
| 12 | Rapid Structural Deterioration | 12 | 12 | 0.3163 | 0.2660 | -0.2930 | 8 | 0.0000 | insufficient evidence |
| 12 | Unsupported Growth | 353 | 318 | 0.2752 | 0.2038 | -0.2763 | 311 | 0.6977 | descriptive; overlapping observations |
| 12 | Weak Downside Stability | 180 | 180 | 0.2790 | 0.2269 | -0.3495 | 148 | 0.2973 | descriptive; overlapping observations |
| 12 | Unsupported Growth + Deteriorating | 20 | 20 | 0.0246 | -0.1559 | -0.4192 | 20 | 0.4000 | descriptive; overlapping observations |
| 12 | High Risk Concentration + Growth-Led | 275 | 249 | 0.3284 | 0.2134 | -0.2712 | 240 | 0.7333 | descriptive; overlapping observations |

Weak Downside Stability: 12M mean drawdown -34.95% (180). Unsupported Growth + Deteriorating: -41.92% (20), an exploratory small joint sample, not a validated trading rule. Rapid Structural Deterioration has only 12 complete 12M observations. Diversification Erosion has no complete 12M outcomes, so no forward claim; terminal signals are not zero-valued outcomes. Inactive flag comparators are in flag_outcomes.csv. Flags overlap and are not independent factors.

## Portfolio structure / 组合结构

Per 141 signal dates: concentrated has 79 High Risk Concentration flags vs equal-weight 0, and 90 Unsupported Growth vs 8. Diversification Erosion is 0 vs 4, so the concentrated portfolio does NOT have more of every weakness. Capital weights and risk-contribution breadth are distinct; equal weights do not guarantee independent exposures.
Single assets have concentration flags at all 141 dates and no High confidence; this is sensible as asset-level concentration but limits differentiation and is not ETF look-through. 12M hit rates: AAPL 52.50% (120), MSFT 59.80% (102), NVDA 62.39% (109); equal-weight 72.41% (116), concentrated 63.87% (119). Do not infer equal weighting is universally superior from these selected assets.

## Interpretation advantage, redundancy and failures / 解释优势、重复与失败

Predeclared matching: same date/horizon, same MC direction, P(up) difference <=5 percentage points, differing structure. All 476 pairs retained: **226 useful drawdown associations, 168 redundant, 82 misleading** by the predeclared audit convention. These categories measure a simple flag-count/state severity association, not user benefit or framework accuracy. They are highly dependent. No selective success-only export.
Earliest example in each category (not chosen for attractive returns):

| date | months | category | direction | higher_severity_portfolio | higher_severity_state | higher_severity_flags | higher_severity_forward_return | higher_severity_forward_drawdown | other_portfolio | other_forward_return | other_forward_drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2006-02-28T00:00:00 | 6 | redundant | Strong Bullish | concentrated | Mixed / Neutral | ["High Risk Concentration", "Unsupported Growth"] | 0.0174 | -0.2929 | equal_weight | 0.0556 | -0.3008 |
| 2006-02-28T00:00:00 | 6 | useful | Strong Bullish | nvda | Mixed / Neutral | ["High Risk Concentration", "Unsupported Growth"] | 0.1625 | -0.4351 | equal_weight | 0.0556 | -0.3008 |
| 2006-04-28T00:00:00 | 12 | misleading | Strong Bullish | aapl | Growth-Led | ["High Risk Concentration", "Unsupported Growth", "Weak Downside Stability"] | 0.4133 | -0.2952 | nvda | 0.1375 | -0.4351 |

2006-02-28: similar Strong Bullish MC signals, NVDA's concentration/unsupported-growth flags accompany a -43.51% subsequent 6M drawdown versus equal-weight -30.08%; both earn positive terminal returns. Structure clarifies path risk, not the sign prediction. The same date concentrated/equal-weight has near-identical drawdowns despite different flags (redundant). 2006-04-28 12M: more-flagged AAPL has milder drawdown than NVDA (misleading).
方向层完全重复 MC；新增解释来自风险集中、下行脆弱性和状态转化的可追溯组合。没有新增独立信息源，未做用户理解实验。

## Failure Cases / 失败案例

Counts across portfolio/horizon records (categories overlap): {"missed_deterioration_proxy": 386, "bullish_loss": 240, "bearish_gain": 184, "high_confidence_failure": 60, "recovering_loss": 35}. False-alarm proxy (Deteriorating and future drawdown >-5%) has **0** cases under this strict definition; this does not establish zero false alarms generally. An ending gain is not itself a false risk warning if the path draws down substantially.
All 386 missed-deterioration proxy records (non-Deteriorating with <=-20% future drawdown) and all 60 High-confidence misses are retained. A Stable label is not a guarantee of safety. These are operational audits, not precision/recall for uniquely defined market events.

| kind | date | months | portfolio | direction | confidence | state | transition | forward_return | forward_drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| missed_deterioration_proxy | 2006-02-28T00:00:00 | 6 | equal_weight | Strong Bullish | High | Mixed / Neutral | Stable | 0.0556 | -0.3008 |
| bullish_loss | 2007-06-29T00:00:00 | 12 | equal_weight | Strong Bullish | High | Growth-Led | Stable | -0.0042 | -0.3739 |
| high_confidence_failure | 2007-06-29T00:00:00 | 12 | equal_weight | Strong Bullish | High | Growth-Led | Stable | -0.0042 | -0.3739 |
| bearish_gain | 2008-07-31T00:00:00 | 12 | equal_weight | Strong Bearish | High | Stressed | Stable | 0.0841 | -0.4915 |
| recovering_loss | 2009-08-31T00:00:00 | 12 | equal_weight | Neutral / Uncertain | Low | Stressed | Recovering | -0.0170 | -0.2674 |

Notable failures: equal-weight 2006-02-28 Strong Bullish/High/Stable precedes -30.08% 6M drawdown despite a positive terminal return; 2007-06-29 Strong Bullish/High loses over the following year; 2008-07-31 Strong Bearish/High ends positive after a deep drawdown. Recovering 2009-08-31 ends slightly negative at 12M. All such observations remain in failure_cases.csv.

## Timeline-selected episodes / 时间线自然识别片段

No famous-event labels were hard-coded into signals. The following selects highest contemporaneous Growth Strength, lowest Downside Stability, and earliest Recovering observations; ties use existing deterministic row order. This is descriptive context, not independent validation.

| selection | date | portfolio | Growth Strength | Downside Stability | state | transition | direction | forward_return | forward_drawdown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| highest contemporaneous Growth Strength | 2006-02-28T00:00:00 | equal_weight | 100.0000 | 65.3057 | Mixed / Neutral | Stable | Strong Bullish | 0.0556 | -0.3008 |
| highest contemporaneous Growth Strength | 2006-03-31T00:00:00 | equal_weight | 100.0000 | 73.2813 | Growth-Led | Stable | Strong Bullish | 0.1092 | -0.3008 |
| highest contemporaneous Growth Strength | 2006-04-28T00:00:00 | equal_weight | 100.0000 | 77.3890 | Growth-Led | Stable | Strong Bullish | 0.1905 | -0.2761 |
| lowest contemporaneous Downside Stability | 2008-07-31T00:00:00 | nvda | 0.0000 | 0.0000 | Stressed | Stable | Strong Bearish | -0.3051 | -0.5809 |
| lowest contemporaneous Downside Stability | 2008-08-29T00:00:00 | nvda | 0.0000 | 0.0000 | Stressed | Stable | Strong Bearish | -0.3766 | -0.5332 |
| lowest contemporaneous Downside Stability | 2008-09-30T00:00:00 | nvda | 0.0000 | 0.0000 | Stressed | Stable | Strong Bearish | -0.0561 | -0.4491 |
| earliest Recovering | 2006-07-31T00:00:00 | msft | 23.8368 | 57.2617 | Mixed / Neutral | Recovering | Neutral / Uncertain | 0.2825 | -0.0357 |
| earliest Recovering | 2006-09-29T00:00:00 | msft | 45.2395 | 57.6858 | Mixed / Neutral | Recovering | Neutral / Uncertain | 0.0190 | -0.1438 |
| earliest Recovering | 2006-10-31T00:00:00 | msft | 56.3350 | 58.1419 | Mixed / Neutral | Recovering | Bullish | 0.0644 | -0.1438 |

## Limits and product decision / 局限与产品建议

**B — Productize as Interpretation / Decision-Support Layer; do not claim predictive superiority.** Distinct structural summaries and descriptive downside differentiation justify an educational interpretation layer. Display its limitations and retain the research identity; this recommendation is not an instruction to change UI or deploy. Claims of calibrated confidence or investment timing remain unsupported.

Limitations: three retrospectively chosen surviving US technology winners; SPY benchmark; sample ends in 2017 and excludes later regimes; no untouched empirical holdout; overlapping horizons and correlated portfolios; modern adjusted-data revisions may use later corporate actions; user-declared license/adjustment; unverified holiday attribution; constant 4% risk-free convention; daily rebalancing without costs; frozen GBM limitations; tiny/empty states and flags; endogenous confidence groups; no causal isolation, human usability study or multiplicity adjustment. No IID bootstrap CIs are presented because they would overstate precision; robust time-block and cross-asset evaluation remains future work, not a reason to tune current rules.

Portfolio/resume assessment: **yes, a reasonable finance/data research-engineering portfolio standard is met**, separately from predictive skill. Financial grounding, independent state/flag/transition architecture, frozen-spec discipline, reproducible real walk-forward evaluation, ordinal confidence, explicit censoring, failure audit and private-data boundaries are concrete contributions. Present as an explainable portfolio research framework evaluated on historical data, not a market-beating prediction engine.
简历创新标准基本满足；贡献在工程与解释框架、研究纪律和失败分析，而非新金融因子或预测优势。

## Reproduction and validation / 复现与检查

```powershell
.\.venv\Scripts\python.exe -m research.evolance_v1_1_real_validation
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m research.evolance_v1_1_real_report
```

Requires authorized local private files/manifest. New datasets/calendar gaps need review; no network fallback. The study writes only its separate real-results directory. Report generation reads derived outputs only. Timeline CSVs have two rows/date (6M/12M), traditional metrics, all five dimensions, candidate/confirmed state, flags, transition, absolute/relative confidence, distribution summaries and censored outcomes. No raw price rows or manifest free text are exported.

Tests: **300 passed, 207 subtests passed in 22.53s**. Offline tests cover future-perturbation/prefix invariance, 126/252 windows, drawdown, censoring, hits/Neutral, grouping, pair audits and explicit export schema. Frozen source/previous research/raw-input SHA checks are performed separately before/after this run. No commit/push/merge/tag/release, UI change or frozen-rule changes.
