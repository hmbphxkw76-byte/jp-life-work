# 日本 医疗·健康·心理 周期更新提示词（职业就业调研型）

> **用途**：本业务线的**季度复核 / 事件触发复核**。
> **继承声明（四层体系）**：本文件 = [通用基座](../../src/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../src/report_templates/monitoring-common-spec.md) × [职业就业调研型周期模板](../../src/report_templates/employment-research/prompt-update-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

---

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期
{{CADENCE}}              = 季 / 年
{{PREVIOUS_REPORT_PATH}} = reports/ 中最近一期同周期报告
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}-<slug>.md
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md 或 reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}        = data/health_wellbeing_indicator_registry.md
{{REPORT_VERSION}}       = vYYYY.MM.DD
```

---

## 一、执行步骤

1. 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，继承「已修正事实清单」全部条目（防回退）。
2. 读登记册活值，逐项核对 8 项追踪指标，填写「是否更新」。
3. 按触发器判定是否启动；无触发且窗口未到 → 降级为核验型轻运行，不重写报告。
4. 命中触发器 → 刷新对应模块；冲突口径并列，无法核实项列「⚠ 待核实」。
5. 回写登记册与报告变更摘要；落盘 md + HTML。

## 二、触发器（摘自业务配置第七节）

- 医保制度改定 → 模块二
- 医疗费 / 药价改定 → 模块三
- 多语言医疗支援变更 → 模块三
- 精神科 / 牙科 / 分娩政策变更 → 模块四
- 介護保険制度变更 → 模块七
- 个人健康情况变化 → 事件触发

## 三、质量自检

- [ ] 已修正事实清单无回退
- [ ] 8 项追踪指标均已核对
- [ ] 未核实项显式标记
- [ ] HTML 通过 lint

---

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 依职业就业调研型周期模板实例化 |
