# B 批对齐工单评审（b1–b9）

> **工单**：`b1-doc-drift-repair`、`b2-html-table-semantics`、`b3-vocab-convergence-map`、`b4-vocab-id-continuity`、`b5-review-gate-hardening`、`b6-unwired-tools-registry`、`b7-source-annotation-program`、`b8-prompt-semantic-alignment`、`b9-workspace-hygiene`
> **日期**：2026-11-19
> **评审对象**：B 批工单 + 实施任务 `b-docs` / `b-html` / `b-vocab` / `b-semverify`
> **结论**：**有条件通过**（P1 项已实施并验证；P2 项按计划 / 评估推进）

---

## 一、范围

- 工单：`docs/toolchain/tickets/b1-*.md` … `b9-*.md`（2026-11-19 审计立项）。
- 实施：文档漂移修补（B1）、HTML 表格语义（B2）、词库映射与 ID 豁免（B3/B4）、提示词语义对齐验证（B8）、不接线清单与计划文档（B5/B6/B7）。
- 不在本次范围：B5 转硬切换（时间门控）、B7 标注执行（长期）、B9 清理（并行会话门控）。

## 二、逐项结论

| 工单 | 优先级 | 状态 | 验证证据 |
|---|---|---|---|
| b1-doc-drift-repair | P1 | 已实施（b-docs） | CI.md v2.17→v2.22；报告周期体系 v1.0→v1.1；审计标准头部 v1.7 + 依据版本说明；tools README 978→1008 + 守卫；pending-verification 76→70 |
| b2-html-table-semantics | P1 | 已实施（b-html） | 294 表 / 1030 `<th>` 全含 `scope`；复杂表 caption 分支有测试；lint E 级校验；parity 21/21；validate 0 |
| b3-vocab-convergence-map | P2 | 已实施（b-vocab） | `verification-retention-map.json`：110/110 分类、1391/1391 条；复核记录 §7A.7 更新 |
| b4-vocab-id-continuity | P2 | 已实施（b-vocab） | `verify-exemptions.json` + `vocab_tool` 豁免；`verify` 0E0W |
| b5-review-gate-hardening | P2 | 计划（未切换） | `review-gate-hardening-plan.md`：转硬条件 C1–C4、评估日 2026-12-19 |
| b6-unwired-tools-registry | P2 | 已实施（b-docs） | CI.md §9 + tools README 清单（4 工具，含理由/复核日） |
| b7-source-annotation-program | P2 | 计划（未执行） | `docs/来源标注批次计划.md`：21 份基线 + 4 期分批 |
| b8-prompt-semantic-alignment | P2 | 已实施（b-semverify） | `prompt-semantic-alignment.md`：实质冲突 2 / 表述差异 11 / 设计内 7 |
| b9-workspace-hygiene | P2 | 待实施 | 受并行会话门控（`consulting-panel` active） |

## 三、发现

1. **实质冲突 2 项（B8 报告 C1/C2，未处理）**：
   - C1：`consumer-research` 命名三方不一致（`YYYY-MM` vs `YYYY-MM-DD`）。
   - C2：8 类事件/项目制产出命名共同偏离注册表 / 合规口径（`template-registry.md:125`）。
   - 建议：P1 处理命名口径，P2 处理脚手架编号断档 / 注册表计数。
2. **基线门禁失败（本评审修复）**：`test_every_ticket_has_review_or_exemption` 因 B1–B9 缺评审记录失败；本评审覆盖全部 9 个 slug。
3. **未接线工具**：`incremental_build` / `migrate_monthly_reports` / `skeleton_builder` / `report_diff` 已显式登记，消除「应接未接」歧义。
4. **词库口径差异**：工单记 1423/87，实测 1391/110；差异来源（升级 / 删除）已在复核记录注明，映射表按实测 100% 覆盖。

## 四、结论与后续

- 本批 P1 项（B1/B2）已实施并通过门禁；P2 项按「已实施 / 计划 / 门控」分类推进。
- 后续（非本批）：C1/C2 命名口径统一；B5 满 1 个月评估；B7 标注分期执行；B9 待并行会话释放后清理。
- 评审纪律：本评审基于实施任务的自报 + 主会话实跑门禁；未改动任何实现代码。
