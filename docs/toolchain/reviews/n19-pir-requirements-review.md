# 双轴评审：规划层情报需求登记（n19-pir-requirements）

> **工单**：n19-pir-requirements（docs/toolchain/tickets/n19-pir-requirements.md）
> **评审日期**：2026-11-20
> **评审口径**：Standards（TOOLCHAIN-DEV-SPEC / 仓库规范符合性）+ Spec（工单设计完备性：目标 / 验收判据 / 涉及文件 / 风险与依赖）
> **证据来源**：工单设计文本 + 规约条款 + 涉及文件存在性核对；**不核验实施产物**（不运行工单所列工具、不检查代码实现）
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**

## 一、Standards 轴（规约符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 命名规范（§四） | 通过 | 工单 slug `n19-pir-requirements` 为 kebab-case，无 `YYYY-MM-` 前缀；评审文件命名 `<slug>-review.md` |
| 适用边界（§二） | 通过（附 P2） | 主体为 `engine/tools/update_planner.py`、`engine/tools/decision_metrics.py`（工具链）；另涉 `00-decision-hub/prompts/business-config.md` 与主题 `prompts/`（内容层），验收第 5 条要求 `prompt_check.py rc=0` 同步内容流程 |
| 退出码契约（§五） | 通过 | `--requirements --porcelain` 退出码 0；`decision_metrics --check` 可解析；未引入 0/1/2 以外语义 |
| 异常不静默（§五） | 通过 | 覆盖状态含「未覆盖 / 超期未闭环」，缺失显式标注，未要求虚构指标 |
| 单一事实源（§六） | 通过 | 数据源限定 `decision_hub_registry.md` §一（五问指标状态表）+ §二（缺失清单）；明确「先只读生成，不新增手工表」，避免与五问 / 缺失清单三处重复维护 |
| 测试（S3） | 通过 | 验收第 4 条要求 `engine/tests/test_tools.py` 守卫测试（退出码 0 + 字段齐全） |
| 隔离与顺序（AGENTS.md 规约二） | 通过 | 工单状态注明 worktree `n19-pir-requirements`；n20 依赖本工单编号规则，索引批 2 排 n19 → n20 |

**Standards 结论：无 P0/P1。**

## 二、Spec 轴（工单设计完备性）

| 验收判据 | 设计可验证性 | 结论 | 证据 |
|---|---|---|---|
| 1. `--requirements --porcelain` 字段齐全 | 命令 + 字段清单可机读 | 覆盖 | 字段（需求编号 / 决策问题 / 责任主题 / 覆盖状态 / 期限 / 关联缺失编号）均可由 §一 / §二列派生（期限见 §二「期限」列，责任主题见 §一「来源主题」） |
| 2. `decision_metrics` 需求维度 | `--check` / `--json` 可解析 | 覆盖 | 指标含总数 / 已覆盖 / 部分 / 未覆盖 / 超期未闭环，口径与 §一「收敛状态」对应 |
| 3. 提示词 PIR 字段 + 命中检查 | `prompt_check.py` 可验 | 覆盖（附 P2） | 00 枢纽 + 2 主题试点；涉及文件主题 slug 与证据不一致，见观察 1 |
| 4. 守卫测试 | unittest 断言 | 覆盖 | 退出码 0 + JSON 字段齐全 |
| 5. 全绿门禁 | `unittest` / `validate.py` / `prompt_check.py` | 覆盖 | 三命令退出码明确 |

**Spec 结论：无 P0/P1。**

## 三、设计观察（P2，不阻断）

1. **涉及文件与证据的主题 slug 不一致**：`涉及文件` 列 `08-visa-residence/prompts/prompt-update.md`，`证据` 列 `08-visa-immigration/prompts/prompt-policy-review.md`；仓库无 `08-visa-residence` 主题，且 `08-visa-immigration/prompts/prompt-update.md` 不存在（实际为 `prompt-policy-review.md`）。建议工单统一为实际主题与文件，消除文本漂移。
2. **需求编号映射未要求落地**：实施步骤①要求定义 `REQ-NN` 并与五问编号对齐，但验收判据未要求编号映射表落地；建议在 `decision_metrics` 输出或登记册中保留 `REQ-NN ↔ 五问 #` 映射，便于审计。

## 四、证据清单

- 工单：`docs/toolchain/tickets/n19-pir-requirements.md` §目标 / §验收判据 1–5 / §涉及文件 / §风险与依赖 / §证据。
- 规约：`docs/toolchain/TOOLCHAIN-DEV-SPEC.md` 第二节、第三节、第四节、第五节、第七节。
- 一致性核对（只读）：`00-decision-hub/data/decision_hub_registry.md` §一 7 列 / §二 6 列存在；`engine/tools/update_planner.py`、`engine/tools/decision_metrics.py`、`00-decision-hub/prompts/business-config.md`、`01-ssw-driver/prompts/prompt-update.md` 存在；`08-visa-residence/prompts/prompt-update.md` 不存在（见观察 1）。
