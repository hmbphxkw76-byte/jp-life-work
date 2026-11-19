# {{REGION}} · {{TOPIC}} · 预警专项提示词（舆情传播监测型 · 泛用版）

> **用途**：突发负面热点当期核实（确认非机器人 / 断章取义）与专项预警，不等待月度窗口。泛用版业务提示词：建新业务线时复制本文件至 `{TOPIC_DIR}/prompts/`，替换变量与 TODO 后即可运行。
> **产出**：专项预警件 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM-DD}}-<主题>.md`）+ 台账增量回写。由 `compliance_check.py` 按事件件（event）识别，validate 对非月度正则仅 WARN 不阻断，属预期。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../engine/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../engine/report_templates/monitoring-common-spec.md) × [周期更新类型模板（舆情传播监测型）](../../engine/report_templates/sentiment-monitoring/prompt-monthly-update-template.md) × 业务专属配置（实例化后为 `./business-config.md`；泛用版暂缺，业务项以 TODO 标注）。冲突时以业务提示词（即本文件实例化版）为准。

---

## 运行变量（每次运行前填写）

```
{{REGION}} / {{TOPIC}}    = 固定值，见实例化后的 business-config.md
{{CURRENT_DATE}}          = 本次执行日期
{{EVENT_NAME}}            = 本次触发热点名称（TODO）
{{PREVIOUS_REPORT_PATH}}  = 最近一期月报路径
{{BASELINE_REPORT_PATH}}  = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}         = data/（TODO）
{{OUTPUT_PATH}}           = reports/{{YYYY-MM-DD}}-<主题>.md
{{REPORT_VERSION}}        = 本次版本号，格式 vYYYY.MM.DD
```

**任务目标**：按[周期类型模板第一节事件触发档](../../engine/report_templates/sentiment-monitoring/prompt-monthly-update-template.md)执行对应模块重点刷新；完成人工复核与台账回写；预警只描述舆论态势与风险信号，不基于舆情给出投资或决策建议。

---

## 一、执行要点

1. 先核验热点真实性（机器人 / 水军 / 断章取义排查，方法与抽样比例 TODO：业务配置规定）。
2. 只刷新受影响模块，其余模块沿用上期值并注明。
3. 关键参与方观点摘编逐条附原文链接；无法核实项单列「待复核清单」。

## 二、联动与交付

- 台账增量回写 `{{REGISTRY_PATH}}`；月度窗口到达时本专项内容并入月报风险预警模块。
- 交付格式：md + 同目录自包含 HTML（`python engine/tools/md2html.py`）；HTML 须通过 `python engine/tools/lint_reports.py`。

---

## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 从 business-prompt-scaffold.md 拆出独立泛用版预警提示词 |
