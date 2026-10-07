# Finance Mini Lab v0.3.0 — Release Notes Draft / 发布说明草稿

状态：仅本地发布准备，尚未推送、合并、打标签、部署或创建 GitHub Release。
Status: local release preparation only; no push, merge, tag, deployment or GitHub Release.

Finance Mini Lab v0.3.0 从金融规划工具扩展为投资组合分析与情景模拟应用。
Finance Mini Lab v0.3.0 expands the project from a financial planning toolkit into a broader portfolio analytics and scenario simulation application.

## New in v0.3.0 / 新增内容

- 历史组合分析与真实行情支持 / Historical portfolio analytics with real-market-data support.
- 基准比较、累计收益、CAGR、波动率、Sharpe、最大回撤 / Benchmark comparison and core risk/return metrics.
- 相关性与分散化分析 / Correlation and diversification analysis.
- SQLite/SQL 缓存、组合保存与分析来源记录 / SQL-backed price cache, portfolio persistence and analysis provenance.
- Future Outlook 情景投影与 Monte Carlo / Scenario projections and Monte Carlo simulation.
- P10/P50/P90 与亏损概率 / Outcome percentiles and loss probability.
- 规则 Portfolio Guidance，匹配风险偏好、期限与目标 / Rule-based guidance matching preference, horizon and goal.
- 指标解释层与 English/中文组合分析 / Explainability and English/Chinese portfolio analytics.
- 完整 pytest 套件 189 项通过 / Expanded automated coverage: 189 tests passing.

## Notes / 说明

Yahoo Finance 保持主要实时来源，优先复用 SQLite；失败时整组切换明确标记的确定性合成 Demo Data。Kibot 不在公开运行路径。Monte Carlo 是简化模拟，不是预测或保证；Guidance 仅作教育性决策辅助，不是受监管投资建议。保留已有规划功能。

Yahoo remains the primary live-data source after SQLite cache. If live retrieval fails, the whole analysis uses clearly labeled deterministic synthetic Demo Data. Kibot is excluded from public runtime. Monte Carlo outputs are simplified simulations, not forecasts or guarantees. Guidance is educational decision support, not regulated investment advice. Existing planning tools are preserved.

## Validation / 验证

Phase 1/2/3 及语言、解释层已完成人工验收；发布包装重新运行完整自动化套件。新截图仍待人工补充，正式发布需要后续明确授权。

Phase 1/2/3, language selection and explainability have passed manual acceptance. Packaging reruns the full automated suite. New screenshots remain a manual follow-up; publication requires separate authorization.

[Live Demo / 在线体验](https://finance-mini-lab-knox.streamlit.app/)

此链接为现有部署，本草稿不代表线上已更新。
The link points to the existing deployment; this draft does not imply an online update.
