# 工单：写回换行口径全量治理（write-eol-all）

> 任务 slug：`fix-all-write-eol-guard`
> 版本：v1.0（2026-11-24）
> 规格：[specs/fix-all-write-eol-guard.md](../specs/fix-all-write-eol-guard.md)
> 合并顺序：S3 → S4 → S5 → S6

| # | 范围 | 依赖 | 验证 |
|---|---|---|---|
| S1 | 规格 `docs/toolchain/specs/fix-all-write-eol-guard.md` | — | 动机/接口/验收齐备 |
| S2 | 工单 `docs/toolchain/tickets/fix-all-write-eol-guard.md` | S1 | 4 列可追溯表格 |
| S3 | 守卫测试 `engine/tests/test_write_eol_guard.py`（先红 62 处） | S2 | 测试失败并列出 62 处 |
| S4 | 修复 62 处写点（24 个文件） | S3 | 守卫转绿、`compileall`/`ruff` 通过 |
| S5 | 评审 `docs/toolchain/reviews/fix-all-write-eol-guard-review.md` | S4 | 双轴、每轴 ≥2 问 |
| S6 | 检查单（`engine/scripts/README.md` §十二） | S5 | 逐项核对 |

**回滚点**：`git revert <merge-commit>`；纯参数追加，无数据迁移。
