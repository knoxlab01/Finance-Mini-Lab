# Local Real Historical Data Input / 本地真实历史数据入口

本入口只检查用户自行取得的历史 CSV，不下载数据、不运行模型、不生成研究结论。原始数据与实际来源清单留在本地；Evolance 不再分发第三方原始行情。数据获取及使用许可由使用者负责。

This pipeline checks manually acquired local CSVs. It does not download prices, run models or produce historical conclusions. Raw market data and the actual provenance manifest stay private. The user is responsible for permitted acquisition and use; Evolance does not redistribute third-party raw prices.

## Quick start / 简单步骤

1. 下载许可允许本地研究使用的 `AAPL.csv`、`MSFT.csv`、`NVDA.csv`、`SPY.csv`；优先选择拆股/分红复权价格，尽量覆盖相同的至少5年区间，8–10年以上更好。
2. 放入 `research/private_data/`。无需手动合并或通常情况下重命名列。
3. 复制本目录的 [manifest template](real_data_manifest.example.json) 到 `research/private_data/manifest.json`，填写实际 `source` 和 `download_date`（YYYY-MM-DD），核对资产类别及价格口径。不要把模板的 adjusted 标记用于普通 Close 数据。
4. 从仓库根目录运行下方命令。

Download the four permitted CSVs, place them in `research/private_data/`, copy the manifest template there and fill in actual provenance. No manual merging is needed. Prefer aligned adjusted histories spanning at least five years; 8–10+ years is a stronger research target.

```powershell
Copy-Item research/real_data_manifest.example.json research/private_data/manifest.json
# Edit the LOCAL manifest: source, download_date and actual price convention.
.\.venv\Scripts\python.exe -m research.real_data_check
```

已激活环境时可用 `python -m research.real_data_check`。上述复制仅在实际 manifest 尚不存在时执行，避免覆盖已填写信息。
With an active environment, use `python -m research.real_data_check`. Copy the template only when no actual manifest exists, to avoid overwriting completed provenance.

## Supported layouts / 支持格式

Primary workflow / 首选:

```text
research/private_data/
    manifest.json
    AAPL.csv
    MSFT.csv
    NVDA.csv
    SPY.csv
```

每份文件为一个 ticker，以文件名识别。也支持 `.private.csv` 后缀。支持 UTF-8（含 BOM）、逗号分隔；数值必须是正数，允许引号包围的标准千位分组。Date 列可降序，程序会排序。
One file per ticker, inferred from its filename; `.private.csv` is also supported. Use UTF-8 comma-separated CSVs with positive numeric prices. Quoted US thousands groups are supported. Descending dates are sorted automatically.

Alternative / 宽表: a single CSV with header `Date,AAPL,MSFT,NVDA,SPY`. Wide columns have no price-field label, so their adjusted/close convention must be declared in the local manifest. Do not supply the same ticker in multiple files or both layouts simultaneously.

宽表不必命名为某个 ticker。不要同时保留覆盖相同 ticker 的宽表和独立文件；程序拒绝含糊来源。

## Field detection / 列识别

| Purpose / 用途 | Recognized names (case-insensitive) / 不区分大小写 |
|---|---|
| Date | Date, Datetime, Timestamp |
| Preferred price | Adj Close, Adjusted Close, adjusted_close, adjusted close, adj_close, adjusted |
| Fallback | Close |

Adjusted 字段优先；即使其中有缺失，也不会逐行用 Close 补齐，避免混合口径。多个含糊的调整字段会被拒绝。OHLC/Volume 等其他列不参与收益输入。
Adjusted fields take priority. Missing adjusted values are never substituted with Close values. Ambiguous adjusted fields are rejected; other OHLC/volume columns are not used as prices.

普通 Close 必须标记为 `close`，会给出 `READY_WITH_WARNINGS`，不能标记“完全研究就绪”。股票/ETF 的拆股、分红和其他公司行动一致性无法从 Close 自动保证。即使 manifest 声称 adjusted，也不会覆盖检测到的普通 Close。
Close-only equity/ETF histories remain warnings and are not fully research-ready. A manifest cannot silently upgrade a Close field into adjusted data. Adjustment/source claims are self-declared, not independently authenticated.

## Dates, missing values and alignment / 日期、缺失与对齐

- 优先 ISO `YYYY-MM-DD`。可选 manifest `date_format`（例如 `%m/%d/%Y`）避免非 ISO 日期歧义；未声明的非 ISO 日期使用 pandas 解析，并给出提示。数字 epoch 不猜测单位，请使用日期字符串。
- 时区时间戳可声明 `market_timezone`（例如 `America/New_York`），先转换到该市场时区再取日期；未声明时保留时间戳编码的本地日期并提示。不会静默转 UTC 导致交易日期偏移。
- 相同日期、相同所选价格只保留一次并统计；价格冲突（含缺失与有效值冲突）拒绝。畸形日期、非数值、无穷、零或负价格拒绝。
- 缺失价格日期被排除并报告。严格取有效日期交集；不 forward-fill、不 backfill，不生成交易日或价格。不同 ticker 的首末日期、原始行数、缺失数、对齐丢弃数和最大间隔可查看。
- 对齐后 >7 自然日的间隔不兼容当前冻结数据检查；5–7 日间隔需要复核节假日或缺失。程序没有证券交易所日历，不能证明每个节假日或小缺口均正确。

Prefer ISO dates, or declare a format/timezone. Exact selected-price duplicates are deduplicated; conflicting duplicates and invalid values block use. Missing observations are excluded with warnings. Alignment is an intersection with no filling. This checker does not authenticate exchange calendars, corporate actions or source licenses.

## Manifest / 来源清单

Actual `manifest.json` is ignored and stays local. Fields: dataset_name, source, download_date, usage_context, asset_class, price_type, tickers (including benchmark), benchmark, notes; optional date_format and market_timezone. Missing provenance produces warnings; malformed JSON, unsupported fields and obvious credential patterns are rejected. Do not include identity, account identifiers, passwords, tokens or API keys in any field.

本地清单只记录数据来源与使用口径，不保存身份或账号信息。Free-text provenance is the user's responsibility; automated checks cannot identify every sensitive value. Do not publish a local readiness JSON without reviewing it.

`asset_class` 支持记录 equity / etf / fund，亦可保留 crypto 等未来类别。Crypto Close 不被套用股票复权假设，但本轮未实现 crypto 年化/日历验证，不会认定为 frozen v1.1 研究兼容。
Crypto metadata is retained for future work. Crypto validation/session conventions are not implemented; Close is not silently treated as equity-adjusted data.

## Readiness / 就绪标准

| Status | Meaning / 含义 |
|---|---|
| READY | 所需资产齐全、复权口径及来源声明完整、有效交集满足窗口要求、至少5年、无未解决质量提示 / Required adjusted histories, declared provenance, windows and five-year target satisfied without warnings |
| READY_WITH_WARNINGS | 技术窗口可用但普通 Close、短历史、缺失日期、来源或类别待确认 / Usable observations with explicit limitations; not automatic permission to run final research |
| NOT_READY | 缺少 ticker、数据错误、冲突重复、交集太短、无完整12M窗口、重大间隔，或CLI无法验证Git保护 / Blocking data, history or private-input protection issue |

最低 505 个对齐价格 = 252 个收益回看 + 基值 + 252 个未来收益。但月末评估位置可能要求更多数据；CLI 只计数实际可用6M/12M窗口，不计算任何未来收益、模型、状态或结论。首选≥5年、强首选8–10+年；不因为不足10年而拒绝。
505 prices are necessary but may be insufficient after completed-month scheduling. The CLI counts eligible 126/252-session windows only. No realized performance or model validation is run.

“技术兼容”仅表示数据满足冻结入口结构和长度条件；不是来源真实性或研究有效性的保证。`fully_research_ready` 只有 READY 才为 true。
Technical compatibility is not provenance authentication or research validity. Only READY sets fully_research_ready to true.

## CLI and reusable loader / 命令与复用

```powershell
.\.venv\Scripts\python.exe -m research.real_data_check
.\.venv\Scripts\python.exe -m research.real_data_check --json
```

Exit 0 = READY or READY_WITH_WARNINGS; exit 2 = NOT_READY/input error. `--json` prints only the local quality/provenance report, not price rows. No files are exported. The reusable `research.real_data_loader.load_local_dataset()` returns `report` and an aligned in-memory `prices` matrix; NOT_READY returns prices=None. It does not invoke the existing validation runner.

自定义输入可使用 `--directory`、`--manifest`、`--tickers`、`--benchmark`；tickers 必须包含 benchmark。CLI要求目录及实际manifest位于本仓库的被忽略路径中，并检查没有已被Git跟踪的原始文件。Library调用方也应使用私有路径；它不会自动保存或发布任何内容。

## Git / Release protection / Git与发布保护

`research/private_data/`, descendants and `*.private.csv` are ignored. `.gitattributes` additionally marks them export-ignore for Git-generated source archives. Normal research reports and derived result CSVs remain eligible for Git.

忽略规则不能阻止 `git add -f`；不要强制添加原始文件，也不要把私有目录放入手动 ZIP、Release附件、public assets或文档。CLI会检查已跟踪文件但不会自动改写Git。仅经审查、许可允许的派生研究结果可公开，原始价格矩阵不得由研究脚本导出。
Do not force-add private data or include it in manual ZIPs, Release attachments, assets or documentation. Only reviewed, permitted derived research results may be public. Git protection does not govern arbitrary external packaging tools.

## Next-phase comparison plan / 下一阶段计划（本轮不运行）

待来源和就绪提示解决后，在每个 T 使用同样的过去信息，对比 Traditional Analytics、Monte Carlo Only、Evolance v1.1。组合包括等权33.33/33.33/33.34、明确配置的70/15/15集中组合，以及各单资产100%；本入口不把权重写入或改变冻结规则。
Later comparisons will use identical information at T for equal-weight, explicitly configured concentration and single-asset portfolios.

Evaluate 6M/12M directional hit rate, Neutral coverage, confidence groups, forward returns by direction, drawdowns by Transition, Primary State/Flag groups, and interpretation differences for similar MC directions. Preserve censoring, overlapping-window caveats and the frozen specification. No thresholds will be tuned from outcomes.

## Source-declared adjusted Close / 来源声明复权 Close

支持 Kaggle 风格 `aapl.us` / `aapl.us.txt`（大小写不敏感），映射为 AAPL，文件内容仍必须是逗号分隔 CSV。原始文件和 Close 列不会被重命名。
Kaggle-style `.us` and `.us.txt` filenames map to canonical tickers; contents must still be comma-separated CSV. Raw files and Close headers remain unchanged.

仅在 manifest 同时包含以下字段时，Close 才按 `source_adjusted_close` 接受：
Close is accepted as `source_adjusted_close` only with all of these manifest declarations:

```json
{
  "source": "Kaggle Huge Stock Market Dataset",
  "author": "Boris Marjanovic",
  "asset_class": "equity",
  "price_type": "source_adjusted_close",
  "source_adjusted_close_opt_in": true
}
```

保留其余必需 provenance 字段；可使用 `license` 记录来源声明的许可。此显式选择依据用户提供的来源文档，入口不联网认证许可或复权准确性。缺少来源/opt-in 的 source-adjusted 声明会阻断；没有此声明的普通 Close 继续显示原有警告。Adjusted Close 列仍优先。
Retain the other required provenance fields; `license` may record the source-declared license. This opt-in relies on user-provided documentation, not online authentication. Incomplete source-adjusted declarations block readiness; ordinary Close retains its warning. An explicit Adjusted Close column still takes priority.
