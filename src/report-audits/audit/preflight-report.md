# 落盘前自检报告（AuditGuard Preflight）

> 检查日期：2026-11-15　|　报告总数：22　|　通过 22 / 不通过 0
> 定位：提交审计前的快速本地检查；判定复用信息质量四维度与 audit_check。

## 逐报告结论

| 报告 | P0 | P1 | P2 | 结论 |
|---|---|---|---|---|
| [00-decision-hub/reports/2026-11-decision-hub.md](../00-decision-hub/reports/2026-11-decision-hub.md) | 0 | 0 | 0 | 通过 |
| [00-decision-hub/reports/2026-12-decision-hub.md](../00-decision-hub/reports/2026-12-decision-hub.md) | 0 | 0 | 1 | 通过 |
| [01-ssw-driver/reports/2026-11-ssw-driver.md](../01-ssw-driver/reports/2026-11-ssw-driver.md) | 0 | 0 | 0 | 通过 |
| [02-career-driver/reports/2026-11-career-driver.md](../02-career-driver/reports/2026-11-career-driver.md) | 0 | 0 | 0 | 通过 |
| [03-career-management/reports/2026-11-career-management.md](../03-career-management/reports/2026-11-career-management.md) | 0 | 0 | 0 | 通过 |
| [04-industry-logistics/reports/2026-11-industry-logistics.md](../04-industry-logistics/reports/2026-11-industry-logistics.md) | 0 | 0 | 1 | 通过 |
| [05-industry-autonomous/reports/2026-11-industry-autonomous.md](../05-industry-autonomous/reports/2026-11-industry-autonomous.md) | 0 | 0 | 1 | 通过 |
| [06-industry-technology/reports/2026-11-industry-technology.md](../06-industry-technology/reports/2026-11-industry-technology.md) | 0 | 0 | 0 | 通过 |
| [07-economy-finance/reports/2026-11-economy-finance.md](../07-economy-finance/reports/2026-11-economy-finance.md) | 0 | 0 | 0 | 通过 |
| [08-visa-immigration/reports/2026-11-visa-immigration.md](../08-visa-immigration/reports/2026-11-visa-immigration.md) | 0 | 0 | 0 | 通过 |
| [09-politics-law/reports/2026-11-politics-law.md](../09-politics-law/reports/2026-11-politics-law.md) | 0 | 0 | 0 | 通过 |
| [10-education-qualification/reports/2026-11-education-qualification.md](../10-education-qualification/reports/2026-11-education-qualification.md) | 0 | 0 | 1 | 通过 |
| [11-language-japanese/reports/2026-11-language-japanese.md](../11-language-japanese/reports/2026-11-language-japanese.md) | 0 | 0 | 0 | 通过 |
| [12-culture-life/reports/2026-11-culture-life.md](../12-culture-life/reports/2026-11-culture-life.md) | 0 | 0 | 1 | 通过 |
| [13-regional-info/reports/2026-11-regional-info.md](../13-regional-info/reports/2026-11-regional-info.md) | 0 | 0 | 0 | 通过 |
| [14-life-operations/reports/2026-11-life-operations.md](../14-life-operations/reports/2026-11-life-operations.md) | 0 | 0 | 0 | 通过 |
| [15-health-wellbeing/reports/2026-11-health-wellbeing.md](../15-health-wellbeing/reports/2026-11-health-wellbeing.md) | 0 | 0 | 0 | 通过 |
| [16-exit-transition-return/reports/2026-11-exit-transition-return.md](../16-exit-transition-return/reports/2026-11-exit-transition-return.md) | 0 | 0 | 0 | 通过 |
| [17-migration-compliance/reports/2026-11-migration-compliance.md](../17-migration-compliance/reports/2026-11-migration-compliance.md) | 0 | 0 | 1 | 通过 |
| [18-family-parenting/reports/2026-11-family-parenting.md](../18-family-parenting/reports/2026-11-family-parenting.md) | 0 | 0 | 0 | 通过 |
| [19-safety-disaster/reports/2026-11-safety-disaster.md](../19-safety-disaster/reports/2026-11-safety-disaster.md) | 0 | 0 | 1 | 通过 |
| [20-overseas-china/reports/2026-11-overseas-china.md](../20-overseas-china/reports/2026-11-overseas-china.md) | 0 | 0 | 0 | 通过 |

## 发现明细

| 编号 | 级别 | 报告 | 位置 | 判定依据 |
|---|---|---|---|---|
| PF-E8 | P2 | 00-decision-hub/reports/2026-12-decision-hub.md | 必需要素 | 缺少后续动作 / 观察清单 |
| PF-REG | P2 | 04-industry-logistics/reports/2026-11-industry-logistics.md | 登记册指针 | 引用登记册 #7, #8 在登记册中不存在 |
| PF-REG | P2 | 05-industry-autonomous/reports/2026-11-industry-autonomous.md | 登记册指针 | 引用登记册 #10 在登记册中不存在 |
| PF-REG | P2 | 10-education-qualification/reports/2026-11-education-qualification.md | 登记册指针 | 引用登记册 #14 在登记册中不存在 |
| PF-ABS | P2 | 12-culture-life/reports/2026-11-culture-life.md | 绝对化表述 | 命中绝对化措辞 1 处（100%），语义确认后定级 |
| PF-ABS | P2 | 17-migration-compliance/reports/2026-11-migration-compliance.md | 绝对化表述 | 命中绝对化措辞 2 处（包过），语义确认后定级 |
| PF-SKELETON | P2 | 19-safety-disaster/reports/2026-11-safety-disaster.md | 类型骨架 | [market-monitoring/monthly] h2 节数 10 超出模板骨架 8 节（如为业务固化锚请人工确认，否则须对齐类型模板 prompt-monthly-monitor-template.md） |

**总体结论：全部通过**
