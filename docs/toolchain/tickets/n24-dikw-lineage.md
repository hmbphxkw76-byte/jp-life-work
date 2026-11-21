# 工单 N24：· DIKW 端到端血缘视图（P2，组 C）

> **来源**：情报科学五框架分析（会话，2026-11-20）· 差距 G6（DIKW）
> **状态**：已入库
> **验收判据**：见下方「验收判据」节；完成后回填状态与证据。

---

· DIKW 端到端血缘视图（P2，组 C）

- **目标**：把分散的派生关系（FC 指针 K→I、C-13 K↔I、血缘模块五 I→D）整合为统一的「结论 ← 知识 ← 信息 ← 数据」可追溯视图，让智慧层（五问）可回溯到来源 URL。
- **验收判据**：
  1. `engine/tools/fact_card_check.py` 扩展输出「血缘索引」：`FC-NNN → 引用报告 → 登记册行`（JSON 或 md）。
  2. `engine/tools/decision_metrics.py` 输出五问结论血缘：`结论 ← FC/报告 ← 登记册 ← 来源 URL`；血缘数据缺失时显式标注，不虚构。
  3. `00-decision-hub/data/decision_hub_registry.md` 增「DIKW 血缘」节（先文档后工具）。
  4. `engine/tests/test_tools.py` 增守卫测试；`unittest` 全绿。
- **实施步骤**：① 盘点既有血缘载体（FC 指针 / C-13 / 模块五 / `source-index.json`）；② 定义血缘输出格式；③ `fact_card_check` 增血缘索引；④ `decision_metrics` 增五问血缘；⑤ 00 登记册增血缘节；⑥ 测试与回填。
- **涉及文件**：`engine/tools/fact_card_check.py`、`engine/tools/decision_metrics.py`、`00-decision-hub/data/decision_hub_registry.md`、`engine/tests/test_tools.py`。
- **风险与依赖**：血缘依赖既有指针完整性（部分报告无 FC 指针），缺失项显式标注；不强制回填历史血缘，避免过度改动。
- **证据**：
  - 工具：`fact_card_check.py` 增 `lineage()` + `--lineage`（FC → 引用报告 / 登记册，知识 ← 信息）；`decision_metrics.py` 增 `lineage()` + `--lineage`（决策问题 → 结论 ← 引用位置 ← 责任主题；结论匹配按括号前缀归一）。
  - 文档：`00-decision-hub/data/decision_hub_registry.md` 增「四·补、DIKW 血缘（n24）」节。
  - 实测：`decision_metrics --lineage` 输出 19 条（结论已关联 4.1 判定，如「去不去 → 待定」）；`fact_card_check --lineage` 输出 16 张卡片血缘（FC-001 引用位于 00 data 层，reports 为空显式留空）。
  - 测试：`test_decision_metrics.py` 11 项 OK（新增 `lineage`）；`test_tools.py` 235 项 OK（新增 `fact_card_check.lineage`）；`validate.py` / ruff 全绿。
  - 文档：`engine/tools/README.md` v1.8。
- **状态**：已入库（实施完成并合并推送至 `origin/main`；证据见上）。
