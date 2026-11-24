# 工单：反例扫描「单源」判定收敛（counterexample-single-source）

> 任务 slug：`fix-counterexample-single-source`
> 版本：v1.0（2026-11-24）
> 规格：[specs/fix-counterexample-single-source.md](../specs/fix-counterexample-single-source.md)
> 合并顺序：S3 → S4 → S5 → S6

| # | 范围 | 依赖 | 验证 |
|---|---|---|---|
| S1 | 规格 `docs/toolchain/specs/fix-counterexample-single-source.md` | — | 动机含逐条核查数据 / 规则 / 验收齐备 |
| S2 | 工单 `docs/toolchain/tickets/fix-counterexample-single-source.md` | S1 | 4 列可追溯表格 |
| S3 | 测试 `engine/tests/test_counterexample_scan.py` 增补排除规则用例 | S2 | 新用例先红 |
| S4 | `engine/tools/counterexample_scan.py` 规则实现 | S3 | 新用例转绿；既有用例不回归 |
| S5 | 裁定清单追加 + 证据文档 + 评审 `docs/toolchain/reviews/fix-counterexample-single-source-review.md` | S4 | 残余条目逐条可查 |
| S6 | 检查单（`engine/scripts/README.md` §十二）+ 计数同步 | S5 | 逐项核对 |

**回滚点**：`git revert <merge-commit>`；只影响扫描候选集与裁定清单，不动报告内容。
