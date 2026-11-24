# 规格：反例扫描「单源」判定收敛（counterexample-single-source）

> 任务 slug：`fix-counterexample-single-source`
> 版本：v1.0（2026-11-24）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)

## 一、动机

`local_ci` 的 `counterexample` 长期 warn：`engine/report-audits/audit/counterexample-report.json`
`total=39`，39 条全为 `单源`，且裁定清单明确未登记（「保持可见、逐条补第二来源后再消解」）。

逐条核查（2026-11-24，只读）显示这 39 条并非同类：

| 类别 | 条数 | 说明 |
|---|---|---|
| 内部自指（来源括注指向本报告章节 / 主题登记册 / business-config / 来源清单 / 基线报告） | 24 | 段内不含任何外部一手来源，「单源」语义不成立 |
| 外部机构直引 | 14 | ISA / 国交省 / 経産省 / 厚生劳动省 / JFT-Basic 実行委員会 / 東京商工リサーチ 等 |
| 无来源括注 | 1 | 疑问句（待答问题清单） |

根因在 `counterexample_scan.py::_single_source_sentences()`：仅按「段落含数字 + 恰好 1 个来源标记 +
无 corroboration 标注 + 句含结论性措辞」判定，**不区分该来源标记是外部一手来源还是报告内部指针**。
内部指针类段落的来源充足性实际由 `source-check` / `info-quality` 两道门禁覆盖，本项检查重复且误报。

## 二、目标与非目标

**目标**：① 让「单源」判定只作用于真正的外部来源；② 疑问句与「（建议）」类操作建议不作为候选；
③ 残余条目逐条人工裁定并登记，`total` 归零、`counterexample` 告警消除。

**非目标**：不改 ABS / GEN / NOSRC 既有规则；不改报告正文语义与结论；不新增来源数据；
不改动裁定清单既有 22 条的 verdict / reason。

## 三、接口设计

- `engine/tools/counterexample_scan.py`
  - 新增 `SRC_TAIL_RE = re.compile(r"来源[：:]\s*([^）)]*)")`
  - 新增 `INTERNAL_HEAD_RE = re.compile(r"^(?:本报告|本主题(?:登记册)?|主题登记册|business-config|来源清单|基线报告)")`
  - `_single_source_sentences()`：
    - 若段落**所有** `来源[：:]` 尾部均命中 `INTERNAL_HEAD_RE` → 跳过该段（内部指针不算外部来源）；
    - 跳过句末为 `？`/`?` 的句子；
    - 跳过含 `（建议）` 的操作建议句。
- 测试：`engine/tests/test_counterexample_scan.py` 增补对应用例。
- 裁定：`engine/config/counterexample-adjudications.json` 追加条目（`verdict` / `reason` / `evidence`），
  证据文档 `docs/反例与近义裁定清单-2026-11-24.md`。

## 四、验收标准

1. 新用例先红（旧实现无排除规则）后绿；既有用例不回归。
2. 重跑 `counterexample_scan.py` 后 `total` 由 39 显著下降；残余条目逐条在裁定清单中可查。
3. `counterexample_scan.py`（退出码 0）与 `local_ci` 的 `counterexample` 检查转为 pass。
4. 测试计数变化同步锁定文档；走任务分支 + PR + 门禁 SUCCESS 后合并。

## 五、边界与约束

- 内部指针白名单仅限规格列出的 6 类字样；出现任何真实外部机构名一律不排除。
- 残余条目的裁定必须逐条给理由与证据，不得整批「保留」了事；无法判定的显式标注待办。
