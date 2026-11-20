# 双轴评审：证据强度标定与合成规则（n22-evidence-strength）

> **工单**：n22-evidence-strength（docs/toolchain/tickets/n22-evidence-strength.md）
> **评审日期**：2026-11-20
> **评审口径**：Standards（TOOLCHAIN-DEV-SPEC / 仓库规范符合性）+ Spec（工单设计完备性：目标 / 验收判据 / 涉及文件 / 风险与依赖）
> **证据来源**：工单设计文本 + 规约条款 + 涉及文件存在性核对；**不核验实施产物**
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**

## 一、Standards 轴（规约符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 命名规范（§四） | 通过 | slug `n22-evidence-strength` kebab-case，无 `YYYY-MM-` 前缀 |
| 适用边界（§二） | 通过（附 P2） | 主体 `engine/report_templates/confidence-grade-standard.md`、`engine/tools/counterexample_scan.py`、`engine/tools/fact_card_check.py`、`engine/tools/audit_check.py`、`engine/report_templates/prompt-generic-base.md`（工具链 + 模板）；验收第 5 条含提示词更新但未含 `prompt_check.py`，见观察 1 |
| 退出码契约（§五） | 通过 | `counterexample_scan` 退出码契约不变（0/1/2）；新增单源扫描不改语义 |
| 异常不静默（§五） | 通过 | 单源扫描可能误报，命中走人工裁定，不自动改结论 |
| 单一事实源（§六） | 通过 | 证据类型 / 强度码 / 合成规则写入 `confidence-grade-standard.md`；`fact-card-standard.md` 同步 |
| 测试（S3） | 通过 | 验收第 5 条守卫测试 + `unittest` 全绿 |
| 隔离与顺序（AGENTS.md 规约二） | 通过 | 状态注明「已复制 n21 产物，合并须按 n25 → n21 → n22 顺序」 |

**Standards 结论：无 P0/P1。**

## 二、Spec 轴（工单设计完备性）

| 验收判据 | 设计可验证性 | 结论 | 证据 |
|---|---|---|---|
| 1. 证据类型维度 + 证据强度码 + 合成规则 | 标准文档条目 | 覆盖 | 合成规则含单源标注 / 多源升级 / 冲突降级；明确「证据码为补充维度，不替换来源等级」 |
| 2. `counterexample_scan` 增单源扫描 | 扫描命中 + 退出码不变 | 覆盖 | 段落级判定（数字结论句 + 单来源 + 无 corroboration） |
| 3. `fact_card_check` 增 corroboration 来源数 | 字段 + P2 校验 | 覆盖 | 可选第 6 字段 / 行内 `corroboration: N` |
| 4. `audit_check` L4 增强度匹配 | `EVI-01` 规则 | 覆盖 | 绝对化措辞 + 证据码 ≥3 级命中；阈值口径见观察 2 |
| 5. 提示词更新 + 守卫测试 | `prompt_check.py` / unittest | 覆盖（附 P2） | 未含 prompt_check，见观察 1 |

**Spec 结论：无 P0/P1。**

## 三、设计观察（P2，不阻断）

1. **验收门禁与改动范围不对称**：验收第 5 条未含 `prompt_check.py rc=0`，但改动 `engine/report_templates/prompt-generic-base.md`；与 n19 第 5 条口径不一致，建议补齐。
2. **阈值口径需固化**：L4 `EVI-01` 的「证据码 ≥3 级」阈值应在 `confidence-grade-standard.md` 与分级码定义一致，避免实施与门禁预期漂移。

## 四、证据清单

- 工单：`docs/toolchain/tickets/n22-evidence-strength.md` §目标 / §验收判据 1–5 / §涉及文件 / §风险与依赖 / §证据。
- 规约：`docs/toolchain/TOOLCHAIN-DEV-SPEC.md` 第二节、第三节、第五节、第七节。
- 一致性核对（只读）：`engine/report_templates/confidence-grade-standard.md`、`engine/report_templates/prompt-generic-base.md`、`engine/tools/counterexample_scan.py`、`engine/tools/fact_card_check.py`、`engine/tools/audit_check.py` 存在。
