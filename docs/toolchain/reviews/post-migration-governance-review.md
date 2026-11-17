# 双轴评审：迁移后全仓治理与清障（post-migration-governance）

> **任务 slug**：post-migration-governance
> **日期**：2026-11-17
> **评审对象**：`task/post-migration-governance-736a856f` 分支全量变更
> **评审人**：CatPaw（独立双轴）
> **基线**：`origin/main` = `3a13f8c`（评审时点，迁移已落地、目录终态达标）；
> 本分支已并入后续 `76d5656`（迁移缺口收口），故下方测试数与计数按合并后 863 项口径复核

---

## 一、Standards 轴（是否符合 AGENTS.md / TOOLCHAIN-DEV-SPEC / 命名 / 退出码 / 测试纪律）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 三层隔离 | ✅ | `workflow_guard.py task start` 建 `task/post-migration-governance-736a856f` + `.worktrees/post-migration-governance`；全部改动在任务工作树内；合并只走 `merge` |
| 分支命名 | ✅ | `task/<slug>-<sid>`，`sid=736a856f`（会话标识前 8 位） |
| 不碰他人改动 | ✅ | 基线 `git status` 干净；仅提交本任务范围内文件 |
| 命名规范 | ✅ | 未新增工具；测试/文档命名不变；代码仅加类型注解与变量重命名 |
| 退出码契约 | ✅ | 未改任何工具退出码逻辑；校验类仍为 0/1/2 |
| 架构边界 | ✅ | `engine/tools/` 无 git 可变操作（仅 `git diff` 只读）；`engine/scripts/` 不产出内容；`_common.SKIP_TOP` 含 `engine` 不含 `src`；`iter_business_dirs()` = 21 |
| 单一事实源 | ✅ | 未新写判定内核；阶段闸仍复用 `info_quality_check` / `compliance_check` / `audit_registry` |
| 测试纪律 | ✅ | 未删测试；`test_engine_migration` / `TestPipelineFlowSpec` 等守卫全绿；新增类型注解未改行为 |
| 生成物纪律 | ✅ | 未手改生成物；`findings-by-path.json` 由 `audit_check --all` 重生成；`index.html` / `INDEX.md` / `search-index.json` 未变更 |
| 报告正文 | ✅ | 未自动改写任何 `*/reports/**` 研究正文；仅工具链代码与文档变更 |

**Standards 结论：无 P0/P1。**

---

## 二、Spec 轴（是否完成验收标准，逐条命令与输出摘要）

### 2.1 目录终态

| 判据 | 命令 | 结果 |
|---|---|---|
| `engine/` 存在；`src/`、根 `tools/`、`src/prompts-tools/` 不存在 | `test -d engine && test ! -d src && test ! -d tools && test ! -d src/prompts-tools && test -d engine/tools && test -d engine/scripts` | `DIR_OK` |
| 主题数 21 | `iter_business_dirs()`（`test_engine_migration`） | 通过 |

### 2.2 全量验证（退出码）

| 命令 | 退出码 | 摘要 |
|---|---|---|
| `python -m unittest discover -s engine/tests -v` | 0 | `Ran 863 tests ... OK (skipped=3)` |
| `python engine/tools/validate.py` | 0 | 结构与规范校验通过 |
| `classify_reports.py --check --unknown-warn` | 0 | 无错位报告 |
| `ensure_region_topics.py --check` | 0 | 结构齐全 |
| `build_hub.py --check` | 0 | index.html 最新 |
| `build_index.py --check` | 0 | 22 份报告一致 |
| `lint_reports.py --new-only` | 0 | 22 份合格 |
| `compliance_check.py --new-only` | 2 | 2 项警告（h2 超骨架），无错误 |
| `stage_gate_check.py` | 2 | 21 主题全过；P0 0 / P1 0 / P2 1 |
| `info_quality_check.py --check` | 2 | P0 0 / P1 0 / P2 14 |
| `fact_card_check.py` | 0 | P0/P1 0 |
| `pending_verification.py --check` | 0 | 进行中项未逾期 |
| `personal_finance_model.py --check` | 0 | 一致 |
| `vocab_tool.py topic-check` / `verify` | 0 / 2 | 0 错误；1 警告（LAW-082 别名重复） |
| `sync_vocab.py check` | 0 | 区间一致 |
| `coverage_gate.py` | 0 | 92.0%（阈值 80%，enforce=true） |
| `audit_pipeline.py --gate` | 0 | 台账 459 条；受检 0；通过 |
| `audit_check.py --all` | 2 | 22 份全过；P0 0 / P1 0 / P2 16 |
| `generate_registry.py --check` | 0 | 工具 34 / 类型 13 / 主题 21 / 工作流 8 |
| `cleanup_workspace.py --check` | 0 | 零残留 |
| `python -m mypy engine/tools engine/vocabulary/script` | 0 | 37 → 0（本轮修复） |
| `python -m ruff check engine` | 135 项（存量） | 与基线 135 一致，**无新增** |

### 2.3 活引用清零

| 判据 | 结果 |
|---|---|
| `git grep "src/"`（排除台账 / 报告正文） | 仅白名单 6 项（迁移方案 / 比对脚本及其测试 / scripts README / 迁移守卫 / 迁移评审） |
| `git grep "prompts-tools"` | 同上白名单 |
| `git grep '"src"'` | 同上白名单 |
| `test_engine_migration.TestNoLiveSrcReferences` | 通过 |

### 2.4 CI/CD 8 条工作流

| 工作流 | 结论 |
|---|---|
| `validate.yml` | `fetch-depth: 0`、契约测试、14 步校验、覆盖率 job、`workspace-hygiene` 自检、前置 + 收尾清理齐备 |
| `html-sync.yml` | md2html → build_hub → `--sync` → `--rebind` → badge `--sync` → record → 提交；权限 `contents: write` |
| `scheduled-maintenance.yml` | 归位 / 补全 / 归档 / 索引 / HTML / 汇总页 / 决策件套 / 审计失效 / 标识 / 回归 / 状态 / 提交；失败补记 |
| `scheduled-report-tasks.yml` | 清单 + Issue 去重 + 状态提交；不产出正文 |
| `info-quality.yml` | `--apply` → md2html → unittest → P0/P1 告警 → record → 提交 |
| `audit-gate.yml` | `--gate` + `audit_check --all` + `review_gate --changed`；PR 限定 main |
| `audit-sampling.yml` | `--apply` + badge `--sync` + record + 提交（含 `audit/`） |
| `pipeline-orchestrator.yml` | 触发检测 → S0→S2 → 监控视图 → Issue；**不含** md2html / auto_verify / audit_pipeline |

**Spec 结论：无 P0/P1。**

---

## 三、变更清单（文件 ↔ 规范条款 ↔ 测试）

| 文件 | 变更 | 规范条款 | 测试 |
|---|---|---|---|
| `docs/README.md` | 补索引、版本记录、863 计数 | docs/README 维护规则 | `test_engine_migration`（白名单口径） |
| `engine/README.md` | 索引补 scripts/README、coverage-config | engine/README 第五节 | — |
| `engine/tools/README.md` | 断链修复、863 / 8 计数 | TOOLCHAIN-DEV-SPEC 第四节 | `test_arch_guard`（工具表） |
| `engine/report-audits/README.md` | 第三节改「CI 接线对照」 | 审计留痕分层 | — |
| `docs/CI.md` / `信息生产全链路执行规范.md` / `信息质量评估提示词体系.md` / `引擎层迁移方案` / `cross-domain-expert-roles.md` / `mainline融合评估报告` / `TOOLCHAIN-DEV-SPEC.md` | 头部版本 / 计数 / 旧路径口径 | 各文档维护规则 | `test_arch_guard`、`test_audit_spec_version_matches_standard_doc` |
| `engine/scripts/cleanup_workspace.py` / `engine/tools/review_gate.py` | docstring 旧路径 | 架构边界 | — |
| `engine/tools/{md2html,incremental_build,stage_gate_check,audit_check,audit_preflight,audit_badge,audit_pipeline,migrate_monthly_reports,info_quality_check}.py`、`engine/vocabulary/script/vocab_tool.py` | 类型注解 / 变量重命名（零行为变更） | TOOLCHAIN-DEV-SPEC 第五节 | 全量 863 + mypy 0 |
| 删除 `docs/toolchain/implementation-confirmation-2026-11-17.md`、`docs/模板合规校验报告-2026-11-16.md` | 无入链一次性留痕 | docs/README 维护规则 | 用户确认（2026-11-17） |

---

## 四、残余风险与 P2 挂账

| # | 项 | 原因 | 复核日期 |
|---|---|---|---|
| P2-1 | 《审计报告标准化管理体系》头部 v1.4 与版本记录 v1.5 不一致 | `audit_registry.SPEC_VERSION=v1.4` 被登记册 / 标识引用，bump 会触发全量徽章重写与审计失效；须与标识体系协同升级 | 2026-12-17 |
| P2-2 | ruff 存量 135 项 | `ruff.toml` 明确「warning 起步，CI 不阻断存量」；自动修复含 unsafe 项，行为风险高 | 2026-12-17 |
| P2-3 | `engine/report-audits/info-quality/findings-by-path.json` 为运行缓存但仍跟踪 | README 标注「建议 .gitignore」；取消跟踪需确认缓存再生路径 | 2026-12-17 |
| P2-4 | `audit_check --all` P2 16 项 | 存量报告历史遗留，已挂 `pending-p2.json` | 2026-12-17 |
| P2-5 | `info_quality_check --check` P2 14 项 | 存量内容质量遗留 | 2026-12-17 |
| P2-6 | `compliance_check --new-only` 2 项警告 | h2 节数超骨架（业务固化锚候选） | 2026-12-17 |
| P2-7 | `vocab_tool verify` 1 项警告 | `politics-law` LAW-082 别名「诬告」与自身重复 | 2026-12-17 |

---

## 五、结论

- **Standards 轴**：无 P0/P1。
- **Spec 轴**：本任务验收标准全部满足；全量验证退出码均在 {0,2}，无 P0/P1；mypy 由 37 → 0，ruff 无新增。
- **可进入 S6 合并前检查单**。

## 版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-17 | 初始双轴评审：Standards / Spec 结论、验证证据、P2 挂账 |
| v1.1 | 2026-11-17 | 合并收口 | 并入 `origin/main` 76d5656（迁移缺口收口）后复核：测试数 861 → 863，计数口径同步；冲突按「保留缺口收口修复 + 版本记录续编 v2.6」解决 |
