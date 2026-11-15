# 信息质量验证报告

> 运行日期：2026-11-15

## 修复后指标（复评）

| 指标 | 修复前 | 修复后 | 门槛 |
|---|---|---|---|
| 必需要素覆盖率 | 100.0% | 100.0% | ≥ 95% |
| 重复冗余率 | 0.0% | 0.0% | ≤ 10% |
| 跨报告事实重复率 | 0.8% | 0.8% | ≤ 10% |
| 空模块占比 | 0.0% | 0.0% | ≤ 20% |
| 交叉引用有效率 | 99.9% | 99.9% | = 100% |
| 矛盾/口径问题数 | 0 | 0 | = 0 |
| 待处理问题数 | 5 | 1 | — |

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

- [P2] C-09 00-decision-hub/00-decision-hub/data/decision_onepager.md：引用目标不存在：./decision_log.md

**验证结论：全部通过**
