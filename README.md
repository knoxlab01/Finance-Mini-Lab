# Finance Mini Lab v0.3.0

一个基于 Python 与 Streamlit 构建的轻量级金融规划、投资组合分析与情景模拟工具。

A lightweight financial planning, portfolio analytics, and scenario simulation toolkit built with Python and Streamlit.

## Live Demo / 在线体验

[Finance Mini Lab](https://finance-mini-lab-knox.streamlit.app/)

此链接指向现有公开部署；本次仅完成本地发布准备，尚未更新线上版本。
This link points to the existing deployment; this release preparation has not been deployed.

## Overview / 项目概览

从长期投入规划，到历史风险收益分析、未来情景模拟和可解释的组合建议，帮助理解假设与结果的关系。用于教育、研究与作品集展示，不是交易平台或受监管投资顾问。

Explore how contributions, historical returns, risk and simulation assumptions shape portfolio outcomes. Built for education, research and portfolio demonstration, with transparent calculations and automated tests.

## Core Modules / 核心模块

| Module / 模块 | Capabilities / 功能 |
|---|---|
| Compound Interest / 复利计算 | 一次性本金增长、情景分析、通胀调整 / Lump-sum growth, scenarios and inflation adjustment |
| DCA Simulator / 定投模拟 | 月度定投、累计投入与资产对比、实际购买力 / Monthly contributions, growth versus contributions and purchasing power |
| Goal Planner / 目标规划 | 所需月投入、目标进度、时间与收益率敏感性 / Required contributions, progress and sensitivity |
| Portfolio Analytics / 组合分析 | 历史表现、基准、风险分散化、未来模拟、组合建议 / Historical performance, benchmarks, diversification, simulation and guidance |

Portfolio Analytics 包含 / includes:

- Total Return, CAGR, Annualized Volatility, Sharpe Ratio and Maximum Drawdown；标准化组合/基准曲线、回撤与相关性矩阵 / normalized portfolio/benchmark growth, drawdowns and correlation.
- SQLite 行情缓存、组合保存/加载与分析元数据 / price caching, portfolio save/load and analysis metadata.
- Future Outlook：情景投影、GBM Monte Carlo、P10/P50/P90、亏损概率 / scenario projections, outcome percentiles and loss probability.
- Portfolio Guidance：规则风险分类、偏好/期限/目标匹配、指标理由 / rule-based risk classification, profile fit and metric-based reasons.
- 指标说明与假设；默认 English，可切换中文，保留计算结果 / explainability and assumptions, with English/Chinese selection preserving results.

## v0.3.0 Highlights / 版本亮点

- 从规划计算器扩展为历史组合分析与情景模拟应用 / Extends planning tools with historical portfolio analytics and scenario simulation.
- 真实行情与确定性演示兜底；透明标记数据来源 / Live-data support with clearly labeled deterministic demo fallback.
- SQLite/SQL 实际参与缓存、配置保存及运行记录 / SQL-backed caching, configuration persistence and run records.
- 可解释组合建议与双语组合分析 / Explainable guidance and bilingual portfolio analytics.
- 保留原有规划功能，完整自动化回归验证 / Preserves planning tools with full automated regression coverage.

## Technical Architecture / 技术架构

Python + Streamlit；pandas/NumPy 数据计算；内置 sqlite3；yfinance 实时来源；pytest 收集并运行 unittest 与 Streamlit AppTest 测试；Git/GitHub 版本管理；Streamlit Community Cloud 部署。

Python and Streamlit, pandas/NumPy, built-in SQLite, yfinance, pytest running unittest and Streamlit AppTest, Git/GitHub, and Streamlit Community Cloud.

| Layer / 层 | Files / 文件 |
|---|---|
| Entry points / 入口 | `streamlit_app.py`, `app.py` (CLI compound calculator) |
| Planning / 规划 | `src/compound_interest.py`, `dca.py`, `goal_planner.py`, `scenario.py`, `inflation.py`, `sensitivity.py` |
| Data / 数据 | `src/market_data.py`, `src/database.py` |
| Analytics / 分析 | `src/portfolio_analysis.py`, `src/portfolio_metrics.py`, `src/benchmark.py` |
| Simulation & guidance / 模拟与建议 | `src/future_simulation.py`, `src/portfolio_guidance.py` |
| Presentation / 展示 | `src/portfolio_ui.py`, `src/future_ui.py`, `src/guidance_ui.py`, `src/i18n.py`, translation catalogs |
| Verification / 验证 | `tests/`, `requirements-dev.txt` |

SQLite tables: `historical_prices` stores downloaded prices; `portfolio_configs` stores named configurations; `analysis_runs` stores analysis metadata and provenance. Parameterized SELECT/INSERT and UPSERT operations provide actual persistence. Runtime databases under `data/` are ignored by Git; cloud local storage is not durable or private account storage.

SQLite 三类表分别保存行情、组合配置和运行来源记录；使用参数化查询和 UPSERT。`data/` 不进入 Git；云端本地文件不保证持久保存，也不是用户账号隔离存储。

## Data Strategy / 数据策略

**SQLite Cache → Yahoo Finance → Demo Data**

缓存有效时复用 Yahoo 行情；否则尝试 yfinance 日线 `auto_adjust=True` Close。结束日期按包含处理，转换为 Yahoo 的不包含结束日期接口。存在重试与短暂冷却，失败则整组资产及基准统一使用演示数据，避免混合真实与合成数据。

Valid cached Yahoo prices are reused first. Otherwise yfinance retrieves adjusted daily Close prices, with inclusive user end dates converted to the provider's exclusive boundary. Retries and a short cooldown reduce repeated failures. If retrieval fails, the whole analysis uses synthetic assets and benchmark consistently.

**Demo Data / 演示数据** 是固定种子生成的 deterministic synthetic time series，支持 AAPL/MSFT/NVDA/SPY 标签、2000–2100 年工作日，不是真实历史行情，不代表这些证券实际表现，不依赖 API，也不再分发第三方行情。相同输入产生相同结果。合成行情不写入真实行情缓存；运行记录保留来源。UI 显示实际来源与非阻断提示。

Demo Data is deterministic synthetic data using fixed seeds, covering weekday dates in 2000–2100 for AAPL/MSFT/NVDA/SPY labels. It is not actual market history, does not represent those securities' performance, and uses no external API. Identical inputs reproduce results; synthetic prices are kept out of the real-price cache. Provenance is retained in run metadata and displayed in the UI.

Kibot 不在公开运行路径；未接入 Alpha Vantage 或其他授权备用源。
Kibot is excluded from public runtime; no Alpha Vantage or other licensed fallback is integrated.

## Methodology / 计算方法

- **Historical analytics / 历史分析**：共同观测交易日对齐，不前向填充；简单日收益按目标权重每日再平衡汇总，非买入持有模型。组合与基准从同一基值开始。
  Align observed dates without forward filling; aggregate simple daily returns with daily target-weight rebalancing. Both growth curves share a starting base.
- **Metrics / 指标**：累计收益为复合增长减一；CAGR 使用共同价格首末日期的实际天数（365.25 天/年）；波动率为样本标准差 × √252；Sharpe 将年有效无风险利率转换为日利率，日超额收益均值/收益标准差 × √252。最大回撤包含初始基值；相关性为共同日收益的 Pearson correlation。未定义指标明确显示不可用。
  Cumulative return compounds daily returns. CAGR uses elapsed calendar days; volatility and Sharpe annualize over 252 trading days. Sharpe converts the effective annual risk-free rate to daily. Drawdown includes the initial baseline; correlation uses aligned daily returns. Undefined metrics are marked unavailable.
- **GBM Monte Carlo / 蒙特卡洛**：至少 60 个历史日收益估计对数收益参数；`g = mean(log1p(r)) × 252`, `sigma = std(log1p(r), ddof=1) × sqrt(252)`, `mu = g + sigma²/2`。月度精确转移 `V_next = V × exp(g/12 + sigma/sqrt(12) × Z)`。固定种子、1/3/5 年、1,000–10,000 路径；最多展示 50 条路径。
  At least 60 daily observations calibrate log-return drift and volatility. Exact monthly GBM transitions use independent normal shocks and a fixed seed, with 1/3/5-year horizons and 1,000–10,000 paths; charts show up to 50 paths.
- **Outcomes / 结果**：P10/P50/P90 是模拟分位数，不是保证或置信承诺；亏损概率指期末低于初始本金的路径比例。Base 情景使用模型期望值，不等于中位数；保守/乐观漂移调整是说明性假设。
  Percentiles describe simulated outcomes. Loss probability counts endings below initial capital. Base projections use model expectation rather than the median; scenario drift adjustments are illustrative.
- **Guidance / 建议**：规则评分而非 AI、优化或下单。波动率 <12% / 12–25% / ≥25%、回撤幅度 <15% / 15–30% / ≥30%、可用亏损概率 <15% / 15–35% / ≥35%，分别计 0/1/2；平均相关性 ≥0.75、最大单项权重 ≥50%、组合波动率 ≥基准的 1.25 倍，各加 1。总分 0–1/2–3/≥4 为 Lower/Moderate/Higher。缺失核心证据不作确定评级；可选证据缺失会披露。
  Transparent rules score volatility, drawdown, available loss probability, correlation, concentration and benchmark-relative volatility. Missing core evidence withholds classification; missing optional evidence is disclosed.
- **Profile fit / 偏好匹配**：偏好、期限与目标映射为三档风险容量，取最谨慎档与组合风险比较；只提供定性匹配与抽象资产类别方向，不评估实际财务适当性，不推荐个股交易。
  Preference, horizon and goal map to three risk levels; the most cautious level determines the comparison. Qualitative fit and broad asset-class directions do not assess personal suitability or recommend trades.

[GBM methodology reference / 方法参考](https://www.columbia.edu/~ks20/FE-Notes/4700-07-Notes-GBM.pdf)

## Run Locally / 本地运行

```powershell
git clone https://github.com/knoxlab01/Finance-Mini-Lab.git
cd Finance-Mini-Lab
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

开发验证 / Development checks:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe app.py
```

macOS/Linux 使用 `.venv/bin/python` 替换 Windows 路径。数据库自动创建；不需要 API key。
On macOS/Linux use `.venv/bin/python`. SQLite initializes automatically; no API key is required.

## Testing / 自动化测试

**189 tests passing** in the complete pytest suite (2026-10-08). Existing unittest cases and Streamlit AppTest are collected by pytest. Coverage includes planning regression, analytics and edge cases, SQLite CRUD/cache, mocked retrieval/fallback/provenance, simulation, guidance, localization and explainability. Tests require no live market API and use isolated databases.

**完整 pytest 套件 189 项通过**（2026-10-08）；涵盖原规划回归、历史指标与边界、SQLite 读写及缓存、mock 行情与来源、模拟、建议、语言与解释层。测试不依赖实时行情，数据库隔离。

## Limitations / 已知限制

- 历史表现不保证未来收益；Yahoo 可能限流或暂时不可用，其数据准确性、调整及使用条款由提供方决定。公开部署者应遵守提供方条款；本项目不授予行情再分发权。
  Historical performance does not guarantee future results. Yahoo availability, accuracy, adjustments and terms remain provider-dependent; this project grants no market-data redistribution rights.
- Demo Data 是合成演示；只支持列出的标签和日期范围，不能用于真实投资判断。
  Synthetic Demo Data supports only the documented labels/date range and cannot support actual investment decisions.
- GBM 假设固定参数、正态独立冲击，不包含尾部风险、制度变化或参数不确定性；月度路径不是日内风险模型。
  Simplified GBM excludes regime shifts, fat tails and parameter uncertainty; monthly paths are not an intraday risk model.
- 除规划模块单列通胀调整外，不计税费、交易成本或通胀；历史组合假设每日再平衡，无现金流，要求同币种且无外汇转换。
  Taxes, fees and transaction costs are omitted. Inflation adjustments apply only where explicitly shown. Historical portfolios assume daily rebalancing, no cash flows and a common currency.
- Guidance 是教育性决策辅助，不是受监管、受托或个性化投资建议；不评估收入、负债、流动性、真实承受能力，也不穿透 ETF 持仓。
  Guidance is educational support, not regulated or personalized advice; it omits finances, liquidity, actual loss capacity and ETF look-through.
- Portfolio Analytics 可选 English/中文；其他规划页面保留原双语风格。云端 SQLite 可能随重部署重置，保存配置对同一应用实例访客共享，避免输入个人信息。
  Language selection covers Portfolio Analytics; planning pages retain bilingual copy. Cloud SQLite can reset on redeploy and saved configurations are shared within the app instance; avoid personal information.

## Screenshots / 截图

### v0.3.0 capture plan / 待人工截图

尚未生成新截图；以下为计划位置，不是缺失图片链接。
No new screenshots have been generated; these are planned filenames, not image links.

| Capture / 内容 | Planned file / 计划文件 |
|---|---|
| Portfolio Analytics — Performance Overview + Benchmark | `assets/portfolio_analytics_v0.3.0.png` |
| Future Outlook — Scenario + Monte Carlo | `assets/future_outlook_v0.3.0.png` |
| Portfolio Guidance — Profile Fit + Guidance | `assets/portfolio_guidance_v0.3.0.png` |
| Compound Interest — current hero + planning results | `assets/compound_interest_v0.3.0.png` |

建议正常桌面宽度截图、显示真实数据源或 Demo 标签，避免标题与数值裁切；可补一张中文组合分析。
Capture at desktop width, keeping source/Demo labels and complete values visible; optionally add a Chinese analytics screenshot.

### Historical planning screenshots / 历史规划截图 — v0.2.0

以下文件保留。复利截图图例略截断、目标规划右侧列和下方图表裁切，建议人工重拍；DCA 可保留为补充。这些截图未展示当前 Hero 或新增组合模块。
These files are retained. Compound Interest has a clipped legend and Goal Planner has cropped columns/chart; retake those for the main showcase. DCA remains useful supplementary material. None shows the new hero or portfolio modules.

![Compound Interest — scenario analysis](assets/compound_interest.png)

![DCA Simulator — inflation-adjusted growth](assets/dca_simulator.png)

![Goal Planner — sensitivity analysis](assets/goal_planner.png)

## Roadmap / 后续方向

- 全站语言一致性 / Global language consistency
- 可选合规行情来源 / Optional additional market-data providers
- 组合优化研究 / Portfolio optimization research
- 报告导出 / Report export

无具体发布时间承诺。No release dates are promised.

## Release History / 版本历史

- **v0.3.0** — 本地发布包装准备：历史组合分析、未来模拟、规则建议及语言/解释层；尚未发布。Local release preparation; not yet published.
- **v0.2.0** — 稳定公开规划版本：Scenario Analysis、Inflation-adjusted Value、Goal Sensitivity；本轮 main/origin/main 保持此版本。Stable public planning release; main/origin/main remain unchanged during this preparation.
- **v0.1.0** — 初始复利、定投与目标规划 / Initial planning modules.

[Project log / 项目日志](docs/project_log.md) · [v0.3.0 release notes draft / 发布说明草稿](docs/release_notes_v0.3.0.md)
