# 业务提示词脚手架（舆情传播监测型）

> **用途**：为舆情传播监测型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将本文件各节复制为 `{REGION}/{PROPERTY}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{REGION}/{PROPERTY}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-monthly-monitor.md`；复制第五节 → `prompts/prompt-flash-warning.md`（可选，预警专项）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立舆情台账与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 品牌公关 / 政府事务 / IR（TODO：按业务收窄） | 报告须声明受众 |
| 渠道清单 | 监测渠道与覆盖声明（TODO：逐渠道） | 声量结构以渠道为维 |
| 议题与关键词 | 议题编号 + 关键词组（TODO） | 环比口径以关键词组固定为前提 |
| 预警触发器 | `信号命中 → 受影响模块`（TODO：声量阈值 / 情感阈值 / 突发负面） | 命中即升级 |
| 来源优先级 | ① 媒体数据库 ② 社交平台 ③ 公开抓取（附抓取时间）（TODO：渠道清单） | 舆情热度 ≠ 事实，须交叉验证 |
| 情感判定 | 工具 + 人工复核混合方法与抽样比例（TODO） | 误差边界须声明 |
| 追踪表 | 监测议题 × 优先渠道（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md 脚手架（复制为 prompts/prompt-baseline-setup.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 首期基线报告提示词（舆情传播监测型）

> **用途**：执行「{{REGION}} {{TOPIC}} 舆情持续监测机制」的**机制建立**任务：产出首期舆论场基线报告与配套舆情台账。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文九节基线报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}_baseline_report.md`）+ 舆情台账（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [基线报告类型模板（舆情传播监测型）](../../../report_templates/sentiment-monitoring/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期，格式 YYYY-MM-DD
{{BASELINE_DATE}}        = 首期基线日期
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO：台账文件名）
{{REPORT_VERSION}}       = v1.0（首期基线固定）
```

**任务目标**：产出九节舆论场基线报告（渠道声量结构、议题基线声量、情感分布）与台账首建；固定声明「舆情热度不等于市场真实状况」；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

## 一、项目专属硬性约束

1. **言论≠事实**：报告输出舆论态势与风险预警，重大结论须与量化指标交叉验证。
2. **结论边界**：不做「公众必然如何反应」断言；不基于舆情给出投资或决策建议；情感判定方法与误差边界须声明。
3. **受众定位**：见[业务配置](./business-config.md)（TODO：实例化）。

## 二、来源优先级

见[业务配置](./business-config.md)（TODO：① 媒体数据库 ② 社交平台 ③ 公开抓取）；每格活值附 `[来源, 抓取日期]`。

## 三～九、结构骨架与联动

九节固定骨架见[基线类型模板第三节](../../../report_templates/sentiment-monitoring/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后逐字继承）；议题与渠道追踪表见[业务配置](./business-config.md)（TODO）。

## 十、渲染与交付

- md + 自包含 HTML（`python src/prompts-tools/tools/md2html.py`）；HTML 须通过 `python src/prompts-tools/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 四、prompt-monthly-monitor.md 脚手架（复制为 prompts/prompt-monthly-monitor.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 舆情月报提示词（舆情传播监测型 · 主更新节拍）

> **用途**：周期性（每月）刷新声量与情感读数、热点事件榜与预警状态。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文九节更新版报告，落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [周期更新类型模板（舆情传播监测型）](../../../report_templates/sentiment-monitoring/prompt-monthly-update-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{PREVIOUS_REPORT_PATH}} = 最近一期月报路径（首期更新时为空，仅锚定基线）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO）
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：完成「抓取 → 判定 → 对比 → 预警」闭环；环比须与基线期同渠道、同关键词组、同口径（口径变更显式标注并保留对照）；九节结构与基线逐字一致；无预警命中时降级为核验轻运行，不得虚构变化。

## 一、各模块更新要点（业务实例化，TODO 按九节展开）

- **舆论场结构**（TODO：渠道声量变化、新渠道、关键参与方变动）。
- **议题声量**（TODO：环比 / 同比、新议题登记、旧议题降温归档）。
- **情感判定**（TODO：分布变化、规则命中、人工复核抽样结果）。
- **风险预警**（TODO：信号命中状态、热点事件榜、意见领袖观点摘编附原文链接、交叉验证结论）。

## 二～六、协议与交付

更新协议与命名见[周期类型模板](../../../report_templates/sentiment-monitoring/prompt-monthly-update-template.md)第二、四节；渲染交付同基线提示词第十节。

---

## 五、prompt-flash-warning.md 脚手架（可选，复制为 prompts/prompt-flash-warning.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 预警专项提示词（舆情传播监测型）

> **用途**：突发负面热点当期核实（确认非机器人 / 断章取义）与专项预警，不等待月度窗口。
> **产出**：专项预警件 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md`）+ 台账增量回写。命名不在标准正则内，validate 仅 WARN 不阻断，属预期。

## 运行变量

```
{{CURRENT_DATE}} = 本次执行日期
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}_baseline_report.md
{{PREVIOUS_REPORT_PATH}} = 最近一期月报路径
{{REGISTRY_PATH}} = data/（TODO）
{{OUTPUT_PATH}} = reports/{{YYYY-MM-DD}}-（TODO：事件主题）.md
{{REPORT_VERSION}} = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：按[周期类型模板第一节事件触发档](../../../report_templates/sentiment-monitoring/prompt-monthly-update-template.md)执行对应模块重点刷新；完成人工复核与台账回写。

---
## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成舆情传播监测型业务提示词脚手架 |
