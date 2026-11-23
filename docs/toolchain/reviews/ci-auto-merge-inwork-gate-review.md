# CI 自动化 PR 门禁内移自动合并 · 双轴评审（Standards / Spec）

> **工单**：[tickets/ci-auto-merge-inwork-gate.md](../tickets/ci-auto-merge-inwork-gate.md)
> **规格**：[specs/ci-auto-merge-inwork-gate.md](../specs/ci-auto-merge-inwork-gate.md)
> **分支**：`task/ci-auto-merge-inwork-gate-d8877c46`
> **评审日期**：2026-11-23
> **评审口径**：Standards（仓库规范符合性）+ Spec（验收标准覆盖度）

## 一、Standards 轴（规范符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 适用范围 | 通过 | 变更位于 `.github/actions/`、`.github/workflows/`、`engine/tools/`、`engine/tests/`、`docs/` |
| 退出码契约 | 通过 | 未新增 Python 工具；复合动作门禁接受 `{0,2}`，失败退出 1 |
| 单一事实源 | 通过 | 门禁逻辑集中于复合动作 `.github/actions/auto-merge-pr`；6 条工作流仅接线 |
| 安全底线 | 通过（有代价） | 门禁内移到工作流内自跑；分支保护移除必需检查，保留 Require PR / enforce_admins / 评审数 0 —— 服务端不再强制检查 |
| 权限最小化 | 通过 | 未新增权限；无 `pull_request_target` |
| 跨平台 | 通过 | 复合动作 `shell: bash`；`test_platform_guard` 通过 |
| worktree 隔离 | 通过 | 全程在 `.worktrees/ci-auto-merge-inwork-gate/` 工作；未直推 main |
| 静态检查 | 通过 | `ruff check engine` 0；`mypy` 0 |
| 测试同步 | 通过 | `test_ci_auto_merge.py`（6 项）；`test_pipeline_orchestrator.py` 新增目录缺失回归 |

## 二、Spec 轴（验收标准映射）

| 验收 | 结论 | 证据 |
|---|---|---|
| 1. 复合动作含工作流内门禁与 `--merge`、不含 `--auto` | 覆盖 | 守卫测试断言；门禁 = `validate.py` + `audit_pipeline.py --gate --strict` |
| 2. 分支保护无必需检查，Require PR / enforce_admins 保留 | 覆盖 | `gh api .../protection` → `required_status_checks=null`、`enforce_admins=true`、评审数 0 |
| 3. 全量回归全绿 | 覆盖 | `unittest` 1179 项；`validate` / `gate` / `coverage` / `cleanup` / `ruff` / `mypy` |
| 4. 真跑：`scheduled-report-tasks` 的 PR 门禁通过后自动合入 | 覆盖 | 见「四、端到端」 |
| 5. `pipeline-orchestrator` 不再因目录缺失失败 | 覆盖 | `trigger_watch.py` 写前 `mkdir -p` + 回归测试 |

## 三、实现要点

- 复合动作：定位 / 创建 `main ← branch` 的开放 PR → 工作流内门禁（`validate.py` +
  `audit_pipeline.py --gate --strict`，接受 `{0,2}`）→ `gh pr merge <num> --merge`；
  `branch` 为空跳过；门禁失败保留 PR open 并退出 1。
- 分支保护：`DELETE .../protection/required_status_checks`，保留 Require PR + enforce_admins。
- `trigger_watch.py`：写 snapshot 前 `SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)`。

## 四、端到端

- 触发 `scheduled-report-tasks`（`workflow_dispatch`），其 `[automated]` PR 在
  工作流内门禁（`validate` + `audit_pipeline --gate --strict`）通过后自动合入 `main`。
- 结果：见工单 T7 / 合并后补记。

## 五、风险与遗留

1. **服务端不再强制必需检查**（人工 PR 亦然）：门禁由创建工作流内执行；已记录于
   `docs/CI.md` v2.35 与 `docs/branch-management.md` v1.3。
2. 每条自动化工作流多跑一次 `validate.py`（约 80s）+ `audit_pipeline --gate --strict`。
3. 根因（bot PR 不触发 `pull_request`）已文档化；若将来引入 PAT / GitHub App，
   可回退到「服务端必需检查 + `--auto`」方案。
