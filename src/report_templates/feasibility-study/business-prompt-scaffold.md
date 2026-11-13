# 业务提示词脚手架（可行性与市场进入型）

> **用途**：为可行性与市场进入型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将本文件各节复制为 `{REGION}/{PROPERTY}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{REGION}/{PROPERTY}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-project-study.md`（项目论证 + 项目复盘统一入口）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立评估框架档案与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 企业决策层 / 项目发起人（TODO：明确授权决策方） | 不构成对不特定公众的建议 |
| 评估维度与权重 | 市场 / 技术 / 财务 / 法规 / 运营各维度权重（TODO） | 框架档案制度化 |
| Go/No-Go 判定标准 | 阈值与打分规则（TODO） | 建议必须逐项对照打分 |
| 财务测算假设 | 投资额 / 成本 / 收入假设与依据（TODO） | 全假设可审计，三情景 |
| 可引用报告清单 | 本仓行业 / 规模 / 政策 / 竞争报告清单（TODO） | 引用注明来源报告与口径 |
| 复盘时点 | 项目实施后复盘窗口（TODO） | 假设回验必执行 |
| 来源优先级 | ① 本仓类型报告引用 ② 实地 / 当地访谈 ③ 二手行业数据 ④ 财务假设（TODO） | 缺口项标「本项目专项调研」 |
| 追踪表 | 评估维度 × 判定标准 × 结论（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md 脚手架（复制为 prompts/prompt-baseline-setup.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 首期可行性论证提示词（可行性与市场进入型）

> **用途**：执行「{{REGION}} {{TOPIC}} 可行性评估机制」的**机制建立**任务：产出首期可行性论证报告与配套评估框架档案。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文九节论证报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}_baseline_report.md`）+ 评估框架档案（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [基线报告类型模板（可行性与市场进入型）](../../../report_templates/feasibility-study/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{BASELINE_DATE}}        = 首期基线日期
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO：框架档案文件名）
{{REPORT_VERSION}}       = v1.0（首期基线固定）
```

**任务目标**：产出九节可行性论证报告（评估框架、市场 / 技术运营 / 财务 / 法规可行性、风险与缓解、结论与路线图）与框架档案首建；**必须收敛到单一 Go / No-Go / 有条件 Go 建议**（不允许双向平衡不表态），与完整风险清单并存；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

## 一、项目专属硬性约束

1. **集成纪律**：市场、规模、政策输入优先引用本仓其他类型报告的最新版（注明来源报告与口径），不重复推导；缺口项专项补充并标注「本项目专项调研」。
2. **结论边界**：仅对授权决策方负责；「有条件 Go」须列明条件清单与验证时点；财务测算全假设可审计、三情景呈现。
3. **受众定位**：见[业务配置](./business-config.md)（TODO：实例化）。

## 二、来源优先级

见[业务配置](./business-config.md)（TODO：① 本仓报告引用 ② 实地 / 当地访谈 ③ 二手行业数据 ④ 财务假设）；每格活值附 `[来源, 时点]`。

## 三～九、结构骨架与联动

九节固定骨架见[基线类型模板第三节](../../../report_templates/feasibility-study/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后逐字继承）；追踪表见[业务配置](./business-config.md)（TODO）。

## 十、渲染与交付

- md + 自包含 HTML（`python prompts/tools/md2html.py`）；HTML 须通过 `python prompts/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 四、prompt-project-study.md 脚手架（复制为 prompts/prompt-project-study.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 项目论证提示词（可行性与市场进入型 · 项目制）

> **用途**：项目制论证统一入口——新市场进入、新产品线、新设点等一次性项目（当次项目范围由业务配置或运行时变量指定）；另覆盖项目实施后复盘。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：项目论证件 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM-DD}}-主题.md`）或复盘件 `reports/{{YYYY-MM-DD}}-主题-复盘.md`（+ 同名 html）。命名不在标准正则内，validate 仅 WARN 不阻断，属预期。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../../report_templates/prompt-generic-base.md) × [监测报告通用规范](../../../report_templates/monitoring-common-spec.md) × [项目论证类型模板（可行性与市场进入型）](../../../report_templates/feasibility-study/prompt-study-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{PROJECT_TYPE}}         = 本次类型（新项目论证 / 项目复盘，TODO：项目名称）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}_baseline_report.md
{{REGISTRY_PATH}}        = data/（TODO）
{{OUTPUT_PATH}}          = 由 {{PROJECT_TYPE}} 决定（见用途）
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：按[项目论证类型模板](../../../report_templates/feasibility-study/prompt-study-template.md)项目协议执行「框架复核 → 多维论证 → 打分判定 → Go/No-Go」闭环；评估维度与判定标准复用基线（调整须声明理由）；复盘档完成假设回验与判定标准有效性复核；运行后回写框架档案。

## 一、各模块要点（业务实例化，TODO 按 {{PROJECT_TYPE}} 展开）

- **市场可行性**（TODO：需求容量、目标客群、竞争强度、进入壁垒）。
- **技术与运营**（TODO：资源可得性、关键依赖、运营假设清单）。
- **财务测算**（TODO：投资额、成本收入假设、回收期 / 内部收益率三情景）。
- **法规合规**（TODO：许可与资质清单、合规路径与时点）。
- **判定**（TODO：逐维度打分、Go / No-Go / 有条件 Go、条件清单与验证时点、实施路线图）。

## 二～六、协议与交付

交付包 = 报告（含判定打分表）+ 假设清单附录；结论与风险清单同时呈现；渲染交付同基线提示词第十节。

---
## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成可行性与市场进入型业务提示词脚手架 |
