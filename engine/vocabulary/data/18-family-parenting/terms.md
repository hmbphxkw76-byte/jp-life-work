# 家族·育儿·人生事件词汇库（18-family-parenting）

> **定位**：vocabulary 子系统主题词库，由 `script/vocab_tool.py` 统一管理；词汇表请勿手工编辑，变更一律走 `import` / `tag` 命令。
> **主题配置**：`config/topics.json` → `18-family-parenting`（家族育儿与人生事件全领域词汇：家族滞在、婚姻离婚、生育保育、教育、扶养、继承）
> **去重规范**：词条与别名经归一化（NFKC + 空白折叠 + 忽略大小写）后全局唯一；别名/标签分隔符为半角 `;`。

## 词汇表

| ID | 词条 | 别名 | 分类 | 标签 | 定义 | 来源 | 首次登记 | 最近更新 | 核验状态 | 来源URL | 置信度 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FAM-001 | 家族滞在 | 家族滞在ビザ;家族带同 | 家族滞在 | 在留;家属 | 扶养资格者的配偶或子的在留资格；特定技能1号原则上不可带家属 | 出入国在留管理庁 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-002 | 扶養 | 扶養義務;扶養関係 | 家族滞在 | 家属;扶养 | 扶养人对配偶或子女承担的抚养义务与关系 | 出入国在留管理庁 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-003 | 在職証明書 | 在职证明 | 家族滞在 | 家属;书类 | 雇主出具的证明雇佣状态与职业的书类，家族滞在申请必备 | 出入国在留管理庁 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-004 | 住民税課税証明書 | 住民税证明;课税证明 | 家族滞在 | 家属;书类 | 自治体出具的住民税课税或非课税证明，用于扶养能力审查 | 出入国在留管理庁 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-005 | 納税証明書 | 纳税证明 | 家族滞在 | 家属;书类 | 证明一年间总所得与纳税状况的书类 | 出入国在留管理庁 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-006 | 国際結婚 | 国际结婚;涉外婚姻 | 婚姻与离婚 | 婚姻;国际 | 一方为外国人、婚姻成立要件依本国法判断的婚姻 | 法務省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/MINJI/minji15.html | B |
| FAM-007 | 婚姻届 | 结婚登记;婚姻申报 | 婚姻与离婚 | 婚姻;书类 | 向市区町村提交的结婚成立申报书 | 法務省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/ONLINE/FAMILYREGISTER/5-2.html | B |
| FAM-008 | 離婚 | 离婚 | 婚姻与离婚 | 离婚 | 婚姻关系依協議・調停・裁判等方式消灭 | 法務省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.courts.go.jp/saiban/syurui/syurui_kazi/kazi_08_01/index.html | B |
| FAM-009 | 親権 | 亲权;监护权 | 婚姻与离婚 | 离婚;子女 | 离婚后对子女的监护与教养权分配 | 家庭裁判所 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.courts.go.jp/saiban/syurui/syurui_kazi/kazi_shinken/index.html | B |
| FAM-010 | 面会交流 | 探视权;会面交往 | 婚姻与离婚 | 离婚;子女 | 离婚后未任親権者一方与子女会面交往的安排 | 家庭裁判所 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.courts.go.jp/saiban/syurui/syurui_kazi/kazi_07_08/index.html | B |
| FAM-011 | 出産育児一時金 | 出产育儿一时金;生育一时金 | 生育与育儿 | 生育;给付 | 加入健康保险者分娩时可申请的一次性给付 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 已核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | A |
| FAM-012 | 母子手帳 | 母子健康手帳;母婴健康手册 | 生育与育儿 | 生育;母子 | 自治体交付的孕期与乳幼儿健康管理手册 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-013 | 産科医療給付金 | 产科医疗给付 | 生育与育儿 | 生育;给付 | 与出産育児一時金并行的产科医疗相关给付口径 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-014 | 育児休業 | 育儿休假 | 生育与育儿 | 育儿;劳动 | 抚育婴幼儿的休假制度，与雇用保険给付衔接 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000130583.html | B |
| FAM-015 | 産後パパ育休 | 产后爸爸育婴假;男性育休 | 生育与育儿 | 育儿;劳动 | 男性在产后一定期间内取得的育婴休假 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-016 | 子育て支援 | 育儿支援 | 生育与育儿 | 育儿;支援 | 自治体与社区提供的育儿支持服务总称 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-017 | 保育所 | 保育园;认可保育所 | 保育与教育 | 保育 | 以需要保育的儿童为对象的福祉设施 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-018 | 認定こども園 | 认定儿童园 | 保育与教育 | 保育;教育 | 教育与保育一体的设施，兼具幼稚園与保育所功能 | 文部科学省 | 2026-11-14 | 2026-11-19 | 已核验 | https://www.mext.go.jp/a_menu/01_b.htm | B |
| FAM-019 | 幼稚園 | 幼儿园 | 保育与教育 | 教育 | 学校教育法上的学校，3岁以上为对象 | 文部科学省 | 2026-11-14 | 2026-11-19 | 已核验 | https://www.mext.go.jp/a_menu/01_b.htm | B |
| FAM-020 | 待機児童 | 待机儿童;等待入园儿童 | 保育与教育 | 保育 | 希望入保育所但因定员不足未能入所的儿童 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-021 | 日本語指導 | 日语指导 | 保育与教育 | 教育;日语 | 为需要日语支援的儿童提供的抽离或特别的教育课程 | 文部科学省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mext.go.jp/content/20260525-mxt_kokoku-000007294_00.pdf | B |
| FAM-022 | 就学援助 | 就学资助 | 保育与教育 | 教育;支援 | 学校教育法第19条上市町村必须援助的就学经济支持 | 文部科学省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mext.go.jp/a_menu/shotou/clarinet/004/1323374.htm | B |
| FAM-023 | 児童手当 | 儿童手当;子ども手当 | 扶养与支援 | 给付;儿童 | 对监护儿童者按月给付的津贴 | 内閣府 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.cfa.go.jp/policies/kokoseido/jidouteate/annai | B |
| FAM-024 | 児童扶養手当 | 儿童抚养手当 | 扶养与支援 | 给付;单亲 | 对单亲家庭监护儿童者给付的津贴 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-025 | 生活保護 | 生活保护;低保 | 扶养与支援 | 支援;生活 | 对困难家庭提供最低生活与医疗等扶助的公的扶助制度 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-026 | 母子福祉資金 | 母子福利资金 | 扶养与支援 | 支援;单亲 | 对母子家庭提供的资金贷付等支援 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-027 | 第3号被保険者 | 第三号被保险人;被抚养配偶 | 扶养与支援 | 保险;扶养 | 厚生年金加入者的被抚养配偶，免直接缴纳厚生年金 | 日本年金機構 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.nenkin.go.jp/service/seidozenpan/20140710.html | B |
| FAM-028 | 相続 | 继承 | 继承与终末 | 继承 | 死亡时对其财产的法定承继 | 法務省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.gov-online.go.jp/useful/article/201809/1.html | B |
| FAM-029 | 遺言 | 遗嘱 | 继承与终末 | 继承 | 对被继承人财产的意定安排 | 法務省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/MINJI/minji03_00051.html | B |
| FAM-030 | 遺産分割 | 遗产分割 | 继承与终末 | 继承 | 多数继承人之间对遗产的分割协议或裁判 | 法務省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.courts.go.jp/saiban/syurui/syurui_kazi/kazi_07_12/index.html | B |
| FAM-031 | 埋葬 | 火葬 | 继承与终末 | 终末 | 死亡后的埋葬或火葬及相关许可 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-032 | 家族帯同 | 家属带同;带家属 | 场景与表达 | 场景;家属 | 在留期间携配偶或子女共同在留的安排 | 出入国在留管理庁 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-033 | 定住者 | 定住ビザ;定住资格 | 场景与表达 | 在留;长期 | 特定事由（如家族滞在高卒后就业）的在留资格 | 出入国在留管理庁 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/resources/nyuukokukanri07_00122.html | B |
| FAM-034 | 世帯年収 | 家庭年收入 | 场景与表达 | 扶养;收入 | 同一生计家庭的年度收入，永住与扶养审查口径 | 出入国在留管理庁 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-035 | 家庭イベント | 家庭事件;人生事件 | 场景与表达 | 场景 | 结婚、生育、离婚、继承等在留与行政手续的统称 | 仓库规范 | 2026-11-14 | 2026-11-19 | 部分核验 |  | C |
| FAM-036 | 出産 | 分娩;生育 | 生育与育儿 | 生育;医疗;出産 | 生育行为；日本设有出産育児一時金等一次性补助，由健康保险支付 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-037 | 介護休業 | 介护休假;介护休业 | 生育与育儿 | 介护;休假 | 因护理家人而休业的制度；与育児休業对照 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000130583.html | B |
| FAM-038 | 出生届 | 出生申报 | 生育与育儿 | 生育;手续 | 出生时向自治体提交的申报 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-039 | 教育 | 教育制度 | 保育与教育 | 教育 | 子女的教育制度与过程 | 文部科学省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mext.go.jp/a_menu/shotou/shugaku/detail/1422256.htm | B |
| FAM-040 | 学校 | スクール | 保育与教育 | 教育;学校 | 实施教育的机构 | 文部科学省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mext.go.jp/a_menu/shotou/shugaku/detail/1422256.htm | B |
| FAM-041 | 入園 | 入园 | 保育与教育 | 保育;入园 | 进入保育所或幼儿园 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-042 | 児童 | 儿童 | 保育与教育 | 儿童;福祉 | 未成年的孩子 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-043 | 年金 | 养老金 | 扶养与支援 | 年金;制度 | 抚养制度中的公共年金 | 日本年金機構 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.nenkin.go.jp/service/index.html | B |
| FAM-044 | 医療 | 医疗 | 扶养与支援 | 医疗;扶养 | 抚养对象享受的医疗保障 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-045 | 保険 | 保险 | 扶养与支援 | 保险;扶养 | 抚养对象加入的保险 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-046 | 住宅 | 住居 | 场景与表达 | 居住;场景 | 家庭居住形态 | 国土交通省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mlit.go.jp/jutakukentiku/house/index.html | B |
| FAM-047 | 生活 | 暮らし | 场景与表达 | 生活;场景 | 家庭的日常生活 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-048 | 同居 | 同住 | 婚姻与离婚 | 婚姻;同居 | 家庭成员同住的状态 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-049 | 独身 | 未婚 | 场景与表达 | 婚姻;场景 | 未婚状态 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-050 | 養子 | 养子 | 婚姻与离婚 | 婚姻;收养 | 通过收养建立的亲子关系 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-051 | 特定技能1号 | 特定技能1号ビザ;技能1号 | 家族滞在 | 在留;家属 | 特定技能1号的在留资格；原则上不可带家属 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/ssw/nyuukokukanri06_00103.html | B |
| FAM-052 | 特定技能2号 | 特定技能2号ビザ;技能2号 | 家族滞在 | 在留;家属 | 特定技能2号的在留资格；可带配偶与子（须另行取得家族滞在资格） | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/ssw/index.html | B |
| FAM-053 | 留学 | 留学ビザ | 家族滞在 | 在留;家属 | 扶养人资格范围内的在留资格之一，其扶养的配偶或子可申请家族滞在 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-054 | 婚姻届受理証明書 | 婚姻届受理证明 | 家族滞在 | 家属;书类 | 家族滞在申请身分关系证明4选1之一 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-055 | 戸籍誊本 | 户籍誊本 | 家族滞在 | 家属;书类 | 家族滞在申请身分关系证明4选1之一 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-056 | 出生証明書 | 出生证明书 | 家族滞在 | 家属;书类 | 家族滞在申请身分关系证明4选1之一 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-057 | 結婚証明書 | 结婚证明书 | 家族滞在 | 家属;书类 | 家族滞在申请身分关系证明4选1之一 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/status/dependent | B |
| FAM-058 | 資格外活動許可 | 资格外活动许可 | 家族滞在 | 在留;就劳 | 家族滞在配偶等就劳前应取得的许可，分包括许可与个别许可 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 已核验 | https://www.moj.go.jp/isa/applications/procedures/nyuukokukanri07_00004.html | A |
| FAM-059 | 包括許可 | 包括许可 | 家族滞在 | 在留;就劳 | 1周28小时以内报偿活动的许可类型，仅需申请书 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/procedures/nyuukokukanri07_00004.html | B |
| FAM-060 | 個別許可 | 个别许可 | 家族滞在 | 在留;就劳 | 包括许可范围外活动的许可类型，要件之一为从事期间不超过在留期间过半 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/procedures/nyuukokukanri07_00004.html | B |
| FAM-061 | 直接支払制度 | 直接支付制度 | 生育与育儿 | 生育;给付 | 出産育児一時金三种支払制度之一，医疗机构代申请并直接受领 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-062 | 受取代理制度 | 受取代理 | 生育与育儿 | 生育;给付 | 出産育児一時金三种支払制度之一，本人申请、医疗机构代领 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-063 | 償還払い制度 | 偿还支付;償還払 | 生育与育儿 | 生育;给付 | 出産育児一時金三种支払制度之一，本人申请并自行受领、先全额垫付 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-064 | 医療情報基盤・診療報酬審査支払機構 | DX審査支払機構;医療情報基盤 | 生育与育儿 | 给付;机构 | 原社会保険診療報酬支払基金更名后的出産育児一時金支払机构 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-065 | 育児・介護休業法 | 育儿介护休业法 | 生育与育儿 | 育儿;劳动 | 规定育児・介護休业的法律；令和6年改正自令和7年（2025年）4月1日阶段性施行 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 已核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000130583.html | A |
| FAM-066 | 公的医療保険 | 公的医疗保险;健康保险 | 生育与育儿 | 生育;保险 | 出産育児一時金支给要件中的日本公共医疗保险 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-067 | 就学義務 | 就学义务 | 保育与教育 | 教育 | 对学龄儿童负有的就学义务；外国人子女无此义务 | 文部科学省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mext.go.jp/a_menu/shotou/clarinet/004/1323374.htm | B |
| FAM-068 | 日本語指導補助者 | 日语指导补助者 | 保育与教育 | 教育;日语 | 支援日本語指導的辅助人员（令和7年调查8,706人） | 文部科学省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mext.go.jp/content/20260525-mxt_kokoku-000007294_00.pdf | B |
| FAM-069 | 母語支援員 | 母语支援员 | 保育与教育 | 教育;日语 | 支援母语教学的职员（令和7年调查7,301人） | 文部科学省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mext.go.jp/a_menu/shotou/shugaku/detail/1422256.htm | B |
| FAM-070 | 教育委員会 | 教育委员会 | 保育与教育 | 教育;窗口 | 自治体负责就学、転校与入学指定的窗口 | 自治体 | 2026-11-18 | 2026-11-19 | 部分核验 |  | C |
| FAM-071 | 戸籍 | 户籍 | 婚姻与离婚 | 婚姻;书类 | 记载亲属关系的行政登记，为離婚・親権事件中的身份凭证 | 法務省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/MINJI/koseki.html | B |
| FAM-072 | 養育費 | 抚养费 | 婚姻与离婚 | 离婚;子女 | 离婚后对子女的抚养费安排，与親権・面会交流分别判断 | 家庭裁判所 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.courts.go.jp/saiban/syurui/syurui_kazi/youikuhi-tetsuzuki/index.html | B |
| FAM-073 | 父子家庭 |  | 扶养与支援 | 单亲;给付 | 父亲单亲家庭，与母子家庭并列为单亲家庭支援对象 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-074 | 母子家庭 |  | 扶养与支援 | 单亲;给付 | 母亲单亲家庭，为児童扶養手当等支援对象 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | B |
| FAM-075 | こども家庭庁 | 儿童家庭厅;CFTA | 扶养与支援 | 窗口;给付 | 児童手当・保育等育儿政策主管窗口 | こども家庭庁 | 2026-11-18 | 2026-11-19 | 已核验 | https://www.cfa.go.jp/ | A |
| FAM-076 | 特定活動 | 特定活动ビザ | 场景与表达 | 在留;长期 | 定住者衔接路径中的在留资格 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/resources/nyuukokukanri07_00122.html | B |
| FAM-077 | 永住者 | 永住ビザ;永住权 | 场景与表达 | 在留;长期 | 无在留期限的在留资格，与定住者相区别 | 出入国在留管理庁 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.moj.go.jp/isa/applications/resources/nyuukokukanri07_00122.html | B |
| FAM-078 | 自治体多语言窗口 | 多语言窗口;多文化共生相談窓口 | 场景与表达 | 窗口 | 自治体提供的外语家庭咨询与翻译转介窗口 | 自治体 | 2026-11-18 | 2026-11-19 | 部分核验 |  | C |

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
| --- | --- | --- | --- |
| v1.0 | 2026-11-14 | 首建词库 | topic-add/init 创建空词库骨架 |
| v1.1 | 2026-11-14 | 批量导入 | 新增 35 条 / 跳过重复 0 条 / 无效 0 条；文件 2026-11-14_词条导入.md |
| v1.2 | 2026-11-15 | 批量导入 | 新增 1 条 / 跳过重复 0 条 / 无效 0 条；文件 2026-11-15_重归位stash2词条.md |
| v1.3 | 2026-11-18 | 批量导入 | 新增 1 条 / 跳过重复 0 条 / 无效 0 条；文件 2026-11-18_提示词库对齐补缺.md |
| v1.4 | 2026-11-18 | 批量导入 | 新增 13 条 / 跳过重复 0 条 / 无效 0 条；文件 2026-11-18_补至阈值.md |
| v1.5 | 2026-11-18 | 批量导入 | 新增 28 条 / 跳过重复 0 条 / 无效 0 条；文件 18-family-parenting.md |
| v1.6 | 2026-11-19 | 核验回填 | 更新 78 条核验字段；文件 2026-11-18_核验回填.md |
| v1.7 | 2026-11-19 | 核验回填 | 更新 14 条核验字段；文件 2026-11-19_核验深化.md |
| v1.8 | 2026-11-19 | 别名调整 | FAM-073：增 — / 删 父子家庭 |
| v1.9 | 2026-11-19 | 别名调整 | FAM-074：增 — / 删 母子家庭 |
| v1.10 | 2026-11-19 | 核验回填 | 更新 2 条核验字段；文件 2026-11-19_门户错配复核.md |
| v1.11 | 2026-11-19 | 核验回填 | 更新 2 条核验字段；文件 2026-11-19_未核实项浏览器核验.md |
