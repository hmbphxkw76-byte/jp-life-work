# 工单：md2html 写回换行口径硬化（eol-lf）

> 任务 slug：`fix-md2html-eol`
> 版本：v1.0（2026-11-23）
> 规格：[specs/fix-md2html-eol.md](../specs/fix-md2html-eol.md)
> 合并顺序：S3 → S4 → S5 → S6

| # | 范围 | 依赖 | 验证 |
|---|---|---|---|
| S1 | 规格 `docs/toolchain/specs/fix-md2html-eol.md` | — | 动机/接口/验收齐备 |
| S2 | 工单 `docs/toolchain/tickets/fix-md2html-eol.md` | S1 | 4 列可追溯表格 |
| S3 | 测试 `engine/tests/test_write_lf.py`（先红） | S2 | 新测试失败 |
| S4 | 实现 `engine/tools/md2html.py` | S3 | 新测试转绿、`validate.py` 通过 |
| S5 | 评审 `docs/toolchain/reviews/fix-md2html-eol-review.md` | S4 | 双轴、每轴 ≥2 问 |
| S6 | 检查单（`engine/scripts/README.md` §十二） | S5 | 逐项核对 |

**回滚点**：`git revert <merge-commit>`。
