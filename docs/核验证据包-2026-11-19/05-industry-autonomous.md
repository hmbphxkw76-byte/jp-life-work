# 核验证据包：05-industry-autonomous（2026-11-19）

> 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页）。
> 范围：本主题「部分核验 且 来源URL 门户级」条目 **49 条**（门户级 = 仅域名/根路径）。
> 处置合计：**升级 14 / 保留 35 / 纠错 0**。不动核验状态、不动置信度。

## A 覆盖表

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| AUT-001 | 自動運転レベル | 升级 | https://saemobilus.sae.org/content/J3016_202104 | J3016 官方页定义 Level 0–5 |
| AUT-002 | レベル0 | 升级 | https://saemobilus.sae.org/content/J3016_202104 | 同上 |
| AUT-003 | レベル1 | 升级 | https://saemobilus.sae.org/content/J3016_202104 | 同上 |
| AUT-004 | レベル2 | 升级 | https://saemobilus.sae.org/content/J3016_202104 | 同上 |
| AUT-005 | レベル3 | 升级 | https://saemobilus.sae.org/content/J3016_202104 | 同上 |
| AUT-006 | レベル4 | 升级 | https://saemobilus.sae.org/content/J3016_202104 | 同上 |
| AUT-007 | レベル5 | 升级 | https://saemobilus.sae.org/content/J3016_202104 | 同上 |
| AUT-008 | ODD | 升级 | https://saemobilus.sae.org/content/J3016_202104 | J3016 定义 ODD |
| AUT-009 | 動的運転タスク | 升级 | https://saemobilus.sae.org/content/J3016_202104 | J3016 定义 DDT |
| AUT-010 | フォールバック | 升级 | https://saemobilus.sae.org/content/J3016_202104 | J3016 定义 DDT fallback |
| AUT-013 | LiDAR | 保留 | https://www.jsae.or.jp/ | 非政府机构（自動車技術会）；通用传感器术语，无单页覆盖 |
| AUT-014 | ミリ波レーダー | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-015 | 車載カメラ | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-016 | 超音波センサー | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-017 | GNSS | 保留 | https://www.gsi.go.jp/ | 宽泛定位术语；国土地理院官方页为大地测量业务，与词条（车载定位）不切题 |
| AUT-018 | IMU | 保留 | https://www.jsae.or.jp/ | 非政府机构；通用传感器术语 |
| AUT-019 | 車載ECU | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-020 | アクチュエータ | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-021 | ステアリング・バイ・ワイヤ | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-022 | ブレーキ・バイ・ワイヤ | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-023 | センサーキャリブレーション | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-024 | 知覚 | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-025 | 物体検出 | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-026 | セマンティックセグメンテーション | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-027 | センサーフュージョン | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-028 | 予測 | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-029 | 経路計画 | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-030 | 制御 | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-031 | SLAM | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-035 | モデル予測制御 | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-042 | SAE J3016 | 升级 | https://saemobilus.sae.org/content/J3016_202104 | J3016 官方标准页 |
| AUT-043 | ISO 26262 | 保留 | https://www.iso.org/ | ISO 官方标准页受 Cloudflare 校验保护，web_fetch 无法实取；无其他官方单页 |
| AUT-044 | ISO 21448 | 保留 | https://www.iso.org/ | 同上 |
| AUT-045 | UN-R157 | 保留 | https://unece.org/ | UNECE 官网受 Cloudflare 校验保护，web_fetch 无法实取 |
| AUT-056 | 保険 | 保留 | https://www.fsa.go.jp/ | 宽泛术语；金融庁无单页覆盖 |
| AUT-065 | 過疎地 | 升级 | https://www.soumu.go.jp/main_sosiki/jichi_gyousei/c-gyousei/2001/kaso/kasomain0.htm | 総務省「過疎対策」官方页 |
| AUT-069 | テイクオーバー | 升级 | https://saemobilus.sae.org/content/J3016_202104 | J3016 定义接管相关术语 |
| AUT-070 | MRM | 升级 | https://saemobilus.sae.org/content/J3016_202104 | J3016 定义最小风险机动 |
| AUT-071 | システムレダンダンシー | 保留 | https://www.iso.org/ | 宽泛术语 + ISO 页无法实取 |
| AUT-072 | フェイルセーフ | 保留 | https://www.iso.org/ | 同上 |
| AUT-073 | フェールオペレーショナル | 保留 | https://www.iso.org/ | 同上 |
| AUT-076 | ステレオカメラ | 保留 | https://www.jsae.or.jp/ | 非政府机构；通用传感器术语 |
| AUT-077 | RTK-GNSS | 保留 | https://www.gsi.go.jp/ | 宽泛定位术语；无切题官方单页 |
| AUT-080 | 電子制御ブレーキ | 保留 | https://www.jsae.or.jp/ | 非政府机构；通用部件术语 |
| AUT-085 | 車線認識 | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-086 | 縦横制御 | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-087 | 障害物回避 | 保留 | https://www.jsae.or.jp/ | 同上 |
| AUT-092 | UN-R171 | 保留 | https://unece.org/ | UNECE 官网受 Cloudflare 校验保护，web_fetch 无法实取 |
| AUT-093 | ISO 34502 | 保留 | https://www.iso.org/ | ISO 官方标准页无法实取 |

## B 升级证据

| 目标 URL | web_fetch 结果 | 页面标题 |
|---|---|---|
| https://saemobilus.sae.org/content/J3016_202104 | 成功 | J3016_202104: Taxonomy and Definitions for Terms Related to Driving Automation Systems for On-Road Motor Vehicles - Recommended Practice |
| https://www.soumu.go.jp/main_sosiki/jichi_gyousei/c-gyousei/2001/kaso/kasomain0.htm | 成功 | 過疎対策（総務省） |

## C 保留理由（逐条）

- **JSAE（自動車技術会）24 条**（AUT-013/014/015/016/018/019/020/021/022/023/024/025/026/027/028/029/030/031/035/076/080/085/086/087）：非政府机构；均为通用汽车工程术语，机构无「单页覆盖」的权威定义页，门户即诚实粒度。
- **国土地理院 2 条**（AUT-017 GNSS、AUT-077 RTK-GNSS）：宽泛定位术语；国土地理院官方页为大地测量/電子基準点业务，与词条（车载定位）不切题。
- **ISO 6 条**（AUT-043/044/071/072/073/093）：ISO 官方标准页受 Cloudflare 校验保护，web_fetch 无法实取；其中 3 条（システムレダンダンシー/フェイルセーフ/フェールオペレーショナル）为宽泛术语。
- **UNECE 2 条**（AUT-045 UN-R157、AUT-092 UN-R171）：UNECE 官网受 Cloudflare 校验保护，web_fetch 无法实取。
- **金融庁 1 条**（AUT-056 保険）：宽泛术语；金融庁无单页覆盖。

## D 纠错记录

无。本主题所有「部分核验」条目的 URL 与来源机构/词条方向一致，未发现错配。

## E 自检结论

```
[verify-update] 读取 14 行 → 更新 14 / 未匹配 0 / 非法 0；词库共 106 条（已更新至 v1.6）
[check] data/05-industry-autonomous/terms.md：共 106 条，版本 v1.6
[check] 结论：通过（0 项错误 / 0 项警告）
```

## F 提交短码与文件清单

- 提交短码：见本文件同目录提交后回填（commit `feat(vocab): 05/19/10/16 门户 URL 核验深化`）。
- 文件清单：
  - `engine/vocabulary/data/05-industry-autonomous/terms.md`
  - `engine/vocabulary/data/05-industry-autonomous/imports/2026-11-19_核验深化.md`
  - `engine/vocabulary/data/05-industry-autonomous/exports/05-industry-autonomous_2026-11-19_export.{json,csv,jsonl}`
