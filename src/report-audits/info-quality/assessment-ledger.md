# 信息质量评估台账

> 运行日期：2026-11-15　|　评估范围：全项目 21 个主题
> 数据来源：info_quality_check.py 程序化判定（《信息质量评估提示词体系》可执行子集）

## 四维度量化指标（修复前）

| 维度 | 指标 | 实测值 | 门槛 | 判定 |
|---|---|---|---|---|
| 完整性 | 必需要素覆盖率 | 100.0% | ≥ 95% | 达标 |
| 完整性 | 完整主题数 | 21/21 | — | — |
| 一致性 | 矛盾/口径问题数 | 0 | = 0 | 达标 |
| 一致性 | 逻辑断层数 | 0 | — | — |
| 准确性 | 来源标注覆盖率 | 37.3% | ≥ 20% | 达标 |
| 准确性 | 语义目标完成度（向 100%，单独公示） | 37.3% | 目标 100%（不阻断） | — |
| 准确性 | 过期未标注报告数 | 0 | = 0 | 达标 |
| 关联性 | 重复冗余率 | 0.5% | ≤ 10% | 达标 |
| 关联性 | 跨报告事实重复率 | 0.8% | ≤ 10% | 达标 |
| 完整性 | 空模块占比 | 0.0% | ≤ 20% | 达标 |
| 关联性 | 归属错误数 | 0 | = 0 | 达标 |
| 关联性 | 交叉引用有效率 | 100.0% | = 100% | 达标 |
| 问题分布 | P0 / P1 / P2 | 0 / 0 / 13 | — | — |

## 问题明细

| 编号 | 级别 | 主题 | 位置 | 位置描述 | 判定依据 | 修复规范 | 状态 |
|---|---|---|---|---|---|---|---|
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/reports/2026-11-ssw-driver.md | 跨文档重复 | 约 362 字的段落与 02-career-driver/reports/2026-11-career-driver.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 04-industry-logistics | 04-industry-logistics/reports/2026-11-industry-logistics.md | 跨文档重复 | 约 140 字的段落与 05-industry-autonomous/reports/2026-11-industry-autonomous.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 04-industry-logistics | 04-industry-logistics/reports/2026-11-industry-logistics.md | 跨文档重复 | 约 140 字的段落与 06-industry-technology/reports/2026-11-industry-technology.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 05-industry-autonomous | 05-industry-autonomous/reports/2026-11-industry-autonomous.md | 跨文档重复 | 约 779 字的段落与 06-industry-technology/reports/2026-11-industry-technology.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 07-economy-finance | 07-economy-finance/reports/2026-11-economy-finance.md | 跨文档重复 | 约 175 字的段落与 10-education-qualification/reports/2026-11-education-qualification.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 11-language-japanese | 11-language-japanese/reports/2026-11-language-japanese.md | 跨文档重复 | 约 189 字的段落与 12-culture-life/reports/2026-11-culture-life.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 11-language-japanese | 11-language-japanese/reports/2026-11-language-japanese.md | 跨文档重复 | 约 186 字的段落与 14-life-operations/reports/2026-11-life-operations.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 12-culture-life | 12-culture-life/reports/2026-11-culture-life.md | 跨文档重复 | 约 229 字的段落与 14-life-operations/reports/2026-11-life-operations.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 12-culture-life | 12-culture-life/reports/2026-11-culture-life.md | 跨文档重复 | 约 165 字的段落与 17-migration-compliance/reports/2026-11-migration-compliance.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 14-life-operations | 14-life-operations/reports/2026-11-life-operations.md | 跨文档重复 | 约 165 字的段落与 17-migration-compliance/reports/2026-11-migration-compliance.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 16-exit-transition-return | 16-exit-transition-return/reports/2026-11-exit-transition-return.md | 跨文档重复 | 约 204 字的段落与 20-overseas-china/reports/2026-11-overseas-china.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 18-family-parenting | 18-family-parenting/reports/2026-11-family-parenting.md | 跨文档重复 | 约 204 字的段落与 20-overseas-china/reports/2026-11-overseas-china.md 相似度 ≥ 80%，疑似研究正文交叉重复，建议确认是否需保留 | S-02 | 待处理 |
| C-07 | P2 | 15-health-wellbeing | 15-health-wellbeing/reports/2026-11-health-wellbeing.md | 事实单元来源覆盖不足 | 含数字事实单元（段落 + 表格行）来源覆盖率 15% < 20%（程序化门槛；语义目标 100%） | S-06 | 待处理 |
