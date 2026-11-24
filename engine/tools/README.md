# engine/tools 使用文档

> **版本**：v1.19（2026-11-23 CI 自动化 PR 免审批自动合并）

CI 工具链使用说明。所有工具基于仓库根目录相对路径运行（自动定位仓库根），
在仓库根目录执行即可；通用层 `engine/report_templates/` + 业务层 `NN-<slug>/` 结构见
[report_templates/prompt-generic-base.md](../report_templates/prompt-generic-base.md) 第 1.1 节。

## 环境准备

```bash
pip install -r requirements.txt   # markdown
python -m unittest discover -s engine/tests -q   # 单元测试（以 docs/CI.md 与实测为准）
```

> 测试计数：1218 项（`python -m unittest discover -s engine/tests` 实测，与 `docs/CI.md` 六节一致；由 `engine/tests/test_arch_guard.py` 双向锁定）。

## 退出码约定（校验类工具统一）

统一约定（`0` 通过 / `1` 阻断 / `2` 放行）见 `docs/CI.md` 的「退出码约定」。

## 工具一览

| 工具 | 类别 | 对应 CI 工作流步骤 |
|---|---|---|
| validate.py | 校验 | validate.yml「规范校验」 |
| lint_reports.py | 校验 | validate.yml「报告内容 lint」（新报告阻断） |
| compliance_check.py | 校验+引导+审计 | validate.yml「报告模板合规校验」（新报告阻断） |
| stage_gate_check.py | 校验 | validate.yml「阶段闸检查」（采集 / 筛选 / 分类左移） |
| generation_gate.py | 校验 | 手动 / 提示词阶段4 前置：生成前信息核验（闸0）；validate.yml「生成前信息核验（闸0）」 |
| local_ci.py | 编排 | 手动：本地等价 CI（只读检查集，validate / audit-gate 的本地兜底，额度受限时替代远端）；结果落盘 `engine/report-audits/local-ci/` |
| classify_reports.py | 校验+修复 | scheduled-maintenance.yml「报告自动归位」 |
| ensure_region_topics.py | 校验+修复 | validate.yml「结构补全」 |
| md2html.py | 生成 | html-sync.yml「HTML 同步」 |
| archive_reports.py | 生成 | scheduled-maintenance.yml「归档策略」 |
| build_index.py | 生成 | scheduled-maintenance.yml「生成全局索引」 |
| build_hub.py | 生成 | validate.yml --check / html-sync.yml「汇总页」 |
| report_diff.py | 生成 | md2html 依赖：跨月内容对比高亮（纯函数） |
| report_cycles.py | 生成 | build_hub / build_index / archive_reports 依赖：周期窗口与归属自动识别（纯函数） |
| incremental_build.py | 生成 | 手动：增量生成 POC（按 git diff 选择报告；含 --bench 对比） |
| generate_registry.py | 编排 | 手动：生成 `registry.json` 并渲染 README 快照（`--write` / `--check`） |
| migrate_monthly_reports.py | 迁移 | 一次性：存量报告合并重命名为月度系列 |
| update_planner.py | 编排 | scheduled-report-tasks.yml「生成月度任务清单」 |
| trigger_watch.py | 编排 | 手动 / pipeline-orchestrator.yml：触发检测（watchlist + freshness + 候选线索） |
| pipeline_status.py | 编排 | 手动：统一监控视图（阶段进度 / 阻塞点 / 审计分布 / 心跳） |
| pipeline_runner.py | 编排 | 手动 / pipeline-orchestrator.yml：六阶段状态机（断点续跑 / S2 人工闸门） |
| automation_status.py | 编排 | 8 条工作流 `record` 入库 + 手动 `activity`（活跃度预警） |
| info_quality_check.py | 校验+修复 | info-quality.yml「信息质量全量评估」+ validate.yml「信息质量检查」 |
| auto_verify.py | 校验 | 手动：生成后自动验证（V1–V5）→ 写回「自动验证结果」→ 提交审计；scheduled-maintenance.yml「全量自动验证（dry-run）」 |
| audit_registry.py / audit_pipeline.py / audit_badge.py / audit_check.py / audit_sampling.py / audit_preflight.py | 审计 | audit-gate.yml / audit-sampling.yml / html-sync.yml |
| personal_finance_model.py | 决策支持 | validate.yml「财务模型一致性」+ scheduled-maintenance.yml「刷新」 |
| fact_card_check.py | 决策支持 | validate.yml「事实卡片校验」+ scheduled-maintenance.yml「刷新」；五字段 / 指针 / 重复率 / corroboration（n22） |
| pending_verification.py | 决策支持 | validate.yml「待核实闭环」+ scheduled-maintenance.yml「刷新」 |
| consulting_panel.py | 决策支持 | 手动：17 项个人参数（PF-01…PF-17）→ 五问判定 + 条件化行动方案；`--render-panel` / `--check` / `--profile` / `--demo` |
| skeleton_builder.py | 生成 | 手动：报告骨架 / 空模块合并 |
| decision_log.py | 编排 | 手动：决策状态变化时间线；validate.yml「决策日志校验」（`--check` 缺失 / 结构损坏检测） |
| coverage_gate.py | 校验 | validate.yml「覆盖率门禁」；阈值读 `coverage-config.json` 单一事实源（`--update-baseline` / `--porcelain`） |
| review_gate.py | 校验 | audit-gate.yml「工具链变更双轴评审软门禁」（`--changed <清单>`） |
| link_check.py | 校验 | validate.yml「内链存在性校验」（报告 / 手册 / 词条 / 汇总页 / 搜索数据的仓库相对链接 + audit-status 键对账） |
| structure_check.py | 校验 | validate.yml「报告必需要素结构校验」（数据可靠性与局限 / 置信度标注 / 信息差与未核验清单 / 决策建议） |
| md_html_parity.py | 校验 | validate.yml「md↔HTML 一致性校验」（P1-3：渲染漂移 / 缺 HTML 阻断） |
| prompt_check.py | 校验 | validate.yml「提示词结构门禁」（P1-11：命名 / 继承声明 / p3–p5 结构 / business-config 槽位与优先级） |
| source_language_gate.py | 校验 | validate.yml「来源语言门禁」（W5：`{{SOURCE_LANGUAGE_RULE}}` 逐字一致 + 中文来源许可扫描 + 变更报告中文域名黑名单） |
| verified_content_gate.py | 校验 | validate.yml「无法核实内容门禁」+ audit-gate.yml 全库兜底（内容层零容忍：待核实 / 未核实 / 需核实原文 / 待核验 / 待补来源；记录层按 `engine/config/verified-content-policy.json` 豁免） |
| l5_meta_check.py | 校验 | audit-gate.yml「L5 证据元评估」（P1-4：覆盖率 / 合格率 / basis 缺失 / 依据充分度） |
| decision_metrics.py | 决策支持 | validate.yml「决策度量校验」（P1-6：五问收敛率 / 判定率 / 缺失 / 决策日志变化） |
| source_check.py | 校验 | validate.yml「来源条目 schema 校验」（P1-2：来源章节 / URL 条目时点 / 分级 / 字段完整率 E5，产出 source-index.json，n25 起入库受控） |
| source_normalize.py | 生成 | n25 来源字段归一化单一事实源（URL / 机构名 / 年份 / NFKC；供 source_check 与 n21 / n22 复用，纯函数） |
| counterexample_scan.py | 校验 | validate.yml「反例扫描」（P2-1：绝对化 / 以偏概全 / 无来源断言 / 单源候选） |
| perf_snapshot.py | 校验 | scheduled-maintenance.yml「性能趋势快照」；规模 + 耗时采集（基线 / 历史，`--with-tests` / `--set-baseline` / `--porcelain`） |

## 设计内不接线工具清单（B6）

以下工具**设计内不接入定时流水线**，仅冒烟 / 手动 / 触发依赖；列此清单消除「应接未接」歧义，
不改变现有接线决策。与 `docs/CI.md` 二.9 同口径。

| 工具 | 现状 | 不接线理由 | 复核日期 |
|---|---|---|---|
| `incremental_build.py` | POC / 手动（含 `--bench`）；仅 `validate.yml` 一次性冒烟（`--help`） | N12 决策不切生产默认；切默认触发条件未满足（见 `docs/CI.md` 第十四节） | 2026-12-19 |
| `migrate_monthly_reports.py` | 一次性迁移，已完成；仅冒烟 | 存量报告合并重命名已完成，无周期触发需求 | 2026-12-19 |
| `skeleton_builder.py` | 手动 / 按需（生成期）；仅冒烟 | 按需入口，无周期触发需求 | 2026-12-19 |
| `report_diff.py` | 触发依赖：`html-sync.yml` 路径过滤器 + `md2html.py` 构建期依赖；无独立校验步骤 | 纯函数依赖，已由 `md2html` / `md_html_parity` 覆盖，不单独设步骤 | 2026-12-19 |

## 校验类

### validate.py — 结构与规范校验

```bash
python engine/tools/validate.py
```

检查项：通用层根部 6 份共享文件齐全（`prompt-generic-base.md` / `monitoring-common-spec.md` /
`template-registry.md` / `report-classification.md` / `registry-schema.md` / `compliance-rules.json`）；
各类型模板目录必备文件齐全（12 类，清单见 `_common.TEMPLATE_TYPE_DIRS`，与
[report_templates/template-registry.md](../report_templates/template-registry.md) 第二节登记一致）；
通用层全目录（含类型子目录）无业务关键词
（迪拜/公寓/Dubai/UAE/DLD/CBUAE/EIBOR 等，清单见 `_common.BUSINESS_KEYWORDS`）；
业务线目录结构（`prompts/business-config.md` 及其 `{{REGION}}/{{TOPIC}}/{{REGISTRY_PATH}}`
变量区）；`reports/` 内文件命名符合月度约定 `YYYY-MM-<主题slug>.md/.html`，
slug 与目录一致，且 md / html 成对存在。

### lint_reports.py — 报告内容校验

```bash
python engine/tools/lint_reports.py
```

扫描全部业务线 `reports/*.html`。**错误项（退出码 1）**：thead/tbody/table 标签不配对、
重复 `</tbody>`、畸形 `<th scope="col"ead>`。**警告项（退出码 2）**：
≥6 列表格 `<th>` 未声明百分比列宽、表格缺 `class="fixed"`、`<img>` 缺 alt。
纯函数 `lint_html(text)` 可被测试直接调用。

### compliance_check.py — 报告模板合规校验 / 模板引导 / 合规审计

校验规则与 12 类报告类型模板骨架一一对应，规则文件为
[report_templates/compliance-rules.json](../report_templates/compliance-rules.json)
（与 [template-registry.md](../report_templates/template-registry.md) 第二节登记一致；
周期未单独登记的类型按「结构逐字继承基线」回落校验）。报告类型自动识别：读取业务线
`prompts/business-config.md` 继承声明中的 `report_templates/<类型ID>/` 引用。

```bash
python engine/tools/compliance_check.py --check        # 全量校验（CI 阻断式关卡）
python engine/tools/compliance_check.py --file <路径>   # 校验单份报告（开发自查）
python engine/tools/compliance_check.py --list-types   # 列出已注册类型与模板引用入口
python engine/tools/compliance_check.py --scaffold market-monitoring monthly   # 模板自动填充引导
python engine/tools/compliance_check.py --audit        # 历史报告合规审计（写审计报告，不阻断）
```

**校验口径**（结构完整性 / 必填字段 / 内容格式三类）：

- **错误项（阻断合并）**：h2 节数少于类型模板骨架（结构缺失）、章节编号 `id="sN"`
  不连续或不有序、缺 `<title>`、月/季/年周期报告缺顶部导航、锚点 `href="#x"` 无对应 id（断头锚点）。
- **警告项（不阻断）**：h2 节数超出骨架（如为业务固化锚需人工确认）、基线报告缺简化
  锚点导航、文件名不符合命名约定（无法识别周期）、业务线未注册类型。
- `--audit` 对全部历史报告执行同口径校验，匹配度汇总与逐项明细写入
  `report-audits/compliance-audit.md`（手动 / 按需入口，不纳入定时维护），发现不符合项
  退出码 2 并转预警 Issue，不阻断维护流水线。
- 纯函数 `check_report(text, rule, common)` / `detect_type(config_text)` /
  `cycle_rule(rules, type_id, cycle)` 可被测试直接调用。

### classify_reports.py — 报告自动归位

```bash
python engine/tools/classify_reports.py --check --unknown-warn   # 只检查
python engine/tools/classify_reports.py --apply --unknown-warn   # 执行移动
```

扫描散落在业务目录之外（仓库根、`report_templates/` 全目录含类型子目录）的报告文件，
按文件名中地区/业务类型词判定归属并移入对应业务线 `reports/`；无法判定归属的报警告警
（`--unknown-warn` 时退出码 2）。

### ensure_region_topics.py — 结构补全（幂等）

```bash
python engine/tools/ensure_region_topics.py --check   # 只报告缺失
python engine/tools/ensure_region_topics.py           # 创建缺失子目录
```

为每条业务线补齐 `prompts/`、`reports/`、`data/` 三个子目录；缺
business-config.md 时告警。重复执行无副作用。

### structure_check.py — 报告必需要素结构校验

```bash
python engine/tools/structure_check.py            # 全量校验（CI 阻断式关卡）
python engine/tools/structure_check.py --report <路径>   # 单份校验
python engine/tools/structure_check.py --json
python engine/tools/structure_check.py --warn     # 仅告警（退出码 2）
```

两部分：

1. **报告必需要素**：校验每份 `*/reports/*.md` 是否具备四大必需要素（h2 级，匹配范围为报告全部二级标题）：
   数据可靠性与局限说明、置信度标注、信息差与未核验清单、决策建议。分级码口径见
   [report_templates/confidence-grade-standard.md](../report_templates/confidence-grade-standard.md)。
2. **主题骨架完备性**（W1 / A5）：已配 `prompts/business-config.md` 的主题须有 `handbook/`，
   或在 `engine/vocabulary/config/skeleton-exemptions.json` 显式豁免；空骨架不占位。

退出码：0=通过；1=存在缺失（阻断）；2=仅告警。纯函数 `missing_elements(text)` /
`check_report(path)` / `check_skeleton()` / `skeleton_exemptions()` 可被测试直接调用。

### md_html_parity.py — md ↔ HTML 一致性校验（P1-3）

```bash
python engine/tools/md_html_parity.py            # 全量校验（CI 阻断式关卡）
python engine/tools/md_html_parity.py --report <路径>   # 单份校验
python engine/tools/md_html_parity.py --json
python engine/tools/md_html_parity.py --warn     # 仅告警（退出码 2）
```

HTML 是 md 的确定性派生物（`md2html.py` 幂等）。本工具重新渲染每份 md 源稿并与仓库
已提交的 HTML 逐字节比对（仅统一换行），阻断「改了 md 未同步 HTML」或「HTML 被手工
改动」造成的漂移。判定：`OK` / `MISSING`（缺同名 HTML）/ `MISMATCH`（漂移）/ `ERROR`
（渲染失败）。退出码：0=全部一致；1=存在漂移/缺失（阻断）；2=仅告警。

### prompt_check.py — 提示词结构门禁（P1-11）

```bash
python engine/tools/prompt_check.py            # 全量校验（CI 阻断式关卡）
python engine/tools/prompt_check.py --json
python engine/tools/prompt_check.py --warn     # 仅告警（退出码 2）
```

校验提示词体系的结构性约定：① 命名——业务提示词 `prompt-<kebab>.md`、类型模板
`prompt-<kebab>-template.md`、泛用版 `prompts/prompt-<kebab>.md`；② 继承声明——基线 /
周期提示词须引用 `../../engine/report_templates/`（四层继承体系）；③ 结构——
`prompt-p3/p4/p5-*.md` 须含 `## 信息缺口` 节；④ 槽位——`business-config.md` 须含
`{{REGION}}` / `{{TOPIC}}` / `{{REGISTRY_PATH}}` 与继承优先级口径。退出码：0=通过；
1=存在违规（阻断）；2=仅告警。

### l5_meta_check.py — L5 语义复核证据元评估（P1-4）

```bash
python engine/tools/l5_meta_check.py            # 全量元评估并写报告
python engine/tools/l5_meta_check.py --check    # 不写文件
python engine/tools/l5_meta_check.py --json
```

独立解析全库 L5 证据（不复用抽检结论），产出证据质量门槛：覆盖率（门槛 100%）、
合格率（`validate_l5_evidence` 六项结构）、basis 缺失（门槛 0）、basis 平均字数
（<20 告警）、verdict=fail 计数。输出 `engine/report-audits/audit/l5-meta-report.{json,md}`。
退出码：0=达标；1=覆盖缺口 / 无效证据 / basis 缺失（阻断）；2=仅告警。

### decision_metrics.py — 五问 / 缺失决策度量（P1-6）

```bash
python engine/tools/decision_metrics.py            # 计算并写报告
python engine/tools/decision_metrics.py --history  # 追加历史快照（跨月对比）
python engine/tools/decision_metrics.py --trend    # 与上一快照对比
python engine/tools/decision_metrics.py --check    # 仅校验可解析，不写文件
```

从 `00-decision-hub` 的结构化登记册与决策日志计算：指标收敛率、五问判定率、缺失条目数、
件套齐备度、决策变化次数，以及**需求维度（n19）**：需求覆盖率（已覆盖 / 部分 / 未覆盖）
与超期未闭环缺失数（由 `requirements_matrix()` 从登记册第一节 + 第二节生成）。
历史序列写入 `decision-metrics-history.jsonl`，供跨月趋势（P2-2 复用）。
**反馈维度（n20）**：缺失闭环率（已接入 / 已完成视为闭环）与超期未闭环缺失数；
决策记录引用次数以 `decision_log_entries` 为代理。退出码：0=正常；1=结构解析失败（阻断）；2=存在待定 / 缺失（告警）。

### source_check.py — 来源条目 schema 化（P1-2）

```bash
python engine/tools/source_check.py            # 全量校验并写 source-index.json
python engine/tools/source_check.py --check    # 不写文件
python engine/tools/source_check.py --json
```

把各报告来源章节的条目解析为机读四元组（来源文本 / 时点年份 / URL / 分级分组），产出
`engine/report-audits/audit/source-index.json`（n25 起为**入库受控产物**，含每份报告内容指纹）。
校验：来源章节存在性（E1，阻断）；URL 条目时点年份（E3）、来源分级声明（E4）、
来源条目字段完整率（E5）（告警）。归一化规则集中在 `source_normalize.py`（单一事实源），
供本工具与后续信源批评（n21）/ 证据强度（n22）复用。退出码：0=通过；1=缺来源章节（阻断）；2=仅告警。

### source_normalize.py — 来源字段归一化（n25）

纯函数模块（无副作用）：`normalize_url` / `normalize_org` / `normalize_year` / `extract_year`。
所有来源字段归一化必须经此模块，其他工具不得再各写一套。

### counterexample_scan.py — 反例 / 绝对化论断扫描（P2-1）

```bash
python engine/tools/counterexample_scan.py            # 扫描并写清单
python engine/tools/counterexample_scan.py --check    # 不写文件
python engine/tools/counterexample_scan.py --json
```

复用 `audit_check.absolute_hits`（已排除否定 / 引述语境）扫描**可证伪的反例候选**：
`ABS`（绝对化措辞）、`GEN`（以偏概全 / 过度推断）、`NOSRC`（断言句无来源标记）、
`单源`（含数字的结论句、所在段落仅一个来源标记且无 corroboration 标注，n22）。
产出 `engine/report-audits/audit/counterexample-report.json` 供人工补反例或限定语。
退出码：0=无命中；1=扫描失败；2=存在候选（需裁定）。

## 生成类

### md2html.py — md → HTML 同步

```bash
python engine/tools/md2html.py
```

将业务线 `reports/*.md` 转换为同名自包含 HTML。报告页采用 macropulse-reports 设计
范式（navy 设计令牌：skip-link + hero 题头 + sticky report-nav + main 章节 + footer），
并在构建期预渲染**跨月对比高亮**（与上一期同主题报告比对，新增 / 修改加「已更新」标记，
删除折叠可追溯，工具条可切换对照阅读）。纯图表型简报（只出 HTML 的业务线）无 md 源时
自动跳过。依赖 markdown 包。

### archive_reports.py — 滚动归档（幂等）

```bash
python engine/tools/archive_reports.py
```

每条业务线按周期类型保留近 N 个自然月报告（月度 18 / 季度 24 / 年度 60，
由 `report_cycles.py` 自动识别；见 `engine/vocabulary/config/report-cycles.json`），
超出部分连同名 md / html 一并移入业务目录内 `reports/archives/`。保留策略为纯函数
`select_archives(items, keep_months, now=None)`。

### build_index.py — 全局索引

```bash
python engine/tools/build_index.py
```

按业务线汇总全部报告，生成根目录 `INDEX.md`（含「最近生成」时间戳，作为定时维护的
活跃度心跳；由 `scheduled-maintenance.yml` 每月 1 日自动生成，`validate.yml` 以 `--check` 校验一致）。

### build_hub.py — 汇总页

```bash
python engine/tools/build_hub.py          # 生成 index.html
python engine/tools/build_hub.py --check  # 校验是否为最新
```

`index.html` 为按业务线分组的报告枢纽（主题卡片 + 详情页，详情页展示窗口按周期
类型：月度默认近 6 个月、可展开至 18；季度 24 个月；年度 60 个月，按时间倒序）；
报告链接直达各主题 `reports/*.html` **独立报告页**
（新标签页打开），报告页内含构建期预渲染的跨月对比高亮（见 md2html.py /
report_diff.py）。列表按报告页 meta 高亮「已更新 / 无更新」。`--check`：过期退出码 1；
文件缺失（全新克隆）退出码 0 并提示，由定时维护首建。比对前对两侧做归一化——
抹平「最近生成」生成时刻时间戳（分钟级心跳，不参与最新性判定），清单逐字节比对。

**检索层产物校验**：`engine/search/{keywords,question-index,five-questions}.json`
（检索输入，单一事实源）须存在且为合法 JSON；构建产物 `search-index.json` 随
`index.html` 一并比对，缺失 / 过期均阻断（退出码 1）。

## 编排类

### update_planner.py — 内容更新任务清单

```bash
# porcelain JSON（供定时任务判断清单是否为空）
python engine/tools/update_planner.py --porcelain --pending-only > tasks.json
# 人读 md 清单
python engine/tools/update_planner.py --pending-only > tasks.md
# 限定项目 / 周期
python engine/tools/update_planner.py --project 01-ssw-driver --period 2026-12
# 需求覆盖矩阵（PIR，n19）
python engine/tools/update_planner.py --requirements           # 人读表格
python engine/tools/update_planner.py --requirements --porcelain  # JSON
```

- `--period` 接受 `YYYY-MM` / `YYYY-Qn` / `YYYY`；缺省按当前 UTC 日期推导
  （季首月用季度标识，与工作流逻辑一致）。
- 报告已统一为月度命名：一个主题每月一份 `reports/{{YYYY-MM}}-<slug>.html`；
  季度节拍按季度末月归档（2026-Q4 → 2026-12），年度取 12 月。
- 任务状态：期望输出已存在 → done，否则 pending；`--pending-only` 只留 pending。
  参数错误退出码 2。
- `--requirements`（n19）输出需求覆盖矩阵（PIR）：`REQ-NN`（决策问题）× 责任主题 /
  覆盖状态 / 期限 / 关联缺失编号 + 缺失清单 `GAP-NN`；数据源 `decision_metrics.requirements_matrix()`。

### trigger_watch.py — 触发检测（watchlist / freshness / 候选线索）

```bash
# 只读：JSON 输出到 stdout（默认行为）
python engine/tools/trigger_watch.py --report --period 2026-11
# 写快照：engine/report-audits/pipeline/trigger-watch.json
python engine/tools/trigger_watch.py --apply --period 2026-11
```

- watchlist **派生**自各主题 `prompts/business-config.md` §7 触发器与
  `data/*_indicator_registry.md` 核验日期，不新增手工配置。
- `window_due` 复用 `update_planner` 待办判定；`stale` 用 `info_quality_check`
  的 `STALE_DAYS`（12 个月）阈值；`candidates` 仅取登记册「观察项与触发器状态」
  的待办线索（**命中 ≠ 核实**，无命中为空）。
- 默认只读；`--apply` 才写快照。退出码 0 = 正常（含空清单）。

### pipeline_status.py — 统一监控视图

```bash
python engine/tools/pipeline_status.py            # 人读 + 写 status.md / .json
python engine/tools/pipeline_status.py --porcelain # 仅 JSON
python engine/tools/pipeline_status.py --period 2026-11
```

- 读编排状态机（`state-<period>.json`）汇总阶段进度与阻塞点（首个非 completed 阶段），
  叠加审计台账状态分布与 `automation-status.json` 最近心跳。
- 状态文件缺失 → 空状态（冷启动）；损坏 / schema 不符 → `state_error` 明示，不静默续跑。
- `STAGES` 为六阶段 canonical 顺序，`pipeline_runner.py` 复用。

### pipeline_runner.py — 端到端编排器（六阶段状态机）

```bash
# 从 S0 起跑（遇 S2 人工闸门自动暂停）
python engine/tools/pipeline_runner.py run --period 2026-11 [--dry-run]
# 人工完成 S2 正文后从 S3 续跑
python engine/tools/pipeline_runner.py resume --period 2026-11 --from-stage S3_build
# 只读状态
python engine/tools/pipeline_runner.py status --period 2026-11
```

- 阶段：`S0_detect → S1_plan → S2_author（人工闸门）→ S3_build → S4_audit → S5_monitor`。
- **S2 为唯一人工环节**：编排器只置 `pending` 并产出待撰写清单，绝不自动产出正文。
- 状态持久化 `engine/report-audits/pipeline/state-<period>.json`；断点续跑、幂等；
  损坏 / schema 不符的状态文件直接终止（退出码 1）。
- 提交 / 合并仍走 `engine/scripts/workflow_guard.py`；编排器不直接 push `main`。

### automation_status.py — 自动化状态与活跃度

```bash
# 记录一次执行（工作流 always 步骤调用）
python engine/tools/automation_status.py record --phase maintenance \
    --result success --run-url "<运行链接>"

# 活跃度检查（>45 天预警；手动 / 按需入口，未纳入自动门禁）
python engine/tools/automation_status.py activity --threshold 45 --porcelain   # 输出天数或 unknown
python engine/tools/automation_status.py activity --threshold 45               # 人读说明
```

状态写入根目录 `automation-status.json`（追加式，工作流提交）。
`--phase` 可选 `content-update` / `maintenance` / `html-sync` / `info-quality` /
`audit-sampling` / `scheduled-report-tasks` / `pipeline`（端到端流水线编排心跳）。

### local_ci.py — 本地等价 CI 入口（本地优先 · 远程兜底）

只读编排层：把 `.github/workflows/` 中本地可跑的检查类步骤收敛为一条命令，
作为 GitHub Actions 不可用（额度 / 网络 / runner）时的本地兜底。**不新增门禁项**，
判定口径仍归各工具。

```bash
python engine/tools/local_ci.py run                    # 默认 33 项只读检查（人读汇总）
python engine/tools/local_ci.py run --json             # 结果 JSON 到 stdout
python engine/tools/local_ci.py run --markdown         # Markdown 摘要
python engine/tools/local_ci.py run --only validate,registry,gen-gate
python engine/tools/local_ci.py run --skip vocab-near,fact-card
python engine/tools/local_ci.py run --with-tests --with-coverage   # 追加单元测试 / 覆盖率
python engine/tools/local_ci.py run --emit engine/report-audits/local-ci/local-ci-status.json
python engine/tools/local_ci.py list                   # 列检查项 / 排除项 / 仅远程
```

- **退出码**：`0` 全过 / `1` 有失败 / `2` 仅警告（含参数错误）。
- **确定性**：结果 JSON 无时间戳 / 耗时，同分支同工作区两次运行逐字节一致。
- **只读边界**：不含 `--apply/--write/--submit/--sync/--rebind/--external` 等回写开关；
  `audit_check --all`、`auto_verify`、`cleanup --check` 因非只读或自伤被排除（`list` 可见）。
- **仅远程**：链接可达率探测、自动开 PR / webhook、GitHub runner 环境与服务端保护。
- 规格 / 工单 / 评审：`docs/toolchain/{specs,tickets,reviews}/local-ci-entry*.md`。

## 决策支持流程（DecisionSupport-Guard）

00 模块的决策支持件套与 `info_quality_check` 升级构成「刚优化的流程」，各阶段复用同一套工具：

| 工具 | 作用 | 复用阶段 |
|---|---|---|
| `personal_finance_model.py` | 读 01/07/14/10/17 登记册活值，算净储蓄率 / 回本周期 | `validate.yml` 一致性 + `scheduled-maintenance.yml` 刷新 |
| `fact_card_check.py` | 事实卡片五字段 / `[@FC-NNN]` 指针 / 跨报告事实重复率 / corroboration 来源数（n22）/ DIKW 血缘（n24） | 同上 |
| `pending_verification.py` | 14/15/17/18/19/20 首轮核验截止跟踪 | 同上 |
| `consulting_panel.py` | 17 项个人参数 → 五问判定 + 条件化方案（时间线 / 预算 / 核验清单） | 手动（`--profile`）；`--check` 校验面板 md |
| `skeleton_builder.py` | 报告骨架生成 / 空模块合并 / 边界声明集中 | 生成期（按需） |
| `decision_log.py` | 决策状态变化时间线 | `update_planner.py` 月度清单 + `validate.yml` `--check`（缺失 / 结构损坏检测） |
| `info_quality_check.py` | 结构化免责声明 / 空模块占比 / 事实重复率 | `info-quality.yml --apply` + `validate.yml --check` |

- **复用一致性测试**：`engine/tests/test_tools.py::TestProcessReuse` 断言各阶段均引用对应工具，漏接即失败。
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
| 手动补跑月度任务清单 | `update_planner.py --project 01-ssw-driver --period 2026-12` |

## 月度报告体系（2026-11 重构）

> CI / 自动化全景（8 条工作流、报告生命周期、测试体系）见 `docs/CI.md`。

- **命名**：全部报告统一 `YYYY-MM-<主题slug>.md` + 同名 `.html`；主题 slug 取
  目录名去编号前缀（`01-ssw-driver` → `ssw-driver`）。
- **分类**：取消基线 / 初析 / 季度等类型标签，全部按自然月聚合；季度报告按季度末月
  归档，与月度报告同一套命名 / 对比 / 展示逻辑。
- **同月合并**：同一主题同一自然月多份存量报告合并为一份，初析为主体、基线作附录，
  原文内容不删改（见 `migrate_monthly_reports.py` 与 `report-audits/report-migration-2026-11.json`）。
- **展示**：单主题报告列表按周期类型展示（月度默认近 6 个月、可展开至 18；
  季度 24 个月；年度 60 个月），按时间倒序（最新在顶端）。
- **对比**：每期报告与上一期（同主题、最近一个更早自然月）全量比对，新增 / 修改
  高亮并加「已更新」标记，删除折叠可追溯。
- **三类校验**（`engine/tests/test_tools.py`）：命名格式合规性、全量历史数据迁移完整性
  （git 历史逐份复核内容零丢失）、跨月份对比准确性。

## 合并前检查单（工具链开发域）

> 依据《工具链开发规约（TOOLCHAIN-DEV-SPEC）》第八节。`workflow_guard merge` 前逐项确认，
> 五项齐备方可合并；守卫测试 `engine/tests/test_toolchain_dev_spec.py::TestMergeChecklist` 断言本节存在。

| # | 项 | 命令 | 判据 |
|---|---|---|---|
| 1 | 测试 | `python -m unittest discover -s engine/tests` | 全绿（退出码 0） |
| 2 | 规范校验 | `python engine/tools/validate.py` | 退出码 ∈ {0,2} |
| 3 | 双轴评审 | 本任务 `docs/toolchain/reviews/<任务 slug>-review.md` | 存在且 Standards / Spec 双轴无 P0/P1 |
| 4 | 覆盖率 | `python engine/tools/coverage_gate.py` | 达标（P3 起 ≥80%，enforce=true） |
| 5 | 工作区卫生 | `python engine/scripts/cleanup_workspace.py --check` | 零残留（退出码 0） |

- **豁免**：≤2 文件且无新增工具的变更免规格 / 工单，但**不得**豁免第 3–5 项。
- **不改内核**：本检查单以文档规约 + 守卫测试固化，不改动 `workflow_guard` 的合并语义。

## 注意事项

- 所有路径均为仓库内相对路径，业务线整体迁移（改目录名）不影响工具运行。
- `archive_reports.py` 会移动历史报告到 `reports/archives/`，每主题按周期保留
  近 18 / 24 / 60 个自然月（月 / 季 / 年）；如需调整见
  `engine/vocabulary/config/report-cycles.json`。

<!-- REGISTRY:BEGIN -->
> 注册表快照：工具 50 · 类型 12 · 主题 21 · 工作流 8（由 `generate_registry.py` 生成，勿手工编辑）
<!-- REGISTRY:END -->


## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-17 | 初始版本 | 工具链使用说明（工具一览 / 工作流 / 测试 / 流水线全貌）；2026-11-17 校准测试数 308、工作流 8、类型 13 与旧路径 |
| v1.1 | 2026-11-17 | 迁移后治理 | 修复 `../../report_templates/` 断链为 `../report_templates/`；测试数 308 → 863；工作流 6 → 8 |
| v1.2 | 2026-11-19 | 文档↔实现对齐 | 测试计数 881 → 978（与 `docs/CI.md` 六节及实测对齐） |
| v1.3 | 2026-11-19 | 测试计数对齐 + 不接线工具登记 | 测试计数 978 → 1008（与实测对齐）；`test_arch_guard` 扩展为同时锁定 `docs/CI.md` 六节与本节计数；新增「设计内不接线工具清单」（B6） |
| v1.4 | 2026-11-19 | 合并后计数校准 | 测试计数 1008 → 1029（并入 consulting-panel 15 项 + B2 表格语义 6 项后实测） |
| v1.5 | 2026-11-19 | 工程守卫（W1 / A1 / A5） | 测试计数 1029 → 1040（新增归档保留期边界 6 项 + 文档数字锁定 3 项 + 骨架完备性 2 项）；退出码约定改为指向 `docs/CI.md`；`structure_check` 新增主题骨架完备性校验 |
| v1.6 | 2026-11-19 | CI/CD 加固（W2） | 测试计数 1040 → 1045（覆盖率单工具阈值 5 项）；工具链代码新增 pre-commit 快速子集（ruff --fix + validate.py）说明 |
| v1.7 | 2026-11-19 | 内容与词库（W4 / B7） | 测试计数 1045 → 1047（B7 新增 2 项 `build_hub` 检索层校验用例）；补记检索层产物校验说明 |
| v1.8 | 2026-11-20 | 加工层受控（n25） | `source-index.json` 由生成物提升为入库活台账（含报告内容指纹）；新增 `source_normalize.py` 归一化单一事实源；`source_check` 增 E5 字段完整率并扩展分组头识别 |
| v1.9 | 2026-11-20 | 证据强度标定（n22） | `counterexample_scan` 增「单源」扫描；`fact_card_check` 增 corroboration 来源数（P2）；`audit_check` L4 增 `EVI-01`（绝对化措辞配 3 级证据码）；置信度分级标准增证据类型 / 强度码 / 合成规则 |
| v1.10 | 2026-11-20 | 需求登记（n19） | `decision_metrics.requirements_matrix()` 需求覆盖矩阵（PIR）+ 需求维度指标；`update_planner --requirements`；00 / 01 / 08 提示词增「需求命中检查」 |
| v1.11 | 2026-11-20 | 反馈回路（n20） | `decision_metrics` 增缺失闭环率（反馈维度）；`decision_log --check` 增「决策问题」关联登记册校验（未关联 rc=2）；`scheduled-maintenance.yml` 增反馈汇总步骤；00 提示词增「反馈回流」 |
| v1.12 | 2026-11-20 | DIKW 血缘（n24） | `fact_card_check --lineage`（FC → 报告 / 登记册）；`decision_metrics --lineage`（决策问题 → 结论 ← 引用位置 ← 责任主题）；00 登记册增「DIKW 血缘」节 |
| v1.13 | 2026-11-20 | 来源语言门禁（W5） | 新增 `source_language_gate.py`（提示词规则逐字一致 + 中文来源许可扫描 + 变更报告中文域名黑名单）与 `engine/config/source-policy.json` 单一事实源；测试计数 1081 → 1095；头部版本对齐 |
| v1.14 | 2026-11-21 | 无法核实内容门禁 | 新增 `verified_content_gate.py`（内容层零容忍硬门禁）与 `engine/config/verified-content-policy.json`（内容层 / 记录层机读边界、标记词、状态列、豁免清单）；接入 `validate.yml` 与 `audit-gate.yml`；测试计数 1095 → 1110 |
| v1.15 | 2026-11-22 | 生成前信息核验（闸0） | 新增 `generation_gate.py`（复用闸1-3 / 来源语言 / 无法核实内容 / 来源 schema 内核）；接入 `validate.yml` 闸0 步骤与提示词基座阶段4 前置；工具 48 → 49、测试计数 1128 → 1146 |
| v1.16 | 2026-11-22 | 本地等价 CI 入口 | 新增 `local_ci.py`（只读编排层：33 项本地检查 + 确定性 JSON，退出码 0/1/2）；结果目录 `engine/report-audits/local-ci/` 入 `.gitignore`；工具 49 → 50、测试计数 1146 → 1167 |
| v1.17 | 2026-11-22 | 合并 PR 化 | `workflow_guard merge` 新增 `--transport auto\|direct\|pr` + `--wait-timeout`（PR 传输：推分支 → 建 PR → 等检查 → 合并）与 4 项 PR 传输测试；测试计数 1167 → 1171 |
| v1.18 | 2026-11-22 | task stop 信任 merged 登记 | `task stop` 对已登记 `merged`（含 `merged_sha`）的任务跳过祖先检查（PR 合并远端分支已删 / 本地 base 滞后时不误报）；测试计数 1171 → 1172 |
| v1.19 | 2026-11-23 | CI 自动化 PR 免审批自动合并 | 新增复合动作 `.github/actions/auto-merge-pr` 与守卫测试 `test_ci_auto_merge.py`（5 项）；6 条工作流 8 个提交点启用自动合并；测试计数 1172 → 1177 |
| v1.20 | 2026-11-23 | 门禁内移修正 | 复合动作改为「建 PR → 工作流内门禁（`validate.py` + `audit_pipeline --gate --strict`）→ `gh pr merge --merge`」；`trigger_watch.py` 写快照前建目录（新增 1 项回归测试）；测试计数 1177 → 1179 |
| v1.21 | 2026-11-23 | 修复 merge 等待竞态 | `workflow_guard` 新增 `PR_REQUIRED_CHECKS=(validate,audit)`，`_gh_pr_wait_checks` 显式等待（空 rollup + `CLEAN` 不再误判为可合并）；新增 4 项回归；测试计数 1179 → 1183 |
| v1.22 | 2026-11-23 | 写回换行口径硬化 | `generate_registry.write()` / `sync_vocab.dump_json()` 写回统一 `newline="\n"`（Windows 不再产 CRLF 假 dirty）；新增 `test_write_lf.py` 2 项；过程留痕守卫元组补 2 份；测试计数 1183 → 1185 |
| v1.23 | 2026-11-23 | 阶段闸登记册判据修复 | `stage_gate_check` 的 `G1-REGISTRY` glob 未命中时认可已声明且存在的 `{{REGISTRY_PATH}}`（修 `00-decision-hub` 误报 P2）；新增 1 项回归；测试计数 1185 → 1186 |
| v1.24 | 2026-11-23 | 事实卡片 corroboration 语义 | `fact_card_check` 支持 `single-source`（唯一权威口径不计 P2）+ 在库卡片守卫；标准文档 v1.2；测试计数 1186 → 1188 |
| v1.25 | 2026-11-23 | md2html 写回换行硬化 | `md2html.py` 唯一写点加 `newline="\n"`；新增 1 项守卫；测试计数 1188 → 1189 |
| v1.26 | 2026-11-23 | 本地校验只读口径 | `local_ci` 信息质量步骤锁定 `--check`（守卫测试）；测试计数 1189 → 1190 |
| v1.27 | 2026-11-23 | 近义扫描已裁定保留清单 | `vocab_near_check` 新增豁免清单与过滤；新增 4 项守卫；测试计数 1190 → 1194 |
| v1.28 | 2026-11-23 | 反例扫描裁定清单 | `counterexample_scan` 新增裁定清单（单源保持可见）；新增 3 项守卫；测试计数 1194 → 1197 |
| v1.29 | 2026-11-23 | link_check 覆盖率提升 | 新增 9 项单元测试；`link_check.py` 65.4% → 78.5%；测试计数 1197 → 1206 |
| v1.30 | 2026-11-24 | 核验闭环第一批 | `verification-retention-map.json` 基线刷新 + 新增 `test_vocab_verification_map.py`（2 项）；测试计数 1206 → 1208 |
| v1.31 | 2026-11-24 | 写回换行全量治理 | 62 处写点补 `newline="\n"`；新增 AST 守卫（2 项）；测试计数 1208 → 1210 |
| v1.32 | 2026-11-24 | 自动化已合并分支显式清理 | `auto-merge-pr` 合并成功后 `gh api -X DELETE .../git/refs/heads/...` 显式删头分支（删失败 `::warning::`）；清理残留 3 个 `auto/*-*`；新增 1 项守卫；测试计数 1210 → 1211 |
| v1.33 | 2026-11-24 | 反例扫描「单源」判定收敛 | `_single_source_sentences()` 仅对外部来源判定；新增内部指针白名单 / 章节指针 / 泛化词剔除与疑问句、建议类排除；新增 7 项守卫；测试计数 1211 → 1218 |
