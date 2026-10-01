# Finance Mini Lab v0.1

Program One 的 Python/Finance 基础项目。从复利计算开始，后续逐步扩展到收益率计算、Sharpe Ratio、金融数据分析、加密资产和投资组合优化。

## 当前功能：Compound Interest Calculator

使用公式 `FV = PV × (1 + r)^n` 计算未来价值：

- `principal`（PV）：本金，不能为负。
- `annual_rate`（r）：年化收益率，使用小数形式，例如 `0.08` 表示 8%，必须大于 `-1`。
- `years`（n）：投资年限，不能为负。

假设年化收益率固定、每年复利，不追加投入或取款，不计税费和通胀。允许大于 -100% 的负收益率。当前只做上述三条基础校验，函数接收数值参数。

## 运行方法

命令行版本仅使用 Python 标准库。在项目根目录运行：

```powershell
python app.py
```

如果 Windows 使用 Python 启动器，也可以运行 `py app.py`。若命令无法识别，请先安装 Python 并配置 PATH，或使用 Python 解释器的完整路径运行。

Milestone 1.1 支持交互输入。运行后依次输入本金、年化收益率百分比和投资年限。例如分别输入 `10000`、`8`、`10`，每次按回车。收益率输入 `8` 表示 8%，程序自动转换为 `0.08` 传给核心函数，不需要输入 `%` 符号。标题和结果示例：

```text
## Finance Mini Lab v0.1

Initial Investment: ¥10,000.00
Annual Return: 8.00%
Investment Period: 10 years
Future Value: ¥21,589.25
```

非数字、负本金、收益率不大于 -100%、负年限都会显示友好错误提示并结束本次运行，请重新运行后输入。也会拦截非有限数值（nan、inf）和计算溢出。按 Ctrl+C 或结束输入会显示取消提示。函数保留计算精度，金额显示时使用千位分隔符和两位小数。核心函数仍是 `calculate_future_value()`，入口通过导入别名 `calculate_compound_interest` 复用它，不重复实现公式。命令行入口仅依赖 Python 标准库，网页入口另需 Streamlit。

## 项目结构

```text
Finance-Mini-Lab/
├─ README.md
├─ requirements.txt
├─ app.py
├─ streamlit_app.py
├─ .gitignore
├─ src/
│  └─ compound_interest.py
├─ tests/
│  └─ test_streamlit_app.py
├─ assets/
└─ docs/
   └─ project_log.md
```

`app.py` 是程序入口，`src/compound_interest.py` 存放可复用的金融计算函数。`streamlit_app.py` 是网页入口，`tests/test_streamlit_app.py` 验证网页交互和图表数据。`assets/` 预留给资源文件。`docs/project_log.md` 记录施工过程。

## Milestone 1.2：Streamlit 网页界面

建议使用 Python 3.12。在项目根目录的 PowerShell 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

启动后打开终端显示的 Local URL，通常为 http://localhost:8501。如果没有自动打开浏览器，可以将该地址复制到浏览器。按 Ctrl+C 停止服务。Windows 若使用 `py` 启动器，可将第一行替换为 `py -3 -m venv .venv`；若都无法识别，请使用已安装 Python 的完整路径。

网页输入本金、年化收益率百分比和整数年限，然后点击 **Calculate**。默认参数是 10000 / 8 / 10，Future Value 应为 ¥21,589.25。年限支持 0–1000 年，上限用于限制图表数据量。数字输入框限制非数字输入；空值、越界值请按控件提示修正，提交后的负本金、收益率不大于 -100% 或负年限会显示错误信息。修正后可再次点击 Calculate。

结果区显示 Initial Investment、Annual Return、Investment Period 和 Future Value。Portfolio Growth Over Time 图表横轴为 Year、纵轴为 Portfolio Value (¥)：对第 0 年到最终年逐年调用原 calculate_future_value 函数，0 年从本金开始，未对中间数据舍入。0 年期限用单个散点显示本金。收益率为 0 时为水平线，负收益率时呈下降趋势。

直接依赖只有 `streamlit>=1.50,<2`。图表使用 Python 字典及 Streamlit 内置图表 API，没有直接使用 pandas，所以不单独声明 pandas；安装 Streamlit 时会自动安装它所需的间接依赖。

运行网页自动化测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

参考：[Streamlit line_chart 文档](https://docs.streamlit.io/develop/api-reference/charts/st.line_chart)。

## Milestone 1.2.1：UI Polish

本次仅优化界面与可读性，未修改核心公式、计算结果逻辑或新增金融功能。默认参数继续为 10000 / 8 / 10。

- 保留 Finance Mini Lab v0.1 标题，增加简短英文副标题：Estimate how an investment grows through annual compounding.
- 输入标签统一为 Principal / 本金 (¥)、Annual Return / 年化收益率 (%)、Investment Period / 投资年限 (Years)。
- 结果使用两列带边框的原生指标卡；金额统一使用 ¥、千分位和两位小数，收益率保留两位小数。
- 图表标题改为 Portfolio Growth Over Time，明确标注 Year 与 Portfolio Value (¥)，使用统一的青绿色和 360 像素高度，保留 Year 0 起点及原有逐年数据。
- 使用 Streamlit 原生组件，不增加 CSS 或第三方依赖，启动方式保持不变。

## Milestone 1.3：Content Enrichment + Financial Insights

在保留输入区与核心复利公式的基础上，增加以下分析内容：

- Calculation Results：初始本金、未来价值、累计收益、总收益率、投资年限和年化收益率。累计收益 = 未来价值 − 初始本金；总收益率 = 累计收益 ÷ 初始本金 × 100%。本金为 0 时，总收益率显示 N/A。
- Year-by-Year Table：从 Year 0 到最终年，显示 Year、Portfolio Value、Profit vs Initial；金额带 ¥、千分位及两位小数。
- Growth Breakdown：柱状图对比 Initial Principal 和 Compound Growth；收益为负时明确显示亏损。
- Scenario Comparison：在相同本金、年限下比较 4%、当前输入收益率和 12%，去除重复收益率。所有曲线均逐年调用原核心函数；超出计算范围的情景会提示并省略，不影响当前结果。
- Rule of 72：只在收益率为正时展示 72 ÷ 年化收益率百分数的近似翻倍年限，并明确说明不是精确结果，极端收益率下偏差较大。
- Financial Insight：简短描述资产倍数、累计收益及近似翻倍年限，不提供投资建议。零本金不显示资产倍数，也不声称资产能翻倍。
- 页面底部的 Assumptions / 假设说明列出固定年化收益率、每年复利、无额外投入或取款、不计税费通胀手续费，以及教育演示用途。

逐年明细、收益构成和情景对比使用标签页组织，不新增第三方依赖。输入 10000 / 8 / 10 时，未来价值为 ¥21,589.25，累计收益为 ¥11,589.25，总收益率为 115.89%，Rule of 72 估算为 9.00 年。实际精确翻倍时间不由本模块计算。

测试命令不变，目前包含 12 个测试方法，覆盖收益汇总、逐年数据、收益构成、Rule of 72、情景去重、零本金及非正收益率等场景。
