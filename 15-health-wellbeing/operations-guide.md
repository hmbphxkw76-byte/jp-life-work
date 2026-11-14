# 医疗·健康·心理 · 报告操作指引（Agent 可执行版）

> **适用范围**：`15-health-wellbeing` 的基线 / 季度复核 / 事件触发。
> **单一事实源**：业务参数以 [prompts/business-config.md](./prompts/business-config.md) 为准。

---

## 0. 目录速查

| 资产 | 路径 |
|---|---|
| 周期提示词 | `15-health-wellbeing/prompts/prompt-{baseline-setup|update}.md` |
| 业务参数 | `15-health-wellbeing/prompts/business-config.md` |
| 指标登记册 | `15-health-wellbeing/data/health_wellbeing_indicator_registry.md` |
| 报告产物 | `15-health-wellbeing/reports/` |

## 1. 通用前置检查

```powershell
python src/prompts-tools/tools/validate.py
python src/prompts-tools/tools/lint_reports.py
```

## 2. 基线（首期已产出，永不重跑）

- 现状：`reports/2026-11_baseline_report.md` v1.0（数据基准 2026-11-14）。
- 重启仅限：①灾难恢复；②结构重排（须留痕）。

## 3. 季度复核 / 事件触发

- 入口：[prompt-update.md](./prompts/prompt-update.md)。
- 触发器：见[业务配置第七节](./prompts/business-config.md)；无触发不启动。
- 输出：`reports/{{YYYY-Qn}}_quarterly.md` 或 `reports/{{YYYY-MM-DD}}-主题.md`。
- 验证：`lint_reports.py` + `classify_reports.py`。

## 4. 与 14 / 07 / 08 / 13 的联动

- 保险加入手续 → 14-life-operations；
- 社保费 / 医疗費控除 → 07-economy-finance；
- 在留 / 家属 / 生活保护 → 08-visa-immigration；
- 地域医疗资源差异 → 13-regional-info。

## 5. 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 建立操作指引 |
