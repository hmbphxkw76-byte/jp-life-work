# 报告合规性审计（历史报告 × 类型模板匹配度）

- **审计时间**：2026-11-14 11:33 UTC
- **审计范围**：全部业务线 reports/*.html（共 18 份）
- **匹配度**：18/18（100%）报告与对应类型模板规则完全匹配
- **规则来源**：[compliance-rules.json](../report_templates/compliance-rules.json)（12 类报告类型结构骨架，与 [template-registry.md](../report_templates/template-registry.md) 登记一致）
- **结论**：全部合规 ✅

## 明细

```
[INFO] 04-industry-logistics/reports/2026-11-industry-logistics.html: 周期「monthly」未单独登记，按基线骨架（结构逐字继承）校验
[INFO] 05-industry-autonomous/reports/2026-11-industry-autonomous.html: 周期「monthly」未单独登记，按基线骨架（结构逐字继承）校验
[INFO] 06-industry-technology/reports/2026-11-industry-technology.html: 周期「monthly」未单独登记，按基线骨架（结构逐字继承）校验
[INFO] 08-visa-immigration/reports/2026-11-visa-immigration.html: 周期「monthly」未单独登记，按基线骨架（结构逐字继承）校验
[INFO] 09-politics-law/reports/2026-11-politics-law.html: 周期「monthly」未单独登记，按基线骨架（结构逐字继承）校验
[INFO] 16-exit-transition-return/reports/2026-11-exit-transition-return.html: 周期「monthly」未单独登记，按基线骨架（结构逐字继承）校验
```
