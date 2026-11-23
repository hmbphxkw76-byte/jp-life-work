# CI 自动化 PR 免审批自动合并 · 双轴评审（Standards / Spec）

> **工单**：[tickets/ci-auto-merge-pr.md](../tickets/ci-auto-merge-pr.md)
> **规格**：[specs/ci-auto-merge-pr.md](../specs/ci-auto-merge-pr.md)
> **分支**：`task/ci-auto-merge-pr-d8877c46`
> **评审日期**：2026-11-23
> **评审口径**：Standards（仓库规范符合性）+ Spec（验收标准覆盖度）
>
> ⚠️ **已废弃（2026-11-23）**：本评审对应的 `--auto` 方案经真跑验证不成立
> （bot / `GITHUB_TOKEN` 创建的 PR 不触发 `pull_request` 工作流，`--auto` 永卡 `BLOCKED`）。
> 已由 [ci-auto-merge-inwork-gate](../reviews/ci-auto-merge-inwork-gate-review.md)（门禁内移）取代。

## 一、Standards 轴（规范符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 适用范围 | 通过 | 变更位于 `.github/workflows/`、`.github/actions/`、`engine/tests/`、`docs/`，属工具链域 |
| 退出码契约 | 通过 | 未新增 Python 工具；复合动作失败以 `::error::` 输出并退出 1 |
| 单一事实源 | 通过 | 自动合并逻辑集中于 `.github/actions/auto-merge-pr/action.yml`；6 条工作流仅接线，无重复实现 |
| 安全底线 | 通过 | 分支保护必需检查 `validate` / `audit` 未变；`required_approving_review_count=0`；CI 未通过的 PR 不合并 |
| 权限最小化 | 通过 | 工作流仅既有 `contents: write` + `pull-requests: write`；未引入 `pull_request_target` |
| 跨平台 | 通过 | 复合动作 `shell: bash`，工作流引用一律正斜杠；`test_platform_guard` 通过 |
| worktree 隔离 | 通过 | 全程在 `.worktrees/ci-auto-merge-pr/` 工作；未直推 main |
| 静态检查 | 通过 | `ruff check engine` 0；`mypy` 63 文件 0 |
| 测试同步 | 通过 | 新增 `test_ci_auto_merge.py`（5 项，先红后绿）；`unittest` 1177 项 |

## 二、Spec 轴（验收标准映射）

| 验收 | 结论 | 证据 |
|---|---|---|
| 1. 8 个 PR 点全部经复合动作，无残留直接 `gh pr create` | 覆盖 | `scheduled-maintenance` 2 / `pipeline-orchestrator` 2 / `html-sync` 1 / `info-quality` 1 / `audit-sampling` 1 / `scheduled-report-tasks` 1；`grep "gh pr create" .github/workflows/` 无命中 |
| 2. `allow_auto_merge=true` 且分支保护不变 | 覆盖 | `gh api ... --jq .allow_auto_merge` = `true`；保护 `contexts=[validate,audit]`、`required_approving_review_count=0`、`enforce_admins=true` |
| 3. 守卫测试断言接线 | 覆盖 | `test_ci_auto_merge.py` 5 项全绿（实现前 3 失败 2 错误） |
| 4. 全量回归 | 覆盖 | `validate.py` 0；`audit_pipeline --gate` 0；`ruff` 0；`mypy` 0；`unittest` 1177 项全绿；`coverage_gate` 88.7% ≥ 80% |
| 5. 端到端：CI 通过后自动合入 | 已验证 | PR #11（空提交）：`validate` / `audit` 全部 SUCCESS 后自动合入，`mergedAt=2026-11-22T23:24:33Z`，merge commit `2ecb68e725d47610f96fc83f3b144fd57a8805cc`；远端分支由 `delete_branch_on_merge` 自动删除 |

## 三、实现要点

- 复合动作 `.github/actions/auto-merge-pr`：输入 `branch` / `title` / `body` / `token`；
  定位或创建 `main ← branch` 的开放 PR → `gh pr merge <num> --auto --merge`；
  `branch` 为空（本轮无变更）幂等跳过；失败 `::error::` 退出 1。
- 6 条工作流的提交步骤 `echo "branch=$BRANCH" >> "$GITHUB_OUTPUT"`，紧随一步 `uses` 复合动作；
  提交步骤与自动合并步骤的 `if:` 条件保持一致（成功路径 / `always()`）。
- 仓库设置启用 `allow_auto_merge`（仅「允许」，不强制）；仅自动化 PR 显式 `--auto`。

## 四、风险与遗留

1. **仓库级开关**：`allow_auto_merge` 允许任意 PR 启用自动合并，但仅自动化 PR 显式调用；
   人工任务 PR 仍走 `workflow_guard merge`（等检查 → `gh pr merge --merge`），不受影响。
2. **检查名耦合**：分支保护要求 `validate` / `audit`；若 job 改名需同步仓库保护。
3. **冲突处理**：PR 冲突时 `--auto` 失败即报错，需人工处理，不覆盖、不绕过。
4. **自动合并时机**：依赖必需检查通过；若检查失败，PR 保持打开并保留 auto-merge，修复后自动合入。
