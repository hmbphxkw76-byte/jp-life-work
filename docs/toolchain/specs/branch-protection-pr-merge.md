# 规格：合并流程 PR 化 + 服务端分支保护（branch-protection-pr-merge）

> **版本**：v1.0（2026-11-22）
> **定位**：工具链变更规格（TOOLCHAIN-DEV-SPEC S1）。≤1 页，只含动机 / 接口 / 验收标准。

## 一、动机

1. 仓库为 PUBLIC，但 `main` 无服务端分支保护；`workflow_guard merge` 直推 `origin/main`，本地钩子 / CI 可被绕过。
2. 最佳实践要求：`main` 启用「Require PR + Require status checks + enforce_admins + 禁 force-push / 禁删除」。
3. 启用该保护后，直推 `main` 会被服务端拒绝，因此 `merge` 必须改为「推任务分支 → 建 PR → 等校验 → 合并 PR」。

## 二、接口

- `workflow_guard merge` 新增 `--transport {auto,direct,pr}`（默认 `auto`）与 `--wait-timeout`（默认 1800s）：
  - `auto`：远端为 GitHub 且 `gh` 可用 → `pr`；否则 `direct`（保持旧行为，供本地 / 测试）。
  - `pr`：推任务分支 → `gh pr create` → 轮询 `statusCheckRollup` → `gh pr merge --merge --delete-branch` → 记录 `merged_sha`。
  - `direct`：现行「本地 --no-ff 合并 + 推 main」，不变。
- 合并前仍跑本地校验（`validate.py`）；冲突处理沿用合并工作树。
- 仓库设置：启用分支保护（`validate` / `audit` 必需、`strict=false`、`enforce_admins=true`、禁 force-push / 删除）。
- 文档：`docs/branch-management.md`、`AGENTS.md` 硬性规约二、`docs/CI.md` §十六 / §十、`engine/scripts/README.md`。

## 三、验收标准

1. `merge --transport pr` 走「推分支 → 建 PR → 等检查 → 合并」，任务登记 `status=merged` 且 `merged_sha` 为远端合并提交；
2. `merge`（auto）在 GitHub 远端选 `pr`，在本地裸 origin（测试）选 `direct`；
3. 现有 34 项 `test_workflow_guard` 全绿；新增 PR 传输测试（fake `gh`）覆盖建 PR / 等检查 / 合并 / 已存在 PR；
4. `unittest` / `validate.py` / `audit_pipeline --gate` / `coverage_gate` 全绿；
5. 分支保护启用后：直推 `main` 被拒；任务 PR 在 `validate` + `audit` 通过后经 `merge` 合并成功。
