# 规格：本地等价 CI 入口（local_ci.py）

> 任务 slug：`local-ci-entry`
> 版本：v1.0（2026-11-22）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)
> 上位依据：[AGENTS.md](../../../AGENTS.md)、[CI.md](../../CI.md)

## 一、动机

账号 `hmbphxkw76-byte` 的 GitHub Actions 因**免费额度用尽**被账号级阻断（2026-11-22 起，
jp-life-work 与 tech-context-digest 均受影响），用户决定等下月额度恢复。此前本地虽已全量全绿，
但**没有单一入口**：一次合并前要手动敲 30+ 条命令，易漏、口径不统一。

本规格新增「本地等价 CI」编排层工具，把 `.github/workflows/` 中**本地可跑、只读、确定性、
不依赖外网**的检查步骤收敛为一条命令，作为额度恢复前的本地兜底，并保留结果分享开口。

## 二、目标与非目标

**目标**
1. 一条命令跑完 validate / audit-gate 的只读检查集，输出人类可读汇总 + 可选 JSON / Markdown。
2. 结果落盘为**确定性** JSON（无时间戳、无时长、键序稳定），可重复运行逐字节一致。
3. 退出码对齐仓库契约：`0` 全过 / `1` 有失败 / `2` 仅警告（含参数错误）。
4. 明确列出「仅远程」环节，消除「本地没跑 = 没做」的歧义。

**非目标**
- 不新增任何门禁判定（只编排既有工具，不写判定逻辑）。
- 不替代 AuditGuard / 交付与审计协议 / 三道内容卡点。
- 不跑需要外网、需要 token、会产生提交或写回审计状态的步骤。

## 三、接口设计

### 3.1 用法

```
python engine/tools/local_ci.py run [选项]
python engine/tools/local_ci.py list
```

`run` 选项：
- `--only a,b` / `--skip a,b`：按检查 id 过滤（未知 id 报参数错误，退出码 2）；
- `--json` / `--markdown` / 默认文本：输出格式；
- `--emit <路径>`：结果 JSON 落盘（默认 `engine/report-audits/local-ci/local-ci-status.json`）；
- `--with-tests`：追加「单元测试」检查（`unittest discover`）；
- `--with-coverage`：追加「覆盖率门禁」检查（`coverage_gate.py`）。

### 3.2 检查集（33 项，全部只读）

- **validate 系（31 项）**：`validate.py`、`classify_reports.py --check --unknown-warn`、
  `ensure_region_topics.py --check`、`build_hub.py --check`、`build_index.py --check`、
  `link_check.py`（不加 `--external`，不探测外网）、`generate_registry.py --check`、
  `audit_registry.py --check`、`audit_preflight.py --all`、`structure_check.py`、
  `md_html_parity.py`、`prompt_check.py`、`source_language_gate.py --changed --base main`、
  `verified_content_gate.py --all`、`decision_metrics.py --check`、`decision_log.py --check`、
  `source_check.py`、`counterexample_scan.py`、`lint_reports.py --new-only`、
  `compliance_check.py --new-only`、`stage_gate_check.py`、`generation_gate.py --all`、
  `info_quality_check.py --check`、`fact_card_check.py`、`pending_verification.py --check`、
  `personal_finance_model.py --check`、`vocab_tool.py topic-check/verify/cross-check`、
  `sync_vocab.py check`、`vocab_near_check.py`。
- **audit-gate 系（2 项）**：`audit_pipeline.py --gate`、`l5_meta_check.py --check`。
- **排除（非只读 / 需外网或清单）**：`audit_check.py --all`（写报告）、`auto_verify.py`（写日志）、
  `cleanup_workspace.py --check`（本工具运行本身产生 `__pycache__`，会自伤）、
  `review_gate.py --changed`（需变更清单）、`html-sync / maintenance` 的回写与修复类步骤。
- **仅远程**：链接可达率探测、自动开 PR / webhook 告警、GitHub runner 环境与服务端保护。

### 3.3 退出码与状态映射

- 单项：退出码 `0` → `pass`；`2` → `warn`；其余 → `fail`。
- 汇总：任一 `fail` → `1`；否则任一 `warn` → `2`；否则 `0`。
- 参数错误（未知 id 等）→ `2`（对齐 TOOLCHAIN-DEV-SPEC 第五节）。

### 3.4 确定性

- 结果 JSON 仅含 `schema_version` / `comment` / `branch` / `checks[]` / `summary`；
- 每项含 `id` / `name` / `ci` / `exit_code` / `status` / `summary`（末行非空输出）；
- **不含时间戳、耗时、随机序**；`checks` 顺序固定为 CHECKS 声明序。

## 四、验收标准

1. `python engine/tools/local_ci.py list` 列出全部检查项与「仅远程」清单，退出码 0。
2. `run --only validate` 退出码 ∈ {0,2}；`run --json` 输出可被 `json.loads` 解析，且两次运行
   （同分支、同工作区）**逐字节一致**。
3. 对合成工作区（tempfile 复制最小结构）注入一处规范违规，对应检查项 `fail`，`run` 退出码 1。
4. 真实仓库 `run`（默认集）退出码 ∈ {0,2}，且无 P0/P1 级失败。
5. `generate_registry.py --check` 通过（工具 49 → 50）；`unittest` / `ruff` / `mypy` /
   `validate.py` / `coverage_gate.py` / `cleanup_workspace.py --check` 全绿。

## 五、边界与约束

- 只读：不写回报告、不提交、不推送、不改审计状态。
- 工具链变更走 TOOLCHAIN-DEV-SPEC S1→S6；本工具为**新增工具**，不豁免任何阶段。
- 登记：`engine/tools/README.md` 工具一览 + `generate_registry` 重生成 `registry.json`。
- 结果文件 `engine/report-audits/local-ci/` 加入 `.gitignore`（可再生、不入库）。
