# 工单 N20：· 反馈层「使用 → 规划」回路（P1，组 A）

> **来源**：情报科学五框架分析（会话，2026-11-20）· 差距 G2（情报周期·反馈）
> **状态**：待实施
> **验收判据**：见下方「验收判据」节；完成后回填状态与证据。

---

· 反馈层「使用 → 规划」回路（P1，组 A）

- **目标**：打通情报周期分发后的**外部反馈回路**——把「决策使用 / 缺失闭环 / 补缺周期」回流到规划，改变当前只有内部质量环、五问判定率 0% 的断裂状态。
- **验收判据**：
  1. `engine/tools/decision_metrics.py` 增反馈指标：五问判定率、缺失闭环率、补缺平均周期、决策记录引用次数；无法采集的指标显式标「不可采集」，不虚构。
  2. `.github/workflows/scheduled-maintenance.yml` 在 `decision_metrics --history` 之后增「反馈汇总」步骤，产物落 `engine/report-audits/toolchain/`。
  3. `00-decision-hub/prompts/business-config.md` 增「反馈回流」节；每期维护输出「决策使用反馈 → 需求变更清单」，无变更时显式写「本期无需求变更」。
  4. `engine/tools/decision_log.py --check` 扩展：反馈事件须关联需求编号；缺失时告警不阻断（rc=2），并在 `validate.yml` 既有步骤内生效。
  5. `engine/tests/test_tools.py` 增守卫测试；`unittest` 全绿。
- **实施步骤**：① 核对 `decision_metrics.py` 跨月逻辑与既有收敛率/判定率；② 增反馈指标与汇总输出；③ 工作流加步骤；④ 00 提示词增反馈回流节；⑤ `decision_log` 校验扩展；⑥ 测试与回填。
- **涉及文件**：`engine/tools/decision_metrics.py`、`engine/tools/decision_log.py`、`.github/workflows/scheduled-maintenance.yml`、`00-decision-hub/prompts/business-config.md`、`engine/tests/test_tools.py`。
- **风险与依赖**：引用次数可能不可得（无埋点）；用 `decision_log` 引用次数代理并显式说明口径。与 N19 的 PIR 需求编号共用同一编号规则。
- **证据**：
  - 工具：`decision_metrics.collect()` 增反馈维度（`gap_total` / `gap_closed` / `gap_close_rate`，缺失闭环率；`gap_close_avg_days=None` 显式标注不可计算；决策记录引用次数以 `decision_log_entries` 为代理）；`render_md` 增「缺失闭环率（n20）」行。
  - `decision_log.py` 增 `_known_questions()`（读登记册第一节决策问题 + 聚合值「全部」）；`check()` 校验每条记录可关联需求，未关联则告警 rc=2。
  - 工作流：`scheduled-maintenance.yml` 在决策度量快照后增「反馈汇总」步骤（生成 `engine/report-audits/toolchain/requirements-matrix.md` + `--trend`）。
  - 提示词：`00-decision-hub/prompts/business-config.md` 第三节增「反馈回流（n20）」。
  - 实测：`decision_metrics` 缺失闭环率 8/11 = 72.7%、需求覆盖 4/19；`decision_log --check` rc=0（4 条记录均可关联）。
  - 测试：`test_decision_metrics.py` 11 项 OK（新增反馈维度断言）；`test_tools.py` 237 项 OK（新增 `decision_log` 关联校验）；`validate.py` / `prompt_check.py` / ruff 全绿。
  - 文档：`engine/tools/README.md` v1.9。
- **状态**：已实施（未提交，位于 worktree `n20-feedback-loop`；已复制 n19 产物，合并须按 n19 → n20 顺序）。
