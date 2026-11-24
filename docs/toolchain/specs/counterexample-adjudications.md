# 规格：反例扫描裁定清单（ce-adjudications）

> 任务 slug：`counterexample-adjudications`
> 版本：v1.0（2026-11-23）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)

## 一、动机

`counterexample_scan.py` 每轮报 61 条候选并退出码 2，其中 ABS / GEN / NOSRC 共 22 条
已被 `docs/反例与近义裁定清单-2026-11-18.md` 裁定「保留」，但扫描器无从得知 → 重复告警。

## 二、目标与非目标

**目标**：新增 `engine/config/counterexample-adjudications.json`（`(report, sentence)` → 裁定），
命中即不再计为待处理；输出附 `adjudicated` 计数。

**非目标**：**不豁免「单源」类**（n22）。那是内容侧补源欠账，必须保持可见，逐条补第二来源后再消解。

## 三、接口设计

- `load_adjudications(path=None) -> dict[tuple[str,str], dict]`（缺失 / 损坏返回空）；
- `main()`：把每条 item 分为 `items`（待处理）与已裁定两类；退出码仅由待处理数决定；
- 报告 JSON 增加 `adjudicated` 字段；
- 新增测试 3 项（缺失 / 损坏 / 过滤后退出码 0），并保持既有 `test_main_exit_2` 语义。

## 四、验收标准

1. 新测试先红后绿；既有 `test_main_exit_2` 语义保持；
2. 实跑：`39 条待处理（另 22 条已裁定）`；
3. 单源条目一条不漏地保留在待处理中；
4. `validate.py` / `unittest` / `ruff` 全绿；测试数变化同步锁定文档。

## 五、边界与约束

- 只登记原裁定覆盖的类别；新增候选默认不豁免。
- 本任务文件数 > 2，S1→S6 不豁免。
