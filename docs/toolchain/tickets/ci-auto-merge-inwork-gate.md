# 工单：CI 自动化 PR 门禁内移自动合并（ci-auto-merge-inwork-gate）

> **版本**：v1.0（2026-11-23）
> **规格**：[specs/ci-auto-merge-inwork-gate.md](../specs/ci-auto-merge-inwork-gate.md)
> **分支**：`task/ci-auto-merge-inwork-gate-d8877c46`
> **状态**：已完成

## 工单

### T1 · 复合动作改为「建 PR → 门禁 → 合并」

- **验收**：`.github/actions/auto-merge-pr/action.yml` 含 `validate.py` 与
  `audit_pipeline.py --gate --strict`（接受 `{0,2}`）与 `gh pr merge --merge`；不含 `--auto`；
  门禁失败退出 1 且保留 PR open。
- **状态**：已完成

### T2 · 移除 main 分支保护必需检查

- **验收**：`gh api .../branches/main/protection` 无 `required_status_checks.contexts`；
  Require PR / enforce_admins / 禁 force-push 保留。
- **状态**：已完成（`required_status_checks=null`、`enforce_admins=true`、评审数 0）

### T3 · 修复 `trigger_watch.py` 建目录

- **验收**：写 `engine/report-audits/pipeline/trigger-watch.json` 前 `mkdir -p`；
  `pipeline-orchestrator` 触发不再 `FileNotFoundError`。
- **状态**：已完成（含回归测试 `test_cli_apply_creates_missing_parent_dir`）

### T4 · 守卫测试更新

- **验收**：`engine/tests/test_ci_auto_merge.py` 断言门禁与 `--merge`、无 `--auto`、
  6 条工作流接线、无残留 `gh pr create`；`unittest` 全绿。
- **状态**：已完成（6 项；全量 1179 项全绿）

### T5 · 文档同步 + 双轴评审

- **验收**：CI.md / branch-management.md / engine scripts∖tools README / docs README /
  cross-domain 与实现一致；新增 `docs/toolchain/reviews/ci-auto-merge-inwork-gate-review.md`。
- **状态**：已完成（旧评审标注废弃）

### T6 · 全量验证与合并

- **验收**：`unittest` / `validate` / `gate` / `coverage` / `cleanup` / `ruff` / `mypy` 全绿；
  合并入 main。
- **状态**：已完成（unittest 1179、validate 0、gate 0、coverage 88.7%、ruff/mypy 0）

### T7 · 真跑验证

- **验收**：触发 `scheduled-report-tasks`，其 PR 在门禁通过后自动合入 `main`（记录 PR 号与合并提交）。
- **状态**：已完成（PR #17，merge `ccbd697`；另 `pipeline-orchestrator` → PR #19 / #20 亦自动合入）
