# 存量报告迁移清单（2026-11 月度体系重构）

> 自动生成，请勿手工编辑。由 `src/prompts-tools/tools/migrate_monthly_reports.py` 产出。

## 一、迁移规则

- 全部报告按自然月份聚合，统一命名 `YYYY-MM-<主题slug>.md` + 同名 `.html`。
- 取消基线 / 初析 / 季度等类型标签；季度报告按季度末月归档（如 2026-Q4 → 2026-12）。
- 同月多份报告合并为一份：初析为主体，基线等作为附录，原文内容未删改。
- HTML 由 `md2html.py` 依据合并后 md 重新生成，与 md 源一致。

## 二、迁移明细

| 主题 | 目标月 | 目标文件 | 来源文件 | 角色 | 内容校验 |
|---|---|---|---|---|---|
| career-driver | 2026-11 | `02-career-driver/reports/2026-11-career-driver.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| career-driver | 2026-11 | `02-career-driver/reports/2026-11-career-driver.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| career-management | 2026-11 | `03-career-management/reports/2026-11-career-management.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| career-management | 2026-11 | `03-career-management/reports/2026-11-career-management.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| culture-life | 2026-11 | `12-culture-life/reports/2026-11-culture-life.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| culture-life | 2026-11 | `12-culture-life/reports/2026-11-culture-life.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| decision-hub | 2026-12 | `00-decision-hub/reports/2026-12-decision-hub.md` | `2026-Q4_quarterly.md` | main | ✅ 原文已收录 |
| decision-hub | 2026-11 | `00-decision-hub/reports/2026-11-decision-hub.md` | `2026-11-13_landing_checklist.md` | main | ✅ 原文已收录 |
| decision-hub | 2026-11 | `00-decision-hub/reports/2026-11-decision-hub.md` | `2026-11-13_settlement_profile.md` | appendix | ✅ 原文已收录 |
| economy-finance | 2026-11 | `07-economy-finance/reports/2026-11-economy-finance.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| economy-finance | 2026-11 | `07-economy-finance/reports/2026-11-economy-finance.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| education-qualification | 2026-11 | `10-education-qualification/reports/2026-11-education-qualification.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| education-qualification | 2026-11 | `10-education-qualification/reports/2026-11-education-qualification.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| exit-transition-return | 2026-11 | `16-exit-transition-return/reports/2026-11-exit-transition-return.md` | `2026-11-14_initial_analysis_report.md` | main | ✅ 原文已收录 |
| exit-transition-return | 2026-11 | `16-exit-transition-return/reports/2026-11-exit-transition-return.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| health-wellbeing | 2026-11 | `15-health-wellbeing/reports/2026-11-health-wellbeing.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| health-wellbeing | 2026-11 | `15-health-wellbeing/reports/2026-11-health-wellbeing.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| industry-autonomous | 2026-11 | `05-industry-autonomous/reports/2026-11-industry-autonomous.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| industry-autonomous | 2026-11 | `05-industry-autonomous/reports/2026-11-industry-autonomous.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| industry-logistics | 2026-11 | `04-industry-logistics/reports/2026-11-industry-logistics.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| industry-logistics | 2026-11 | `04-industry-logistics/reports/2026-11-industry-logistics.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| industry-technology | 2026-11 | `06-industry-technology/reports/2026-11-industry-technology.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| industry-technology | 2026-11 | `06-industry-technology/reports/2026-11-industry-technology.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| language-japanese | 2026-11 | `11-language-japanese/reports/2026-11-language-japanese.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| language-japanese | 2026-11 | `11-language-japanese/reports/2026-11-language-japanese.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| life-operations | 2026-11 | `14-life-operations/reports/2026-11-life-operations.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| life-operations | 2026-11 | `14-life-operations/reports/2026-11-life-operations.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| politics-law | 2026-11 | `09-politics-law/reports/2026-11-politics-law.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| politics-law | 2026-11 | `09-politics-law/reports/2026-11-politics-law.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| regional-info | 2026-11 | `13-regional-info/reports/2026-11-regional-info.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| regional-info | 2026-11 | `13-regional-info/reports/2026-11-regional-info.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| ssw-driver | 2026-12 | `01-ssw-driver/reports/2026-12-ssw-driver.md` | `2026-Q4_quarterly.md` | main | ✅ 原文已收录 |
| ssw-driver | 2026-11 | `01-ssw-driver/reports/2026-11-ssw-driver.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| ssw-driver | 2026-11 | `01-ssw-driver/reports/2026-11-ssw-driver.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |
| visa-immigration | 2026-11 | `08-visa-immigration/reports/2026-11-visa-immigration.md` | `2026-11-13_initial_analysis_report.md` | main | ✅ 原文已收录 |
| visa-immigration | 2026-11 | `08-visa-immigration/reports/2026-11-visa-immigration.md` | `2026-11_baseline_report.md` | appendix | ✅ 原文已收录 |

## 三、内容留存校验

每份存量报告的归一化全文（去空白）均作为子串出现在目标文件中，脚本在 --apply 时逐份校验，任一缺失即报错退出。

- 迁移报告总数：36
- 全部通过内容留存校验：是
