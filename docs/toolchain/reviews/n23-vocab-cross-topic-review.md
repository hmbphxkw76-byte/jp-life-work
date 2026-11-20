# 双轴评审：受控词表跨主题同概念对齐（n23-vocab-cross-topic）

> **工单**：n23-vocab-cross-topic（docs/toolchain/tickets/n23-vocab-cross-topic.md）
> **评审日期**：2026-11-20
> **评审口径**：Standards（TOOLCHAIN-DEV-SPEC / 仓库规范符合性）+ Spec（工单设计完备性：目标 / 验收判据 / 涉及文件 / 风险与依赖）
> **证据来源**：工单设计文本 + 规约条款 + 涉及文件存在性核对；**不核验实施产物**
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**

## 一、Standards 轴（规约符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 命名规范（§四） | 通过 | slug `n23-vocab-cross-topic` kebab-case，无 `YYYY-MM-` 前缀 |
| 适用边界（§二） | 通过（附 P2） | 主体 `engine/vocabulary/config/topics.json`、`engine/vocabulary/script/vocab_tool.py`、`engine/tools/info_quality_check.py`、`.github/workflows/validate.yml`（工具链 + 配置 + CI）；另涉各主题 `prompts/prompt-p1-term-alignment.md`（内容层），验收第 5 条未含 `prompt_check.py`，见观察 1 |
| 退出码契约（§五） | 通过 | `cross-check` 0=通过 / 1=错误 / 2=警告；引用完整性缺失 rc=1，同定义异名 / 未登记 rc=2；C-15 仅告警不阻断 |
| 异常不静默（§五） | 通过 | 映射缺失时 `cross-check` 告警而非阻断；不自动合并词条 |
| 单一事实源（§六） | 通过 | `info_quality_check` C-15 复用 `cross_check_gaps()` 单一事实源；`topics.json` 顶层键由 `topic-add` 保留 |
| 测试（S3） | 通过 | 验收第 4 条 `engine/tests/test_tools.py` 守卫测试 |
| 隔离与顺序（AGENTS.md 规约二） | 通过 | 独立工单（批 3），无跨工单依赖 |

**Standards 结论：无 P0/P1。**

## 二、Spec 轴（工单设计完备性）

| 验收判据 | 设计可验证性 | 结论 | 证据 |
|---|---|---|---|
| 1. `topics.json` 增 `concept_map` | 映射字段 + 试点主题 | 覆盖 | `concept_id → 各主题词条 ID 列表`；先覆盖 01 / 04 / 08 / 16 等高频主题 |
| 2. `vocab_tool cross-check` | 子命令 + 退出码 0/1/2 | 覆盖 | 检测同定义 / 同别名 / 同概念异名 |
| 3. `info_quality_check` C-15 | P2 仅告警 | 覆盖 | 复用 `cross_check_gaps()` |
| 4. `validate.yml` 增步骤 + 守卫测试 | 工作流 + unittest | 覆盖 | 词库校验接入 `cross-check` |
| 5. 各主题提示词增步骤 + `unittest` | `prompt_check.py` / unittest | 覆盖（附 P2） | 未含 prompt_check，见观察 1 |

**Spec 结论：无 P0/P1。**

## 三、设计观察（P2，不阻断）

1. **验收门禁与改动范围不对称**：验收第 5 条未含 `prompt_check.py rc=0`，但改动 21 个主题 `prompt-p1-term-alignment.md`；与 n19 第 5 条口径不一致，建议补齐。
2. **映射维护节奏未定义**：工单已声明「先只读检测、后人工登记映射」，但未定义登记节奏 / 复核人；建议约定新增词条触发 C-15 告警后的季度复核。

## 四、证据清单

- 工单：`docs/toolchain/tickets/n23-vocab-cross-topic.md` §目标 / §验收判据 1–5 / §涉及文件 / §风险与依赖 / §证据。
- 规约：`docs/toolchain/TOOLCHAIN-DEV-SPEC.md` 第二节、第三节、第五节、第七节。
- 一致性核对（只读）：`engine/vocabulary/config/topics.json`、`engine/vocabulary/script/vocab_tool.py`、`engine/tools/info_quality_check.py`、`.github/workflows/validate.yml`、`01-ssw-driver/prompts/prompt-p1-term-alignment.md`、`08-visa-immigration/prompts/prompt-p1-term-alignment.md` 存在。
