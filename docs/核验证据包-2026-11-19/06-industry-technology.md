# 核验证据包 06-industry-technology（2026-11-19）

> 组 1 并行核验子会话；worktree `.worktrees/deepen-g1`，分支 `task/deepen-g1-dcdf4009`。
> 依据 `docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C：仅落地**已实取确认**的官方具体页；不动核验状态 / 置信度。
> 范围：本主题「核验状态=部分核验 且 来源URL 为门户级」共 **19** 条。

## A 覆盖表（全部 19 条门户条目，一条不漏）

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| TEC-004 | マイクロサービス | **升级** | https://glossary.cncf.io/microservices/ | CNCF Cloud Native Glossary「Microservices Architecture」；已 fetch 成功 |
| TEC-006 | イベント駆動アーキテクチャ | **升级** | https://glossary.cncf.io/event-driven-architecture/ | CNCF Glossary「Event-Driven Architecture」；已 fetch 成功 |
| TEC-020 | スクラム | 保留 | https://www.scrumalliance.org/ | Scrum Alliance 为商业认证机构（非官方标准机构），无权威单页定义，保留门户 |
| TEC-033 | クラウド | 保留 | https://www.soumu.go.jp/ | 総務省仅有情報通信白書等宽泛市场页，无「单页覆盖」定义页，保留门户 |
| TEC-034 | IaaS | 保留 | https://www.soumu.go.jp/ | 同上；官方无单页定义 |
| TEC-035 | PaaS | 保留 | https://www.soumu.go.jp/ | 同上；官方无单页定义 |
| TEC-036 | SaaS | 保留 | https://www.soumu.go.jp/ | 同上；官方无单页定义 |
| TEC-037 | コンテナ | **升级** | https://glossary.cncf.io/container/ | CNCF Glossary「Containers」；已 fetch 成功 |
| TEC-038 | Docker | 保留 | https://docs.docker.com/ | Docker 官方文档门户（docs 门户本身即来源），无更具体单页，保留 |
| TEC-039 | Kubernetes | **升级** | https://glossary.cncf.io/kubernetes/ | CNCF Glossary「Kubernetes」；已 fetch 成功 |
| TEC-040 | サーバーレス | **升级** | https://glossary.cncf.io/serverless/ | CNCF Glossary「Serverless」；已 fetch 成功 |
| TEC-041 | 可用性 | **升级** | https://www.iso.org/standard/35733.html | ISO/IEC 25010（SQuaRE 质量模型，含可用性/使用性）；已 fetch 成功（2011 版已撤，现行 2023 版为 iso.org/standard/78176） |
| TEC-045 | OAuth | **升级** | https://www.rfc-editor.org/rfc/rfc6749.html | IETF RFC 6749《The OAuth 2.0 Authorization Framework》（RFC Editor 官方发布）；已 fetch 成功 |
| TEC-048 | 脆弱性 | 保留 | https://owasp.org/ | OWASP 为非政府社区组织，无权威单页定义，保留门户 |
| TEC-049 | ゼロトラスト | **升级** | https://csrc.nist.gov/publications/detail/sp/800-207/final | NIST SP 800-207《Zero Trust Architecture》；已 fetch 成功 |
| TEC-050 | 個人情報保護法 | **升级** | https://www.ppc.go.jp/personalinfo/ | 個人情報保護委員会「個人情報保護法等」；已 fetch 成功 |
| TEC-051 | セキュリティ監査 | **升级** | https://www.iso.org/standard/27001 | ISO/IEC 27001:2022（ISMS 要求，安全审计/管理体系标准页）；已 fetch 成功 |
| TEC-052 | インシデント対応 | **升级** | https://csrc.nist.gov/pubs/sp/800/61/r3/final | NIST SP 800-61 Rev.3《Incident Response Recommendations…》；已 fetch 成功 |
| TEC-074 | IT資格 | 保留 | https://www.ipa.go.jp/ | IPA「試験情報」页存在，但本次 web_fetch 未能取回内容（站点拦截），不满足「实取确认」门槛，保留门户 |

合计：**升级 11 / 保留 8 / 纠错 0**。

## B 升级证据（目标 URL + web_fetch 成功记录 + 页面标题）

| ID | 目标 URL | 页面标题（fetch 实取） |
|---|---|---|
| TEC-004 | https://glossary.cncf.io/microservices/ | Microservices Architecture — Cloud Native Glossary |
| TEC-006 | https://glossary.cncf.io/event-driven-architecture/ | Event-Driven Architecture — Cloud Native Glossary |
| TEC-037 | https://glossary.cncf.io/container/ | Containers — Cloud Native Glossary |
| TEC-039 | https://glossary.cncf.io/kubernetes/ | Kubernetes — Cloud Native Glossary |
| TEC-040 | https://glossary.cncf.io/serverless/ | Serverless — Cloud Native Glossary |
| TEC-041 | https://www.iso.org/standard/35733.html | ISO/IEC 25010:2011 — Systems and software engineering … System and software quality models |
| TEC-045 | https://www.rfc-editor.org/rfc/rfc6749.html | The OAuth 2.0 Authorization Framework（RFC 6749, IETF） |
| TEC-049 | https://csrc.nist.gov/publications/detail/sp/800-207/final | SP 800-207, Zero Trust Architecture \| CSRC |
| TEC-050 | https://www.ppc.go.jp/personalinfo/ | 個人情報保護法等 ｜個人情報保護委員会 |
| TEC-051 | https://www.iso.org/standard/27001 | ISO/IEC 27001:2022 — Information security management systems |
| TEC-052 | https://csrc.nist.gov/pubs/sp/800/61/r3/final | SP 800-61 Rev. 3, Incident Response Recommendations and Considerations… \| CSRC |

## C 保留理由（逐条）

- TEC-020 スクラム：来源 Scrum Alliance 为商业认证机构，非官方标准机构；无权威单页定义，保留门户。
- TEC-033 / 034 / 035 / 036 クラウド / IaaS / PaaS / SaaS：来源 総務省；官方仅有情報通信白書等宽泛市场动向页，无「单页覆盖」的定义页，保留门户。
- TEC-038 Docker：来源为 Docker 官方文档门户（docs.docker.com），门户本身即诚实粒度，保留。
- TEC-048 脆弱性：来源 OWASP 为非政府社区组织，无权威单页定义，保留门户。
- TEC-074 IT資格：IPA「試験情報」页存在，但 web_fetch 未能取回内容（站点拦截），不满足实取确认门槛，保留门户。

## D 纠错记录

无。本主题门户条目的来源URL 与来源机构一致，未发现错配。

## E 自检结论

```
$ python engine/vocabulary/script/vocab_tool.py verify-update --topic 06-industry-technology --file engine/vocabulary/data/06-industry-technology/imports/2026-11-19_核验深化.md
[verify-update] 读取 11 行 → 更新 11 / 未匹配 0 / 非法 0；词库共 74 条（已更新至 v1.4）

$ python engine/vocabulary/script/vocab_tool.py export --topic 06-industry-technology --format all
[export] data/06-industry-technology/exports/06-industry-technology_2026-11-19_export.json（74 条，v1.4）
[export] data/06-industry-technology/exports/06-industry-technology_2026-11-19_export.csv（74 条，v1.4）
[export] data/06-industry-technology/exports/06-industry-technology_2026-11-19_export.jsonl（74 条，v1.4）

$ python engine/vocabulary/script/vocab_tool.py check --topic 06-industry-technology
[check] data/06-industry-technology/terms.md：共 74 条，版本 v1.4
[check] 结论：通过（0 项错误 / 0 项警告）
```

## F 提交短码与文件清单

- commit：见本组提交（中文 message：`feat(vocab): 03/06/08/15 门户 URL 核验深化`）
- 变更文件：
  - `engine/vocabulary/data/06-industry-technology/terms.md`（v1.3 → v1.4）
  - `engine/vocabulary/data/06-industry-technology/imports/2026-11-19_核验深化.md`（新增）
  - `engine/vocabulary/data/06-industry-technology/exports/06-industry-technology_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/06-industry-technology.md`（本文件）
