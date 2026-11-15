# CI 与自动化体系

> 本文档说明 jp-life-work 报告管理体系的持续集成（CI）与定时自动化。
> 代码位置：`.github/workflows/`；工具链：`src/prompts-tools/tools/`；测试：`src/tests/test_tools.py`。

## 一、总览

本体系的**目标**：让「报告源文件 → 交付物」的生成始终一致，规范不退化，变更可追溯。

| 关注点 | 由谁保障 |
|---|---|
| 报告命名 / 结构 / 配对规范 | `validate.yml`（阻断） |
| md → HTML、汇总页 | `html-sync.yml`（push 触发） |
| 归档 / 索引 / 结构维护 | `scheduled-maintenance.yml`（每月 1 日） |
| 月度产出待办提醒 | `scheduled-report-tasks.yml`（每月 1 日） |
| 内容零丢失 / 对比准确性 | `src/tests/test_tools.py`（76 项） |
| 信息质量评估 / 混乱修复 | `info-quality.yml`（每周一 02:20 UTC） |
| 审计门禁（登记册 / 台账 / 标识 / L1–L5） | `audit-gate.yml`（阻断） |

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
| 报告内容 lint | `lint_reports.py --new-only` | 阻断（新报告；退出码 1） |
| 模板合规校验 | `compliance_check.py --new-only` | 阻断（新报告；退出码 1） |

> 两个关卡对期间 >= 2026-11 的**新报告**阻断；历史报告由 `--new-only` 跳过，
> 遗留项列入 `src/report-audits/audit/lint-whitelist.json` 豁免（逾期恢复阻断）。

### 2. `html-sync.yml` — 生成物同步

- **触发**：push（`**/reports/*.md`、`build_hub.py`、`md2html.py`、`report_diff.py`、`topics.json`、`template-registry.md`、词库 `terms.md`、`src/search/**` 变更）、手动
- **步骤**：
  1. `md2html.py` — 重新生成同名自包含 HTML（含构建期跨月对比高亮）
  2. `build_hub.py` — 重建 `index.html` 与 `search-index.json`
  3. 提交并推送（无变更则跳过）

### 3. `scheduled-maintenance.yml` — 每月定时维护

- **触发**：`cron: "15 0 1 * *"`（每月 1 日 00:15 UTC = 09:15 JST）、手动
- **步骤**（均幂等）：

| 步骤 | 命令 | 作用 |
|---|---|---|
| 归位 | `classify_reports.py --apply` | 移动错位报告到所属主题 |
| 补全 | `ensure_region_topics.py` | 补齐缺失的主题结构 |
| 归档 | `archive_reports.py` | 每主题保留最新 12 期，超出移入 `reports/archives/` |
| 索引 | `build_index.py` | 生成 `INDEX.md`（含活跃度心跳时间戳） |
| 报告 HTML | `md2html.py` | 同步报告页（含跨月对比高亮） |
| 汇总页 | `build_hub.py` | 重建 `index.html` |
| 回归 | `unittest` | 确认维护未破坏契约 |
| 提交 | `git commit` + `git push` | 有变更才提交 |

- **退出码约定**：`0` 通过；`1` 错误（阻断）；`2` 警告（放行）。

### 4. `scheduled-report-tasks.yml` — 月度产出提醒

- **触发**：`cron: "20 0 1 * *"`（每月 1 日 00:20 UTC）、手动（可指定 `period`）
- **步骤**：
  1. `update_planner.py --period <YYYY-MM>` 生成当月任务清单
  2. 用 `gh issue create` 开「【月度报告产出】YYYY-MM 任务清单」Issue
- **去重**：先 `gh issue list --state open --search "in:title 【月度报告产出】<period>"`；
  命中则 `gh issue edit` 更新正文并退出，否则新建。
- **只提醒、不写内容**：Issue 仅列待办，报告仍需人工/Agent 产出。

### 5. `info-quality.yml` — 信息质量周期评估与闭环修复

- **触发**：`cron: "20 2 * * 1"`（每周一 02:20 UTC = 11:20 JST）、手动
- **规范**：`docs/信息质量评估提示词体系.md`
- **步骤**：
  1. `info_quality_check.py --apply` — 全量评估 → 混乱识别分类 → 自动修复 → 复评验证（退出码 0/1/2）
  2. `md2html.py` — 同步被修复报告的 HTML
  3. `unittest` — 含文档↔程序一致性校验
  4. 提交三清单（无变更则跳过）；退出码 1 时 `::error::` 告警
- **产物**：`src/report-audits/info-quality/`（评估台账 / 修复台账 / 验证报告 / 累计修复历史 / JSON）

### 6. `audit-gate.yml` — 审计门禁（阻断式）

- **触发**：`push` 到 main、`pull_request`
- **步骤与阻断条件**：

| 步骤 | 命令 | 失败后果 |
|---|---|---|
| 登记册双向一致 | `audit_registry.py --check` | 阻断（退出码 1） |
| 台账哈希链 + 指纹绑定 | `audit_pipeline.py --verify` | 阻断 |
| 已审计标识一致 | `audit_badge.py --check` | 阻断 |
| 多层级校验 | `audit_check.py --all` | 存在 P0/P1 阻断；仅 P2 放行 |

- **L5 证据门禁**：`audited` 报告必须附有效 L5 语义复核证据（`re_review --evidence` 或一次性 `--backfill-l5`），缺失即 `L5-EVIDENCE`（P1）阻断。
- **信息质量新标准**（2026-11-15 起）：C-03 跨文档重复按相似度 ≥ 80%；C-07 事实单元含表格行、纯交叉引用括号不计；C-08 读登记册字段化日期；C-10 按登记册 Schema 分支；C-13 报告↔登记册数值一致性；C-14 ④/⑤ 级来源强制核验标注。

- **配套**：新增报告须先按提示词三步（preflight → audit_check → audit_pipeline --submit）自检并提交审计；未通过初审不得合并。

### 7. `audit-sampling.yml` — 月度分层抽检

- **触发**：`cron: "25 0 1 * *"`（每月 1 日 00:25 UTC = 09:25 JST）、手动
- **步骤**：`audit_sampling.py --apply`（分层抽样：每主题至少 1 份、总数 ≥ 20%，逐期轮换）→ 提交抽检报告
- **门槛**：结构合规率 = 100%、要素完整率 ≥ 95%、状态一致率 = 100%、抽检合格率 ≥ 95%、P0/P1 = 0
- **不合格**：命中 P0/P1 → `::error::` 告警，报告进入重新审计流程

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

## 六、测试体系（`src/tests/`，140 项）

| 场景 | 测试类 | 覆盖 |
|---|---|---|
| 命名格式合规性 | `TestNamingCompliance` | 命名正则、slug 归属、md/html 配对、无旧标签残留 |
| 全量历史数据校验 | `TestHistoricalMigration` | 迁移清单完整性 + git 历史逐份复核内容零丢失 |
| 跨月份对比准确性 | `TestDiffAccuracy` | 相同 / 新增 / 修改 / 删除 / 相似度阈值 / 首期 / 报告页 diff 高亮 |
| 并行协作三层隔离 | `test_workflow_guard.py`（33 项） | 任务分支 / worktree、检出锁（占用 / 释放 / 强取 / 失效）、串行合并（happy / 冲突保留 / 校验阻断）、sync |

其他：命名解析（新 + 历史）、周期与任务推导、归档策略、lint / 合规、`build_hub` 归一化比对、活跃度天数、16 主题契约。

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

## 九、本地并行协作机制（`tools/workflow_guard.py`）

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
