# 工单 N4：· decision_log 接入 CI（P1，组 C）

> **来源**：`docs/未完成项与对齐状态梳理-2026-11-19.md` 第五节
> **状态**：已完成（证据见 docs/未完成项与对齐状态梳理-2026-11-19.md 第八节）
> **验收判据**：见下方「验收判据」节；完成后回填状态与证据。

---

· decision_log 接入 CI（P1，组 C）

- **目标**：把 `engine/tools/decision_log.py` 纳入维护流水线，使决策日志可检测缺失。
- **验收判据**：`scheduled-maintenance.yml`（或 `validate.yml`）新增 `decision_log` 步骤；新增守卫测试断言步骤存在；`unittest` 全绿。
- **步骤**：① 读 `decision_log.py` 用法；② 在维护工作流加步骤（刷新决策日志）；③ 加守卫测试；④ 跑测试。
- **证据**：工作流 diff + 测试输出。
- **状态**：待实施。
