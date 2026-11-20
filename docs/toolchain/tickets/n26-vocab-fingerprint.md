# 工单 N26：· 词表变更审计指纹（P2，组 D）

> **来源**：情报科学五框架分析（会话，2026-11-20）· 差距 G8（受控词表 / 证据学）
> **状态**：待实施
> **验收判据**：见下方「验收判据」节；完成后回填状态与证据。

---

· 词表变更审计指纹（P2，组 D）

- **目标**：为词库变更补上审计指纹（对齐报告侧的 SHA-256 哈希链），使「词库变更 ↔ 提示词同步 ↔ 报告口径」跨层一致性可检测。
- **验收判据**：
  1. `.github/workflows/audit-gate.yml` 增词库哈希校验步骤：词库导出哈希变更而 `sync_vocab` 未同步提示词 → 告警或阻断（rc=2/1）。
  2. `engine/tools/audit_registry.py` 或 `engine/tools/decision_metrics.py` 登记 `vocab_hash`，纳入跨层一致性校验。
  3. `engine/tests/test_tools.py` 增守卫测试；`unittest` 全绿。
- **实施步骤**：① 确定词库哈希计算口径（基于 `terms.md` 规范化内容，排除时间戳）；② 接入 `audit-gate.yml`；③ 登记 `vocab_hash`；④ 守卫测试；⑤ 回填。
- **涉及文件**：`.github/workflows/audit-gate.yml`、`engine/tools/audit_registry.py`（或 `decision_metrics.py`）、`engine/tests/test_tools.py`。
- **风险与依赖**：词库导出产物若当前在 `.gitignore` 内，需改为入库或改用以 `terms.md` 为基准的哈希口径；哈希须确定性（不含 mtime）。
- **证据**：
  - 工具：`vocab_tool.py` 增 `vocab_hash(cfg)`（纯函数，词汇表小节 SHA-256，确定性）+ `vocab-hash` 命令（打印 / `--check` / `--write`）；基线 `engine/vocabulary/config/vocab-fingerprint.json`（`22519aa4807b…`，20 主题 / 1612 词条）。
  - 门禁：`audit-gate.yml` 增“词表指纹校验（vocab-hash --check）”步骤（失配 rc=2 告警，提示 sync_vocab + 刷新基线）。
  - 跨层：`decision_metrics.collect()` 增 `vocab_hash` 字段。
  - 实测：`vocab-hash --check` 匹配 rc=0；变更词条后失配 rc=2（测试覆盖）。
  - 测试：`test_tools.py` 235 项 OK（新增 `test_vocab_hash_and_check`）；`test_decision_metrics.py` 10 项 OK（新增 vocab_hash 字段）；`validate.py` / ruff 全绿。
  - 文档：`engine/vocabulary/README.md` S7。
- **状态**：已实施（未提交，位于 worktree `n26-vocab-fingerprint`）。
