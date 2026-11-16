# CI 与自动化体系

> **版本**：v1.2（2026-11-16 精简合并）
> 本文档说明 jp-life-work 报告管理体系的持续集成（CI）与定时自动化。
> 代码位置：`.github/workflows/`（7 条工作流）；工具链：`src/prompts-tools/tools/`；测试：`src/tests/`。

## 一、总览

本体系的**目标**：让「报告源文件 → 交付物」的生成始终一致，规范不退化，变更可追溯。

| 关注点 | 由谁保障 |
|---|---|
| 报告命名 / 结构 / 配对规范 | `validate.yml`（阻断） |
| md → HTML、汇总页 | `html-sync.yml`（push 触发） |
| 归档 / 索引 / 结构维护 | `scheduled-maintenance.yml`（每月 1 日） |
| 月度产出待办提醒 | `scheduled-report-tasks.yml`（每月 1 日） |
| 内容零丢失 / 对比准确性 | `src/tests/test_tools.py` |
| 信息质量评估 / 混乱修复 | `info-quality.yml`（每周一 02:20 UTC） |
| 审计门禁（登记册 / 台账 / 标识 / L1–L5） | `audit-gate.yml`（阻断） |
| 决策支持件套（参数 / 一页纸 / 财务模型 / 事实卡片 / 待核实闭环） | `validate.yml`（复用门禁）+ `scheduled-maintenance.yml`（刷新） |
| 流程复用一致性 | `src/tests/test_tools.py::TestProcessReuse` |
| 阶段出口质量（采集 / 筛选 / 分类左移） | `validate.yml`（`stage_gate_check.py`） |

**CI 不产出报告研究内容**——报告由各主题 `prompts/business-config.md` 定义的研究流程人工/Agent 产出；CI 只校验与同步生成物。

## 二、工作流清单

### 1. `validate.yml` — 质量门禁（阻断式）

- **触发**：`push` 到 main、pull_request（main 方向）
- **权限**：`contents: read`
- **checkout**：`fetch-depth: 0`（必须完整历史——迁移内容复核需取旧文件）

| 步骤 | 命令 | 失败后果 |
|---|---|---|
| 契约测试 | `python -m unittest discover -s src/tests` | 阻断（退出码 1） |
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

> 两个关卡对期间 >= 2026-11 的**新报告**阻断；历史报告由 `--new-only` 跳过，
> 遗留项列入 `src/report-audits/audit/lint-whitelist.json` 豁免（逾期恢复阻断）。

### 2. `html-sync.yml` — 生成物同步

- **触发**：push（`**/reports/*.md`、`build_hub.py`、`md2html.py`、`report_diff.py`、`topics.json`、`template-registry.md`、词库 `terms.md`、`src/search/**` 变更）、手动
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
- **产物**：`src/report-audits/info-quality/`（评估台账 / 修复台账 / 验证报告 / 累计修复历史 / JSON）

### 6. `audit-gate.yml` — 审计门禁（阻断式）

- **触发**：`push` 到 main、`pull_request`（main 方向，与 `validate.yml` 同口径）
- **步骤与阻断条件**：

| 步骤 | 命令 | 失败后果 |
|---|---|---|
| 合并门禁（统一入口） | `audit_pipeline.py --gate`（`--changed` 增量 / `--strict` 全库） | 阻断（退出码 1） |
| 多层级校验 | `audit_check.py --all` | 存在 P0/P1 阻断；仅 P2 放行 |

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

## 六、测试体系（`src/tests/`，272 项）

| 场景 | 测试类 | 覆盖 |
|---|---|---|
| 命名格式合规性 | `TestNamingCompliance` | 命名正则、slug 归属、md/html 配对、无旧标签残留 |
| 全量历史数据校验 | `TestHistoricalMigration` | 迁移清单完整性 + git 历史逐份复核内容零丢失 |
| 跨月份对比准确性 | `TestDiffAccuracy` | 相同 / 新增 / 修改 / 删除 / 相似度阈值 / 首期 / 报告页 diff 高亮 |
| 并行协作三层隔离 | `test_workflow_guard.py`（33 项） | 任务分支 / worktree、检出锁（占用 / 释放 / 强取 / 失效）、串行合并（happy / 冲突保留 / 校验阻断）、sync |
| 推送双通道 failover | `test_git_push.py`（6 项） | ssh 主通道成功、失败切 https、两条都失败时恰好各试一次（不重试） |
| 工作区标准化清理 | `test_cleanup.py`（18 项） | 残留识别与清理、`--check` / `--dry-run` 契约、日志作用域限定、已跟踪文件 / 目录保护、CI 接线契约（每工作流前置 + 收尾 `always`） |
| 工具契约 | `test_tools.py`（198 项） | 命名解析（新 + 历史）、周期与任务推导、归档策略、lint / 合规、`build_hub` 归一化比对、活跃度天数、全主题契约、流程复用与三体系一致性 |

> 合计 272 项（`python -m unittest discover -s src/tests`，当前全绿）。

## 七、手动命令速查

```bash
# 环境
pip install -r requirements.txt

# 测试与校验
python -m unittest discover -s src/tests -v
python src/prompts-tools/tools/validate.py
python src/prompts-tools/tools/build_hub.py --check

# 生成物
python src/prompts-tools/tools/md2html.py          # md → HTML
python src/prompts-tools/tools/build_hub.py        # index.html
python src/prompts-tools/tools/build_index.py      # INDEX.md

# 维护
python src/prompts-tools/tools/classify_reports.py --apply
python src/prompts-tools/tools/ensure_region_topics.py
python src/prompts-tools/tools/archive_reports.py

# 任务与状态
python src/prompts-tools/tools/update_planner.py --period 2026-12
python src/prompts-tools/tools/automation_status.py activity

# 信息质量
python src/prompts-tools/tools/info_quality_check.py --apply

# 审计
python src/prompts-tools/tools/audit_preflight.py --report <报告.md>
python src/prompts-tools/tools/audit_check.py --report <报告.md>
python src/prompts-tools/tools/audit_pipeline.py --submit --report <报告.md>
python src/prompts-tools/tools/audit_pipeline.py --gate

# 阶段闸（采集 / 筛选 / 分类左移）
python src/prompts-tools/tools/stage_gate_check.py

# 决策支持 / 信息质量流程复用
python src/prompts-tools/tools/info_quality_check.py --check
python src/prompts-tools/tools/fact_card_check.py
python src/prompts-tools/tools/pending_verification.py --check
python src/prompts-tools/tools/personal_finance_model.py --check
python src/prompts-tools/tools/skeleton_builder.py --topic 14-life-operations --mode compact
python src/prompts-tools/tools/decision_log.py --timeline
```

## 八、常见问题

**Q：`build_hub.py --check` 报「汇总页已过期」？**
报告或生成器变更后需重新生成：`python src/prompts-tools/tools/build_hub.py`，或直接 push 触发 `html-sync`。

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
| 检索层 | `build_hub.py` + `src/search/*` | `keywords.json` / `five-questions.json` / `question-index.json`（group） |

- **复用一致性测试**：`TestProcessReuse`（`src/tests/test_tools.py`）逐项断言上述阶段均引用对应工具 / 产物；任一处漏接即测试失败，防止流程漂移。
- **维护闭环**：`scheduled-maintenance.yml` 每月刷新财务模型 / 待核实闭环 / 事实卡片报告；`validate.yml` 在 PR 阶段校验其一致性。

---

## 十、本地并行协作机制（`tools/workflow_guard.py`）

CI 之外的**本地多会话 / 多任务并行**由三层隔离机制约束，避免合并错误：

| 层 | 载体 | 命令 |
|---|---|---|
| 分支隔离（任务间） | `task/<name>` 分支 + `.worktrees/<name>` 独立工作树 | `task start / list / stop` |
| 串行合并（main 级） | 全局 merge 锁 + 隔离合并工作树 `.worktrees/_merge` + 校验 + `--force-with-lease` | `merge` |
| 共享检出锁（工作目录级） | `.git/workflow-guard/*.lock`（owner / 超时失效） | `lock acquire / release / run / status` |

- **典型流程**：`task start <name>` → 在 `.worktrees/<name>/` 工作 → `merge <name>`
  → `task stop <name>`；本地 main 对齐用 `sync`。
- **与 CI 的边界**：Actions 在远端 runner 上直接推 `main`，不经过本地锁；
  合并侧用 `--force-with-lease` 兜底，远端被 CI 推进时本地合并失败重试，不覆盖。
- **详文档**：`tools/README.md`；**会话规约**：`.meituan-catpaw/5833106238/skills/workflow-guard/SKILL.md`；
  **测试**：`src/tests/test_workflow_guard.py`。

---

## 十一、信息生产全链路（闭环与阶段闸）

> 本节只保留 CI 侧的程序化边界。阶段交付物、五闸执行规则、缺陷路由、周期保障与补缺准入的完整规范见 [信息生产全链路执行规范](信息生产全链路执行规范.md)；审计层门禁见 [审计报告标准化管理体系](审计报告标准化管理体系.md)。工具：`stage_gate_check.py`。

### 11.1 程序化边界（形态 vs 语义）

- **形态 / 结构类**（可程序化、秒级、无网络）→ 进 CI 硬门禁：命名、配对、继承声明、登记册 Schema、类型注册、时效字段（闸1 / 2 / 3，`stage_gate_check.py`）；
- **语义类**（来源语言规则、六族十三类选型判别、口径冲突裁决、以偏概全）→ 不进 CI 硬门禁，由提示词自检 + L5 语义复核 + 季度跨领域角色（R2 / R4 / R5）承载。
- **判定内核单一事实源**：闸复用 `info_quality_check.evaluate()` / `compliance_check` / `audit_registry` 的解析，不新写判定。

阶段闸定义、闭环判据与全链路图见总规范第三节与 1.2。

---

## 十二、工作区卫生与标准化清理（横切）

**目标**：流水线运行前、运行中、运行结束后，runner 工作区与本地开发工作区都不留缓存、临时文件、过期日志等残留；清理规则单点维护，且可被门禁验证。

### 12.1 单一事实源：`tools/cleanup_workspace.py`

清理对象（仅限未入库产物）：

- 缓存目录：`__pycache__/`、`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、`.hypothesis/`、`.trae-html-share-packages/`、`.screenshots/`；
- 生成备份目录：`src/vocabulary/data/sync-backups/`、`src/vocabulary/data/topic-backups/`；
- 单文件：`*.py[cod]`、`*$py.class`、`*.tmp`、`*.temp`、`.DS_Store`、`Thumbs.db`、`desktop.ini`；
- 运行日志：`src/vocabulary/data/*.log`（作用域限定，不误删其他目录的同名文件）。

**安全约束**：只清仓库根内路径；已被 `git ls-files` 覆盖的文件 / 目录一律跳过；不进入 `.git`；不跟随符号链接。

退出码：`0` = 干净或已清理；`1` = `--check` 发现残留 / 参数错误 / 删除失败。

```bash
python tools/cleanup_workspace.py            # 清理
python tools/cleanup_workspace.py --check    # 门禁：只检查，发现残留即退出码 1
python tools/cleanup_workspace.py --dry-run  # 预览将删除项
```

### 12.2 流水线接入（复合动作 `.github/actions/workspace-cleanup`）

每条工作流的每个 job 固定两处调用，形成「阶段前置 → 阶段收尾」闭环
（例外：`validate.yml` 的 `workspace-hygiene` 自检 job 本身就是清理链路验证，不接前置 / 收尾）：

| 位置 | 调用 | 作用 |
|---|---|---|
| 阶段前置（checkout + setup-python 之后） | `uses: ./.github/actions/workspace-cleanup`，`mode: ci` | 清掉 runner 带入的上游缓存 / 临时文件，保证阶段起点干净 |
| 阶段收尾（job 最后一步，`if: always()`） | 同上 | 无论成败清理本阶段产生的缓存 / 临时产物，并 `pip cache purge` |

- `mode: ci` 额外清理 pip 缓存（位于 runner HOME）；`check-only: 'true'` 只检查不删除，用于门禁。
- 提交 / 推送类步骤（`git commit` / `git push`）**必须**排在收尾清理之前，避免清理早于交付。
- 现已接入：`validate` / `audit-gate` / `html-sync` / `scheduled-maintenance` / `scheduled-report-tasks` / `info-quality` / `audit-sampling`（7 条）。

### 12.3 门禁：`validate.yml` 的 `workspace-hygiene` job

独立 job，自证清理链路有效，防止「清理规则失效 / 新增产物类型未纳入清理」静默退化：

1. 安装依赖并跑契约测试（制造 `__pycache__`）；
2. 显式制造残留：`.pytest_cache/`、`sync-backups/`、`sync.log`、`.DS_Store`；
3. 执行标准化清理；
4. 以 `--check` 断言**零残留**，有残留即失败。

### 12.4 本地纪律

- 提交前运行 `python tools/cleanup_workspace.py`，随后 `git status` 应无未跟踪残留；
- 运行日志不入库（`.gitignore`：`src/vocabulary/data/*.log`），本地仍由工具正常写入；
- `.worktrees/` 由 `tools/workflow_guard.py` 管理，不在清理脚本作用域内。

---

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 建立 CI 与自动化全景：7 条工作流、报告生命周期、命名分类、跨月对比、测试体系、手动命令、复用一致性、并行协作 |
| v1.2 | 2026-11-16 | 精简与修正 | 测试数修正为 222（189 + 33）；第十一节精简为指针 + 程序化边界，去除与总规范重复的全链路图与阶段闸表；手动命令补审计入口 |
| v1.3 | 2026-11-16 | 对齐校验整改 | 步骤清单与实际工作流逐一对齐（validate 14 步 / html-sync 7 步 / maintenance 14 步 / info-quality 6 步 / sampling 4 步 / report-tasks 3 步）；补阶段闸、信息质量、事实卡片、待核实、财务模型、自动化状态条目；sampling 不合格处置改为自动置 `stale` |
| v1.4 | 2026-11-16 | 工作区卫生横切 | 新增 `tools/cleanup_workspace.py`（缓存 / 临时文件 / 日志清理，含 `--check` 门禁与已跟踪文件保护）与复合动作 `.github/actions/workspace-cleanup`；7 条工作流全部接入「阶段前置 + 阶段收尾（`if: always()`）」清理；`validate.yml` 新增 `workspace-hygiene` 自检 job（制造残留 → 清理 → `--check` 断言零残留）；运行日志改为不入库；测试数 227 → 251 |
| v1.5 | 2026-11-16 | 第二轮对齐校验 | `audit-gate.yml` 的 `pull_request` 限定 `branches: [main]`（与 `validate.yml` 同口径）；十二.2 修正「每个 job」表述（`workspace-hygiene` 自检 job 例外）；二.3 补「自动化状态失败补记」步骤与活跃度预警口径；二.6 触发口径同步；测试数 251 → 255 |
