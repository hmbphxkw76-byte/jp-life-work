# 核验证据包：19-safety-disaster（2026-11-19）

> 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页）。
> 范围：本主题「部分核验 且 来源URL 门户级」条目 **29 条**（门户级 = 仅域名/根路径）。
> 处置合计：**升级 6 / 保留 23 / 纠错 0**。不动核验状态、不动置信度。

## A 覆盖表

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| SFD-009 | 情報難民 | 保留 | https://www.soumu.go.jp/ | 宽泛术语；未确认到総務省单页覆盖 |
| SFD-011 | 特殊诈欺 | 保留 | https://www.npa.go.jp/ | 警察庁官网受 CloudFront 地域限制，web_fetch 无法实取 |
| SFD-012 | 生活安全 | 保留 | https://www.npa.go.jp/ | 同上 |
| SFD-013 | 犯罪统计 | 保留 | https://www.npa.go.jp/ | 同上 |
| SFD-014 | 振り込め詐欺 | 保留 | https://www.npa.go.jp/ | 同上 |
| SFD-015 | 领事保护 | 保留 | https://www.mofa.go.jp/ | 外務省官网受 Akamai 限制，web_fetch 无法实取 |
| SFD-016 | 在外公館 | 保留 | https://www.mofa.go.jp/ | 同上 |
| SFD-017 | 海外安全情报 | 升级 | https://www.anzen.mofa.go.jp/ | 外務省「海外安全ホームページ」官方页 |
| SFD-018 | パスポート | 保留 | https://www.mofa.go.jp/ | 外務省官网受 Akamai 限制，web_fetch 无法实取 |
| SFD-019 | 110 | 保留 | https://www.npa.go.jp/ | 警察庁官网受 CloudFront 地域限制，web_fetch 无法实取 |
| SFD-024 | 非常用持ち出し袋 | 保留 | https://www.cao.go.jp/ | 宽泛备灾术语；内閣府防災内容已迁移，无单页定义页 |
| SFD-025 | 備蓄 | 保留 | https://www.cao.go.jp/ | 同上 |
| SFD-026 | 家具固定 | 保留 | https://www.cao.go.jp/ | 同上 |
| SFD-031 | 土砂災害 | 保留 | https://www.mlit.go.jp/ | 宽泛灾害术语；国交省无单页定义页 |
| SFD-033 | 洪水 | 保留 | https://www.mlit.go.jp/ | 同上 |
| SFD-040 | 治安 | 保留 | https://www.npa.go.jp/ | 宽泛术语 + 警察庁官网无法实取 |
| SFD-052 | 防災の手引き | 升级 | https://www.kantei.go.jp/jp/headline/bousai/index.html | 首相官邸「防災の手引き」官方页（令和8年10月更新） |
| SFD-053 | ハザードマップ | 升级 | https://disaportal.gsi.go.jp/ | 国交省・国土地理院「ハザードマップポータルサイト」 |
| SFD-058 | 川の防災情報 | 升级 | https://www.river.go.jp/portal/ | 国交省「川の防災情報」公式页 |
| SFD-059 | 情報コーディネーター | 保留 | https://www.soumu.go.jp/ | 宽泛术语；未确认到単页覆盖 |
| SFD-060 | 情報難民ゼロ | 保留 | https://www.soumu.go.jp/ | 同上 |
| SFD-066 | マイナポータル | 保留 | https://www.mofa.go.jp/ | 外務省官网受 Akamai 限制，web_fetch 无法实取 |
| SFD-067 | ORRネット | 升级 | https://www.ezairyu.mofa.go.jp/RRnet/index.html | 外務省オンライン在留届（ORRネット）公式页 |
| SFD-068 | 在留届 | 升级 | https://www.ezairyu.mofa.go.jp/RRnet/index.html | 在留届電子届出システム公式页 |
| SFD-069 | マイナンバーカード | 保留 | https://www.mofa.go.jp/ | 外務省官网受 Akamai 限制，web_fetch 无法实取 |
| SFD-070 | ローリングストック | 保留 | https://www.cao.go.jp/ | 宽泛备灾术语；无单页定义页 |
| SFD-071 | 感震断路器 | 保留 | https://www.cao.go.jp/ | 同上 |
| SFD-072 | ガラス飛散防止膜 | 保留 | https://www.cao.go.jp/ | 同上 |
| SFD-075 | 子供の電話詐欺 | 保留 | https://www.npa.go.jp/ | 警察庁官网受 CloudFront 地域限制，web_fetch 无法实取 |

## B 升级证据

| 目标 URL | web_fetch 结果 | 页面标题 |
|---|---|---|
| https://www.anzen.mofa.go.jp/ | 成功 | 外務省 海外安全ホームページ |
| https://www.kantei.go.jp/jp/headline/bousai/index.html | 成功 | 防災の手引き｜災害への備えと身の守り方｜首相官邸 |
| https://disaportal.gsi.go.jp/ | 成功 | ハザードマップポータルサイト |
| https://www.river.go.jp/portal/ | 成功 | 川の防災情報 - 国土交通省 |
| https://www.ezairyu.mofa.go.jp/RRnet/index.html | 成功 | トップページ｜在留届（オンライン在留届 ORRネット） |

## C 保留理由（逐条）

- **警察庁 7 条**（SFD-011/012/013/014/019/040/075）：警察庁官网（npa.go.jp）受 CloudFront 地域限制，web_fetch 返回 403，无法实取任何具体页；其中「治安」为宽泛术语。
- **外務省 5 条**（SFD-015/016/018/066/069）：外務省官网（mofa.go.jp）受 Akamai 限制，web_fetch 返回 Access Denied，无法实取具体页。
- **内閣府 6 条**（SFD-024/025/026/070/071/072）：宽泛备灾术语；内閣府防灾内容已迁移至防災庁，无「单页覆盖」的权威定义页。
- **総務省 3 条**（SFD-009/059/060）：宽泛术语/项目名，未确认到単页覆盖的官方定义页。
- **国交省 2 条**（SFD-031 土砂災害、SFD-033 洪水）：宽泛灾害术语；国交省无单页定义页。

## D 纠错记录

无。本主题所有「部分核验」条目的 URL 与来源机构/词条方向一致，未发现错配。

## E 自检结论

```
[verify-update] 读取 6 行 → 更新 6 / 未匹配 0 / 非法 0；词库共 75 条（已更新至 v1.5）
[check] data/19-safety-disaster/terms.md：共 75 条，版本 v1.5
  [warn] SFD-049: 别名「高潮」与自身词条/别名重复（冗余，建议清理）
  [warn] SFD-071: 别名「感震断路器」与自身词条/别名重复（冗余，建议清理）
[check] 结论：通过（0 项错误 / 2 项警告）
```

说明：上述 2 项警告为**既有别名冗余**（SFD-049「高潮」、SFD-071「感震断路器」别名与词条重复），非本次来源URL变更引入；按任务要求原文记录，未改动词条/别名。

## F 提交短码与文件清单

- 提交短码：`4b1ce78`（`feat(vocab): 05/19/10/16 门户 URL 核验深化`）。
- 文件清单：
  - `engine/vocabulary/data/19-safety-disaster/terms.md`
  - `engine/vocabulary/data/19-safety-disaster/imports/2026-11-19_核验深化.md`
  - `engine/vocabulary/data/19-safety-disaster/exports/19-safety-disaster_2026-11-19_export.{json,csv,jsonl}`
