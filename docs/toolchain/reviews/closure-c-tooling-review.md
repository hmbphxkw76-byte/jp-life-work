# 组 C 工具接线 · 双轴评审（Standards + Spec）

> 分支：`task/closure-c-93955b6d`　Worktree：`.worktrees/closure-c`
> 工单：`n4-decision-log-ci` / `n5-info-quality-artifacts` / `n6-auto-verify-logs` / `n8-five-questions-convergence`
> 评审日期：2026-11-19　评审人：本任务 Agent（自评）；收尾复核：2026-11-19（接手 Agent 独立实跑，见第七节）
> 结论：**Standards 无 P0/P1；Spec 无 P0/P1**，可进入 S6 合并前检查单。

## 一、范围与改动清单

| # | 文件 | 性质 | 对应 |
|---|---|---|---|
| 1 | `engine/tools/decision_log.py` | 代码 | N4 新增 `--check`（缺失 / 结构损坏检测） |
| 2 | `engine/tests/test_cov_pipeline.py` | 测试 | N4 四条 `--check` 单测（TDD 红→绿） |
| 3 | `engine/tests/test_tools.py` | 测试 | N4 守卫：`validate.yml` 必须含 `decision_log.py --check` |
| 4 | `.github/workflows/validate.yml` | 工作流 | N4 新增「决策日志校验」步骤 |
| 5 | `engine/report-audits/info-quality/`（三清单 + `repair-ledger.md`） | 产物 | N5 运行 `--apply` 重建 |
| 6 | `docs/CI.md` | 文档 | N4 步骤行 + N5/N6 留存策略 + 计数 983 + v2.17 |
| 7 | `docs/信息质量评估提示词体系.md` | 文档 | N5 新增 8.4 产物留存策略 |
| 8 | `engine/tools/README.md` | 文档 | N4 复用阶段更新 |
| 9 | `00-decision-hub/data/decision_hub_registry.md` | 决策记录 | N8 新增 4.3 收敛机制说明 + v1.5 |
| 10 | `docs/toolchain/reviews/closure-c-tooling-review.md` | 评审 | 本文件 |

## 二、Standards 轴（规约符合性）

| 规约条款 | 落实 | 位置 |
|---|---|---|
| 退出码 0/1/2 契约 | `--check`：0 通过 / 1 缺失或结构损坏 / 2 暂无记录 | `decision_log.py::check` |
| 异常不静默 | 缺失 / 损坏走 `stderr` 并返回 1；`relative_to` 越界降级为原路径 | `decision_log.py::check` |
| TDD（先红后绿） | 先加 4 条单测 + 守卫测试（红：`error: unrecognized arguments: --check`），再实现 | `test_cov_pipeline.py` / `test_tools.py` |
| 测试入 `engine/tests/` | 新增 5 条测试，计数 978 → 983 | `docs/CI.md` 六节 |
| 单一事实源 | 未新增阈值；`decision_metrics` 阈值仍读 `engine/tools/decision-metrics-thresholds.json` | 未改 |
| 工作流复用测试 | 守卫断言步骤存在，漏接即失败 | `test_tools.py::TestProcessReuse` |
| 文档↔程序一致 | 提示词体系 8.4 与 `info_quality_check` 实际写盘行为一致 | `docs/信息质量评估提示词体系.md` |
| 工作区卫生 | `cleanup_workspace.py --check` 零残留 | 见证据 E9 |

**Standards 结论：无 P0/P1。** 备注（P3 级观察，不阻断）：`decision_log.py` 的 `--check` 为新增入口，未同步进 `engine/tools/registry.json`（该表只登记工具元数据、不登记子命令，`generate_registry --check` 通过，故不视为缺口）。

## 三、Spec 轴（工单验收映射）

| 工单验收 | 实现 | 证据 |
|---|---|---|
| N4 工作流含 decision_log 步骤 | `validate.yml` 新增步骤 | E4 |
| N4 守卫测试通过 | `test_validate_gate_checks_decision_log` | E2 |
| N5 三清单 + `rules-notes.md` 落盘 | `--apply` 重写三清单并新建 `repair-ledger.md`；`rules-notes.md` 原样保留 | E5 |
| N5 维护工作流刷新后仍存在 | `info-quality.yml` 步骤 1 `--apply` + 步骤 6 提交三清单，未改 | E5 / 工作流未改 |
| N5 `.gitignore` 口径 | 该目录未被忽略；策略写入 CI.md 与提示词体系 8.4 | E5 |
| N6 文档明确日志策略 | CI.md「核验日志策略（N6）」+ `engine/report-audits/README.md` 已有一致描述 | E6 |
| N6 全量日志 21 份 | `--all --dry-run` 生成 21 份 `<slug>.json` | E6 |
| N8 触发条件说明 | 登记册 4.3 三条件 + 0% 原因 | E7 |
| N8 `decision_metrics --check` 不劣化 | rc=2（存在待定 / 缺失，仅告警），与改动前一致 | E7 |

**Spec 结论：无 P0/P1。**

## 四、证据（命令 + 输出摘要）

- **E1 全量测试**：`python -m unittest discover -s engine/tests -q`
  → `Ran 983 tests in 48.520s` / `OK (skipped=4)`（rc=0）
- **E2 定向测试**：`python -m unittest engine.tests.test_cov_pipeline.TestCovPipelineDecisionLog engine.tests.test_tools.TestProcessReuse -q`
  → `OK`（rc=0）；TDD 红态为 `error: unrecognized arguments: --check`
- **E3 规范校验**：`python engine/tools/validate.py`
  → `结构与规范校验通过：通用层完整、业务线结构齐全、命名合规`（rc=0）
- **E4 工作流步骤**：`grep -n "decision_log.py --check" .github/workflows/validate.yml`
  → 命中新增步骤（`决策日志校验（decision_log.py --check）`）
- **E5 信息质量产物**：`python engine/tools/info_quality_check.py --apply`
  → `问题：P0 0 / P1 0 / P2 0`；`自动修复 0 条`；`报告已写入：assessment-ledger.md, repair-ledger.md, verification-report.md, info-quality.json`（rc=0）
  → 目录实含：`assessment-ledger.md` / `repair-ledger.md` / `verification-report.md` / `rules-notes.md` / `info-quality.json` / `repair-history.md` / `findings-by-path.json`
- **E6 核验日志**：`python engine/tools/auto_verify.py --all --dry-run`
  → rc=0；`ls engine/report-audits/audit/verify/ | wc -l` = **21**；`git check-ignore -v` 命中 `.gitignore:23`（不入库）
- **E7 决策度量**：`python engine/tools/decision_metrics.py --check`
  → `指标收敛率 21%、五问判定率 0%、缺失 16 条、决策变化 4 次`（rc=2，仅告警）
  → `--trend` 无历史时 rc=2（历史文件不存在，符合「仅一期数据」说明）
- **E8 注册表 / 静态检查**：`python engine/tools/generate_registry.py --check` → `注册表一致：工具 43 · 类型 12 · 主题 21 · 工作流 8`（rc=0）
  → `mypy engine/tools/decision_log.py` → `Success: no issues found`（rc=0）
  → `ruff`：`decision_log.py` 0 错误；`test_cov_pipeline.py` 8 / `test_tools.py` 10，与 HEAD 同数（无新增）
- **E9 工作区卫生**：`python engine/scripts/cleanup_workspace.py --check` → `工作区干净，无残留`（rc=0）
- **E10 覆盖率**：`coverage run --source=engine -m unittest discover -s engine/tests -q` + `coverage_gate.py`
  → `覆盖率 90.4%（阈值 80%，enforce=True）（测试 全绿）` / `[OK] 覆盖率达标`（rc=0）

## 五、决策取舍说明

1. **N4 接 `validate.yml` 而非 `scheduled-maintenance.yml`**：`decision_log.md` 是跟踪交付物，「可检测缺失」属门禁属性；`validate.yml` 在每次 PR / push 即时拦截，且与既有 `decision_metrics --check` 同处，语义一致。维护流水线按月跑太慢，不足以承担「缺失检测」。
2. **N4 新增 `--check` 而非「刷新」**：`decision_log` 为追加式人工记录，无可自动刷新的派生数据；「检测缺失」才是可自动化部分，故实现 `--check`（0/1/2），不伪造刷新动作。
3. **N5 不调整 `.gitignore`**：`engine/report-audits/info-quality/` 本就未被忽略，产物可留存；仅补文档说明，避免扩大改动面。`repair-ledger.md` 在零修复轮次也写盘，消除「零修复 = 文件缺失」歧义。
4. **N6 维持「不入库」**：`.gitignore:23` 已排除 `audit/verify/`，`engine/report-audits/README.md` 已声明为运行期产物；本次仅补 CI.md 策略说明并实测 21 份，保持单一事实源一致，不引入双轨。
5. **N8 只补决策记录，不补代码**：`decision_metrics --history/--trend` 跨月机制已在，`update_planner --decisions` 已消费 `decision_log`；当前 0% 的根因是五问全「待定」+ 仅一期数据，属数据状态而非机制缺失，故按工单「择一」取决策记录（登记册 4.3），不虚构收敛时点。
6. **测试计数同步**：新增 5 条测试，`docs/CI.md` 六节与合计行 978 → 983，`test_arch_guard` 计数守卫恢复通过。

## 六、残留与后续（不阻断）

- 测试计数漂移的**实际残留位置是 `engine/tools/README.md:13`**（仍写「单元测试（881 项）」）。`docs/README.md` 已于 2026-11-19 升版 v2.0，不再携带该数字（维护规则第 4 条改为「以代码实测为准，由测试双向锁定」）。该 881 属组 A / N1 文档对齐范围，本任务未改，避免与组 A 改动重叠。
- `engine/report-audits/README.md` 与 N5 留存策略存在措辞冲突：第 25 行把 `repair-history.md` 列为「台账」、第 35–37 行把 `assessment-ledger.md` / `verification-report.md` 列为「生成物（可删除重生成）」、第 44 行仍把 `repair-ledger.md` 列入「已清理的生成物」。N5 已明确三清单随提交留存（`docs/CI.md` 第 6 节 / 提示词体系 8.4），README 需由 N1 统一收口；本任务未改。
- `findings-by-path.json` 为内容哈希缓存，随 md 变更刷新；本次因文档改动而更新，属预期。
- 未提交、未合并、未推送（按任务约束）。

## 七、收尾复核（2026-11-19，接手 Agent 独立实跑）

> 前一实施 Agent 被中断后，接手 Agent 在 `.worktrees/closure-c` 对下列结论逐项实跑复核，全部与本节上文一致。

| 复核项 | 命令 | 结果 | 退出码 |
|---|---|---|---|
| 全量单测 | `python -m unittest discover -s engine/tests -q` | `Ran 983 tests` / `OK (skipped=4)` | 0 |
| 规范校验 | `python engine/tools/validate.py` | 结构与规范校验通过 | 0 |
| 决策日志门禁 | `python engine/tools/decision_log.py --check` | 4 条记录，最新 2026-11-14 | 0 |
| 决策度量 | `python engine/tools/decision_metrics.py --check` | 收敛率 21% / 五问 0% / 缺失 16 | 2（与基线一致，未劣化） |
| 跨月趋势 | `python engine/tools/decision_metrics.py --trend` | 无历史快照（`available=false`），不虚构 | 2 |
| 注册表 | `python engine/tools/generate_registry.py --check` | 工具 43 · 类型 12 · 主题 21 · 工作流 8 | 0 |
| 类型检查 | `python -m mypy engine/tools/decision_log.py` | Success: no issues found | 0 |
| 静态检查 | `ruff check`（逐文件） | `decision_log.py` 0 / `test_cov_pipeline.py` 8 / `test_tools.py` 10 | 1（存量，均与 HEAD 同数） |
| 覆盖率 | `coverage run --source=engine -m unittest ...` + `coverage_gate.py` | 90.4%（阈值 80%） | 0 |
| 工作区卫生 | `python engine/scripts/cleanup_workspace.py --check` | 工作区干净，无残留 | 0 |
| 核验日志 | `ls engine/report-audits/audit/verify/` | 21 份 per-slug 日志（无 `auto-verify-all.json`，该文件由维护流水线 `--json` 落盘） | — |
| 信息质量产物 | `ls engine/report-audits/info-quality/` | 7 文件齐全（三清单 + `rules-notes.md` + `repair-history.md` + `info-quality.json` + `findings-by-path.json`） | — |

- ruff 存量复核：`git show HEAD:<file> | ruff check -` 分别为 10 / 8 / 0，与改动后同数，确认**未新增**静态问题。
- 工作区卫生说明：复核过程中 `unittest` / `mypy` / `ruff` 产生 6 个 cache-dir（`.mypy_cache` / `.ruff_cache` / 三处 `__pycache__`，均 `.gitignore` 命中），已用 `cleanup_workspace.py` 清理，`--check` 恢复 0。
- `git status` 全程未出现新的未跟踪残留；`decision_metrics --trend` 写回的 `audit/decision-metrics.{json,md}` 与 HEAD 内容一致，未产生额外 diff。
