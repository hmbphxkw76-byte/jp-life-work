# 工单：词库近义「已裁定保留」清单（near-exempt）

> 任务 slug：`vocab-near-exemptions`
> 版本：v1.0（2026-11-23）
> 规格：[specs/vocab-near-exemptions.md](../specs/vocab-near-exemptions.md)
> 合并顺序：S3 → S4 → S5 → S6

| # | 范围 | 依赖 | 验证 |
|---|---|---|---|
| S1 | 规格 `docs/toolchain/specs/vocab-near-exemptions.md` | — | 动机/接口/验收齐备 |
| S2 | 工单 `docs/toolchain/tickets/vocab-near-exemptions.md` | S1 | 4 列可追溯表格 |
| S3 | 测试 `engine/tests/test_vocab_near_check.py`（先红） | S2 | 新增 4 项失败 |
| S4 | 实现 `vocab_near_check.py` + `config/near-dup-exemptions.json` | S3 | 测试转绿、工具退出码 0 |
| S5 | 评审 `docs/toolchain/reviews/vocab-near-exemptions-review.md` | S4 | 双轴、每轴 ≥2 问 |
| S6 | 检查单（`engine/scripts/README.md` §十二） | S5 | 逐项核对 |

**回滚点**：`git revert <merge-commit>`；删除新增配置即可恢复旧行为。
