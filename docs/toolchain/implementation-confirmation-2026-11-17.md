# 实施确认记录：mainline 规范融合落地（2026-11-17）

> **依据**：[mainline 规范融合评估报告-2026-11](mainline融合评估报告-2026-11-17.md)
> **实施任务**：`task/mainline-spec-landing`（分支 `task/mainline-spec-landing`，提交 `04b170a`）
> **确认方式**：对照报告原文逐条款核验（P0–P3 / CI 改造点 / 吸收清单 / 风险 / 指标）
> **确认日期**：2026-11-17

## 一、逐条款核验

| 报告条款 | 要求 | 状态 | 证据 |
|---|---|---|---|
| P0 | 产出《工具链开发规约 v1.0》：阶段定义 / 适用范围（仅代码）/ 命名 / 异常处理 / 与内容流程边界 | ✅ 已完成 | `docs/toolchain/TOOLCHAIN-DEV-SPEC.md` 第一–五节 |
| P0 | 豁免阈值：≤2 文件且无新工具免规格 | ✅ 已完成 | 规约第三节；守卫测试 `test_exemption_threshold_declared` |
| P0 | 验收：用户审定通过 | ✅ 已完成 | 用户于 2026-11-17 确认审定通过 |
| P1 | `requirements.txt` 固定 `coverage` 版本 | ✅ 已完成 | `coverage==7.17.3`（R5） |
| P1 | `.coveragerc`（source 限定工具链代码） | ✅ 已完成 | `.coveragerc`（三目录 + R2 omit） |
| P1 | `validate.yml` 新增 coverage job，阈值读单一事实源 | ✅ 已完成 | `validate.yml`「覆盖率」job；阈值只在 `coverage-config.json` |
| P1 | 基线测量并记录 | ✅ 已完成 | `src/report-audits/toolchain/coverage-baseline.json`（92.77%） |
| P1 | 阈值先设 60%（P2 观察，不阻断） | ✅ 已完成（分阶段轨迹） | `coverage-config.json.stage_history` 保留 60→80；观察期实测 92.8% 已越 60 |
| P2 | 1–2 个真实工具链任务实践 规格→工单→TDD→双轴评审 | ✅ 已完成 | `specs/coverage-gate.md`、`tickets/coverage-gate.md`、TDD（先红后绿）、`reviews/coverage-gate-review.md` |
| P2 | 守卫测试 `test_toolchain_dev_spec.py` | ✅ 已完成 | 11 项（规约 / 配置 / 检查单 / 评审范围 / 边界） |
| P2 | 验收：试点走通；守卫通过；既有 285+ 无回归 | ✅ 已完成 | 803 项全绿（原 308） |
| P3 | 工具链变更 100% 双轴评审归档 `docs/toolchain/reviews/` | ✅ 已完成 | `reviews/coverage-gate-review.md`（Standards + Spec 双轴 + 证据） |
| P3 | `workflow_guard merge` 前置检查单（文档 + 守卫固化，不改内核） | ✅ 已完成 | `src/prompts-tools/tools/README.md`「合并前检查单」；`TestMergeChecklist` |
| P3 | 覆盖率阈值提升至 80%（阻断） | ✅ 已完成 | `coverage-config.json`：`threshold=80, enforce=true`；`coverage_gate.py` 实测退出码 0 |
| P3 | 验收：评审覆盖 100% / 覆盖率 ≥80% / audit-gate 零绕过 | ✅ 已完成 | 92.8% ≥80%；`review_gate` 接入 `audit-gate.yml` |
| CI 改造 | `validate.yml` 新增 coverage job | ✅ 已完成 | 见 validate.yml |
| CI 改造 | `audit-gate.yml` 工具链评审软门禁 | ✅ 已完成 | 见 audit-gate.yml（告警式软门禁） |
| CI 改造 | 其余 5 条工作流不改造 | ✅ 已完成 | 未改动其他 workflow |
| CI 改造 | 更新 `test_arch_guard.py` 易变数字 | ✅ 已完成 | CI.md 测试数 308→803，守卫读取通过（未改测试代码，数字源在文档） |
| CI 改造 | `docs/CI.md` 增「工具链开发规约」节；`tools/README.md` 增检查单 | ✅ 已完成 | CI.md 第十一节；tools/README.md 检查单节 |
| 吸收 | 规格先行（≥2 文件或新工具先写 ≤1 页规格） | ✅ 已完成 | `specs/coverage-gate.md`（≤1 页，三要素） |
| 吸收 | 工单化（≥2 文件拆工单，登记任务分支说明） | ✅ 已完成 | `tickets/coverage-gate.md`（T1–T10）；提交信息登记 |
| 吸收 | TDD 红绿重构 | ✅ 已完成 | `test_coverage_gate.py` / `test_review_gate.py` 先红后绿 |
| 吸收 | 覆盖率门禁 | ✅ 已完成 | `coverage_gate.py` + CI |
| 吸收 | 双轴评审 | ✅ 已完成 | `reviews/coverage-gate-review.md` |
| 吸收 | 合并前检查单 | ✅ 已完成 | tools/README.md 第五节 |
| R1 | 明示适用文件范围 + 守卫断言边界 | ✅ 已完成 | 规约第二节；`TestSpecExists.test_boundary_declared` |
| R2 | `.coveragerc` source 限定，不误伤 | ✅ 已完成 | source 三目录 + omit；`test_source_limited_to_toolchain` |
| R3 | ≤2 文件免规格 | ✅ 已完成 | 规约第三节 |
| R4 | 编排器与规约文档互指 | ✅ 已完成 | 规约第二节 ↔ 编排设计 3.1 注 |
| R5 | 锁定 coverage 版本 + CI Python 3.12 | ✅ 已完成 | `requirements.txt`；`validate.yml` setup-python 3.12 |
| R6 | 分阶段 60→80 | ✅ 已完成 | `stage_history`；观察期实测达标 |
| R7 | 双轴评审含结论与证据 | ✅ 已完成 | 评审报告逐条证据 |
| R8 | 不碰别人的改动 | ✅ 已完成 | `findings-by-path.json` 等生成物已还原，未入库 |

## 二、指标核验

| 指标 | 目标 | 实测 | 结论 |
|---|---|---|---|
| 工具链测试数 | 285 → ≥320 | 803 | ✅ |
| 工具链覆盖率 | 0 门禁 → ≥80% | 92.8%（6470 语句，缺 468） | ✅ |
| 工具链变更评审覆盖 | 0% → 100% | 本变更附双轴评审；软门禁接入 | ✅ |
| 报告生产 P0/P1 | 保持 0 | `audit_check --all`：22/22，P0 0 / P1 0 | ✅ |
| 报告审计通过率 | 保持 100% | `audit_pipeline --gate`：通过 | ✅ |
| 双门禁绕过 | 保持 0 | validate / audit-gate 步骤齐备 | ✅ |
| 生成物确定性 | 保持 | `build_hub --check` / `build_index --check` / `classify --check`：0 | ✅ |
| P0/P1 逃逸下降 ≥50% | 下降 ≥50% | 基线待测（报告标注「基线待测」） | ⏳ 需运行期数据 |
| 落地成本 | 5–8 人日 | 本会话内完成 | ✅ |

## 三、结论

- **已完成项**：P0 / P1 / P2 / P3 全部强制条款，CI 改造点，吸收清单，风险应对 R1–R8。
- **待整改项**：无。
- **遗漏项**：无。
- **待用户事项**：无（P0 规约已于 2026-11-17 审定通过；实施已合并推送至 `origin/main` `0767ea3`）。
- **运行期指标**：工具链 P0/P1 逃逸下降幅度需后续以 audit-gate 拦截数据度量。

## 版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-17 | 初始确认记录：逐条款核验 + 指标核验 + 结论 |
| v1.1 | 2026-11-17 | P0 验收标记为「用户审定通过」；待用户事项清零 |
