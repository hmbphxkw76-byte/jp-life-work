# 双轴评审：反例扫描「单源」判定收敛（counterexample-single-source）

> 工单：[tickets/fix-counterexample-single-source.md](../tickets/fix-counterexample-single-source.md)
> 评审日期：2026-11-24
> 评审对象：`engine/tools/counterexample_scan.py`、`engine/tests/test_counterexample_scan.py`、
> `engine/config/counterexample-adjudications.json`、`docs/反例与近义裁定清单-2026-11-24.md`、
> `docs/CI.md`、`docs/README.md`、`docs/cross-domain-expert-roles.md`、`engine/tools/README.md`、`engine/scripts/README.md`
> 规格：[specs/fix-counterexample-single-source.md](../specs/fix-counterexample-single-source.md)

## 一、Standards 轴（规约符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| 复用既有判定内核、不新造规则 | 通过 | 仅收紧 `_single_source_sentences()`，未动 ABS / GEN / NOSRC 与 `absolute_hits` |
| 测试先行 | 通过 | 新增 7 条守卫先红（5 条失败、2 条防过度排除用例即绿）后绿 |
| 交付可核验、数字锁定 | 通过 | 测试计数 1211 → 1218 同步 5 处 |
| 过程留痕 | 通过 | ticket / spec / 本评审齐全；证据文档入库 |
| 不掩盖失败 | 通过 | 见第三节「实施过程偏差」 |

## 二、Spec 轴（规格 ↔ 实现映射）

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 内部指针不参与判定 | `_internal_source_only()` + `INTERNAL_TOKENS` / `SECTION_PTR_RE` / `GENERIC_WORDS` / `NUM_CHARS_RE` | 39 → 16，24 条内部自指与 1 条疑问句退出 |
| 疑问句排除 | 句末 `？`/`?` 跳过 | `test_single_source_question_not_hit` |
| 「（建议）」建议类排除 | `ADVICE_MARK not in sent` | `test_single_source_advice_not_hit` |
| 防过度排除 | 混合「内部指针 + 外部机构实证」仍命中；真实外部单一来源仍命中 | `test_single_source_mixed_internal_external_still_hit` / `test_single_source_external_still_hit` |
| 残余逐条裁定 | 16 条各带理由（12 类原因），无笼统整批 | `counterexample-adjudications.json` 38 条；证据文档 |
| 验收 3 | `counterexample_scan.py` 退出码 0；`local_ci` counterexample 转 pass | 见检查单 §十二 |

## 三、实施过程偏差（如实记录）

1. **首版排除算法过度宽松**：`GENERIC_TAIL_RE` 含 `.?` 通配导致恒真，内部指针判定失效——由新用例暴露后改为
   「剔除内部字样 / 泛化词 / 数字章节后无实质残留」的算法。
2. **常量命名笔误**：`ADVvice_MARK` 已修正为 `ADVICE_MARK`。
3. **正则漏配**：`详见第八节` 这类省略「第」的章节指针未被识别，`SECTION_PTR_RE` 改为 `第?`；
   `本报告第四 / 五 / 七节` 残留「第」字未清，`NUM_CHARS_RE` 补入「第」。
4. **裁定清单两次写坏**：先用旧扫描结果生成，产生 4 条孤儿条目；随后用的是**已裁定状态**的报告，
   把当时仅存的候选全部误判为孤儿、清单被削回 22 条。最终改为「恢复基线配置 → 重跑扫描取候选 → 生成条目」，
   得到 22 + 16 = 38 条且零孤儿。两次偏差均在本评审留痕，未静默修正。

## 四、残余风险 / 遗留

- **排除规则基于关键词表**：`INTERNAL_TOKENS` / `GENERIC_WORDS` 为受控白名单，若日后报告出现新的内部指针写法
  未被覆盖，会退回「单源」候选——届时应扩白名单而非放宽判定（新增候选默认不豁免，安全侧倾）。
- **16 条裁定中多数为「元表述 / 状态说明 / 操作建议」**：这与「单源 = 经验论断缺 corroboration」的原定义
  不同，属**判定口径的显式迁移**，已写入证据文档与配置 `comment`；如后续要求更严，可重开一类「自指引用」规则。
- **`metrics` 告警未处理**：仍卡在五问个人决策，不在本任务范围。
