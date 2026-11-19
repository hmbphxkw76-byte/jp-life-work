# 核验证据包 — 13-regional-info（2026-11-19）

> 组 4 / 分支 `task/deepen-g4-dcdf4009` / worktree `.worktrees/deepen-g4`。
> 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页，不动核验状态 / 置信度）。
> 范围：本主题「部分核验 且 来源URL 门户级」条目共 **35** 条。

## A 覆盖表

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| REG-001 | 都道府県 | 升级 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/bunken/chihou-koukyoudantai_kubun.html | 総務省「地方公共団体の分類」（都道府県/市町村/特別区/政令市等）；web_fetch 成功 |
| REG-002 | 市町村 | 升级 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/bunken/chihou-koukyoudantai_kubun.html | 同上；web_fetch 成功 |
| REG-003 | 政令指定都市 | 升级 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/bunken/shitei_toshi-ichiran.html | 総務省「指定都市一覧」（20市・指定政令）；web_fetch 成功 |
| REG-004 | 中核市 | 升级 | https://www.soumu.go.jp/cyukaku/ | 総務省「中核市・施行時特例市」（要件・指定市62）；web_fetch 成功 |
| REG-005 | 特別区 | 升级 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/bunken/chihou-koukyoudantai_kubun.html | 総務省「地方公共団体の分類」含 特別区（東京23区）；web_fetch 成功 |
| REG-011 | 地形 | 保留 | https://www.gsi.go.jp/ | 国土地理院未见「地形」单页定义（有地形分類/地形特性情報等分散内容）；宽泛术语，保留门户 |
| REG-013 | 人口 | 升级 | https://www.stat.go.jp/data/jinsui/index.html | 総務省統計局「人口推計」（総人口・年齢別）；web_fetch 成功 |
| REG-014 | 高齢化率 | 保留 | https://www.stat.go.jp/ | 統計局未见「高齢化率」单页定义（分散于国勢調査/人口推計）；宽泛统计术语，保留门户 |
| REG-018 | 人口減少 | 保留 | https://www.stat.go.jp/ | 統計局未见「人口減少」单页定义；宽泛术语，保留门户 |
| REG-019 | 地方創生 | 升级 | https://www.chisou.go.jp/sousei/ | 内閣府・内閣官房「地方創生」総合サイト；web_fetch 成功 |
| REG-020 | 東京一極集中 | 保留 | https://www.cao.go.jp/ | 内閣府未见「東京一極集中」单页定义；政策课题泛称，保留门户 |
| REG-021 | 過疎地域 | 升级 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/c-gyousei/2001/kaso/kasomain0.htm | 総務省「過疎対策」（過疎地域一覧・制度）；web_fetch 成功 |
| REG-023 | 昼夜間人口比率 | 保留 | https://www.stat.go.jp/ | 統計局未见单页定义（分散于国勢調査）；宽泛统计术语，保留门户 |
| REG-024 | 地域経済 | 保留 | https://www.cao.go.jp/ | 内閣府未见「地域経済」单页定义；宽泛术语，保留门户 |
| REG-025 | 産業構造 | 保留 | https://www.meti.go.jp/ | 経産省未见「産業構造」单页定义；宽泛术语，保留门户 |
| REG-026 | 第一次産業 | 保留 | https://www.stat.go.jp/ | 統計局未见「第一次産業」单页定义；産業分類泛称，保留门户 |
| REG-027 | 第二次産業 | 保留 | https://www.stat.go.jp/ | 同上，保留门户 |
| REG-028 | 第三次産業 | 保留 | https://www.stat.go.jp/ | 同上，保留门户 |
| REG-030 | 農業 | 保留 | https://www.maff.go.jp/ | 農林水産省未见「農業」单页定义（政策/統計分散）；宽泛术语，保留门户 |
| REG-032 | 製造業 | 保留 | https://www.meti.go.jp/ | 経産省未见「製造業」单页定义；宽泛术语，保留门户 |
| REG-033 | 地場産業 | 保留 | https://www.meti.go.jp/ | 経産省未见「地場産業」单页定义；宽泛术语，保留门户 |
| REG-034 | 企業誘致 | 保留 | https://www.cao.go.jp/ | 内閣府未見「企業誘致」单页定义；政策泛称，保留门户 |
| REG-036 | 物価 | 升级 | https://www.stat.go.jp/data/cpi/ | 総務省統計局「消費者物価指数（CPI）」；web_fetch 成功 |
| REG-042 | 商業施設 | 保留 | https://www.meti.go.jp/ | 経産省未见「商業施設」单页定义；宽泛术语，保留门户 |
| REG-046 | 地方自治 | 升级 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/bunken/gaiyou.html | 総務省「地方自治制度の概要」；web_fetch 成功 |
| REG-047 | 地方税 | 升级 | https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czais.html | 総務省自治税務局「地方税の概要」；web_fetch 成功 |
| REG-048 | 地方交付税 | 保留 | https://www.soumu.go.jp/ | 未确认到総務省「地方交付税」单页定义（制度説明分散）；保留门户 |
| REG-051 | 移住支援金 | 保留 | https://www.cao.go.jp/ | 内閣府未見「移住支援金」单页定义；制度细节按自治体而异，保留门户 |
| REG-052 | 地方分権 | 保留 | https://www.cao.go.jp/ | 内閣府/総務省未见「地方分権」单页定义；改革泛称，保留门户 |
| REG-053 | 自治体DX | 升级 | https://www.soumu.go.jp/denshijiti/digital_transformation_portal/index.html | 総務省「地域DXポータルサイト」（自治体DX・地域社会DX）；web_fetch 成功 |
| REG-056 | 補助金 | 保留 | https://www.meti.go.jp/ | 経産省未见「補助金」单页定义（按政策分散）；宽泛术语，保留门户 |
| REG-057 | 条例 | 保留 | https://www.soumu.go.jp/ | 総務省未见「条例」单页定义（地方自治法条文分散）；宽泛术语，保留门户 |
| REG-058 | 移住 | 保留 | https://www.cao.go.jp/ | 内閣府未見「移住」单页定义；政策泛称，保留门户 |
| REG-060 | 地域差 | 保留 | https://www.stat.go.jp/ | 統計局未见「地域差」单页定义；宽泛术语，保留门户 |
| REG-064 | 地域おこし | 保留 | https://www.cao.go.jp/ | 内閣府未見「地域おこし」单页定义（地方創生に包含）；保留门户 |

合计：升级 12 / 保留 23 / 纠错 0。

## B 升级证据（目标 URL + web_fetch 成功记录 + 页面标题）

| ID | 目标 URL | web_fetch | 页面标题 |
|---|---|---|---|
| REG-001 / REG-002 / REG-005 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/bunken/chihou-koukyoudantai_kubun.html | 成功 | 総務省 自治行政局 地方自治制度「地方公共団体の分類」 |
| REG-003 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/bunken/shitei_toshi-ichiran.html | 成功 | 総務省 自治行政局「指定都市一覧」 |
| REG-004 | https://www.soumu.go.jp/cyukaku/ | 成功 | 総務省「中核市・施行時特例市」（地方公共団体の分類） |
| REG-013 | https://www.stat.go.jp/data/jinsui/index.html | 成功 | 総務省統計局「人口推計」 |
| REG-019 | https://www.chisou.go.jp/sousei/ | 成功 | 地方創生（内閣府・内閣官房 総合サイト） |
| REG-021 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/c-gyousei/2001/kaso/kasomain0.htm | 成功 | 総務省「過疎対策」 |
| REG-036 | https://www.stat.go.jp/data/cpi/ | 成功 | 総務省統計局「消費者物価指数（CPI）」 |
| REG-046 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/bunken/gaiyou.html | 成功 | 総務省 自治行政局「地方自治制度の概要」 |
| REG-047 | https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czais.html | 成功 | 総務省 自治税務局「地方税の概要」 |
| REG-053 | https://www.soumu.go.jp/denshijiti/digital_transformation_portal/index.html | 成功 | 総務省 地域DXポータルサイト |

## C 保留理由（逐条）

- **REG-011 地形**：国土地理院为测绘机构，无「地形」单页定义（地形分類/地形特性情報等为分散专题）。
- **REG-014 高齢化率 / REG-023 昼夜間人口比率 / REG-060 地域差**：統計局统计指标泛称，无单页定义页。
- **REG-018 人口減少**：統計局/内閣府均无单页定义页。
- **REG-020 東京一極集中 / REG-024 地域経済 / REG-034 企業誘致 / REG-052 地方分権 / REG-058 移住 / REG-064 地域おこし**：内閣府政策课题/改革泛称，无单页覆盖。
- **REG-025 産業構造 / REG-026 第一次産業 / REG-027 第二次産業 / REG-028 第三次産業**：産業分類泛称，総務省統計局/経産省无单页定义页。
- **REG-030 農業 / REG-032 製造業 / REG-033 地場産業 / REG-042 商業施設 / REG-056 補助金**：農林水産省/経産省政策与统计分散，无单页定义页。
- **REG-048 地方交付税 / REG-057 条例**：総務省制度说明分散，未确认到单页权威定义页。
- **REG-051 移住支援金**：制度细节按自治体而异，无全国统一单页定义。

## D 纠错记录

本主题「部分核验」非门户条目中发现**批量同源 URL 疑似错配**，因需逐条重新定向核验、超出本组门户核验范围，**未在本批改写**，标注待后续处理：

| 条目 | 现 URL | 疑似错配原因 |
|---|---|---|
| REG-006 地方 / REG-007 関東地方 / REG-008 近畿地方 / REG-009 九州地方 / REG-022 都市計画 / REG-035 家賃相場 / REG-037 公共交通 / REG-038 鉄道 / REG-039 路線バス / REG-043 公園 / REG-044 上下水道 / REG-045 生活インフラ / REG-059 住みやすさ / REG-061 田舎暮らし / REG-062 交通不便 / REG-063 災害リスク / REG-065 二拠点生活 / REG-068 住環境（共 18 条） | https://www.mlit.go.jp/totikensangyo/totikensangyo_fr4_000044.html | 该页实为国土交通省「都道府県地価調査」，与上述词条均不切題；疑为前批批量同源赋值 |
| REG-012 気候 | https://www.jma.go.jp/jma/kishou/know/bosai/keiho-update2026/index.html | 该页为気象庁「新たな防災気象情報」，非「気候」定义页 |
| REG-069 求人件数 | https://www.mhlw.go.jp/toukei/list/33-20.html | 该页为厚生労働省「人口動態統計」，非「求人件数/職業安定統計」 |

> 建议：由主会话或后续批次对上述 20 条逐条定向核验并回填。

## E 自检结论

```
[verify-update] 读取 18 行 → 更新 12 / 未匹配 0 / 非法 0；词库共 69 条（已更新至 v1.5）
[check] data/13-regional-info/terms.md：共 69 条，版本 v1.5
[check] 结论：通过（0 项错误 / 0 项警告）
```

## F 提交短码与文件清单

- 提交短码：`a57d702`（`feat(vocab): 07/13/11/17 门户 URL 核验深化`）。
- 文件清单：
  - `engine/vocabulary/data/13-regional-info/terms.md`
  - `engine/vocabulary/data/13-regional-info/imports/2026-11-19_核验深化.md`
  - `engine/vocabulary/data/13-regional-info/exports/13-regional-info_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/13-regional-info.md`
