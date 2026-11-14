# 词汇库索引（vocabulary）

> 由 `script/vocab_tool.py index` 自动生成，请勿手工编辑。生成时间：2026-11-14T10:30:14

## 主题总览

| 主题 | 名称 | ID 前缀 | 词条数 | 分类分布 | 词库版本 | 存储路径 | 最近更新 |
|---|---|---|---|---|---|---|---|
| ssw-driver | 特定技能司机 | SSW | 109 | 驾驶与运输作业 21 / 在留资格与制度 19 / 岗位与业务场景 18 / 薪酬与劳动条件 18 / 资格考试与培训 17 / 生活适应与表达 16 | v1.5 | data/ssw-driver/terms.md | 2026-11-14 |
| career-driver | 司机职业发展 | CDR | 104 | 技能与证照 19 / 求职与雇佣 19 / 薪资与待遇 19 / 职级与晋升路径 18 / 职业转型 16 / 场景与表达 13 | v1.3 | data/career-driver/terms.md | 2026-11-13 |
| career-management | 职业管理与晋升 | CMG | 72 | 绩效与评估 14 / 管理岗位与职责 13 / 团队与运营管理 12 / 人才发展与培训 11 / 场景与表达 11 / 组织与制度 11 | v1.2 | data/career-management/terms.md | 2026-11-13 |
| industry-logistics | 物流行业 | LOG | 106 | 行业结构与业态 19 / 企业与市场 18 / 仓储与配送作业 16 / 运输模式与枢纽 16 / 法规与政策 14 / 技术与数字化 12 / 场景与表达 11 | v1.3 | data/industry-logistics/terms.md | 2026-11-13 |
| industry-autonomous | 自动驾驶与自动化 | AUT | 104 | 算法与系统架构 19 / 自动驾驶技术 19 / 法规与标准 18 / 商业化与运营 17 / 车辆与传感器 16 / 场景与表达 15 | v1.3 | data/industry-autonomous/terms.md | 2026-11-13 |
| industry-technology | 技术行业 | TEC | 74 | 岗位与协作 14 / 技术栈与架构 12 / 数据与人工智能 11 / 云与基础设施 10 / 安全与合规 10 / 开发与工程实践 10 / 场景与表达 7 | v1.2 | data/industry-technology/terms.md | 2026-11-13 |
| economy-finance | 经济与财务 | ECF | 77 | 个人财务与税务 17 / 宏观与经济指标 12 / 金融机构与工具 12 / 市场机制与交易 10 / 估值与风险 9 / 监管与政策 9 / 场景与表达 8 | v1.3 | data/economy-finance/terms.md | 2026-11-14 |
| visa-immigration | 签证与移民 | VIS | 74 | 在留资格类型 15 / 家属与生活 15 / 申请与审查流程 14 / 永住与归化 12 / 法规与政策 10 / 场景与表达 8 | v1.3 | data/visa-immigration/terms.md | 2026-11-14 |
| politics-law | 政治与法律 | LAW | 72 | 法律体系与条文 13 / 劳动与民事法律 12 / 政治制度与机构 12 / 政策与选举 12 / 行政与司法程序 12 / 场景与表达 11 | v1.3 | data/politics-law/terms.md | 2026-11-14 |
| education-qualification | 教育与资格 | EDU | 68 | 教育体系与阶段 13 / 考试与备考 12 / 资格与认证 12 / 学费与资助 11 / 场景与表达 10 / 院校与专业 10 | v1.1 | data/education-qualification/terms.md | 2026-11-13 |
| language-japanese | 日语语言 | JPN | 69 | 语言能力与考试 13 / 语法与句型 12 / 词汇与表达 11 / 学习与教学 9 / 场景与表达 8 / 敬语与语体 8 / 职场日语 8 | v1.2 | data/language-japanese/terms.md | 2026-11-13 |
| culture-life | 文化与生活 | CUL | 80 | 公共服务与设施 17 / 日常生活与居住 17 / 文化习俗与节庆 12 / 饮食与消费 12 / 场景与表达 11 / 社交与礼仪 11 | v1.3 | data/culture-life/terms.md | 2026-11-14 |
| regional-info | 地区信息 | REG | 71 | 人口与城市 12 / 地方政策与自治 12 / 场景与表达 12 / 生活成本与设施 12 / 行政区划与地理 12 / 地方经济与产业 11 | v1.3 | data/regional-info/terms.md | 2026-11-14 |
| life-operations | 在日生活实务 | LOP | 25 | 住房与租赁 10 / 水电燃气与基础设施 4 / 银行与支付 4 / 场景与表达 2 / 行政手续 2 / 通信与网络 2 / 在留与住民登记 1 | v1.2 | data/life-operations/terms.md | 2026-11-14 |
| health-wellbeing | 医疗健康心理 | HLW | 20 | 就医实务 7 / 介護与福祉 5 / 医疗制度 3 / 体检与预防 2 / 心理健康与适应 2 / 牙科与精神科 1 | v1.1 | data/health-wellbeing/terms.md | 2026-11-14 |

合计：15 个主题，1125 条词条。

## 上层对接

- 结构化导出：各主题 `data/<topic>/exports/` 下的 JSON / JSONL / CSV（数据契约见 README 第六节）。
- 检索建议：以词条 ID 为主键，别名与标签作为索引字段，分类作为过滤面。
