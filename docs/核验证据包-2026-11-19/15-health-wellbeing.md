# 核验证据包 15-health-wellbeing（2026-11-19）

> 组 1 并行核验子会话；worktree `.worktrees/deepen-g1`，分支 `task/deepen-g1-dcdf4009`。
> 依据 `docs/登记册待核实项复核记录-2026-11-19.md` §六 方案 C：仅落地**已实取确认**的官方具体页；不动核验状态 / 置信度。
> 范围：本主题「核验状态=部分核验 且 来源URL 为门户级（域名/根路径）」共 **3** 条；并复查全部「部分核验」条目的 URL 切题性。

## A 覆盖表（全部 3 条门户条目，一条不漏）

| ID | 词条 | 处置 | 目标URL | 证据/理由 |
|---|---|---|---|---|
| HLW-006 | 医疗费扣除 | **升级** | https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1120.htm | 国税庁「No.1120 医療費を支払ったとき（医療費控除）」；已 fetch 成功 |
| HLW-057 | 子ども・子育て支援金 | 保留 | https://www.bk.mufg.jp/ | 现来源为三菱UFJ銀行（非政府机构）；未检索到厚生労働省等官方单页，保留门户 |
| HLW-031 | いのちの電話 | 保留 | https://www.lifelink.or.jp/ | 运营方为 NPO 法人自殺対策支援センターライフリンク（非政府机构），无官方单页，保留门户 |

合计（门户条目）：**升级 1 / 保留 2 / 纠错 0**。

## B 升级证据（目标 URL + web_fetch 成功记录 + 页面标题）

| ID | 目标 URL | 页面标题（fetch 实取） |
|---|---|---|
| HLW-006 | https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1120.htm | No.1120　医療費を支払ったとき（医療費控除）｜国税庁 |

## C 保留理由（逐条）

- HLW-057 子ども・子育て支援金：现来源为三菱UFJ銀行（非政府机构），不满足「仅官方域名」门槛；经检索（`site:mhlw.go.jp 子ども・子育て支援金` 等）未确认到厚生労働省等官方单页，保留门户。
- HLW-031 いのちの電話：运营方为 NPO 法人「自殺対策支援センターライフリンク」（非政府机构），无官方单页，保留门户。

## D 纠错记录（全量「部分核验」URL 切题复查）

复查发现 2026-11-18 核验回填批次存在**系统性错配**：大量无关词条被指向「高額療養費制度」页（`.../juuyou/kougakuiryou/index.html`）或「マイナ保険証」页（`.../newpage_22682.html`）等单一页面。本次逐条纠正，原则：有已实取确认的正确官方单页则指向该页，否则回落厚生労働省门户（诚实粒度）。

URL 键位（均已在本次 web_fetch 实取成功）：

| 键 | URL |
|---|---|
| P | https://www.mhlw.go.jp/ |
| IRY | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/index.html （医療保険） |
| KOUKOU | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/koukikourei/index.html （高齢者医療制度） |
| KAIGO | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/kaigo_koureisha/index.html （介護・高齢者福祉） |
| TOKUTEI | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000161103.html （特定健診・特定保健指導） |
| KOKUMIN | https://www.mhlw.go.jp/stf/newpage_21517.html （国民健康保険の保険料・保険税） |
| SHUSSAN | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html （出産育児一時金等） |

| ID | 词条 | 原 URL（错配） | 新 URL | 理由 |
|---|---|---|---|---|
| HLW-001 | 健康保険 | MYNA（マイナ保険証） | IRY | 综合概念，指向医疗保険综合页 |
| HLW-002 | 后期高龄 | KOUGAKU（高額療養費） | KOUKOU | 指向「後期高齢者医療制度」页 |
| HLW-003 | 被保险者证 | KOUGAKU | IRY | 被保険者証属医疗保険制度 |
| HLW-004 | 保险费 | KOUGAKU | IRY | 保険料属医疗保険制度 |
| HLW-007 | 精神科 | KOUGAKU | P | 宽泛诊疗科，无官方单页 |
| HLW-008 | 心疗内科 | KOUGAKU | P | 宽泛诊疗科，无官方单页 |
| HLW-009 | 心理疏导 | KOUGAKU | P | 非制度术语，无官方单页 |
| HLW-010 | 心理咨询 | KOUGAKU | P | 非制度术语，无官方单页 |
| HLW-011 | 健康诊断 | MYNA | P | 健康診断无对应官方单页 |
| HLW-012 | 综合检查 | KOUGAKU | P | 自費人間ドック，无官方单页 |
| HLW-014 | 预防接种 | KOUGAKU | P | 予防接種无对应官方单页 |
| HLW-015 | 保健所 | TOKUTEI（特定健診） | P | 保健所非特定健診页内容 |
| HLW-016 | 护理保险 | KOUGAKU | KAIGO | 介護保険属介護・高齢者福祉 |
| HLW-017 | 护理等级 | KOUGAKU | KAIGO | 要介護度属介護制度 |
| HLW-018 | 医疗费 | KOUGAKU | P | 宽泛费用概念 |
| HLW-019 | 患者登记 | KOUGAKU | P | 就医实务术语，无官方单页 |
| HLW-021 | 被用者健康保険 | MYNA | IRY | 被用者保険属医疗保険制度 |
| HLW-022 | 初診料 | KOUGAKU | P | 診療報酬项目，无官方单页 |
| HLW-023 | 再診料 | KOUGAKU | P | 診療報酬项目，无官方单页 |
| HLW-024 | 処方箋 | KOUGAKU | P | 就医实务术语，无官方单页 |
| HLW-025 | 調剤薬局 | KOUGAKU | P | 药房概念，无官方单页 |
| HLW-030 | 精神保健福祉センター | KAIGO | P | 精神保健福祉非介護页内容 |
| HLW-034 | 障害者手帳 | KOUGAKU | P | 手帳制度无对应官方单页 |
| HLW-035 | 精神障害者保健福祉手帳 | KAIGO | P | 精神保健福祉手帳非介護页内容 |
| HLW-036 | 面会 | KOUGAKU | P | 就医实务术语，无官方单页 |
| HLW-037 | 病欠 | KOUGAKU | P | 劳动制度术语，无官方单页 |
| HLW-038 | 療養 | KOUGAKU | P | 宽泛术语，无官方单页 |
| HLW-039 | 休職 | KOUGAKU | P | 劳动制度术语，无官方单页 |
| HLW-040 | 薬価 | KOUGAKU | P | 薬価基准无对应官方单页 |
| HLW-041 | 医療機関 | KOUKOU（高齢者医療） | IRY | 医療機関属医疗保険制度 |
| HLW-042 | 訪問看護 | KOUGAKU | IRY | 訪問看護属保険医療 |
| HLW-043 | 認知症 | KOUGAKU | KAIGO | 認知症施策属介護・高齢者福祉 |
| HLW-044 | うつ病 | KOUGAKU | P | 疾病名，无官方单页 |
| HLW-045 | パニック障害 | KOUGAKU | P | 疾病名，无官方单页 |
| HLW-046 | 不眠症 | KOUGAKU | P | 疾病名，无官方单页 |
| HLW-047 | 乳児健診 | TOKUTEI | P | 乳児健診非特定健診页内容 |
| HLW-048 | 歯科健診 | TOKUTEI | P | 歯科健診非特定健診页内容 |
| HLW-049 | 助産所 | KOUGAKU | SHUSSAN | 出産施設，指向出産育児一時金页 |
| HLW-050 | 入院 | KOUGAKU | P | 宽泛术语，无官方单页 |
| HLW-055 | 直接支払制度 | KOUGAKU | SHUSSAN | 出産育児一時金の直接支払制度 |
| HLW-056 | 国民健康保険料 | MYNA | KOKUMIN | 指向「国民健康保険の保険料・保険税」页 |
| HLW-058 | 健康保険組合 | MYNA | IRY | 被用者保険运营主体属医疗保険制度 |
| HLW-059 | 协会けんぽ | KOUGAKU | IRY | 被用者保険一种属医疗保険制度 |
| HLW-061 | 救急病院 | KOUGAKU | P | 急救医疗概念，无官方单页 |
| HLW-064 | 保険医療機関 | KOUKOU | IRY | 保険医療機関属医疗保険制度 |
| HLW-067 | 事業主健診 | TOKUTEI | P | 事業主健診非特定健診页内容 |
| HLW-068 | メタボリックシンドローム | MYNA | TOKUTEI | 特定健診以之为重点对象 |
| HLW-069 | 適性診断 | KOUGAKU | P | 资格/劳务术语，无官方单页 |
| HLW-071 | 高額介護サービス費 | KOUGAKU | KAIGO | 介護费用减免属介護制度 |
| HLW-072 | 第1号被保险者 | KOUGAKU | KAIGO | 介護保険被保険者属介護制度 |
| HLW-073 | 第2号被保险者 | KOUGAKU | KAIGO | 介護保険被保険者属介護制度 |
| HLW-074 | 要支援 | KOUGAKU | KAIGO | 要支援认定属介護制度 |

合计：**纠错 52** 条（其中指向已实取官方具体页 22 条，回落厚生労働省门户 30 条）。

未改动且切题（保持原样）：HLW-005、HLW-013、HLW-032、HLW-033、HLW-051、HLW-052、HLW-053、HLW-062、HLW-070、HLW-075（高額療養費 / 特定健診 / 介護 / マイナ保険証 等页与词条一致）。

## E 自检结论

```
$ python engine/vocabulary/script/vocab_tool.py verify-update --topic 15-health-wellbeing --file engine/vocabulary/data/15-health-wellbeing/imports/2026-11-19_核验深化.md
[verify-update] 读取 53 行 → 更新 53 / 未匹配 0 / 非法 0；词库共 76 条（已更新至 v1.7）

$ python engine/vocabulary/script/vocab_tool.py export --topic 15-health-wellbeing --format all
[export] data/15-health-wellbeing/exports/15-health-wellbeing_2026-11-19_export.json（76 条，v1.7）
[export] data/15-health-wellbeing/exports/15-health-wellbeing_2026-11-19_export.csv（76 条，v1.7）
[export] data/15-health-wellbeing/exports/15-health-wellbeing_2026-11-19_export.jsonl（76 条，v1.7）

$ python engine/vocabulary/script/vocab_tool.py check --topic 15-health-wellbeing
[check] data/15-health-wellbeing/terms.md：共 76 条，版本 v1.7
[check] 结论：通过（0 项错误 / 0 项警告）
```

## F 提交短码与文件清单

- commit：见本组提交（中文 message：`feat(vocab): 03/06/08/15 门户 URL 核验深化`）
- 变更文件：
  - `engine/vocabulary/data/15-health-wellbeing/terms.md`（v1.6 → v1.7）
  - `engine/vocabulary/data/15-health-wellbeing/imports/2026-11-19_核验深化.md`（新增）
  - `engine/vocabulary/data/15-health-wellbeing/exports/15-health-wellbeing_2026-11-19_export.{json,csv,jsonl}`
  - `docs/核验证据包-2026-11-19/15-health-wellbeing.md`（本文件）
