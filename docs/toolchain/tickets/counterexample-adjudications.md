# 工单：反例扫描裁定清单（ce-adjudications）

> 任务 slug：`counterexample-adjudications`
> 版本：v1.0（2026-11-23）
> 规格：[specs/counterexample-adjudications.md](../specs/counterexample-adjudications.md)
> 合并顺序：S3 → S4 → S5 → S6

| # | 范围 | 依赖 | 验证 |
|---|---|---|---|
| S1 | 规格 `docs/toolchain/specs/counterexample-adjudications.md` | — | 动机/接口/验收齐备 |
| S2 | 工单 `docs/toolchain/tickets/counterexample-adjudications.md` | S1 | 4 列可追溯表格 |
| S3 | 测试 `engine/tests/test_counterexample_scan.py`（先红） | S2 | 新增用例失败 |
| S4 | 实现 `counterexample_scan.py` + `config/counterexample-adjudications.json` | S3 | 测试转绿 |
| S5 | 评审 `docs/toolchain/reviews/counterexample-adjudications-review.md` | S4 | 双轴、每轴 ≥2 问 |
| S6 | 检查单（`engine/scripts/README.md` §十二） | S5 | 逐项核对 |

**回滚点**：`git revert <merge-commit>`；删除新增配置即可恢复旧行为。
