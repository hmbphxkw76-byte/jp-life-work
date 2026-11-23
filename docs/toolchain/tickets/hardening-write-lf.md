# 工单：工具写回换行口径硬化（write-lf）

> 任务 slug：`hardening-write-lf`
> 版本：v1.0（2026-11-23）
> 规格：[specs/hardening-write-lf.md](../specs/hardening-write-lf.md)
> 合并顺序：S3 → S4 → S5 → S6（S1/S2 已完成）

| # | 范围 | 依赖 | 验证 |
|---|---|---|---|
| S1 | 规格 `docs/toolchain/specs/hardening-write-lf.md` | — | 动机/接口/验收齐备，≤1 页 |
| S2 | 工单 `docs/toolchain/tickets/hardening-write-lf.md` | S1 | 4 列可追溯表格 |
| S3 | 测试 `engine/tests/test_write_lf.py`（先红） | S2 | 新测试在修复前失败 |
| S4 | 实现 `generate_registry.py` / `sync_vocab.py` / `test_arch_guard.py` | S3 | 新测试转绿，`validate.py` 通过 |
| S5 | 评审 `docs/toolchain/reviews/hardening-write-lf-review.md` | S4 | 双轴并行、每轴 ≥2 问、有签字 |
| S6 | 检查单（`engine/scripts/README.md` 7 项） | S5 | 逐项核对通过 |

**回滚点**：`git revert <merge-commit>`；无数据迁移、无外部副作用。
