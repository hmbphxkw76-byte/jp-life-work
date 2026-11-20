# 双轴评审：DIKW 端到端血缘视图（n24-dikw-lineage）

> **工单**：n24-dikw-lineage（docs/toolchain/tickets/n24-dikw-lineage.md）
> **评审日期**：2026-11-20
> **评审口径**：Standards（TOOLCHAIN-DEV-SPEC / 仓库规范符合性）+ Spec（工单设计完备性：目标 / 验收判据 / 涉及文件 / 风险与依赖）
> **证据来源**：工单设计文本 + 规约条款 + 涉及文件存在性核对；**不核验实施产物**
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**

## 一、Standards 轴（规约符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 命名规范（§四） | 通过 | slug `n24-dikw-lineage` kebab-case，无 `YYYY-MM-` 前缀 |
| 适用边界（§二） | 通过 | 主体 `engine/tools/fact_card_check.py`、`engine/tools/decision_metrics.py`（工具链）；`00-decision-hub/data/decision_hub_registry.md` 为数据活台账，工单声明「先文档后工具」 |
| 退出码契约（§五） | 通过 | 未新增工具退出码；血缘缺失显式标注，不虚构 |
| 异常不静默（§五） | 通过 | 血缘数据缺失时显式标注；不强制回填历史血缘，避免过度改动 |
| 单一事实源（§六） | 通过 | 整合既有 FC 指针 / C-13 / 血缘模块五 / `source-index.json`，不新增手工血缘表 |
| 测试（S3） | 通过 | 验收第 4 条守卫测试 + `unittest` 全绿 |
| 隔离与顺序（AGENTS.md 规约二） | 通过 | 状态注明与 n19 / n20 改动区域不同，建议 n19 → n20 → n24 |

**Standards 结论：无 P0/P1。**

## 二、Spec 轴（工单设计完备性）

| 验收判据 | 设计可验证性 | 结论 | 证据 |
|---|---|---|---|
| 1. `fact_card_check` 血缘索引 | 输出格式（JSON / md） | 覆盖 | `FC-NNN → 引用报告 → 登记册行` |
| 2. `decision_metrics` 五问结论血缘 | 输出 + 缺失标注 | 覆盖 | `结论 ← FC/报告 ← 登记册 ← 来源 URL` |
| 3. 登记册增「DIKW 血缘」节 | 文档节 | 覆盖 | 「先文档后工具」；缺失显式标注 |
| 4. 守卫测试 + `unittest` | unittest 断言 | 覆盖 | `test_tools.py` 增 `lineage` 断言 |

**Spec 结论：无 P0/P1。**

## 三、设计观察（P2，不阻断）

1. **空值表示未定义**：血缘依赖既有 FC 指针完整性，部分报告无指针；工单已声明缺失显式标注、不强制回填，但未见「无指针」时的空值表示（如 `references: []`）约定，建议明确以区分「缺失」与「无指针」。
2. **结论匹配口径需固化**：`decision_metrics --lineage` 结论匹配按括号前缀归一，口径建议在 `00-decision-hub/data/decision_hub_registry.md` 血缘节固化，避免跨月漂移。

## 四、证据清单

- 工单：`docs/toolchain/tickets/n24-dikw-lineage.md` §目标 / §验收判据 1–4 / §涉及文件 / §风险与依赖 / §证据。
- 规约：`docs/toolchain/TOOLCHAIN-DEV-SPEC.md` 第二节、第三节、第五节、第七节。
- 一致性核对（只读）：`engine/tools/fact_card_check.py`、`engine/tools/decision_metrics.py`、`00-decision-hub/data/decision_hub_registry.md`（含 §四·补 DIKW 血缘节）存在。
