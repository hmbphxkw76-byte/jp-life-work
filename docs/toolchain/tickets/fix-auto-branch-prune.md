# 工单：自动化已合并分支显式清理（auto-branch-prune）

> 任务 slug：`fix-auto-branch-prune`
> 版本：v1.0（2026-11-24）
> 规格：[specs/fix-auto-branch-prune.md](../specs/fix-auto-branch-prune.md)
> 合并顺序：S3 → S4 → S5 → S6

| # | 范围 | 依赖 | 验证 |
|---|---|---|---|
| S1 | 规格 `docs/toolchain/specs/fix-auto-branch-prune.md` | — | 动机（含 3 例实证）/接口/验收齐备 |
| S2 | 工单 `docs/toolchain/tickets/fix-auto-branch-prune.md` | S1 | 4 列可追溯表格 |
| S3 | 守卫测试 `engine/tests/test_ci_auto_merge.py` 增删分支断言 | S2 | 新守卫先红（旧动作无删除逻辑） |
| S4 | `.github/actions/auto-merge-pr/action.yml` 追加显式删分支 + 失败告警 | S3 | YAML 可解析；守卫转绿 |
| S5 | 评审 `docs/toolchain/reviews/fix-auto-branch-prune-review.md` | S4 | 双轴、残余风险写明 |
| S6 | 检查单（`engine/scripts/README.md` §十二）+ 文档计数同步 | S5 | 逐项核对 |

**附带清理**：删除远端残留 3 个 `auto/*-*`（`gh api -X DELETE .../git/refs/heads/<branch>`）。

**回滚点**：`git revert <merge-commit>`；机制改动仅影响自动化合并后的分支生命周期，不影响内容与生成物。
