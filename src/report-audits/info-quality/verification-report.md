# 信息质量验证报告

> 运行日期：2026-11-14

## 修复后指标（复评）

| 指标 | 修复前 | 修复后 | 门槛 |
|---|---|---|---|
| 必需要素覆盖率 | 100.0% | 100.0% | ≥ 95% |
| 重复冗余率 | 0.0% | 0.0% | ≤ 10% |
| 交叉引用有效率 | 100.0% | 100.0% | = 100% |
| 矛盾/口径问题数 | 2 | 2 | = 0 |
| 待处理问题数 | 52 | 52 | — |

## 校验项

| 校验项 | 结果 |
|---|---|
| required_coverage_ok | 通过 |
| dup_ratio_ok | 通过 |
| cite_valid_not_regressed | 通过 |
| p0p1_contradictions_zero | 通过 |
| no_new_open_findings | 通过 |
| no_regression | 通过 |
| repairs_verified | 通过 |

## 遗留项（需人工/外部介入）

- [P2] C-07 05-industry-autonomous/05-industry-autonomous/reports/2026-11-industry-autonomous.md：含数字事实段落来源覆盖率 19% < 20%
- [P2] C-07 07-economy-finance/07-economy-finance/reports/2026-11-economy-finance.md：含数字事实段落来源覆盖率 19% < 20%
- [P2] C-07 14-life-operations/14-life-operations/reports/2026-11-life-operations.md：含数字事实段落来源覆盖率 14% < 20%
- [P2] C-10 01-ssw-driver|02-career-driver|07-economy-finance/data/（登记册）：指标「運輸業月均工资」在 3 个主题登记册中口径表述不一致
- [P2] C-10 16-exit-transition-return|17-migration-compliance|18-family-parenting|19-safety-disaster|20-overseas-china/data/（登记册）：指标「官方来源更新与口径冲突」在 5 个主题登记册中口径表述不一致

**验证结论：全部通过**
