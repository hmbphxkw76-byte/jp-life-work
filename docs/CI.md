# CI 与自动化体系

> **版本**：v2.33（2026-11-22 合并 PR 化 + main 分支保护）
> 本文档说明 jp-life-work 报告管理体系的持续集成（CI）与定时自动化。
> 代码位置：`.github/workflows/`（8 条工作流）；工具链：`engine/tools/`；测试：`engine/tests/`。

## 一、总览

本体系的**目标**：让「报告源文件 → 交付物」的生成始终一致，规范不退化，变更可追溯。

| 关注点 | 由谁保障 |
|---|---|
| 报告命名 / 结构 / 配对规范 | `validate.yml`（阻断） |
| md → HTML、汇总页 | `html-sync.yml`（push 触发） |
| 归档 / 索引 / 结构维护 | `scheduled-maintenance.yml`（每月 1 日） |
| 月度产出待办提醒 | `scheduled-report-tasks.yml`（每月 1 日） |
| 内容零丢失 / 对比准确性 | `engine/tests/test_tools.py` |
| 信息质量评估 / 混乱修复 | `info-quality.yml`（每周一 02:20 UTC） |
| 审计门禁（登记册 / 台账 / 标识 / L1–L5） | `audit-gate.yml`（阻断） |
| 决策支持件套（参数 / 一页纸 / 财务模型 / 事实卡片 / 待核实闭环） | `validate.yml`（复用门禁）+ `scheduled-maintenance.yml`（刷新） |
| 流程复用一致性 | `engine/tests/test_tools.py::TestProcessReuse` |
| 阶段出口质量（采集 / 筛选 / 分类左移） | `validate.yml`（`stage_gate_check.py`） |
| 触发检测 / 编排状态（S0→S2） | `pipeline-orchestrator.yml`（每月 1 日 01:45 UTC） |
| 生成 / 发布前信息核验（闸0 + 无法核实内容） | `.github/actions/content-verify`（接入 `pipeline-orchestrator.yml` / `html-sync.yml`） |
| 工具链覆盖率 / 双轴评审 | `validate.yml`（`coverage_gate.py`）/ `audit-gate.yml`（`review_gate.py`） |

**CI 不产出报告研究内容**——报告由各主题 `prompts/business-config.md` 定义的研究流程人工/Agent 产出；CI 只校验与同步生成物。

## 二、工作流清单

### 1. `validate.yml` — 质量门禁（阻断式）

- **触发**：`push` 到 main、pull_request（main 方向）
- **权限**：`contents: read`
- **checkout**：`fetch-depth: 0`（必须完整历史——迁移内容复核需取旧文件）

| 步骤 | 命令 | 失败后果 |
|---|---|---|
| 缓存 pip 依赖 | `actions/cache@v4`（key 随 requirements 哈希） | 未命中仅降速，不阻断 |
| 契约测试（分片 job） | `run_tests_parallel.py --shard <i>/4`（4 片并行） | 阻断（任一片失败） |
| 结构与规范校验 | `validate.py` | 阻断 |
| 报告自动归位检查 | `classify_reports.py --check --unknown-warn` | 阻断 |
| 结构补全检查 | `ensure_region_topics.py --check` | 阻断 |
| 汇总页一致性校验 | `build_hub.py --check` | 阻断 |
| 全局索引一致性校验 | `build_index.py --check` | 阻断 |
| 内链存在性校验 | `link_check.py` | 阻断 |
| 工具注册表一致性 | `generate_registry.py --check` | 阻断 |
| 报告登记册一致性 | `audit_registry.py --check` | 阻断 |
| 落盘前自检 | `audit_preflight.py --all` | 阻断（P0/P1） |
| 报告必需要素结构校验 | `structure_check.py` | 阻断（要素缺失） |
| md↔HTML 一致性校验 | `md_html_parity.py` | 阻断（漂移 / 缺失） |
| 提示词结构门禁 | `prompt_check.py` | 阻断（命名 / 继承 / 结构 / 槽位） |
| 来源语言门禁 | `source_language_gate.py --changed` | 阻断（规则不一致 / 中文来源许可 / 变更报告中文域名） |
| 无法核实内容门禁 | `verified_content_gate.py --all` | 阻断（内容层含待核实 / 未核实 / 需核实原文 / 待核验 / 待补来源） |
| 决策度量校验 | `decision_metrics.py --check` | 阻断（解析失败） |
| 来源条目 schema 校验 | `source_check.py` | 阻断（来源章节缺失） |
| 反例扫描 | `counterexample_scan.py` | 阻断（扫描失败；候选放行） |
| 报告内容 lint | `lint_reports.py --new-only` | 阻断（新报告；退出码 1） |
| 模板合规校验 | `compliance_check.py --new-only` | 阻断（新报告；退出码 1） |
| 阶段闸检查 | `stage_gate_check.py`（采集 / 筛选 / 分类） | 阻断（P0/P1） |
| 生成前信息核验 | `generation_gate.py --all` | 阻断（P0/P1；闸0） |
| 信息质量全量检查 | `info_quality_check.py --check` | 阻断（P0/P1） |
| 事实卡片校验 | `fact_card_check.py` | 阻断（P0/P1） |
| 待核实闭环检查 | `pending_verification.py --check` | 阻断（未登记 / 逾期） |
| 个人财务模型一致性 | `personal_finance_model.py --check` | 阻断（缺失 / 过期） |
| 词库校验 | `vocab_tool.py topic-check` / `verify` + `sync_vocab.py check` + `vocab_near_check.py` | 阻断 |
| 决策日志校验 | `decision_log.py --check` | 阻断（日志缺失 / 结构损坏；暂无记录仅告警） |
| 安装开发依赖 | `pip install -r requirements-dev.lock` | 失败即阻断 |
| ruff 静态检查 | `python -m ruff check engine` | 阻断（W2 起） |
| mypy 静态检查 | `python -m mypy engine/tools engine/vocabulary/script engine/scripts` | 阻断 |
| 一次性工具冒烟 | 8 个一次性工具 `--help` | 阻断 |
| 覆盖率门禁（附加 job） | `coverage_gate.py`（阈值读 `coverage-config.json`） | 阻断（enforce=true 未达标 / 测试失败） |
| 工作区卫生自检（附加 job） | `cleanup_workspace.py --check` | 阻断（存在残留） |

> 实测（2026-11-22，生成前信息核验任务）：主 job **32 个命名步骤**（不含通用「安装依赖」，含「安装开发依赖」；主 job 实际共 33 个 `- name:` 步骤）+ **3 个附加 job**（契约测试分片 / 覆盖率 / 工作区卫生）；契约测试已拆为独立 4 分片 job，`ruff` 与 `mypy` 为主 job 内静态检查步骤。集成合并后如步骤数变化，以实测为准并更新本表。

> 通用改造（W2 / R5 / R1 / R7，2026-11-19）：8 条工作流均已接入 `actions/cache@v4` pip 缓存（key 随 `requirements*.txt` 哈希）并补齐 `timeout-minutes`；5 条定时工作流（maintenance / audit-sampling / info-quality / scheduled-report-tasks / pipeline-orchestrator）提交改为推自动分支 + 开 PR（`[automated]` 标记，保留 `github-actions[bot]` 提交身份）；月度 cron 错峰至 00:15 / 00:45 / 01:15 / 01:45（间隔 ≥ 30 分钟）；契约测试由 `run_tests_parallel.py` 分 4 片并行。

> 两个关卡对期间 >= 2026-11 的**新报告**阻断；历史报告由 `--new-only` 跳过，
> 遗留项列入 `engine/report-audits/audit/lint-whitelist.json` 豁免（逾期恢复阻断）。

### 2. `html-sync.yml` — 生成物同步

- **触发**：push（`**/reports/*.md`、`build_hub.py`、`md2html.py`、`report_diff.py`、`topics.json`、`template-registry.md`、词库 `terms.md`、`engine/search/**` 变更）、手动
- **步骤**：
  1. 生成 / 发布前信息核验（`.github/actions/content-verify`：闸0 + 无法核实内容硬门禁）
  2. `md2html.py` — 重新生成同名自包含 HTML（含构建期跨月对比高亮）
  3. `build_hub.py` — 重建 `index.html` 与 `search-index.json`
  4. `audit_pipeline.py --sync` — 指纹失配 → `stale`
  5. `audit_pipeline.py --rebind` — 渲染漂移重绑
  6. `audit_badge.py --sync` — 标识同步
  7. `automation_status.py record` — 记录执行状态
  8. 提交并推送（无变更则跳过）

### 3. `scheduled-maintenance.yml` — 每月定时维护

- **触发**：`cron: "15 0 1 * *"`（每月 1 日 00:15 UTC = 09:15 JST）、手动
- **步骤**（均幂等）：

| 步骤 | 命令 | 作用 |
|---|---|---|
| 归位 | `classify_reports.py --apply` | 移动错位报告到所属主题 |
| 补全 | `ensure_region_topics.py` | 补齐缺失的主题结构 |
| 归档 | `archive_reports.py` | 按周期保留近 18 / 24 / 60 个自然月，超出移入 `reports/archives/` |
| 索引 | `build_index.py` | 生成 `INDEX.md`（含活跃度心跳时间戳）；PR 阶段由 `build_index.py --check` 校验一致 |
| 报告 HTML | `md2html.py` | 同步报告页（含跨月对比高亮） |
| 汇总页 | `build_hub.py` | 重建 `index.html` |
| 财务模型 | `personal_finance_model.py` | 刷新个人财务模型 |
| 待核实闭环 | `pending_verification.py` | 刷新待核实闭环 |
| 事实卡片 | `fact_card_check.py --write` | 刷新事实卡片校验报告 |
| 决策度量快照 | `decision_metrics.py --history` | 追加一条指标序列，供跨月趋势对比 |
| L5 证据元评估 | `l5_meta_check.py` | 刷新 L5 证据元评估（不入库，供人工查阅） |
| 反例扫描 | `counterexample_scan.py` | 刷新反例扫描清单（不入库，供人工查阅） |
| 审计失效 | `audit_pipeline.py --sync` | 指纹失配 → `stale` |
| 标识同步 | `audit_badge.py --sync` | 有效注入 / 失效撤销 |
| 全量自动验证 | `auto_verify.py --all --dry-run` | V1–V5 逐报告校验；P0/P1 即失败（只写 gitignored 运行日志） |
| 回归 | `unittest` | 确认维护未破坏契约 |
| 自动化状态 | `automation_status.py record` | 记录维护执行状态（`if: always()`） |
| 提交 | `git commit` + `git push` | 有变更才提交 |
| 自动化状态失败补记 | `git add -A -- automation-status.json` → `commit` + `push`（`if: always()`） | job 失败时主提交跳过，本步骤仍把本轮状态入库，避免「记录了却因未提交而丢失」 |

> 实测（2026-11-20，main @`ff19ac8`）：共 **22 步**（不含通用「安装依赖」），含 `auto_verify.py --all --dry-run` / `decision_metrics.py --history` / `l5_meta_check.py` / `counterexample_scan.py`；定时任务提交已改为推分支 + 开 PR（W2 / R1）。

- **退出码约定**：`0` 通过；`1` 错误（阻断）；`2` 警告（放行）。
- **核验日志策略（N6）**：`auto_verify.py --all --dry-run` 逐报告写
  `engine/report-audits/audit/verify/<slug>.json`（21 份；维护流水线另写 `auto-verify-all.json` 汇总）。
  该目录由 `.gitignore` 第 23 行排除，属**运行期产物、不入库**；CI 只保证可重跑生成，
  排查时取日志，不做提交。策略变更需同步 `engine/report-audits/README.md` 与本文。
- **活跃度预警**：`automation_status.py activity --threshold 45` 为**手动 / 按需入口**（见第七节），
  不纳入自动门禁；自动侧只保证各工作流 `record` 入库，供人工判断节拍是否断档。

### 4. `scheduled-report-tasks.yml` — 月度产出提醒

- **触发**：`cron: "45 0 1 * *"`（每月 1 日 00:45 UTC）、手动（可指定 `period`）
- **步骤**：
  1. `update_planner.py --period <YYYY-MM>` 生成当月任务清单
  2. 用 `gh issue create` 开「【月度报告产出】YYYY-MM 任务清单」Issue
  3. `automation_status.py record` — 记录执行状态并提交状态文件
- **去重**：先 `gh issue list --state open --search "in:title 【月度报告产出】<period>"`；
  命中则 `gh issue edit` 更新正文并退出，否则新建。
- **只提醒、不写内容**：Issue 仅列待办，报告仍需人工/Agent 产出。
- **00 节点 + 审计提醒**：`update_planner.py` 纳入无 `prompt-*.md` 但已建 `business-config.md` 的主题（`00-decision-hub`），
  逐条标注审计状态并汇总未审计报告；提交前须完成 `audit_preflight → audit_check → audit_pipeline --submit`。

### 5. `info-quality.yml` — 信息质量周期评估与闭环修复

- **触发**：`cron: "20 2 * * 1"`（每周一 02:20 UTC = 11:20 JST）、手动
- **规范**：`docs/信息质量评估提示词体系.md`
- **步骤**：
  1. `info_quality_check.py --apply` — 全量评估 → 混乱识别分类 → 自动修复 → 复评验证（退出码 0/1/2）
  2. `md2html.py` — 同步被修复报告的 HTML
  3. `unittest` — 含文档↔程序一致性校验
  4. 存在 P0/P1 遗留时 `::error::` 告警（退出码 1）
  5. `automation_status.py record` — 记录执行状态
  6. 提交三清单（无变更则跳过）
- **产物**：`engine/report-audits/info-quality/`（评估台账 / 修复台账 / 验证报告 / 累计修复历史 / JSON）
- **留存策略（N5）**：该目录**不纳入 `.gitignore`**，三清单（`assessment-ledger.md` /
  `repair-ledger.md` / `verification-report.md`）与人工维护的 `rules-notes.md` 随提交留存；
  `info-quality.yml` 每次运行 `--apply` 重写，`git status` 出现漂移即提交，不做运行期清理。
  `findings-by-path.json` 为 `audit_check` 的内容哈希缓存（键含全部 md 指纹），随内容变更刷新。

### 6. `audit-gate.yml` — 审计门禁（阻断式）

- **触发**：`push` 到 main、`pull_request`（main 方向，与 `validate.yml` 同口径）
- **步骤与阻断条件**：

| 步骤 | 命令 | 失败后果 |
|---|---|---|
| 合并门禁（统一入口） | `audit_pipeline.py --gate`（`--changed` 增量 / `--strict` 全库） | 阻断（退出码 1） |
| 全库审计兜底 | `audit_pipeline.py --gate --strict` | 阻断（存量报告未通过审计） |
| L5 证据元评估 | `l5_meta_check.py --check` | 阻断（覆盖缺口 / 无效证据 / basis 缺失） |
| 多层级校验 | `audit_check.py --all` | 存在 P0/P1 阻断；仅 P2 放行 |
| 无法核实内容门禁 | `verified_content_gate.py --all` | 阻断（内容层无法核实内容） |
| 工具链双轴评审软门禁 | `review_gate.py --changed .changed-files` | 软门禁（缺评审告警，不阻断） |

> 实测（2026-11-21，无法核实内容门禁任务）：共 **8 步**（不含通用「安装依赖」，含 pip 缓存准备）。

- **合并门禁覆盖**：`--gate` 一次完成台账哈希链、登记册双向一致、已审计标识一致、受检报告审计状态（`audited` + md/HTML 指纹匹配 + 有效 L5 证据）；PR 默认只查本次变更报告，`--strict` 查全库。
- **L5 证据门禁**：`audited` 报告必须附有效 L5 语义复核证据（`re_review --evidence` 或一次性 `--backfill-l5`），缺失即 `L5-EVIDENCE`（P1）阻断。
- **信息质量新标准**（2026-11-15 起）：C-03 跨文档重复按相似度 ≥ 80%；C-07 事实单元含表格行、纯交叉引用括号不计；C-08 读登记册字段化日期；C-10 按登记册 Schema 分支；C-13 报告↔登记册数值一致性；C-14 ④/⑤ 级来源强制核验标注。

- **配套（与提示词 / AGENTS 同一口径）**：交付与审计协议 = HTML 生成（`md2html.py`）→ 落盘前自检（`audit_preflight`）→ 多层级校验（`audit_check`）→ 提交审计（`audit_pipeline --submit`）；未通过自检 / 校验 / 初审的报告不得合并。

### 7. `audit-sampling.yml` — 月度分层抽检

- **触发**：`cron: "15 1 1 * *"`（每月 1 日 01:15 UTC = 10:15 JST）、手动
- **步骤**：
  1. `audit_sampling.py --apply`（分层抽样：每主题至少 1 份、总数 ≥ 20%，逐期轮换；命中 P0/P1 自动置 `stale`）
  2. `audit_badge.py --sync`（撤销不合格报告的「已审计」标识）
  3. `automation_status.py record`（记录执行状态）
  4. 提交抽检报告与审计状态
- **门槛**：结构合规率 = 100%、要素完整率 ≥ 95%、状态一致率 = 100%、抽检合格率 ≥ 95%、P0/P1 = 0
- **不合格**：命中 P0/P1 → `::error::` 告警 + 自动置 `stale`（`sampling_fail`）+ 撤销标识，报告重走 `submit → 初审 → 复核 → 终审`

### 8. `pipeline-orchestrator.yml` — 端到端流水线编排（检测 + 计划）

- **触发**：`cron: "45 1 1 * *"`（每月 1 日 01:45 UTC = 10:45 JST，与 00:15 / 00:45 / 01:15 错开 ≥ 30 分钟）、手动（可指定 `--period`）
- **步骤**：
  1. 生成前信息核验（`.github/actions/content-verify`：闸0 + 无法核实内容硬门禁）
  2. `trigger_watch.py --apply`（派生 watchlist + freshness + 候选线索，写 `trigger-watch.json`）
  3. `pipeline_runner.py run`（S0 检测 → S1 计划 → **S2 人工闸门自动暂停**，不产出正文）
  4. `pipeline_status.py`（生成统一监控视图 `status.md` / `status.json`）
  5. 候选命中时开提醒 Issue（去重：当期已存在则更新正文）
  6. `automation_status.py record --phase pipeline` + 提交 `engine/report-audits/pipeline/**`
- **纪律**：**不含任何撰写步骤**；不跑 S3–S5 本地生成（由 `html-sync` / `validate` / `audit-gate` 承担）
- **退出码**：`pipeline_runner run` 0 = 正常（含 S2 暂停）；1 = 阶段失败 / 状态损坏；2 = 参数错误

### 9. 设计内不接线工具清单（B6）

以下工具**设计内不接入定时流水线**，仅冒烟 / 手动 / 触发依赖；列此清单消除「应接未接」歧义，
不改变现有接线决策。与 `engine/tools/README.md`「设计内不接线工具清单」同口径。

| 工具 | 现状 | 不接线理由 | 复核日期 |
|---|---|---|---|
| `incremental_build.py` | POC / 手动（含 `--bench`）；仅 `validate.yml` 一次性冒烟（`--help`） | N12 决策不切生产默认；切默认触发条件未满足（见第十四节） | 2026-12-19 |
| `migrate_monthly_reports.py` | 一次性迁移，已完成；仅冒烟 | 存量报告合并重命名已完成，无周期触发需求 | 2026-12-19 |
| `skeleton_builder.py` | 手动 / 按需（生成期）；仅冒烟 | 按需入口，无周期触发需求 | 2026-12-19 |
| `report_diff.py` | 触发依赖：`html-sync.yml` 路径过滤器 + `md2html.py` 构建期依赖；无独立校验步骤 | 纯函数依赖，已由 `md2html` / `md_html_parity` 覆盖，不单独设步骤 | 2026-12-19 |

## 三、报告生命周期

```
人工/Agent 按 prompts/ 流程产出
        │
        ▼
reports/YYYY-MM-<slug>.md  ──md2html.py──►  reports/YYYY-MM-<slug>.html
        │                                            │
        │                                            ▼
        │                              独立报告页（hero + report-nav
        │                              + 构建期跨月对比高亮 + 返回链接）
        │                                            │
        └──────────────build_hub.py──────────────────┘
                              │
                              ▼
        index.html（主题索引：卡片 + 详情页，报告链接新标签页直达独立报告页）
                              │
                    归档：按周期保留近 18 / 24 / 60 个自然月
```

## 四、命名与分类规范

- **命名**：`YYYY-MM-<主题slug>.md` + 同名 `.html`；slug = 目录名去 `NN-` 前缀（`01-ssw-driver` → `ssw-driver`）。
- **分类**：取消基线 / 初析 / 季度等类型标签，全部按**自然月**聚合。
- **季度报告**：按季度末月归档（`2026-Q4` → `2026-12`），与月度报告同一套命名 / 对比 / 展示逻辑。
- **同月合并**：同一主题同一自然月多份存量报告合并为一份（初析为主体、基线作附录，原文不删改）。
- **展示**：单主题报告列表默认展示最近 **12 个自然月**，按时间倒序（最新在顶端），可展开更早。

## 五、跨月对比高亮（独立报告页）

- **机制**：每期报告与上一期（同主题、最近一个更早自然月）做 block 级 LCS 比对（`report_diff.py`），在 `md2html.py` 构建期预渲染进报告页。
- **标记**：
  - 新增 → 绿色 + 「已更新 · 新增」
  - 修改 → 黄色 + 「已更新 · 修改」（带相似度阈值 0.35，低相似度按「删除 + 新增」处理）
  - 删除 → 折叠组（默认收起，可展开追溯）+ 「已更新 · 删除」
  - 未变更 → 原样展示
  - 表格整体成块比对，保留完整表格结构
- **辅助开关**：报告页工具条「隐藏更新标记」对照阅读、「展开全部删除」。
- **呈现**：报告页新标签页独立打开，页脚提供「← 返回主题 / 返回首页」。

## 六、测试体系（`engine/tests/`，1171 项）

| 场景 | 测试类 | 覆盖 |
|---|---|---|
| 命名格式合规性 | `TestNamingCompliance` | 命名正则、slug 归属、md/html 配对、无旧标签残留 |
| 全量历史数据校验 | `TestHistoricalMigration` | 迁移清单完整性 + git 历史逐份复核内容零丢失 |
| 跨月份对比准确性 | `TestDiffAccuracy` | 相同 / 新增 / 修改 / 删除 / 相似度阈值 / 首期 / 报告页 diff 高亮 |
| 并行协作三层隔离 | `test_workflow_guard.py`（33 项） | 任务分支 / worktree、检出锁（占用 / 释放 / 强取 / 失效）、串行合并（happy / 冲突保留 / 校验阻断）、sync |
| 推送双通道 failover | `test_git_push.py`（6 项） | ssh 主通道成功、失败切 https、两条都失败时恰好各试一次（不重试） |
| 工作区标准化清理 | `test_cleanup.py`（19 项） | 残留识别与清理、`--check` / `--dry-run` 契约、日志作用域限定、已跟踪文件 / 目录保护、CI 接线契约（每工作流前置 + 收尾 `always`） |
| 工具契约 | `test_tools.py`（221 项） | 命名解析（新 + 历史）、周期与任务推导、归档策略、lint / 合规、`build_hub` 归一化比对与死链校验、`link_check` 内链 / 外链采集、提示词七节结构守卫、活跃度天数、全主题契约、流程复用与三体系一致性、模板合规守卫（链接 / 命名 / 节数 / 周期） |
| 架构守卫 | `test_arch_guard.py`（8 项） | 测试数与本文档一致、类型注册三处一致、目录 / 命名规范守卫 |
| 增量构建 | `test_incremental_build.py`（4 项） | 增量构建判定与缓存一致性 |
| 流水线端到端 | `test_pipeline_e2e.py`（2 项） | 审计状态机端到端 |
| 流水线编排 | `test_pipeline_orchestrator.py`（23 项） | 状态 shape / save-load 往返 / 损坏与 schema 负例（含非对象）、触发检测 watchlist 派生 / freshness / 幂等 / 只读默认、监控视图空状态 / 阻塞定位 / 损坏显式报错、编排器阶段顺序 / S2 闸门 / 续跑 / 损坏终止 / 非法周期 / 幂等、CI 工作流定时 + 无撰写步骤 |
| 登记册生成 | `test_registry_generator.py`（3 项） | 登记册生成契约 |
| 安全回归 | `test_security_regression.py`（3 项） | 注入 / 越界路径回归 |
| 工具链覆盖率门禁 | `test_coverage_gate.py`（15 项） | 配置读取 / 退出码判定 / 基线写入 / 报告测量 |
| 工具链评审软门禁 | `test_review_gate.py`（9 项） | 范围判定 / 评审存在性 / 清单解析 |
| 工具链开发规约守卫 | `test_toolchain_dev_spec.py`（11 项） | 规约阶段顺序 / 覆盖率单一事实源 / 合并前检查单 |
| 咨询面板决策引擎 | `test_consulting_panel.py`（15 项） | 配置 schema / 单一事实源消费 / PF-03·PF-14 派生 / 五问判定（空白·已填·边界）/ 面板确定性与演示标注 |
| 工具链补测（审计家族） | `test_cov_audit.py`（69 项） | audit_pipeline / check / badge / preflight / sampling / registry / auto_verify |
| 工具链补测（合规校验） | `test_cov_compliance.py`（122 项） | compliance / info_quality / lint / fact_card / validate / classify / ensure |
| 工具链补测（生成类） | `test_cov_build.py`（57 项） | build_hub / build_index / md2html / skeleton / archive / incremental / registry / diff |
| 工具链补测（编排决策） | `test_cov_pipeline.py`（111 项） | pipeline_runner / status / trigger / update_planner / automation / decision_log / stage_gate / pending / finance / _common |
| 工具链补测（并行协作） | `test_cov_workflow.py`（100 项） | workflow_guard / git_push / cleanup / run_tests_parallel |
| 分支命名与会话标识 | `test_branch_naming.py`（19 项） | sid 派生 / 分支名校验 / pre-push / pre-commit / 钩子安装 |
| 报告生成一致性比对 | `test_verify_report_parity.py`（25 项） | 归一化（单遍路径重写 / 时间戳 / JSON 易变键）、基线写入与覆盖清空、比对（一致 / 仅路径 / MISMATCH / MISSING / NEW）、退出码 0/1/2 |
| 引擎层迁移守卫 | `test_engine_migration.py`（16 项） | 目录终态（engine 存在 / 旧引擎层与根协作脚本目录不存在）、SKIP_TOP / TYPE_RE、主题数 21、深度推导 ROOT、旧路径与代码常量活引用清零、裸 tools 目录引用与旧模块路径 `src.<包>` 清零 |
| 跨平台差异守卫 | `test_platform_guard.py`（9 项） | 路径分隔（无 Windows 路径字面量 / 工作流正斜杠）、换行（仓库 blob LF / `.gitattributes` / `atomic_write` 保 LF）、命令可用性（无 `shell=True` / 无 PowerShell 专属语法 / 工具路径存在） |
| 性能趋势快照 | `test_perf_snapshot.py`（6 项） | 规模快照字段与实测口径、耗时采集、基线语义（首条为基线 / 追加不改基线 / `--set-baseline` 覆盖）、CLI `--porcelain` |

> 合计 1171 项（`python -m unittest discover -s engine/tests` 集成后实测，当前全绿；`incremental_build` 两项「无变更」断言在集成分支领先 main 时按预期失败，合并后通过）。

## 七、手动命令速查

```bash
# 环境
pip install -r requirements.txt

# 测试与校验
python -m unittest discover -s engine/tests -v
python engine/tools/validate.py
python engine/tools/build_hub.py --check

# 生成物
python engine/tools/md2html.py          # md → HTML
python engine/tools/build_hub.py        # index.html
python engine/tools/build_index.py      # INDEX.md

# 维护
python engine/tools/classify_reports.py --apply
python engine/tools/ensure_region_topics.py
python engine/tools/archive_reports.py

# 任务与状态
python engine/tools/update_planner.py --period 2026-12
python engine/tools/automation_status.py activity

# 信息质量
python engine/tools/info_quality_check.py --apply

# 审计
python engine/tools/audit_preflight.py --report <报告.md>
python engine/tools/audit_check.py --report <报告.md>
python engine/tools/audit_pipeline.py --submit --report <报告.md>
python engine/tools/audit_pipeline.py --gate

# 阶段闸（采集 / 筛选 / 分类左移）
python engine/tools/stage_gate_check.py

# 无法核实内容硬门禁（内容层零容忍）
python engine/tools/verified_content_gate.py --all

# 工具链开发域（TOOLCHAIN-DEV-SPEC）
python engine/tools/coverage_gate.py            # 覆盖率门禁（--update-baseline / --porcelain）
python engine/tools/review_gate.py --changed <变更清单>  # 双轴评审软门禁

# 决策支持 / 信息质量流程复用
python engine/tools/info_quality_check.py --check
python engine/tools/fact_card_check.py
python engine/tools/pending_verification.py --check
python engine/tools/personal_finance_model.py --check
python engine/tools/skeleton_builder.py --topic 14-life-operations --mode compact
python engine/tools/decision_log.py --timeline
```

## 八、常见问题

**Q：`build_hub.py --check` 报「汇总页已过期」？**
报告或生成器变更后需重新生成：`python engine/tools/build_hub.py`，或直接 push 触发 `html-sync`。

**Q：`validate.yml` 失败但本地测试通过？**
多为浅克隆取不到历史（`TestHistoricalMigration`）。CI 已配置 `fetch-depth: 0`；本地请确认 git 历史完整。

**Q：月度提醒 Issue 重复了？**
工作流已内置去重：当月存在未关闭的同标题 Issue 时会更新正文而非新建。若仍重复，检查 Issue 是否被关闭后又被重建。

**Q：历史报告 lint / 合规报错？**
历史报告由 `--new-only` 跳过，不再报错；如个别报告需临时豁免，加入 `lint-whitelist.json`（含原因与复核日期，逾期恢复阻断）。

**Q：如何手动跑一次定时任务？**
GitHub Actions 页面 → 对应 workflow → 「Run workflow」；或在本地按「手动命令速查」执行。

## 九、流程复用一致性（DecisionSupport-Guard）

「刚优化的流程」= 00 决策支持件套（个人参数档案 / 决策一页纸 / 个人财务模型 / 事实卡片 / 置信度分级 / 决策树 / 决策日志 / 待核实闭环）+ `info_quality_check` 升级（结构化免责声明 / 空模块占比 / 跨报告事实重复率）。**所有后续阶段必须复用同一套工具，不得另起判定逻辑。**

| 阶段 | 载体 | 复用的工具 / 产物 |
|---|---|---|
| PR / push 门禁 | `validate.yml` | `info_quality_check --check`、`fact_card_check`、`pending_verification --check`、`personal_finance_model --check` |
| 生成物同步 | `html-sync.yml` | `build_hub.py`（嵌入关键词 / 五问视图）、`audit_pipeline --sync` |
| 月度维护 | `scheduled-maintenance.yml` | `personal_finance_model.py`、`pending_verification.py`、`fact_card_check.py --write`、`build_hub.py` |
| 信息质量周期 | `info-quality.yml` | `info_quality_check.py --apply` |
| 审计门禁 | `audit-gate.yml` | `audit_check.py --all`（内嵌 info_quality_check 发现） |
| 月度提醒 | `scheduled-report-tasks.yml` | `update_planner.py`（含「决策状态变化」字段） |
| 生成期提示词 | `prompt-generic-base.md` / 00 `business-config.md` / `operations-guide.md` | 模块边界集中、五问「是/否/待定 + 依据」、件套路径 |
| 检索层 | `build_hub.py` + `engine/search/*` | `keywords.json` / `five-questions.json` / `question-index.json`（group） |

- **复用一致性测试**：`TestProcessReuse`（`engine/tests/test_tools.py`）逐项断言上述阶段均引用对应工具 / 产物；任一处漏接即测试失败，防止流程漂移。
- **维护闭环**：`scheduled-maintenance.yml` 每月刷新财务模型 / 待核实闭环 / 事实卡片报告；`validate.yml` 在 PR 阶段校验其一致性。

---

## 十、本地并行协作机制（`engine/scripts/workflow_guard.py`）

CI 之外的**本地多会话 / 多任务并行**由三层隔离机制约束，避免合并错误：

| 层 | 载体 | 命令 |
|---|---|---|
| 分支隔离（任务间） | `task/<name>-<sid>` 分支（`sid`=会话标识前 8 位）+ `.worktrees/<name>` 独立工作树 | `task start / list / stop` |
| 串行合并（main 级） | 全局 merge 锁 + 校验 + PR 传输（推分支 → 建 PR → 等 `validate` / `audit` → 合并）；服务端分支保护 | `merge` |
| 共享检出锁（工作目录级） | `.git/workflow-guard/*.lock`（owner / 超时失效） | `lock acquire / release / run / status` |

- **典型流程**：`task start <name>` → 在 `.worktrees/<name>/` 工作 → `merge <name>`
  → `task stop <name>`；本地 main 对齐用 `sync`。
- **分支命名**：开发分支 `task/<name>-<sid>`，`sid` = 会话标识（`CATPAW_CONVERSATION_ID`）前 8 位；
  钩子 `python engine/scripts/workflow_guard.py hooks`（pre-push / pre-commit）自动校验，新克隆 / 换机后必装。
  规范与台账：`docs/branch-management.md`。
- **与 CI 的边界**：Actions 在远端 runner 上直接推 `main`，不经过本地锁；
  合并侧用 `--force-with-lease` 兜底，远端被 CI 推进时本地合并失败重试，不覆盖。
- **详文档**：`engine/scripts/README.md`；**会话规约**：`.meituan-catpaw/5833106238/skills/workflow-guard/SKILL.md`；
  **分支规范**：`docs/branch-management.md`；**测试**：`engine/tests/test_workflow_guard.py`、`engine/tests/test_branch_naming.py`。

---

## 十一、工具链开发规约（代码交付域）

> 完整规约见 [工具链开发规约（TOOLCHAIN-DEV-SPEC）](toolchain/TOOLCHAIN-DEV-SPEC.md)。本节只保留 CI 侧的程序化边界。

工具链变更（`engine/`、`engine/scripts/`、`.github/workflows/`、根配置）走本规约六阶段（规格先行 → 工单化 → TDD → 实现 → 双轴评审 → 合并前检查单）；报告生产内容（`*/reports/`、`*/prompts/` 等）仍走五阶段 + AuditGuard，两层并行且边界清晰。

| 关注点 | 载体 | 命令 / 判据 |
|---|---|---|
| 覆盖率门禁 | `validate.yml`「覆盖率」job | `coverage_gate.py`；阈值 / 开关读 `coverage-config.json` 单一事实源；统计范围由 `.coveragerc` 限定工具链三目录 |
| 双轴评审软门禁 | `audit-gate.yml` | `review_gate.py --changed`；工具链变更须有 `docs/toolchain/reviews/*.md` |
| 合并前检查单 | `engine/scripts/README.md` | 测试 / validate / 评审 / 覆盖率 / 工作区卫生五项齐备 |
| 防漂移守卫 | `engine/tests/test_toolchain_dev_spec.py` | 规约阶段顺序 / 单一事实源 / 检查单存在性 |

- **豁免阈值**：≤2 文件且无新增工具的变更免规格 / 工单，但不得豁免双轴评审与合并前检查单。
- **分阶段阈值**：P1/P2 观察期 60%（`enforce=false`）；P3 起 80%（`enforce=true`，阻断）。
- **review_gate 转硬评估**：见 [review_gate 转硬评估框架](toolchain/review-gate-hardening-plan.md)；当前保持软门禁，条件未满足不切换。

---

## 十二、信息生产全链路（闭环与阶段闸）

> 本节只保留 CI 侧的程序化边界。阶段交付物、五闸执行规则、缺陷路由、周期保障与补缺准入的完整规范见 [信息生产全链路执行规范](信息生产全链路执行规范.md)；审计层门禁见 [审计报告标准化管理体系](审计报告标准化管理体系.md)。工具：`stage_gate_check.py`。

### 12.1 程序化边界（形态 vs 语义）

- **形态 / 结构类**（可程序化、秒级、无网络）→ 进 CI 硬门禁：命名、配对、继承声明、登记册 Schema、类型注册、时效字段（闸1 / 2 / 3，`stage_gate_check.py`）；
- **语义类**（六族十二类选型判别、口径冲突裁决、以偏概全）→ 不进 CI 硬门禁，由提示词自检 + L5 语义复核 + 季度跨领域角色（R2 / R4 / R5）承载；**来源语言规则**已程序化（`source_language_gate.py`，见二.1），属形态 / 结构类硬门禁。
- **判定内核单一事实源**：闸复用 `info_quality_check.evaluate()` / `compliance_check` / `audit_registry` 的解析，不新写判定。

阶段闸定义、闭环判据与全链路图见总规范第三节与 1.2。

---

## 十三、工作区卫生与标准化清理（横切）

**目标**：流水线运行前、运行中、运行结束后，runner 工作区与本地开发工作区都不留缓存、临时文件、过期日志等残留；清理规则单点维护，且可被门禁验证。

### 13.1 单一事实源：`engine/scripts/cleanup_workspace.py`

清理对象（仅限未入库产物）：

- 缓存目录：`__pycache__/`、`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、`.hypothesis/`、`.trae-html-share-packages/`、`.screenshots/`；
- 生成备份目录：`engine/vocabulary/data/sync-backups/`、`engine/vocabulary/data/topic-backups/`；
- 单文件：`*.py[cod]`、`*$py.class`、`*.tmp`、`*.temp`、`.DS_Store`、`Thumbs.db`、`desktop.ini`；
- 运行日志：`engine/vocabulary/data/*.log`（作用域限定，不误删其他目录的同名文件）；
- 覆盖率产物：`.coverage*`（coverage 数据文件）、`htmlcov/`（HTML 报告目录）。

**安全约束**：只清仓库根内路径；已被 `git ls-files` 覆盖的文件 / 目录一律跳过；不进入 `.git`；不跟随符号链接。

退出码：`0` = 干净或已清理；`1` = `--check` 发现残留 / 参数错误 / 删除失败。

```bash
python engine/scripts/cleanup_workspace.py            # 清理
python engine/scripts/cleanup_workspace.py --check    # 门禁：只检查，发现残留即退出码 1
python engine/scripts/cleanup_workspace.py --dry-run  # 预览将删除项
```

### 13.2 流水线接入（复合动作 `.github/actions/workspace-cleanup`）

每条工作流的每个 job 固定两处调用，形成「阶段前置 → 阶段收尾」闭环
（例外：`validate.yml` 的 `workspace-hygiene` 自检 job 本身就是清理链路验证，不接前置 / 收尾）：

| 位置 | 调用 | 作用 |
|---|---|---|
| 阶段前置（checkout + setup-python 之后） | `uses: ./.github/actions/workspace-cleanup`，`mode: ci` | 清掉 runner 带入的上游缓存 / 临时文件，保证阶段起点干净 |
| 阶段收尾（job 最后一步，`if: always()`） | 同上 | 无论成败清理本阶段产生的缓存 / 临时产物，并 `pip cache purge` |

- `mode: ci` 额外清理 pip 缓存（位于 runner HOME）；`check-only: 'true'` 只检查不删除，用于门禁。
- 提交 / 推送类步骤（`git commit` / `git push`）**必须**排在收尾清理之前，避免清理早于交付。
- 现已接入：`validate` / `audit-gate` / `html-sync` / `scheduled-maintenance` / `scheduled-report-tasks` / `info-quality` / `audit-sampling` / `pipeline-orchestrator`（8 条）。

### 13.3 门禁：`validate.yml` 的 `workspace-hygiene` job

独立 job，自证清理链路有效，防止「清理规则失效 / 新增产物类型未纳入清理」静默退化：

1. 安装依赖并跑契约测试（制造 `__pycache__`）；
2. 显式制造残留：`.pytest_cache/`、`sync-backups/`、`sync.log`、`.DS_Store`；
3. 执行标准化清理；
4. 以 `--check` 断言**零残留**，有残留即失败。

### 13.4 本地纪律

- 提交前运行 `python engine/scripts/cleanup_workspace.py`，随后 `git status` 应无未跟踪残留；
- 运行日志不入库（`.gitignore`：`engine/vocabulary/data/*.log`），本地仍由工具正常写入；
- `.worktrees/` 由 `engine/scripts/workflow_guard.py` 管理，不在清理脚本作用域内。

### 13.5 跨平台换行与路径口径（I-11 / N13）

CI 在 ubuntu runner 上用 **bash** 执行 `run:`，本地维护者用 **PowerShell**，两端在路径分隔、
换行、命令可用性上存在实质差异。仓库用「单一事实源 + 守卫测试」固化口径：

| 差异点 | 口径 | 载体 |
|---|---|---|
| 路径分隔 | 工具链代码禁止 Windows 路径字面量；工作流 `python engine/...` 一律正斜杠 | `engine/tests/test_platform_guard.py` |
| 换行 | 仓库文本一律 LF（`.gitattributes`：`* text=auto eol=lf`）；`atomic_write` 以 `newline=""` 原样保留 LF | `.gitattributes` + 守卫测试 |
| 命令可用性 | 工具禁止 `shell=True`；工作流禁止 PowerShell 专属语法 / `shell: powershell`；工作流引用的工具路径必须存在 | 守卫测试 |

> 守卫测试校验的是**仓库 blob**（`git show HEAD:<path>`）而非工作树：Windows 本地
> `core.autocrlf=true` 会把 LF 检出为 CRLF，若按工作树断言会误报。

---

## 十四、增量构建切默认决策记录（N12）

> **结论：不切生产默认**（2026-11-19 决策）。`incremental_build.py` 保持 POC / 手动入口，
> `md2html.py --changed` 可用但未接入默认构建流程；`build_hub` / `build_index` 仍全量。

### 14.1 现状

- `incremental_build.py`：按 `git diff --name-only <base>` 选月度报告 md，仅转换变更项；
  含 `--bench` 全量 vs 增量耗时对比。
- `md2html.py --changed`：同一筛选逻辑的 CLI 入口（默认基点 `main...HEAD`）。
- 既有测试：`test_incremental_build.py`（4 项）覆盖筛选 / 子集 / CLI / bench。

### 14.2 切默认的触发条件（须全部满足）

1. 连续 ≥3 次维护 / html-sync 运行中，增量产物与全量产物逐字节一致
   （`md_html_parity.py` 全绿 + 人工抽检）。
2. 变更集合判定覆盖**删除 / 重命名 / 跨月改名**场景，且有回归用例。
3. `build_hub` / `build_index` 的全量依赖被显式建模（汇总页 / 搜索索引必须全量重建），
   文档与测试同步。
4. `--bench` 显示增量耗时不高于全量的 60%，且无额外失败。

### 14.3 回滚判据（任一触发即回滚）

1. 增量产物与全量产物不一致（`md_html_parity` 报 MISMATCH / MISSING / NEW）。
2. 变更集合漏选（新增报告未生成 HTML）或误选（非报告文件进入转换）。
3. 增量路径下 `build_hub --check` / `build_index --check` / `validate.py` 任一退出码为 1。
4. **回滚方式**：恢复 `html-sync.yml` / `scheduled-maintenance.yml` 的 `md2html.py` 全量调用，
   移除增量开关；POC 工具保留不删。

### 14.4 验证口径

- **正确性**：`md_html_parity.py` 21/21 OK；`validate.py` 退出码 ∈ {0,2}；`unittest` 全绿。
- **等价性**：同一提交下增量与全量 HTML 逐字节一致（`report_diff` / `md_html_parity`）。
- **性能**：`incremental_build.py --bench` 输出 `incremental_sec` / `full_sec` / `speedup`，
  作为趋势快照录入 `engine/report-audits/toolchain/`（见第十五节）。
- **回归**：`test_incremental_build.py` 4 项 + 新增删除 / 重命名用例。

---

## 十五、性能趋势采集机制（N14）

`engine/tools/perf_snapshot.py` 采集**规模 + 耗时**并追加到
`engine/report-audits/toolchain/perf-trend.json`（基线 + 历史，保留最近 36 条）：

- **规模**：仓库文件数 / 体积、报告 md / html 数与 html 体积、`index.html` /
  `search-index.json` 体积、工具数、契约测试数。
- **耗时**：`validate` / `build_hub --check` / `build_index --check` / `md2html`；
  `--with-tests` 额外采集 `unittest`（默认关闭，避免维护流程翻倍耗时）。
- **基线**：首条快照即为基线；`--set-baseline` 覆盖基线；`--porcelain` 输出 JSON。
- **接线**：`scheduled-maintenance.yml` 每月追加一条快照，供跨月趋势对比。

> 基线数值可复用 `engine/report-audits/toolchain/coverage-baseline.json` 的覆盖率基线口径；
> 本报告不涉及覆盖率阈值（单一事实源仍为 `engine/tools/coverage-config.json`）。

---

## 十六、public 仓库安全姿态与生成前核验

仓库为 **PUBLIC**（GitHub Free）。已对齐的最佳实践与边界：

| 关注点 | 状态 | 载体 |
|---|---|---|
| 生成前信息核验（计划 / 发布前） | ✅ | `.github/actions/content-verify`（闸0 + 无法核实内容硬门禁）接入 `pipeline-orchestrator.yml` 与 `html-sync.yml` |
| 提交前内容硬门禁 | ✅ | `engine/scripts/precommit_content_gate.py`（pre-commit 钩子） |
| 合并门禁 | ✅ | `validate.yml` / `audit-gate.yml`（push + PR） |
| 密钥扫描 | ✅ enabled | 仓库设置 `secret_scanning` |
| 推送保护 | ✅ enabled | 仓库设置 `secret_scanning_push_protection` |
| 依赖安全更新 | ✅ enabled | 仓库设置 `dependabot_security_updates` |
| 依赖版本更新 | ✅ | `.github/dependabot.yml`（github-actions / pip 周更） |
| 工作流最小权限 | ✅ | 8 条工作流均显式 `permissions`；定时任务推分支 + 开 PR，无 `pull_request_target` |
| Actions 可创建 PR | ✅ enabled | 仓库设置 `can_approve_pull_request_reviews`（修复前自动化 `gh pr create` 被静默拒绝，积压 26 个 `auto/html-sync-*` 僵尸分支） |
| 远端分支治理 | ✅ | `delete_branch_on_merge=true`；已清理 26 个僵尸分支，当前远端仅 `main` |
| 服务端分支保护 | ✅ 已启用 | `main`：Require PR + Require status checks（`validate` / `audit`）+ enforce_admins + 禁 force-push / 删除；`merge` 默认走 PR 传输 |
| GitHub Pages | ✅ public | legacy Pages（main 根），与 PUBLIC 仓库一致 |

---

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 建立 CI 与自动化全景：7 条工作流、报告生命周期、命名分类、跨月对比、测试体系、手动命令、复用一致性、并行协作 |
| v1.2 | 2026-11-16 | 精简与修正 | 测试数修正为 222（189 + 33）；第十一节精简为指针 + 程序化边界，去除与总规范重复的全链路图与阶段闸表；手动命令补审计入口 |
| v1.3 | 2026-11-16 | 对齐校验整改 | 步骤清单与实际工作流逐一对齐（validate 14 步 / html-sync 7 步 / maintenance 14 步 / info-quality 6 步 / sampling 4 步 / report-tasks 3 步）；补阶段闸、信息质量、事实卡片、待核实、财务模型、自动化状态条目；sampling 不合格处置改为自动置 `stale` |
| v1.4 | 2026-11-16 | 工作区卫生横切 | 新增 `engine/scripts/cleanup_workspace.py`（缓存 / 临时文件 / 日志清理，含 `--check` 门禁与已跟踪文件保护）与复合动作 `.github/actions/workspace-cleanup`；7 条工作流全部接入「阶段前置 + 阶段收尾（`if: always()`）」清理；`validate.yml` 新增 `workspace-hygiene` 自检 job（制造残留 → 清理 → `--check` 断言零残留）；运行日志改为不入库；测试数 227 → 251 |
| v1.5 | 2026-11-16 | 第二轮对齐校验 | `audit-gate.yml` 的 `pull_request` 限定 `branches: [main]`（与 `validate.yml` 同口径）；十二.2 修正「每个 job」表述（`workspace-hygiene` 自检 job 例外）；二.3 补「自动化状态失败补记」步骤与活跃度预警口径；二.6 触发口径同步；测试数 251 → 255 |
| v1.6 | 2026-11-17 | 流水线编排状态层 | 新增 `engine/tests/test_pipeline_orchestrator.py`（状态 shape / 往返 / 损坏与版本不符，4 项）；六节测试数 285 → 289 |
| v1.7 | 2026-11-17 | 流水线触发检测 | 新增 `trigger_watch.py`（watchlist 派生 / freshness / 候选线索 / 只读默认）及同文件 6 项用例；六节测试数 289 → 295 |
| v1.8 | 2026-11-17 | 流水线监控视图 | 新增 `pipeline_status.py`（阶段进度 / 阻塞点 / 审计分布 / 心跳）及同文件 4 项用例；`automation_status` 新增 `pipeline` 心跳相位；六节测试数 295 → 299 |
| v1.9 | 2026-11-17 | 流水线编排器 | 新增 `pipeline_runner.py`（六阶段状态机 / 断点续跑 / S2 人工闸门）及同文件 6 项用例；六节测试数 299 → 305 |
| v2.0 | 2026-11-17 | 流水线 CI 接线 | 新增 `.github/workflows/pipeline-orchestrator.yml`（每月 1 日 00:35 UTC：触发检测 → S0→S2 → 监控视图 → 候选 Issue；不含撰写）及同文件 2 项用例；工作流 7 → 8，六节测试数 305 → 307 |
| v2.1 | 2026-11-17 | 流水线全链路验证 | 新增 E2E 用例（S0→S5 全链路 + S2 闸门 + 幂等，1 项）；六节测试数 307 → 308 |
| v2.2 | 2026-11-17 | 工具链开发规约落地 | 新增 TOOLCHAIN-DEV-SPEC（六阶段 / 豁免阈值 / 覆盖率门禁 / 双轴评审 / 合并前检查单）；新增 `coverage_gate.py`、`review_gate.py`、`coverage-config.json`、`.coveragerc`；`validate.yml` 增覆盖率 job、`audit-gate.yml` 增评审软门禁；新增守卫测试 `test_toolchain_dev_spec.py` 与 5 个补测文件；工具链覆盖率 0 门禁 → 93%（阈值 80% 阻断）；六节测试数 308 → 803；新增第十一节 |
| v2.3 | 2026-11-17 | 分支命名与会话标识 | 新增 `engine/scripts/branch_naming.py`（`task/<name>-<sid>` 规范 / 校验 / 钩子安装）与 `engine/scripts/git-hooks/{pre-push,pre-commit}`；`workflow_guard task start` 自动追加会话 sid，新增 `hooks` 子命令；存量 4 条分支补全 sid 并建立台账（`docs/branch-management.md`）；新增 `test_branch_naming.py`（19 项）并适配既有守卫；六节测试数 803 → 822 |
| v2.4 | 2026-11-17 | 引擎层迁移（SRC→ENGINE） | 旧引擎层目录整体迁至 `engine/`、根协作脚本迁至 `engine/scripts/`（纯路径迁移，零行为变更）；新增迁移守卫 `test_engine_migration.py`（14 项）与报告生成一致性比对 `test_verify_report_parity.py`（25 项）；六节测试数 822 → 861 |
| v2.5 | 2026-11-17 | 引擎层迁移缺口收口 | 修复二次确认列出的 7 处旧路径文本残留（`TOOLCHAIN-DEV-SPEC` 适用范围 / 覆盖率范围、`review_gate` 与 `cleanup_workspace` docstring、`test_cov_pipeline` 运行命令、mainline 评估报告、代码冗余清理报告）；迁移守卫扩展「裸 tools 目录引用」与「旧模块路径 `src.<包>`」两项扫描（14 → 16 项）；六节测试数 861 → 863 |
| v2.6 | 2026-11-17 | 迁移后治理 | 头部版本号与版本记录对齐；补 docs 索引与 toolchain 子目录索引；工具链类型注解补全（mypy 37 → 0）；删除 2 份无入链一次性留痕文档；新增迁移后治理双轴评审 |
| v2.7 | 2026-11-18 | 测试计数同步 | 测试数与实测对齐（863 → 868）；同步 `docs/README.md`、`docs/cross-domain-expert-roles.md`、`engine/tools/README.md` 当前计数 |
| v2.8 | 2026-11-18 | P0-9 报告必需要素门禁 | 新增 `structure_check.py`（报告必需要素结构校验）与 `TestStructureCheck`（6 项）、`audit_check` E9–E11 用例（1 项）；`validate.yml` 增结构校验步骤；六节测试数 874 → 881 |
| v2.9 | 2026-11-18 | P1 门禁三件套（P1-3 / P1-5 / P1-11） | 新增 `md_html_parity.py`（md↔HTML 漂移门禁，13 项）与 `prompt_check.py`（提示词命名/继承/结构/槽位门禁，13 项）；`validate.yml` 增两步阻断校验；`audit-gate.yml` 增全库审计兜底（`--gate --strict`）；工具 37 → 39；六节测试数 881 → 907 |
| v2.10 | 2026-11-18 | P1 质量机制（P1-10 / P1-4 / P1-6） | 新增 `engine/config/decision-tools.json`（决策工具参数外置）与 `test_decision_config.py` 漂移守卫（9 项）；新增 `l5_meta_check.py`（L5 证据元评估，12 项）接入 `audit-gate.yml`；新增 `decision_metrics.py`（五问/缺失度量，10 项）接入 `validate.yml`；工具 39 → 41；六节测试数 907 → 938 |
| v2.11 | 2026-11-18 | P1 索引与提示词（P1-7 / P1-8） | `build_hub` 搜索索引新增 `handbooks` 载体（74 条手册条目，含链接语法清洗）与前端「手册命中」；`prompt_check` 覆盖 00；00 补 `prompt-baseline-setup.md` / `prompt-quarterly-review.md`，优先级口径与通用基座统一；六节测试数 938 → 939 |
| v2.12 | 2026-11-18 | P1 报告结构统一（P1-1） | 局限章节标准名统一为「数据可靠性与局限说明」（7 份报告改名并重走 audit）；`structure_check` 收严为仅认标准名；修复 `audit_pipeline.write_status` 幽灵状态残留（新增守卫用例）；六节测试数 939 → 940 |
| v2.13 | 2026-11-18 | P1 来源 schema（P1-2） | 新增 `source_check.py`（来源条目四元组字段化 → `source-index.json`，10 项）接入 `validate.yml`；工具 41 → 42；六节测试数 940 → 950 |
| v2.14 | 2026-11-18 | P2 批次（P2-1…P2-7） | 新增 `counterexample_scan.py`（7 项）、`vocab_near_check.py`（8 项）与 `docs/词库近义合并规范.md`；`coverage_gate` 增逐工具明细（2 项）；`workflow_guard` 锁域扩展 commit/push；mypy 清零并转阻断 + 一次性工具冒烟；`decision_metrics --history` 入维护流水线；P2-7 跨月基线回归；工具 42 → 43；六节测试数 950 → 969 |
| v2.15 | 2026-11-18 | P1-9 词条 + P1-2 来源时点 | 14–20 词条补全至 ≥70（新增 245 条）；`source_check` 识别和历（令和/平成/昭和）与核对标记；6 份报告来源条目补「（2026-11 核对）」并重走审计；六节测试数 969 → 971 |
| v2.16 | 2026-11-19 | 测试计数同步 | 六节标题与合计行对齐实测：976 → 978、合计 881 → 978（含他会话 `6879c0e` 974→976 与 `e91940e` +2 未同步的累积漂移）；`test_arch_guard` 计数守卫恢复通过 |
| v2.17 | 2026-11-19 | 文档↔实现对齐 | 二.1 `validate` 步骤表补齐至实测（主 job 28 个命名步骤 + 2 个附加 job：覆盖率 / 工作区卫生）；二.3 `maintenance` 补齐至 19 步（含 `auto_verify --all --dry-run`）；二.6 `audit-gate` 补齐至 5 步；十二.1「六族十三类」→「六族十二类」。实测来源：`.github/workflows/{validate,audit-gate,scheduled-maintenance}.yml`（main @`fb1a38b`） |
| v2.18 | 2026-11-19 | 工具接线（组 C） | N4 `decision_log.py --check` 接入 `validate.yml`（缺失 / 结构损坏阻断）+ 守卫测试；N5 信息质量三清单留存策略；N6 `auto_verify` 全量日志策略；N8 五问收敛触发条件说明 |
| v2.19 | 2026-11-19 | 工程硬化（组 D / N11–N14） | ruff 存量 138 → 0（100 自动修复 + 38 人工等价重构，unittest / mypy / validate 等价验证）；新增 `test_platform_guard.py`（9 项）/ `test_perf_snapshot.py`（6 项）；新增 `perf_snapshot.py` 并接入 `scheduled-maintenance.yml`；`.gitattributes` 固化 LF；新增 13.5 / 十四 / 十五节；六节测试数 978 → 998（集成后实测） |
| v2.20 | 2026-11-19 | 词条删除 + remove 命令 | 新增 `vocab_tool remove`（TDD，3 项测试）；删除 22 条无法核验 `npa.go.jp` 词条（01: 109→98、02: 104→93）；`index.html` 重新生成；测试数 998 → 1001 |
| v2.21 | 2026-11-19 | 工程硬化收口（T3/T8） | T3 收口 `findings-by-path.json` 忽略（`git check-ignore` 命中，跑测试后工作区无残留）；T8 新增规格 `docs/toolchain/specs/align-2026-11-19.md` 与守卫 `TestReviewCoverage`（2 项，工单 100% 评审覆盖断言）；补 `coverage-gate-review.md` 与 closure-b 工单 slug 留痕；六节测试数 1001 → 1003 |
| v2.22 | 2026-11-19 | 文档↔实现对齐（T1/T10） | 修正工具 43→44、类型 13→12、测试 978→1008、validate 29/30 步、maintenance 20 步、词库 1634→1612、覆盖率 92.0→90.35%；`docs/README` 一次性文档声明改为「4 份在库、过程留痕保留」；新增 5 项守卫（类型数 / 词条数 / CI 步骤数 / 覆盖率基线 / 一次性文档声明） |
| v2.23 | 2026-11-19 | CI/CD 加固（W2 / R5 / R1 / R6 / R7） | 8 条工作流接入 pip 缓存 + 补齐 timeout；定时任务改推分支 + 开 PR（不再直推 main）；月度 cron 错峰（00:15 / 00:45 / 01:15 / 01:45）；`requirements-dev` 固定 + 新增 `requirements-dev.lock`；ruff 转阻断、mypy 覆盖 `engine/scripts`；契约测试改 4 分片 job（`run_tests_parallel.py`）；覆盖率新增单工具最低阈值（`per_tool_min`）+ `upload-artifact`；本地 pre-commit 增 `ruff --fix` + `validate.py`；测试数 1040 → 1045 |
| v2.24 | 2026-11-20 | 主健康修复 | 工具 45 → 46（`source_normalize.py` 登记入工具一览）、测试 1056 → 1081、`scheduled-maintenance` 步骤 21 → 22、`audit-gate` 步骤 6 → 7；`decision_log --check` 测试适配 n20「需求编号关联」契约（改用登记册真实问题）；`update_planner --requirements` 测试 patch 目标修正为 `update_planner.decision_metrics`（修复测试隔离）；n19–n26 工单双轴评审覆盖补齐（另由评审任务合入） |
| v2.25 | 2026-11-20 | 来源语言门禁（W5） | 新增 `engine/config/source-policy.json`（来源语言单一事实源）与 `source_language_gate.py`（提示词规则逐字一致 + 中文来源许可扫描 + 变更报告中文域名黑名单，14 项测试）；`validate.yml` 增「来源语言门禁」步骤（主 job 29 → 30 个命名步骤）；全库 21 主题 business-config 与 10 份泛用版提示词的 `{{SOURCE_LANGUAGE_RULE}}` 统一为「仅英文 / 日文来源，杜绝中文来源」；工具 46 → 47、测试 1081 → 1095 |
| v2.26 | 2026-11-21 | 无法核实内容门禁 | 新增 `engine/config/verified-content-policy.json`（内容层 / 记录层机读边界、标记词、状态列、豁免清单单一事实源）与 `verified_content_gate.py`（内容层零容忍硬门禁，15 项测试）；`validate.yml` 增「无法核实内容门禁」步骤（主 job 30 → 31 个命名步骤）、`audit-gate.yml` 增全库兜底（7 → 8 步）；全库清除内容层无法核实内容（报告 / 手册 / 登记册 / 词库）；工具 47 → 48、测试 1095 → 1110 |
| v2.27 | 2026-11-22 | 来源质量 P0-P2 修复 | `source_normalize` 新增受控分组词表 / 独立性 / 权威等级 / 语言判定；`extract_year` 先剥离 URL 再取年（修复 URL 数字 ID 误判）+ 行尾年 / URL 日期路径回退；`source_check` 增 E7 年份合理性 / E8 中文页 / E9 分组词表；`verified_content_gate` 默认语义与 CI 注释对齐；台账 append-only 回归；测试 1110 → 1127 |
| v2.28 | 2026-11-22 | 咨询面板门禁一致性 | `consulting_panel` 核验清单不再输出无法核实标记（未完成项转 `00-decision-hub/data/source-backlog.md` 第三节）；`test_panel_roundtrip` 改密闭临时目录 + 新增标记回归；测试 1127 → 1128 |
| v2.29 | 2026-11-22 | 生成前信息核验（闸0） | 新增 `engine/tools/generation_gate.py`（复用闸1-3 / 来源语言 / 无法核实内容 / 来源 schema 内核，18 项测试）与 `engine/scripts/precommit_content_gate.py`（提交前内容硬门禁）；`validate.yml` 增「生成前信息核验（闸0）」步骤（主 job 31 → 32 个命名步骤）；pre-commit 钩子接入内容硬门禁；提示词基座增「阶段4 前置：生成前信息核验」；工具 48 → 49、测试 1128 → 1146 |
| v2.30 | 2026-11-22 | 本地等价 CI 入口 | 新增 `engine/tools/local_ci.py`（只读编排层：validate / audit-gate 的 33 项本地检查，确定性 JSON，退出码 0/1/2；`--with-tests` / `--with-coverage` 可选）与 `engine/tests/test_local_ci.py`（21 项）；结果目录 `engine/report-audits/local-ci/` 入 `.gitignore`；工具 49 → 50、测试 1146 → 1167 |
| v2.31 | 2026-11-22 | 生成前核验接入 + public 安全姿态 | 新增复合动作 `.github/actions/content-verify`（闸0 + 无法核实内容硬门禁），接入 `pipeline-orchestrator.yml`（计划前）与 `html-sync.yml`（发布前）；新增 `.github/dependabot.yml`；仓库设置启用 secret scanning / push protection / Dependabot 安全更新；新增第十六节 |
| v2.32 | 2026-11-22 | 自动化 PR 权限修复 + 分支治理 | 仓库设置 `can_approve_pull_request_reviews=true`（修复自动化 PR 创建被静默拒绝）+ `delete_branch_on_merge=true`；合并 4 个 Dependabot actions 升级（checkout v7 / setup-python v7 / cache v6 / upload-artifact v7）；清理 26 个 `auto/html-sync-*` 僵尸分支；第十六节补两行 |
| v2.33 | 2026-11-22 | 合并 PR 化 + main 分支保护 | `workflow_guard merge` 新增 `--transport auto\|direct\|pr` + `--wait-timeout`（PR 传输：推分支 → 建 PR → 等检查 → 合并）；`main` 启用分支保护（Require PR + `validate`/`audit` + enforce_admins + 禁 force-push/删除）；`AGENTS.md` / `branch-management.md` v1.1 / `engine/scripts/README.md` 同步 |
