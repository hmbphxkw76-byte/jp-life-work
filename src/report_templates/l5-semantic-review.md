# L5 语义复核提示词（AuditGuard 复核环节）

> **用途**：`reviewer_l2` 在审计复核环节（`audit_pipeline.py --review --stage re_review`）执行。
> 对单份报告逐项确认六个语义项，输出固定 JSON 作为 `--evidence` 写入审计台账。
> **上位依据**：`docs/审计报告标准化管理体系.md` 第 4 节 L5 层、`docs/信息质量评估提示词体系.md` 维度二/三。

---

## 一、复核对象

- 报告 md 源稿与其 HTML 交付物；
- 报告引用的登记册（`data/*_indicator_registry.md`）与手册（`handbook/`）相关段落；
- 来源清单与关键数字的对应关系。

## 二、六项复核项（逐项给出结论）

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

> 注：码值由 `audit_pipeline.validate_l5_evidence()` 依据 `audit_check.L5_CHECKLIST` 校验，
> 写入完整句子或其它名称会被判为无效证据。

## 三、输出格式（严格 JSON，不得输出其它内容）

```json
{
  "report": "01-ssw-driver/reports/2026-11-ssw-driver.md",
  "items": [
    {"item": "结", "result": "yes", "basis": "结论与依据匹配：核心结论 3 条均附来源与推理链"},
    {"item": "表", "result": "yes", "basis": "表述与来源一致：抽查 10 条与原文一致"},
    {"item": "关", "result": "uncertain", "basis": "时效合格：9 月分数据已最新，10 月分未发布，需下月复核"},
    {"item": "是", "result": "yes", "basis": "无以偏概全/过度推断：推断项均已标注「推断」"},
    {"item": "口", "result": "yes", "basis": "口径并列清晰：运賃/工资/倒産口径分别标注不可混用"},
    {"item": "跨", "result": "yes", "basis": "跨主题引用准确：引用 04/07/08 均为主责方"}
  ]
}
```

- `result` 仅取 `yes` / `no` / `uncertain`；
- `no` 或 `uncertain` 必须给出 `basis` 说明（否则视为无效证据）；
- 六项缺一不可。

## 四、执行约定

- 只复核、不修改报告内容；发现问题在 `basis` 中说明，并在审计结论中记 `fail`。
- 证据将写入台账 `evidence` 字段，供终审与门禁校验；缺证据的复核 `pass` 会被系统拒绝。
