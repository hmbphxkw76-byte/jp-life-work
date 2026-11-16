# 业务提示词脚手架（消费者·用户调研型）

> **用途**：为消费者·用户调研型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将本文件各节复制为 `{TOPIC_DIR}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{TOPIC_DIR}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-study.md`（专题调研 / 年度复测统一入口）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立调研设计档案与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 产品 / 营销 / 用户体验团队（TODO：按业务收窄） | 报告须声明受众 |
| 目标人群与抽样框 | 人群定义、抽样方式、配额、样本量下限（TODO） | 样本质量决定可信度 |
| 调研方法组合 | 问卷 / 深访 / 焦点小组 / 行为数据（TODO：按专题选择） | 一手数据为核心证据 |
| 细分维度与画像假设 | 细分维度、每类画像要素（TODO） | 假设须标验证状态 |
| 专题准入 | 年度专题清单与立项标准（TODO） | 项目制触发 |
| 来源优先级 | ① 一手调研（问卷/深访/实测） ② 行为数据 ③ 二手背景（TODO） | 二手仅作交叉验证 |
| 伦理与隐私 | 知情同意、脱敏规则、留存边界（TODO） | 不得采集可识别个人身份的敏感信息 |
| 追踪表 | 调研追踪项 × 方法（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md 脚手架（复制为 prompts/prompt-baseline-setup.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 首期基线调研提示词（消费者·用户调研型）

> **用途**：执行「{{REGION}} {{TOPIC}} 消费者调研机制」的**机制建立**任务：产出首期基线调研报告与配套调研设计档案。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文八节基线报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md`）+ 调研设计档案（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../src/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../src/report_templates/monitoring-common-spec.md) × [基线报告类型模板（消费者·用户调研型）](../../src/report_templates/consumer-research/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{BASELINE_DATE}}        = 首期基线日期
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}        = data/（TODO：设计档案文件名）
{{REPORT_VERSION}}       = v1.0（首期基线固定）
```

**任务目标**：产出八节基线调研报告（设计与方法论、细分框架、首期结果、交叉分析）与设计档案首建；样本量、抽样方式、回收率、置信水平完整声明；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

## 一、项目专属硬性约束

1. **一手数据为主**：核心结论以一手调研为证据；无一手数据支撑的结论标「二手推断」。
2. **结论边界**：不输出「市场必然接受」断言；画像标「假设 / 验证状态」；行动建议标「建议」。
3. **伦理与隐私**：遵守知情同意与隐私保护，定性材料引用脱敏。
4. **受众定位**：见[业务配置](./business-config.md)（TODO：实例化）。

## 二、来源与抽样

抽样框与配额见[业务配置](./business-config.md)（TODO）；二手数据仅作背景与交叉验证（冲突并列）。

## 三～八、结构骨架与联动

八节固定骨架见[基线类型模板第三节](../../src/report_templates/consumer-research/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后逐字继承）；追踪表见[业务配置](./business-config.md)（TODO）。

## 九、渲染与交付

- md + 自包含 HTML（`python src/prompts-tools/tools/md2html.py`）；HTML 须通过 `python src/prompts-tools/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 四、prompt-study.md 脚手架（复制为 prompts/prompt-study.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 专题调研提示词（消费者·用户调研型 · 项目制）

> **用途**：项目制专题调研统一入口——概念测试、满意度 / NPS 年度复测、画像刷新、决策路径研究（当次项目主题由业务配置或运行时变量指定）。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：单份专题报告（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`。命名不在标准正则内，validate 仅 WARN 不阻断，属预期；年度复测命名与标准正则兼容。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{STUDY_TYPE}}           = 本次专题类型（概念测试 / 满意度复测 / 画像刷新 / 决策路径，TODO：按业务配置枚举）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}        = data/（TODO）
{{OUTPUT_PATH}}          = 专题件 reports/{{YYYY-MM-DD}}-（TODO：主题）.md；年度复测 reports/{{YYYY-MM}}-<slug>.md
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：按[专题类型模板](../../src/report_templates/consumer-research/prompt-study-template.md)项目协议执行「设计 → 采集 → 分析 → 建议」闭环；方法与口径与基线一致（变更显式声明）；样本不足或差异不显著时结论降级为「方向性发现」并标注；运行后回写设计档案。

## 一、项目模块要点（业务实例化，TODO 按 {{STUDY_TYPE}} 展开）

- **概念 / 产品测试**（TODO：接受度、购买意向、价格敏感度、竞品对照）。
- **满意度 / NPS 复测**（TODO：口径与上年一致、分项满意度、驱动因素、贬损者归因）。
- **画像刷新**（TODO：细分维度有效性复核、新画像假设、触点迁移）。
- **决策路径**（TODO：触达 → 认知 → 比较 → 转化环节行为与态度、关键决策因素排序）。

## 二、交付

交付包 = 报告 + 数据表附录（脱敏）+ 方法说明；事实发现与建议分离；渲染交付同基线提示词第九节。

---

## 六、落盘后审计（提交前必做，适用于本脚手架全部提示词）

落盘后依次运行 `python src/prompts-tools/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python src/prompts-tools/tools/audit_preflight.py --report <报告相对路径>`、`python src/prompts-tools/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python src/prompts-tools/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

> 复制到业务 `prompts/` 后，须在**每一份**业务提示词末尾保留本节（与类型模板同口径）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成消费者·用户调研型业务提示词脚手架 |
