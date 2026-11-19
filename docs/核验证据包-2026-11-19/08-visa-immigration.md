# 核验证据包 08-visa-immigration（2026-11-19）

> 组 1 并行核验子会话；worktree `.worktrees/deepen-g1`，分支 `task/deepen-g1-dcdf4009`。
> 依据 `docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C：仅落地**已实取确认**的官方具体页；不动核验状态 / 置信度。
> 范围：本主题「核验状态=部分核验 且 来源URL 为门户级（域名/根路径）」共 **18** 条。

## A 覆盖表（全部 18 条门户条目，一条不漏）

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| VIS-031 | 帰化 | **升级** | https://www.moj.go.jp/MINJI/kokuseki.html | 法務省「国籍」（国籍Q&A・帰化許可申請案内）；已 fetch 成功 |
| VIS-034 | 素行善良 | 保留 | https://www.moj.go.jp/ | 永住・帰化要件，官方无单页定义，保留门户 |
| VIS-036 | 納税義務 | **升级** | https://www.nta.go.jp/taxes/kids/hatten/page14.htm | 国税庁「納税の義務」（宪法30条・申告納税制度）；已 fetch 成功 |
| VIS-037 | 年金保険料 | 保留 | https://www.nenkin.go.jp/ | 日本年金機構仅有纳付・手続页，无「保険料」概念单页定义，保留门户 |
| VIS-038 | 健康保険料 | 保留 | https://www.mhlw.go.jp/ | 厚生労働省仅有医疗保険综合页，无「健康保険料」单页定义，保留门户 |
| VIS-041 | 帰化許可申請 | **升级** | https://www.moj.go.jp/ONLINE/NATIONALITY/6-2.html | 法務省「帰化許可申請」（手続根拠・提出先等）；已 fetch 成功 |
| VIS-043 | 扶養 | 保留 | https://www.mhlw.go.jp/ | 家族法/福祉概念，官方无单页定义，保留门户 |
| VIS-045 | 住民登録 | **升级** | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/c-gyousei/zairyu/ | 総務省「外国人住民に係る住民基本台帳制度」；已 fetch 成功 |
| VIS-047 | 国民健康保険 | **升级** | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/koukikourei/index_00002.html | 厚生労働省「国民健康保険制度」；已 fetch 成功 |
| VIS-049 | 学校 | 保留 | https://www.mext.go.jp/ | 文部科学省「小学校、中学校、高等学校」页存在，但本次 web_fetch 未能取回内容，不满足实取门槛，保留门户 |
| VIS-050 | 住宅 | 保留 | https://www.mlit.go.jp | 国土交通省无「住宅」单页定义（仅公营住宅施策），保留门户 |
| VIS-051 | 生活保護 | **升级** | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/seikatsuhogo/seikatuhogo/index.html | 厚生労働省「生活保護制度」；已 fetch 成功 |
| VIS-052 | 出入国管理及び難民認定法 | 保留 | https://www.moj.go.jp/ | 法令正文在 e-Gov；未确认到 stable 单页直链，保留门户 |
| VIS-053 | 入管法改正 | 保留 | https://www.moj.go.jp/ | 修法过程型事件，无单页定义，保留门户 |
| VIS-060 | 難民認定 | 保留 | https://www.moj.go.jp/ | 法务省难民认定制度页未确认到可直链单页，保留门户 |
| VIS-066 | 弁護士 | 保留 | https://www.nichibenren.or.jp/ | 日本弁護士連合会（非政府机构），保留门户 |
| VIS-075 | 取消訴訟 | 保留 | https://www.courts.go.jp/ | 通用诉讼类型术语，最高裁判所无单页定义，保留门户 |
| VIS-076 | 行政不服審査 | 保留 | https://www.soumu.go.jp/ | 総務省仅有情報公開・行政手続综合页，无「行政不服審査」单页定义，保留门户 |

合计：**升级 6 / 保留 12 / 纠错 0**。

## B 升级证据（目标 URL + web_fetch 成功记录 + 页面标题）

| ID | 目标 URL | 页面标题（fetch 实取） |
|---|---|---|
| VIS-031 | https://www.moj.go.jp/MINJI/kokuseki.html | 法務省：国籍 |
| VIS-036 | https://www.nta.go.jp/taxes/kids/hatten/page14.htm | 納税の義務 ｜税の学習コーナー｜国税庁 |
| VIS-041 | https://www.moj.go.jp/ONLINE/NATIONALITY/6-2.html | 法務省：帰化許可申請 |
| VIS-045 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/c-gyousei/zairyu/ | 総務省｜外国人住民に係る住民基本台帳制度 |
| VIS-047 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/koukikourei/index_00002.html | 国民健康保険制度 ｜厚生労働省 |
| VIS-051 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/seikatsuhogo/seikatuhogo/index.html | 生活保護制度 ｜厚生労働省 |

## C 保留理由（逐条）

- VIS-034 素行善良：永住・帰化要件，官方无单页定义，保留门户。
- VIS-037 年金保険料：日本年金機構仅有纳付・手続页，无「保険料」概念单页定义，保留门户。
- VIS-038 健康保険料：厚生労働省仅有医疗保険综合页，无「健康保険料」单页定义，保留门户。
- VIS-043 扶養：家族法/福祉概念，官方无单页定义，保留门户。
- VIS-049 学校：文部科学省页面存在，但 web_fetch 未取回内容（站点拦截），不满足实取门槛，保留门户。
- VIS-050 住宅：国土交通省无「住宅」单页定义（仅公营住宅施策），保留门户。
- VIS-052 出入国管理及び難民認定法：法令正文在 e-Gov，未确认到稳定单页直链，保留门户。
- VIS-053 入管法改正：修法过程型事件，无单页定义，保留门户。
- VIS-060 難民認定：未确认到可直链的法务省单页，保留门户。
- VIS-066 弁護士：日本弁護士連合会（非政府机构），保留门户。
- VIS-075 取消訴訟：通用诉讼类型术语，最高裁判所无单页定义，保留门户。
- VIS-076 行政不服審査：総務省仅有情報公開・行政手続综合页，无「行政不服審査」单页定义，保留门户。

## D 纠错记录

无。本主题门户条目的来源URL 与来源机构一致，未发现错配。

## E 自检结论

```
$ python engine/vocabulary/script/vocab_tool.py verify-update --topic 08-visa-immigration --file engine/vocabulary/data/08-visa-immigration/imports/2026-11-19_核验深化.md
[verify-update] 读取 6 行 → 更新 6 / 未匹配 0 / 非法 0；词库共 79 条（已更新至 v1.5）

$ python engine/vocabulary/script/vocab_tool.py export --topic 08-visa-immigration --format all
[export] data/08-visa-immigration/exports/08-visa-immigration_2026-11-19_export.json（79 条，v1.5）
[export] data/08-visa-immigration/exports/08-visa-immigration_2026-11-19_export.csv（79 条，v1.5）
[export] data/08-visa-immigration/exports/08-visa-immigration_2026-11-19_export.jsonl（79 条，v1.5）

$ python engine/vocabulary/script/vocab_tool.py check --topic 08-visa-immigration
[check] data/08-visa-immigration/terms.md：共 79 条，版本 v1.5
[check] 结论：通过（0 项错误 / 0 项警告）
```

## F 提交短码与文件清单

- commit：见本组提交（中文 message：`feat(vocab): 03/06/08/15 门户 URL 核验深化`）
- 变更文件：
  - `engine/vocabulary/data/08-visa-immigration/terms.md`（v1.4 → v1.5）
  - `engine/vocabulary/data/08-visa-immigration/imports/2026-11-19_核验深化.md`（新增）
  - `engine/vocabulary/data/08-visa-immigration/exports/08-visa-immigration_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/08-visa-immigration.md`（本文件）
