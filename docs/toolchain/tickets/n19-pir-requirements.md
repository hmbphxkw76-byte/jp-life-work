# 工单 N19：· 规划层情报需求登记（P1，组 A）

> **来源**：情报科学五框架分析（会话，2026-11-20）· 差距 G1（情报周期·规划）
> **状态**：已入库
> **验收判据**：见下方「验收判据」节；完成后回填状态与证据。

---

· 规划层情报需求登记（P1，组 A）

- **目标**：建立「情报需求（PIR）」登记与覆盖矩阵，使报告规划由**决策需求**驱动，而非仅由「主题 × 周期」驱动；让「为谁决策、缺什么、谁负责」可机读。
- **验收判据**：
  1. `python engine/tools/update_planner.py --requirements --porcelain` 输出需求覆盖矩阵 JSON，字段含：`需求编号 / 决策问题 / 责任主题 / 覆盖状态 / 期限 / 关联缺失编号`；数据源为 `00-decision-hub/data/decision_hub_registry.md` 第一节（五问指标状态表）+ 第二节（缺失清单）。
  2. `engine/tools/decision_metrics.py` 增「需求维度」输出：需求总数 / 已覆盖 / 部分 / 未覆盖 / 超期未闭环；`--check` 可解析、`--json` 含该段。
  3. `00-decision-hub/prompts/business-config.md` 第三节增 PIR 字段与「需求命中检查」步骤；至少 `01-ssw-driver` 与 `08-visa-residence` 两个主题的 `prompts/prompt-update.md` 落地试点。
  4. `engine/tests/test_tools.py` 增守卫测试：`--requirements` 退出码 0、JSON 字段齐全；`decision_metrics` 需求指标存在。
  5. `unittest` 全绿；`validate.py` rc=0；`prompt_check.py` rc=0。
- **实施步骤**：① 读 `decision_hub_registry.md` 表结构，定义需求编号规则（如 `REQ-01…`，与五问编号对齐）；② `update_planner.py` 增 `--requirements`（复用 `--porcelain` 输出约定）；③ `decision_metrics.py` 增需求指标；④ 提示词改动（00 + 2 主题试点）；⑤ 补守卫测试；⑥ 回填证据。
- **涉及文件**：`engine/tools/update_planner.py`、`engine/tools/decision_metrics.py`、`00-decision-hub/prompts/business-config.md`、`01-ssw-driver/prompts/prompt-update.md`、`08-visa-residence/prompts/prompt-update.md`、`engine/tests/test_tools.py`。
- **风险与依赖**：需求登记与既有「五问」「缺失清单」边界须明确——五问=决策问题、缺失清单=数据缺口、PIR=需求优先级与责任主题映射；**先只读生成，不新增手工表**，避免三处重复维护。
- **证据**：
  - 工具：`decision_metrics.requirements_matrix()` 从登记册第一节（五问指标状态表，7 列）+ 第二节（暴露的缺失清单，6 列）生成 `REQ-NN` 需求覆盖矩阵与 `GAP-NN` 缺失清单，按「覆盖的决策问题」包含「决策问题」关联；`collect()` 增需求维度（需求总数 / 已覆盖 / 部分 / 未覆盖 / 超期未闭环 / 覆盖率）。
  - `update_planner.py` 增 `--requirements`（人读表格 / `--porcelain` JSON）；`render_requirements()`。
  - 提示词：`00-decision-hub/prompts/business-config.md` 第三节增 PIR 登记字段与需求命中检查；`01-ssw-driver/prompts/prompt-update.md`、`08-visa-immigration/prompts/prompt-policy-review.md` 第五节增「需求命中检查」。
  - 实测：`update_planner --requirements --porcelain` 输出 19 条需求 / 11 条缺失（rc=0）；`decision_metrics` 需求覆盖率 4/19、超期 0（rc=2，因既有缺失）。
  - 测试：`test_decision_metrics.py` 11 项 OK（新增需求矩阵 / render / collect 需求字段）；`test_tools.py` 236 项 OK（新增 `render_requirements` / `--requirements --porcelain`）；`validate.py` / `prompt_check.py` / ruff 全绿。
  - 文档：`engine/tools/README.md` v1.8。
- **状态**：已入库（实施完成并合并推送至 `origin/main`；证据见上）。
