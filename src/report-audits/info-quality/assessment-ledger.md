# 信息质量评估台账

> 运行日期：2026-11-14　|　评估范围：全项目 21 个主题
> 数据来源：info_quality_check.py 程序化判定（《信息质量评估提示词体系》可执行子集）

## 四维度量化指标（修复前）

| 维度 | 指标 | 实测值 | 门槛 | 判定 |
|---|---|---|---|---|
| 完整性 | 必需要素覆盖率 | 100.0% | ≥ 95% | 达标 |
| 完整性 | 完整主题数 | 21/21 | — | — |
| 一致性 | 矛盾/口径问题数 | 2 | = 0 | 不达标 |
| 一致性 | 逻辑断层数 | 0 | — | — |
| 准确性 | 来源标注覆盖率 | 41.4% | ≥ 20% | 达标 |
| 准确性 | 过期未标注报告数 | 0 | = 0 | 达标 |
| 关联性 | 重复冗余率 | 0.0% | ≤ 10% | 达标 |
| 关联性 | 归属错误数 | 0 | = 0 | 达标 |
| 关联性 | 交叉引用有效率 | 100.0% | = 100% | 达标 |
| 问题分布 | P0 / P1 / P2 | 0 / 0 / 52 | — | — |

## 问题明细

| 编号 | 级别 | 主题 | 位置 | 位置描述 | 判定依据 | 修复规范 | 状态 |
|---|---|---|---|---|---|---|---|
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/operations-guide.md | 跨文档重复 | 约 180 字的段落同时出现在 7 个主题（01-ssw-driver, 02-career-driver, 03-career-management, 07-economy-finance, 10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/operations-guide.md | 跨文档重复 | 约 209 字的段落同时出现在 7 个主题（01-ssw-driver, 02-career-driver, 03-career-management, 07-economy-finance, 10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/operations-guide.md | 跨文档重复 | 约 129 字的段落同时出现在 7 个主题（01-ssw-driver, 02-career-driver, 03-career-management, 07-economy-finance, 10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/operations-guide.md | 跨文档重复 | 约 142 字的段落同时出现在 7 个主题（01-ssw-driver, 02-career-driver, 03-career-management, 07-economy-finance, 10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/operations-guide.md | 跨文档重复 | 约 153 字的段落同时出现在 7 个主题（01-ssw-driver, 02-career-driver, 03-career-management, 07-economy-finance, 10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/prompts/prompt-baseline-setup.md | 跨文档重复 | 约 145 字的段落同时出现在 3 个主题（01-ssw-driver, 02-career-driver, 03-career-management），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/prompts/prompt-baseline-setup.md | 跨文档重复 | 约 214 字的段落同时出现在 7 个主题（01-ssw-driver, 02-career-driver, 03-career-management, 07-economy-finance, 10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/prompts/prompt-baseline-setup.md | 跨文档重复 | 约 219 字的段落同时出现在 16 个主题（01-ssw-driver, 02-career-driver, 03-career-management, 04-industry-logistics, 05-industry-autonomous, 06-industry-technology, 07-economy-finance, 08-visa-immigration, 09-politics-law, 10-education-qualification, 11-language-japanese, 12-culture-life, 13-regional-info, 16-exit-transition-return, 17-migration-compliance, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/prompts/prompt-update.md | 跨文档重复 | 约 555 字的段落同时出现在 7 个主题（01-ssw-driver, 02-career-driver, 03-career-management, 07-economy-finance, 10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/prompts/prompt-update.md | 跨文档重复 | 约 219 字的段落同时出现在 6 个主题（01-ssw-driver, 02-career-driver, 03-career-management, 07-economy-finance, 10-education-qualification, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 01-ssw-driver | 01-ssw-driver/prompts/prompt-update.md | 跨文档重复 | 约 180 字的段落同时出现在 7 个主题（01-ssw-driver, 02-career-driver, 03-career-management, 07-economy-finance, 10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 02-career-driver | 02-career-driver/operations-guide.md | 跨文档重复 | 约 184 字的段落同时出现在 2 个主题（02-career-driver, 03-career-management），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 02-career-driver | 02-career-driver/prompts/business-config.md | 跨文档重复 | 约 187 字的段落同时出现在 3 个主题（02-career-driver, 03-career-management, 07-economy-finance），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 02-career-driver | 02-career-driver/prompts/business-config.md | 跨文档重复 | 约 333 字的段落同时出现在 5 个主题（02-career-driver, 03-career-management, 10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 02-career-driver | 02-career-driver/prompts/prompt-update.md | 跨文档重复 | 约 141 字的段落同时出现在 2 个主题（02-career-driver, 07-economy-finance），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 03-career-management | 03-career-management/prompts/prompt-update.md | 跨文档重复 | 约 141 字的段落同时出现在 3 个主题（03-career-management, 11-language-japanese, 13-regional-info），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 04-industry-logistics | 04-industry-logistics/operations-guide.md | 跨文档重复 | 约 140 字的段落同时出现在 3 个主题（04-industry-logistics, 05-industry-autonomous, 06-industry-technology），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 04-industry-logistics | 04-industry-logistics/operations-guide.md | 跨文档重复 | 约 153 字的段落同时出现在 3 个主题（04-industry-logistics, 05-industry-autonomous, 06-industry-technology），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 04-industry-logistics | 04-industry-logistics/prompts/business-config.md | 跨文档重复 | 约 184 字的段落同时出现在 2 个主题（04-industry-logistics, 05-industry-autonomous），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 04-industry-logistics | 04-industry-logistics/prompts/prompt-annual-refresh.md | 跨文档重复 | 约 158 字的段落同时出现在 3 个主题（04-industry-logistics, 05-industry-autonomous, 06-industry-technology），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 04-industry-logistics | 04-industry-logistics/prompts/prompt-annual-refresh.md | 跨文档重复 | 约 216 字的段落同时出现在 3 个主题（04-industry-logistics, 05-industry-autonomous, 06-industry-technology），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 04-industry-logistics | 04-industry-logistics/prompts/prompt-annual-refresh.md | 跨文档重复 | 约 192 字的段落同时出现在 3 个主题（04-industry-logistics, 05-industry-autonomous, 06-industry-technology），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 04-industry-logistics | 04-industry-logistics/prompts/prompt-baseline-setup.md | 跨文档重复 | 约 216 字的段落同时出现在 2 个主题（04-industry-logistics, 05-industry-autonomous），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 05-industry-autonomous | 05-industry-autonomous/prompts/business-config.md | 跨文档重复 | 约 288 字的段落同时出现在 2 个主题（05-industry-autonomous, 06-industry-technology），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 08-visa-immigration | 08-visa-immigration/operations-guide.md | 跨文档重复 | 约 214 字的段落同时出现在 4 个主题（08-visa-immigration, 09-politics-law, 16-exit-transition-return, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 08-visa-immigration | 08-visa-immigration/operations-guide.md | 跨文档重复 | 约 156 字的段落同时出现在 3 个主题（08-visa-immigration, 09-politics-law, 16-exit-transition-return），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 08-visa-immigration | 08-visa-immigration/operations-guide.md | 跨文档重复 | 约 153 字的段落同时出现在 5 个主题（08-visa-immigration, 09-politics-law, 16-exit-transition-return, 17-migration-compliance, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 08-visa-immigration | 08-visa-immigration/prompts/prompt-baseline-setup.md | 跨文档重复 | 约 196 字的段落同时出现在 2 个主题（08-visa-immigration, 16-exit-transition-return），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 08-visa-immigration | 08-visa-immigration/prompts/prompt-policy-review.md | 跨文档重复 | 约 498 字的段落同时出现在 4 个主题（08-visa-immigration, 09-politics-law, 16-exit-transition-return, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 08-visa-immigration | 08-visa-immigration/prompts/prompt-policy-review.md | 跨文档重复 | 约 127 字的段落同时出现在 5 个主题（08-visa-immigration, 09-politics-law, 16-exit-transition-return, 17-migration-compliance, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 08-visa-immigration | 08-visa-immigration/prompts/prompt-policy-review.md | 跨文档重复 | 约 159 字的段落同时出现在 2 个主题（08-visa-immigration, 09-politics-law），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 08-visa-immigration | 08-visa-immigration/prompts/prompt-policy-review.md | 跨文档重复 | 约 251 字的段落同时出现在 2 个主题（08-visa-immigration, 09-politics-law），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 08-visa-immigration | 08-visa-immigration/prompts/prompt-policy-review.md | 跨文档重复 | 约 194 字的段落同时出现在 5 个主题（08-visa-immigration, 09-politics-law, 16-exit-transition-return, 17-migration-compliance, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 10-education-qualification | 10-education-qualification/prompts/business-config.md | 跨文档重复 | 约 182 字的段落同时出现在 3 个主题（10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 10-education-qualification | 10-education-qualification/prompts/prompt-baseline-setup.md | 跨文档重复 | 约 186 字的段落同时出现在 3 个主题（10-education-qualification, 11-language-japanese, 12-culture-life），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 14-life-operations | 14-life-operations/operations-guide.md | 跨文档重复 | 约 211 字的段落同时出现在 2 个主题（14-life-operations, 15-health-wellbeing），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 14-life-operations | 14-life-operations/prompts/prompt-baseline-setup.md | 跨文档重复 | 约 570 字的段落同时出现在 2 个主题（14-life-operations, 15-health-wellbeing），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 14-life-operations | 14-life-operations/prompts/prompt-baseline-setup.md | 跨文档重复 | 约 148 字的段落同时出现在 2 个主题（14-life-operations, 15-health-wellbeing），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 14-life-operations | 14-life-operations/prompts/prompt-update.md | 跨文档重复 | 约 302 字的段落同时出现在 2 个主题（14-life-operations, 15-health-wellbeing），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 16-exit-transition-return | 16-exit-transition-return/operations-guide.md | 跨文档重复 | 约 121 字的段落同时出现在 3 个主题（16-exit-transition-return, 17-migration-compliance, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 16-exit-transition-return | 16-exit-transition-return/prompts/business-config.md | 跨文档重复 | 约 300 字的段落同时出现在 2 个主题（16-exit-transition-return, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 16-exit-transition-return | 16-exit-transition-return/prompts/prompt-baseline-setup.md | 跨文档重复 | 约 156 字的段落同时出现在 2 个主题（16-exit-transition-return, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 16-exit-transition-return | 16-exit-transition-return/prompts/prompt-policy-review.md | 跨文档重复 | 约 159 字的段落同时出现在 2 个主题（16-exit-transition-return, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 16-exit-transition-return | 16-exit-transition-return/prompts/prompt-policy-review.md | 跨文档重复 | 约 242 字的段落同时出现在 2 个主题（16-exit-transition-return, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 16-exit-transition-return | 16-exit-transition-return/prompts/prompt-policy-review.md | 跨文档重复 | 约 154 字的段落同时出现在 2 个主题（16-exit-transition-return, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 16-exit-transition-return | 16-exit-transition-return/prompts/prompt-policy-review.md | 跨文档重复 | 约 251 字的段落同时出现在 2 个主题（16-exit-transition-return, 20-overseas-china），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-03 | P2 | 18-family-parenting | 18-family-parenting/prompts/prompt-baseline-setup.md | 跨文档重复 | 约 224 字的段落同时出现在 2 个主题（18-family-parenting, 19-safety-disaster），疑似模板冗余，建议确认是否需保留 | S-02 | 待处理 |
| C-07 | P2 | 05-industry-autonomous | 05-industry-autonomous/reports/2026-11-industry-autonomous.md | 事实段落来源覆盖不足 | 含数字事实段落来源覆盖率 19% < 20% | S-06 | 需人工/外部 |
| C-07 | P2 | 07-economy-finance | 07-economy-finance/reports/2026-11-economy-finance.md | 事实段落来源覆盖不足 | 含数字事实段落来源覆盖率 19% < 20% | S-06 | 需人工/外部 |
| C-07 | P2 | 14-life-operations | 14-life-operations/reports/2026-11-life-operations.md | 事实段落来源覆盖不足 | 含数字事实段落来源覆盖率 14% < 20% | S-06 | 需人工/外部 |
| C-10 | P2 | 01-ssw-driver|02-career-driver|07-economy-finance | data/（登记册） | 口径不一致 | 指标「運輸業月均工资」在 3 个主题登记册中口径表述不一致 | S-09 | 需人工/外部 |
| C-10 | P2 | 16-exit-transition-return|17-migration-compliance|18-family-parenting|19-safety-disaster|20-overseas-china | data/（登记册） | 口径不一致 | 指标「官方来源更新与口径冲突」在 5 个主题登记册中口径表述不一致 | S-09 | 需人工/外部 |
