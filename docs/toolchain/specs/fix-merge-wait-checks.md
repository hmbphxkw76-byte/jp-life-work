# 规格：修复 merge 等待竞态（fix-merge-wait-checks）

> **版本**：v1.0（2026-11-23）
> **定位**：工具链变更规格（TOOLCHAIN-DEV-SPEC S1）。≤1 页，只含动机 / 接口 / 验收标准。

## 一、动机

- 方案 B 移除 `main` 分支保护必需检查后，`mergeStateStatus=CLEAN` 不再代表「检查通过」。
- `_gh_pr_wait_checks`（`engine/scripts/workflow_guard.py`）在 `statusCheckRollup` 为空时
  `pending=[]`，叠加 `CLEAN` 会**立即返回**，导致 PR 在远程 `validate` / `audit` 完成前被合并。
- 实证：PR #21 `mergedAt=02:47:13Z`，当时 `validate` / `audit` / `tests` / `coverage` 仍 `IN_PROGRESS`。

## 二、接口

- `engine/scripts/workflow_guard.py`：新增模块常量
  `PR_REQUIRED_CHECKS = ("validate", "audit")`（注释指向 `docs/CI.md` 的门禁定义）。
- `_gh_pr_wait_checks`：除原有「任一检查失败即报错」外，**必须等待 `PR_REQUIRED_CHECKS`
  全部出现且结论 ∈ `{SUCCESS, NEUTRAL, SKIPPED, COMPLETED}`** 才返回；
  缺失或未完成视为 pending，超时（沿用 `--wait-timeout`）报错、不合并。
- `engine/tests/test_workflow_guard.py`：`FAKE_GH` 返回**带名**检查；新增回归
  （空 rollup + `CLEAN` 不得立即返回）。

## 三、验收标准

1. 空 `statusCheckRollup` + `CLEAN` 时 `_gh_pr_wait_checks` 不立即返回（超时/等待）。
2. `validate` / `audit` 均 SUCCESS 后才合并；任一 FAILURE 报错。
3. `unittest` 全绿；`validate` / `audit_pipeline --gate` / `ruff` / `mypy` 通过。
4. 文档同步 + 双轴评审。
