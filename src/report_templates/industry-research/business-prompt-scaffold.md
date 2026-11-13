# 业务提示词脚手架（行业深度研究型）

> **用途**：为行业深度研究型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将本文件各节复制为 `{REGION}/{PROPERTY}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{REGION}/{PROPERTY}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-annual-refresh.md`（含重大事件插刷说明）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立研究边界档案与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 战略决策层 / 投资者 / 新进入者（TODO：按业务收窄） | 报告须声明受众 |
| 研究边界 | 行业边界定义（含 / 不含清单）、产业链分层口径（TODO） | 边界档案制度化 |
| 玩家清单 | 入选标准 + 分层清单（TODO） | 进出须留痕 |
| 规模口径清单 | 多口径并列清单（TODO：每口径附来源与假设） | 并列不合并 |
| 插刷触发器 | `事件 → 受影响模块`（TODO：重大并购 / 监管重构 / 技术代际切换） | 命中即提前刷新 |
| 来源优先级 | ① 统计局 / 行业协会 ② 上市公司财报 ③ 第三方研究机构 ④ 专家访谈（TODO：机构清单） | 多源交叉验证 |
| 追踪表 | 研究维度 × 优先来源（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md 脚手架（复制为 prompts/prompt-baseline-setup.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 首期基线报告提示词（行业深度研究型）

> **用途**：执行「{{REGION}} {{TOPIC}} 行业研究机制」的**机制建立**任务：产出首期行业全景基线报告与配套研究边界档案。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文九节基线报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}_baseline_report.md`）+ 研究边界档案（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [基线报告类型模板（行业深度研究型）](../../../report_templates/industry-research/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{BASELINE_DATE}}        = 首期基线日期
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO：边界档案文件名）
{{REPORT_VERSION}}       = v1.0（首期基线固定）
```

**任务目标**：产出九节行业全景基线报告（产业链图谱、规模与格局、头部玩家、驱动与风险、趋势判断）与边界档案首建；多口径规模并列不合并；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

## 一、项目专属硬性约束

1. **中性立场**：不给投资评级、不出具 Go/No-Go 决策建议（边界归投资尽调型、可行性型）。
2. **结论边界**：趋势判断一律标「推断」并配反向声音；口径冲突并列呈现。
3. **受众定位**：见[业务配置](./business-config.md)（TODO：实例化）。

## 二、来源优先级

见[业务配置](./business-config.md)（TODO：① 官方统计 ② 财报 ③ 第三方研究 ④ 专家访谈）；每格活值附 `[来源, 年份]`。

## 三～九、结构骨架与联动

九节固定骨架见[基线类型模板第三节](../../../report_templates/industry-research/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后逐字继承）；追踪表见[业务配置](./business-config.md)（TODO）。

## 十、渲染与交付

- md + 自包含 HTML（`python prompts/tools/md2html.py`）；HTML 须通过 `python prompts/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 四、prompt-annual-refresh.md 脚手架（复制为 prompts/prompt-annual-refresh.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 年度刷新提示词（行业深度研究型）

> **用途**：每年固定窗口对行业全景做全量刷新；重大结构性事件触发器命中时提前插刷对应模块。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：刷新版报告落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY}}_annual.md`）；插刷件 `reports/{{YYYY-MM-DD}}-主题.md`（命名不在标准正则内，validate 仅 WARN 不阻断，属预期）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [年度刷新类型模板（行业深度研究型）](../../../report_templates/industry-research/prompt-annual-refresh-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{PREVIOUS_REPORT_PATH}} = 上一年度刷新版路径（首年刷新时为空，仅锚定基线）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO）
{{OUTPUT_PATH}}          = reports/{{YYYY}}_annual.md
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：完成「口径复核 → 数据刷新 → 格局更新 → 趋势复判」闭环；上年趋势判断逐条对照实际进展（命中 / 部分命中 / 未命中），复判结论与依据并列，**上年判断原文保留不删除**；九节结构与基线逐字一致；无触发且窗口未到时不启动，不得虚构变化。

## 一、各模块更新要点（业务实例化，TODO 按九节展开）

- **产业链**（TODO：环节进出、价值分布迁移、传导关系变化）。
- **规模与格局**（TODO：最新口径规模与增速、集中度变化、口径修订留痕）。
- **玩家**（TODO：清单复核与进出登记、逐家要点更新）。
- **驱动与风险**（TODO：证据更新、新增风险、失效驱动归档）。
- **趋势**（TODO：上年复判 + 新趋势推导，反向声音至少 2 条）。

## 二～六、协议与交付

更新协议与命名见[年度刷新类型模板](../../../report_templates/industry-research/prompt-annual-refresh-template.md)第二、四节；渲染交付同基线提示词第十节。

---
## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成行业深度研究型业务提示词脚手架 |
