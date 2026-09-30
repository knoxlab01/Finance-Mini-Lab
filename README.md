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

结果区显示 Initial Investment、Annual Return、Investment Period 和 Future Value。Growth Chart 横轴为 Year、纵轴为 Portfolio Value：对第 0 年到最终年逐年调用原 calculate_future_value 函数，0 年从本金开始，未对中间数据舍入。0 年期限用单个散点显示本金。收益率为 0 时为水平线，负收益率时呈下降趋势。

直接依赖只有 `streamlit>=1.50,<2`。图表使用 Python 字典及 Streamlit 内置图表 API，没有直接使用 pandas，所以不单独声明 pandas；安装 Streamlit 时会自动安装它所需的间接依赖。

运行网页自动化测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

参考：[Streamlit line_chart 文档](https://docs.streamlit.io/develop/api-reference/charts/st.line_chart)。
