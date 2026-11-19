# 工单 B1：文档 ↔ 实现漂移修补（P1）

> **来源**：2026-11-19 工程收尾审计（D1–D6）
> **状态**：已完成（`task/b-docs`，已合并 `4cb47a1`）
> **优先级**：P1

---

## 背景

审计实测发现 6 处「文档声称 = 实现」但实际漂移，属文档可信度问题：

| # | 文档 | 声称 | 实测 |
|---|---|---|---|
| D1 | `docs/CI.md` | 头部 v2.17 | 版本记录末版 v2.22 |
| D2 | `docs/报告周期体系.md` | 头部 v1.0 | 版本记录末版 v1.1（§七 N17 未抬头部） |
| D3 | `docs/审计报告标准化管理体系.md` | 头部 v1.4 | 版本记录末版 v1.7；代码 `audit_registry.SPEC_VERSION = "v1.4"` |
| D4 | `engine/tools/README.md` | v1.2 记测试 978 | 实测 1008（无守卫锁定） |
| D5 | `engine/vocabulary/INDEX.md` | 1634（生成于 2026-11-18） | 实测 1612（删除 22 条后未重生成） |
| D6 | `engine/report-audits/audit/pending-verification.json` | summary 76 | `pending_verification --check` 实测 70 |

## 目标

把 6 处漂移逐项对齐，恢复「文档 = 实现」口径。

## 范围

- 做：6 处文档/生成物的版本号、计数、索引、台账刷新。
- 不做：不改动审计标准语义（D3 只对齐版本口径，不擅自改 `SPEC_VERSION` 语义）。

## 关联

- 源审计：本轮审计 §四 D1–D6。
- 上游：N1（文档↔实现对齐，已合并）。

## 约束

- 生成物（`INDEX.md` / `pending-verification.json`）用对应生成器刷新，不手工编辑。
- 头部版本号口径：头部 = 版本记录末版。

## 验收判据

1. `docs/CI.md` 头部版本 = 版本记录末版。
2. `docs/报告周期体系.md` 头部 = 记录末版。
3. `docs/审计报告标准化管理体系.md` 头部 = 记录末版，且与 `audit_registry.SPEC_VERSION` 口径一致（或显式说明差异）。
4. `engine/tools/README.md` 测试计数 = 实测，且建议加守卫锁定。
5. `engine/vocabulary/INDEX.md` = 重生成后词条数。
6. `engine/report-audits/audit/pending-verification.json` = 刷新后台账数。
7. `validate.py` / `unittest` 全绿。

## 步骤

1. 实测各值（工具/测试/词条/待核实数）。
2. 修 D1–D4 头部与计数。
3. 跑 `vocab_tool index` 刷新 INDEX；跑 `pending_verification` 刷新台账。
4. 跑校验。

## 证据

- diff + 校验退出码（完成后回填）。

## 状态

已完成（`task/b-docs`，已合并 `4cb47a1`）。
