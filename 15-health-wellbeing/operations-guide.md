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
python engine/tools/validate.py
python engine/tools/lint_reports.py
```

## 2. 基线（首期已产出，永不重跑）

- 现状：`reports/2026-11-health-wellbeing.md` v1.0（数据基准 2026-11-14）。
- 重启仅限：①灾难恢复；②结构重排（须留痕）。

## 3. 季度复核 / 事件触发

- 入口：[prompt-update.md](./prompts/prompt-update.md)。
- 触发器：见[业务配置第七节](./prompts/business-config.md)；无触发不启动。
- 输出：`reports/{{YYYY-MM}}-<slug>.md` 或 `reports/{{YYYY-MM}}-<slug>.md`。
- 验证：`lint_reports.py` + `classify_reports.py`。

## 4. 与 14 / 07 / 08 / 13 的联动

- 保险加入手续 → 14-life-operations；
- 社保费 / 医疗費控除 → 07-economy-finance；
- 在留 / 家属 / 生活保护 → 08-visa-immigration；
- 地域医疗资源差异 → 13-regional-info。

## 5. 落盘后审计（提交前必做）

```powershell
python engine/tools/audit_preflight.py --report <报告相对路径>
python engine/tools/audit_check.py --report <报告相对路径>
python engine/tools/audit_pipeline.py --submit --report <报告相对路径>
```

- [ ] 审计自检（preflight / audit_check）无 P0/P1，且已 `audit_pipeline --submit` 提交初审

---

## 6. 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 建立操作指引 |

## 语义指标人工核验清单

> 依据《信息质量评估提示词体系》模块四：语义类指标需人工 / LLM 复核，不在自动门槛内。
> `audit_sampling.py` 月度抽检强制覆盖以下 ≥2 项；抽检结果入 `engine/report-audits/info-quality/assessment-ledger.md`。

| 指标 | 核验要点 |
|---|---|
| S-01 | 自付比例通常 3 割与 75 岁以上分层；高额疗养费令和 8-08 改革示例 9.3 万円。 |
| S-06 | 初诊费用行情、精神科初诊费用与候诊时间、多语言窗口清单标 ⚠ 待核实。 |
| S-07 | 核对 2027 年度国保保费上限 96 万円、介護费率 1.62% 回官方原文。 |
| C-11 | 检查障害者手帳 / 精神障害者保健福祉手帳外国人对应是否避免概括。 |
