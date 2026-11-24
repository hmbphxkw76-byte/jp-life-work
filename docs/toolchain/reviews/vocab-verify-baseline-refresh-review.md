# 双轴评审：核验闭环第一批（vocab-verify-baseline-refresh）

> 评审日期：2026-11-24
> 评审对象：`engine/vocabulary/config/verification-retention-map.json`、
> `engine/tests/test_vocab_verification_map.py`、`engine/vocabulary/README.md`

## 一、Standards 轴

| 条款 | 结论 | 证据 |
|---|---|---|
| 不虚报 | 通过 | 基线数字全部来自实跑统计；无法联网核验的条目**未**被改为「已核验」 |
| 单一事实源 | 通过 | 映射文件 `coverage` / `baseline` 与 README §5.2 一致 |
| 文档数字锁定 | 通过 | 测试计数 1206 → 1208 同步 4 处 |
| 测试先行 | 说明 | 新增 2 项守卫在旧数据上会因计数漂移而失败，刷新后通过 |

## 二、Spec 轴（第一批目标 ↔ 结果）

| 目标 | 结果 |
|---|---|
| 分类统计 | 全库 **1,518** 条 = 已核验 **164** + 部分核验 **1,354**；待核实 **0** |
| 离线可判定项 | 部分核验涉及 **109 个分类，100% 在保留口径映射内**（无未映射 → 无需临时裁定） |
| 基线一致性 | `coverage` 增加 `terms_total / verified_terms / pending_terms`，与实测逐项相等（有守卫锁定） |

## 三、残余风险 / 遗留

- **1,354 条「部分核验」仍是内容欠账**：它们有保留口径（合法），但未逐条补齐官方原文证据。深化受网络可达性限制（多数 `.go.jp` / `mofa.go.jp` 直连 403），须人工或换网络环境分批推进——已在 README §5.2 写明。
- 无其他遗留。
