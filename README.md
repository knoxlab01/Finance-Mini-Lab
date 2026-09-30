# Finance Mini Lab v0.1

Program One 的 Python/Finance 基础项目。从复利计算开始，后续逐步扩展到收益率计算、Sharpe Ratio、金融数据分析、加密资产和投资组合优化。

## 当前功能：Compound Interest Calculator

使用公式 `FV = PV × (1 + r)^n` 计算未来价值：

- `principal`（PV）：本金，不能为负。
- `annual_rate`（r）：年化收益率，使用小数形式，例如 `0.08` 表示 8%，必须大于 `-1`。
- `years`（n）：投资年限，不能为负。

假设年化收益率固定、每年复利，不追加投入或取款，不计税费和通胀。允许大于 -100% 的负收益率。当前只做上述三条基础校验，函数接收数值参数。

## 运行方法

需要 Python 3，无第三方依赖，无需执行 pip 安装。在项目根目录运行：

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

非数字、负本金、收益率不大于 -100%、负年限都会显示友好错误提示并结束本次运行，请重新运行后输入。也会拦截非有限数值（nan、inf）和计算溢出。按 Ctrl+C 或结束输入会显示取消提示。函数保留计算精度，金额显示时使用千位分隔符和两位小数。核心函数仍是 `calculate_future_value()`，入口通过导入别名 `calculate_compound_interest` 复用它，不重复实现公式。当前仅依赖 Python 标准库。

## 项目结构

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

`app.py` 是程序入口，`src/compound_interest.py` 存放可复用的金融计算函数。`tests/` 和 `assets/` 暂为空，预留给测试与资源文件。`docs/project_log.md` 记录施工过程。
