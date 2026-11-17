# CI 与自动化体系

> **版本**：v2.2（2026-11-17 工具链开发规约落地）
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
| 触发检测 / 编排状态（S0→S2） | `pipeline-orchestrator.yml`（每月 1 日 00:35 UTC） |
| 工具链覆盖率 / 双轴评审 | `validate.yml`（`coverage_gate.py`）/ `audit-gate.yml`（`review_gate.py`） |

**CI 不产出报告研究内容**——报告由各主题 `prompts/business-config.md` 定义的研究流程人工/Agent 产出；CI 只校验与同步生成物。

## 二、工作流清单

### 1. `validate.yml` — 质量门禁（阻断式）

- **触发**：`push` 到 main、pull_request（main 方向）
- **权限**：`contents: read`
- **checkout**：`fetch-depth: 0`（必须完整历史——迁移内容复核需取旧文件）

| 步骤 | 命令 | 失败后果 |
|---|---|---|
| 契约测试 | `python -m unittest discover -s engine/tests` | 阻断（退出码 1） |
| 结构与规范校验 | `validate.py` | 阻断 |
| 报告归位检查 | `classify_reports.py --check --unknown-warn` | 阻断 |
| 结构补全检查 | `ensure_region_topics.py --check` | 阻断 |
| 汇总页一致性 | `build_hub.py --check` | 阻断 |
| 全局索引一致性 | `build_index.py --check` | 阻断 |
| 报告内容 lint | `lint_reports.py --new-only` | 阻断（新报告；退出码 1） |
| 模板合规校验 | `compliance_check.py --new-only` | 阻断（新报告；退出码 1） |
| 阶段闸检查 | `stage_gate_check.py`（采集 / 筛选 / 分类） | 阻断（P0/P1） |
| 信息质量全量检查 | `info_quality_check.py --check` | 阻断（P0/P1） |
| 事实卡片校验 | `fact_card_check.py` | 阻断（P0/P1） |
| 待核实闭环检查 | `pending_verification.py --check` | 阻断（未登记 / 逾期） |
| 个人财务模型一致性 | `personal_finance_model.py --check` | 阻断（缺失 / 过期） |
| 词库校验 | `vocab_tool.py topic-check` / `verify` + `sync_vocab.py check` | 阻断 |
| 覆盖率门禁 | `coverage_gate.py`（阈值读 `coverage-config.json`） | 阻断（enforce=true 未达标 / 测试失败） |

> 两个关卡对期间 >= 2026-11 的**新报告**阻断；历史报告由 `--new-only` 跳过，
> 遗留项列入 `engine/report-audits/audit/lint-whitelist.json` 豁免（逾期恢复阻断）。

### 2. `html-sync.yml` — 生成物同步

- **触发**：push（`**/reports/*.md`、`build_hub.py`、`md2html.py`、`report_diff.py`、`topics.json`、`template-registry.md`、词库 `terms.md`、`engine/search/**` 变更）、手动
- **步骤**：
  1. `md2html.py` — 重新生成同名自包含 HTML（含构建期跨月对比高亮）
  2. `build_hub.py` — 重建 `index.html` 与 `search-index.json`
  3. `audit_pipeline.py --sync` — 指纹失配 → `stale`
  4. `audit_pipeline.py --rebind` — 渲染漂移重绑
  5. `audit_badge.py --sync` — 标识同步
  6. `automation_status.py record` — 记录执行状态
  7. 提交并推送（无变更则跳过）

### 3. `scheduled-maintenance.yml` — 每月定时维护

- **触发**：`cron: "15 0 1 * *"`（每月 1 日 00:15 UTC = 09:15 JST）、手动
- **步骤**（均幂等）：

| 步骤 | 命令 | 作用 |
|---|---|---|
| 归位 | `classify_reports.py --apply` | 移动错位报告到所属主题 |
| 补全 | `ensure_region_topics.py` | 补齐缺失的主题结构 |
| 归档 | `archive_reports.py` | 每主题保留最新 12 期，超出移入 `reports/archives/` |
| 索引 | `build_index.py` | 生成 `INDEX.md`（含活跃度心跳时间戳）；PR 阶段由 `build_index.py --check` 校验一致 |
| 报告 HTML | `md2html.py` | 同步报告页（含跨月对比高亮） |
| 汇总页 | `build_hub.py` | 重建 `index.html` |
| 财务模型 | `personal_finance_model.py` | 刷新个人财务模型 |
| 待核实闭环 | `pending_verification.py` | 刷新待核实闭环 |
| 事实卡片 | `fact_card_check.py --write` | 刷新事实卡片校验报告 |
| 审计失效 | `audit_pipeline.py --sync` | 指纹失配 → `stale` |
| 标识同步 | `audit_badge.py --sync` | 有效注入 / 失效撤销 |
| 回归 | `unittest` | 确认维护未破坏契约 |
| 自动化状态 | `automation_status.py record` | 记录维护执行状态 |
| 提交 | `git commit` + `git push` | 有变更才提交 |
| 自动化状态失败补记 | `git add -A -- automation-status.json` → `commit` + `push`（`if: always()`） | job 失败时主提交跳过，本步骤仍把本轮状态入库，避免「记录了却因未提交而丢失」 |

- **退出码约定**：`0` 通过；`1` 错误（阻断）；`2` 警告（放行）。
- **活跃度预警**：`automation_status.py activity --threshold 45` 为**手动 / 按需入口**（见第七节），
  不纳入自动门禁；自动侧只保证各工作流 `record` 入库，供人工判断节拍是否断档。

### 4. `scheduled-report-tasks.yml` — 月度产出提醒

- **触发**：`cron: "20 0 1 * *"`（每月 1 日 00:20 UTC）、手动（可指定 `period`）
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

### 6. `audit-gate.yml` — 审计门禁（阻断式）

- **触发**：`push` 到 main、`pull_request`（main 方向，与 `validate.yml` 同口径）
- **步骤与阻断条件**：

| 步骤 | 命令 | 失败后果 |
|---|---|---|
| 合并门禁（统一入口） | `audit_pipeline.py --gate`（`--changed` 增量 / `--strict` 全库） | 阻断（退出码 1） |
| 多层级校验 | `audit_check.py --all` | 存在 P0/P1 阻断；仅 P2 放行 |
| 工具链双轴评审软门禁 | `review_gate.py --changed .changed-files` | 软门禁（缺评审告警，不阻断） |

- **合并门禁覆盖**：`--gate` 一次完成台账哈希链、登记册双向一致、已审计标识一致、受检报告审计状态（`audited` + md/HTML 指纹匹配 + 有效 L5 证据）；PR 默认只查本次变更报告，`--strict` 查全库。
- **L5 证据门禁**：`audited` 报告必须附有效 L5 语义复核证据（`re_review --evidence` 或一次性 `--backfill-l5`），缺失即 `L5-EVIDENCE`（P1）阻断。
- **信息质量新标准**（2026-11-15 起）：C-03 跨文档重复按相似度 ≥ 80%；C-07 事实单元含表格行、纯交叉引用括号不计；C-08 读登记册字段化日期；C-10 按登记册 Schema 分支；C-13 报告↔登记册数值一致性；C-14 ④/⑤ 级来源强制核验标注。

- **配套（与提示词 / AGENTS 同一口径）**：交付与审计协议 = HTML 生成（`md2html.py`）→ 落盘前自检（`audit_preflight`）→ 多层级校验（`audit_check`）→ 提交审计（`audit_pipeline --submit`）；未通过自检 / 校验 / 初审的报告不得合并。

### 7. `audit-sampling.yml` — 月度分层抽检

- **触发**：`cron: "25 0 1 * *"`（每月 1 日 00:25 UTC = 09:25 JST）、手动
- **步骤**：
  1. `audit_sampling.py --apply`（分层抽样：每主题至少 1 份、总数 ≥ 20%，逐期轮换；命中 P0/P1 自动置 `stale`）
  2. `audit_badge.py --sync`（撤销不合格报告的「已审计」标识）
  3. `automation_status.py record`（记录执行状态）
  4. 提交抽检报告与审计状态
- **门槛**：结构合规率 = 100%、要素完整率 ≥ 95%、状态一致率 = 100%、抽检合格率 ≥ 95%、P0/P1 = 0
- **不合格**：命中 P0/P1 → `::error::` 告警 + 自动置 `stale`（`sampling_fail`）+ 撤销标识，报告重走 `submit → 初审 → 复核 → 终审`

### 8. `pipeline-orchestrator.yml` — 端到端流水线编排（检测 + 计划）

- **触发**：`cron: "35 0 1 * *"`（每月 1 日 00:35 UTC = 09:35 JST，与 00:15 / 00:20 / 00:25 错开）、手动（可指定 `--period`）
- **步骤**：
  1. `trigger_watch.py --apply`（派生 watchlist + freshness + 候选线索，写 `trigger-watch.json`）
  2. `pipeline_runner.py run`（S0 检测 → S1 计划 → **S2 人工闸门自动暂停**，不产出正文）
  3. `pipeline_status.py`（生成统一监控视图 `status.md` / `status.json`）
  4. 候选命中时开提醒 Issue（去重：当期已存在则更新正文）
  5. `automation_status.py record --phase pipeline` + 提交 `engine/report-audits/pipeline/**`
- **纪律**：**不含任何撰写步骤**；不跑 S3–S5 本地生成（由 `html-sync` / `validate` / `audit-gate` 承担）
- **退出码**：`pipeline_runner run` 0 = 正常（含 S2 暂停）；1 = 阶段失败 / 状态损坏；2 = 参数错误

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
                    归档：每主题保留最新 12 期
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

## 六、测试体系（`engine/tests/`，860 项）

| 场景 | 测试类 | 覆盖 |
|---|---|---|
| 命名格式合规性 | `TestNamingCompliance` | 命名正则、slug 归属、md/html 配对、无旧标签残留 |
| 全量历史数据校验 | `TestHistoricalMigration` | 迁移清单完整性 + git 历史逐份复核内容零丢失 |
| 跨月份对比准确性 | `TestDiffAccuracy` | 相同 / 新增 / 修改 / 删除 / 相似度阈值 / 首期 / 报告页 diff 高亮 |
| 并行协作三层隔离 | `test_workflow_guard.py`（33 项） | 任务分支 / worktree、检出锁（占用 / 释放 / 强取 / 失效）、串行合并（happy / 冲突保留 / 校验阻断）、sync |
| 推送双通道 failover | `test_git_push.py`（6 项） | ssh 主通道成功、失败切 https、两条都失败时恰好各试一次（不重试） |
| 工作区标准化清理 | `test_cleanup.py`（19 项） | 残留识别与清理、`--check` / `--dry-run` 契约、日志作用域限定、已跟踪文件 / 目录保护、CI 接线契约（每工作流前置 + 收尾 `always`） |
| 工具契约 | `test_tools.py`（208 项） | 命名解析（新 + 历史）、周期与任务推导、归档策略、lint / 合规、`build_hub` 归一化比对、活跃度天数、全主题契约、流程复用与三体系一致性、模板合规守卫（链接 / 命名 / 节数 / 周期） |
| 架构守卫 | `test_arch_guard.py`（8 项） | 测试数与本文档一致、类型注册三处一致、目录 / 命名规范守卫 |
| 增量构建 | `test_incremental_build.py`（4 项） | 增量构建判定与缓存一致性 |
| 流水线端到端 | `test_pipeline_e2e.py`（2 项） | 审计状态机端到端 |
| 流水线编排 | `test_pipeline_orchestrator.py`（23 项） | 状态 shape / save-load 往返 / 损坏与 schema 负例（含非对象）、触发检测 watchlist 派生 / freshness / 幂等 / 只读默认、监控视图空状态 / 阻塞定位 / 损坏显式报错、编排器阶段顺序 / S2 闸门 / 续跑 / 损坏终止 / 非法周期 / 幂等、CI 工作流定时 + 无撰写步骤 |
| 登记册生成 | `test_registry_generator.py`（3 项） | 登记册生成契约 |
| 安全回归 | `test_security_regression.py`（3 项） | 注入 / 越界路径回归 |
| 工具链覆盖率门禁 | `test_coverage_gate.py`（15 项） | 配置读取 / 退出码判定 / 基线写入 / 报告测量 |
| 工具链评审软门禁 | `test_review_gate.py`（9 项） | 范围判定 / 评审存在性 / 清单解析 |
| 工具链开发规约守卫 | `test_toolchain_dev_spec.py`（11 项） | 规约阶段顺序 / 覆盖率单一事实源 / 合并前检查单 |
| 工具链补测（审计家族） | `test_cov_audit.py`（69 项） | audit_pipeline / check / badge / preflight / sampling / registry / auto_verify |
| 工具链补测（合规校验） | `test_cov_compliance.py`（122 项） | compliance / info_quality / lint / fact_card / validate / classify / ensure |
| 工具链补测（生成类） | `test_cov_build.py`（57 项） | build_hub / build_index / md2html / skeleton / archive / incremental / registry / diff |
| 工具链补测（编排决策） | `test_cov_pipeline.py`（111 项） | pipeline_runner / status / trigger / update_planner / automation / decision_log / stage_gate / pending / finance / _common |
| 工具链补测（并行协作） | `test_cov_workflow.py`（100 项） | workflow_guard / git_push / cleanup / run_tests_parallel |
| 分支命名与会话标识 | `test_branch_naming.py`（19 项） | sid 派生 / 分支名校验 / pre-push / pre-commit / 钩子安装 |
| 报告生成一致性比对 | `test_verify_report_parity.py`（25 项） | 归一化（单遍路径重写 / 时间戳 / JSON 易变键）、基线写入与覆盖清空、比对（一致 / 仅路径 / MISMATCH / MISSING / NEW）、退出码 0/1/2 |
| 引擎层迁移守卫 | `test_engine_migration.py`（13 项） | 目录终态（engine 存在 / 旧引擎层与根协作脚本目录不存在）、SKIP_TOP / TYPE_RE、主题数 21、深度推导 ROOT、旧路径与代码常量活引用清零 |

> 合计 860 项（`python -m unittest discover -s engine/tests`，当前全绿）。

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
| 串行合并（main 级） | 全局 merge 锁 + 隔离合并工作树 `.worktrees/_merge` + 校验 + `--force-with-lease` | `merge` |
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

---

## 十二、信息生产全链路（闭环与阶段闸）

> 本节只保留 CI 侧的程序化边界。阶段交付物、五闸执行规则、缺陷路由、周期保障与补缺准入的完整规范见 [信息生产全链路执行规范](信息生产全链路执行规范.md)；审计层门禁见 [审计报告标准化管理体系](审计报告标准化管理体系.md)。工具：`stage_gate_check.py`。

### 12.1 程序化边界（形态 vs 语义）

- **形态 / 结构类**（可程序化、秒级、无网络）→ 进 CI 硬门禁：命名、配对、继承声明、登记册 Schema、类型注册、时效字段（闸1 / 2 / 3，`stage_gate_check.py`）；
- **语义类**（来源语言规则、六族十三类选型判别、口径冲突裁决、以偏概全）→ 不进 CI 硬门禁，由提示词自检 + L5 语义复核 + 季度跨领域角色（R2 / R4 / R5）承载。
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
| v2.4 | 2026-11-17 | 引擎层迁移（SRC→ENGINE） | 旧引擎层目录整体迁至 `engine/`、根协作脚本迁至 `engine/scripts/`（纯路径迁移，零行为变更）；新增迁移守卫 `test_engine_migration.py`（13 项）与报告生成一致性比对 `test_verify_report_parity.py`（25 项）；六节测试数 822 → 860 |
