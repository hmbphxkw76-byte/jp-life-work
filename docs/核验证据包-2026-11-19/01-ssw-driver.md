# 核验证据包 — 01-ssw-driver（2026-11-19）

> 组 5 / 分支 `task/deepen-g5-dcdf4009` / worktree `.worktrees/deepen-g5`。
> 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页；不动核验状态 / 置信度）。
> 范围：本主题「部分核验 且 来源URL 门户级」共 **33** 条，全量处置（升级 17 / 保留 16 / 纠错 0）。

## A 覆盖表（33 条全量）

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| SSW-025 | 月給 | 保留 | https://www.mhlw.go.jp/ | 宽泛工资术语，无单页定义覆盖 |
| SSW-026 | 手取り | 保留 | https://www.mhlw.go.jp/ | 宽泛工资术语，无单页定义覆盖 |
| SSW-027 | 歩合給 | 保留 | https://www.mhlw.go.jp/ | 宽泛工资术语，无单页定义覆盖 |
| SSW-028 | 固定残業代 | 保留 | https://www.mhlw.go.jp/ | 宽泛工资术语，无单页定义覆盖 |
| SSW-029 | 時間外労働 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/roudouzikan/index.html | web_fetch 成功；标题「労働時間・休日 ｜厚生労働省」 |
| SSW-030 | 深夜割増 | 保留 | https://www.mhlw.go.jp/ | 宽泛工资术语，未确认到单页定义覆盖 |
| SSW-031 | 社会保険 | 保留 | https://www.mhlw.go.jp/ | 宽泛制度术语，无单页定义覆盖 |
| SSW-032 | 最低賃金 | 升级 | https://saiteichingin.mhlw.go.jp/ | web_fetch 成功；标题「最低賃金制度」（厚生労働省特設サイト） |
| SSW-033 | 36協定 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/roudouzikan/index.html | web_fetch 成功；同页含「時間外労働協定（３６協定）」 |
| SSW-034 | 改善基準告示 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/gyosyu/roudoujouken05/index.html | web_fetch 成功；标题「自動車運転者の労働時間等の改善のための基準（改善基準告示） ｜厚生労働省」 |
| SSW-035 | 拘束時間 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/gyosyu/roudoujouken05/index.html | web_fetch 成功；同页含拘束時間上限与遵守确认软件 |
| SSW-038 | フォークリフト | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/roudoukijun/anzeneisei10/qualificaton_education.html | web_fetch 成功；标题「労働安全衛生関係の免許・資格・技能講習・特別教育など｜厚生労働省」 |
| SSW-039 | 玉掛け | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/roudoukijun/anzeneisei10/qualificaton_education.html | web_fetch 成功；同页含技能講習 / 就業制限一览 |
| SSW-048 | JFT-Basic | 保留 | https://www.jpf.go.jp/ | jft-basic.jp 实取失败（无内容返回），无 web_fetch 成功记录 |
| SSW-052 | 健康診断 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/index.html | web_fetch 成功；标题「安全・衛生 ｜厚生労働省」，含健康診断概要 |
| SSW-055 | 労働安全衛生法 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/index.html | web_fetch 成功；同页含「労働安全衛生法の概要」 |
| SSW-056 | 危険物取扱者 | 保留 | https://www.fdma.go.jp/ | 未確認到消防庁单页覆盖（危険物取扱者試験由都道府県实施） |
| SSW-060 | 送金 | 保留 | https://www.fsa.go.jp/ | 宽泛生活金融术语，未確認到金融庁单页覆盖 |
| SSW-061 | 銀行口座 | 保留 | https://www.fsa.go.jp/ | 宽泛生活金融术语，未確認到金融庁单页覆盖 |
| SSW-064 | 確定申告 | 升级 | https://www.nta.go.jp/taxes/shiraberu/shinkoku/kakutei.htm | web_fetch 成功；标题「所得税の確定申告｜国税庁」 |
| SSW-065 | 国民健康保険 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/koukikourei/index_00002.html | web_fetch 成功；标题「国民健康保険制度 ｜厚生労働省」 |
| SSW-067 | 相談窓口 | 保留 | https://www.mhlw.go.jp/ | 宽泛术语，无单页定义覆盖 |
| SSW-081 | 厚生年金 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/nenkin/nenkin/ | web_fetch 成功；标题「年金・日本年金機構関係 ｜厚生労働省」，含公的年金（国民年金・厚生年金） |
| SSW-082 | 雇用保険 | 升级 | https://www.mhlw.go.jp/seisakunitsuite/bunya/koyou_roudou/roudoukijun/hoken/tokusetusaito.html | web_fetch 成功；标题「労災保険×雇用保険 労働保険特設サイト」（厚生労働省） |
| SSW-083 | 労災保険 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/rousai/gaiyou.html | web_fetch 成功；标题「労災保険制度の概要、給付の請求手続等 ｜厚生労働省」 |
| SSW-084 | 年次有給休暇 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/roudouzikan/index.html | web_fetch 成功；同页含「年次有給休暇」付与日数规定 |
| SSW-087 | 危険物乙種第4類 | 保留 | https://www.fdma.go.jp/ | 未確認到消防庁单页覆盖 |
| SSW-096 | 安全衛生教育 | 升级 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/roudoukijun/anzeneisei10/qualificaton_education.html | web_fetch 成功；同页含「安全衛生教育」条款与教育内容 |
| SSW-101 | 国際送金 | 保留 | https://www.fsa.go.jp/ | 宽泛生活金融术语，未確認到金融庁单页覆盖 |
| SSW-102 | 年末調整 | 升级 | https://www.nta.go.jp/users/gensen/nencho/index/gimusya.htm | web_fetch 成功；标题「源泉徴収義務者（給与の支払者）の方へ（令和８年分）｜国税庁」，含年末調整 |
| SSW-104 | 賃金水準 | 保留 | https://www.mhlw.go.jp/ | 统计/行情术语，无单页定义覆盖 |
| SSW-105 | 運輸業賃金 | 保留 | https://www.mhlw.go.jp/ | 统计/行情术语，无单页定义覆盖 |
| SSW-108 | 自賠責保険 | 保留 | https://www.fsa.go.jp/ | 未確認到金融庁单页覆盖（自賠責制度官网为国土交通省口径，来源字段不匹配，未改写） |

## B 升级证据（17 条）

| ID | 目标 URL | web_fetch | 页面标题 |
|---|---|---|---|
| SSW-029 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/roudouzikan/index.html | 成功 | 労働時間・休日 ｜厚生労働省 |
| SSW-032 | https://saiteichingin.mhlw.go.jp/ | 成功 | 最低賃金制度 |
| SSW-033 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/roudouzikan/index.html | 成功 | 労働時間・休日 ｜厚生労働省 |
| SSW-034 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/gyosyu/roudoujouken05/index.html | 成功 | 自動車運転者の労働時間等の改善のための基準（改善基準告示） ｜厚生労働省 |
| SSW-035 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/gyosyu/roudoujouken05/index.html | 成功 | 自動車運転者の労働時間等の改善のための基準（改善基準告示） ｜厚生労働省 |
| SSW-038 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/roudoukijun/anzeneisei10/qualificaton_education.html | 成功 | 労働安全衛生関係の免許・資格・技能講習・特別教育など｜厚生労働省 |
| SSW-039 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/roudoukijun/anzeneisei10/qualificaton_education.html | 成功 | 労働安全衛生関係の免許・資格・技能講習・特別教育など｜厚生労働省 |
| SSW-052 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/index.html | 成功 | 安全・衛生 ｜厚生労働省 |
| SSW-055 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/anzen/index.html | 成功 | 安全・衛生 ｜厚生労働省 |
| SSW-064 | https://www.nta.go.jp/taxes/shiraberu/shinkoku/kakutei.htm | 成功 | 所得税の確定申告｜国税庁 |
| SSW-065 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/koukikourei/index_00002.html | 成功 | 国民健康保険制度 ｜厚生労働省 |
| SSW-081 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/nenkin/nenkin/ | 成功 | 年金・日本年金機構関係 ｜厚生労働省 |
| SSW-082 | https://www.mhlw.go.jp/seisakunitsuite/bunya/koyou_roudou/roudoukijun/hoken/tokusetusaito.html | 成功 | 労災保険×雇用保険 労働保険特設サイト（厚生労働省） |
| SSW-083 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/rousai/gaiyou.html | 成功 | 労災保険制度の概要、給付の請求手続等 ｜厚生労働省 |
| SSW-084 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/roudouzikan/index.html | 成功 | 労働時間・休日 ｜厚生労働省 |
| SSW-096 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/roudoukijun/anzeneisei10/qualificaton_education.html | 成功 | 労働安全衛生関係の免許・資格・技能講習・特別教育など｜厚生労働省 |
| SSW-102 | https://www.nta.go.jp/users/gensen/nencho/index/gimusya.htm | 成功 | 源泉徴収義務者（給与の支払者）の方へ（令和８年分）｜国税庁 |

## C 保留理由（16 条，逐条）

- **宽泛工资/劳动术语（厚生労働省，9 条）**：SSW-025（月給）、SSW-026（手取り）、SSW-027（歩合給）、SSW-028（固定残業代）、SSW-030（深夜割増）、SSW-031（社会保険）、SSW-067（相談窓口）、SSW-104（賃金水準）、SSW-105（運輸業賃金）——均未确认到覆盖各词的单页定义页，保留门户。
- **实取失败（1 条）**：SSW-048（JFT-Basic）——`https://www.jft-basic.jp/` 多次 `web_fetch` 无内容返回，无成功记录，保留门户。
- **消防庁危険物资格（2 条）**：SSW-056（危険物取扱者）、SSW-087（危険物乙種第4類）——未確認到消防庁单页覆盖（考试由都道府県实施），保留门户。
- **金融庁生活金融（4 条）**：SSW-060（送金）、SSW-061（銀行口座）、SSW-101（国際送金）、SSW-108（自賠責保険）——未確認到金融庁单页覆盖，保留门户。

## D 纠错记录

- 本次无门户级错配纠错。
- 附带说明（非门户级，未改动）：SSW-036/037/043/054/057/068/086/092/093/094/095 的来源URL 为 `drivey.jp`（私人博客），非官方域名；因非门户级且需另行核验官方页（警察庁等），本批次未擅自改写，留待主会话统一处置。

### D.1 N2 专项复核补充（2026-11-19，closure-b）

原 D 节记录的 11 条 drivey.jp 私人博客来源逐条复核：该域名非官方；本会话 web_fetch 可达，内容仅对外免切替相关表述切題，其余词条不切題。官方同源机构（警察庁）门户 https://www.npa.go.jp/ 经 web_fetch 返回 403（CloudFront 地域拦截），无法实取具体页。处置：纠错回落官方门户并标「未核实（CDN 拦截）」。涉及 SSW-036 / 037 / 043 / 054 / 057 / 068 / 086 / 092 / 093 / 094 / 095（11 条）。

## E 自检结论

```
$ python engine/vocabulary/script/vocab_tool.py verify-update --topic 01-ssw-driver --file engine/vocabulary/data/01-ssw-driver/imports/2026-11-19_核验深化.md
[verify-update] 读取 17 行 → 更新 17 / 未匹配 0 / 非法 0；词库共 109 条（已更新至 v1.7）

$ python engine/vocabulary/script/vocab_tool.py export --topic 01-ssw-driver --format all
[export] data/01-ssw-driver/exports/01-ssw-driver_2026-11-19_export.json（109 条，v1.7）
[export] data/01-ssw-driver/exports/01-ssw-driver_2026-11-19_export.csv（109 条，v1.7）
[export] data/01-ssw-driver/exports/01-ssw-driver_2026-11-19_export.jsonl（109 条，v1.7）

$ python engine/vocabulary/script/vocab_tool.py check --topic 01-ssw-driver
[check] data/01-ssw-driver/terms.md：共 109 条，版本 v1.7
[check] 结论：通过（0 项错误 / 0 项警告）
```

## F 提交短码与文件清单

- 提交短码：见本文件提交后回填（commit `feat(vocab): 01 门户 URL 核验深化`）。
- 变更文件：
  - `engine/vocabulary/data/01-ssw-driver/terms.md`（v1.7，17 条 source_url 更新）
  - `engine/vocabulary/data/01-ssw-driver/imports/2026-11-19_核验深化.md`（新增，17 行）
  - `engine/vocabulary/data/01-ssw-driver/exports/01-ssw-driver_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/01-ssw-driver.md`（本文件）
