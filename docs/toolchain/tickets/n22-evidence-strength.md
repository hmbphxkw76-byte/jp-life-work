# 工单 N22：· 证据强度标定与合成规则（P1，组 B）

> **来源**：情报科学五框架分析（会话，2026-11-20）· 差距 G4（证据学）
> **状态**：待实施
> **验收判据**：见下方「验收判据」节；完成后回填状态与证据。

---

· 证据强度标定与合成规则（P1，组 B）

- **目标**：在既有「来源等级 × 时效 × 核验」之外增加**证据类型**维度与**合成规则**，使「结论强度 ≤ 证据强度」可程序化拦截，避免单源/弱证据推出强结论。
- **验收判据**：
  1. `engine/report_templates/confidence-grade-standard.md` 增「证据类型」维度（官方统计 / 政策原文 / 自算 / 推断 / 预测 / 转述），合成「证据强度码」（如 `S1·统计`、`B2·自算`、`C3·推断`）；增合成规则：单源结论须标「单源」；多源 corroboration 可升级；冲突来源降级并并列。
  2. `engine/tools/counterexample_scan.py` 在 `ABS/GEN/NOSRC` 之外增 `单源` 扫描：关键数字所在段落仅一个来源且无 corroboration 标注即命中；退出码契约不变（0/1/2）。
  3. `engine/tools/fact_card_check.py` 增卡片「corroboration 来源数」字段与校验（P2）。
  4. `engine/tools/audit_check.py` L4 增「证据强度 < 结论强度」扫描：结论句含绝对化措辞且证据码 ≥3 级 → 命中。
  5. `engine/report_templates/prompt-generic-base.md` 第三节「事实与推断分离」扩为「证据类型标注」；`engine/tests/test_tools.py` 增守卫测试；`unittest` 全绿。
- **实施步骤**：① 定义证据类型与强度码（与既有两位码并存，明确优先级：证据码为补充维度，不替换来源等级）；② 标准文档更新；③ `counterexample_scan` 增单源扫描；④ `fact_card_check` 增字段；⑤ `audit_check` L4 增强度匹配；⑥ 提示词更新；⑦ 测试与回填。
- **涉及文件**：`engine/report_templates/confidence-grade-standard.md`、`engine/tools/counterexample_scan.py`、`engine/tools/fact_card_check.py`、`engine/tools/audit_check.py`、`engine/report_templates/prompt-generic-base.md`、`engine/tests/test_tools.py`。
- **风险与依赖**：证据码与既有置信度两位码并存，需在标准中明确「来源等级 → 证据强度」的映射优先级；单源扫描可能误报（如官方唯一来源本身即权威），命中走人工裁定，不自动改结论。
- **证据**：
  - 标准：`confidence-grade-standard.md` v1.2——新增 §2.1 证据类型（官方统计 / 政策原文 / 自算 / 推断 / 预测 / 转述）、§2.2 证据强度码（分级码 + 类型）与合成规则（单源标注 / 多源互证 / 冲突降级 / 强度匹配）；`prompt-generic-base.md` 第 2 条同步。
  - 工具：`counterexample_scan.py` 增「单源」扫描（段落级：含数字的结论句 + 仅一个来源标记 + 无 corroboration 标注，`CLAIM_RE` 收紧避免误报）；`fact_card_check.py` 增 `corroboration` 来源数（可选第 6 字段 / 行内 `corroboration: N`）与 P2 校验；`audit_check.py` L4 增 `EVI-01`（绝对化措辞配 3 级证据码）。
  - 文档：`fact-card-standard.md` v1.1（corroboration 字段）；`engine/tools/README.md` v1.9。
  - 实测：`counterexample_scan` 15 份 / 28 条候选（rc=2，含新增单源）；`fact_card_check` 16 张卡片 / 16 条 P2（corroboration 未标注，已知缺口）；`audit_pipeline --gate` 通过；`l5_meta_check` 覆盖率 100% rc=0；`validate.py` rc=0。
  - 测试：`test_counterexample_scan.py` 10 项 OK（新增单源 3 项）；`test_cov_audit.py` 76 项 OK；`test_tools.py` 237 项 OK（新增 EVI-01 / corroboration）；ruff 全绿。
- **状态**：已实施（未提交，位于 worktree `n22-evidence-strength`；已复制 n21 产物，合并须按 n25 → n21 → n22 顺序）。
