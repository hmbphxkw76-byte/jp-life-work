# 核验证据包 2026-11-19 · 12-culture-life

- 会话：并行核验子会话（组 3），worktree `D:\文档\GitHub\jp-life-work\.worktrees\deepen-g3`，分支 `task/deepen-g3-dcdf4009`
- 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页；不动核验状态 / 置信度）
- 范围：核验状态=部分核验 且来源URL 门户级，共 33 条
- 处置合计：升级 6 / 保留门户 27 / 纠错 0

## A 覆盖表（33 条门户条目）

| ID | 词条 | 处置 | 说明 |
| --- | --- | --- | --- |
| CUL-001 | 正月 | 保留 | 宽泛节庆术语，文化庁无单页，保留门户 |
| CUL-002 | お盆 | 保留 | 同上 |
| CUL-003 | 花見 | 保留 | 同上 |
| CUL-004 | 祭り | 保留 | 同上 |
| CUL-005 | 七夕 | 保留 | 同上 |
| CUL-006 | 節分 | 保留 | 同上 |
| CUL-007 | 彼岸 | 保留 | 同上 |
| CUL-008 | 年末年始 | 保留 | 同上 |
| CUL-010 | 初詣 | 保留 | 同上 |
| CUL-020 | 火災保険 | 保留 | 金融庁无单页，保留门户 |
| CUL-022 | ゴミ出し | 升级 | 環境省「環境再生・資源循環」 |
| CUL-025 | 和食 | 升级 | 文化庁「食文化」 |
| CUL-026 | 定食 | 保留 | 農水産省无单页，保留门户 |
| CUL-027 | 弁当 | 保留 | 同上 |
| CUL-029 | コンビニ | 升级 | 経済産業省「商業統計」 |
| CUL-030 | スーパー | 升级 | 経済産業省「商業統計」 |
| CUL-032 | 消費税 | 升级 | 国税庁「消費税」 |
| CUL-033 | 電子マネー | 保留 | 金融庁无单页，保留门户 |
| CUL-034 | ポイントカード | 保留 | 消費者庁无单页，保留门户 |
| CUL-035 | クレジットカード | 保留 | 金融庁无单页，保留门户 |
| CUL-036 | 食べ放題 | 保留 | 消費者庁无单页，保留门户 |
| CUL-038 | お辞儀 | 保留 | 宽泛文化术语，保留门户 |
| CUL-039 | 贈り物 | 保留 | 同上 |
| CUL-040 | お中元 | 保留 | 同上 |
| CUL-041 | お歳暮 | 保留 | 同上 |
| CUL-042 | 冠婚葬祭 | 保留 | 同上 |
| CUL-043 | ご祝儀 | 保留 | 同上 |
| CUL-044 | 香典 | 保留 | 同上 |
| CUL-045 | 挨拶 | 保留 | 同上 |
| CUL-050 | 図書館 | 保留 | 文科省无单页，保留门户 |
| CUL-051 | 公民館 | 保留 | 同上 |
| CUL-054 | ゴミ収集 | 升级 | 環境省「環境再生・資源循環」 |
| CUL-064 | クレーム | 保留 | 消費者庁无单页，保留门户 |

## B 升级证据（6 条）

| ID | 词条 | 新来源URL | 实取页面（标题/性质） | 实取 |
| --- | --- | --- | --- | --- |
| CUL-022 | ゴミ出し | https://www.env.go.jp/recycle/ | 環境再生・資源循環（環境省） | 成功 |
| CUL-025 | 和食 | https://www.bunka.go.jp/seisaku/shokubunka/index.html | 食文化（文化庁） | 成功 |
| CUL-029 | コンビニ | https://www.meti.go.jp/statistics/tyo/syoudou/index.html | 商業統計（経済産業省） | 成功 |
| CUL-030 | スーパー | https://www.meti.go.jp/statistics/tyo/syoudou/index.html | 商業統計（経済産業省） | 成功 |
| CUL-032 | 消費税 | https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi.htm | 消費税（国税庁） | 成功 |
| CUL-054 | ゴミ収集 | https://www.env.go.jp/recycle/ | 環境再生・資源循環（環境省） | 成功 |

## C 保留理由（27 条）

多为宽泛生活文化术语（节庆、礼仪、赠答）或省厅无对应单页（金融庁 電子マネー/クレジットカード/火災保険、消費者庁 ポイントカード/食べ放題/クレーム、文科省 図書館/公民館、農水産省 定食/弁当），无权威单页覆盖，保留门户并记录理由。

## D 纠错记录

本次未发现门户条目错配。另记录既有格式瑕疵（非门户、未修正）：部分非门户条目来源URL 末尾带多余后缀「，2026。」，属格式问题，未纳入本次变更。

### D.1 N2 专项复核补充（2026-11-19，closure-b）

35 条非门户条目来源 URL 末尾多余后缀「，2026。」已全部去除（格式纠错），基础 URL 不变；经 `vocab_tool verify-update` 回写，`check` 0E0W。

## E 自检结论

- `verify-update --topic 12-culture-life --file engine/vocabulary/data/12-culture-life/imports/2026-11-19_核验深化.md`：读取 6 行 → 更新 6 / 未匹配 0 / 非法 0；词库 73 条 → v1.5。
- `export --format all`：生成 json/csv/jsonl（v1.5）。
- `check --topic 12-culture-life`：通过（0 项错误 / 0 项警告）。
- 未改动核验状态 / 置信度；未改 `docs/登记册待核实项复核记录-2026-11-19.md`。

## F 提交短码与文件清单

- 提交：commit message `feat(vocab): 09/12/20/14 门户 URL 核验深化`（短码以提交记录为准）。
- 变更文件：
  - `engine/vocabulary/data/12-culture-life/terms.md`（v1.5）
  - `engine/vocabulary/data/12-culture-life/imports/2026-11-19_核验深化.md`
  - `engine/vocabulary/data/12-culture-life/exports/12-culture-life_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/12-culture-life.md`
