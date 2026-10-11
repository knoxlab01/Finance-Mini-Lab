# Vexa v0.4.0 — Release Candidate Notes / 候选版本发布说明

状态：本地发布候选版本，待人工批准；尚未合并、推送、打标签、部署或创建 GitHub Release。
Status: local release candidate awaiting human approval; no merge, push, tag, deployment or GitHub Release has been performed for v0.4.0.

## Product Identity / 产品身份

- **Vexa — Portfolio Intelligence, Made Clear.** Finance Mini Lab retains its repository and historical development identity within Program One; Evolance is the signature interpretation framework. / Vexa 是公开产品名，Finance Mini Lab 保留为仓库与历史开发项目名，Evolance 是特色解释框架。

## Evolance / 结构化解读

- Frozen Evolance v1.1 organizes established financial evidence into Growth Strength, Downside Stability, Diversification Quality, Return Efficiency and Structural Resilience. / 冻结 v1.1 从增长、下行稳定、分散化、收益效率与结构韧性五个维度整理既有金融证据。
- Primary State, independent Structural Flags, Transition, Directional Outlook and ordinal Confidence are presented through **Traditional Analytics vs Evolance** and **Evolance Takeaway**. / 并列呈现传统指标与状态、独立压力标签、变化趋势、方向和有序置信度，并提供组合解读总结。
- Structural interpretation affects explanation/confidence, not Monte Carlo drift or volatility. / 结构只影响解读与置信度，不改动模拟参数。

## Research & Validation / 研究与验证

- Frozen specification, deterministic synthetic validation and real historical walk-forward validation using AAPL/MSFT/NVDA/SPY over 2005–2017; retained failure audits and reproducible artifacts. / 冻结规范、确定性合成验证、2005–2017 真实历史逐期验证及保留的失败审计。
- **Predictive superiority was not established.** Descriptive relationships were observed in a limited, overlapping sample; confidence was not independently calibrated. Positioning remains interpretation and educational decision support. / **未确立预测优势。** 样本有限且重叠，观察到的关联是描述性的，置信度未独立校准；定位为解释与教育性决策辅助。
- See [Methodology](METHODOLOGY.md) and the unchanged [historical validation report](evolance_v1_1_real_validation.md) for definitions and limitations.

## Preserved Portfolio Capabilities / 保留的组合能力

- Historical return/risk metrics, benchmark growth comparison, drawdown, correlation and diversification analysis. SQLite provides real price caching, saved portfolios and analysis provenance. / 历史风险收益指标、基准、回撤、相关性与分散化分析；SQLite 支持缓存、保存组合与来源记录。
- Future Outlook retains scenario projections, GBM Monte Carlo, P10/P50/P90 and loss probability; Evolance supports 6M/12M outlooks when evidence permits. / 保留情景投影与概率模拟，证据允许时提供半年和一年方向解读。
- Profile-aware educational Guidance uses preference, horizon and goal. Compound Interest, DCA and Goal Planner remain available. / 保留偏好、期限、目标引导，以及复利、定投与目标规划。

## UX / 产品体验

- Global English/中文, natural Chinese localization, Vexa branding, restrained visual polish and semantic Evolance presentation. / 全局双语、自然中文、Vexa 品牌、克制视觉打磨及 Evolance 语义呈现。
- Five approved screenshots cover Home → Performance Overview → Future Outlook → Evolance → Guidance. Image bytes remain unchanged. / 五张已批准截图按产品到决策辅助顺序展示，未改动图片内容。

## Reliability / 可靠性

- Dynamic-input end-to-end audit verified input-driven analysis and compatible result reuse. User-defined portfolios depend on available market data; this is not an unconditional all-symbol guarantee. / 输入链审计确认动态分析与兼容结果复用；自定义组合取决于可用行情，不保证所有代码均可获取。
- Product month-end cutoff now distinguishes the selected calendar cutoff from the last trading observation. `2026-05-31` correctly selects `2026-05-29`; mid-month cutoffs do not complete that month. Future observations are excluded, without price filling. Frozen research rules remain unchanged. / 修复非交易日月末截止，排除前视，不填充价格，不改变冻结研究。
- Offline release-candidate suite: **336 passed / 213 subtests passed**. / 候选版本完整离线测试：**336 项及 213 个子测试通过**。

## Architecture & Data / 架构与数据

```text
User Inputs → Market Data / Demo Data → Traditional Portfolio Analytics
            → Future Simulation → Evolance Interpretation → Portfolio Guidance
SQLite: cache / persistence
Separate research: frozen validation / failure audits
```

Runtime priority is **SQLite Cache → Yahoo Finance → deterministic synthetic Demo Data**. If fallback is required, the whole portfolio and benchmark use labeled Demo Data. The Demo universe is AAPL/MSFT/NVDA/SPY; repeatable synthetic prices are not real historical/live prices or predictions. Yahoo availability is not guaranteed; Kibot is excluded from public runtime.

运行时优先缓存和 Yahoo，失败时整组统一使用明确标记的合成演示数据。Demo 范围有限，不能当作真实行情或预测；Yahoo 可用性不作保证，公开路径不调用 Kibot。

Real historical research uses local/private source files. Raw prices and private manifests remain excluded from Git; reviewed derived research artifacts are distinct from raw inputs. / 真实研究使用本地私有源文件，原始行情与私有清单不进入 Git，派生研究结果与原始数据分离。

## Release Boundary / 发布边界

[Live Demo / 在线体验](https://finance-mini-lab-knox.streamlit.app/) points to the existing deployment and does not certify that v0.4.0 is live. Publication requires separate merge/push/tag/release approval. Historical v0.3 records are preserved.

在线链接不代表 v0.4.0 已部署；合并、推送、标签与发布需后续批准，历史 v0.3 记录保持原样。

**For educational and research purposes only. Not investment advice. Historical performance and model outputs do not guarantee future results.** / **仅供教育与研究，不构成投资建议；历史表现与模型输出不保证未来结果。**
