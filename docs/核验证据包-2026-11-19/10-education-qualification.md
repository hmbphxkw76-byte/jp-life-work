# 核验证据包：10-education-qualification（2026-11-19）

> 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页）。
> 范围：本主题「部分核验 且 来源URL 门户级」条目 **17 条**（门户级 = 仅域名/根路径）。
> 处置合计：**升级 4 / 保留 13 / 纠错 0**。不动核验状态、不动置信度。

## A 覆盖表

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| EDU-014 | 国家資格 | 保留 | https://www.mhlw.go.jp/ | 宽泛术语；厚労省无单页定义页 |
| EDU-017 | 業務独占資格 | 保留 | https://www.mhlw.go.jp/ | 同上 |
| EDU-018 | 名称独占資格 | 保留 | https://www.mhlw.go.jp/ | 同上 |
| EDU-019 | 運転免許 | 保留 | https://www.npa.go.jp/ | 警察庁官网受 CloudFront 地域限制，web_fetch 无法实取 |
| EDU-020 | フォークリフト | 保留 | https://www.mhlw.go.jp/ | 宽泛资格术语；厚労省无单页定义页 |
| EDU-022 | 運行管理者 | 保留 | https://www.mlit.go.jp/ | 宽泛资格术语；国交省无单页定义页 |
| EDU-023 | 介護福祉士 | 保留 | https://www.mhlw.go.jp/ | 厚労省仅有「資格・試験情報」总览页，非本词条单页 |
| EDU-025 | ITパスポート | 升级 | https://www.ipa.go.jp/shiken/kubun/ip.html | IPA「ITパスポート試験」官方页 |
| EDU-030 | 実技試験 | 保留 | https://www.mhlw.go.jp/ | 宽泛考试形式术语 |
| EDU-041 | 奨学金 | 升级 | https://www.jasso.go.jp/shogakukin/index.html | JASSO「奨学金」官方页 |
| EDU-042 | 給付型奨学金 | 升级 | https://www.jasso.go.jp/shogakukin/about/index.html | JASSO「奨学金制度の種類と概要」（含給付型） |
| EDU-043 | 貸与型奨学金 | 升级 | https://www.jasso.go.jp/shogakukin/about/index.html | JASSO「奨学金制度の種類と概要」（含貸与型） |
| EDU-048 | アルバイト | 保留 | https://www.mhlw.go.jp/ | 宽泛术语 |
| EDU-061 | 資格取得 | 保留 | https://www.mhlw.go.jp/ | 宽泛术语 |
| EDU-062 | キャリア形成 | 保留 | https://www.mhlw.go.jp/ | 宽泛术语 |
| EDU-064 | 学費相談 | 保留 | https://www.jasso.go.jp/ | 宽泛场景术语；JASSO 无单页定义页 |
| EDU-069 | 外免切替 | 保留 | https://www.npa.go.jp/ | 警察庁官网受 CloudFront 地域限制，web_fetch 无法实取 |

## B 升级证据

| 目标 URL | web_fetch 结果 | 页面标题 |
|---|---|---|
| https://www.ipa.go.jp/shiken/kubun/ip.html | 成功 | ITパスポート試験 \| 試験情報 \| IPA 独立行政法人 情報処理推進機構 |
| https://www.jasso.go.jp/shogakukin/index.html | 成功 | 奨学金 \| JASSO |
| https://www.jasso.go.jp/shogakukin/about/index.html | 成功 | 奨学金制度の種類と概要 \| JASSO |

## C 保留理由（逐条）

- **厚生労働省 9 条**（EDU-014/017/018/020/023/030/048/061/062）：宽泛资格/考试/场景术语；厚労省无对应「单页覆盖」的权威定义页（介護福祉士仅有「資格・試験情報」总览页）。
- **警察庁 2 条**（EDU-019 運転免許、EDU-069 外免切替）：警察庁官网受 CloudFront 地域限制，web_fetch 返回 403，无法实取。
- **JASSO 1 条**（EDU-064 学費相談）：宽泛场景术语；JASSO 无单页定义页。
- **国土交通省 1 条**（EDU-022 運行管理者）：宽泛资格术语；国交省无单页定义页。

## D 纠错记录

无。本主题所有「部分核验」条目的 URL 与来源机构/词条方向一致，未发现错配。

## E 自检结论

```
[verify-update] 读取 4 行 → 更新 4 / 未匹配 0 / 非法 0；词库共 70 条（已更新至 v1.4）
[check] data/10-education-qualification/terms.md：共 70 条，版本 v1.4
[check] 结论：通过（0 项错误 / 0 项警告）
```

## F 提交短码与文件清单

- 提交短码：见本文件同目录提交后回填（commit `feat(vocab): 05/19/10/16 门户 URL 核验深化`）。
- 文件清单：
  - `engine/vocabulary/data/10-education-qualification/terms.md`
  - `engine/vocabulary/data/10-education-qualification/imports/2026-11-19_核验深化.md`
  - `engine/vocabulary/data/10-education-qualification/exports/10-education-qualification_2026-11-19_export.{json,csv,jsonl}`
