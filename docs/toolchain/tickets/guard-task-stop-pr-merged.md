# 工单：task stop 信任 merged 登记（guard-task-stop-pr-merged）

> **版本**：v1.0（2026-11-22）
> **分支**：`task/guard-task-stop-pr-merged-<sid>`
> **状态**：已完成

## 背景

合并 PR 化后，任务经 PR 合并时远端分支由 `delete_branch_on_merge` 自动删除，且本地 `base`
引用可能滞后；`task stop` 的祖先检查会误报「尚未合入」，迫使使用 `--force`。

## 工单

### T1 · task stop 信任已登记 merged

- **验收**：`task stop` 对 `status=merged` 且含 `merged_sha` 的任务跳过祖先检查；其余情况仍校验。
- **状态**：已完成

### T2 · 测试

- **验收**：新增 `test_stop_recorded_merged_task_without_ancestor`；`test_workflow_guard` 39 项全绿。
- **状态**：已完成

### T3 · 文档数字同步

- **验收**：`docs/CI.md` / `engine/tools/README.md` / `docs/README.md` / `cross-domain-expert-roles.md` 测试数 1172。
- **状态**：已完成

## 合并前检查单（S6）

- [x] `python -m unittest discover -s engine/tests` 全绿（1172 项）
- [x] `python engine/tools/validate.py` 退出码 ∈ {0,2}
- [x] 评审报告存在且双轴无 P0/P1
- [x] `ruff` / `mypy` 0
- [x] `cleanup_workspace.py --check` 零残留
