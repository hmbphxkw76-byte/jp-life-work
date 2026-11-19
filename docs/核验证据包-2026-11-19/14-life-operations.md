# 核验证据包 2026-11-19 · 14-life-operations

- 会话：并行核验子会话（组 3），worktree `D:\文档\GitHub\jp-life-work\.worktrees\deepen-g3`，分支 `task/deepen-g3-dcdf4009`
- 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页；不动核验状态 / 置信度）
- 范围：核验状态=部分核验 且来源URL 门户级，共 8 条
- 处置合计：升级 4 / 保留门户 4 / 纠错 0

## A 覆盖表（8 条门户条目）

| ID | 词条 | 处置 | 说明 |
| --- | --- | --- | --- |
| LOP-033 | 地震保険 | 保留 | 金融庁无对应单页，保留门户 |
| LOP-035 | 粗大ゴミ | 升级 | 環境省廃棄物 Q&A（Q4 粗大ごみ） |
| LOP-036 | 資源ゴミ | 保留 | 環境省无「資源ごみ」单页，保留门户 |
| LOP-039 | 印鑑 | 保留 | 金融庁非所管，无单页，保留门户 |
| LOP-041 | デビットカード | 保留 | 金融庁无对应单页，保留门户 |
| LOP-049 | キャッシュレス | 升级 | 経済産業省「キャッシュレス」 |
| LOP-075 | ゆうちょ銀行 | 升级 | ゆうちょ銀行「口座開設」（日本郵便） |
| LOP-076 | 電子マネー | 升级 | 経済産業省「キャッシュレス」（列举电子货币） |

## B 升级证据（4 条）

| ID | 词条 | 新来源URL | 实取页面（标题/性质） | 实取 |
| --- | --- | --- | --- | --- |
| LOP-035 | 粗大ゴミ | https://www.env.go.jp/recycle/kaden/tv-recycle/qa.html | 廃棄物の処分に「無許可」の回収業者を利用しないでください（Q4 粗大ごみ） | 成功 |
| LOP-049 | キャッシュレス | https://www.meti.go.jp/policy/mono_info_service/cashless/index.html | キャッシュレス（経済産業省） | 成功 |
| LOP-075 | ゆうちょ銀行 | https://jp-bank-kaisetsu.japanpost.jp/account_open | 口座開設｜ゆうちょ銀行（日本郵便） | 成功 |
| LOP-076 | 電子マネー | https://www.meti.go.jp/policy/mono_info_service/cashless/index.html | キャッシュレス（経済産業省，列举电子货币为手段） | 成功 |

## C 保留理由（4 条）

- LOP-033 地震保険：金融庁站内有「保険について」页，但无地震保険专页；地震保険制度说明主要由財務省/損害保険料率算出機構承担，与来源字段「金融庁」不匹配且无同源单页，保留门户。
- LOP-036 資源ゴミ：分別・収集规则属自治体，環境省无「資源ごみ」单页（仅有 3R/容器包装リサイクル法等专项页），保留门户。
- LOP-039 印鑑：印鑑登録・実印は自治体/法務局領域，金融庁非所管，保留门户。
- LOP-041 デビットカード：金融庁无デビットカード单页（资金决済法下的电子决済手段页不直接对应），保留门户。

## D 纠错记录

本次门户条目无错配。另记录两条非门户既有错配（不属本次门户范围，未改动，留待专项处理）：LOP-034（引越し会社）、LOP-077（多言語通訳コールセンター）来源URL 均复用総務省 `.../c-gyousei/zairyu/`（外国人住民に係る住民基本台帳制度页），与词条不切题；因来源字段（総務省）不可改且未检索到同源权威单页，暂保留原 URL 并记录。

### D.1 N2 专项复核补充（2026-11-19，closure-b）

| 条目 | 结论 | 新 URL | 依据 |
|---|---|---|---|
| LOP-034 引越し会社 | 纠错（回落门户） | https://www.soumu.go.jp/ | 原 URL 为「外国人住民に係る住民基本台帳制度」页，与词条不切題；総務省无引越し業者单页，回落门户 |
| LOP-077 多言語通訳コールセンター | 纠错（回落门户） | https://www.soumu.go.jp/ | 同上；未确认到総務省多言語通訳コールセンター専页 |

### D.2 N7 抽样纠错（2026-11-19，closure-b 收尾）

| 条目 | 结论 | 新 URL | 依据 |
|---|---|---|---|
| LOP-044 水道料金 | 纠错（升级） | https://www.mlit.go.jp/mizukokudo/watersupply/ | 原 URL 为住宅局页（jutakukentiku/house），不覆盖水道；改水道局「水道対策」页（web_fetch 成功） |
| LOP-073 水道局 | 纠错（升级） | https://www.mlit.go.jp/mizukokudo/watersupply/ | 同上 |

> 备注：LOP-035 粗大ゴミ 原 URL（廃家電・粗大ごみ Q&A）经复测**切題**，不改。

## E 自检结论

- `verify-update --topic 14-life-operations --file engine/vocabulary/data/14-life-operations/imports/2026-11-19_核验深化.md`：读取 4 行 → 更新 4 / 未匹配 0 / 非法 0；词库 77 条 → v1.8。
- `export --format all`：生成 json/csv/jsonl（v1.8）。
- `check --topic 14-life-operations`：通过（0 项错误 / 0 项警告）。
- 未改动核验状态 / 置信度；未改 `docs/登记册待核实项复核记录-2026-11-19.md`。
- （closure-b 收尾）`verify-update --topic 14-life-operations --file engine/vocabulary/data/14-life-operations/imports/2026-11-19_核验深化抽样.md`：更新 2 条（LOP-044 / LOP-073）→ v1.11；`verify` 全库 0 错误 / 0 警告。

## F 提交短码与文件清单

- 提交：commit message `feat(vocab): 09/12/20/14 门户 URL 核验深化`（短码以提交记录为准）。
- 变更文件：
  - `engine/vocabulary/data/14-life-operations/terms.md`（v1.8）
  - `engine/vocabulary/data/14-life-operations/imports/2026-11-19_核验深化.md`
  - `engine/vocabulary/data/14-life-operations/exports/14-life-operations_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/14-life-operations.md`
