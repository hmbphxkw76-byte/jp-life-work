# 工单：修复 merge 等待竞态（fix-merge-wait-checks）

> **版本**：v1.0（2026-11-23）
> **规格**：[specs/fix-merge-wait-checks.md](../specs/fix-merge-wait-checks.md)
> **分支**：`task/fix-merge-wait-checks-d8877c46`
> **状态**：进行中

## 工单

### T1 · 守卫等待逻辑修复

- **验收**：新增 `PR_REQUIRED_CHECKS = ("validate", "audit")`；`_gh_pr_wait_checks`
  必须等这两个检查出现且通过；空 rollup + `CLEAN` 不得立即返回；失败/超时的不合并。
- **状态**：待办

### T2 · 回归测试

- **验收**：`FAKE_GH` 返回带名检查；新增测试断言空 rollup + `CLEAN` 不立即返回；
  `unittest` 全绿。
- **状态**：待办

### T3 · 文档同步 + 双轴评审

- **验收**：`engine/scripts/README.md` 与实现一致；新增评审
  `docs/toolchain/reviews/fix-merge-wait-checks-review.md`。
- **状态**：待办

### T4 · 全量验证与合并

- **验收**：`unittest` / `validate` / `gate` / `ruff` / `mypy` 全绿；合并入 main；
  观察 `workflow_guard merge` 实际等待行为。
- **状态**：待办
