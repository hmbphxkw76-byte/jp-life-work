# 日本 · 技术与数字化 · 首期基线报告提示词（行业深度研究型）

> **用途**：执行「日本 技术与数字化 行业研究机制」的**机制建立**任务：产出首期行业全景基线报告与配套研究边界档案。
> **现状**：本业务线基线已于 2026-11 产出（[reports/{{YYYY-MM}}-<slug>.md](../reports/{{YYYY-MM}}-<slug>.md) + 同名 HTML，v1.0）。**正常运行永不重跑基线提示词**；仅在①报告与登记册全部丢失（灾难恢复），或②经维护规范批准的九节结构重排时启动。
> **产出**：md 源稿 + 同目录自包含 HTML，落盘 `{{OUTPUT_PATH}}`；研究边界档案回写 `{{REGISTRY_PATH}}`。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../engine/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../engine/report_templates/monitoring-common-spec.md) × [基线报告类型模板（行业深度研究型）](../../engine/report_templates/industry-research/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

---

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期，格式 YYYY-MM-DD
{{BASELINE_DATE}}        = 2026-11-12（首期已产出；重建时改为重建日期）
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}        = data/technology_industry_indicator_registry.md
{{REPORT_VERSION}}       = v1.0（首期固定；灾难恢复重建时递增）
```

**任务目标**：产出九节行业全景基线报告（执行摘要、研究范围与方法、技能图谱、数字化应用格局、头部厂商、驱动因素与风险、趋势判断、数据治理与局限、参考来源清单）与研究边界档案首建；多口径并列不合并；运行后回写 `{{REGISTRY_PATH}}`；基线报告**无上期报告**，不读取 `{{PREVIOUS_REPORT_PATH}}`。

---

## 一、项目专属硬性约束

1. **中性立场**：不给投资评级、不出具 Go/No-Go 决策建议（边界归投资尽调型、可行性型）。
2. **结论边界**：岗位转型与行情读法一律标「推断」；口径冲突并列呈现。
3. **受众定位**：见[业务配置第二节](./business-config.md)；报告须声明受众与视角。
4. **术语口径**：WMS / TMS / WCS 不得混用；「オペレーター」/「システム担当」/「改善・分析岗」不得混用；IT 人才缺口情景值不得合并。
5. **边界纪律**：产业趋势归 04、自动化技术归 05、在留制度与日语审查要件归 08、法规条文归 09、资格教育归 10；本报告只写个人技能与岗位对接并交叉链接。

## 二、来源优先级

见[业务配置第五节](./business-config.md)：① 国土交通省 / 経済産業省 ＞ ② IPA / 厚生労働省 ＞ ③ 行业协会与 WMS/TMS 厂商 ＞ ④ 求人门户与薪资调查（预期指标） ＞ ⑤ 技术学习平台。每条数据附完整 URL，每格活值附 `[来源, 年份]`。

## 三、基线锚定与重启条件

- 基线报告一经产出即为对比锚：结构、口径裁决与已核实结论由后续年度刷新完整继承。
- **正常运行不重跑**。重启仅限两种情形：①灾难恢复（报告与登记册全部丢失）；②九节结构经维护规范批准重排。重排须在[业务配置](./business-config.md)第十二节版本记录留痕，并同步评估年度刷新提示词。
- 现状：首期基线保留现行三章结构（业务固化锚），结构映射见[业务配置第 3.3 节](./business-config.md)。

## 四、报告结构

九节固定骨架见[基线类型模板第三节](../../engine/report_templates/industry-research/prompt-baseline-setup-template.md)：

| 节 | 模块 |
|---|---|
| 1 | 执行摘要 |
| 2 | 研究范围与方法 |
| 3 | 产业链图谱 |
| 4 | 市场规模与格局 |
| 5 | 头部玩家与竞争格局 |
| 6 | 驱动因素与风险 |
| 7 | 趋势判断（推断） |
| 8 | 数据治理与局限 |
| 9 | 参考来源清单 |

- 已产出的 2026-11 基线：按[业务配置 3.3 节](./business-config.md)的映射表对应到现行三章，**不改写正文**。
- 若经批准重建：九节标题为固化锚，逐字继承，不得增删节或调整顺序。

## 五、追踪表与边界档案

按[业务配置第八节](./business-config.md)的六维度逐项核对并填写「是否更新」；运行后回写 `{{REGISTRY_PATH}}` 的核心指标与[研究边界档案](./business-config.md)（领域边界、技能分层、主体清单与入选标准、口径清单）。未核实项注明「待核实」，不补值、不外推；prompt 模板内不填活值。

## 六、执行方式（建议）

1. 并行启动 2–3 个研究子代理：① 物流 DX 政策与技能需求；② 数字化岗位求人抽样；③ IT 人材需給 / 薪资带 / 外国人就业行情。全部限定日 / 英来源、逐点引用，每条数据附可直接访问的 URL；求人门户数据标注为预期指标。
2. 主代理合并差异，冲突口径保留双份引用，无法核实项单列「待复核清单」。
3. 与 04-industry-logistics / 05-industry-autonomous 最新报告交叉验证一致（只读锚，不回写）。

## 七、渲染与交付

- 交付格式：md + 同目录自包含 HTML（`python engine/tools/md2html.py`）；HTML 须通过 `python engine/tools/lint_reports.py`。
- 基线导航采用简化锚点目录，不强制 `.report-nav`。
- 落盘后将[业务配置第一节](./business-config.md)的 `{{BASELINE_REPORT_PATH}}` 指向本报告（重建场景）。

---

## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依行业深度研究型基线模板实例化；承接原 `prompt-technology-industry-update.md` 的主题约束、来源与交叉验证锚 |
