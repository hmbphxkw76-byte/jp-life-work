# 无法核实内容硬门禁 · 双轴评审（verified-content-gate，2026-11-21）

> **范围**：`task/verified-content-gate-fdb54479` worktree（`D:\文档\GitHub\jp-life-work\.worktrees\verified-content-gate`）。
> **基线**：`origin/main`；改动含工具链（`engine/tools/` + `engine/config/` + `engine/tests/` + `.github/workflows/`）与内容层清理（`*/reports/*.md`、`*/data/*.md`、`terms.md`）。
> **口径**：只审本任务范围；判定口径单一事实源为 `engine/config/verified-content-policy.json`；不编造。
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**。残留为 2 条预期失败（分支领先 main 的 `incremental_build` 断言）。

---

## 一、改动清单

| 类别 | 文件 | 改动 |
|---|---|---|
| 工具 | `engine/tools/verified_content_gate.py` | 新增（内容层零容忍硬门禁；策略驱动；退出码 0/1/2） |
| 配置 | `engine/config/verified-content-policy.json` | 新增（markers / record_sections / status_columns / excluded_files / excluded_lines） |
| 测试 | `engine/tests/test_verified_content_gate.py` | 新增 15 项（策略加载 / 内容命中 / 记录层豁免 / 状态列豁免 / 行级豁免 / 退出码） |
| CI | `.github/workflows/validate.yml` | 增「无法核实内容门禁」步骤（主 job 30 → 31 个命名步骤） |
| CI | `.github/workflows/audit-gate.yml` | 增全库兜底步骤（7 → 8 步） |
| 注册 | `engine/tools/registry.json`、`engine/tools/README.md` | 工具 47 → 48；测试计数 1095 → 1110 |
| 文档 | `docs/CI.md`、`docs/README.md`、`docs/信息生产全链路执行规范.md`、`docs/cross-domain-expert-roles.md`、`docs/提示词库体系.md` | 版本 / 步骤数 / 工具数 / 测试数 / 词条数对齐 |
| 内容 | 20 份报告 + 00 data + 07 登记册 + 2 份 `terms.md` | 清除内容层无法核实内容（命中 105 → 0） |
| 派生 | `*/reports/*.html`、`index.html`、`search-index.json`、`00/data/personal_finance_model.md` | 重新生成 |

---

## 二、轴一：Standards（规范符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| AGENTS.md 硬性规约二：分支 / worktree / 不直推 main / 串行合并 | ✅ | 全程在 `.worktrees/verified-content-gate`；未直推；合并走 `workflow_guard.py merge` |
| 工具链开发规约：规格先行 / TDD / 双轴评审 / 合并前检查单 | ✅ | 先策略 + 工具 + 15 项测试，再接入 CI；本评审为双轴评审 |
| 退出码约定 0/1/2 | ✅ | 工具退出码 0（通过）/ 1（命中阻断）/ 2（`--warn`）；CI 显式判 1 阻断 |
| 单一事实源 | ✅ | 判定规则全部读 `verified-content-policy.json`，不硬编码；与 `confidence-grade-standard.md`「待核实」定义一致 |
| 跨平台 / 静态检查 | ✅ | 无 `shell=True`；正斜杠路径；`ruff` / `mypy` 通过 |
| 文档↔实现对齐守卫 | ✅ | `test_arch_guard` 16 项通过（工具 48 / 测试 1110 / 步骤数 / 词条 1518） |
| 工具注册表一致性 | ✅ | `generate_registry.py --check` 通过（工具 48） |

**Standards 结论：无 P0 / P1。**

---

## 三、轴二：Spec（任务验收映射）

| 任务 | 验收标准 | 实现 | 证据 |
|---|---|---|---|
| 内容层阻断 | 内容层出现即阻断 | ✅ | `--all` 命中 105 → 清理后 0；退出码 1 |
| 零容忍 | 无告警放行路径（除 `--warn` 显式） | ✅ | 默认退出码 1；CI 判 1 即失败 |
| 全部范围 | 报告 / 手册 / 登记册 / 词库 / 00 data | ✅ | `iter_targets()` 覆盖 144 份受检文件 |
| 一次性处理 | 不设存量豁免 / 不分阶段 | ✅ | 一次性清理至 0 命中后启用门禁 |
| 未通过不得产出 | 生成阶段前置 + 合并兜底 | ✅ | `validate.yml`（PR）+ `audit-gate.yml`（全库）双拦截 |
| 记录层放行 | 置信度表 / 信息差清单 / 待复核清单 / 状态列 / 来源清单 | ✅ | 策略 `record_sections` + `status_columns` + `excluded_lines`；15 项测试覆盖 |
| 回归 | 全量契约测试 | ✅ | 1110 项，2 项为分支领先 main 的预期失败（`incremental_build`） |

**Spec 结论：无 P0 / P1。**

---

## 四、关键发现（Findings）

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| 1 | 观察 | 「内容层 vs 记录层」需机读边界：标记词在置信度表 / 信息差清单 / 核验状态列中大量出现，若全判会把诚实状态记录一并阻断 | 策略用「章节级 record_sections + 表格状态列 + 行级 excluded_lines」三重豁免；已在 `verified-content-policy.json` 单一事实源定义 |
| 2 | P2（既有） | 17 登记册核心指标 12 → 11（删中国侧 #1 后重编号），`decision-tools.json` 的 `intermediary` 源引用失效 | 已改为 #11；`personal_finance_model` 重生成 |
| 3 | P2（有意减项） | 事实卡片 FC-007（生活成本「手册估算」）删除后卡片 16 → 15 | `test_tools.py::test_cards_five_fields` 下限 16 → 15（注明有意减项） |
| 4 | 既有遗留 | `提示词库体系.md` / `cross-domain-expert-roles.md` 词条数 1612 未随上一专项（删 94 条）更新 | 本次一并对齐为 1518 |
| 5 | 预期失败 | `test_incremental_build` 两项断言分支领先 main 时失败 | CI.md 已注明「合并后通过」；非本任务缺陷 |
| 6 | P2（既有遗留） | `origin/main` 既有 1 项 ruff（`test_tools.py` 未用导入）+ 4 项 mypy（`info_quality_check` / `decision_metrics` 多余 `type: ignore`、`audit_preflight` 变量遮蔽致类型误判），会挡 CI 静态检查 | 一并修复：删未用导入、删多余 ignore、`audit_preflight` 循环变量 `missing` → `vals`；`ruff` / `mypy` 复跑均 0 |

---

## 五、回归校验（实测退出码）

| 命令 | 结果 | 退出码 |
|---|---|---|
| `verified_content_gate.py --all` | 受检 144 份，命中 0 | **0** |
| `validate.py` | 结构与规范校验通过 | **0** |
| `lint_reports.py` | 21 份报告全部合格 | **0** |
| `md_html_parity.py` | 无漂移 | **0** |
| `audit_preflight.py --all` | 通过 21 / 21 | **0** |
| `audit_check.py --all` | 通过 21 / 21（P0/P1 = 0） | **0** |
| `auto_verify.py --all`（V1–V5） | 21 份全部通过 | **0** |
| `audit_pipeline.py --verify` / `--gate` | 哈希链完整 / 门禁通过 | **0** |
| `unittest discover` | 1110 项，2 项预期失败 | — |
| `ruff` / `mypy` | 通过 | **0** |

---

## 六、结论

- **Standards**：无 P0 / P1。
- **Spec**：无 P0 / P1；内容层阻断 / 零容忍 / 全部范围 / 一次性处理 / 生成前置 + 合并兜底全部达成。
- 残留：2 项预期失败（分支领先 main）+ 若干记录层状态值（按设计保留）。
- 双轴均无 P0/P1，可进入合并前检查单（S6）。
