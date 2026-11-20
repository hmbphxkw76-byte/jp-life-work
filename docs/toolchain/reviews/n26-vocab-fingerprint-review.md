# 双轴评审：词表变更审计指纹（n26-vocab-fingerprint）

> **工单**：n26-vocab-fingerprint（docs/toolchain/tickets/n26-vocab-fingerprint.md）
> **评审日期**：2026-11-20
> **评审口径**：Standards（TOOLCHAIN-DEV-SPEC / 仓库规范符合性）+ Spec（工单设计完备性：目标 / 验收判据 / 涉及文件 / 风险与依赖）
> **证据来源**：工单设计文本 + 规约条款 + 涉及文件存在性核对；**不核验实施产物**
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**

## 一、Standards 轴（规约符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 命名规范（§四） | 通过 | slug `n26-vocab-fingerprint` kebab-case，无 `YYYY-MM-` 前缀 |
| 适用边界（§二） | 通过 | 主体 `.github/workflows/audit-gate.yml`、`engine/tools/audit_registry.py`（或 `decision_metrics.py`）、`engine/tests/test_tools.py`（工具链 + CI + 测试） |
| 退出码契约（§五） | 通过 | `audit-gate` 哈希失配 rc=2 告警（P2 观察期口径），提示 `sync_vocab` + 刷新基线 |
| 异常不静默（§五） | 通过 | 失配给出修复指引；不静默吞掉 |
| 单一事实源（§六） | 通过 | 哈希口径基于 `terms.md` 规范化内容，确定性（不含 mtime）；基线 `engine/vocabulary/config/vocab-fingerprint.json` |
| 测试（S3） | 通过 | 验收第 3 条守卫测试 + `unittest` 全绿 |
| 隔离与顺序（AGENTS.md 规约二） | 通过 | 独立工单（批 3），无跨工单依赖 |

**Standards 结论：无 P0/P1。**

## 二、Spec 轴（工单设计完备性）

| 验收判据 | 设计可验证性 | 结论 | 证据 |
|---|---|---|---|
| 1. `audit-gate.yml` 词库哈希校验 | 工作流步骤 + rc=2/1 | 覆盖 | 词库导出哈希变更而 `sync_vocab` 未同步提示词 → 告警或阻断 |
| 2. 登记 `vocab_hash` | `audit_registry.py` 或 `decision_metrics.py` | 覆盖 | 证据落在 `decision_metrics.collect()`，工单「或」允许；观察 1 涉涉及文件补列 |
| 3. 守卫测试 + `unittest` | unittest 断言 | 覆盖 | `test_tools.py` 增 `test_vocab_hash_and_check` |

**Spec 结论：无 P0/P1。**

## 三、设计观察（P2，不阻断）

1. **涉及文件与实现范围不一致**：`涉及文件` 未列 `engine/vocabulary/script/vocab_tool.py`，但 `证据` 在该文件实现 `vocab_hash()` 与 `vocab-hash` 命令；建议补列，保持涉及文件与实现范围一致。
2. **告警 / 阻断口径需在工单固化**：验收第 1 条允许「告警或阻断（rc=2/1）」，证据选 rc=2（P2 观察期）；建议工单固化所选口径，避免实施与门禁预期漂移。

## 四、证据清单

- 工单：`docs/toolchain/tickets/n26-vocab-fingerprint.md` §目标 / §验收判据 1–3 / §涉及文件 / §风险与依赖 / §证据。
- 规约：`docs/toolchain/TOOLCHAIN-DEV-SPEC.md` 第二节、第三节、第五节、第七节。
- 一致性核对（只读）：`.github/workflows/audit-gate.yml`、`engine/tools/audit_registry.py`、`engine/tools/decision_metrics.py`、`engine/vocabulary/script/vocab_tool.py` 存在。
