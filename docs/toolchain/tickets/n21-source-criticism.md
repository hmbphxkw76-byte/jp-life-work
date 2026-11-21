# 工单 N21：· 信源批评升级（来源质量四维）（P1，组 B）

> **来源**：情报科学五框架分析（会话，2026-11-20）· 差距 G3（信源批评）
> **状态**：已入库
> **验收判据**：见下方「验收判据」节；完成后回填状态与证据。

---

· 信源批评升级（来源质量四维）（P1，组 B）

- **目标**：把来源评估从「来源分级」升级为「来源质量」——补齐**独立性、立场/利益、转述层级、三角验证（corroboration）**四个结构化维度，使关键结论的来源可信度可机读、可审计。
- **验收判据**：
  1. `engine/report_templates/registry-schema.md` v2 标准表增列：`来源类型`（一手/转引/转载）、`独立性`（独立/非独立/不明）、`转述层级`（1–3）；旧表不强制回填，新表必须。
  2. `engine/tools/source_check.py` 四元组扩为六元组（+ `relay_level` / `independence`），`source-index.json` 同步扩字段；`engine/tools/info_quality_check.py` 增列存在性与值域校验（P2）。
  3. `engine/report_templates/prompt-generic-base.md` 第四节来源分级表增「来源批评四问」（发布者与立场 / 一手性 / 独立性 / 可否三角验证）；至少 3 个主题 `prompts/business-config.md` 实例化。
  4. `engine/report_templates/l5-semantic-review.md` 与 `engine/tools/audit_check.py` 的 `L5_CHECKLIST` 增第 7 项「独」：关键结论是否多源互证，单源是否已标注。
  5. L5 证据 backfill：提供 `--backfill-l5` 或等价机制，21 份报告补录第 7 项；**backfill 前先出映射说明**，backfill 后 `l5_meta_check` rc=0。
  6. `unittest` 全绿；`validate.py` rc=0。
- **实施步骤**：① Schema 扩列与值域定义；② `source_check` / `source-index` 扩字段；③ `info_quality_check` 校验；④ 提示词「来源批评四问」；⑤ L5 清单与复核提示词增项；⑥ 出 backfill 映射说明并补录；⑦ 测试与回填。
- **涉及文件**：`engine/report_templates/registry-schema.md`、`engine/tools/source_check.py`、`engine/tools/info_quality_check.py`、`engine/report_templates/prompt-generic-base.md`、`engine/report_templates/l5-semantic-review.md`、`engine/tools/audit_check.py`、3 个主题 `prompts/business-config.md`、`engine/tests/test_tools.py`。
- **风险与依赖**：Schema 扩列触发登记册解析 / 工具 / 测试联动；L5 增项影响 21 份报告证据格式，**须先 backfill 再开启门禁**，否则 `l5_meta_check` 全量失败。转述层级依赖人工判定，先允许「不明」。
- **证据**：
  - Schema：`registry-schema.md` v1.2，v2 标准表 12 → 15 列（新增 `来源类型 / 独立性 / 转述层级`，新表必填、存量豁免）；新增 C-16 规则与 `REGISTRY_EXT_REQUIRED_FROM`。
  - 工具：`source_check.py` 四元组 → 六元组（+ `relay_level` / `independence`，含关键词初判，人工可覆盖），增 E6；`info_quality_check.py` 新增 `registry_ext_gaps()` / C-16（P2）；`audit_check.C_TO_LAYER` 增 C-16 → L3。
  - L5：`audit_check.L5_CHECKLIST` 六项 → 七项（新增「独」）；`l5-semantic-review.md` v1.1 同步；`validate_l5_evidence` 按清单长度自动校验。
  - 提示词：`prompt-generic-base.md` 第四节增「来源批评四问」；01 / 04 / 08 三个主题 `business-config.md` 实例化。
  - Backfill：新增第 7 项后 L5 覆盖率 0% → 以临时脚本为 21 份已审计报告追加「独」项（`result=uncertain`，basis 标注「程序化补录，非人工结论」），经 `--backfill-l5` 写入台账；补录后 `l5_meta_check` 覆盖率 100%、rc=0；`audit_pipeline --gate` 通过（台账 868 条，链完整）。
  - 测试：`test_source_check.py` 20 项 OK（新增六元组 / E6）；`test_cov_audit.py` 76 项 OK；`test_tools.py` 235 项 OK（新增 C-16）；`test_l5_meta_check.py` 12 项 OK；`validate.py` / `prompt_check.py` / ruff 全绿。
  - 文档：`docs/信息质量评估提示词体系.md` v1.6（C-16）、`docs/审计报告标准化管理体系.md` v1.8（L5 七项 / C-16）。
- **状态**：已入库（实施完成并合并推送至 `origin/main`；证据见上）。
