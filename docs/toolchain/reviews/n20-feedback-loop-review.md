# 双轴评审：反馈层「使用 → 规划」回路（n20-feedback-loop）

> **工单**：n20-feedback-loop（docs/toolchain/tickets/n20-feedback-loop.md）
> **评审日期**：2026-11-20
> **评审口径**：Standards（TOOLCHAIN-DEV-SPEC / 仓库规范符合性）+ Spec（工单设计完备性：目标 / 验收判据 / 涉及文件 / 风险与依赖）
> **证据来源**：工单设计文本 + 规约条款 + 涉及文件存在性核对；**不核验实施产物**
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**

## 一、Standards 轴（规约符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 命名规范（§四） | 通过 | slug `n20-feedback-loop` kebab-case，无 `YYYY-MM-` 前缀 |
| 适用边界（§二） | 通过（附 P2） | 主体 `engine/tools/decision_metrics.py`、`engine/tools/decision_log.py`、`.github/workflows/scheduled-maintenance.yml`（工具链 + CI）；另涉 `00-decision-hub/prompts/business-config.md`（内容层），验收未含 `prompt_check.py`，见观察 1 |
| 退出码契约（§五） | 通过 | `decision_log --check` 未关联需求 rc=2 告警不阻断；未引入 0/1/2 以外语义 |
| 异常不静默（§五） | 通过 | 无法采集指标显式标「不可采集」；引用次数以 `decision_log` 为代理并显式说明口径 |
| 单一事实源（§六） | 通过 | 反馈指标复用 `decision_metrics.collect()`；与 n19 共用 PIR 编号规则，未新增手工表 |
| 测试（S3） | 通过 | 验收第 5 条要求 `engine/tests/test_tools.py` 守卫测试 + `unittest` 全绿 |
| 隔离与顺序（AGENTS.md 规约二） | 通过 | 状态注明「已复制 n19 产物，合并须按 n19 → n20 顺序」 |

**Standards 结论：无 P0/P1。**

## 二、Spec 轴（工单设计完备性）

| 验收判据 | 设计可验证性 | 结论 | 证据 |
|---|---|---|---|
| 1. 反馈指标（判定率 / 闭环率 / 补缺周期 / 引用次数） | 指标清单 + 不可采集标注 | 覆盖 | 与 `decision_metrics` 既有收敛率 / 判定率口径衔接；不可计算项显式 `None` |
| 2. 维护工作流「反馈汇总」步骤 | 工作流步骤 + 产物路径可验 | 覆盖 | 产物落 `engine/report-audits/toolchain/`；观察 2 涉入库口径 |
| 3. 提示词「反馈回流」节 + 需求变更清单 | `prompt_check.py` 可验 | 覆盖（附 P2） | 无变更时显式写「本期无需求变更」；验收未含 prompt_check，见观察 1 |
| 4. `decision_log --check` 关联需求 | 未关联 rc=2，`validate.yml` 既有步骤生效 | 覆盖 | 告警不阻断，符合退出码契约 |
| 5. 守卫测试 + `unittest` | unittest 断言 | 覆盖 | `test_tools.py` 增关联校验断言 |

**Spec 结论：无 P0/P1。**

## 三、设计观察（P2，不阻断）

1. **验收门禁与改动范围不对称**：验收第 5 条仅要求 `unittest` 全绿，未含 `prompt_check.py rc=0`，但工单改动 `00-decision-hub/prompts/business-config.md`；与 n19 第 5 条口径不一致，建议补齐。
2. **反馈汇总产物入库口径未说明**：`engine/report-audits/toolchain/requirements-matrix.md` 的入库 / 忽略口径未在工单说明，建议与 n25 的 `source-index.json` 入库口径一致处理，避免工作区噪声。

## 四、证据清单

- 工单：`docs/toolchain/tickets/n20-feedback-loop.md` §目标 / §验收判据 1–5 / §涉及文件 / §风险与依赖 / §证据。
- 规约：`docs/toolchain/TOOLCHAIN-DEV-SPEC.md` 第二节、第三节、第五节、第七节。
- 一致性核对（只读）：`engine/tools/decision_metrics.py`、`engine/tools/decision_log.py`、`.github/workflows/scheduled-maintenance.yml`、`00-decision-hub/prompts/business-config.md` 存在。
