# 规格：事实卡片 corroboration 语义（single-source）

> 任务 slug：`fact-card-corroboration`
> 版本：v1.0（2026-11-23）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)

## 一、动机

`fact_card_check` 报 15 条 P2「corroboration 来源数 < 2」。逐卡评估后发现：这些值多为**唯一权威口径**
（厚労省 / 総務省 / 日銀 / 警察庁等官方统计量，或官方定价），**不存在独立第二来源**；
强行补一条非独立或不可核验的链接反而降低可信度，违反「不虚报」纪律。

## 二、目标与非目标

**目标**：给 corroboration 增加显式取值 `single-source`——表示「已核验为单一权威口径、不适用 ≥2 互证」，工具不再对该情形告警。

**非目标**：不为凑数引入弱来源；不改卡片五字段结构；不重排 ID。

## 三、接口设计

1. `engine/tools/fact_card_check.py`
   - `parse_cards()`：第 7 列允许 `N` 或 `single-source`；
   - `check_corroboration()`：
     - `single-source` → 无问题；
     - 空 → P2「未标注」（不变）；
     - 整数 `<2` → P2（不变）。
2. `engine/report_templates/fact-card-standard.md`：登记取值语义与填写要求。
3. `00-decision-hub/data/fact_cards.md`：头部口径说明 + 各卡按结论填写。
4. 测试：`engine/tests/test_tools.py::TestFactCardCheck` 新增 2 项。

## 四、验收标准

1. 新测试先红后绿。
2. `fact_card_check.run()` 不再产生任何 issue；`local_ci` 的 `fact-card` 转 PASS。
3. `validate.py` / `unittest` / `ruff` / `mypy` 全绿；测试数变化同步锁定文档。

## 五、边界与约束

- **不得**为让计数 ≥2 而加入同一发布者的重复页面或非独立转载。
- 无法在本环境核验的可达第二来源（多数 .go.jp 页面 403）**不予引用**，留待人工复核。
