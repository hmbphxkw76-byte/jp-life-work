# 业务提示词脚手架（市场规模测算与预测型）

> **用途**：为市场规模测算与预测型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将本文件各节复制为 `{REGION}/{PROPERTY}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{REGION}/{PROPERTY}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-annual-refresh.md`（含失效信号插刷说明）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立测算模型档案与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 创业者 / 投资人 / 产品战略（TODO：按业务收窄） | 报告须声明受众 |
| 市场定义与边界 | 含 / 不含清单、测算路径选择（TODO） | 口径底座制度化 |
| 假设清单 | 逐条假设：依据 / 强度 / 失效信号（TODO） | 每个数字可追溯到假设 |
| 回测规则 | 回测周期、偏差容忍度、校准动作（TODO） | 年度刷新必执行 |
| 插刷触发器 | `失效信号 → 受影响模块`（TODO） | 命中即专项修订 |
| 来源优先级 | ① 官方统计 ② 第三方数据 ③ 自建假设（逐条附依据与估计方法）（TODO） | 无依据参数标「估计值」 |
| 追踪表 | 模型参数 × 取值依据（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md 脚手架（复制为 prompts/prompt-baseline-setup.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 首期基准测算提示词（市场规模测算与预测型）

> **用途**：执行「{{REGION}} {{TOPIC}} 市场测算机制」的**机制建立**任务：产出首期基准测算报告与配套测算模型档案。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文九节基线报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}_baseline_report.md`）+ 模型档案（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [基线报告类型模板（市场规模测算与预测型）](../../../report_templates/market-sizing/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{BASELINE_DATE}}        = 首期基线日期
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO：模型档案文件名）
{{REPORT_VERSION}}       = v1.0（首期基线固定）
```

**任务目标**：产出九节基准测算报告（方法与模型结构、口径底座、基准年测算、三情景预测、敏感性）与模型档案首建；**核心交付物是可审计的测算模型**——每个数字可追溯到假设与来源；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

## 一、项目专属硬性约束

1. **区间纪律**：测算与预测一律以区间 + 三情景（乐观 / 基准 / 悲观）呈现，不给单一「神数字」；全部预测标「推断」。
2. **结论边界**：不做投资评级、不出具进入决策建议（边界归投资尽调型、可行性型）。
3. **口径纪律**：多口径并列不合并，选用口径须声明理由；无依据参数标「估计值 + 估计方法」。
4. **受众定位**：见[业务配置](./business-config.md)（TODO：实例化）。

## 二、来源优先级

见[业务配置](./business-config.md)（TODO：① 官方统计 ② 第三方数据 ③ 自建假设）；模型透明度优先于数字精确度。

## 三～九、结构骨架与联动

九节固定骨架见[基线类型模板第三节](../../../report_templates/market-sizing/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后逐字继承）；参数追踪表见[业务配置](./business-config.md)（TODO）。

## 十、渲染与交付

- md + 自包含 HTML（`python src/prompts-tools/tools/md2html.py`）；HTML 须通过 `python src/prompts-tools/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 四、prompt-annual-refresh.md 脚手架（复制为 prompts/prompt-annual-refresh.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 年度假设刷新提示词（市场规模测算与预测型）

> **用途**：每年固定窗口对模型假设做刷新与回测；关键假设失效信号触发器命中时专项插刷。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：刷新版报告落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md`）+ 模型档案年度新版（另存不覆盖）；插刷件 `reports/{{YYYY-MM}}-<slug>.md`（命名不在标准正则内，validate 仅 WARN 不阻断，属预期）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [年度刷新类型模板（市场规模测算与预测型）](../../../report_templates/market-sizing/prompt-annual-refresh-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{PREVIOUS_REPORT_PATH}} = 上一年度刷新版路径（首年刷新时为空，仅锚定基线）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO）
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md
{{OUTPUT_REGISTRY}}      = data/（TODO：模型档案年度新版文件名）
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：完成「假设审计 → 回测对照 → 参数刷新 → 预测修订」闭环；上年预测（各情景）逐条与实际值对照，偏差归因（假设失效 / 口径修订 / 结构突变），**上年预测原文保留不删除**；只修参数与假设、不推翻模型结构（结构变更走新基线）；无失效信号且窗口未到时不启动。

## 一、各模块更新要点（业务实例化，TODO 按九节展开）

- **口径底座**（TODO：最新可得口径、口径修订留痕、新数据源评估）。
- **假设审计**（TODO：每条假设现状——成立 / 弱化 / 失效、依据更新、失效信号命中）。
- **参数刷新**（TODO：取值更新附新依据、敏感性重算）。
- **预测修订**（TODO：三情景区间修订、与上年偏差归因）。

## 二～六、协议与交付

更新协议与命名见[年度刷新类型模板](../../../report_templates/market-sizing/prompt-annual-refresh-template.md)第二、四节；渲染交付同基线提示词第十节。

---
## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成市场规模测算与预测型业务提示词脚手架 |
