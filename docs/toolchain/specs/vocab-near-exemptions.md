# 规格：词库近义「已裁定保留」清单（near-exempt）

> 任务 slug：`vocab-near-exemptions`
> 版本：v1.0（2026-11-23）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)

## 一、动机

`vocab_near_check.py` 只认「包含关系」，每轮报 218 对疑似并退出码 2。
2026-11-18 裁定清单已认定这些对「非同一对象、保留」，但扫描器无从得知，导致**每轮重复告警**
（告警疲劳）。工具需要从「全量报警」转为「增量检测器」。

## 二、目标与非目标

**目标**：新增 `engine/vocabulary/config/near-dup-exemptions.json`（已裁定保留的 `(topic, a, b)` 集合），
命中即不计为疑似；新增疑似默认不豁免。

**非目标**：不做自动合并；不改判定规则（仍只认包含关系）。

## 三、接口设计

- `load_exemptions(path=None) -> set[tuple[str,str,str]]`：文件缺失 / 损坏返回空集（不报错）；
- `filter_exempted(pairs, exempt) -> list[dict]`；
- `main()`：输出与报告增加 `exempted` 计数；仅对未豁免对退出码 2；
- 新增测试 4 项（缺失 / 损坏 / 精准剔除 / 全豁免时退出码 0）。

## 四、验收标准

1. 新测试先红后绿；
2. 实跑 `vocab_near_check.py`：`0 对疑似（另 218 对已裁定保留）`，退出码 0；
3. `local_ci` 的 `vocab-near` 不再因存量而 warn（仅在新疑似出现时才报）；
4. `validate.py` / `unittest` / `ruff` 全绿；测试数变化同步锁定文档。

## 五、边界与约束

- 登记依据必须可溯：本批依据 `docs/反例与近义裁定清单-2026-11-18.md`；**新增疑似不得自动豁免**。
- 本任务文件数 > 2，流程 S1→S6 不豁免。
