# 业务提示词脚手架（白皮书·专题深度型）

> **用途**：为白皮书·专题深度型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将本文件各节复制为 `{TOPIC_DIR}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{TOPIC_DIR}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-topic-study.md`（新选题 / 年度系列 / 框架修订统一入口）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，产出首份白皮书并建立选题与品牌规范档案。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 行业公众 / 客户 / 决策者（TODO：按业务收窄） | 对外传播属性最强 |
| 选题库与准入标准 | 选题方向、准入评审规则（TODO） | 无准入选题不启动 |
| 原创框架登记 | 框架名称 / 要素 / 版本（TODO） | 求深求观点，事实仍逐点附来源 |
| 品牌与合规审校 | 署名规则、数据授权、争议措辞边界 | 对外发布前置条件 |
| 系列篇节拍 | 年度窗口与复判规则（TODO） | 上年观点原文保留 |
| 来源优先级 | ① 自有数据 ② 一手访谈 ③ 二手研究（TODO） | 自有与二手边界须声明 |
| 追踪表 | 核心论据 × 来源（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md 脚手架（复制为 prompts/prompt-baseline-setup.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 首份白皮书提示词（白皮书·专题深度型）

> **用途**：执行「{{REGION}} {{TOPIC}} 白皮书机制」的**机制建立**任务：产出首份白皮书与配套选题与品牌规范档案。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：中文八节白皮书（md 源稿 + 同目录自包含 HTML），落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md`）+ 选题与品牌规范档案（`{{REGISTRY_PATH}}`）。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../src/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../src/report_templates/monitoring-common-spec.md) × [基线报告类型模板（白皮书·专题深度型）](../../src/report_templates/whitepaper/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{BASELINE_DATE}}        = 首期基线日期
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}        = data/（TODO：选题与品牌规范档案文件名）
{{REPORT_VERSION}}       = v1.0（首期基线固定）
```

**任务目标**：产出八节首份白皮书（问题定义与原创框架、深度论证、案例佐证、观点与倡议、品牌合规审校记录）与选题档案首建；**必须提出原创框架或鲜明主张**（与行业研究的中性全景不同），事实论据仍逐点附来源；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

## 一、项目专属硬性约束

1. **观点与事实分离**：观点部分标「本报告观点」；不借白皮书输出投资评级或法律意见（边界归投资尽调型、政策解读型）。
2. **对外发布标准**：须通过品牌与合规审校（审校清单见业务配置 TODO）后才可发布；已发布白皮书不得改动，勘误以勘误件形式发布。
3. **受众定位**：见[业务配置](./business-config.md)（TODO：实例化）。

## 二、来源优先级

见[业务配置](./business-config.md)（TODO：① 自有数据 ② 一手访谈 ③ 二手研究）；自有数据与二手数据边界声明须写入报告。

## 三～八、结构骨架与联动

八节固定骨架见[基线类型模板第三节](../../src/report_templates/whitepaper/prompt-baseline-setup-template.md)；业务固化锚节标题（TODO：实例化后逐字继承）；论据追踪表见[业务配置](./business-config.md)（TODO）。

## 九、渲染与交付

- md + 自包含 HTML（`python src/prompts-tools/tools/md2html.py`）；HTML 须通过 `python src/prompts-tools/tools/lint_reports.py`；基线导航采用简化锚点目录。

---

## 四、prompt-topic-study.md 脚手架（复制为 prompts/prompt-topic-study.md，以下为全文）

# {{REGION}} · {{TOPIC}} · 专题续作提示词（白皮书·专题深度型 · 选题制）

> **用途**：专题续作统一入口——新选题白皮书、年度系列篇、框架修订篇（当次类型由业务配置或运行时变量指定）。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：新选题件 `reports/{{YYYY-MM}}-<slug>.md` 或框架修订件 `reports/{{YYYY-MM-DD}}-主题-修订.md`、年度系列篇 `reports/{{YYYY-MM}}-<slug>.md`（+ 同名 html）。新选题与修订篇命名不在标准正则内，validate 仅 WARN 不阻断，属预期。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../src/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../src/report_templates/monitoring-common-spec.md) × [专题续作类型模板（白皮书·专题深度型）](../../src/report_templates/whitepaper/prompt-topic-study-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{STUDY_TYPE}}           = 本次类型（新选题 / 年度系列 / 框架修订，TODO：选题名称）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}-<slug>.md
{{PREVIOUS_REPORT_PATH}} = 最近一篇同系列白皮书路径（如无则空）
{{REGISTRY_PATH}}        = data/（TODO）
{{OUTPUT_PATH}}          = 由 {{STUDY_TYPE}} 决定（见用途）
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：按[专题续作类型模板](../../src/report_templates/whitepaper/prompt-topic-study-template.md)续作协议执行「选题准入 → 框架复用 / 修订 → 深度论证 → 审校发布」闭环；系列篇与上年篇逐节对照，上年观点原文保留、复判结论（维持 / 修正 / 撤回）显式声明；框架修订篇须新旧框架对照，不静默替换；无准入选题不启动。

## 一、各模块要点（业务实例化，TODO 按 {{STUDY_TYPE}} 展开）

- **问题与框架**（TODO：新选题问题定义、复用 / 扩展 / 新建框架决策、与基线框架关系声明）。
- **深度论证**（TODO：沿框架逐要素展开，事实论据逐点附来源，推断显式标注）。
- **案例佐证**（TODO：入选标准、逐案例分析对框架的支撑 / 修正）。
- **观点复判**（系列篇，TODO：上年观点逐条对照新证据）。
- **倡议**（TODO：面向受众的行动倡议，标「倡议」）。

## 二～六、协议与交付

审校清单（品牌与合规）成稿后集中执行并留痕；重大未决项存在时不发布；渲染交付同基线提示词第九节。

---

## 六、落盘后审计（提交前必做，适用于本脚手架全部提示词）

落盘后依次运行 `python src/prompts-tools/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python src/prompts-tools/tools/audit_preflight.py --report <报告相对路径>`、`python src/prompts-tools/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python src/prompts-tools/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

> 复制到业务 `prompts/` 后，须在**每一份**业务提示词末尾保留本节（与类型模板同口径）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成白皮书·专题深度型业务提示词脚手架 |
