# 双轴评审：文档 ↔ 实现对齐（T1 / T10 · align-docs）

> **任务 slug**：align-docs
> **日期**：2026-11-19
> **评审对象**：`task/align-docs-9a56c316` 工作树（`.worktrees/align-docs`，基线 `origin/main` @`ab5ab6b`）
> **工单**：T1（文档↔实现完整对齐）+ T10（扩展守卫测试），源：2026-11-19 审计漂移清单
> **评审人**：CatPaw（独立双轴）

---

## 一、Standards 轴（是否符合本规约 / 仓库规范）

| 条款 | 结论 | 证据 |
|---|---|---|
| 单一事实源 / 不新造口径 | ✅ | 所有数字来自实测（`generate_registry.py --check`、`unittest discover`、`.github/workflows/*.yml` 逐行解析、`terms.md` 正则汇总、`coverage_gate.py --porcelain`），未引入新口径；类型口径统一「六族十二类」 |
| 只改本任务范围 | ✅ | 变更仅落在 `docs/`、`engine/README.md`、`engine/scripts/README.md`、`engine/tests/test_arch_guard.py`；未改 `*/reports/*.md`、未改 `engine/tools/` 逻辑、未改 `.github/workflows/`、未碰共享检出与其他 worktree |
| 不弱化既有断言 | ✅ | 既有 `TestDocNumberGuard` / `TestRegistrationConsistency` / `TestAtomicWrite` / `TestResolveWithin` 全部保留；新增守卫为附加类 `TestDocImplAlignmentGuard`，未修改任何既有断言 |
| 守卫测试同步 | ✅ | 新增 5 项守卫（类型数 / 词库条数 / CI 步骤数 ↔ workflow / 覆盖率基线 ↔ scripts/README / docs/README 一次性文档声明），全部通过 |
| 文档命名 / 结构 | ✅ | 评审报告用 kebab-case，未被 `classify_reports.py` 误判；既有文档章节结构未变 |
| 工作区卫生 | ✅ | 提交前 `cleanup_workspace.py`；`test_write_is_idempotent` 在 Windows 下会把 `engine/tools/README.md` / `registry.json` 写成 CRLF（内容不变），已归一化回 LF 后再提交 |
| 不越权改内核 | ✅ | 未改工具逻辑 / 工作流 / 报告；仅文档与守卫测试 |

**Standards 轴结论：无 P0 / P1。**

## 二、Spec 轴（逐项漂移修正）

| # | 对象 | 改前 → 改后 | 位置 | 结论 |
|---|---|---|---|---|
| 1 | 工具数 | 43 → 44 | `docs/信息生产全链路执行规范.md` 头部；`docs/README.md` v2.1 版本记录 | ✅ |
| 2 | 工具数 / 类型数 | 34 / 13 → 44 / 12 | `engine/scripts/README.md` §十二 第 6 项 | ✅ |
| 3 | 测试数 | 978 → 1003（见第四节第 2 条） | `docs/README.md` v2.1；`docs/CI.md` 六节；`docs/cross-domain-expert-roles.md` R1 | ✅ |
| 4 | validate 主 job 步骤 | 28 命名 / 29 `- name:` → 29 命名 / 30 `- name:` | `docs/CI.md` 二.1；`docs/信息生产全链路执行规范.md` §三 | ✅ |
| 5 | maintenance 步骤 | 19 → 20 | `docs/CI.md` 二.3 | ✅ |
| 6 | audit-gate 步骤 | 5（已一致，未动） | `docs/CI.md` 二.6 | ✅ 不动 |
| 7 | 类型数 | 13 类 / 六族十三类 → 12 | `engine/README.md`（4 处）；`docs/提示词库体系.md` 第 22 行 | ✅ |
| 8 | 词库条数 | 1327 / 1389 → 1634 | `docs/cross-domain-expert-roles.md` 第 69 行；`docs/提示词库体系.md` 第 6 / 21 行 | ✅ |
| 9 | 覆盖率 | 92.0% → 90.35% | `engine/scripts/README.md` §十二 第 4 项 | ✅ |
| 10 | 一次性文档声明 | 称「3 份已删除、第 4 份未入库」→ 4 份均在库 | `docs/README.md` v2.1 版本记录末行 | ✅ |

**Spec 轴结论：无 P0 / P1。**

## 三、实测值与来源（本次对齐基线）

| 项 | 实测值 | 来源 / 命令 |
|---|---|---|
| 工具数 | 44 | `python engine/tools/generate_registry.py --check` → 「工具 44 · 类型 12 · 主题 21 · 工作流 8」 |
| 类型数 | 12（六族十二类） | `_common.TEMPLATE_TYPE_DIRS` / `template-registry.md` / `compliance-rules.json`；`engine/report_templates/` 12 个类型目录 |
| 主题数 | 21 | 同上注册表 |
| 工作流数 | 8 | `.github/workflows/*.yml` 计数 |
| 测试数 | 1003（OK，skipped=4） | `python -m unittest discover -s engine/tests` |
| validate.yml | 主 job 30 个 `- name:`（扣除「安装依赖」= 29 命名步骤）+ 2 附加 job | 逐行解析 `.github/workflows/validate.yml` 的 `jobs:` / `- name:` |
| scheduled-maintenance.yml | 21 个 `- name:`（扣除「安装依赖」= 20） | 同上 |
| audit-gate.yml | 6 个 `- name:`（扣除「安装依赖」= 5） | 同上 |
| 词库条数 | 1634 | 正则 `^\|\s*[A-Z]{3}-\d+` 汇总 `engine/vocabulary/data/*/terms.md`；`vocab_tool.py verify` → 20 主题 0 错误 |
| 覆盖率 | 90.35%（阈值 80%，enforce=true，退出码 0） | `python engine/tools/coverage_gate.py --porcelain` |

> 实测环境：`task/align-docs-9a56c316` 工作树，基线 `origin/main` @`ab5ab6b`（2026-11-19 15:47:07 +0800）。

## 四、偏差与处理说明（如实记录）

1. **4 份过程文档的处理**：`git ls-files` 实证 4 份（登记册待核实项复核记录、门户 URL 核验深化方案、核验证据包-2026-11-19、未完成项与对齐状态梳理-2026-11-19）**均在库**。此前 `docs/README.md` v2.1 称「3 份已删除、第 4 份未纳入版本库」与实库不符。本次按「过程留痕」定性：**不纳入 14 份规范清单**（遵守「只收规范」），但**保留在库**（它们是 2026-11-19 审计闭环的证据，删除会破坏留痕，且 `engine/README.md` 维护纪律要求「删除前全仓 grep 确认零引用」，这些文档被审计记录引用）。已加守卫锁定该声明。
2. **测试数 978 → 1003（非 998）**：审计清单写「978 → 998」，但交付要求新增 5 项守卫，`unittest` 实测由 998 增至 1003；既有守卫 `test_test_count_matches_ci_doc` 双向锁定 `docs/CI.md` 测试数，故 `docs/CI.md` 六节 / 合计行、`docs/README.md` v2.1、`docs/cross-domain-expert-roles.md` R1 同步更新为 1003，否则全绿无法达成。**未弱化该既有断言**。
3. **覆盖率口径**：`--porcelain` 实测 90.35%；已提交的基线文件 `engine/report-audits/toolchain/coverage-baseline.json` 为 90.46%（2026-11-18 生成，已过期，且不在本任务可改范围）。守卫以「文档值 ↔ 基线文件 ±0.5pp」锁定：覆盖率随每次运行小幅波动，±0.5pp 既能拦住 92.0% 这类 1.5pp 漂移，又不因正常波动误报。
4. **顺带修正（清单外）**：`docs/cross-domain-expert-roles.md` R1 的「43 个工具 / 978 项」同为漂移，一并修正为 44 / 1003，避免同类数字继续不一致。
5. **版本记录口径**：`docs/CI.md` v2.17、`docs/信息生产全链路执行规范.md` v1.5 等历史版本记录保留当时数值（历史留痕），不改；本次现行数值以各文档正文/头部为准。
6. **audit-gate 步骤数**：实测 6 个 `- name:`（扣除「安装依赖」= 5）与文档一致，按要求未改动。

## 五、新增守卫测试名

`engine/tests/test_arch_guard.py::TestDocImplAlignmentGuard`：

- `test_type_count_docs_match_registry`
- `test_vocab_term_count_docs_match_terms`
- `test_ci_step_counts_match_workflows`
- `test_coverage_baseline_matches_scripts_readme`
- `test_docs_readme_process_docs_statement`

## 六、校验命令与输出摘要

| 命令 | 退出码 | 输出摘要 |
|---|---|---|
| `python -m unittest discover -s engine/tests` | 0 | `Ran 1003 tests in 43.922s` / `OK (skipped=4)` |
| `python engine/tools/validate.py` | 0 | `结构与规范校验通过：通用层完整、业务线结构齐全、命名合规` |
| `python engine/tools/generate_registry.py --check` | 0 | `注册表一致：工具 44 · 类型 12 · 主题 21 · 工作流 8` |
| `python engine/tools/coverage_gate.py --porcelain` | 0 | `total_percent 90.35` / `exit_code 0` |
| `python engine/vocabulary/script/vocab_tool.py verify` | 0 | `注册主题 20 个：0 项错误 / 0 项警告` |
| `python -m ruff check engine/tests/test_arch_guard.py` | 0 | `All checks passed!` |
| `python engine/tests/test_arch_guard.py`（模块） | 0 | `Ran 13 tests` / `OK` |

**双轴结论：Standards 无 P0 / P1；Spec 无 P0 / P1（测试数因新增守卫由 998 变 1003，已同步文档并留痕）。**
