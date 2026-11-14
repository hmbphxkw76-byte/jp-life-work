# 业务提示词脚手架（竞争情报监测型）

> **用途**：为竞争情报监测型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将本文件各节复制为 `{REGION}/{PROPERTY}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**（业务提示词目录）书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{REGION}/{PROPERTY}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-monthly-monitor.md`；复制第五节 → `prompts/prompt-flash-update.md`（可选，事件触发专项）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立竞品档案库与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}（如 `data/{主题}_registry.md`）、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 产品 / 市场 / 战略团队（TODO：按业务收窄） | 报告须声明受众 |
| 监测竞品清单 | 直接 / 间接 / 潜在进入者分层与入选标准（TODO） | 档案卡逐家维护 |
| 信号触发器 | `事件 → 受影响模块`（TODO：融资 / 并购 / 换帅 / 定价重构 / 新产品线等） | 命中即升级 |
| 来源优先级 | ① 官网 / 财报 / 公告 ② 招聘 / 应用商店 / 专利 ③ 第三方研究 ④ 公开社媒（TODO：机构清单） | 只用公开合法信息 |
| 口径清单 | 份额口径、动作登记字段（编号 + 玩家 + 动作 + 日期 + 来源 URL）（TODO） | 多口径并列 |
| 追踪表 | 监测竞品 × 优先信息渠道（TODO：逐家列渠道） | 回写 {{REGISTRY_PATH}} |
| 已修正事实清单 | 首期为空，产生修正后逐条补记 | 无来源不得入清单 |

---

## 三、prompt-baseline-setup.md 脚手架（复制为 prompts/prompt-baseline-setup.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 首期基线报告提示词（竞争情报监测型）

> **用途**：执行「{{REGION}} {{TOPIC}} 竞争情报持续监测机制」的**机制建立**任务：产出首期竞争格局基线报告与配套竞品档案库。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文九节基线报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}_baseline_report.md`）+ 竞品档案库（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [基线报告类型模板（竞争情报监测型）](../../../report_templates/competitive-intelligence/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。质量规则见通用基座与通用规范；基线差异与九节骨架见基线类型模板；业务变量、监测竞品清单、触发器、来源优先级见业务配置；冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期，格式 YYYY-MM-DD
{{BASELINE_DATE}}        = 首期基线日期
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO：档案库文件名）
{{REPORT_VERSION}}       = v1.0（首期基线固定）
```

**任务目标**：产出九节竞争格局基线报告与竞品档案库首建。覆盖业务配置声明的全部监测竞品（逐家档案卡，每格附 `[来源, 日期]`）；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

## 一、项目专属硬性约束

1. **信息边界**：只采集公开合法信息（官网、财报、招聘、应用商店、专利、公开社媒）；不使用非公开渠道。
2. **结论边界**：威胁 / 机会提示标「判断 / 推断」，与事实分离；不做对手成败断言。
3. **受众定位**：见[业务配置](./business-config.md)（TODO：实例化）。

## 二、来源优先级

见[业务配置](./business-config.md)（TODO：① 官网/财报/公告 ② 招聘/应用商店/专利 ③ 第三方研究 ④ 公开社媒）；关键动作至少 2 家独立来源确认，单源标「单源待证」。

## 三～九、结构骨架与联动

九节固定骨架见[基线类型模板第三节](../../../report_templates/competitive-intelligence/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后逐字继承）；追踪表见[业务配置](./business-config.md)（TODO）。

## 十、渲染与交付

- md + 自包含 HTML（仓库根目录执行 `python prompts/tools/md2html.py`）；HTML 须通过 `python prompts/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 四、prompt-monthly-monitor.md 脚手架（复制为 prompts/prompt-monthly-monitor.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 月度更新提示词（竞争情报监测型 · 主更新节拍）

> **用途**：周期性（每月）刷新竞争动态矩阵与竞品档案；重大动作触发器命中时亦走本提示词做对应模块重点更新。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文九节更新版报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [周期更新类型模板（竞争情报监测型）](../../../report_templates/competitive-intelligence/prompt-monthly-update-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期，格式 YYYY-MM-DD
{{PREVIOUS_REPORT_PATH}} = 最近一期月度报告路径（首期更新时为空，仅锚定基线）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO）
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：以公开来源为依据、以上一期报告与首期基线为对比锚，完成「采集 → 核验 → 矩阵刷新 → 影响提示」闭环；九节结构与基线逐字一致；继承已修正事实清单；无触发器命中且无新动作时降级为核验轻运行（登记册标注「截至 {{CURRENT_DATE}} 无更新」），不得虚构变化。

## 一、各模块更新要点（业务实例化，TODO 按九节展开）

- **竞争格局**（TODO：份额口径更新、新进入者 / 退出者）。
- **竞品档案**（TODO：产品矩阵、定价与促销、渠道生态、组织与人事、招聘动向）。
- **动态矩阵**（TODO：本期动作逐条登记，编号 + 玩家 + 动作 + 日期 + 来源 URL；信号规则命中状态）。
- **影响提示**（TODO：威胁 / 机会，标「判断 / 推断」）。

## 二～六、协议与交付

更新协议与命名见[周期类型模板](../../../report_templates/competitive-intelligence/prompt-monthly-update-template.md)第二、四节；追踪表逐项核对回写 `{{REGISTRY_PATH}}`；渲染交付同基线提示词第十节。

---

## 五、prompt-flash-update.md 脚手架（可选，复制为 prompts/prompt-flash-update.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 事件触发专项提示词（竞争情报监测型）

> **用途**：重大竞品动作（融资 / 并购 / 换帅 / 定价重构 / 新产品线）当期核实与专项更新，不等待月度窗口。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：专项更新件 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md`）+ 档案库增量回写。命名不在工具链标准正则内，validate 仅 WARN 不阻断，属预期。

## 运行变量

```
{{CURRENT_DATE}} = 本次执行日期
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}_baseline_report.md
{{PREVIOUS_REPORT_PATH}} = 最近一期月度报告路径
{{REGISTRY_PATH}} = data/（TODO）
{{OUTPUT_PATH}} = reports/{{YYYY-MM-DD}}-（TODO：事件主题）.md
{{REPORT_VERSION}} = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：按[周期类型模板第一节事件触发档](../../../report_templates/competitive-intelligence/prompt-monthly-update-template.md)执行对应模块重点刷新；事实与判断分离，完成档案库回写与升级记录。

---
## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成竞争情报监测型业务提示词脚手架 |
