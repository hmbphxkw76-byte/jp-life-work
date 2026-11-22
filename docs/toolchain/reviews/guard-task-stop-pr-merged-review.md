# task stop 信任 merged 登记 · 双轴评审（Standards / Spec）

> **工单**：[guard-task-stop-pr-merged](../tickets/guard-task-stop-pr-merged.md)
> **分支**：`task/guard-task-stop-pr-merged-<sid>`
> **评审日期**：2026-11-22
> **评审口径**：Standards + Spec

## 一、Standards 轴

| 检查项 | 结论 | 证据 |
|---|---|---|
| 适用范围 | 通过 | `engine/scripts/workflow_guard.py` 工具链域 |
| 退出码契约 | 通过 | 未新增工具；`task stop` 语义不变 |
| 跨平台 | 通过 | 无新增平台相关代码；`test_platform_guard` 通过 |
| worktree 隔离 | 通过 | 全程在 `.worktrees/guard-task-stop-pr-merged/` 工作 |
| 测试同步 | 通过 | 新增 1 项；`test_workflow_guard` 39 项全绿 |
| 文档↔数字同步 | 通过 | 四处测试数同步 1172；`test_arch_guard` 全绿 |
| 静态检查 | 通过 | `ruff` 0；`mypy` 0 |

## 二、Spec 轴

| 验收 | 结论 | 证据 |
|---|---|---|
| 已登记 merged 的任务 stop 跳过祖先检查 | 覆盖 | `cmd_task_stop`：`recorded_merged = status==merged && merged_sha` |
| 其余情况仍校验 | 覆盖 | 未登记 merged 时保留 `merge-base --is-ancestor` 检查 |
| 测试 | 覆盖 | `test_stop_recorded_merged_task_without_ancestor`（构造分支非祖先 + 登记 merged → stop 成功） |

## 三、风险与遗留

- 信任 `merged_sha` 登记意味着若登记被人为篡改为未真正合并，`stop` 会跳过检查；登记由
  `merge` 在 PR 合并成功后写入，篡改需人为修改 `.git/workflow-guard/tasks.json`，风险可接受。
