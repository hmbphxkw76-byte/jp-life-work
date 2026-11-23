# 修复 merge 等待竞态 · 双轴评审（Standards / Spec）

> **工单**：[tickets/fix-merge-wait-checks.md](../tickets/fix-merge-wait-checks.md)
> **规格**：[specs/fix-merge-wait-checks.md](../specs/fix-merge-wait-checks.md)
> **分支**：`task/fix-merge-wait-checks-d8877c46`
> **评审日期**：2026-11-23
> **评审口径**：Standards（仓库规范符合性）+ Spec（验收标准覆盖度）

## 一、Standards 轴（规范符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 适用范围 | 通过 | 变更位于 `engine/scripts/`、`engine/tests/`、`docs/` |
| 退出码契约 | 通过 | 未新增工具；失败/超时仍报错、不合并 |
| 单一事实源 | 通过 | 检查名集中于 `PR_REQUIRED_CHECKS` 常量，注释指向 `docs/CI.md` 门禁定义 |
| 安全底线 | 通过 | 恢复「等 `validate` / `audit` 通过再合并」语义，堵住方案 B 引入的竞态 |
| 跨平台 | 通过 | 仅用 `gh pr view --json`，无平台相关代码 |
| worktree 隔离 | 通过 | 全程 `.worktrees/fix-merge-wait-checks/`；未直推 main |
| 静态检查 | 通过 | `ruff` / `mypy` |
| 测试同步 | 通过 | `test_workflow_guard.py` 39 → 43 项（含 4 项等待逻辑回归） |

## 二、Spec 轴（验收标准映射）

| 验收 | 结论 | 证据 |
|---|---|---|
| 1. 空 rollup + `CLEAN` 不立即返回 | 覆盖 | `test_empty_rollup_clean_waits`（timeout=0 → GuardError） |
| 2. 缺任一指定检查则等待 | 覆盖 | `test_missing_required_check_waits` |
| 3. 两检查 SUCCESS 才返回 | 覆盖 | `test_required_checks_success_returns` |
| 4. 指定检查 FAILURE 报错 | 覆盖 | `test_required_check_failure_blocks` |
| 5. 全量回归 | 覆盖 | `unittest` 1183；`validate` / `gate` / `ruff` / `mypy` |

## 三、实现要点

- 新增 `PR_REQUIRED_CHECKS = ("validate", "audit")` 与 `_CHECK_PASSED` / `_CHECK_FAILED` 常量。
- `_gh_pr_wait_checks` 改为按检查名判定：任一失败即报错；`validate` / `audit`
  必须全部出现且通过才返回；缺失/未完成视为 pending，超时（`--wait-timeout`）报错。
- `FAKE_GH` 测试替身改为返回**带名**检查，贴合真实 `gh pr view` 输出。

## 四、风险与遗留

1. 检查名硬编码：若 CI 改名（`validate` / `audit`）需同步常量与分支保护口径。
2. 若某类 PR 始终不触发这两个检查，将等待至超时（预期行为：暴露异常，而非静默合并）。
3. 本修复不改变方案 B 的门禁内移设计；仅恢复 `workflow_guard` 侧的等待语义。
