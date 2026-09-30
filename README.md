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

当前使用固定参数：本金 `10000`、年化收益率 `0.08`、投资年限 `10`。预期输出：

```text
21589.25
```

函数保留计算精度，显示结果时才保留两位小数。下一步加入用户输入。

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
