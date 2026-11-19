# 核验证据包 — 17-migration-compliance（2026-11-19）

> 组 4 / 分支 `task/deepen-g4-dcdf4009` / worktree `.worktrees/deepen-g4`。
> 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页，不动核验状态 / 置信度）。
> 范围：本主题「部分核验 且 来源URL 门户级」条目共 **6** 条。

## A 覆盖表

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| MPC-007 | 出境入境中介服务 | 升级 | https://www.nia.gov.cn/n897453/c1801612/content.html | 国家移民管理局 2026-09-14 发布《从事出境入境中介服务的机构和人员备案管理办法》，第二条明确中介服务定义（三构成要件）；web_fetch 成功 |
| MPC-008 | 备案 | 升级 | https://www.nia.gov.cn/n897453/c1801612/content.html | 同上，备案管理办法正文页（备案范围/期限/材料）；web_fetch 成功 |
| MPC-025 | 母国語相談 | 升级 | https://www.support.otit.go.jp/soudan/ | 外国人技能実習機構（OTIT）母国語相談ホームページ（多言語サイトマップ）；web_fetch 成功 |
| MPC-047 | 备案信息公示 | 升级 | https://www.nia.gov.cn/announcement/pub/index.html | 国家移民管理局「从事出境入境中介服务的机构和人员备案信息公示」查询平台；web_fetch 成功 |
| MPC-063 | 12367 | 升级 | https://www.nia.gov.cn/n741445/n741614/index.html | 国家移民管理局「咨询电话」页，列各省级移民管理机构服务电话（均为 12367 热线）；web_fetch 成功 |
| MPC-070 | 个人挂靠 | 升级 | https://www.nia.gov.cn/n897453/c1801612/content.html | 备案管理办法规定个人不得从事出境入境中介服务；web_fetch 成功 |

合计：升级 6 / 保留 0 / 纠错 0。

## B 升级证据（目标 URL + web_fetch 成功记录 + 页面标题）

| ID | 目标 URL | web_fetch | 页面标题 |
|---|---|---|---|
| MPC-007 / MPC-008 / MPC-070 | https://www.nia.gov.cn/n897453/c1801612/content.html | 成功 | 国家移民管理局 国家市场监督管理总局发布《从事出境入境中介服务的机构和人员备案管理办法》 |
| MPC-025 | https://www.support.otit.go.jp/soudan/ | 成功 | 母国語支援サイトマップ｜母国語相談ホームページ｜外国人技能実習機構 |
| MPC-047 | https://www.nia.gov.cn/announcement/pub/index.html | 成功 | 国家移民管理局-从事出境入境中介服务的机构和人员备案信息公示 |
| MPC-063 | https://www.nia.gov.cn/n741445/n741614/index.html | 成功 | 咨询电话_国家移民管理局 |

## C 保留理由

（无）

## D 纠错记录

（无）

## E 自检结论

```
[verify-update] 读取 6 行 → 更新 6 / 未匹配 0 / 非法 0；词库共 77 条（已更新至 v1.5）
[check] data/17-migration-compliance/terms.md：共 77 条，版本 v1.5
  [warn] MPC-071: 别名「特定技能专门中介」与自身词条/别名重复（冗余，建议清理）
[check] 结论：通过（0 项错误 / 1 项警告）
```

说明：唯一警告为**既有别名冗余类**（MPC-071「特定技能专门中介」与自身词条重复），非本次改动引入，原文记录备查。

## F 提交短码与文件清单

- 提交短码：见本组提交（`feat(vocab): 07/13/11/17 门户 URL 核验深化`）。
- 文件清单：
  - `engine/vocabulary/data/17-migration-compliance/terms.md`
  - `engine/vocabulary/data/17-migration-compliance/imports/2026-11-19_核验深化.md`
  - `engine/vocabulary/data/17-migration-compliance/exports/17-migration-compliance_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/17-migration-compliance.md`
