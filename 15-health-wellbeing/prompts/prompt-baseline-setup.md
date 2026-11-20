# 日本 医疗·健康·心理 首期基线报告提示词（职业就业调研型）

> **用途**：执行本业务线的**机制建立**任务：产出首期基线报告与配套指标登记册。
> **现状**：本业务线基线已于 2026-11 产出（[reports/{{YYYY-MM}}-<slug>.md](../reports/{{YYYY-MM}}-<slug>.md) + 同名 HTML，v1.0，数据基准 2026-11-14）。**正常运行永不重跑基线提示词**；仅在①报告与登记册全部丢失，或②经维护规范批准的结构重排时启动。
> **产出**：md 源稿 + 同目录自包含 HTML，落盘 `{{OUTPUT_PATH}}`；指标活值回写 `{{REGISTRY_PATH}}`。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../engine/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../engine/report_templates/monitoring-common-spec.md) × [基线报告类型模板（职业就业调研型）](../../engine/report_templates/employment-research/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

---

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{BASELINE_DATE}}        = 2026-11-14（首期已产出；重建时改为重建日期）
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}        = data/health_wellbeing_indicator_registry.md
{{REPORT_VERSION}}       = v1.0（首期固定；灾难恢复重建时递增）
```

**任务目标**：产出本主题专属结构的基线报告（核心结论 / 医保制度 / 就医实务 / 牙科与精神科 / 心理健康 / 体检与预防 / 介護与福祉 / 数据可靠性 / 来源）；运行后回写 `{{REGISTRY_PATH}}`。

---

## 一、项目专属硬性约束

1. **受众与结论边界**：面向本人；输出「制度 → 流程 → 费用 → 外国人可否 → 多语言支援」；**不替代医疗诊断**；事实与推断分离。
2. **来源语言规则**：{{SOURCE_LANGUAGE_RULE}}（仅英文 / 日文来源，杜绝中文来源；见[业务配置第一节](./business-config.md)）。
3. **边界纪律**：社保费 / 税转 07；在留 / 家属转 08；劳动安全转 09；地域差异转 13；保险加入手续转 14。
4. **缺失标记**：未核实项写「⚠ 待核实」，不补值、不外推。

## 二、来源优先级

见[业务配置第五节](./business-config.md)。每条数据附完整 URL，每格活值附 `[来源, 年份]`。

## 三、报告结构

本主题专属结构（见[业务配置第 3.2 节](./business-config.md)映射）：核心结论 / 医保制度 / 就医实务 / 牙科与精神科 / 心理健康与适应 / 体检与预防 / 介護与福祉 / 数据可靠性与局限说明 / 参考来源清单。

## 四、追踪表与边界档案

按[业务配置第八节](./business-config.md)的 8 项追踪指标逐项核对并填写「是否更新」；运行后回写 `{{REGISTRY_PATH}}` 的核心指标与[研究边界档案](./business-config.md)。

## 五、执行方式（建议）

1. 并行启动 4 个研究子代理：① 医保 / 高额疗养费；② 就医 / 多语言通译；③ 牙科 / 精神科 / 分娩；④ 心理健康 / 体检 / 介護。全部限定日 / 官方来源、逐点引用。
2. 主代理合并差异，冲突口径保留双份引用，无法核实项单列「⚠ 待核实」。

## 六、渲染与交付

- md + 同目录自包含 HTML（`python engine/tools/md2html.py`）；HTML 须通过 `lint_reports.py`。
- 落盘后将[业务配置第一节](./business-config.md)的 `{{BASELINE_REPORT_PATH}}` 指向本报告。

## 七、质量自检

- [ ] 全篇来源均为英文 / 日文，无中文来源
- [ ] 医保 / 就医 / 牙科精神科 / 心理 / 体检 / 介護各章齐全
- [ ] 未核实项显式标记「⚠ 待核实」
- [ ] 追踪表 8 项均已核对
- [ ] HTML 通过 lint（标签配对）

---

## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 依职业就业调研型基线模板实例化 |
