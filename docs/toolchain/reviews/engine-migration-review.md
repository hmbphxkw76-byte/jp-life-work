# 引擎层迁移（SRC→ENGINE）· 双轴评审报告

> **任务**：`task/engine-migration-2026-11-60ee5587`
> **评审对象**：`docs/引擎层迁移方案-2026-11-17.md`（v1.1）↔ 本次实现
> **性质**：纯目录 / 路径 / 命名迁移，零行为变更
> **评审时间**：2026-11-17

---

## 一、Standards 轴（是否符合本规约 / 仓库规范）

| 条款 | 结论 | 证据 |
|---|---|---|
| 三层隔离（AGENTS.md） | ✅ | `task start` 建 `task/engine-migration-2026-11-60ee5587` + `.worktrees/engine-migration-2026-11`；全部改动在任务工作树内；合并只走 `merge` |
| 不碰他人改动 | ✅ | 活跃任务 `monthly-update-2026-11` 在独立工作树，未触碰；变更仅限本任务范围 |
| 分支命名 | ✅ | `task/engine-migration-2026-11-60ee5587`（`task/<name>-<sid>`） |
| 工具链开发规约（TOOLCHAIN-DEV-SPEC） | ✅ | 适用对象更新为 `engine/` + `engine/scripts/`；六阶段顺序未变；守卫 `test_toolchain_dev_spec.py` 通过 |
| 命名规范 | ✅ | 目录 kebab-case；无新增 Python 包目录；测试文件 `test_engine_migration.py` snake_case |
| 单一事实源 | ✅ | `_common.py` 为结构识别唯一事实源；`coverage-config.json` 为阈值事实源；生成物由工具重生成 |
| 文档口径 | ✅ | `AGENTS.md` / `docs/**` / 21 主题 `prompts/**` 与 `operations-guide.md` 路径口径统一为 `engine/` |
| 工作区卫生 | ✅ | `cleanup_workspace.py --check` 零残留（收尾复跑） |
| 报告研究内容 | ✅ | `NN-*/reports/**` 零改动；`NN-*/data/**` 仅 3 处路径引用文本（见第四节） |

## 二、Spec 轴（方案条目 ↔ 实现 / 测试映射）

| 方案条目 | 实现 | 验证 |
|---|---|---|
| §3.1 目录映射（8 项） | `git mv`：`src/prompts-tools/tools→engine/tools`、`src/{report_templates,report-audits,search,vocabulary,tests}→engine/`、`src/README.md→engine/README.md`、根 `tools/→engine/scripts/`；删空壳 `src/` | `test_engine_migration.py::TestLayoutTerminalState`；`test -d engine && test ! -d src && test ! -d tools` |
| §3.2 替换顺序 1–6 | 长 → 短字符串替换（代码常量 + 全仓文本） | `test_no_src_path_references` / `test_no_src_string_constant` |
| §3.2 规则 7（根 tools → engine/scripts） | `workflow_guard` / `git_push` / `cleanup_workspace` / `run_tests_parallel` / `branch_naming` / `git-hooks/` / `README` 引用全部改口 | `test_branch_naming` / `test_git_push` / `test_cleanup` / `test_workflow_guard` 通过 |
| §3.2 规则 8（`ROOT / "src"`、`SKIP_TOP`） | `_common.ROOT`/`ENGINE`；`SKIP_TOP` 删 `src` 加 `engine` | `test_skip_top_contains_engine_not_src`；`iter_business_dirs()==21` |
| §3.3 `_common` parents[3]→[2] | `engine/tools/_common.py:13` | `test_common_root` |
| §3.3 coverage_gate / generate_registry / review_gate | parents[3]→[2] | `test_tool_roots` |
| §3.3 migrate_monthly_reports | `parents[2]→parents[1]/"report-audits"` | `test_migrate_audit_dir` |
| §3.3 test_tools.py:24 | `parents[1]/"prompts-tools"/"tools"` → `parents[1]/"tools"` | 全量测试通过 |
| §3.3 test_cov_audit:117 / test_tools:1019/1153/2217 | parents[3]→[2] | 全量测试通过 |
| §3.3 cleanup_workspace / run_tests_parallel | `parent.parent`→`parents[2]`；`parents[1]`→`parents[2]` | `test_script_roots` |
| §3.3 workflow_guard `_find_push_script` / `_run_verify` | `cwd/"engine"/"scripts"/"git_push.py`；`wt/"engine"/"tools"/"validate.py` | `test_find_push_script_*`；`merge` 前置校验可执行 |
| §3.4 `_common` SRC→ENGINE / SKIP_TOP / TYPE_RE | 已改 | `test_skip_top_*` / `test_type_re_*` |
| §3.4 各工具 ROOT 常量（~14 个） | `ROOT/"engine"/...` | 全量测试 + `test_tool_roots` |
| §3.4 根配置 4 项 | `.coveragerc`（source/omit）、`ruff.toml`、`.gitignore`、`coverage-config.json` | `coverage_gate` 92%；`validate.yml` ruff/mypy 路径同步 |
| §3.4 8 工作流 + composite action | 8 条工作流路径改口；`workspace-cleanup` action 指向 `engine/scripts/cleanup_workspace.py` | `generate_registry --check` 工作流 8；YAML 解析守卫 |
| §3.5 不改动项 | 审计台账 / 报告正文 / git 历史未改 | `git diff --stat`（见第三节） |
| §5 路径校验 1–6 | 活引用清零（白名单除外）、`"src"` 清零、目录终态、深度推导、主题数 21、registry 一致 | `test_engine_migration.py` 13 项 |
| §6 全量验证 | 见第三节 | 全绿 |
| §8.2 双路径兼容 | **未启用**（见第四节取舍） | — |
| 附录 B 比对脚本 | `engine/scripts/verify_report_parity.py` + 25 项单测 | `--compare` 退出码 0 |

## 三、合并前检查单（engine/tools/README.md 五项）

| # | 项 | 结果 |
|---|---|---|
| 1 | `python -m unittest discover -s engine/tests` | ✅ `Ran 861 tests — OK (skipped=3)`（基线 844 + 新增守卫 14 + 比对脚本补测 3） |
| 2 | `python engine/tools/validate.py` | ✅ 退出码 0 |
| 3 | 双轴评审 | ✅ 本报告（Standards / Spec 双轴，无 P0/P1） |
| 4 | `python engine/tools/coverage_gate.py` | ✅ 92.0% ≥ 80%（enforce=true） |
| 5 | `python engine/scripts/cleanup_workspace.py --check` | ✅ 零残留 |

**其余门禁**：`classify_reports --check` 0；`ensure_region_topics --check` 0；`build_hub --check` 0；`build_index --check` 0；`lint_reports --new-only` 0；`compliance_check --new-only` 2（仅告警）；`stage_gate_check` 2（P2×1）；`info_quality_check --check` 2（P2×14）；`fact_card_check` 0；`pending_verification --check` 0；`personal_finance_model --check` 0；`vocab_tool topic-check` 0 / `verify` 2（既有告警）；`sync_vocab check` 0；`audit_pipeline --gate` 0；`audit_check --all` 2（P2×16）；`generate_registry --check` 一致（工具 34 · 类型 13 · 主题 21 · 工作流 8）。

**一致性判据**：`python engine/scripts/verify_report_parity.py --compare .migration-baseline` → 退出码 **0**（一致 45 / 仅路径与时间戳 3 / 不匹配 0 / 缺失 0 / 新增 0）。

## 四、残留与取舍（显式登记）

1. **双路径兼容未启用**：方案 §0 列为「建议」，但执行提示词阶段 2 未列入，且它会引入布局探测分支、与「零行为变更」冲突。本次按纯路径迁移落地，靠 §8.3 的 `revert` 兜底；如后续他会话在旧布局上受阻，再单独授权启用。
2. **`src/` 活引用白名单**（`test_engine_migration.py::SRC_WHITELIST`）：
   - `docs/引擎层迁移方案-2026-11-17.md`（本迁移规格书，含旧→新映射表，属历史规格）；
   - `engine/scripts/verify_report_parity.py` 及其单测（映射表本身）；
   - `engine/scripts/README.md`（比对工具说明，描述旧→新映射）。
   除此之外 `git grep "src/"` 与 `git grep '"src"'` 均清零；`NN-*/reports/**` 按 §3.5 保留留痕。
3. **`NN-*/data/**` 3 处路径引用**：`00-decision-hub/data/{fact_cards,five_questions_view,personal_finance_model}.md` 各 1 行，仅为指向 `engine/report_templates/`、`engine/search/`、`engine/tools/` 的引用文本，无研究内容变化；不改则链接失效。已用 `git diff --stat` 核对。
4. **比对脚本两处修正**（附录 B 源码的 latent 缺陷，客观判据必须成立）：
   - `PATH_REWRITES` 的 `tools/` 兜底项会二次命中新路径 `engine/tools/`（→ `engine/engine/scripts/`）；在其之前加入 `engine/tools/`、`engine/scripts/` 恒等映射；
   - 时间戳归一化仅覆盖「构建心跳」，无法覆盖 `INDEX.md` 头部「最近生成：… UTC」与报告行构建时间列，导致误报 MISMATCH；已扩展并补 3 项单测。
5. **`review_gate.SCOPE_DIRS`** 的 `"tools/"` 同步为 `"engine/scripts/"`（方案 §3.4「各工具常量」口径）。
6. **守卫扫描口径修正（合并后 CI 暴露）**：首版守卫用 `git grep`（仅搜已跟踪文件），未覆盖尚未 `add` 的新文件，导致守卫自身与本评审报告中的旧路径字面量漏检——本地绿、CI 红（`validate` 失败一次）。已改为**全量文件扫描**（含未跟踪文件，排除版本库 / 工作树 / 运行期产物 / 报告正文），并补 1 项回归用例 `test_scan_sees_untracked_files`；白名单相应纳入守卫自身与本评审报告。该失败属守卫假阴性，非产品回归，故修复前推而非 revert。

## 五、回滚判据核对（方案 §9）

| 触发条件 | 本次状态 |
|---|---|
| 1 全量 unittest 失败 / 测试数异常减少 | 未命中（860 ≥ 844，无减少） |
| 2 validate 退出码 1 / 门禁阻断 | 未命中（validate 0；门禁均 0 或 2 告警） |
| 3 主题数 ≠ 21 / vocabulary 误判 | 未命中（21，`engine` 在 SKIP_TOP） |
| 4 ROOT 解析异常 | 未命中（`test_tool_roots` / `test_script_roots` / `test_migrate_audit_dir`） |
| 5 生成物与迁移前不一致 | 未命中（parity rc=0） |
| 6 CI 连续 2 次失败 / 覆盖率跌破 | 待合并后观察（覆盖率 92%） |
| 7 合并后 24h 内 `src/` 活引用回潮 | 待观察 |

**结论**：Standards / Spec 双轴均无 P0/P1，五项检查单齐备，满足合并条件。

---

## 六、二次确认缺口收口（2026-11-17 追加）

独立二次确认（全量文件扫描，含未跟踪；非 `git grep`）判定迁移**部分对齐**：A–H 全过，但发现 7 处
「无斜杠前缀」旧路径文本残留，未被原迁移的全局替换覆盖，也未登记于 §四。本次逐条修复并补强守卫：

| # | 位置 | 修复 |
|---|---|---|
| G1 | `docs/toolchain/TOOLCHAIN-DEV-SPEC.md:22` 适用范围表 | 第三项 `tools/` → `engine/scripts/` |
| G2 | `docs/toolchain/TOOLCHAIN-DEV-SPEC.md:66` 覆盖率统计范围 | 第三项 `tools/` → `engine/scripts/` |
| G3 | `engine/tools/review_gate.py` module docstring | 第三项 ``tools/`` → ``engine/scripts/`` |
| G4 | `engine/scripts/cleanup_workspace.py:18` 安全约束 | 删除已不存在的 `src`、`tools` |
| G5 | `engine/tests/test_cov_pipeline.py:8` 运行命令 | `src.tests.` → `engine.tests.` |
| G6 | `docs/mainline融合评估报告-2026-11-17.md:239` | 第三项 `tools/` → `engine/scripts/` |
| G7 | `docs/代码冗余与无效代码清理报告-2026-11-17.md:78` | `compileall -q src tools` → `compileall -q engine` |

**守卫盲区补强**（`engine/tests/test_engine_migration.py`，14 → 16 项）：新增两项全量扫描断言——
裸 `tools/` 目录引用（正则 `(?<![\w/])tools/`）、旧模块路径 `src.<包>`（正则 `src\.(?:tests|prompts|report|search|vocabulary|tools)\b`）。
白名单沿用既有 6 项（映射表 / 规格书 / 评审报告 / 守卫自身），**未纳入任何 G1–G7 文件**；
另设 `TOOLS_TOKEN_EXCLUDE` 仅豁免两处**非旧根 tools/ 引用**的结构性用法（`prompt-generic-base.md` 的
engine/ 子树示意图、`test_cleanup.py` 的合成 fixture），并在代码注释中写明理由。

**收口验证**：`unittest discover -s engine/tests` = **863 OK (skipped=3)**；`validate.py` 退出码 0；
`build_hub --check` / `build_index --check` 均 0；`generate_registry --check` 一致（34/13/21/8）；
`iter_business_dirs()` = 21；生成物 CRLF 归一后逐字节相等；三类扫描（`src/`、`"src"`、裸 `tools/`、`src.<包>`）
白名单外 0 命中；`NN-*/reports/**` 与 `*/handbook/**` 零改动；`docs/CI.md` 测试数同步 861 → 863。

**结论**：缺口全部收口，迁移与方案完全对齐；无行为变更、无生成物漂移。

