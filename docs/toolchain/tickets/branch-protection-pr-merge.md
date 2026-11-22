# 工单：合并流程 PR 化 + 服务端分支保护（branch-protection-pr-merge）

> **版本**：v1.0（2026-11-22）
> **规格**：[specs/branch-protection-pr-merge.md](../specs/branch-protection-pr-merge.md)
> **分支**：`task/branch-protection-pr-merge-<sid>`
> **状态**：进行中

## 工单

### T1 · `workflow_guard merge` 增加 PR 传输

- **验收**：新增 `--transport` / `--wait-timeout`；`pr` 传输依次完成推分支、`gh pr create`、轮询检查、`gh pr merge --merge --delete-branch`；失败给出可读错误。
- **状态**：进行中

### T2 · 自动选择传输

- **验收**：`auto` 在 GitHub 远端 + `gh` 可用时选 `pr`，否则 `direct`；`direct` 行为与现状一致。
- **状态**：进行中

### T3 · 测试

- **验收**：现有 34 项全绿；新增 fake `gh` 测试覆盖建 PR / 等检查 / 合并 / PR 已存在；`test_workflow_guard` 全绿。
- **状态**：进行中

### T4 · 文档同步

- **验收**：`docs/branch-management.md`（合并角色 + PR 流程）、`AGENTS.md` 硬性规约二、`docs/CI.md`（§十六分支保护行 + §十合并）、`engine/scripts/README.md` 同步。
- **状态**：待办

### T5 · 评审与合并前检查单

- **验收**：`docs/toolchain/reviews/branch-protection-pr-merge-review.md` 双轴无 P0/P1；`unittest` / `validate.py` / `gate` / `coverage` / `cleanup` 全绿。
- **状态**：待办

### T6 · 启用分支保护 + 端到端验证

- **验收**：仓库 `main` 保护启用；直推被拒；任务 PR 经 `merge` 合并成功。
- **状态**：待办
