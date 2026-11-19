# 双轴评审：文档 ↔ 实现对齐（closure-a / N1 · N3 · N16）

> **任务 slug**：closure-a-doc-align
> **日期**：2026-11-19
> **评审对象**：`task/closure-a-93955b6d` 工作树（`.worktrees/closure-a`，基线 main @`fb1a38b`）
> **工单**：`docs/toolchain/tickets/n1-doc-align.md` / `n3-close-coverage-gate-t10.md` / `n16-docs-readme-index.md`（源：`docs/未完成项与对齐状态梳理-2026-11-19.md` 第五节）
> **评审人**：CatPaw（独立双轴）

---

## 一、Standards 轴（是否符合本规约 / 仓库规范）

| 条款 | 结论 | 证据 |
|---|---|---|
| 单一事实源 / 不新造口径 | ✅ | 数字全部来自实测（`generate_registry.py --check`、`unittest discover`、`.github/workflows/*.yml` 逐个数步），未引入新口径；类型口径统一为「六族十二类」 |
| 文档命名 / 结构 | ✅ | 未新增报告命名文件；评审报告用 kebab-case，未被 `classify_reports.py` 误判；既有文档章节结构（CI 二.1/二.3/二.6、总规范 §三、docs/README 一/四）保持不变 |
| 版本记录留痕 | ✅ | `docs/CI.md` v2.16→v2.17、`docs/信息生产全链路执行规范.md` v1.4→v1.5、`docs/README.md` v2.0→v2.1、`docs/cross-domain-expert-roles.md` v1.2→v1.3、`engine/tools/README.md` v1.1→v1.2 均追加版本记录，头部版本号 = 记录末版 |
| 头部版本 = 记录末版 | ✅ | 见上；`docs/README.md` 头部 v2.1 = 记录末版 v2.1（N16 验收项） |
| 守卫测试同步 | ✅ | `test_arch_guard.py::TestDocNumberGuard` 断言「N 条工作流」「测试数」与 `docs/CI.md` 一致；本次未改工作流数（8）与测试数（978），仅改步骤表 / 类型口径，守卫通过 |
| 不越权改内核 | ✅ | 未改 `engine/tools/` 逻辑、`.github/workflows/`、`engine/tests/`；仅文档与工单回填 |
| 工作区卫生 | ✅ | 变更仅落在 `docs/` 与 `engine/tools/README.md`；无缓存 / 临时残留 |

**Standards 轴结论：无 P0 / P1。**

## 二、Spec 轴（是否实现工单的验收标准）

| 工单验收标准 | 结论 | 证据 |
|---|---|---|
| N1：`docs/CI.md` 数字与实测一致 | ✅ | 二.1 步骤表补齐 28 步 + 2 附加 job；二.3 maintenance 19 步；二.6 audit-gate 5 步；十二.1「六族十二类」 |
| N1：`docs/信息生产全链路执行规范.md` 数字与实测一致 | ✅ | 头部工具 34→43；§三「共 14 步」→ 实测表述；§1.2 / §2.3 / §A.3「六族十二类」 |
| N1：`docs/README.md` 描述与头部版本 | ✅ | 头部 v2.0→v2.1 = 记录末版；版本记录 v2.1 已追加，计数与实测一致 |
| N1：`test_arch_guard.py` / `TestPipelineFlowSpec` 全绿 | ✅ | `python -m unittest discover -s engine/tests` → 978 tests，OK（skipped=4），退出码 0 |
| N3：T10 标 ✅ + 实测覆盖率 90.4% | ✅ | `docs/toolchain/tickets/coverage-gate.md` T10 = 「✅ 已完成」，附 `coverage_gate.py` 实测 90.4%（阈值 80%，enforce=true，退出码 0）。**偏差见第四节** |
| N16：`docs/README.md` 清单含 2026-11-19 文档 + 头部版本 | ⚠ 部分 | 头部版本已同步；2026-11-19 的 3 份过程文档已在 `14706bb` 清理中删除、第 4 份（未完成项与对齐状态梳理）从未入库，按「只收规范」均不纳入索引。**偏差见第四节** |

**Spec 轴结论：无 P0 / P1（N16 为「不适用」而非缺陷，已记录）。**

## 三、实测值与来源（本次对齐基线）

| 项 | 实测值 | 来源 / 命令 |
|---|---|---|
| 工具数 | 43 | `python engine/tools/generate_registry.py --check` → 「工具 43 · 类型 12 · 主题 21 · 工作流 8」 |
| 类型数 | 12（六族十二类） | `engine/report_templates/report-classification.md` / `template-registry.md` / `_common.TEMPLATE_TYPE_DIRS`；`test_tools.py::test_classification_matches_registry` 断言 12 |
| 主题数 | 21 | 同上注册表 |
| 工作流数 | 8 | `.github/workflows/*.yml` 计数；`docs/CI.md` 头部 |
| 测试数 | 978（OK，skipped=4） | `python -m unittest discover -s engine/tests` |
| validate.yml | 主 job 28 个命名步骤 + 2 个附加 job（覆盖率 / 工作区卫生） | 逐行解析 `.github/workflows/validate.yml` 的 `- name:` 与 `jobs:` |
| audit-gate.yml | 5 步 | `.github/workflows/audit-gate.yml`（gate / gate --strict / l5_meta_check / audit_check --all / review_gate） |
| scheduled-maintenance.yml | 19 步 | `.github/workflows/scheduled-maintenance.yml`（不含通用「安装依赖」） |
| 覆盖率 | 90.4%（阈值 80%，enforce=true，退出码 0） | `python engine/tools/coverage_gate.py` |

> 实测环境：`task/closure-a-93955b6d` 工作树，基线 main @`fb1a38b`（2026-11-19 13:07:44 +0800）。

## 四、偏差与未对齐项（如实记录）

1. **N3 目标文件已被删除**：`docs/toolchain/tickets/coverage-gate.md` 在原 `docs` 清理（`14706bb`，2026-11-19 12:52）中随一次性工单删除，`closure-a` 基线中不存在。为闭环 N3，从 git 历史恢复该文件并回填 T10 = 「✅ 已完成」+ 实测证据；如需保持「只收规范」，可在合并前改为仅在评审报告留痕。
2. **N16 目标文档已被删除 / 未入库**：登记册待核实项复核记录、门户 URL 核验深化方案、核验证据包-2026-11-19 这 **3 份**在 `14706bb`（`git log --diff-filter=D` 实证）中随一次性记录删除；第 4 份「未完成项与对齐状态梳理-2026-11-19」**从未进入版本库**（`git log --all -- "*未完成项*"` 无记录，仅存在于 closure-doc 工作树且为未跟踪文件）。当前 `docs/README.md` 明确「只收规范，不收一次性过程记录」，故均未补入索引；改为在版本记录 v2.1 留痕，已删除项指向 git 历史。
   > 工单 N16 原要求「清单含 2026-11-19 文档」与「只收规范」规则冲突，按仓库规则（`docs/README.md` 维护规则第 2 条 + `AGENTS.md` token 最小化）以只收规范为准，故 N16 判为**不适用**而非缺陷。
3. **validate 步骤数口径**：工单书写「主 job 28 个命名步骤 + 3 个附加 job（覆盖率 / 工作区卫生 / ruff+mypy）」。实测主 job 共 29 个 `- name:` 步骤（含通用「安装依赖」与「安装开发依赖」），扣除通用「安装依赖」为 28；`ruff` / `mypy` 是主 job 内步骤，**附加 job 为 2 个**（`coverage` / `workspace-hygiene`），第 3 个「ruff+mypy」不是独立 job。文档按实测口径书写并显式注明。
4. **A7（审计标准版本 v1.4 vs 记录 v1.7）** 不在 N1 目标（A1–A6、A8）内，未处理；`docs/审计报告标准化管理体系.md` 头部已注明「完整变更见版本记录，最新 v1.7」，`audit_registry.SPEC_VERSION` 测试通过。
5. **顺带对齐**：`docs/cross-domain-expert-roles.md`（34→43 工具、868→978 测试）与 `engine/tools/README.md`（881→978 测试）存在同类漂移，一并修正并留版本记录。
6. **工单载体**：本工作树 `docs/toolchain/tickets/` 仅有 `coverage-gate.md`（N3 目标）；`n1-doc-align.md` / `n3-close-coverage-gate-t10.md` / `n16-docs-readme-index.md` 未在本工作树落地，其定义来自参考文档《未完成项与对齐状态梳理-2026-11-19》第五节，故工单状态回填仅对 `coverage-gate.md` 生效（N1 / N16 以文档 diff + 校验退出码为证据）。

## 五、校验命令与输出摘要

| 命令 | 退出码 | 输出摘要 |
|---|---|---|
| `python -m unittest discover -s engine/tests -q` | 0 | `Ran 978 tests in 53.180s` / `OK (skipped=4)` |
| `python engine/tools/validate.py` | 0 | `结构与规范校验通过：通用层完整、业务线结构齐全、命名合规` |
| `python engine/tools/prompt_check.py` | 0 | `提示词门禁：0 项违规` |
| `python engine/tools/link_check.py` | 0 | `内链校验通过：无失效引用` |
| `python engine/tools/generate_registry.py --check` | 0 | `注册表一致：工具 43 · 类型 12 · 主题 21 · 工作流 8` |
| `python engine/tools/coverage_gate.py` | 0 | `覆盖率 90.4%（阈值 80%，enforce=True）（测试 全绿）` / `[OK] 覆盖率达标` |

**双轴结论：Standards 无 P0 / P1；Spec 无 P0 / P1（N16 为不适用项，已留痕）。**
