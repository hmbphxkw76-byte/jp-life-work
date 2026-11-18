# 赴日决策仪表盘 · 季度复核提示词（职业就业调研型）

> **用途**：按季度复核节拍（含事件触发）更新 `00-decision-hub` 的五问仪表盘：重估五问判定、暴露新增缺失、更新触发器状态与决策支持件套。
> **产出**：季度报告落盘 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-decision-hub.md`）+ 同名 HTML。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../engine/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../engine/report_templates/monitoring-common-spec.md) × [周期更新类型模板（职业就业调研型）](../../engine/report_templates/employment-research/prompt-update-template.md) × [业务专属配置](./business-config.md)。冲突优先级：**本文件 ＞ 类型模板 ＞ 通用基座 ＞ 通用规范**。

---

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期，格式 YYYY-MM-DD
{{CADENCE}}              = 季（季度复核）/ 事件触发
{{PREVIOUS_REPORT_PATH}} = 上一期季度报告路径
{{BASELINE_REPORT_PATH}} = reports/2026-11-decision-hub.md
{{REGISTRY_PATH}}        = data/decision_hub_registry.md
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-decision-hub.md
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

固定值（不填，读自业务配置第一节）：`{{REGION}}`、`{{TOPIC}}`、`{{FIVE_QUESTIONS_VIEW}}`、`{{DECISION_LOG_PATH}}`。

## 任务目标

完成「核验 → 收敛 → 暴露 → 触发」闭环：读取 01–20 最新一期结论，更新五问判定与缺失清单；无变化时明确声明「本期无变化」，不得虚构变化。

## 执行步骤

1. **核验**：读取 `{{PREVIOUS_REPORT_PATH}}` 与 01–20 最新报告 / 登记册，确认来源主题是否更新。
2. **收敛**：逐问重估判定（是 / 否 / 待定）+ 依据 + 置信度；判定变化记入 `{{DECISION_LOG_PATH}}`。
3. **暴露**：更新缺失清单与优先级；已消减项标注消减依据。
4. **触发**：按缺失清单优先级更新触发器状态与期限。
5. **件套**：刷新决策支持件套状态（财务模型 / 决策树 / 一页纸）。

## 输出与命名

- 报告落盘 `{{OUTPUT_PATH}}`，HTML 由 `engine/tools/md2html.py` 同步生成。
- 五问视图与登记册同步更新。

## 质量自检

- [ ] 五问判定逐问有依据 / 置信度，判定变化已记入决策日志
- [ ] 缺失清单优先级与期限更新，消减项有据
- [ ] 结论可追溯到来源主题，未独立改值
- [ ] HTML 通过 lint（标签配对）

## 维护规范

- **修订触发条件**：五问框架调整、件套增减、来源主题清单变更。
- **变更流程**：先改本文件 → 同步类型模板 → 更新版本记录。

---
## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/auto_verify.py --report <报告相对路径>`、`python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-18 | 首次建立 | 00 补季度复核周期提示词（P1-8） |
