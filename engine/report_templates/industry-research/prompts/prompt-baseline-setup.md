# {{REGION}} · {{TOPIC}} · 首期基线报告提示词（行业深度研究型 · 泛用版）

> **用途**：执行「{{REGION}} {{TOPIC}} 行业研究机制」的**机制建立**任务：产出首期行业全景基线报告与配套研究边界档案。泛用版业务提示词：建新业务线时复制本文件至 `{TOPIC_DIR}/prompts/`，替换变量与 TODO 后即可运行。
> **产出**：中文九节基线报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md`）+ 研究边界档案（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../engine/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../engine/report_templates/monitoring-common-spec.md) × [基线报告类型模板（行业深度研究型）](../../engine/report_templates/industry-research/prompt-baseline-setup-template.md) × 业务专属配置（实例化后为 `./business-config.md`；泛用版暂缺，业务项以 TODO 标注）。冲突时以业务提示词（即本文件实例化版）为准。

---

## 运行变量（每次运行前填写）

```
{{REGION}} / {{TOPIC}}    = 固定值，实例化时写入 business-config.md
{{CURRENT_DATE}}          = 本次执行日期，格式 YYYY-MM-DD
{{BASELINE_DATE}}         = 首期基线日期
{{OUTPUT_PATH}}           = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}         = data/（TODO：边界档案文件名）
{{REGISTRY_FORMAT}}       = md-table（TODO：按业务配置）
{{SOURCE_LANGUAGE_RULE}}  = 仅英文 / 日文来源：① 官方权威（日本政府省厅・e-Gov・统计、国际机构、其他国家政府官方）；② 主流投资平台 / 顾问机构；③ 主流新闻媒体（英文 / 日文）。杜绝中文来源（含中文媒体及其中英文版、中国机构中英文版），不得引用、不得作线索、不得设例外。
{{REPORT_VERSION}}        = v1.0（首期基线固定）
```

**任务目标**：产出九节行业全景基线报告（产业链图谱、市场规模与格局、头部玩家、驱动因素与风险、趋势判断）与研究边界档案首建；多口径规模并列不合并；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

---

## 一、项目专属硬性约束

1. **中性立场**：不给投资评级、不出具 Go/No-Go 决策建议（边界归投资尽调型、可行性型）。
2. **结论边界**：趋势判断一律标「推断」并配反向声音（至少 2 条）；口径冲突并列呈现。
3. **受众定位**：（TODO：按业务配置实例化，默认战略决策层 / 投资者 / 新进入者）。

## 二、来源优先级

（TODO：按业务配置实例化机构清单）默认层级：① 统计局 / 行业协会 ② 上市公司财报 ③ 第三方研究机构 ④ 专家访谈；二手数据须多源交叉验证，每格活值附 `[来源, 年份]`。

## 三、基线锚定

对比锚属性、边界档案首建等通用差异见[基线类型模板第一节](../../engine/report_templates/industry-research/prompt-baseline-setup-template.md)。基线产出后，`{{BASELINE_REPORT_PATH}}` 即指向本报告；节标题为固化锚，正常运行**永不重跑**基线提示词。

## 四、追踪表（边界档案联动）

行业边界定义、产业链分层口径、玩家清单与入选标准、规模口径清单（TODO：业务配置定义逐项）；基线运行后逐项回写 `{{REGISTRY_PATH}}`，未核实项注明「待核实」，prompt 模板内严禁填写活值。

## 五、报告结构骨架

九节固定骨架见[基线类型模板第三节](../../engine/report_templates/industry-research/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后声明并逐字继承）。

## 六、执行方式（建议）

1. 按研究维度并行启动研究子代理（产业链 / 规模格局 / 玩家 / 驱动风险），全部逐点引用（TODO：按业务配置调整分工）。
2. 主代理合并差异；冲突口径保留双份引用；无法核实项单列「待复核清单」。

## 七、渲染与交付

- 交付格式：md + 同目录自包含 HTML（`python engine/tools/md2html.py`）；HTML 须通过 `python engine/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 从 business-prompt-scaffold.md 拆出独立泛用版基线提示词 |
