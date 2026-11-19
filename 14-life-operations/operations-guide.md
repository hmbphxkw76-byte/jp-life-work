# 在日生活实务 · 报告操作指引（Agent 可执行版）

> **适用范围**：`14-life-operations` 的基线 / 季度复核 / 事件触发。
> **单一事实源**：业务参数以 [prompts/business-config.md](./prompts/business-config.md) 为准。

---

## 0. 目录速查

| 资产 | 路径 |
|---|---|
| 周期提示词 | `14-life-operations/prompts/prompt-{baseline-setup|update}.md` |
| 业务参数 | `14-life-operations/prompts/business-config.md` |
| 指标登记册 | `14-life-operations/data/life_operations_indicator_registry.md` |
| 报告产物 | `14-life-operations/reports/` |

## 1. 通用前置检查

```powershell
python engine/tools/validate.py
python engine/tools/lint_reports.py
```

## 2. 基线（首期已产出，永不重跑）

- 现状：`reports/2026-11-life-operations.md` v1.0（数据基准 2026-11-14）。
- 重启仅限：①灾难恢复；②结构重排（须留痕）。

## 3. 季度复核 / 事件触发

- 入口：[prompt-update.md](./prompts/prompt-update.md)。
- 触发器：见[业务配置第七节](./prompts/business-config.md)；无触发不启动。
- 输出：`reports/{{YYYY-MM}}-<slug>.md` 或 `reports/{{YYYY-MM}}-<slug>.md`。
- 验证：`lint_reports.py` + `classify_reports.py`。

## 4. 个人定居地联动

- 定居地确定后，重点更新模块八（90 天清单）与登记册 #10（多语言窗口）。
- 与 00-decision-hub 的[定居地档案](../00-decision-hub/reports/2026-11-decision-hub.md)联动。

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
| S-01 | 在留 / 住民时限 14 日；健康保険自付 3 割（75 岁以上分层）；通信费用 / 银行开户无官方统一口径。 |
| S-06 | 各银行在留期限门槛、大手 / 格安 SIM 月费、定期券月费、自治体多语言窗口清单待补。 |
| S-10 | 部分房东 / 管理会社不接受外国人为推断项，检查是否标注。 |
| C-12 | 检查 90 天清单个人完成状态与登记册 #9 是否对应。 |
