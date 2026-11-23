# 规格：CI 自动化 PR 门禁内移自动合并（ci-auto-merge-inwork-gate）

> **版本**：v1.0（2026-11-23）
> **定位**：工具链变更规格（TOOLCHAIN-DEV-SPEC S1）。≤1 页，只含动机 / 接口 / 验收标准。

## 一、动机

1. 真跑实证：用 `GITHUB_TOKEN`（`github-actions[bot]`）创建的 PR **不触发** `pull_request` 工作流，
   故 `validate` / `audit` 永不运行，`gh pr merge --auto` 永卡 `BLOCKED`
   （PR #13 / #15 `check-runs=0`；用户令牌创建的 PR #12 `check-runs=8`）。
2. 在**无 PAT** 约束下，把质量门禁从「分支保护必需检查」迁移到「创建工作流内自跑」，
   通过即自动合并。

## 二、接口

- 复合动作 `.github/actions/auto-merge-pr` 改为：定位 / 创建 PR → **工作流内门禁**
  （`engine/tools/validate.py` + `engine/tools/audit_pipeline.py --gate --strict`，接受退出码 `{0,2}`）
  → `gh pr merge <num> --merge`；门禁失败保留 PR open 并退出 1。
- **分支保护**：移除 required status checks（`validate` / `audit`），保留
  Require PR + `enforce_admins` + 禁 force-push / 删除；评审数仍 0。
- 修复 `engine/tools/trigger_watch.py`：写 snapshot 前建目录
  （`engine/report-audits/pipeline/` 未被 git 跟踪，致 `pipeline-orchestrator` 每次失败）。
- 6 条工作流接线（提交步骤输出 `branch` → 调用复合动作）保持不变。

## 三、验收标准

1. 复合动作含工作流内门禁与 `--merge`、不含 `--auto`；6 条工作流接线不变；守卫测试断言。
2. `main` 分支保护无 required status checks，且 Require PR / enforce_admins 保留。
3. 全量回归全绿；真跑：触发的 `scheduled-report-tasks` 产出的 PR 在门禁通过后自动合入 `main`。
4. `pipeline-orchestrator` 触发不再因目录缺失而失败。
