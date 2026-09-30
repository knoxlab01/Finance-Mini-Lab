# 项目日志

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
