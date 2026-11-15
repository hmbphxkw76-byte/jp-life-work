# 业务提示词脚手架（快评·事件点评型）

> **用途**：为快评·事件点评型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将本文件各节复制为 `{REGION}/{PROPERTY}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{REGION}/{PROPERTY}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`（**基线期只建机制，不出快评正文**）；复制第四节 → `prompts/prompt-flash-note.md`（快评正文统一入口）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立事件日历与预期台账。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 需要快速反应的决策者 / 投资者（TODO：按业务收窄） | 报告须声明受众 |
| 事件监测日历 | 定期事件（数据发布 / 会议 / 财报窗口：名称 / 频次 / 窗口 / 官方渠道 URL）+ 不定期事件类型（TODO） | 逐渠道附 URL |
| 预期台账 | 事件类型 → 共识预期 / 官方目标值 → 依据来源 → 更新时效（TODO） | 无可靠预期登记「无预期」，不虚构共识值 |
| 时效标准 | 72h 上限内目标时效（TODO） | 宁可延迟，不可转述直引 |
| 升级规则 | 偏离阈值 → 快评升级为深度报告 / 期报联动（TODO） | 快评只登记偏离信号 |
| 篇幅上限 | 快评正文上限（TODO：一般 1–3 页） | 四段式固定结构 |
| 来源优先级 | ① 官方发布稿 / 财报原文（唯一即时采信） ② 预期台账 ③ 媒体转述禁单源直引（TODO） | 事后补验流程须登记 |
| 追踪表 | 事件类型 × 预期来源 × 更新时效（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md 脚手架（复制为 prompts/prompt-baseline-setup.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 快评机制建立提示词（快评·事件点评型）

> **用途**：执行「{{REGION}} {{TOPIC}} 快评机制」的**机制建立**任务：产出快评机制基线文档（事件监测日历、预期台账、快评框架）。**基线期不出快评正文**，只建机制。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：机制文档（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}_baseline_report.md`）+ 预期台账（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [基线报告类型模板（快评·事件点评型）](../../../report_templates/flash-commentary/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{BASELINE_DATE}}        = 首期基线日期
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO：预期台账文件名）
{{REPORT_VERSION}}       = v1.0（首期基线固定）
```

**任务目标**：产出八节机制文档（事件监测日历、预期台账首建、快评四段式框架、信号与升级规则、来源与时效治理）；**核验底线**为「官方发布稿 / 财报原文为准」，转述信息单源直引为硬性禁止；运行后回写 `{{REGISTRY_PATH}}`；基线文档**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

## 一、项目专属硬性约束

1. **初步判断纪律**：快评输出快速影响判断，一律标「初步判断，待后续报告验证」；单份快评不推翻既有深度结论。
2. **受众定位**：见[业务配置](./business-config.md)（TODO：实例化）。

## 二、来源与时效治理

官方发布渠道清单与事后补验流程见[业务配置](./business-config.md)（TODO）；时效取舍遵循 {{FRESHNESS_PRIORITY}}。

## 三～八、结构骨架与联动

八节固定骨架见[基线类型模板第三节](../../../report_templates/flash-commentary/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后逐字继承）；预期台账追踪表见[业务配置](./business-config.md)（TODO）。

## 九、渲染与交付

- md + 自包含 HTML（`python src/prompts-tools/tools/md2html.py`）；HTML 须通过 `python src/prompts-tools/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 四、prompt-flash-note.md 脚手架（复制为 prompts/prompt-flash-note.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 快评正文提示词（快评·事件点评型 · 事件触发）

> **用途**：重大事件（数据发布、政策出台、财报披露、突发事件）发生后 72 小时内输出单份快评。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：快评正文（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM-DD}}-主题-快评.md`）。命名不在标准正则内，validate 仅 WARN 不阻断，属预期。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [快评正文类型模板（快评·事件点评型）](../../../report_templates/flash-commentary/prompt-flash-note-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{EVENT_NAME}}           = 本次事件名称（TODO）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO）
{{OUTPUT_PATH}}          = reports/{{YYYY-MM-DD}}-（TODO：主题）-快评.md
{{REPORT_VERSION}}       = 本次版本号（vYYYY.MM.DD + 完成时间）
```

**任务目标**：完成「事件核验 → 预期对比 → 初步判断 → 观察点登记」闭环；**核验先行**——官方原文可得前不输出快评；无事件窗口不启动，台账标注「截至 {{CURRENT_DATE}} 无更新」。

## 一、四段式正文结构（固定顺序，不得增删段）

1. **事件摘要**：事件事实（何时、官方发布渠道与 URL、原文关键数据）；只记事实，不解读。
2. **预期对比**：台账预期值 vs 实际值（偏离方向与幅度）；无预期项声明「无可靠预期」；口径提示。
3. **初步影响判断**：传导方向判断（标「初步判断，待后续报告验证」）；依据 1–3 条；反向情形说明。
4. **后续观察点**：后续盯什么（指标 / 事件 / 时点）；升级条件命中评估。

## 二～五、协议与交付

快评协议与事后补验见[快评正文类型模板](../../../report_templates/flash-commentary/prompt-flash-note-template.md)第二、五节；完成后立即回写预期台账（实际值 + 偏离）并评估升级条件；渲染交付同基线提示词第九节。

---
## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成快评·事件点评型业务提示词脚手架 |
