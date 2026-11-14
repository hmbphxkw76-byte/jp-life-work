# 02 司机供需与薪酬
<!-- updated: 2026-11-14 | 拆分自 reports/2026-11-ssw-driver.md 附录基线版「三、司机供需与薪资待遇」 -->

> 信息核对日期：2026-11-11（基线）。对应维度 02：供需缺口、薪资统计、求人抽样、运赁与净收入参考模型（登记册 #4 #5 #6）。
>
> **边界**：活值查 [data/ssw_driver_indicator_registry.md](../data/ssw_driver_indicator_registry.md) #4 #5 #6；净收入模型的社保 / 税 → [07-economy-finance](../../07-economy-finance)；求人四元组定位教训 → [13-regional-info](../../13-regional-info)（只读继承）。

## 3.1 供需缺口（口径差异并列呈现）

| 指标 | 数值 | 口径 |
| --- | --- | --- |
| [2024 年度运力不足](https://www.mlit.go.jp/hakusyo/mlit/r06/hakusho/r07/html/n1112000.html "来源：https://www.mlit.go.jp/hakusyo/mlit/r06/hakusho/r07/html/n1112000.html, 2025") | 约 14%（14.2%/约 4 亿吨） | 不采取对策情形，"已基本消化" |
| [2030 年度缺口（旧估）](https://www.mlit.go.jp/hakusyo/mlit/r06/hakusho/r07/html/n1112000.html "来源：https://www.mlit.go.jp/hakusyo/mlit/r06/hakusho/r07/html/n1112000.html, 2025") | 约 34% | 不采取对策 |
| [2030 年度缺口（再检证）](https://www.mlit.go.jp/seisakutokatsu/freight/content/001984794.pdf "来源：https://www.mlit.go.jp/seisakutokatsu/freight/content/001984794.pdf, 2025；https://www.jil.go.jp/event/ro_forum/20260529/houkoku/01-keynote-shuto.html, 2026") | **平均约 7%／最大约 25%**（无法运送 72 亿吨） | 采取官民对策后修正 |
| [现役事业用卡车司机](https://www.magazine.mlit.go.jp/interview/vol50-1-c-1/ "来源：https://www.magazine.mlit.go.jp/interview/vol50-1-c-1/, 2024") | 约 84 万人 | 干线运输事业用（2024，>24 个月标注） |
| [有效求人倍率](https://www.mhlw.go.jp/content/11602000/001753011.pdf "来源：https://www.mhlw.go.jp/content/11602000/001753011.pdf, 2026") | **2.54**（汽车驾驶业）vs 全产业 1.06 | 2026 年 8 月 |
| [年龄结构](https://www.mlit.go.jp/hakusyo/mlit/r06/hakusho/r07/html/n1111000.html "来源：https://www.mlit.go.jp/hakusyo/mlit/r06/hakusho/r07/html/n1111000.html, 2025") | 运输业 55 岁以上占 33.9%、29 岁以下仅 11.0%（全产业 16.9%） | 2024 年劳动力调查 |
| [劳动强度](https://www.jil.go.jp/event/ro_forum/20260529/houkoku/01-keynote-shuto.html "来源：https://www.jil.go.jp/event/ro_forum/20260529/houkoku/01-keynote-shuto.html, 2025 / 2026") | 大型司机年均劳动 2,544 小时（全产业 2,136）；年间拘束时间上限 2024 年起 3,516→3,300 小时 | 2023 年/新基准 |
| [每运次拘束](https://www.mlit.go.jp/report/press/tokatsu02_hh_000084.html "来源：https://www.mlit.go.jp/report/press/tokatsu02_hh_000084.html, 2026") | 10 小时 13 分（同比-1h33m），其中荷待·装卸 2h02m | FY2025 年 4–8 月平常期 |

⚠️ 提示词指定的 MLIT「トラックドライバー不足実態調査」专项调查的不足人数精确值与"49 岁以下占比"未命中原文页（白書/JILPT 为替代口径）→ 待复核清单。

## 3.2 薪资统计（厚労省毎月勤労統計，2026 年 9 月分速报，2026-11-06 公布）

| 项目 | 运输业·邮政业（5 人以上事业所） | 全产业对照 |
|---|---|---|
| 现金给与总额（月） | **341,158 円（+4.9%）** | 311,409 円（+4.6%） |
| 固定给与 | 334,957 円（+4.5%） | — |
| 所定内给与 | 292,610 円（+5.4%） | — |
| 所定外给与（加班等） | 42,347 円（-0.6%） | — |
| 一般劳动者总额 | 386,399 円（+4.7%） | — |

口径：名义月额、**未含年度赏与**；"运输业·邮政业"为产业中分类，未细分子行业。[Source: https://www.mhlw.go.jp/toukei/itiran/roudou/monthly/r08/2609p/xls/2609c01p.xlsx, 2026]
年龄别年收（2023，白書）：大型司机 485 万円／中小型 438 万円（全产业 507 万円）。[Source: https://www.mlit.go.jp/hakusyo/mlit/r06/hakusho/r07/html/n1111000.html, 2025]
全ト协 2026 年版工资调查（4,624 社中 589 社回答）：男性大型司机月薪 39.5 万円（+4%）、全职务平均 35.98 万円（+5.3%）、含奖金 41.64 万円（+7.1%）。[Source: https://logishift.net/2026/08/06/post-7782/, 2026]（经 LogiShift 转引，原件待复核）

## 3.3 求人抽样（岗位 × 地域分层；月给口径含诸手当）

⚠️ HelloWork/Indeed 原站反爬无法直抓，以下为聚合平台（求人Box 等）转载值，引用时应回溯至原企业求人页核对"各種手当"明细 → 待复核清单。

| 地域 | 企业·岗位 | 月给 | 备注 |
|---|---|---|---|
| 东京圈 | [第一自动车运送（世田谷，2t）](https://xn--pckua2a7gp15o89zb.com/運送業-トラックの仕事 "来源：https://xn--pckua2a7gp15o89zb.com/運送業-トラックの仕事, 2026") | 22 万–45 万円 | 赏与あり |
| 东京圈 | [东京台东区中型](https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/ "来源：https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/, 2026-11") | 346,650 円～ |  |
| 大阪圈 | [桑原服务（茨木，夜勤 4t）](https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/ "来源：https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/, 2026") | 36.5 万–40.5 万円 | 赏与昇给あり |
| 大阪圈 | [Marumasu 食品物流（东住吉，2t）](https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/ "来源：https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/") | 30 万円～ |  |
| 地方 | [朝日运输（富山射水，中/大型）](https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/ "来源：https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/") | 25 万–33.5 万円 | 无事故手当 |
| 地方 | [西本急送（广岛）](https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/ "来源：https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/") | 25 万–36 万円 |  |
| 地方 | [大富（福冈市，2t 便利店配送）](https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/ "来源：https://en.genbars.jp/kw/all/中型ドライバー%20東京%20求人/") | 28.5 万–30.7 万円 |  |
| **特定技能专项** | [Mintoku Work（埼玉，「育成 Driver」）](https://mintoku.work/?specific_skills_industry=15 "来源：https://mintoku.work/?specific_skills_industry=15, 2026") | **265,020 円** | N3＋第一种免许、升给赏与あり |

企业待遇公告参考：佐川急便招聘面月收例 32 万円、年收 480 万起 [Source: https://www.trucknews.biz/article/r091138/, 2025]；雅玛多 SD 司机"年收 600 万円以上可"（例：30 岁·入社 5 年·月收 40 万円）[Source: https://www.kuronekoyamato.co.jp/ytc/corp/recruit/sales-driver/benefits-and-training.html, 2026]。

## 3.4 运赁（司机工资的行情基础）

- 日银企业向服务价格指数「道路货物运输」：2026-09 = 113.3（2020=100），**同比+4.6%**。[Source: https://www.dlri.co.jp/files/macro/666907.pdf, 2026（引日银 SPPI）]
- WebKit 成约运赁指数：2026-10 = **142**（同比+5pt）；并列：2026-09 = 143（LogiShift 口径）。[Source: https://cargo-news.online/news/detail.php?id=12653, 2026; https://logishift.net/stats/truck-freight-rate-index/, 2026]
- 标准运赁：令和 6 年告示第 209 号（2024-03）水准 **+8%** 并新增装卸费加算。[Source: https://jta.or.jp/member/kaisei_jigyoho/unchin_new.html, 2024]
- 价格转嫁率：2023-09 的 24.2% → 2025-09 的 **34.7%**（中小企业厅）。[Source: https://www.jil.go.jp/event/ro_forum/20260529/houkoku/01-keynote-shuto.html, 2026]

## 3.5 净收入参考模型（推断）

**模型输入参数（均官方来源）**

| 参数 | 数值 |
| --- | --- |
| [健康保险料率（协会けんぽ令和 8 年度，劳动折半）](https://www.kyoukaikenpo.or.jp/about/business/insurance_rate/rate_prefectures/r08/ "来源：https://www.kyoukaikenpo.or.jp/about/business/insurance_rate/rate_prefectures/r08/, 2026") | 东京 9.85%／大阪 10.13%＋子ども·子育て支援金 0.23%（2026-04 起全国） |
| [厚生年金](https://www.nenkin.go.jp/service/kounen/hokenryo/hoshu/20150515-01.html "来源：https://www.nenkin.go.jp/service/kounen/hokenryo/hoshu/20150515-01.html, 2026") | 18.3%、本人折半 9.15% |
| [雇用保险（一般事业，本人负担）](https://jsite.mhlw.go.jp/yamagata-roudoukyoku/koyouhoken-20260316.html "来源：https://jsite.mhlw.go.jp/yamagata-roudoukyoku/koyouhoken-20260316.html, 2026") | 0.5% |
| [源泉征收](https://www.nta.go.jp/publication/pamph/gensen/zeigakuhyo2026/01.htm "来源：https://www.nta.go.jp/publication/pamph/gensen/zeigakuhyo2026/01.htm, 2026") | 国税厅令和 8 年分税额表（2026-01 改定） |

**示例概算（月给总额 30 万円、东京、40 岁未满、单身无扶养——全部为推断）**：社保约 4.4 万円（健康保険折半约 1.5 万＋年金折半 2.7 万＋雇用 0.15 万）＋所得税约 0.44 万＋住民税约 0.85 万 → **到手约 24.3 万円/月**（入职首年无前年住民税约 25.2 万）。模型未含赏与、通勤手当等非课税/变动项；中国同岗到手收入对比因需中文来源回溯未建立 → 待次期补充。

## 关联

- 司机缺口 / 运输业工资 / 求人抽样 → [data/ssw_driver_indicator_registry.md](../data/ssw_driver_indicator_registry.md) #4 #5 #6
- 净收入模型的社保 / 税口径 → [07-economy-finance](../../07-economy-finance)
- 求人四元组（岗位×地域×月収×URL）→ [13-regional-info](../../13-regional-info)

---
> 导航：[00-导航与使用约定](00-navigation.md) · [数据登记册](../data/ssw_driver_indicator_registry.md)
