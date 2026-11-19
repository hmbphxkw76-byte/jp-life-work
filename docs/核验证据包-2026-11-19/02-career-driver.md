# 核验证据包 — 02-career-driver（2026-11-19）

> 组 5 / 分支 `task/deepen-g5-dcdf4009` / worktree `.worktrees/deepen-g5`。
> 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页；不动核验状态 / 置信度）。
> 范围：本主题「部分核验 且 来源URL 门户级」共 **5** 条，全量处置（升级 2 / 保留 3 / 纠错 0）。

## A 覆盖表（5 条全量）

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| CDR-022 | 年収 | 升级 | https://www.nta.go.jp/publication/statistics/kokuzeicho/minkan/top.htm | web_fetch 成功；标题「民間給与実態統計調査｜国税庁」，含年間給与の実態 |
| CDR-031 | 危険物取扱者 | 保留 | https://www.fdma.go.jp/ | 未確認到消防庁单页覆盖（危険物取扱者試験由都道府県实施），保留门户 |
| CDR-058 | 個人事業主 | 升级 | https://www.nta.go.jp/taxes/tetsuzuki/shinsei/annai/shinkoku/annai/04.htm | web_fetch 成功；标题「A1-5 個人事業の開業届出・廃業届出等手続｜国税庁」 |
| CDR-081 | 危険物乙種第4類 | 保留 | https://www.fdma.go.jp/ | 未確認到消防庁单页覆盖（同上），保留门户 |
| CDR-084 | 教習所指導員 | 保留 | https://www.npa.go.jp/ | 未確認到警察庁/公安委員会单页覆盖（指定驾校内部指导资格），保留门户 |

## B 升级证据（2 条）

| ID | 目标 URL | web_fetch | 页面标题 |
|---|---|---|---|
| CDR-022 | https://www.nta.go.jp/publication/statistics/kokuzeicho/minkan/top.htm | 成功 | 民間給与実態統計調査｜国税庁 |
| CDR-058 | https://www.nta.go.jp/taxes/tetsuzuki/shinsei/annai/shinkoku/annai/04.htm | 成功 | A1-5　個人事業の開業届出・廃業届出等手続｜国税庁 |

## C 保留理由（3 条，逐条）

- **危険物取扱者资格（消防庁，2 条）**：CDR-031（危険物取扱者）、CDR-081（危険物乙種第4類）——未確認到消防庁单页覆盖（该考试由都道府県实施，消防庁站点无对应资格说明页），保留门户。
- **教習所指導員（公安委員会，1 条）**：CDR-084（教習所指導員）——未確認到警察庁/公安委員会单页覆盖（指定自動車教習所の内部指导资格），保留门户。

## D 纠错记录

- 本次无门户级错配纠错。
- 附带说明（非门户级，未改动）：CDR-008/024/025/026/027/028/033/082/083/085 的来源URL 为 `mp.weixin.qq.com`（中文微信公众号），非日本官方域名；因非门户级且需另行核验官方页（警察庁等），本批次未擅自改写，留待主会话统一处置。

### D.1 N2 专项复核补充（2026-11-19，closure-b）

原 D 节记录的 10 条 mp.weixin.qq.com 微信公众号来源逐条复核：非日本官方域名；本会话 web_fetch 返回「环境异常」验证拦截，无法实取。处置：纠错回落警察庁官方门户 https://www.npa.go.jp/ 并标「未核实（官方门户 CDN 拦截）」。涉及 CDR-008 / 024 / 025 / 026 / 027 / 028 / 033 / 082 / 083 / 085（10 条）。

### D.2 未核实项浏览器核验（2026-11-19，closure-unverified）

浏览器实测 `www.npa.go.jp` 门户与深链均返回 CloudFront 403（同 01 证据，2026-11-19）。处置（2026-11-19 用户确认，保障信息质量）：11 条**已删除**（无法核验来源的条目不保留）；词库 104 → 93（v1.10），`business-config.md` 区块同步删除，`exports/` 重生成。涉及 CDR-008 / 024 / 025 / 026 / 027 / 028 / 033 / 082 / 083 / 084 / 085（含任务书枚举遗漏的 CDR-084：来源 公安委員会、URL 同为 npa.go.jp，按「整批」口径一并处置）；上表为删除前状态留痕。

## E 自检结论

```
$ python engine/vocabulary/script/vocab_tool.py verify-update --topic 02-career-driver --file engine/vocabulary/data/02-career-driver/imports/2026-11-19_核验深化.md
[verify-update] 读取 2 行 → 更新 2 / 未匹配 0 / 非法 0；词库共 104 条（已更新至 v1.6）

$ python engine/vocabulary/script/vocab_tool.py export --topic 02-career-driver --format all
[export] data/02-career-driver/exports/02-career-driver_2026-11-19_export.json（104 条，v1.6）
[export] data/02-career-driver/exports/02-career-driver_2026-11-19_export.csv（104 条，v1.6）
[export] data/02-career-driver/exports/02-career-driver_2026-11-19_export.jsonl（104 条，v1.6）

$ python engine/vocabulary/script/vocab_tool.py check --topic 02-career-driver
[check] data/02-career-driver/terms.md：共 104 条，版本 v1.6
[check] 结论：通过（0 项错误 / 0 项警告）
```

## F 提交短码与文件清单

- 提交短码：见本文件提交后回填。
- 变更文件：
  - `engine/vocabulary/data/02-career-driver/terms.md`（v1.6，2 条 source_url 更新）
  - `engine/vocabulary/data/02-career-driver/imports/2026-11-19_核验深化.md`（新增，2 行）
  - `engine/vocabulary/data/02-career-driver/exports/02-career-driver_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/02-career-driver.md`（本文件）
