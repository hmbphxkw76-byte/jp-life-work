# 工单：CI 自动化 PR 免审批自动合并（ci-auto-merge-pr）

> **版本**：v1.0（2026-11-23）
> **规格**：[specs/ci-auto-merge-pr.md](../specs/ci-auto-merge-pr.md)
> **分支**：`task/ci-auto-merge-pr-d8877c46`
> **状态**：已完成

## 工单

### T1 · 新增复合动作 `auto-merge-pr`

- **验收**：`.github/actions/auto-merge-pr/action.yml` 存在；输入 `branch` / `title` / `body` / `token`；
  行为为「定位或创建 PR → `gh pr merge --auto --merge`」；`branch` 为空时幂等跳过；失败退出 1。
- **状态**：已完成

### T2 · 6 条工作流 8 个 PR 点接线

- **验收**：`scheduled-maintenance`（2）、`html-sync`（1）、`info-quality`（1）、
  `audit-sampling`（1）、`pipeline-orchestrator`（2）、`scheduled-report-tasks`（1）
  的提交步骤输出 `branch` 并调用复合动作；仓库内不再有直接 `gh pr create`。
- **状态**：已完成

### T3 · 启用仓库自动合并

- **验收**：`gh api repos/... --jq .allow_auto_merge` 为 `true`；`main` 分支保护必需检查仍为
  `validate` / `audit`。
- **状态**：已完成（`allow_auto_merge=true`；保护 `contexts=[validate,audit]` / 评审数 0 / enforce_admins）

### T4 · 守卫测试

- **验收**：新增 `engine/tests/test_ci_auto_merge.py`，断言复合动作存在、8 处接线到位、
  无残留直接 `gh pr create`；`unittest` 全绿。
- **状态**：已完成（5 项，先红后绿）

### T5 · 文档同步

- **验收**：`docs/CI.md`（工作流说明 + §十 + §十六 + 版本记录）、`docs/branch-management.md`、
  `engine/scripts/README.md`（§六）与实现一致。
- **状态**：已完成（另同步 `docs/README.md` / `cross-domain-expert-roles.md` / `engine/tools/README.md` 计数）

### T6 · 双轴评审与合并前检查单

- **验收**：`docs/toolchain/reviews/ci-auto-merge-pr-review.md` 双轴无 P0/P1；
  `unittest` / `validate.py` / `gate` / `coverage` / `cleanup` 全绿。
- **状态**：已完成

### T7 · 端到端验证

- **验收**：真实 PR 在 `validate` + `audit` 通过后自动合入 `main`（记录 PR 号与合并提交）。
- **状态**：已完成（PR #11 空提交；`mergedAt=2026-11-22T23:24:33Z`，merge commit `2ecb68e`）
