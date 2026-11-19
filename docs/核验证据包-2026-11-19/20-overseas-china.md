# 核验证据包 2026-11-19 · 20-overseas-china

- 会话：并行核验子会话（组 3），worktree `D:\文档\GitHub\jp-life-work\.worktrees\deepen-g3`，分支 `task/deepen-g3-dcdf4009`
- 依据：`docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C（仅落地已实取确认的官方具体页；不动核验状态 / 置信度）
- 范围：核验状态=部分核验 且来源URL 门户级，共 9 条
- 处置合计：升级 6 / 保留门户 3 / 纠错 0

## A 覆盖表（9 条门户条目）

| ID | 词条 | 处置 | 说明 |
| --- | --- | --- | --- |
| OVC-011 | 留学存档 | 升级 | 留服中心网上服务大厅「留学存档」 |
| OVC-021 | 学历认证 | 升级 | 留服中心网上服务大厅「学历学位认证」 |
| OVC-022 | 国外学历学位认证书 | 升级 | 留服中心「国（境）外学历学位认证指南」 |
| OVC-025 | 公证 | 升级 | 司法部中国法律服务网「公证办理」 |
| OVC-035 | 外交 | 保留 | 外務省域名 web_fetch 被拒，保留门户 |
| OVC-036 | 日中関係 | 保留 | 同上 |
| OVC-063 | 加强认证审查公告 | 升级 | 留服中心公告（九）具体页 |
| OVC-064 | 跨境远程文凭 | 升级 | 留服中心「关于跨境远程文凭证书不在认证范围内的郑重提醒」 |
| OVC-069 | 公印确认・アポスティーユ | 保留 | 外務省域名 web_fetch 被拒，保留门户 |

## B 升级证据（6 条）

| ID | 词条 | 新来源URL | 实取页面（标题/性质） | 实取 |
| --- | --- | --- | --- | --- |
| OVC-011 | 留学存档 | https://zwfw.cscse.edu.cn/cscse/lxfwzxwsfwdt2020/lxcd/index.html | 存档（教育部留学服务中心网上服务大厅） | 成功 |
| OVC-021 | 学历认证 | https://zwfw.cscse.edu.cn/zwfw/lxfwzxwsfwdt2020/index.html | 学历学位认证（网上服务大厅） | 成功 |
| OVC-022 | 国外学历学位认证书 | https://zwfw.cscse.edu.cn/zwfw/lxfwzxwsfwdt2020/xlxwrz32/qtxx/2026042823585825550/index.html | 国（境）外学历学位认证指南 | 成功 |
| OVC-025 | 公证 | https://www.moj.gov.cn/pub/sfbgw/zwfw/zwfwgzbl/ | 中国法律服务网「公证办理」（中华人民共和国司法部） | 成功 |
| OVC-063 | 加强认证审查公告 | https://www.cscse.edu.cn/cscse/sy/tzgg/2025102809225023345/index.html | 关于对部分国外院校学历学位认证加强认证审查的公告（九） | 成功 |
| OVC-064 | 跨境远程文凭 | https://zwfw.cscse.edu.cn/zwfw/lxfwzxwsfwdt2020/xlxwrz32/tzgg61/2026051815272573928/index.html | 关于跨境远程文凭证书不在认证范围内的郑重提醒 | 成功 |

## C 保留理由（3 条）

OVC-035（外交）、OVC-036（日中関係）、OVC-069（公印确认・アポスティーユ）来源均为外務省 `https://www.mofa.go.jp/`。会话内对外務省域名多个路径（`/mofaj/`、`/mofaj/gaiko/index.html`、`/mofaj/area/china/index.html`、`/mofaj/toko/`、`/mofaj/toko/todoke/shomei/`）发起 web_fetch 均被 CDN 拒绝（Access Denied），仅检索快照可佐证页面存在，不满足本任务「每条升级 URL 必须有 web_fetch 成功记录」的硬条件，故保留门户并记录理由。

## D 纠错记录

本次未发现门户条目错配。

## E 自检结论

- `verify-update --topic 20-overseas-china --file engine/vocabulary/data/20-overseas-china/imports/2026-11-19_核验深化.md`：读取 6 行 → 更新 6 / 未匹配 0 / 非法 0；词库 79 条 → v1.5。
- `export --format all`：生成 json/csv/jsonl（v1.5）。
- `check --topic 20-overseas-china`：通过（0 项错误 / 0 项警告）。
- 未改动核验状态 / 置信度；未改 `docs/登记册待核实项复核记录-2026-11-19.md`。

## F 提交短码与文件清单

- 提交：commit message `feat(vocab): 09/12/20/14 门户 URL 核验深化`（短码以提交记录为准）。
- 变更文件：
  - `engine/vocabulary/data/20-overseas-china/terms.md`（v1.5）
  - `engine/vocabulary/data/20-overseas-china/imports/2026-11-19_核验深化.md`
  - `engine/vocabulary/data/20-overseas-china/exports/20-overseas-china_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/20-overseas-china.md`
