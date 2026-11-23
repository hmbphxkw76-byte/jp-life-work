# 工单：事实卡片 corroboration 语义（single-source）

> 任务 slug：`fact-card-corroboration`
> 版本：v1.0（2026-11-23）
> 规格：[specs/fact-card-corroboration.md](../specs/fact-card-corroboration.md)
> 合并顺序：S3 → S4 → S5 → S6

| # | 范围 | 依赖 | 验证 |
|---|---|---|---|
| S1 | 规格 `docs/toolchain/specs/fact-card-corroboration.md` | — | 动机/接口/验收齐备 |
| S2 | 工单 `docs/toolchain/tickets/fact-card-corroboration.md` | S1 | 4 列可追溯表格 |
| S3 | 测试 `engine/tests/test_tools.py::TestFactCardCheck`（先红） | S2 | 新测试失败 |
| S4 | 实现 `fact_card_check.py` + 标准文档 + 卡片数据 | S3 | 新测试转绿、`validate.py` 通过 |
| S5 | 评审 `docs/toolchain/reviews/fact-card-corroboration-review.md` | S4 | 双轴、每轴 ≥2 问、有签字 |
| S6 | 检查单（`engine/scripts/README.md` §十二） | S5 | 逐项核对 |

**回滚点**：`git revert <merge-commit>`；卡片数据变更可逐行还原。
