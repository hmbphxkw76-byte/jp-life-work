# 双轴评审：信源批评升级（来源质量四维）（n21-source-criticism）

> **工单**：n21-source-criticism（docs/toolchain/tickets/n21-source-criticism.md）
> **评审日期**：2026-11-20
> **评审口径**：Standards（TOOLCHAIN-DEV-SPEC / 仓库规范符合性）+ Spec（工单设计完备性：目标 / 验收判据 / 涉及文件 / 风险与依赖）
> **证据来源**：工单设计文本 + 规约条款 + 涉及文件存在性核对；**不核验实施产物**
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**

## 一、Standards 轴（规约符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 命名规范（§四） | 通过 | slug `n21-source-criticism` kebab-case，无 `YYYY-MM-` 前缀 |
| 适用边界（§二） | 通过（附 P2） | 主体 `engine/report_templates/registry-schema.md`、`engine/tools/source_check.py`、`engine/tools/info_quality_check.py`、`engine/report_templates/prompt-generic-base.md`、`engine/report_templates/l5-semantic-review.md`、`engine/tools/audit_check.py`（工具链 + 模板）；另涉 3 主题 `prompts/business-config.md`（内容层），验收第 6 条未含 `prompt_check.py`，见观察 2 |
| 退出码契约（§五） | 通过 | `source_check` 六元组沿用既有退出码；`info_quality_check` C-16 标 P2；未改变 0/1/2 语义 |
| 异常不静默（§五） | 通过 | 转述层级先允许「不明」；backfill 前先出映射说明；单源标注不自动改结论 |
| 单一事实源（§六） | 通过 | Schema 扩列单一事实源 `registry-schema.md`；backfill 走 `--backfill-l5` 统一入口 |
| 测试（S3） | 通过 | 验收第 6 条 `unittest` 全绿 + `validate.py` rc=0 |
| 隔离与顺序（AGENTS.md 规约二） | 通过 | 状态注明「已复制 n25 产物，合并须按 n25 → n21 顺序」 |

**Standards 结论：无 P0/P1。**

## 二、Spec 轴（工单设计完备性）

| 验收判据 | 设计可验证性 | 结论 | 证据 |
|---|---|---|---|
| 1. Schema v2 增列来源类型 / 独立性 / 转述层级 | 列清单 + 值域明确 | 覆盖 | 旧表不强制回填、新表必须；`REGISTRY_EXT_REQUIRED_FROM` 时间门控 |
| 2. `source_check` 四元组 → 六元组 | 字段 + `source-index.json` 同步 | 覆盖 | + `relay_level` / `independence`；`info_quality_check` 列存在性 / 值域（P2） |
| 3. 「来源批评四问」提示词 + 3 主题实例化 | `prompt_check.py` 可验 | 覆盖（附 P2） | 涉及文件未列具体主题，证据列 01 / 04 / 08，见观察 1 |
| 4. L5 清单增第 7 项「独」 | `l5-semantic-review.md` + `audit_check.L5_CHECKLIST` | 覆盖 | 两处同步，清单长度驱动校验 |
| 5. L5 backfill + `l5_meta_check` rc=0 | 命令 + 覆盖率可验 | 覆盖 | 风险声明「先 backfill 再开启门禁」，避免全量失败 |
| 6. `unittest` + `validate.py` | 命令退出码 | 覆盖 | rc=0 |

**Spec 结论：无 P0/P1。**

## 三、设计观察（P2，不阻断）

1. **涉及文件未列具体主题**：`涉及文件` 写「3 个主题 `prompts/business-config.md`」，`证据` 列 01 / 04 / 08；建议工单补列具体主题以便核验。
2. **验收门禁与改动范围不对称**：验收第 6 条仅要求 `unittest` + `validate.py`，未含 `prompt_check.py rc=0`，但改动 3 个主题 `business-config.md`；与 n19 第 5 条口径不一致，建议补齐。

## 四、证据清单

- 工单：`docs/toolchain/tickets/n21-source-criticism.md` §目标 / §验收判据 1–6 / §涉及文件 / §风险与依赖 / §证据。
- 规约：`docs/toolchain/TOOLCHAIN-DEV-SPEC.md` 第二节、第三节、第五节、第七节。
- 一致性核对（只读）：`engine/report_templates/registry-schema.md`、`engine/report_templates/prompt-generic-base.md`、`engine/report_templates/l5-semantic-review.md`、`engine/tools/source_check.py`、`engine/tools/info_quality_check.py`、`engine/tools/audit_check.py`、`01-ssw-driver/prompts/business-config.md`、`04-industry-logistics/prompts/business-config.md`、`08-visa-immigration/prompts/business-config.md` 存在。
