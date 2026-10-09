# Evolance research milestone / 研究里程碑

Evolance v1.1 Research Phase is frozen as a Git milestone. Stable product/UI code remains separate.
Evolance v1.1 研究阶段作为 Git 里程碑冻结；本目录不代表产品上线或预测优势。

- [v1 research / v1 研究](../docs/evolance_v1_research.md): original implementation and synthetic evidence in `evolance_results/`.
- [v1.1 frozen specification / 冻结规范](../docs/evolance_v1_1_frozen_spec.md), [machine-readable rules](../docs/evolance_v1_1_frozen_spec.json).
- [v1.1 synthetic research / 合成验证](../docs/evolance_v1_1_research.md): preserved in `evolance_v1_1_results/`.
- [Private input instructions / 私有数据入口](REAL_DATA_INPUT.md), [public manifest template](real_data_manifest.example.json).
- [Preregistered real-study method / 真实验证方法](../docs/evolance_v1_1_real_method.md).
- [Real historical report / 真实历史报告](../docs/evolance_v1_1_real_validation.md): derived evidence in `evolance_v1_1_real_results/`.

Real-study recommendation: **B — Productize as Interpretation / Decision-Support Layer, without predictive-superiority claims.**
真实研究建议：仅作为解释与决策辅助层产品化，不声称预测优势。

Frozen Spec SHA-256: `bea9d81702d4afe70a2d65d3fd1beb33c410eeefa0298cc2e5fe5d06e521e0b7`.

From the repository root / 从仓库根目录运行：

```powershell
python -m pytest -q
python -m research.real_data_check
python -m research.evolance_v1_1_real_validation
python -m research.evolance_v1_1_real_report
```

Real-data commands require separately acquired authorized local inputs; no raw data is distributed. Never stage `private_data/` or its actual manifest. Derived outputs contain metrics, classifications and outcomes, not raw price tables. Synthetic NPZ files hold reproducible simulated terminal returns. Test-result snapshots record their respective historical runs, not a promise that every snapshot has the latest test count.

真实数据须另行合法取得并放入被忽略的本地目录；不得提交原始数据或实际 manifest。派生输出只保存指标、分类和结果。各阶段测试记录保留原运行时间点的证据。Git attributes preserve research bytes to keep recorded hashes stable across Windows/Linux checkouts; do not tune frozen rules from outcomes.
