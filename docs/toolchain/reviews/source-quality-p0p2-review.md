# 来源质量 P0-P2 修复 · 双轴评审（source-quality-p0p2，2026-11-22）

> **范围**：`task/quality-p0p2-fix-6b916f70` worktree（`D:\文档\GitHub\jp-life-work\.worktrees\quality-p0p2-fix`）。
> **基线**：`origin/main` = `f756b7c`。
> **触发**：本轮质量评估（软件质量 A- / 信息真实性 B+）确认的 P0–P2 八项。
> **口径**：只审本任务范围；来源判定单一事实源为 `engine/tools/source_normalize.py` 与 `engine/config/source-policy.json`；不编造 URL / 数值。
> **结论**：**Standards 无 P0/P1；Spec 八项全部落地**。残留：7 条日本官方中文页待回溯日文原文（已标注 + 告警，未编造替代 URL）。

---

## 一、改动清单

| 类别 | 文件 | 改动 |
|---|---|---|
| 工具 | `engine/tools/source_normalize.py` | 新增受控分组词表 `GROUP_VOCAB` / `normalize_group` / `classify_independence` / `authority_grade` / `detect_language` / `year_is_plausible`；`extract_year` 先剥离 URL 再取年 + 行尾年 / URL 日期路径回退 |
| 工具 | `engine/tools/source_check.py` | 复用分类层；条目增 `group_canonical` / `authority_grade` / `language`；新增 E7 年份合理性 / E8 中文页 / E9 分组词表 |
| 配置 | `engine/config/verified-content-policy.json` | 增 `mode_note`：豁免键仅 `--content-only` 生效 |
| 配置 | `engine/config/source-policy.json` | 增 `official_chinese_page_policy`：日本官方中文页口径 |
| CI | `.github/workflows/validate.yml`、`audit-gate.yml` | 注释与实际 `--all`（全层零容忍）语义对齐 |
| 测试 | `test_source_check.py` / `test_verified_content_gate.py` / `test_cov_audit.py` | +17 项（年份回归 / 词表 / 独立性 / 等级 / 语言 / 门禁模式 / 台账不可变） |
| 内容 | `01` / `08` / `11` / `18` 报告 | 来源小节中文页标注「建议回溯日文原文」；`01` 分组标题口径修正 |
| 派生 | `*/reports/*.html`、`source-index.json`、审计台账 / 状态 / 登记册 | 重新生成 / 重走审计 |
| 文档 | `docs/CI.md`、`docs/README.md`、`docs/cross-domain-expert-roles.md`、`engine/tools/README.md` | 测试计数 1110 → 1127 与版本记录对齐 |

---

## 二、轴一：Standards（规范符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| AGENTS.md 硬性规约二：分支 / worktree / 串行合并 | ✅ | 全程在 `.worktrees/quality-p0p2-fix`；合并走 `workflow_guard.py merge` |
| 工具链开发规约：TDD / 双轴评审 / 合并前检查单 | ✅ | 先补测试再实现；本评审为双轴评审 |
| 单一事实源 | ✅ | 分组 / 独立性 / 等级 / 语言 / 年份判定全部收敛于 `source_normalize.py`；政策收敛于 `source-policy.json` |
| 退出码约定 0/1/2 | ✅ | `source_check` 0/1/2；`verified_content_gate` 0/1/2；CI 显式判 1 阻断 |
| 来源语言政策 | ✅ | 未引入新中文来源；仅对既有日本官方中文页补标注；`source_language_gate --changed` 通过 |
| 跨平台 / 静态检查 | ✅ | 无 `shell=True`；`ruff` / `mypy` 通过 |
| 文档↔实现对齐守卫 | ✅ | `test_arch_guard` 通过（工具 48 / 测试 1127 / 步骤数 / 词条 1518） |
| 审计协议 | ✅ | 4 份改动报告重走 `md2html → auto_verify → 初审 → 复核（L5 证据）→ 终审 → badge`，21/21 `audited` |

**Standards 结论：无 P0 / P1。**

---

## 三、轴二：Spec（P0–P2 验收映射）

| 项 | 验收标准 | 实现 | 证据 |
|---|---|---|---|
| P0-1 | 年份不再被 URL 数字误判 | `extract_year` 先剥离 URL；4 条异常年份（1906/2086/2041）归零 | `source_check` 年份异常 0；`test_url_digits_not_year` |
| P0-2 | 门禁默认语义与 CI 一致 | 策略增 `mode_note`；CI 注释改为「全层零容忍，豁免仅 `--content-only`」；加模式回归 | `test_default_ignores_record_exemption` / `test_content_only_honors_record_exemption` |
| P1-3 | 31 条「独立性不明」闭环 | 扩充判定规则（平台 / 媒体 / 企业 / 自引 → 非独立；官方 / 机构 / 域名 → 独立） | 全库「不明」31 → **0** |
| P1-4 | 来源分组受控词表 | `GROUP_VOCAB` 六类；39 种异构标签收敛 | `source-index` 分组未纳入 0；`test_normalize_group_vocab` |
| P1-5 | 日本官方中文页口径 | 政策明确「可保留 + 标注 + 告警」；7 条标注 | `source_check` 中文页告警 7；`official_chinese_page_policy` |
| P2-6 | 年份合理性校验 | `year_is_plausible`（1990–2030）+ E7 告警 | `test_year_sanity_warns` / `test_year_is_plausible` |
| P2-7 | 媒体 / 企业来源权威等级 | `authority_grade` A/B/C/D/X 写入 `source-index` | 分组 → 等级映射；`test_authority_grade` |
| P2-8 | 台账不可变合并回归 | append-only / 重写检测 / 远端前缀续链 3 项 | `TestAuditImmutability` |

**Spec 结论：八项全部落地。**

---

## 四、残留与后续

1. **7 条日本官方中文页**（`01` 4 条、`08` / `11` / `18` 各 1 条）已标注并告警；**未编造日文替代 URL**，建议后续以浏览器核验后替换为日文原文页。
2. `source_check` 退出码 2（告警）为预期：中文页 7 条 + `00` 来源章节无 URL 条目。
3. `l5_meta_check` 告警「basis 平均字数 19.0 < 20」：本次复核 basis 偏简，后续复核说明宜更充分。
