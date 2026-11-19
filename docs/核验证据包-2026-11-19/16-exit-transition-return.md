# 核验证据包：16-exit-transition-return（2026-11-19）

> 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页）。
> 范围：本主题「部分核验 且 来源URL 门户级」条目 **1 条**（门户级 = 仅域名/根路径）。
> 处置合计：**升级 0 / 保留 1 / 纠错 0**。不动核验状态、不动置信度。

## A 覆盖表

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| ETR-052 | 協会けんぽ | 保留 | https://www.kyoukaikenpo.or.jp/ | 机构定义（全国健康保険協会本身）；门户即准确来源，无「单页定义页」 |

## B 升级证据

无（本主题无升级条目）。

## C 保留理由（逐条）

- **ETR-052 協会けんぽ**：词条为机构通称（全国健康保険協会），属「机构定义」类；其定义即机构本身，不存在单页覆盖的权威定义页，机构官网门户为准确且诚实的来源，不强行具体化。

## D 纠错记录

无。本主题所有「部分核验」条目的 URL 与来源机构/词条方向一致，未发现错配。

## E 自检结论

```
[verify-update] 读取 0 行 → 更新 0 / 未匹配 0 / 非法 0；词库共 78 条（未写盘）
[check] data/16-exit-transition-return/terms.md：共 78 条，版本 v1.5
[check] 结论：通过（0 项错误 / 0 项警告）
```

## F 提交短码与文件清单

- 提交短码：`4b1ce78`（`feat(vocab): 05/19/10/16 门户 URL 核验深化`）。
- 文件清单：
  - `engine/vocabulary/data/16-exit-transition-return/imports/2026-11-19_核验深化.md`（仅表头，无变更行）
  - `engine/vocabulary/data/16-exit-transition-return/exports/16-exit-transition-return_2026-11-19_export.json`（仅 `generated_at` 时间戳刷新）
  - `engine/vocabulary/data/16-exit-transition-return/terms.md`（未变更，无提交内容）
