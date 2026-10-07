## 2026-10-08 — Phase 3 Language & Explainability Cleanup / 语言与解释层收尾

- 用户确认 Phase 3 逻辑人工验收通过。Portfolio Analytics 增加默认 English 的语言选择器，覆盖历史分析、未来模拟、Guidance、Demo、表格、帮助和按钮；其他计算器不变。 / User confirmed logic acceptance; added English-default single-language portfolio rendering with Chinese support.
- 文案集中管理于 i18n helper 与两个 JSON catalogs；保留现有金融模型和评分逻辑，仅转换展示。表单按钮使用稳定 key，语言切换保留输入、分析结果和模拟路径，不请求网络/重跑模型。 / Centralized translations and stable widget keys preserve analytics across language switches.
- 十类专业指标增加通俗 tooltip/helper/折叠解释；Guidance 详细评分和模型假设默认折叠，主视图保留关键原因。 / Added metric explainability and compact information hierarchy.
- 完整离线测试 189/189 通过（原有 183 + 新增 6），git diff --check 通过；切换语言保留数值、模拟路径及匹配结果，未触发下载/模拟。Git 文件及常见密钥扫描通过，数据库/缓存/Secrets/日志均排除；main/origin/main 保持 2bf94c5d5e07da1564372ede7bb0d741654aa467。 / All 189 offline tests, formatting and file/secret checks passed; analytics invariance and unchanged main refs verified.
- 已准备 English/中文视觉验收步骤；本轮创建本地开发 commit，不 push、不 merge、不开始 release packaging，稳定公开版本保持 v0.2.0。 / Language visual acceptance steps prepared; local commit only, with stable main unchanged.

## 2026-10-08 — Phase 3 Portfolio Guidance / 组合建议（开发中）

- 在 v0.3-dev 实现 Portfolio Guidance：三个轻量偏好字段、风险等级、偏好匹配、3–5 条有依据的建议、抽象配置方向和评分明细。无新主 Tab、数据源、依赖或优化器。 / Added modular rule-based guidance within Portfolio Analytics.
- 复用历史指标、相关性、权重、基准、模拟分位数/亏损率/参数和情景，不下载行情或重算核心结果。新增模拟后建议自动刷新。 / Reuses existing evidence without network or simulation calls.
- 启发式多指标评分；有效波动率和回撤为必需证据。偏好/期限/目标共同设定风险上限。具体阈值见 README，不是经验证或受监管的适当性模型。 / Documents educational thresholds and profile caps.
- Demo guidance 明确 synthetic；可在没有未来模拟时运行基础判断；数据不足时披露缺失，不伪造确定结论。 / Supports demo and partial evidence with explicit limitations.
- 完整离线测试 183/183 通过（原有 155 + 新增 28），git diff --check 通过。覆盖偏好匹配、阈值边界、相关性/回撤/亏损提示、缺失数据、Demo 标签及端到端无重复下载/模拟调用。 / All 183 offline tests and formatting checks passed, including 28 new engine/UI cases.
- 人工验收待完成。局限：不穿透 ETF、不识别行业/风格，不评估真实资金承受能力；不同模拟期限及缺失可选证据可影响评级。教育性类别方向，不提供具体交易建议。 / Manual acceptance pending; heuristic, data-coverage and profile limitations are explicit.
- 未 commit、push 或 merge，不做 v0.3 release packaging；稳定公开版本仍为 v0.2.0。 / No commit, push, merge or release packaging.

## 2026-10-08 — Phase 2 Final Acceptance / Phase 2 最终验收

- 用户确认 Future Outlook、三情景、Monte Carlo、P10/P50/P90、亏损概率、分布、解释和 Demo 标注均通过人工视觉验收。 / User confirmed manual and visual acceptance of Phase 2 outputs and demo provenance.
- Performance Overview 已采用 3+2 KPI 布局；百分比和 Sharpe 均为两位小数。保留现有 Future Outlook 布局，仅补充恒定参数、无通胀或参数误差等简洁假设提示。 / Preserved the accepted 3+2 KPI layout; clarified assumptions without changing the financial model.
- 方法复核：至少 60 个组合日收益观测、252 日年化对数参数、月度 GBM、μ±σ 情景、P10/P50/P90、终值严格低于初值的亏损概率、固定种子复现。Base 为平均财富，P50 为中位数；未来模拟复用历史收益，不下载行情。 / Confirmed consistent methods, mean/median distinction and no redundant downloads.
- 模型简化：恒定参数、独立正态对数收益；不计追加投入、税费、通胀或参数估计不确定性。Demo 模拟仅作 synthetic 功能展示，不是预测或保证。 / Simplified model assumptions and synthetic-demo limitations remain explicit.
- 最终完整离线测试 155/155 通过；git diff --check 通过。提交文件检查与常见密钥模式扫描通过；数据库、缓存、Secrets、测试日志和本地运行文件均未纳入提交。main/origin/main 均保持 2bf94c5d5e07da1564372ede7bb0d741654aa467。 / Final full offline suite: 155/155 passed; formatting and file/secret review passed. Runtime files excluded; both main refs unchanged.
- 仅在 v0.3-dev 创建本地 Phase 2 commit，不 push、不 merge、不开始 Phase 3；稳定公开版保持 v0.2.0。 / Local development commit only; stable public v0.2.0 remains unchanged.

## 2026-10-07 — Phase 2 Future Outlook / 未来展望（开发中）

- 在 v0.3-dev 实现 Future Outlook，接在 Portfolio Analytics 底部；不新增主 Tab、数据源或依赖。 / Added Future Outlook within Portfolio Analytics on v0.3-dev, without a new tab, provider or dependency.
- 复用历史组合收益；至少 60 个观测。日对数收益估计 g、σ，252 日年化，GBM 漂移 μ=g+σ²/2；按月精确转移，默认 5000 次、固定 seed=20261007。 / Estimates log-return parameters from history with exact monthly GBM transitions.
- 三情景使用 μ±σ 和 μ；Base 为模型平均财富，不是 P50。输出期限内节点、三条曲线、P10/P50/P90、严格终值亏损/获利概率、50 条路径、点态区间和分布；规则解释不提供荐股或交易信号。 / Added scenarios, simulated outcomes, probabilities, bounded path rendering, distributions and rule-based interpretation.
- Demo-based simulation 明确为 synthetic 功能演示；重新历史分析清除模拟，普通重跑复用 session 结果，未来分析不请求行情。 / Preserves demo provenance and avoids redundant downloads or simulations.
- 完整离线测试 155/155 通过（原有 136 + 新增 19）；git diff --check 通过。包括端到端 Yahoo 失败 → Demo → Future Outlook 的 UI smoke。 / All 155 offline tests and formatting checks passed.
- 本机纯计算性能（5 次运行中位数，非浏览器渲染）：5 年/5000 次约 0.0114 秒、路径数组 2.33 MiB；10000 次约 0.0219 秒、4.65 MiB。 / Local numerical timings only, excluding browser rendering.
- 限制：恒定参数、独立正态对数收益、无追加投入/税费；样本和模型误差未纳入，分位数不是保证，60 个观测不代表可靠估计。README 记录方法和人工验收输入。 / Documents model assumptions and manual acceptance steps.
- Phase 2 等待用户人工验收；未 commit、push 或 merge，未进入 Phase 3。main/origin/main 和稳定公开 v0.2.0 保持不变。 / Awaiting manual acceptance; no commit, push, merge or Phase 3 work.

## 2026-10-07 — Phase 1 Final Cleanup / Phase 1 最终收尾

- 用户确认人工验收通过：Portfolio Analytics、来源优先级、Demo 标注、五项 KPI、增长比较、表格、回撤和相关性均正常。 / User confirmed manual browser acceptance of the Phase 1 workflow and outputs.
- 保留五列 KPI 布局；Total Return、Volatility、Max Drawdown 使用短标题，悬浮说明保留完整定义。Demo 提示明确仅用于功能展示，不是真实行情或预测。 / Shortened KPI titles with full help text; clarified demo purpose.
- Demo Mode 用于应对 Yahoo 不可用，避免外部数据授权流程阻塞演示；整次分析统一使用 synthetic 数据，不混用真实数据。 / Demo mode keeps the public demonstration available without another provider, with consistent synthetic portfolio and benchmark data.
- 最终完整离线测试 136/136 通过（含原有 v0.2 回归、组合分析、Demo fallback、SQLite 和 UI）；git diff --check 通过。Git 文件与常见密钥模式检查未发现敏感内容；数据库、缓存、Secrets、虚拟环境和测试日志均被忽略。 / Final full offline suite: 136/136 passed; git diff --check passed. File and common secret-pattern review found no sensitive content; runtime databases, caches, secrets, virtual environment and test logs are ignored.
- 仅 Phase 1 收尾；未进入 Phase 2，未升级公开版本，未 push。 / Phase 1 cleanup only; no Phase 2, public version bump or push.

## 2026-10-07 — Public Demo Data Strategy / 公开演示数据策略

- 完整离线测试 136/136 通过；以演示模式测试替换已移除 Kibot 接口的专用测试。 / Full offline suite: 136/136 passed; demo tests replace removed Kibot-specific tests.

- 公开路径改为 SQLite → Yahoo → deterministic synthetic Demo Data；移除 Kibot 下载代码并排除旧 Kibot 缓存。 / Removed Kibot runtime and excluded its cached data.
- 在 src/market_data.py 新增生成器：固定种子与起点，四资产合成工作日价格；任一资产 fallback 时整次分析统一演示，不混合真实数据。 / Fixed-seed, fixed-epoch synthetic prices; coherent all-demo analysis on fallback.
- 演示数据不污染真实行情缓存；分析记录保留 demo 来源、synthetic 口径和版本。UI 明确标注并使用非阻断提示。 / Demo provenance persists in analysis metadata; real cache remains separate.
- 未新增依赖、未改金融计算、未接入 Alpha Vantage、未 commit。稳定公开版本仍为 v0.2.0。 / No dependencies, calculation changes, Alpha Vantage or commit; stable version remains v0.2.0.

> 当前版本：**v0.2.0**。下方旧版本名称和验证数字属于历史里程碑记录，不代表当前产品状态。

# 项目日志

## 2026-10-07 — Lightweight Market Fallback / 轻量备用行情

- 保留 SQLite → Yahoo 优先级，新增 Kibot 官方 guest 日线作为本地内部评估 fallback；使用内置 urllib，无新增依赖。Stooq 实测为浏览器验证页且 2026 年出现 API key 要求；Nasdaq 条款限制提取/再分发，未采用。 / Preserved cache/Yahoo priority; added documented Kibot guest daily evaluation access with standard-library HTTP.
- Yahoo 限流、临时网络或空响应会自动切换；格式非法 ticker 不请求网络，合法但无数据的代码经两个来源确认后才提示检查 ticker/date。两个服务故障不误报 ticker 无效。 / Failure categories and fallback decisions distinguish symbol/data availability from outages.
- Kibot 显式请求拆股/分红复权（unadjusted=0, splitadjusted=0），不混拼同一资产的不同来源价格；提供方收盘定义和精度可能不同。 / Explicit split/dividend adjustment; no within-series provider splicing.
- SQLite historical_prices.source 真实记录提供方，新增请求/分析来源 JSON 列，采用保留数据的迁移；缓存命中保留原提供方并标记 retrieval=cache。页面仅增加来源 caption 和评估限制提示，未修改指标、基准计算或 UI 结构。 / Persisted origin/retrieval metadata with additive migrations and minimal UI status text.
- 完整离线测试 140 项通过（此前 124 + 新增 16），使用合成 CSV、mock 和隔离数据库；覆盖主源成功、备用成功/失败、invalid ticker、缓存、来源记录、旧数据库迁移和页面提示。 / All 140 offline tests pass, including 16 new fallback/provenance tests.
- 真实最小输入 AAPL 100%、SPY、2025-01-01 至 2026-01-01、无风险利率 4%：Yahoo 限流后双资产自动使用 Kibot，获得 250 个共同价格日（2025-01-02 至 2025-12-31），指标和缓存重用验证成功。实际验证使用独立、Git 忽略的 SQLite 文件。 / Live local evaluation succeeded through fallback and then cache.
- Kibot guest 仅供评估，license 仅授权内部使用，不能据此公开再分发；README 要求公开部署前设置 FINANCE_LAB_FALLBACK=off（同时排除已缓存 Kibot 数据），或取得适用授权。公开数据授权及人工浏览器验收仍待完成。 / Guest/internal evaluation is not a public redistribution license.
- 不 commit、不推送、不部署、不更改公开 v0.2.0 版本。 / No commit, push, deployment or public-version change.

## 2026-10-07 — v0.3 Phase 1 Development / 历史组合分析开发

- 新增 database、market_data、portfolio_analysis、portfolio_metrics、benchmark、portfolio_ui 六个独立模块；原有六个 v0.2 计算模块未修改，公开版本标题保持 v0.2.0。 / Added six analytics modules; existing v0.2 calculations and version titles are preserved.
- 新增 Portfolio Analytics 主标签页、多资产权重输入、基准、日期、可编辑无风险利率、配置保存/加载、五个 KPI、增长曲线、回撤与相关矩阵。 / Added setup, persistence, KPIs, comparison growth, drawdown and correlation UI.
- SQLite 实际保存历史复权价格、24 小时请求缓存、命名配置和成功分析元数据，使用参数化 SQL、UPSERT 和事务。 / SQLite powers historical price caching, named configurations and analysis records through parameterized SQL and transactions.
- Yahoo Finance / yfinance 使用 auto_adjust=True，结束日包含；共同日期对齐且不填充。组合假设每日恢复目标权重；252 交易日样本波动与 Sharpe，CAGR 使用实际日历期，无税费。 / Adjusted daily prices, common observed dates without fills, daily target-weight rebalancing, 252-session risk and calendar CAGR, without fees.
- requirements 新增 yfinance 并直接声明 pandas/numpy；数据库与验证日志被 Git 忽略。 / Dependencies and ignore rules updated.
- 完整离线套件 104 项通过：原有 65 项 + 新增 39 项；行情测试 mock，SQLite 使用隔离临时文件。仅调整现有 UI 测试的新增标签页/控件结构断言。 / All 104 offline tests pass, including 65 existing and 39 new tests.
- 本地 Streamlit 临时端口 18503 健康检查返回 HTTP 200 / ok，测试服务随后关闭；git diff --check 通过。 / Local Streamlit health returned HTTP 200 / ok; the test server was stopped. Diff whitespace checks pass.
- 真实 Yahoo 下载遭遇 Too Many Requests 限流；因此真实下载成功与浏览器人工视觉验收尚待确认，不宣称 Phase 1 最终验收完成。 / Live Yahoo retrieval was rate-limited; live success and manual visual acceptance remain pending.
- 不 commit、不推送、不部署、不创建 v0.3.0 Release。 / No commit, push, deployment or v0.3.0 release.

## 2026-09-30 — Milestone 1：Compound Interest Calculator

### 今天完成的内容

- 建立 Python 项目结构，预留 tests 和 assets 目录。
- 实现复利函数 calculate_future_value，以及本金、年化收益率和年限的基础校验。
- 在 app.py 中调用函数，使用固定参数 10000、0.08、10，结果格式化为两位小数。
- 编写 README、仅含标准库说明的 requirements.txt 和 Python .gitignore。
- 未初始化 Git，未进行 commit。

### 核心金融公式

`FV = PV × (1 + r)^n`

PV 是本金，r 是小数形式的年化收益率，n 是投资年限，FV 是未来价值。假设收益每年复投、收益率固定、没有追加投入或取款，不计税费和通胀。

示例：`10000 × (1 + 0.08)^10 ≈ 21589.25`。

### 当前项目结构

```text
Finance-Mini-Lab/
├─ README.md
├─ requirements.txt
├─ app.py
├─ .gitignore
├─ src/
│  └─ compound_interest.py
├─ tests/
├─ assets/
└─ docs/
   └─ project_log.md
```

### 本次技术路线

采用 Python 3 和标准库，无第三方依赖。计算函数与程序入口分离，便于后续复用。使用 ** 表示乘方，使用 ValueError 报告违反约束的参数，仅在输出时用 .2f 保留两位小数。

### 实际验证结果

当前环境无法识别 python、py 或 python3 命令，因此使用 Codex 自带 Python 解释器运行 app.py，实际输出为 `21589.25`，程序无报错。

使用临时命令检查了 5 个有效场景（标准示例、零收益率、零年限、零本金、负收益率）和 4 个无效场景（负本金、收益率等于 -1、收益率小于 -1、负年限），全部通过。无效参数均按预期抛出 ValueError。此次未添加测试文件，tests 目录仍为空。

### 下一步计划

加入用户输入：读取本金、百分数形式的年化收益率和投资年限，将收益率转换为小数；处理非数字输入，并友好展示校验错误。

## 2026-09-30 — Milestone 1.1：Interactive User Input

### 本次完成

- app.py 改为依次读取本金、年化收益率百分比和投资年限。
- 使用 float 将输入转换为数字，收益率百分比除以 100，例如 8 转换为 0.08。
- 核心文件 src/compound_interest.py 保持不变，通过导入别名 calculate_compound_interest 调用原 calculate_future_value 函数，复用公式和基础校验。
- 对非数字、负本金、收益率不大于 -100%、负年限提供友好错误提示；错误后结束本次运行，用户可重新运行。补充非有限数值、溢出和取消输入处理。
- 输出本金、收益率、年限及未来价值；金额使用人民币符号、千位分隔符和两位小数。
- 更新 README 交互运行说明。本次未暂存、未 commit，无新增第三方依赖，项目目录结构不变。

### 核心公式与技术路线

继续使用 Python 3 和标准库，金融公式仍为 FV = PV × (1 + r)^n。入口负责输入转换、提示和输出；核心函数负责参数约束及复利计算。使用 math.isfinite 拦截非有限数值。

### 实际验证

使用 Codex 自带 Python 解释器，通过子进程向 app.py 传入标准输入，共验证 14 个场景，全部通过，无未处理异常：

- 10000 / 8 / 10：Future Value: ¥21,589.25。
- 10000 / 0 / 10：Future Value: ¥10,000.00。
- 在本金、收益率、年限任一位置输入非数字：显示有效数字提示。
- 负本金、收益率 -100%、收益率 -101%、负年限：显示对应约束提示。
- nan：显示有限数值提示。
- 10000 / -10 / 1：¥9,000.00。
- 10000 / 8 / 0：¥10,000.00。
- 极大参数导致计算溢出：显示超出支持范围提示。
- 输入流结束：显示取消提示。

当前系统 python 命令仍未配置，本次使用现有解释器完整路径验证。沙箱进程启动失败后，经授权在沙箱外完成读写和验证。

### 下一步候选计划

后续可加入错误后重新输入，并将当前验证场景整理成可重复运行的自动化测试；本次未实现这些扩展。

## 2026-09-30 — Milestone 1.2：Streamlit UI + Growth Chart

### UI 技术路线与新增功能

- 新增 streamlit_app.py，使用 Streamlit 表单、数字输入框、Calculate 按钮、metric 结果区和内置图表；保留 app.py 命令行入口。
- 原 src/compound_interest.py 完全不变。网页将百分比除以 100，再复用 calculate_future_value；未重复实现复利公式。
- 图表数据使用 Python 字典。第 0 年到最终年逐年调用核心函数，横轴 Year，纵轴 Portfolio Value。0 年期限用单个散点展示本金。
- 本金和年限不能为负，收益率必须大于 -100%；提供友好错误提示，并处理非有限数值及溢出。用户可修改参数后重新计算。
- 网页使用整数年，上限为 1000 年，限制图表数据量。数字控件负责非数字及控件范围的输入约束。
- requirements.txt 新增唯一直接依赖 streamlit>=1.50,<2；未直接使用 pandas，不单独声明。Streamlit 的间接依赖由 pip 安装。
- 在项目 .venv 中安装依赖，实际验证版本为 Python 3.12.14、Streamlit 1.64.0；.venv 已由现有 .gitignore 忽略。
- 更新 README，补充安装、启动、交互、曲线说明及测试命令。
- 新增 tests/test_streamlit_app.py，使用标准库 unittest 与 Streamlit AppTest 验证交互与图表数据，无新增测试框架依赖。

### 验证结果

- Python 语法检查通过，覆盖命令行入口、网页入口、核心函数和测试文件。
- 核心函数 10000 / 0.08 / 10 返回值按两位小数显示为 21589.25。
- 6 个自动化测试方法全部通过，包含标准结果及逐年数据、零收益率、零年限、4 种无效参数、溢出、错误修正后再次计算。
- 默认曲线共有 11 个点，起点为 10000，终点约 21589.25；验证各相邻年份按 8% 增长。
- 实际启动 Streamlit 服务成功；http://127.0.0.1:8501/ 返回 HTTP 200，/_stcore/health 返回 HTTP 200 和 ok。
- 测试最初发现 AppTest 相对路径以测试文件目录为基准，改为绝对路径后通过。测试运行会出现可忽略的 missing ScriptRunContext 提示，没有未处理异常。
- 本次完成应用层自动化测试与 HTTP 启动检查，未进行真实浏览器视觉验收。
- Git 差异检查通过，app.py 和核心函数无改动。本次不暂存、不 commit。

### 环境与运行方式

沙箱进程仍无法启动，经授权在沙箱外执行。系统 python 命令不可用，因此利用已有解释器创建项目虚拟环境。后续可直接在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

本次验证服务在 127.0.0.1:8501 启动，用户可在浏览器打开该地址查看。

## 2026-10-01 — Milestone 1.2.1：UI Polish

本次仅优化界面与可读性，不新增金融功能，不修改核心公式或计算结果逻辑，不进行 Git commit。

### 主要视觉与可读性调整

- 保留 Finance Mini Lab v0.1 标题，增加英文副标题 Estimate how an investment grows through annual compounding.
- 输入标签统一为自然的双语格式，增加 Investment Inputs 分区标题；保留默认值 10000 / 8 / 10。
- 结果使用两列、四张原生带边框指标卡；金额统一显示 ¥、千分位及两位小数，收益率显示两位小数。
- 图表标题为 Portfolio Growth Over Time；坐标轴为 Year 和 Portfolio Value (¥)，统一为青绿色、360 像素高度。
- 保留从 Year 0 开始的原有数据，以及 0 年期限的单点展示。简化计算前说明，不引入 CSS 或新依赖。
- 更新 README；测试仅同步金额轴名称断言，其余计算与校验断言保持不变。

### 验证结果与环境

- 原有 6 个测试方法全部通过，默认结果为 ¥21,589.25；图表数据仍为第 0–10 年共 11 个点，从 10000 增长至约 21589.25。
- 验证范围包括正常结果、图表组件生成、零收益率、零年限、无效输入、溢出和错误后重算。
- 本地 Streamlit 服务正常，健康检查返回 ok。
- 浏览器验证工具两次因 Windows 沙箱初始化失败退出，无法进行真实浏览器视觉检查；图表由 AppTest 验证生成。
- 继续使用项目 .venv。因沙箱启动失败，经授权在沙箱外完成文件修改及测试。测试中出现可忽略的 ScriptRunContext 提示，无未处理异常。

## 2026-10-01 — Milestone 1.3：Content Enrichment + Financial Insights

### 完成内容

- 保留输入区、原核心计算及校验逻辑，扩展六项双语结果指标。
- 新增 Total Profit = FV − PV；Total Return = (FV − PV) / PV × 100%。零本金时比率不适用。
- 新增逐年表格（Year 0 到最终年）、本金与累计收益构成柱状图、4% / 当前收益率 / 12% 情景曲线；相同收益率去重，情景计算仍复用 calculate_future_value。
- 新增正收益率下的 Rule of 72 近似翻倍估算；明确标注非精确结果。
- 新增资产倍数、累计收益和近似翻倍时间的简短说明，以及底部假设说明。仅描述计算结果，不提供投资建议。
- 使用标签页组织明细和对比内容，无新增第三方依赖。负收益如实显示，零本金不输出误导性的倍数或翻倍描述。
- 情景计算发生溢出时提示并省略该曲线，保留当前结果。
- 更新 README 和原有测试，保留 Milestone 1.2.1 尚未提交的界面修改；本次不暂存、不 commit。

### 验证结果

- 共 12 个测试方法全部通过，涵盖原有场景和新增收益、逐年表格、收益构成、Rule of 72、情景曲线及去重。
- 10000 / 8 / 10：FV = ¥21,589.25；Total Profit = ¥11,589.25；Total Return = 115.89%；Rule of 72 = 9.00 年（近似）。
- 逐年数据从 Year 0 本金 ¥10,000.00、收益 ¥0.00 开始，到 Year 10 的资产 ¥21,589.25、收益 ¥11,589.25。
- 当前收益率 4% 或 12% 时仅两条对比曲线，8% 时三条，当前情景均有 Current 标识。
- 零本金、非正收益率、零年限、负输入、计算溢出和错误后重算均通过验证。
- 测试过程中出现可忽略的 ScriptRunContext 提示，无未处理异常。沙箱启动问题仍存在，经授权在沙箱外使用项目 .venv 执行；本次未进行浏览器视觉验收。

## 2026-10-01 — Milestone 2.0：DCA Simulator

### 完成内容与技术路线

- 新增 src/dca.py 中的 calculate_dca，固定月收益率为 annual_rate / 12；每月先增长，再加入月末定投金额。v0.1 为固定收益率模拟，并非真实市场回报预测。
- 返回最终资产、累计投入（含初始本金）、投资收益、简单总收益率及 Year 0 到最终年的逐年数据。总收益率 = 投资收益 / 累计投入，不是年化或资金加权收益率；零投入时为 None。
- 校验非负本金、非负每月投入、年化收益率大于 -100%、有限数值和 0–1000 整数年，并处理溢出。
- Streamlit 分为 Compound Interest / 复利计算、DCA Simulator / 定投模拟两个标签页。原模块封装为独立渲染函数，避免其提前 return 阻止 DCA 页面显示。
- DCA 页面提供四个输入、五项结果、累计投入与资产价值双曲线和逐年表格；金额统一格式化。0 年使用单点图。
- 新增 tests/test_dca.py 和 tests/test_dca_ui.py，原 tests/test_streamlit_app.py 保持不变；README 更新双模块说明、算法假设、运行方式及标准案例。
- 无新增第三方依赖，未修改 app.py 或 src/compound_interest.py，未进行 Git 暂存或 commit。

### 实际验证

- 全部 25 个测试方法通过：原 Compound Interest 12 个、DCA 核心 9 个、DCA 页面 4 个。
- 标准案例 10000 / 每月1000 / 8% / 10年：最终资产 ¥205,142.44，累计投入 ¥130,000.00，投资收益 ¥75,142.44，总收益率 57.80%。
- 使用独立月末年金闭式公式验证标准案例，确保末次投入不获得当月利息。
- 0% 收益率下最终资产等于本金加全部投入；零本金仍可定投；每月投入为 0 时与月度复利公式一致，并通过有效年收益率换算与原年度复利函数交叉验证。
- 年度数据、输入错误、负收益、溢出、零年限、图表、表格及两个模块交替计算均已测试。
- 测试中出现可忽略的 ScriptRunContext 提示，无未处理异常。沙箱启动错误仍存在，经授权在沙箱外使用项目 .venv 验证；本次未进行真实浏览器视觉验收。

## 2026-10-01 — Milestone 3.0：Goal Planner / 目标规划器

### 完成内容

- 新增 src/goal_planner.py，calculate_goal_plan 通过 DCA 计算本金自身期末价值和单位月投入系数，反推所需月投入，再调用 DCA 生成完整模拟结果。
- 与 DCA 共用月收益率 annual_rate / 12、每月先增长后投入的假设；0% 时按月数线性分摊，本金期末价值足够时月投入为 0。
- 目标必须大于 0、本金非负、收益率大于 -100%、年限为 1–1000 整数，校验有限输入并处理溢出。
- 页面新增第三个 Goal Planner 标签，独立输入、五项结果、累计投入/模拟资产/水平目标线图表、逐年表格和简短 Financial Insight。
- Remaining Gap 最小为 0；若本金已足够，真实期末资产允许超过目标。结果模拟保留未舍入月投入，页面明确提示两位小数仅用于显示。
- 新增 tests/test_goal_planner.py 和 tests/test_goal_planner_ui.py；tests/test_dca_ui.py 仅将标签列表断言从两个更新为三个。README 更新三模块、算法、容差和标准案例说明。
- 没有修改原两个模块的核心文件，没有新增依赖，未暂存、未 commit。

### 测试与标准案例

- 全部 37 个测试方法通过：原有 25 个，加 Goal Planner 核心 8 个及 UI 4 个。
- 覆盖 0% 收益率、本金已足够、零本金、无效输入、负收益率、极小正收益率、DCA 回算、非负差额、图表目标线、表格和原模块交替运行。
- 明确浮点容差：rel_tol=1e-9、abs_tol=1e-6，允许误差为两者对应限值的较大者。
- 标准案例 1000000 / 100000 / 8% / 10 年：所需月投入 4252.816825315485，显示 ¥4,252.82。
- DCA 回算期末资产为 999999.9999999972，误差远小于该案例 ¥0.001 容差；总投入 ¥610,338.02，投资增长 ¥389,661.98。
- 沙箱启动问题仍存在，经授权在沙箱外使用项目 .venv 测试。测试出现可忽略的 ScriptRunContext 提示，无未处理异常；本次未进行真实浏览器视觉验收。

## 2026-10-01 — v0.1 Finalization - UI Consistency

### 展示层统一

- 顶部增加简短英文产品介绍及中文用途说明，保留 Finance Mini Lab v0.1。
- 保留三个原有标签页及各模块简短介绍，统一输入区、结果区、图表、逐年表格、结果解读及模块假设的双语标题。
- 统一初始本金、未来价值、累计投入、投资增长等概念命名；金额、百分比及年限格式保持一致。
- 图表统一为 360 像素高度、自适应宽度，时间轴 Year、金额轴 Value (¥)；统一 Portfolio Value 和 Total Contributions 图例，保留目标线及收益构成的分类轴。
- 各模块保留必要的复利频率、月末投入及计算口径说明；页脚集中展示固定收益率、年度/月度复利、不计税费通胀手续费及波动、教育用途和非投资建议的简短双语说明。
- 更新 README 及三个 UI 测试文件的展示名称断言；未修改核心测试数值，未新增依赖或 CSS，未暂存或 commit。

### 验证结果

- 完整测试套件 37 个测试全部通过，包含三个标准案例与原有边界场景。
- Compound Interest：¥21,589.25；DCA：¥205,142.44；Goal Planner 所需月投入：¥4,252.82，均保持不变。
- Git 差异确认 src/compound_interest.py、src/dca.py、src/goal_planner.py 和 requirements.txt 无修改。
- Streamlit 服务健康端点返回 HTTP 200 / ok，页面返回 HTTP 200。
- 环境仍存在沙箱初始化失败，经授权在沙箱外使用项目 .venv 完成修改与测试。AppTest 的 ScriptRunContext 提示不影响测试；本次未进行真实浏览器视觉验收。

## 2026-10-03 — GitHub Ready / Documentation Finalization

### 文档与结构检查

- 将 README 从里程碑累积记录重写为正式项目首页：项目概览、三个核心模块、功能清单、实际技术栈、目录结构、Windows 和通用安装运行方式、CLI、测试、计算口径、假设、未来路线图及 v0.1.0 版本说明。
- 未配置 Git 远程地址，因此 git clone 示例明确使用待替换的仓库所有者占位符；未声称存在在线演示或已发布 Release。
- assets/ 无正式截图，使用 Screenshots coming with v0.1.0 release. 占位，不编造截图文件。
- requirements.txt 仅含 streamlit>=1.50,<2，无需调整。没有添加新依赖。
- .gitignore 已覆盖 .venv、__pycache__、.pytest_cache、.idea、.vscode 等，使用 git check-ignore 验证规则生效，无需修改。
- src/ 三个核心文件独立，tests/ 测试齐全，docs/project_log.md、app.py CLI 与 streamlit_app.py 网页入口均保留；未删除任何必要文件。

### 实际验证

- 完整 37 个测试方法全部通过。
- 独立启动 Streamlit 于本机测试端口 18501，健康端点和页面均返回 HTTP 200；测试进程随后关闭。
- 标准案例保持不变：Compound Interest 21589.25，DCA 205142.44，Goal Planner 每月所需投入显示 4252.82。
- 沙箱初始化问题仍存在，经授权在沙箱外使用项目虚拟环境验证。AppTest 输出可忽略的 ScriptRunContext 提示，无未处理异常。
- 仅修改 README 和本日志；不修改核心代码、不 commit、不推送、不创建 Release。

### 发布前待办

- 用户确定并创建真实 GitHub 仓库后，替换 README 中的仓库地址占位符。
- 人工补充正式截图；当前没有虚构截图、在线演示或发布链接。

## 2026-10-03 — v0.1.0 正式截图补充完成

- 人工提供 assets/compound_interest.png、assets/dca_simulator.png、assets/goal_planner.png 三张正式截图。
- 三张文件均为可完整解码的 RGB PNG，尺寸分别为 999×1387、936×1386、1021×1379。
- README Screenshot / Demo 区域包含三个模块图片及简短说明；移除过时的缺图 TODO 和 assets 为空说明。
- 使用 Markdown 转换器验证产生三个 img 元素，全部 src 相对路径均正确解析到本地 PNG。图片完整性与引用检查通过；图片预览工具因沙箱初始化错误不可用，未进行截图内容的视觉复核。
- 不修改核心代码，不创建 Release。本次按用户要求提交正式截图、README 和日志。


## 2026-10-07 — v0.2.0 Final Packaging

- 当前 README、网页标题、CLI 标题和版本测试统一为 v0.2.0；DCA 文件说明中的版本文字同步，不改金融计算。
- README 更新三个模块定位及 Scenario Analysis、Inflation-adjusted Value、Goal Sensitivity，补充版本亮点、计算口径、真实技术栈和简洁未来方向。
- 保留 Live Demo、knoxlab01 仓库地址、安装与运行命令、安全规则、固定假设和非投资建议说明。
- 三张旧截图保留且可解码，README 分别标记重拍情景分析、通胀结果与目标敏感性区域。
- 发布前仍需更新截图、提交推送并确认线上部署版本；本轮不创建 tag 或 Release，不重写历史。

### 本轮验证

- 完整测试 65 项全部通过，README 如实标记 65 automated tests passing；git diff --check 通过。
- 核对 Python diff 仅涉及版本及产品介绍字符串，无金融计算变化。
- README 本地图片与日志链接均存在，三张 PNG 完整解码；GitHub knoxlab01 仓库页面可访问，未发现旧用户名。localhost:8501 为本地启动示例，不是公共在线地址。
- Live Demo 地址保持不变；初次自动读取遇到重定向问题，加入 Cookie 支持后返回 HTTP 200。已确认地址可达，但发布前仍需浏览器确认线上部署版本与交互功能。

## 2026-10-07 — v0.2.0 新版截图与最终检查

- 人工提供三张新版 PNG，修正文件名中多余的 assets 前缀，恢复 README 约定路径；未修改图片内容。
- 三张 PNG 完整解码，尺寸分别为 987×1345、940×1239、926×1365；README 图片引用存在，截图更新 TODO 已清除。
- 当前公开版本文案统一 v0.2.0，旧版本名称仅保留于历史里程碑记录。
- 完整 65 项测试通过；本轮按要求提交发布包装，不创建 tag 或 Release。
