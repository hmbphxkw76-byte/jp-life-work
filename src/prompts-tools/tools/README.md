# prompts/tools 使用文档

CI 工具链使用说明。所有工具基于仓库根目录相对路径运行（自动定位仓库根），
在仓库根目录执行即可；通用层 + 业务层（`{地区}/{物业类型}/`）结构见
[report_templates/prompt-generic-base.md](../../report_templates/prompt-generic-base.md) 第 1.1 节。

## 环境准备

```bash
pip install -r requirements.txt   # markdown
python -m unittest discover -s src/tests -v   # 单元测试（255 项：tools 198 / workflow_guard 33 / cleanup 18 / git_push 6）
```

## 退出码约定（校验类工具统一）

| 退出码 | 含义 | CI 行为 |
|---|---|---|
| 0 | 通过（含空清单 / 无可处理项） | 继续 |
| 1 | 存在错误项 | 阻断 |
| 2 | 仅警告项 / 需人工确认 | 不阻断 |

## 工具一览

| 工具 | 类别 | 对应 CI 工作流步骤 |
|---|---|---|
| validate.py | 校验 | validate.yml「规范校验」 |
| lint_reports.py | 校验 | validate.yml「报告内容 lint」（新报告阻断） |
| compliance_check.py | 校验+引导+审计 | validate.yml「报告模板合规校验」（新报告阻断） |
| stage_gate_check.py | 校验 | validate.yml「阶段闸检查」（采集 / 筛选 / 分类左移） |
| classify_reports.py | 校验+修复 | scheduled-maintenance.yml「报告自动归位」 |
| ensure_region_topics.py | 校验+修复 | validate.yml「结构补全」 |
| md2html.py | 生成 | html-sync.yml「HTML 同步」 |
| archive_reports.py | 生成 | scheduled-maintenance.yml「归档策略」 |
| build_index.py | 生成 | scheduled-maintenance.yml「生成全局索引」 |
| build_hub.py | 生成 | validate.yml --check / html-sync.yml「汇总页」 |
| report_diff.py | 生成 | md2html 依赖：跨月内容对比高亮（纯函数） |
| incremental_build.py | 生成 | 手动：增量生成 POC（按 git diff 选择报告；含 --bench 对比） |
| generate_registry.py | 编排 | 手动：生成 `registry.json` 并渲染 README 快照（`--write` / `--check`） |
| migrate_monthly_reports.py | 迁移 | 一次性：存量报告合并重命名为月度系列 |
| update_planner.py | 编排 | scheduled-report-tasks.yml「生成月度任务清单」 |
| trigger_watch.py | 编排 | 手动 / pipeline-orchestrator.yml：触发检测（watchlist + freshness + 候选线索） |
| pipeline_status.py | 编排 | 手动：统一监控视图（阶段进度 / 阻塞点 / 审计分布 / 心跳） |
| automation_status.py | 编排 | 5 条工作流 `record` 入库 + 手动 `activity`（活跃度预警） |
| info_quality_check.py | 校验+修复 | info-quality.yml「信息质量全量评估」+ validate.yml「信息质量检查」 |
| auto_verify.py | 校验 | 手动：生成后自动验证（V1–V5）→ 写回「自动验证结果」→ 提交审计 |
| audit_registry.py / audit_pipeline.py / audit_badge.py / audit_check.py / audit_sampling.py / audit_preflight.py | 审计 | audit-gate.yml / audit-sampling.yml / html-sync.yml |
| personal_finance_model.py | 决策支持 | validate.yml「财务模型一致性」+ scheduled-maintenance.yml「刷新」 |
| fact_card_check.py | 决策支持 | validate.yml「事实卡片校验」+ scheduled-maintenance.yml「刷新」 |
| pending_verification.py | 决策支持 | validate.yml「待核实闭环」+ scheduled-maintenance.yml「刷新」 |
| skeleton_builder.py | 生成 | 手动：报告骨架 / 空模块合并 |
| decision_log.py | 编排 | 手动：决策状态变化时间线 |

## 校验类

### validate.py — 结构与规范校验

```bash
python src/prompts-tools/tools/validate.py
```

检查项：通用层根部 6 份共享文件齐全（`prompt-generic-base.md` / `monitoring-common-spec.md` /
`template-registry.md` / `report-classification.md` / `registry-schema.md` / `compliance-rules.json`）；
各类型模板目录必备文件齐全（13 类，清单见 `_common.TEMPLATE_TYPE_DIRS`，与
[report_templates/template-registry.md](../../report_templates/template-registry.md) 第二节登记一致）；
通用层全目录（含类型子目录）无业务关键词
（迪拜/公寓/Dubai/UAE/DLD/CBUAE/EIBOR 等，清单见 `_common.BUSINESS_KEYWORDS`）；
业务线目录结构（`prompts/business-config.md` 及其 `{{REGION}}/{{TOPIC}}/{{REGISTRY_PATH}}`
变量区）；`reports/` 内文件命名符合月度约定 `YYYY-MM-<主题slug>.md/.html`，
slug 与目录一致，且 md / html 成对存在。

### lint_reports.py — 报告内容校验

```bash
python src/prompts-tools/tools/lint_reports.py
```

扫描全部业务线 `reports/*.html`。**错误项（退出码 1）**：thead/tbody/table 标签不配对、
重复 `</tbody>`、畸形 `<th scope="col"ead>`。**警告项（退出码 2）**：
≥6 列表格 `<th>` 未声明百分比列宽、表格缺 `class="fixed"`、`<img>` 缺 alt。
纯函数 `lint_html(text)` 可被测试直接调用。

### compliance_check.py — 报告模板合规校验 / 模板引导 / 合规审计

校验规则与 12 类报告类型模板骨架一一对应，规则文件为
[report_templates/compliance-rules.json](../../report_templates/compliance-rules.json)
（与 [template-registry.md](../../report_templates/template-registry.md) 第二节登记一致；
周期未单独登记的类型按「结构逐字继承基线」回落校验）。报告类型自动识别：读取业务线
`prompts/business-config.md` 继承声明中的 `report_templates/<类型ID>/` 引用。

```bash
python src/prompts-tools/tools/compliance_check.py --check        # 全量校验（CI 阻断式关卡）
python src/prompts-tools/tools/compliance_check.py --file <路径>   # 校验单份报告（开发自查）
python src/prompts-tools/tools/compliance_check.py --list-types   # 列出已注册类型与模板引用入口
python src/prompts-tools/tools/compliance_check.py --scaffold market-monitoring monthly   # 模板自动填充引导
python src/prompts-tools/tools/compliance_check.py --audit        # 历史报告合规审计（写审计报告，不阻断）
```

**校验口径**（结构完整性 / 必填字段 / 内容格式三类）：

- **错误项（阻断合并）**：h2 节数少于类型模板骨架（结构缺失）、章节编号 `id="sN"`
  不连续或不有序、缺 `<title>`、月/季/年周期报告缺顶部导航、锚点 `href="#x"` 无对应 id（断头锚点）。
- **警告项（不阻断）**：h2 节数超出骨架（如为业务固化锚需人工确认）、基线报告缺简化
  锚点导航、文件名不符合命名约定（无法识别周期）、业务线未注册类型。
- `--audit` 对全部历史报告执行同口径校验，匹配度汇总与逐项明细写入
  `report-audits/compliance-audit.md`（定时维护提交留痕），发现不符合项退出码 2 并转
  预警 Issue，不阻断维护流水线。
- 纯函数 `check_report(text, rule, common)` / `detect_type(config_text)` /
  `cycle_rule(rules, type_id, cycle)` 可被测试直接调用。

### classify_reports.py — 报告自动归位

```bash
python src/prompts-tools/tools/classify_reports.py --check --unknown-warn   # 只检查
python src/prompts-tools/tools/classify_reports.py --apply --unknown-warn   # 执行移动
```

扫描散落在业务目录之外（仓库根、`report_templates/` 全目录含类型子目录）的报告文件，
按文件名中地区/业务类型词判定归属并移入对应业务线 `reports/`；无法判定归属的报警告警
（`--unknown-warn` 时退出码 2）。

### ensure_region_topics.py — 结构补全（幂等）

```bash
python src/prompts-tools/tools/ensure_region_topics.py --check   # 只报告缺失
python src/prompts-tools/tools/ensure_region_topics.py           # 创建缺失子目录
```

为每条业务线补齐 `prompts/`、`reports/`、`data/` 三个子目录；缺
business-config.md 时告警。重复执行无副作用。

## 生成类

### md2html.py — md → HTML 同步

```bash
python src/prompts-tools/tools/md2html.py
```

将业务线 `reports/*.md` 转换为同名自包含 HTML。报告页采用 macropulse-reports 设计
范式（navy 设计令牌：skip-link + hero 题头 + sticky report-nav + main 章节 + footer），
并在构建期预渲染**跨月对比高亮**（与上一期同主题报告比对，新增 / 修改加「已更新」标记，
删除折叠可追溯，工具条可切换对照阅读）。纯图表型简报（只出 HTML 的业务线）无 md 源时
自动跳过。依赖 markdown 包。

### archive_reports.py — 滚动归档（幂等）

```bash
python src/prompts-tools/tools/archive_reports.py
```

每条业务线保留最新 12 期月度报告（与首页详情页默认窗口一致），超出部分连同名
md / html 一并移入业务目录内 `reports/archives/`。保留策略为纯函数
`select_archives(items, keep)`。

### build_index.py — 全局索引

```bash
python src/prompts-tools/tools/build_index.py
```

按业务线汇总全部报告，生成根目录 `INDEX.md`（含「最近生成」时间戳，作为定时维护的
活跃度心跳；由 `scheduled-maintenance.yml` 每月 1 日自动生成，`validate.yml` 以 `--check` 校验一致）。

### build_hub.py — 汇总页

```bash
python src/prompts-tools/tools/build_hub.py          # 生成 index.html
python src/prompts-tools/tools/build_hub.py --check  # 校验是否为最新
```

`index.html` 为按业务线分组的报告枢纽（主题卡片 + 详情页，详情页默认展示最近
12 个月报告、按时间倒序）；报告链接直达各主题 `reports/*.html` **独立报告页**
（新标签页打开），报告页内含构建期预渲染的跨月对比高亮（见 md2html.py /
report_diff.py）。`--check`：过期退出码 1；文件缺失（全新克隆）退出码 0 并提示，
由定时维护首建。比对前对两侧做归一化——抹平「最近生成」生成时刻时间戳（分钟级心跳，
不参与最新性判定），报告清单部分逐字节比对。

## 编排类

### update_planner.py — 内容更新任务清单

```bash
# porcelain JSON（供定时任务判断清单是否为空）
python src/prompts-tools/tools/update_planner.py --porcelain --pending-only > tasks.json
# 人读 md 清单
python src/prompts-tools/tools/update_planner.py --pending-only > tasks.md
# 限定项目 / 周期
python src/prompts-tools/tools/update_planner.py --project dubai/apartment --period 2026-Q4
```

- `--period` 接受 `YYYY-MM` / `YYYY-Qn` / `YYYY`；缺省按当前 UTC 日期推导
  （季首月用季度标识，与工作流逻辑一致）。
- 报告已统一为月度命名：一个主题每月一份 `reports/{{YYYY-MM}}-<slug>.html`；
  季度节拍按季度末月归档（2026-Q4 → 2026-12），年度取 12 月。
- 任务状态：期望输出已存在 → done，否则 pending；`--pending-only` 只留 pending。
  参数错误退出码 2。

### trigger_watch.py — 触发检测（watchlist / freshness / 候选线索）

```bash
# 只读：JSON 输出到 stdout（默认行为）
python src/prompts-tools/tools/trigger_watch.py --report --period 2026-11
# 写快照：src/report-audits/pipeline/trigger-watch.json
python src/prompts-tools/tools/trigger_watch.py --apply --period 2026-11
```

- watchlist **派生**自各主题 `prompts/business-config.md` §7 触发器与
  `data/*_indicator_registry.md` 核验日期，不新增手工配置。
- `window_due` 复用 `update_planner` 待办判定；`stale` 用 `info_quality_check`
  的 `STALE_DAYS`（12 个月）阈值；`candidates` 仅取登记册「观察项与触发器状态」
  的待办线索（**命中 ≠ 核实**，无命中为空）。
- 默认只读；`--apply` 才写快照。退出码 0 = 正常（含空清单）。

### pipeline_status.py — 统一监控视图

```bash
python src/prompts-tools/tools/pipeline_status.py            # 人读 + 写 status.md / .json
python src/prompts-tools/tools/pipeline_status.py --porcelain # 仅 JSON
python src/prompts-tools/tools/pipeline_status.py --period 2026-11
```

- 读编排状态机（`state-<period>.json`）汇总阶段进度与阻塞点（首个非 completed 阶段），
  叠加审计台账状态分布与 `automation-status.json` 最近心跳。
- 状态文件缺失 → 空状态（冷启动）；损坏 / schema 不符 → `state_error` 明示，不静默续跑。
- `STAGES` 为六阶段 canonical 顺序，`pipeline_runner.py` 复用。

### automation_status.py — 自动化状态与活跃度

```bash
# 记录一次执行（工作流 always 步骤调用）
python src/prompts-tools/tools/automation_status.py record --phase maintenance \
    --result success --run-url "<运行链接>"

# 活跃度检查（>45 天预警；手动 / 按需入口，未纳入自动门禁）
python src/prompts-tools/tools/automation_status.py activity --threshold 45 --porcelain   # 输出天数或 unknown
python src/prompts-tools/tools/automation_status.py activity --threshold 45               # 人读说明
```

状态写入根目录 `automation-status.json`（追加式，工作流提交）。
`--phase` 可选 `content-update` / `maintenance` / `html-sync` / `info-quality` /
`audit-sampling` / `scheduled-report-tasks` / `pipeline`（端到端流水线编排心跳）。

## 决策支持流程（DecisionSupport-Guard）

00 模块的决策支持件套与 `info_quality_check` 升级构成「刚优化的流程」，各阶段复用同一套工具：

| 工具 | 作用 | 复用阶段 |
|---|---|---|
| `personal_finance_model.py` | 读 01/07/14/10/17 登记册活值，算净储蓄率 / 回本周期 | `validate.yml` 一致性 + `scheduled-maintenance.yml` 刷新 |
| `fact_card_check.py` | 事实卡片五字段 / `[@FC-NNN]` 指针 / 跨报告事实重复率 | 同上 |
| `pending_verification.py` | 14/15/17/18/19/20 首轮核验截止跟踪 | 同上 |
| `skeleton_builder.py` | 报告骨架生成 / 空模块合并 / 边界声明集中 | 生成期（按需） |
| `decision_log.py` | 决策状态变化时间线 | `update_planner.py` 月度清单 |
| `info_quality_check.py` | 结构化免责声明 / 空模块占比 / 事实重复率 | `info-quality.yml --apply` + `validate.yml --check` |

- **复用一致性测试**：`src/tests/test_tools.py::TestProcessReuse` 断言各阶段均引用对应工具，漏接即失败。
- **流程文档**：`docs/CI.md` 第九节（流程复用矩阵）。

## 常见场景速查

| 场景 | 命令 |
|---|---|
| 提交前本地自查 | `validate.py && lint_reports.py && compliance_check.py --check && build_hub.py --check` |
| CI 报「汇总页已过期」 | 运行 `build_hub.py` 重新生成后提交 |
| CI 报 lint 错误 | 按 `[E] 文件: 原因` 修复报告 HTML（多为标签不配对） |
| CI 报模板合规错误 | 按 `[E] 文件: [类型/周期] 不符合项` 对照类型模板补齐（结构缺失 / 必填字段 / 断头锚点） |
| 新报告开写前取骨架 | `compliance_check.py --scaffold <类型ID> [周期]` 输出骨架与自检要点 |
| 查历史报告合规匹配度 | `compliance_check.py --audit` 后看 `report-audits/compliance-audit.md` |
| 新增业务线后首跑 | `ensure_region_topics.py` → 补 business-config.md → 首期基线报告 |
| 手动补跑月度任务清单 | `update_planner.py --project dubai/apartment --period 2026-12` |

## 月度报告体系（2026-11 重构）

> CI / 自动化全景（7 条工作流、报告生命周期、测试体系）见 `docs/CI.md`。

- **命名**：全部报告统一 `YYYY-MM-<主题slug>.md` + 同名 `.html`；主题 slug 取
  目录名去编号前缀（`01-ssw-driver` → `ssw-driver`）。
- **分类**：取消基线 / 初析 / 季度等类型标签，全部按自然月聚合；季度报告按季度末月
  归档，与月度报告同一套命名 / 对比 / 展示逻辑。
- **同月合并**：同一主题同一自然月多份存量报告合并为一份，初析为主体、基线作附录，
  原文内容不删改（见 `migrate_monthly_reports.py` 与 `report-audits/report-migration-2026-11.md`）。
- **展示**：单主题报告列表默认展示最近 12 个月，按时间倒序（最新在顶端）。
- **对比**：每期报告与上一期（同主题、最近一个更早自然月）全量比对，新增 / 修改
  高亮并加「已更新」标记，删除折叠可追溯。
- **三类校验**（`src/tests/test_tools.py`）：命名格式合规性、全量历史数据迁移完整性
  （git 历史逐份复核内容零丢失）、跨月份对比准确性。

## 注意事项

- 所有路径均为仓库内相对路径，业务线整体迁移（改目录名）不影响工具运行。
- `archive_reports.py` 会移动历史报告到 `reports/archives/`，每主题保留最新 12 期；
  如需永久保留请自行调整 `archive_reports.KEEP`。

<!-- REGISTRY:BEGIN -->
> 注册表快照：工具 31 · 类型 13 · 主题 21 · 工作流 7（由 `generate_registry.py` 生成，勿手工编辑）
<!-- REGISTRY:END -->
