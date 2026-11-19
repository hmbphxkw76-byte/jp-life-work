# 医疗·健康·心理词汇库（15-health-wellbeing）

> **定位**：vocabulary 子系统主题词库，由 `script/vocab_tool.py` 统一管理；词汇表请勿手工编辑，变更一律走 `import` / `tag` 命令。
> **主题配置**：`config/topics.json` → `15-health-wellbeing`（医疗健康与心理全领域词汇：医保制度、就医实务、精神科、心理健康、体检预防、介护福祉）
> **去重规范**：词条与别名经归一化（NFKC + 空白折叠 + 忽略大小写）后全局唯一；别名/标签分隔符为半角 `;`。

## 词汇表

| ID | 词条 | 别名 | 分类 | 标签 | 定义 | 来源 | 首次登记 | 最近更新 | 核验状态 | 来源URL | 置信度 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HLW-001 | 健康保険 | 国保;国民健康保険 | 医疗制度 | 医疗;保险 | 公共医疗保险统称，国保与被用者保险按加入主体区分 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/newpage_22682.html | B |
| HLW-002 | 后期高龄 | 后期高龄者医疗;後期高齢者医療 | 医疗制度 | 医疗;老年 | 75 岁以上（一定障碍者 65 岁以上）加入的后期高龄者医疗制度 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-003 | 被保险者证 | 被保险者証;健康保険証 | 医疗制度 | 医疗;凭证 | 证明被保险者身份的保险证，就医时提示 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-004 | 保险费 | 保険料;保险料 | 医疗制度 | 医疗;费用 | 按收入与制度计算的保险费用，与医疗费自付区分 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-005 | 高额疗养 | 高額療養費;高额疗养费 | 医疗制度 | 医疗;报销 | 医疗费超过限度额后事后报销的制度，与医疗费控除区分 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-006 | 医疗费扣除 | 医療費控除;医疗费控税 | 医疗制度 | 税务;医疗 | 确定申告时按医疗费支出扣除所得的税制，与高额疗养不同 | 国税庁 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.nta.go.jp/ | B |
| HLW-007 | 精神科 | 精神神经科 | 牙科与精神科 | 医疗;精神 | 以重笃精神疾患为对象的诊疗科，与心疗内科区分 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-008 | 心疗内科 | 心療内科;身心科 | 牙科与精神科 | 医疗;心理 | 以轻症与心理因素为对象的诊疗科 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-009 | 心理疏导 | カウンセリング;心理辅导 | 心理健康与适应 | 心理;支援 | 由专业人员提供的谈话性心理支持 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-010 | 心理咨询 | 相談 | 心理健康与适应 | 心理;支援 | 面向心理困扰的咨询窗口，含保健所与自治体相谈 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-011 | 健康诊断 | 健康診断;体检 | 体检与预防 | 体检;预防 | 雇主或自治体依法实施的健康检查 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/newpage_22682.html | B |
| HLW-012 | 综合检查 | 人間ドック;精密体检 | 体检与预防 | 体检;自费 | 自费综合检查，项目多于法定健康诊断 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-013 | 特定体检 | 特定健康診断;特定健诊 | 体检与预防 | 体检;预防 | 面向 40–74 岁、以代谢综合征为对象的特定健诊 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000161103.html | B |
| HLW-014 | 预防接种 | 予防接種;疫苗接种 | 体检与预防 | 预防;疫苗 | 依自治体与医疗机关实施的预防接种 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-015 | 保健所 | 公共卫生中心 | 就医实务 | 医疗;公共 | 自治体设置的公共卫生行政机关，提供相谈、预防接种等 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000161103.html | B |
| HLW-016 | 护理保险 | 介護保険 | 介护与福祉 | 介护;保险 | 40 岁以上加入的介护保险制度，与医疗保险区分 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-017 | 护理等级 | 要介護度;介護認定 | 介护与福祉 | 介护;认定 | 介护需要的认定等级，决定可用服务量 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-018 | 医疗费 | 医療費;诊疗费 | 就医实务 | 医疗;费用 | 诊疗与药价的合计，与保险费、自付比例区分 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-019 | 患者登记 | 患者登録;就诊登记 | 就医实务 | 医疗;手续 | 医疗机关就诊时的挂号与患者信息登记 | 厚生労働省 | 2026-11-14 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-020 | カルチャーショック | 文化冲击;culture shock | 心理健康与适应 | 适应;心理;文化差异 | 进入异文化环境后因习惯、价值观与语言差异产生的心理不适与不安定状态 | 需核实原文 | 2026-11-15 | 2026-11-15 | 待核实 |  | 待评 |
| HLW-021 | 被用者健康保険 | 公司职员医保;被用者保险 | 医疗制度 | 保险;被用者;职员 | 公司职员加入的健康保险，由公司与个人分担保费，自付通常 3 割 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/newpage_22682.html | B |
| HLW-022 | 初診料 | 初诊费;初诊料 | 就医实务 | 医疗;费用;初诊 | 首次到某医疗机构就诊时支付的初诊费用 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-023 | 再診料 | 复诊费;再诊料 | 就医实务 | 医疗;费用;复诊 | 初诊后同病复诊时支付的诊察费 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-024 | 処方箋 | 处方笺;处方 | 就医实务 | 医疗;处方;药房 | 医师开具的用药指示，凭此处方到調剤薬局取药 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-025 | 調剤薬局 | 调剂药局;配药局 | 就医实务 | 医疗;药房;配药 | 根据处方笺配药并交付药剂的药房 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-026 | 救急搬送 | 急救运送;急救搬运 | 就医实务 | 急救;搬送;119 | 由消防机关将患者紧急运送至医疗机构的行动 | 消防庁 | 2026-11-15 | 2026-11-19 | 已核验 | https://www.fdma.go.jp/ | A |
| HLW-027 | 医療通訳 | 医疗翻译;医疗通译 | 就医实务 | 多语言;通译;医疗 | 在医疗机关提供的多语言口译服务，需提前确认与预约 | 各自治体 | 2026-11-15 | 2026-11-19 | 部分核验 |  | C |
| HLW-028 | 多言語診療 | 多语言诊疗;外语诊疗 | 就医实务 | 多语言;诊疗;医疗 | 医疗机构提供的外语对应诊疗服务 | 各自治体 | 2026-11-15 | 2026-11-19 | 部分核验 |  | C |
| HLW-029 | 訪問歯科 | 访问牙科;上门牙科 | 牙科与精神科 | 牙科;访问;高龄 | 到宅或设施为卧床患者提供的牙科诊疗 | 日本歯科医師会 | 2026-11-15 | 2026-11-19 | 已核验 | https://www.jda.or.jp/ | A |
| HLW-030 | 精神保健福祉センター | 精神保健福祉中心 | 心理健康与适应 | 心理;福祉;支援 | 自治体设置的精神健康综合支援设施，提供咨询与相談 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/kaigo_koureisha/index.html | B |
| HLW-031 | いのちの電話 | 生命电话;生命之电 | 心理健康与适应 | 心理;自杀防止;电话 | 提供自杀预防与情绪支援的电话相談服务 | いのちの電話連盟 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.lifelink.or.jp/ | B |
| HLW-032 | 介護サービス | 介护服务 | 介护与福祉 | 介護;服务;福祉 | 介護保険提供的居家、设施与社区介护服务 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/kaigo_koureisha/index.html | B |
| HLW-033 | 要介護認定 | 要介护认定;介护认定 | 介护与福祉 | 介護;认定;福祉 | 申请介護服务时由自治体认定的介护等级 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/kaigo_koureisha/index.html | B |
| HLW-034 | 障害者手帳 | 残疾人手册;残障手册 | 介护与福祉 | 障害;手帐;福祉 | 记录残疾等级与福利权利的证件 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-035 | 精神障害者保健福祉手帳 | 精神障碍者保健福祉手册 | 介护与福祉 | 精神;障害;手帐 | 记录精神障碍者保健福祉权利的证件 | 厚生労働省 | 2026-11-15 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/kaigo_koureisha/index.html | B |
| HLW-036 | 面会 | 探视 | 就医实务 | 医疗;探视 | 住院或入住设施时的探望制度 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-037 | 病欠 | 病假 | 医疗制度 | 医疗;休假 | 因疾病不能上班时的缺勤与工资制度 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-038 | 療養 | 疗养 | 医疗制度 | 医疗;疗养 | 以治疗与静养为目的的期间与状态 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-039 | 休職 | 停职 | 医疗制度 | 医疗;休假 | 因疾病等原因暂时离开职务的制度 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-040 | 薬価 | 药价 | 就医实务 | 医疗;费用 | 保险药价的基准金额 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-041 | 医療機関 | 医疗机构 | 就医实务 | 医疗;机构 | 提供诊疗的医院、诊所等设施 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/koukikourei/index.html | B |
| HLW-042 | 訪問看護 | 居家护理 | 介护与福祉 | 介护;访问 | 护士或介护人员到宅提供护理服务 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-043 | 認知症 | 认知障碍 | 介护与福祉 | 介护;认知 | 因脑功能下降导致日常生活障碍的状态 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-044 | うつ病 | 抑郁症 | 牙科与精神科 | 精神;疾病 | 以持续低落情绪为核心症状的精神疾患 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-045 | パニック障害 | 惊恐障碍 | 牙科与精神科 | 精神;疾病 | 反复惊恐发作的精神疾患 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-046 | 不眠症 | 失眠 | 牙科与精神科 | 精神;睡眠 | 入睡或维持睡眠困难的状态 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-047 | 乳児健診 | 婴儿体检 | 体检与预防 | 体检;预防 | 面向婴儿的健康检查 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000161103.html | B |
| HLW-048 | 歯科健診 | 牙科体检 | 体检与预防 | 体检;牙科 | 面向牙齿与口腔的健康检查 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000161103.html | B |
| HLW-049 | 助産所 | 助产所 | 就医实务 | 医疗;分娩 | 助产师实施分娩的设施 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-050 | 入院 | 住院 | 就医实务 | 医疗;住院 | 在医疗机构住院治疗的期间与制度 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-051 | マイナ保険証 | 个人编号卡保险证;マイナンバー保険証 | 医疗制度 | 医疗;保险;凭证 | 以マイナンバーカード作为健康保険証使用，无需限度額適用認定証即可在窗口免付超过高额疗养费上限的部分 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/newpage_22682.html | B |
| HLW-052 | 限度額適用認定証 | 限额适用认定证 | 医疗制度 | 医疗;报销;凭证 | 高额疗养费窗口上限适用凭证，凭其在窗口免付超上限部分；マイナ保険証可替代其免垫付功能 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-053 | 年間上限 | 年度上限 | 医疗制度 | 医疗;报销;高额 | 令和8年8月高额疗养费改革新设的年单位自付上限，改善长期疗养者负担可预见性 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-054 | 出産育児一時金 | 生产育儿一时金;分娩育儿一时金 | 医疗制度 | 医疗;分娩;补助 | 公的医疗保险被保险者或其在留扶养者分娩时，每胎原则50万円的一次性补助 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 已核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/shussan/index.html | A |
| HLW-055 | 直接支払制度 | 直接支付制度 | 医疗制度 | 医疗;分娩;支付 | 出産育児一時金不向申请者支付而直接向分娩设施支付的制度 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-056 | 国民健康保険料 | 国保保费;国民健康保险料 | 医疗制度 | 医疗;费用;国保 | 国民健康保険的保费，由医疗分、支援分、介护分及子ども・子育て支援金合算构成 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/newpage_22682.html | B |
| HLW-057 | 子ども・子育て支援金 | 儿童育儿支援金 | 医疗制度 | 医疗;费用;国保 | 令和8年度（2026年度）起国保保费追加合算征收的儿童与育儿支援金 | 三菱UFJ銀行 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.bk.mufg.jp/ | B |
| HLW-058 | 健康保険組合 | 健康保险组合 | 医疗制度 | 医疗;保险;被用者 | 被用者健康保険的运营主体之一，由公司与个人分担保费 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/newpage_22682.html | B |
| HLW-059 | 协会けんぽ | 协会健保;けんぽ | 医疗制度 | 医疗;保险;被用者 | 被用者健康保険的一种，由协会运营的医疗保险 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-060 | かかりつけ病院 | 常就诊医院 | 就医实务 | 医疗;就医;基层 | 居住地域日常就诊的医院，抵达后应确认并记录 | 报告 | 2026-11-18 | 2026-11-19 | 部分核验 |  | C |
| HLW-061 | 救急病院 | 急救医院 | 就医实务 | 医疗;急救;轮值 | 按轮值制提供急救医疗的医院 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-062 | マイナ救急 | 个人编号卡急救 | 就医实务 | 医疗;急救;保险 | 令和7年10月起全国运用，救急搬送中活用マイナ保険証以选定搬送先 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/newpage_22682.html | B |
| HLW-063 | 救急相談 | 救急咨询;#7119 | 就医实务 | 医疗;急救;咨询 | 自治体设置的夜间与假日救急咨询电话服务（#7119） | 各自治体 | 2026-11-18 | 2026-11-19 | 部分核验 |  | C |
| HLW-064 | 保険医療機関 | 保险医疗机构 | 就医实务 | 医疗;保险;机构 | 适用公共医疗保险的医疗机构，与保険薬局等并列的法律概念 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/koukikourei/index.html | B |
| HLW-065 | 歯科医院 | 牙科医院 | 就医实务 | 医疗;牙科;机构 | 实施牙科诊疗的医疗机构，大部分治疗适用保险 | 日本歯科医師会 | 2026-11-18 | 2026-11-19 | 已核验 | https://www.jda.or.jp/ | A |
| HLW-066 | 特定保健指導 | 特定保健指导 | 体检与预防 | 体检;预防;指导 | 特定健康診査后对需要者实施的保健指导，与特定健康診査同为40–74岁对象 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 已核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000161103.html | A |
| HLW-067 | 事業主健診 | 事业主健诊;雇主健诊 | 体检与预防 | 体检;预防;劳务 | 事业主依据劳动安全卫生法实施的健康诊断 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000161103.html | B |
| HLW-068 | メタボリックシンドローム | 代谢综合征 | 体检与预防 | 体检;预防;代谢 | 特定健康診査以之为重点对象的代谢异常状态 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/newpage_22682.html | B |
| HLW-069 | 適性診断 | 适应性诊断 | 体检与预防 | 体检;预防;资格 | 旅客自动车运送新任者研修中的适应性诊断；货物自动车运送无法定义务 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-070 | 介護保険被保险者证 | 介护保险被保险者证 | 介护与福祉 | 介护;保险;凭证 | 40岁以上加入介护保险的凭证 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/kaigo_koureisha/index.html | B |
| HLW-071 | 高額介護サービス費 | 高额介护服务费 | 介护与福祉 | 介护;费用;减免 | 介护服务费用超过自付上限时的减免制度 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-072 | 第1号被保险者 | 第一号被保险者 | 介护与福祉 | 介护;保险;资格 | 65岁以上加入介护保险的被保险者 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-073 | 第2号被保险者 | 第二号被保险者 | 介护与福祉 | 介护;保险;资格 | 40–64岁加入介护保险的被保险者 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-074 | 要支援 | 要支援认定 | 介护与福祉 | 介护;认定 | 介护保险服务前提之一的认定类别，与要介護并列 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html | B |
| HLW-075 | 介護保険料 | 介护保险费 | 介护与福祉 | 介护;保险;费用 | 介护保险的保费，第2号被保险者搭在医疗保险上征收 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 部分核验 | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/kaigo_koureisha/index.html | B |
| HLW-076 | まもろうよこころ | 守护心灵 | 心理健康与适应 | 心理;咨询;窗口 | 厚生労働省按咨询形态汇总各类心理健康咨询窗口的总览 | 厚生労働省 | 2026-11-18 | 2026-11-19 | 已核验 | https://www.mhlw.go.jp/mamorouyokokoro/ | A |

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
| --- | --- | --- | --- |
| v1.0 | 2026-11-14 | 首建词库 | topic-add/init 创建空词库骨架 |
| v1.1 | 2026-11-14 | 批量导入 | 新增 19 条 / 跳过重复 1 条 / 无效 0 条；文件 2026-11-14_词条导入.md |
| v1.2 | 2026-11-15 | 批量导入 | 新增 1 条 / 跳过重复 0 条 / 无效 0 条；文件 2026-11-15_补录遗失词条.md |
| v1.3 | 2026-11-15 | 批量导入 | 新增 15 条 / 跳过重复 5 条 / 无效 0 条；文件 2026-11-15_恢复stash2补录-health-wellbeing.md |
| v1.4 | 2026-11-18 | 批量导入 | 新增 15 条 / 跳过重复 0 条 / 无效 0 条；文件 2026-11-18_补至阈值.md |
| v1.5 | 2026-11-18 | 批量导入 | 新增 26 条 / 跳过重复 0 条 / 无效 0 条；文件 15-health-wellbeing.md |
| v1.6 | 2026-11-19 | 核验回填 | 更新 75 条核验字段；文件 2026-11-18_核验回填.md |
