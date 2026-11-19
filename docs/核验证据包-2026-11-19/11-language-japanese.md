# 核验证据包 — 11-language-japanese（2026-11-19）

> 组 4 / 分支 `task/deepen-g4-dcdf4009` / worktree `.worktrees/deepen-g4`。
> 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页，不动核验状态 / 置信度）。
> 范围：本主题「部分核验 且 来源URL 门户级」条目共 **9** 条。前批 §七 已升级 44 条（非门户），本批 9 条门户逐条复核。

## A 覆盖表

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| JPN-007 | JFT-Basic | 保留（前批已登记） | https://www.jft-basic.jp/ | 已为 JFT-Basic 官方站根域，前批 §七 已登记且 URL 未变；无更深具体页可落地 |
| JPN-026 | 漢語 | 保留 | https://www.ninjal.ac.jp/ | 国立国語研究所为研究机构，未确认到「漢語」单页定义页；宽泛語種术语，保留机构门户 |
| JPN-045 | 教材 | 保留 | https://www.irodori.jpf.go.jp | 国際交流基金「irodori」为教材站，无「教材」单页定义；非政府机构，保留门户 |
| JPN-049 | インプット | 保留 | https://www.irodori.jpf.go.jp | 学習法泛称，未见权威单页覆盖；非政府机构，保留门户 |
| JPN-050 | アウトプット | 保留 | https://www.irodori.jpf.go.jp | 学習法泛称，未见权威单页覆盖；非政府机构，保留门户 |
| JPN-051 | シャドーイング | 保留 | https://www.irodori.jpf.go.jp | 練習法泛称，未见权威单页覆盖；非政府机构，保留门户 |
| JPN-053 | 報連相 | 保留 | https://www.mhlw.go.jp/ | 職場日語泛称，厚生労働省未见单页定义页；保留门户 |
| JPN-060 | 上司への確認 | 保留 | https://www.mhlw.go.jp/ | 職場日語泛称，厚生労働省未见单页定义页；保留门户 |
| JPN-062 | 面接 | 保留 | https://www.mhlw.go.jp/ | 就職・選考泛称，厚生労働省未见单页定义页；保留门户 |

合计：升级 0 / 保留 9 / 纠错 0。

## B 升级证据

（本批无升级）

## C 保留理由（逐条）

- **JPN-007 JFT-Basic**：URL 即 JFT-Basic 官方站根域（`https://www.jft-basic.jp/`），前批已登记；根域即该考试官方门户，无更深具体页。
- **JPN-026 漢語**：来源为国立国語研究所（研究机构），检索未确认到以「漢語」为对象的单页权威定义；属宽泛語種术语。
- **JPN-045 教材**：来源为国際交流基金（非政府机构），`irodori` 站为教材站但无「教材」单页定义。
- **JPN-049 インプット / JPN-050 アウトプット / JPN-051 シャドーイング**：均为学習法泛称，国際交流基金无单页覆盖。
- **JPN-053 報連相 / JPN-060 上司への確認 / JPN-062 面接**：均为職場日語泛称，厚生労働省无单页定义页。

## D 纠错记录

（无）

## E 自检结论

```
[verify-update] 读取 44 行 → 更新 0 / 未匹配 0 / 非法 0；词库共 70 条（未写盘）
[check] data/11-language-japanese/terms.md：共 70 条，版本 v1.5
[check] 结论：通过（0 项错误 / 0 项警告）
```

说明：`imports/2026-11-19_核验深化.md` 仅含前批 44 条升级行，本批无新增变更行（9 条门户均为保留）。

## F 提交短码与文件清单

- 提交短码：`a57d702`（`feat(vocab): 07/13/11/17 门户 URL 核验深化`）。
- 文件清单：
  - `engine/vocabulary/data/11-language-japanese/terms.md`（未变更）
  - `engine/vocabulary/data/11-language-japanese/imports/2026-11-19_核验深化.md`（未变更）
  - `engine/vocabulary/data/11-language-japanese/exports/11-language-japanese_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/11-language-japanese.md`
