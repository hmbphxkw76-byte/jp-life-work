# 赴日决策仪表盘 · 首期基线提示词（职业就业调研型）

> **用途**：建立 `00-decision-hub` 决策枢纽的**机制建立**任务：产出首期五问仪表盘报告与配套登记册（五问指标状态表 / 缺失清单 / 决策支持件套），作为后续季度复核与事件触发的对比锚。
> **现状**：本业务线基线已于 2026-11 产出（[reports/{{YYYY-MM}}-decision-hub.md](../reports/{{YYYY-MM}}-decision-hub.md) + 同名 HTML）。**正常运行永不重跑基线提示词**；仅在①报告与登记册全部丢失（灾难恢复），或②经维护规范批准时启动。
> **产出**：md 源稿 + 同目录自包含 HTML，落盘 `{{OUTPUT_PATH}}`；登记册回写 `{{REGISTRY_PATH}}`。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../engine/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../engine/report_templates/monitoring-common-spec.md) × [基线报告类型模板（职业就业调研型）](../../engine/report_templates/employment-research/prompt-baseline-setup-template.md) × [业务专属配置](./business-config.md)。冲突优先级：**本文件 ＞ 类型模板 ＞ 通用基座 ＞ 通用规范**。

---

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期，格式 YYYY-MM-DD
{{BASELINE_DATE}}        = 2026-11-14（首期已产出；重建时改为重建日期）
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-decision-hub.md
{{REGISTRY_PATH}}        = data/decision_hub_registry.md
{{REPORT_VERSION}}       = v1.0（首期固定；灾难恢复重建时递增）
```

固定值（不填，读自业务配置第一节）：`{{REGION}}`、`{{TOPIC}}`、`{{FIVE_QUESTIONS_VIEW}}`、`{{DECISION_LOG_PATH}}`、`{{PERSONAL_PROFILE_PATH}}`、`{{FINANCE_MODEL_PATH}}`。

## 任务目标

建立「收敛 → 暴露 → 触发」机制：把 01–20 主题的最新结论收敛为五问答案，标记缺失事实，并按缺失清单启动补缺。**本业务线不产出研究内容**，一切数字与结论引用来源主题。

## 执行步骤

1. 读取 `{{FIVE_QUESTIONS_VIEW}}` 与 01–20 最新一期报告 / 登记册活值。
2. 按业务配置「五问指标状态表」逐项收敛：判定（是 / 否 / 待定）+ 依据 + 置信度 + 缺失标记。
3. 汇总缺失清单，按「决策价值 × 缺口完整度」排序定优先级与期限。
4. 建立决策支持件套（个人参数档案 / 决策一页纸 / 财务模型 / 置信度分级 / 决策树）。
5. 回写 `{{REGISTRY_PATH}}`，生成五问视图与决策日志首条记录。

## 输出与命名

- 报告落盘 `{{OUTPUT_PATH}}`，HTML 由 `engine/tools/md2html.py` 同步生成。
- 登记册 / 视图 / 日志路径见业务配置第一节。

## 质量自检

- [ ] 五问指标状态表齐全，判定与依据 / 置信度一一对应
- [ ] 缺失清单按优先级排序，期限明确
- [ ] 全部结论可追溯到来源主题（主题 + 报告 / 登记册指标号）
- [ ] 决策支持件套齐备
- [ ] HTML 通过 lint（标签配对）

## 维护规范

- **修订触发条件**：五问框架调整、件套增减、来源主题清单变更。
- **变更流程**：先改本文件 → 同步类型模板 → 更新版本记录。
- **固化保护**：已产出基线报告不得改动；结构变更只影响后续新基线。

---
## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/auto_verify.py --report <报告相对路径>`、`python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-18 | 首次建立 | 00 补基线提示词（P1-8） |
