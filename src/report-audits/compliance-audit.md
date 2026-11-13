# 报告合规性审计（历史报告 × 类型模板匹配度）

- **审计时间**：2026-11-13 10:24 UTC
- **审计范围**：全部业务线 reports/*.html（共 18 份）
- **匹配度**：4/18（22%）报告与对应类型模板规则完全匹配
- **规则来源**：[compliance-rules.json](../report_templates/compliance-rules.json)（12 类报告类型结构骨架，与 [template-registry.md](../report_templates/template-registry.md) 登记一致）
- **结论**：14 份报告存在不符合项，需整改 ⚠️

## 明细

```
[E] 01-ssw-driver/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「免责声明」
[E] 01-ssw-driver/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「不构成投资建议」
[W] 01-ssw-driver/reports/2026-11_baseline_report.html: [employment-research/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[W] 01-ssw-driver/reports/2026-Q4_quarterly.html: [employment-research/quarterly] h2 节数 10 超出模板骨架 9 节（如为业务固化锚请人工确认，否则须对齐类型模板 prompt-update-template.md）
[E] 01-ssw-driver/reports/2026-Q4_quarterly.html: [employment-research/quarterly] 缺少必填内容：「免责声明」
[E] 01-ssw-driver/reports/2026-Q4_quarterly.html: [employment-research/quarterly] 缺少必填内容：「不构成投资建议」
[E] 01-ssw-driver/reports/2026-Q4_quarterly.html: [employment-research/quarterly] 周期报告缺少顶部导航 <nav aria-label="报告导航">（通用规范第 5 节强制）
[E] 02-career-driver/reports/2026-11_baseline_report.html: [employment-research/baseline] 结构不完整：h2 节数 8 少于模板骨架 9 节（缺失即阻断）
[E] 02-career-driver/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「免责声明」
[E] 02-career-driver/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「不构成投资建议」
[W] 02-career-driver/reports/2026-11_baseline_report.html: [employment-research/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[E] 03-career-management/reports/2026-11_baseline_report.html: [employment-research/baseline] 结构不完整：h2 节数 7 少于模板骨架 9 节（缺失即阻断）
[E] 03-career-management/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「免责声明」
[E] 03-career-management/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「不构成投资建议」
[W] 03-career-management/reports/2026-11_baseline_report.html: [employment-research/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[E] 04-industry-logistics/reports/2026-11_baseline_report.html: [industry-research/baseline] 结构不完整：h2 节数 6 少于模板骨架 9 节（缺失即阻断）
[E] 04-industry-logistics/reports/2026-11_baseline_report.html: [industry-research/baseline] 缺少必填内容：「免责声明」
[E] 04-industry-logistics/reports/2026-11_baseline_report.html: [industry-research/baseline] 缺少必填内容：「不构成投资建议」
[W] 04-industry-logistics/reports/2026-11_baseline_report.html: [industry-research/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[E] 05-industry-autonomous/reports/2026-11_baseline_report.html: [industry-research/baseline] 结构不完整：h2 节数 6 少于模板骨架 9 节（缺失即阻断）
[E] 05-industry-autonomous/reports/2026-11_baseline_report.html: [industry-research/baseline] 缺少必填内容：「免责声明」
[E] 05-industry-autonomous/reports/2026-11_baseline_report.html: [industry-research/baseline] 缺少必填内容：「不构成投资建议」
[W] 05-industry-autonomous/reports/2026-11_baseline_report.html: [industry-research/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[E] 06-industry-technology/reports/2026-11_baseline_report.html: [industry-research/baseline] 结构不完整：h2 节数 5 少于模板骨架 9 节（缺失即阻断）
[E] 06-industry-technology/reports/2026-11_baseline_report.html: [industry-research/baseline] 缺少必填内容：「免责声明」
[E] 06-industry-technology/reports/2026-11_baseline_report.html: [industry-research/baseline] 缺少必填内容：「不构成投资建议」
[W] 06-industry-technology/reports/2026-11_baseline_report.html: [industry-research/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[E] 07-economy-finance/reports/2026-11_baseline_report.html: [employment-research/baseline] 结构不完整：h2 节数 6 少于模板骨架 9 节（缺失即阻断）
[E] 07-economy-finance/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「免责声明」
[E] 07-economy-finance/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「不构成投资建议」
[W] 07-economy-finance/reports/2026-11_baseline_report.html: [employment-research/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[W] 08-visa-immigration/reports/2026-11_baseline_report.html: [policy-analysis/baseline] h2 节数 11 超出模板骨架 9 节（如为业务固化锚请人工确认，否则须对齐类型模板 prompt-baseline-setup-template.md）
[E] 08-visa-immigration/reports/2026-11_baseline_report.html: [policy-analysis/baseline] 缺少必填内容：「免责声明」
[E] 08-visa-immigration/reports/2026-11_baseline_report.html: [policy-analysis/baseline] 缺少必填内容：「不构成投资建议」
[W] 08-visa-immigration/reports/2026-11_baseline_report.html: [policy-analysis/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[E] 09-politics-law/reports/2026-11_baseline_report.html: [policy-analysis/baseline] 结构不完整：h2 节数 5 少于模板骨架 9 节（缺失即阻断）
[E] 09-politics-law/reports/2026-11_baseline_report.html: [policy-analysis/baseline] 缺少必填内容：「免责声明」
[E] 09-politics-law/reports/2026-11_baseline_report.html: [policy-analysis/baseline] 缺少必填内容：「不构成投资建议」
[W] 09-politics-law/reports/2026-11_baseline_report.html: [policy-analysis/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[E] 10-education-qualification/reports/2026-11_baseline_report.html: [employment-research/baseline] 结构不完整：h2 节数 6 少于模板骨架 9 节（缺失即阻断）
[E] 10-education-qualification/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「免责声明」
[E] 10-education-qualification/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「不构成投资建议」
[W] 10-education-qualification/reports/2026-11_baseline_report.html: [employment-research/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[E] 11-language-japanese/reports/2026-11_baseline_report.html: [employment-research/baseline] 结构不完整：h2 节数 8 少于模板骨架 9 节（缺失即阻断）
[E] 11-language-japanese/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「免责声明」
[E] 11-language-japanese/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「不构成投资建议」
[W] 11-language-japanese/reports/2026-11_baseline_report.html: [employment-research/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[E] 12-culture-life/reports/2026-11_baseline_report.html: [employment-research/baseline] 结构不完整：h2 节数 7 少于模板骨架 9 节（缺失即阻断）
[E] 12-culture-life/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「免责声明」
[E] 12-culture-life/reports/2026-11_baseline_report.html: [employment-research/baseline] 缺少必填内容：「不构成投资建议」
[W] 12-culture-life/reports/2026-11_baseline_report.html: [employment-research/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
[E] 13-regional-info/reports/2026-11_baseline_report.html: [market-monitoring/baseline] 结构不完整：h2 节数 4 少于模板骨架 10 节（缺失即阻断）
[E] 13-regional-info/reports/2026-11_baseline_report.html: [market-monitoring/baseline] 缺少必填内容：「免责声明」
[E] 13-regional-info/reports/2026-11_baseline_report.html: [market-monitoring/baseline] 缺少必填内容：「不构成投资建议」
[W] 13-regional-info/reports/2026-11_baseline_report.html: [market-monitoring/baseline] 基线报告缺少简化锚点导航 <nav>（建议补充，不阻断）
```
