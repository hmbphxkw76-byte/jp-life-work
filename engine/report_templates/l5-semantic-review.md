# L5 语义复核提示词（AuditGuard 复核环节）

> **用途**：`reviewer_l2` 在审计复核环节（`audit_pipeline.py --review --stage re_review`）执行。
> 对单份报告逐项确认七个语义项，输出固定 JSON 作为 `--evidence` 写入审计台账。
> **上位依据**：`docs/审计报告标准化管理体系.md` 第 4 节 L5 层、`docs/信息质量评估提示词体系.md` 维度二/三。

---

## 一、复核对象

- 报告 md 源稿与其 HTML 交付物；
- 报告引用的登记册（`data/*_indicator_registry.md`）与手册（`handbook/`）相关段落；
- 来源清单与关键数字的对应关系。

## 二、七项复核项（逐项给出结论）

`item` 字段**必须**取 `audit_check.L5_CHECKLIST` 对应项的**首字码**（下表「码」列），顺序固定、缺一不可；
完整复核项原文见「复核项」列，`basis` 中可用完整表述。

| 码 | 复核项 |
|---|---|
| `结` | 结论与依据是否匹配（关键结论有「事实→推理→结论」链） |
| `表` | 表述是否与来源原文含义一致（无夸大 / 曲解） |
| `关` | 关键信息是否在时效内、未被更新版本取代 |
| `是` | 是否存在以偏概全 / 过度推断 / 绝对化表述 |
| `口` | 口径并列是否清晰、未合并未取均值 |
| `跨` | 跨主题引用是否准确、无归属错误 |
| `独` | 关键结论是否多源互证、单源是否已标注（来源独立性与三角验证） |

> 注：码值由 `audit_pipeline.validate_l5_evidence()` 依据 `audit_check.L5_CHECKLIST` 校验，
> 写入完整句子或其它名称会被判为无效证据。

## 三、输出格式（严格 JSON，不得输出其它内容）

**v2（2026-11-15 起，新格式）**：带版本号封套，`version` / `verdict` / `notes` 可选但推荐；
`items` 七项固定不变（n21 起新增「独」项）。`audit_pipeline.validate_l5_evidence()` 同时认可 v1（无 `version`，
仅 `report` + `items`）存量格式；n21 前已审计报告的「独」项由 `--backfill-l5` 补录。

```json
{
  "version": "2.0",
  "report": "01-ssw-driver/reports/2026-11-ssw-driver.md",
  "verdict": "pass",
  "items": [
    {"item": "结", "result": "yes", "basis": "结论与依据匹配：核心结论 3 条均附来源与推理链"},
    {"item": "表", "result": "yes", "basis": "表述与来源一致：抽查 10 条与原文一致"},
    {"item": "关", "result": "uncertain", "basis": "时效合格：9 月分数据已最新，10 月分未发布，需下月复核"},
    {"item": "是", "result": "yes", "basis": "无以偏概全/过度推断：推断项均已标注「推断」"},
    {"item": "口", "result": "yes", "basis": "口径并列清晰：运賃/工资/倒産口径分别标注不可混用"},
    {"item": "跨", "result": "yes", "basis": "跨主题引用准确：引用 04/07/08 均为主责方"},
    {"item": "独", "result": "yes", "basis": "关键结论多源互证：核心数字均≥2 独立来源；单源项已标注"}
  ],
  "notes": "30–60 字复核说明"
}
```

- `version` 若填写须为 `"2.0"`；`verdict` 仅取 `pass` / `fail`；
- `result` 仅取 `yes` / `no` / `uncertain`；
- `no` 或 `uncertain` 必须给出 `basis` 说明；
- 七项缺一不可。

## 四、执行约定

- 只复核、不修改报告内容；发现问题在 `basis` 中说明，并在审计结论中记 `fail`。
- 证据将写入台账 `evidence` 字段，供终审与门禁校验；缺证据的复核 `pass` 会被系统拒绝。
- **存量补核**：已审计但缺证据的报告，由 `audit_pipeline.py --backfill-l5 --report <路径> --evidence <JSON>`
  一次性补录（v2 格式），台账追加 `l5_backfill` 事件，状态与指纹不变。


## 五、版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-17 | 初始版本 | L5 语义复核六项清单（数据语义忠实性 / 来源忠实性 / 结论准确 / 语境提示 / 价值中立 / 工程冗余），与 audit_check.L5_CHECKLIST 同口径 |
| v1.1 | 2026-11-20 | 信源批评（n21） | 六项 → 七项，新增「独」（关键结论多源互证 / 单源标注），与 `audit_check.L5_CHECKLIST` 同口径 |
