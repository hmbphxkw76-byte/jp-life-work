# 核验证据包 — 07-economy-finance（2026-11-19）

> 组 4 / 分支 `task/deepen-g4-dcdf4009` / worktree `.worktrees/deepen-g4`。
> 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页，不动核验状态 / 置信度）。
> 范围：本主题「部分核验 且 来源URL 门户级」条目共 **46** 条。前批 §七 已升级 23 条（非门户），本批 46 条门户逐条复核。

## A 覆盖表

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| ECF-005 | 企業物価指数 | 升级 | https://www.boj.or.jp/statistics/pi/index.htm | 日本銀行「物価関連統計」（含企業物価指数各基準）；web_fetch 成功 |
| ECF-007 | 政策金利 | 升级 | https://www.boj.or.jp/mopo/outline/index.htm | 日本銀行「金融政策の概要」（政策金利・金融市場調節）；web_fetch 成功 |
| ECF-009 | 購買力平価 | 保留 | https://www.imf.org/ | 来源为 IMF，未确认 IMF 有单页覆盖的 PPP 定义页（PPP 数据由 World Bank ICP 提供，与来源机构不一致，不强行改写）；宽泛术语，保留门户 |
| ECF-010 | 円安 | 保留 | https://www.boj.or.jp/ | 日本銀行未见「円安」单页定义（汇率议题分散）；宽泛术语，保留门户 |
| ECF-011 | 日本銀行 | 保留 | https://www.boj.or.jp/ | 机构定义，机构门户即准确来源；保留门户 |
| ECF-012 | 金融庁 | 保留 | https://www.fsa.go.jp/ | 机构定义；保留门户 |
| ECF-013 | 連邦準備制度 | 保留 | https://www.federalreserve.gov/ | 机构定义（外国央行）；保留门户 |
| ECF-014 | 欧州中央銀行 | 保留 | https://www.ecb.europa.eu/ | 机构定义（外国央行）；保留门户 |
| ECF-015 | 中国人民銀行 | 保留 | http://www.pbc.gov.cn/ | 机构定义（外国央行）；保留门户 |
| ECF-016 | 国際通貨基金 | 保留 | https://www.imf.org/ | 机构定义（国际机构）；保留门户 |
| ECF-017 | 世界銀行 | 保留 | https://www.worldbank.org/ | 机构定义（国际机构）；保留门户 |
| ECF-019 | 株式 | 保留 | https://www.fsa.go.jp/ | 金融庁未见「株式」单页定义；宽泛概念，保留门户 |
| ECF-020 | 投資信託 | 保留 | https://www.fsa.go.jp/ | 金融庁未见「投資信託」单页定义（按商品分散）；宽泛概念，保留门户 |
| ECF-021 | ETF | 保留 | https://www.fsa.go.jp/ | 金融庁未见「ETF」单页定义；宽泛概念，保留门户 |
| ECF-022 | 為替 | 保留 | https://www.boj.or.jp/ | 日本銀行未見「外国為替」单页定义（相場/制度分散）；宽泛概念，保留门户 |
| ECF-023 | 流動性 | 保留 | https://www.boj.or.jp/ | 日本銀行未见「流動性」单页定义；宽泛概念，保留门户 |
| ECF-024 | マーケットメイカー | 保留 | https://www.jsda.or.jp/ | 来源为日本証券業協会（非政府机构），未见单页定义；保留门户 |
| ECF-025 | 空売り | 保留 | https://www.fsa.go.jp/ | 金融庁未见「空売り」单页定义；宽泛概念，保留门户 |
| ECF-026 | レバレッジ | 保留 | https://www.fsa.go.jp/ | 金融庁未见「レバレッジ」单页定义；宽泛概念，保留门户 |
| ECF-027 | 証拠金 | 保留 | https://www.fsa.go.jp/ | 金融庁未见「証拠金」单页定义；宽泛概念，保留门户 |
| ECF-029 | 時価総額 | 保留 | https://www.jsda.or.jp/ | 来源为日本証券業協会（非政府机构），未见单页定义；保留门户 |
| ECF-030 | ベーシスポイント | 保留 | https://www.boj.or.jp/ | 日本銀行未见「ベーシスポイント」单页定义（单位说明分散）；宽泛概念，保留门户 |
| ECF-032 | デリバティブ | 保留 | https://www.fsa.go.jp/ | 金融庁未见「デリバティブ」单页定义（店頭デリバティブ取引情報等为数据页）；宽泛概念，保留门户 |
| ECF-033 | 金融商品取引法 | 保留 | https://www.fsa.go.jp/ | 金融庁「法令・指針等」仅列所管法令一览（Excel），无该法单页说明；保留门户 |
| ECF-034 | 銀行法 | 保留 | https://www.fsa.go.jp/ | 同上，无单页说明；保留门户 |
| ECF-035 | 保険業法 | 保留 | https://www.fsa.go.jp/ | 同上，无单页说明；保留门户 |
| ECF-036 | マネーロンダリング防止 | 保留 | https://www.fsa.go.jp/ | 金融庁未见单页定义（对策分散）；宽泛概念，保留门户 |
| ECF-037 | KYC | 保留 | https://www.fsa.go.jp/ | 金融庁未见「KYC」单页定义；宽泛概念，保留门户 |
| ECF-039 | 量的緩和 | 升级 | https://www.boj.or.jp/mopo/outline/ref_qqe.htm | 日本銀行「（参考）2013年以降の『量的・質的金融緩和』のもとでの金融政策」；web_fetch 成功 |
| ECF-040 | 量的引き締め | 保留 | https://www.boj.or.jp/ | 日本銀行未见「量的引き締め」单页定义（2024 正常化仅在 QQE 参考页述及）；宽泛概念，保留门户 |
| ECF-041 | 金融庁検査 | 保留 | https://www.fsa.go.jp/ | 金融庁未见「金融庁検査」单页定义（検査・監督の基本方針等分散）；保留门户 |
| ECF-045 | 社会保険料 | 保留 | https://www.nenkin.go.jp/ | 日本年金機構仅覆盖年金保険料，未见覆盖健康/雇用/労災的「社会保険料」单页定义；保留门户 |
| ECF-053 | PER | 保留 | https://www.jsda.or.jp/ | 来源为日本証券業協会（非政府机构），未见单页定义；保留门户 |
| ECF-054 | PBR | 保留 | https://www.jsda.or.jp/ | 同上，保留门户 |
| ECF-055 | 配当利回り | 保留 | https://www.jsda.or.jp/ | 同上，保留门户 |
| ECF-056 | リスクプレミアム | 保留 | https://www.bis.org/ | BIS 未见「リスクプレミアム」单页定义；宽泛概念，保留门户 |
| ECF-057 | 信用格付け | 保留 | https://www.fsa.go.jp/ | 金融庁未见「信用格付け」单页定义；宽泛概念，保留门户 |
| ECF-058 | VaR | 保留 | https://www.bis.org/ | BIS 未见「VaR」单页定义；宽泛概念，保留门户 |
| ECF-059 | 分散投資 | 保留 | https://www.fsa.go.jp/ | 金融庁未见「分散投資」单页定义；宽泛概念，保留门户 |
| ECF-060 | ポートフォリオ | 保留 | https://www.fsa.go.jp/ | 金融庁未见「ポートフォリオ」单页定义；宽泛概念，保留门户 |
| ECF-061 | 為替リスク | 保留 | https://www.boj.or.jp/ | 日本銀行未見「為替リスク」单页定义；宽泛概念，保留门户 |
| ECF-064 | 家計相談 | 保留 | https://www.jafp.or.jp/ | 来源为日本FP協会（非政府机构），未见单页定义；保留门户 |
| ECF-065 | 保険選び | 保留 | https://www.jafp.or.jp/ | 来源为日本FP協会（非政府机构），未见单页定义；保留门户 |
| ECF-067 | 送金 | 保留 | https://www.boj.or.jp/ | 日本銀行未见「送金」单页定义（国際送金は外国為替・決済制度に分散）；宽泛概念，保留门户 |
| ECF-068 | 投資判断 | 保留 | https://www.fsa.go.jp/ | 金融庁未见「投資判断」单页定义；宽泛概念，保留门户 |
| ECF-069 | 最低賃金 | 保留（前批已登记） | https://saiteichingin.mhlw.go.jp/ | 前批 §七 已登记为厚生労働省最低賃金特設サイト（专门站），URL 未变 |

合计：升级 3 / 保留 43 / 纠错 0。

## B 升级证据（目标 URL + web_fetch 成功记录 + 页面标题）

| ID | 目标 URL | web_fetch | 页面标题 |
|---|---|---|---|
| ECF-005 | https://www.boj.or.jp/statistics/pi/index.htm | 成功 | 物価関連統計 : 日本銀行 Bank of Japan |
| ECF-007 | https://www.boj.or.jp/mopo/outline/index.htm | 成功 | 金融政策の概要 : 日本銀行 Bank of Japan |
| ECF-039 | https://www.boj.or.jp/mopo/outline/ref_qqe.htm | 成功 | （参考）2013年以降の「量的・質的金融緩和」のもとでの金融政策 : 日本銀行 |

## C 保留理由（逐条）

- **机构定义（7 条）**：ECF-011 日本銀行 / ECF-012 金融庁 / ECF-013 連邦準備制度 / ECF-014 欧州中央銀行 / ECF-015 中国人民銀行 / ECF-016 国際通貨基金 / ECF-017 世界銀行 —— 机构门户即准确且诚实的来源，不强行具体化。
- **非政府机构（7 条）**：ECF-024 / ECF-029 / ECF-053 / ECF-054 / ECF-055（日本証券業協会）、ECF-064 / ECF-065（日本FP協会）—— 非政府机构，未见单页覆盖，保留门户。
- **宽泛概念 / 无单页覆盖（29 条）**：ECF-009 / ECF-010 / ECF-019 / ECF-020 / ECF-021 / ECF-022 / ECF-023 / ECF-025 / ECF-026 / ECF-027 / ECF-030 / ECF-032 / ECF-033 / ECF-034 / ECF-035 / ECF-036 / ECF-037 / ECF-040 / ECF-041 / ECF-045 / ECF-056 / ECF-057 / ECF-058 / ECF-059 / ECF-060 / ECF-061 / ECF-067 / ECF-068，以及 ECF-069（前批已登记专门站，URL 未变）。
- **ECF-009 購買力平価**：来源为 IMF，IMF 无单页 PPP 定义页；PPP 官方数据由 World Bank ICP 提供（与来源机构不一致），不强行改写。
- **ECF-033 / ECF-034 / ECF-035（金商法・銀行法・保険業法）**：金融庁「法令・指針等」仅提供所管法令一览（Excel），无各法单页说明，保留门户。

## D 纠错记录

（无。本主题非门户「部分核验」条目的 URL 未发现明显错配。）

## E 自检结论

```
[verify-update] 读取 26 行 → 更新 3 / 未匹配 0 / 非法 0；词库共 77 条（已更新至 v1.6）
[check] data/07-economy-finance/terms.md：共 77 条，版本 v1.6
[check] 结论：通过（0 项错误 / 0 项警告）
```

## F 提交短码与文件清单

- 提交短码：`a57d702`（`feat(vocab): 07/13/11/17 门户 URL 核验深化`）。
- 文件清单：
  - `engine/vocabulary/data/07-economy-finance/terms.md`
  - `engine/vocabulary/data/07-economy-finance/imports/2026-11-19_核验深化.md`
  - `engine/vocabulary/data/07-economy-finance/exports/07-economy-finance_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/07-economy-finance.md`
