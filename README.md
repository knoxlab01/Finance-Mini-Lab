# Finance Mini Lab v0.2.0

A lightweight financial planning and scenario analysis toolkit built with Python and Streamlit.

一个使用 **Python + Streamlit** 构建的轻量级投资规划与情景分析工具，用于理解时间、投入、收益率和通胀如何影响长期财富结果。

包含复利计算、定投模拟和目标规划三个模块，支持交互输入、增长图表、逐年明细、输入校验与自动化测试。采用固定假设，适合教育和规划模拟，不构成投资建议。当前版本：**v0.2.0**。

## Live Demo / 在线体验

**[打开 Finance Mini Lab 在线体验](https://finance-mini-lab-knox.streamlit.app/)**

无需本地安装，即可在浏览器中体验三个模块。

## Core Modules / 核心模块

| 模块 | 用途 |
|---|---|
| **Compound Interest / 复利计算** | 模拟一次性本金按年复利的增长，展示收益、逐年数据、收益构成、Conservative / Base / Optimistic 情景分析及通胀调整后的实际购买力。 |
| **DCA Simulator / 定投模拟** | DCA（Dollar-Cost Averaging）即定期定额投资。本模块模拟初始本金加每月固定投入，对比累计投入与资产价值，并展示最终资产的通胀调整结果。 |
| **Goal Planner / 目标规划** | 根据目标资产、本金、收益率和期限反推每月所需投入，复用 DCA 模拟验证目标，并展示逐年目标差额、时间敏感性和收益率敏感性。 |

三个模块通过独立标签页使用。网页之外，还保留了命令行复利计算器。

## v0.2.0 Highlights / 版本亮点

- **Scenario Analysis**：Conservative / Base / Optimistic 三档收益率比较。
- **Inflation-adjusted Value**：复利与定投的名义金额、实际购买力及购买力损失。
- **Goal Sensitivity**：时间敏感性与收益率敏感性，比较所需月投入及较基准差额。
- Interactive growth charts / 交互增长图表。
- Year-by-year projections / 逐年模拟明细。
- Input validation / 输入校验与数值异常处理。
- **65 automated tests passing** / 核心计算与页面测试。
- Public Streamlit deployment / 公开在线体验。

## Screenshot / Demo

以下为 v0.2.0 三个模块的实际产品截图。

### Compound Interest

![Compound Interest：复利计算结果与资产增长曲线](assets/compound_interest.png)

展示一次性本金的复利增长、收益指标和逐年资产变化。

### DCA Simulator

![DCA Simulator：累计投入与资产价值对比](assets/dca_simulator.png)

展示每月固定投入下的资产积累，以及累计投入与投资增长的差距。

### Goal Planner

![Goal Planner：每月所需投入与目标进度](assets/goal_planner.png)

展示达到目标资产所需的月投入，以及模拟资产与目标线的对比。

可通过 [Live Demo](https://finance-mini-lab-knox.streamlit.app/) 体验交互，或按下方 Run Locally 步骤在本地运行。

## Key Features / 主要功能

- Compound growth simulation：年度复利增长模拟。
- Monthly DCA simulation：月度复利与月末定投模拟。
- Goal-based contribution planning：目标导向的月投入反推。
- Growth charts：资产、累计投入与目标参考线。
- Year-by-year tables：从 Year 0 开始的逐年明细。
- Scenario analysis：保守、基准、乐观情景对比及收益率边界处理。
- Inflation adjustment：默认 2% 固定通胀假设，可调节；复利与定投的终值折现。
- Goal sensitivity：期限与收益率变化下的月投入比较。
- Financial insights：结果摘要与 Rule of 72 近似翻倍估算。
- Input validation：友好处理无效输入、非有限数值及计算溢出。
- Automated tests：核心计算与 Streamlit 页面自动化测试。

## Tech Stack / 技术栈

- **Python 3.12**：已验证的运行环境。
- **Streamlit**：网页界面、交互表单、图表和表格。
- **Python standard library**：金融计算、输入校验及 `unittest` 测试。
- **Streamlit AppTest**：页面交互测试，包含在 Streamlit 中。
- **Git / GitHub**：版本管理与公开代码托管。
- **Streamlit Community Cloud**：公开应用部署。

公开 v0.2.0 原有依赖为 Streamlit。当前 v0.3 Phase 1 开发新增 yfinance，并直接声明用于历史数据计算的 pandas、numpy；SQLite 使用 Python 内置 `sqlite3`。开发验证使用 Python 3.12 / Streamlit 1.64.0。

The public v0.2.0 release used Streamlit. Phase 1 development adds yfinance and declares pandas/numpy directly for analytics; SQLite uses built-in `sqlite3`.

## Project Structure / 项目结构

```text
Finance-Mini-Lab/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ app.py                         # 命令行复利计算器
├─ streamlit_app.py               # 原有三个模块 + 开发中的组合分析
├─ src/                          # 独立金融计算逻辑
│  ├─ compound_interest.py
│  ├─ dca.py
│  ├─ goal_planner.py
│  ├─ scenario.py                 # 三档情景
│  ├─ inflation.py                # 通胀折现
│  ├─ sensitivity.py              # 目标敏感性
│  ├─ database.py                 # SQLite 缓存、配置、分析记录
│  ├─ market_data.py              # Yahoo 历史复权行情
│  ├─ portfolio_analysis.py       # 权重、日期对齐、收益与相关性
│  ├─ portfolio_metrics.py        # 历史风险收益指标
│  ├─ benchmark.py                # 同期基准比较
│  └─ portfolio_ui.py             # 独立组合分析页面
├─ tests/                        # 核心计算与页面测试
│  ├─ test_streamlit_app.py
│  ├─ test_dca.py
│  ├─ test_dca_ui.py
│  ├─ test_goal_planner.py
│  ├─ test_goal_planner_ui.py
│  ├─ test_scenario.py
│  ├─ test_inflation.py
│  ├─ test_inflation_ui.py
│  ├─ test_sensitivity.py
│  ├─ test_sensitivity_ui.py
│  ├─ test_portfolio.py
│  └─ test_portfolio_ui.py
├─ data/                         # 本地 SQLite（自动创建，不提交）
├─ assets/                       # README 截图
└─ docs/
   └─ project_log.md              # 里程碑及验证记录
```

`assets/` 保存 Screenshot / Demo 区域引用的三张正式 PNG 截图。`.venv/`、缓存及 IDE 临时文件由 `.gitignore` 排除。

## Installation / 安装

先安装 Python 3.12 和 Git。以下命令均在终端执行。

### 1. 获取项目

从 GitHub 克隆项目，然后进入项目目录：

```bash
git clone https://github.com/knoxlab01/Finance-Mini-Lab.git
cd Finance-Mini-Lab
```

如果已经持有本地项目目录，直接进入该目录，跳过克隆步骤。

### 2. 创建虚拟环境并安装依赖

**Windows / PowerShell：**不必激活虚拟环境，直接调用其中的 Python，避免执行策略问题。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

如果没有 `py` 启动器，可将第一行改为 `python -m venv .venv`，并确认该 Python 为 3.12；若命令未加入 PATH，可使用解释器的完整路径。

**macOS / Linux：**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

若系统使用 `python3`，请先确认 `python3 --version` 为所需版本。

## Run Locally / 本地运行

在项目根目录、已激活虚拟环境的终端中运行：

```bash
python -m streamlit run streamlit_app.py
```

Windows 无需激活即可运行：

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

打开终端显示的 Local URL，通常是 [http://localhost:8501](http://localhost:8501)。选择模块、填写参数并点击 **Calculate**；终端按 `Ctrl+C` 停止服务。

运行 CLI 复利版本：

```bash
python app.py
```

Windows 未激活环境时可使用 `.\.venv\Scripts\python.exe app.py`。CLI 年化收益率输入 `8` 表示 8%；三个网页模块也采用百分数输入，而核心函数接收小数 `0.08`。

## Testing / 测试

在项目根目录运行完整套件：

```bash
python -m unittest discover -s tests -v
```

Windows 无需激活环境的运行方式：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**136 automated tests passing**（2026-10-07 Phase 1 开发验证）：原有 65 项回归测试与新增 71 项组合计算、数据对齐、基准、相关性、SQLite、缓存、备用源、来源元数据及页面测试。所有测试均不依赖实时互联网，行情通过 mock 隔离，数据库测试使用独立临时文件。AppTest 的 `missing ScriptRunContext` 提示不影响结果。

**136 tests pass**: 65 existing regression tests plus 71 analytics, retrieval/fallback, provenance, SQLite/cache, and UI tests. Tests use mocked downloads and isolated databases; live network access is not required.

### 标准验证案例

| 模块 | 输入 | 预期结果 |
|---|---|---:|
| Compound Interest | 本金 10,000；年化 8%；10 年 | 未来价值 ¥21,589.25 |
| DCA Simulator | 本金 10,000；每月投入 1,000；年化 8%；10 年 | 未来价值 ¥205,142.44 |
| Goal Planner | 目标 1,000,000；本金 100,000；年化 8%；10 年 | 每月所需投入约 ¥4,252.82 |

## Calculation Notes / 计算口径

- **Compound Interest**：`FV = PV × (1 + r)^n`，每年复利，无追加投入。
- **DCA**：月收益率为 `r / 12`，每月先增长、再加入固定投入；累计投入包含初始本金。总收益率为投资增长除以累计投入，不是年化或资金加权收益率。
- **Goal Planner**：复用 DCA 的本金期末价值与单位月投入系数反推金额，再通过 DCA 回算。本金自身增长已达到目标时，月投入为 0。
- **Scenario Analysis**：基准收益率 ±3 个百分点；保守值触及 -100% 时改取基准与 -100% 的中点，极近边界受浮点精度限制。
- **Inflation-adjusted Value**：`Real Value = Nominal Value / (1 + inflation_rate)^years`；购买力损失为名义金额减实际购买力，以投资起点计价。固定通胀率默认 2%，须大于 -100%；负值表示通缩。DCA 月投入保持固定名义金额。
- **Goal Sensitivity**：复用 Goal Planner 比较当前期限 ±5 年（限制为 1–1000 并去重）以及三档收益率；差额为情景月投入减基准月投入。异常情景显示 N/A，不改变基准结果。
- 月度复利与年度复利在同一名义年化收益率下通常产生不同结果。
- Compound Interest 与 DCA 支持 0–1000 整数年；Goal Planner 支持 1–1000 整数年，目标必须大于 0。本金和月投入非负，收益率必须大于 -100%。
- 内部计算保留完整精度，显示时才舍入。目标规划按显示的两位小数金额投入可能产生少量差额；回算允许误差为 `max(target × 1e-9, 1e-6)`。
- 零本金或零累计投入时，相应收益率显示 N/A。Rule of 72 仅在正收益率下展示，是近似估算。

## Assumptions / 假设说明

- **Fixed return assumption**：收益率固定，不保证实际收益。
- **Compounding frequency depends on module**：复利模块按年，DCA 和目标规划按月。
- **No tax or fees**：不考虑税费和手续费。
- **Fixed inflation assumption**：仅复利与定投另列通胀折现结果，不预测真实通胀；原有收益与图表保持名义金额，Goal Planner 不做通胀调整。
- **Planning modules**：原有三个规划模块使用固定收益假设，不使用真实行情；开发中的 Portfolio Analytics 使用真实历史行情。 / The three planning modules use fixed assumptions; Portfolio Analytics uses historical market data.
- **Educational use only**：仅用于金融教育和演示。
- **Not investment advice**：结果不构成投资建议或市场回报预测。

## Roadmap / 未来方向

以下为潜在探索方向，**不属于 v0.2.0，尚未实现或承诺交付**：

- v0.3 Phase 1 Historical Portfolio Analytics / 历史组合分析正在本地开发，详见下节。
- Export/report functionality / 导出与报告。
- Additional financial insight tools / 更多金融解读工具。

## v0.3 Phase 1 Development / 历史组合分析开发中

公开稳定版本仍为 **v0.2.0**；以下功能为本地开发，尚未发布 v0.3.0。

The stable public release remains **v0.2.0**. These are local development features, not a v0.3.0 release.

- **组合设置 / Setup**：输入 `AAPL, MSFT, NVDA` 和 `40, 30, 30` 等百分比权重；权重非负且合计 100%（容差 0.01 个百分点，随后标准化），结束日包含在请求中。默认基准 SPY，无风险年有效利率 4% 可编辑，是固定假设而非实时国债报价。
- **历史分析 / Analytics**：Analyze Portfolio 展示五个 KPI、组合与基准增长曲线（共同起点 100）、指标对照表、回撤图和相关性矩阵。
- **保存加载 / Persistence**：填写名称后 Save Portfolio；在 Saved Portfolios 中选择并 Load Portfolio。同名保存更新配置、保留创建时间，保存不需要下载行情。支持同币种股票/ETF，不进行外汇转换。

Enter comma-separated tickers and percentage weights, dates, benchmark, and effective annual risk-free rate. Click **Analyze Portfolio** for KPIs, normalized growth, comparison metrics, drawdown and correlations. Save a named configuration and load it from Saved Portfolios; saving the same name updates it. Use same-currency stocks/ETFs; no FX conversion is performed.

### Market Data / 数据与对齐

行情来自 Yahoo Finance，经 [yfinance.download](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html) 获取 `auto_adjust=True` 的日频 Close，采用提供方拆股/分红复权口径，是历史总收益的实用近似，并非经审计的精确可交易总收益。应用将结束日加一天，适配提供方结束日不包含规则。

Daily prices come from Yahoo Finance through yfinance with `auto_adjust=True`, using provider-adjusted close for splits/dividends as a practical return proxy. This is not an audited investable total-return series. The UI end date is inclusive; the download accounts for the provider's exclusive end date.

资产和基准先取共同有效价格日，不前填/后填，再计算 `P[t] / P[t-1] - 1`。至少需要三个共同价格观测值。页面显示实际区间和收益观测数；上市时间等情况可能缩短区间。超过七个日历日的缺口被拒绝；较短报价缺失或跨市场假日可能产生跨交易日收益，年化风险因此为近似值。建议使用同市场、同币种资产，核对实际区间。

Prices are intersected on common observed dates before calculating returns, with no fills. At least three common prices are required. Actual dates and observation counts are displayed; listings and missing data may narrow the period. Gaps over seven calendar days are rejected. Shorter missing quotes or differing holidays can span multiple sessions, making annualized risk approximate. Prefer assets in the same market and currency.

### Public Data Strategy / 公开数据策略

优先级：**有效 SQLite Cache → Yahoo Finance / yfinance → Demo Data / 演示数据**。Kibot 下载代码已移除；旧 Kibot 缓存被排除，旧 FINANCE_LAB_FALLBACK 设置不会重新启用它。没有接入 Alpha Vantage。

Priority: **fresh SQLite cache → Yahoo Finance / yfinance → Demo Data**. Kibot download code is removed, existing Kibot cache is excluded, and the old FINANCE_LAB_FALLBACK variable cannot enable it. Alpha Vantage is not integrated.

Yahoo 使用 auto_adjust=True 的拆股/分红复权日线；有效缓存保留来源，重复请求可直接复用。限流、临时网络或空行情响应可触发演示模式。若任一资产需要演示数据，整个组合及基准统一改用演示数据，避免混合真实和合成收益。

Yahoo uses split/dividend-adjusted daily prices (auto_adjust=True). Cache metadata preserves origin. Rate limits, network failures or empty prices can trigger demo mode. If any asset needs demo data, all assets and the benchmark use synthetic prices for a consistent comparison.

演示数据完全由本项目程序生成，不含第三方真实行情：支持 AAPL、MSFT、NVDA、SPY，2000–2100 年工作日日历。固定随机种子、固定起点和公共/独立冲击生成正价格，包含波动、回撤及相关性。同 ticker 同日期的结果保持一致，不随请求区间变化。它不是真实历史、实时行情、预测或经校准的市场模型；工作日不排除交易所假日。

Demo data is generated entirely by this project, without third-party market prices. It supports AAPL, MSFT, NVDA and SPY over business days in 2000–2100. Fixed seeds, a fixed epoch and shared/individual shocks produce repeatable positive prices, volatility, drawdowns and correlation. Values are stable across overlapping requests. This is neither historical/live market data, a prediction nor a calibrated market model; exchange holidays are not excluded.

页面显示 Yahoo Finance、SQLite Cache 或 Demo Data；演示时显示非阻断提示和合成数据说明。演示价格不写入真实行情缓存，因此不会掩盖下一次 Yahoo 恢复；analysis_runs 仍记录 demo、synthetic 和数据集版本。其他 ticker 可使用 Yahoo，但不在演示目录内时会给出清晰提示。

The UI identifies Yahoo Finance, SQLite Cache or Demo Data and displays non-blocking synthetic-data notices. Demo prices are not stored in the real-price cache, so later requests can recover to Yahoo. Analysis metadata records demo provenance, synthetic price type and dataset version. Other tickers can use Yahoo but are unavailable in the demo catalog.

本地验收：AAPL / 100 / SPY / 2025-01-01 → 2026-01-01 / 无风险利率 4%；或 AAPL, MSFT, NVDA / 40, 30, 30 / 相同基准和日期。Yahoo 不可用时仍应显示五项 KPI、增长曲线、比较表、回撤和相关性矩阵，并明确标注演示数据。公开版仍是 v0.3 Phase 1 开发，稳定公开版本保持 v0.2.0。

Manual validation: AAPL / 100 / SPY / 2025-01-01 → 2026-01-01 / risk-free 4%; alternatively AAPL, MSFT, NVDA / 40, 30, 30. Yahoo failures should yield five KPIs, growth, comparison, drawdown and correlation, clearly labeled as Demo Data. This remains v0.3 Phase 1 development; the stable public release remains v0.2.0.

### Metrics / 计算口径

组合日收益为 `sum(weight[i] * return[i])`；假设每日恢复目标权重、无出入金、不计税费/交易成本，不是权重自然漂移的 buy-and-hold。

Portfolio returns are weighted daily asset returns assuming daily target-weight rebalancing, no cash flows, and no taxes or transaction costs.

| Metric / 指标 | Definition / 定义 |
|---|---|
| Cumulative Return / 累计收益 | `product(1 + r) - 1` |
| CAGR / 年化复合收益 | `product(1 + r) ** (365.25 / elapsed_calendar_days) - 1`，使用实际共同价格首末日期 / actual common price dates |
| Annualized Volatility / 年化波动 | 样本标准差 / sample `std(r, ddof=1) * sqrt(252)` |
| Sharpe Ratio | `mean(r - daily_rf) / std(r, ddof=1) * sqrt(252)`；`daily_rf = (1 + annual_rf) ** (1/252) - 1` |
| Maximum Drawdown / 最大回撤 | `min(wealth / running_peak - 1)`，含初始本金，返回非正值 / includes initial capital, nonpositive |

空值、NaN、无穷和非法价格/日期明确报错。不足两项收益时波动/Sharpe 不适用；零波动 Sharpe 和常数收益相关性显示 N/A。短区间 CAGR 可能极端，不代表未来预期。

Invalid/empty/nonfinite data and invalid periods raise errors. Risk metrics require at least two returns; zero-volatility Sharpe and constant-series correlations show N/A. Short-period CAGR can be extreme and is not a forecast.

### SQLite / 实际 SQL 存储

默认路径 `data/finance_lab.sqlite3`，可通过 `FINANCE_LAB_DB` 环境变量覆盖。内置 sqlite3 实际执行参数化 `SELECT`、`INSERT`、`DELETE`、`INSERT OR REPLACE`、`ON CONFLICT ... DO UPDATE`，并使用建表、事务提交与回滚。

The default database is `data/finance_lab.sqlite3`, configurable through `FINANCE_LAB_DB`. Built-in sqlite3 runs real parameterized SQL reads, inserts, updates, deletes, and transactional commits/rollbacks.

| Table / 表 | Purpose / 用途 |
|---|---|
| `historical_prices` | `(ticker, date)` 主键，复权价格、来源、更新时间 / adjusted prices, source and timestamp |
| `price_requests` | 成功区间请求、来源元数据、24 小时有效期；可复用覆盖请求 / successful range markers and provenance, covering-cache reuse, 24-hour TTL |
| `portfolio_configs` | 名称主键、JSON 配置（资产、权重、基准、日期、利率）、创建及更新时间 / named configuration snapshots and timestamps |
| `analysis_runs` | 自增 run_id、配置、时间戳、基准、实际区间、每个 ticker 实际来源 / completed-analysis metadata, actual dates and provider provenance |

重复请求通过 SQL 读取缓存，过期后重新获取。复权数据刷新替换对应区间，使重叠请求标记失效；失败/空下载不标记成功。数据库不纳入 Git。部署平台重启可能丢失 SQLite；公共实例的保存名称空间共享、无用户隔离，请勿保存敏感信息。

Repeated requests read SQLite; expired requests refresh. Revised adjusted prices replace the range and invalidate overlapping cache markers. Failed/empty downloads are not cached as successful. Database files are ignored by Git. Hosting restarts may discard local SQLite; public instances share saved names without user isolation.

### Acceptance Status / 验收状态

Phase 1 主要功能已通过人工浏览器验收（用户确认）：数据源优先级、演示切换及标注、五项 KPI、增长曲线、比较表、回撤和相关性矩阵均正常。公开路径使用 Yahoo 和确定性演示数据。本次收尾缩短 KPI 标题，并保留完整指标说明。**当前仍为 v0.3 development，稳定公开版本保持 v0.2.0；不是 v0.3.0 发布。**未加入未来预测、Monte Carlo、VaR/CVaR、优化、AI 助手或交易功能。

The user confirmed manual browser acceptance of Phase 1: provider priority, labeled demo fallback, five KPIs, growth/comparison, drawdown and correlation. Public runtime uses Yahoo and deterministic synthetic demo data. Final polish shortens KPI labels while retaining full descriptions. **This remains v0.3 development based on stable public v0.2.0, not a v0.3.0 release.** No forecasting, Monte Carlo, VaR/CVaR, optimization, AI assistant, or trading features are included.

仅用于教育和研究，不构成投资建议。**历史表现不保证未来收益。**

For education and research only, not investment advice. **Historical performance does not guarantee future results.**

## Security / 安全

不要提交密码、API key 或凭据。`.gitignore` 排除 `.env`、`.env.*` 和 `.streamlit/secrets.toml`；私密配置不应纳入公开仓库。

## Version / 版本

当前版本：**v0.2.0**。网页与 CLI 均显示 `Finance Mini Lab v0.2.0`。

开发过程与各里程碑验证记录见 [Project Log](docs/project_log.md)。
