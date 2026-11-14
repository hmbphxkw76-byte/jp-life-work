# 业务提示词脚手架（政策法规解读型）

> **用途**：为政策法规解读型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将本文件各节复制为 `{REGION}/{PROPERTY}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{REGION}/{PROPERTY}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-policy-review.md`（事件触发解读 + 年度台账复盘统一入口）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立政策台账与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 合规团队 / 政府事务 / 受影响企业与个人（TODO：按业务收窄） | 报告须声明受众 |
| 监测法规清单 | 法规名称 / 层级 / 状态（TODO） | 台账逐项维护 |
| 官方发布渠道 | 公报 / 法规数据库清单，逐渠道附 URL 与更新机制（TODO） | 官方原文为唯一采信层 |
| 解读触发器 | `渠道 / 政策名称 → 动作`（TODO：新发布 / 修订 / 征求意见稿 / 生效） | 征求意见稿标「非最终文本」 |
| 影响对象矩阵 | 政策 × 受影响主体 × 方向 / 量级 / 依据条款（TODO） | 逐格附条款依据 |
| 来源优先级 | ① 官方公报 / 法规数据库 ② 立法记录 ③ 媒体转述仅线索（TODO） | 引用逐条附官方原文 URL |
| 追踪表 | 监测法规 × 发布渠道 × 状态（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md 脚手架（复制为 prompts/prompt-baseline-setup.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 首期基线报告提示词（政策法规解读型）

> **用途**：执行「{{REGION}} {{TOPIC}} 政策解读机制」的**机制建立**任务：产出首期监管框架基线报告与配套政策台账。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文九节基线报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}_baseline_report.md`）+ 政策台账（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [基线报告类型模板（政策法规解读型）](../../../report_templates/policy-analysis/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{BASELINE_DATE}}        = 首期基线日期
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO：政策台账文件名）
{{REPORT_VERSION}}       = v1.0（首期基线固定）
```

**任务目标**：产出九节监管框架基线报告（框架地图、重点政策逐条解读、影响对象矩阵、合规建议、生效时间线）与政策台账首建；**官方原文铁律**：全部引用回溯官方公报 / 法规数据库原文并附 URL，媒体转述仅作线索；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

## 一、项目专属硬性约束

1. **只盯官方文本**：不采集舆论反应（那是舆情监测型的边界）；解读以官方原文为准，原文有歧义处并列多解，不静默择一。
2. **结论边界**：不构成法律意见；合规应对建议标「建议」；重大合规决策提示咨询执业法律专业人士。
3. **受众定位**：见[业务配置](./business-config.md)（TODO：实例化）。

## 二、来源优先级

见[业务配置](./business-config.md)（TODO：① 官方公报 / 法规数据库 ② 立法记录 ③ 媒体转述线索）；每格活值附 `[官方原文 URL, 版本日期]`。

## 三～九、结构骨架与联动

九节固定骨架见[基线类型模板第三节](../../../report_templates/policy-analysis/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后逐字继承）；追踪表见[业务配置](./business-config.md)（TODO）。

## 十、渲染与交付

- md + 自包含 HTML（`python prompts/tools/md2html.py`）；HTML 须通过 `python prompts/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 四、prompt-policy-review.md 脚手架（复制为 prompts/prompt-policy-review.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 政策解读提示词（政策法规解读型 · 事件触发 + 年度复盘）

> **用途**：事件触发单份解读（新政策 / 修订 / 配套细则出台后）与年度台账复盘统一入口。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：单份解读件 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md`）或年度复盘（`reports/{{YYYY-MM}}-<slug>.md` + 台账年度新版另存不覆盖）。解读件命名不在标准正则内，validate 仅 WARN 不阻断，属预期。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [事件触发解读类型模板（政策法规解读型）](../../../report_templates/policy-analysis/prompt-policy-review-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{TRIGGER_TYPE}}         = 本次触发类型（新政策 / 修订 / 细则 / 年度复盘，TODO）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}_baseline_report.md
{{PREVIOUS_REPORT_PATH}} = 上期解读 / 复盘路径（如无则空，仅锚定基线）
{{REGISTRY_PATH}}        = data/（TODO）
{{OUTPUT_PATH}}          = 由 {{TRIGGER_TYPE}} 决定（见用途）
{{OUTPUT_REGISTRY}}      = 年度复盘时填写（台账年度新版路径）
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：完成「原文回溯 → 逐条解读 → 影响评估 → 台账更新」闭环；新政策先登记发布与生效日期、官方 URL 后才可进入解读；征求意见稿登记但标注「非最终文本，以正式发布为准」；无触发时不启动新解读，台账标注「截至 {{CURRENT_DATE}} 无更新」。

## 一、各模块要点（业务实例化，TODO 按类型模板第三节框架展开）

- **政策原文**（TODO：发布机构、文号、日期、适用范围、关键条款摘编逐条附 URL）。
- **逐条解读**（TODO：条款含义、新旧制度衔接对照、歧义多解、官方答问对照）。
- **影响评估**（TODO：影响对象矩阵增量、过渡期与合规时点）。
- **应对建议**（TODO：合规要点、待明确事项清单，标「建议」）。

## 二～六、协议与交付

更新协议与命名见[事件触发解读类型模板](../../../report_templates/policy-analysis/prompt-policy-review-template.md)第二、四节；渲染交付同基线提示词第十节。

---
## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成政策法规解读型业务提示词脚手架 |
