# 合并 PR 化 + main 分支保护 · 双轴评审（Standards / Spec）

> **工单**：[branch-protection-pr-merge](../tickets/branch-protection-pr-merge.md)
> **规格**：[branch-protection-pr-merge](../specs/branch-protection-pr-merge.md)
> **分支**：`task/branch-protection-pr-merge-<sid>`
> **评审日期**：2026-11-22
> **评审口径**：Standards（仓库规范符合性）+ Spec（验收标准覆盖度）

## 一、Standards 轴（规范符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 适用范围 | 通过 | 变更位于 `engine/scripts/workflow_guard.py`、`engine/tests/test_workflow_guard.py`、`.github/` 配套与 `docs/`，属工具链域 |
| 退出码契约 | 通过 | 未新增工具；`workflow_guard` 保持 0/1/2 语义（`validate.py` 失败阻断） |
| 单一事实源 | 通过 | PR 传输逻辑集中于 `workflow_guard.py`；`docs/branch-management.md` §3.1 为分支保护唯一说明 |
| 跨平台 | 通过 | `_gh` 用 `shlex.split(..., posix=(os.name != "nt"))` 保留 Windows 反斜杠路径；`test_platform_guard` 通过 |
| worktree 隔离 | 通过 | 全程在 `.worktrees/branch-protection-pr-merge/` 工作；未直推 main |
| 工具 / 测试登记 | 通过 | 未新增工具（50）；`docs/CI.md` / `engine/tools/README.md` / `docs/README.md` / `cross-domain-expert-roles.md` 测试数同步 1171 |
| 静态检查 | 通过 | `ruff check` 0；`mypy engine/scripts/workflow_guard.py` 0 |
| 测试同步 | 通过 | 新增 4 项 PR 传输测试（fake `gh`）；`test_workflow_guard` 38 项全绿 |

## 二、Spec 轴（验收标准映射）

| 验收 | 结论 | 证据 |
|---|---|---|
| 1. `merge --transport pr` 走推分支→建 PR→等检查→合并 | 覆盖 | `_merge_via_pr` + `_gh_pr_create/_gh_pr_wait_checks/_gh_pr_merge`；`TestPRTransport.test_merge_via_pr_happy` |
| 2. auto 在 GitHub 选 pr、本地裸 origin 选 direct | 覆盖 | `_resolve_transport`；`test_transport_auto_local_origin_is_direct`（未触碰 gh） |
| 3. 现有测试全绿 + 新增 PR 传输测试 | 覆盖 | 34 项旧测试 + 4 项新测试全绿；含 PR 已存在复用、检查失败阻断 |
| 4. 全量回归 | 覆盖 | `unittest` 1171 项全绿；`validate.py` 0；`audit_pipeline --gate` 通过；`ruff` / `mypy` 0 |
| 5. 分支保护启用后直推被拒、PR 合并成功 | 已验证 | 直推 `main` 被拒（`GH006: Protected branch update failed`）；PR #7 在 `BLOCKED → CLEAN` 后由 `merge` 合并（`831d7ef`） |

## 三、实现要点

- `merge` 新增 `--transport {auto,direct,pr}`（默认 `auto`）与 `--wait-timeout`（默认 1800s）。
- `auto`：远端 URL 含 `github.com` 且 `gh` 可用 → `pr`；否则 `direct`（旧行为，供本地 / 测试）。
- `pr`：推任务分支 → `gh pr create`（已存在则复用）→ 轮询 `statusCheckRollup` / `mergeStateStatus` →
  `gh pr merge --merge`（`delete_branch_on_merge` 自动删远端分支）→ 记录 `merged_sha`。
- 合并前仍在任务工作树跑 `validate.py`（`--no-verify` 可跳过）；退出码 1 阻断、2 放行。
- `WORKFLOW_GUARD_GH` 环境变量可覆盖 `gh` 命令，供测试注入 fake `gh`。

## 四、风险与遗留

1. **PR 传输耗时**：需等待 `validate` + `audit`（约 2–4 分钟）；`--wait-timeout` 超时即失败，不直推。
2. **检查名称耦合**：分支保护要求 `validate` / `audit` 两个 job 名；若改名需同步仓库保护与本工具。
3. **`direct` 仍为旧行为**：仅非 GitHub / 测试使用；生产默认 `auto` → `pr`。
4. **端到端**：已在真实仓库启用保护后验证「直推被拒 + PR 合并成功」（T6 完成）。
