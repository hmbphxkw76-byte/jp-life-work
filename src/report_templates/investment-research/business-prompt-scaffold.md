# 业务提示词脚手架（投资分析与尽调型）

> **用途**：为投资分析与尽调型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将本文件各节复制为 `{TOPIC_DIR}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{TOPIC_DIR}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-target-review.md`（定期复核 + 事件触发统一入口）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词（首次覆盖），建立标的档案与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 授权决策方（投委会 / 项目负责人）（TODO：明确） | 不构成对不特定公众的邀约 |
| 标的清单与监测项 | 标的概况 / 财务序列 / 假设 / 风险监测项（TODO） | 档案逐项维护 |
| 复核节拍 | 定期复核窗口（季度 / 年度）+ 事件触发器（TODO：并购 / 管理层变动 / 诉讼 / 政策冲击） | 重大事项当期复核 |
| 估值方法与假设 | 收益法 / 可比法参数与依据（TODO） | 全假设可审计 |
| 非公开信息规则 | 使用授权与标注方式（TODO） | 逐处标注授权依据 |
| 来源优先级 | ① 官方披露（公告 / 财报 / 监管文件） ② 授权数据室 / 访谈 ③ 行业二手（TODO） | 媒体转述仅作线索 |
| 追踪表 | 标的监测项 × 信息渠道（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md 脚手架（复制为 prompts/prompt-baseline-setup.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 首次覆盖提示词（投资分析与尽调型）

> **用途**：执行「{{REGION}} {{TOPIC}} 标的覆盖机制」的**机制建立**任务：产出首期标的覆盖报告（首次覆盖）与配套标的档案。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文八节覆盖报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md`）+ 标的档案（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../src/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../src/report_templates/monitoring-common-spec.md) × [基线报告类型模板（投资分析与尽调型）](../../src/report_templates/investment-research/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{BASELINE_DATE}}        = 首期基线日期
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}        = data/（TODO：标的档案文件名）
{{REPORT_VERSION}}       = v1.0（首期基线固定）
```

**任务目标**：产出八节首次覆盖报告（投资要点、标的概况、行业输入、财务与估值、风险清单、情景与敏感性、合规与免责）与标的档案首建；**结论必须明确**（评级 / 建议 / 估值区间）且与完整风险清单并存；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

## 一、项目专属硬性约束

1. **结论边界**：报告声明「不构成对不特定公众的投资邀约」，仅服务授权决策方；重大未决事项存在时结论降级为「有条件结论」并披露。
2. **估值纪律**：估值模型全假设可审计；估值区间多方法并列；情景为三档（乐观 / 基准 / 悲观）。
3. **合规**：信息来源合法性声明、利益冲突声明；非公开信息使用逐处标注授权依据。
4. **受众定位**：见[业务配置](./business-config.md)（TODO：实例化）。

## 二、来源优先级

见[业务配置](./business-config.md)（TODO：① 官方披露 ② 授权数据室 / 访谈 ③ 行业二手）；事件核实以官方披露原文为准。

## 三～八、结构骨架与联动

八节固定骨架见[基线类型模板第三节](../../src/report_templates/investment-research/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后逐字继承）；追踪表见[业务配置](./business-config.md)（TODO）。

## 九、渲染与交付

- md + 自包含 HTML（`python src/prompts-tools/tools/md2html.py`）；HTML 须通过 `python src/prompts-tools/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 四、prompt-target-review.md 脚手架（复制为 prompts/prompt-target-review.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 标的复核提示词（投资分析与尽调型 · 定期复核 + 事件触发）

> **用途**：定期复核（财报 / 定期数据窗口）与事件触发复核（重大事项披露后）统一入口。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：更新版报告 `reports/{{YYYY-MM}}-<slug>.md`（+ 同名 html，由业务配置规定）或事件专项修订件 `reports/{{YYYY-MM}}-<slug>.md`（命名不在标准正则内，validate 仅 WARN 不阻断，属预期）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../src/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../src/report_templates/monitoring-common-spec.md) × [事件触发更新类型模板（投资分析与尽调型）](../../src/report_templates/investment-research/prompt-target-update-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{TRIGGER_TYPE}}         = 本次触发类型（定期复核 / 事件名称，TODO）
{{PREVIOUS_REPORT_PATH}} = 最近一期更新版路径（首次复核时为空，仅锚定首次覆盖）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}        = data/（TODO）
{{OUTPUT_PATH}}          = 见用途（由 {{TRIGGER_TYPE}} 决定）
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：完成「事件核验 → 假设复核 → 估值更新 → 结论修订」闭环；估值假设变更逐条留痕（旧值 → 新值 → 依据）；只修参数与假设、不推翻模型结构（结构变更走重新覆盖）；结论变化方向（维持 / 上调 / 下调 / 降级为有条件）显式声明；无触发且窗口未到时登记册标注「截至 {{CURRENT_DATE}} 无更新」。

## 一、各模块更新要点（业务实例化，TODO 按八节展开）

- **标的概况**（TODO：股权与治理变动、合同与资质变化）。
- **财务与估值**（TODO：最新财务序列、假设逐条复核、估值区间更新）。
- **风险登记**（TODO：新增风险、已缓解归档、重大未决事项状态）。
- **结论复核**（TODO：投资要点逐条对照新证据、情景与敏感性重算、反向声音更新）。

## 二～六、协议与交付

更新协议与命名见[事件触发更新类型模板](../../src/report_templates/investment-research/prompt-target-update-template.md)第二、四节；渲染交付同基线提示词第九节。

---

## 六、落盘后审计（提交前必做，适用于本脚手架全部提示词）

落盘后依次运行 `python src/prompts-tools/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python src/prompts-tools/tools/audit_preflight.py --report <报告相对路径>`、`python src/prompts-tools/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python src/prompts-tools/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

> 复制到业务 `prompts/` 后，须在**每一份**业务提示词末尾保留本节（与类型模板同口径）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成投资分析与尽调型业务提示词脚手架 |
