# 词汇库索引（vocabulary）

> 由 `script/vocab_tool.py index` 自动生成，请勿手工编辑。生成时间：2026-11-14T11:08:26

## 主题总览

| 主题 | 名称 | ID 前缀 | 词条数 | 分类分布 | 词库版本 | 存储路径 | 最近更新 |
|---|---|---|---|---|---|---|---|
| ssw-driver | 特定技能司机 | SSW | 105 | 在留资格与制度 19 / 岗位与业务场景 18 / 薪酬与劳动条件 18 / 资格考试与培训 17 / 驾驶与运输作业 17 / 生活适应与表达 16 | v1.4 | data/ssw-driver/terms.md | 2026-11-13 |
| career-driver | 司机职业发展 | CDR | 104 | 技能与证照 19 / 求职与雇佣 19 / 薪资与待遇 19 / 职级与晋升路径 18 / 职业转型 16 / 场景与表达 13 | v1.3 | data/career-driver/terms.md | 2026-11-13 |
| career-management | 职业管理与晋升 | CMG | 72 | 绩效与评估 14 / 管理岗位与职责 13 / 团队与运营管理 12 / 人才发展与培训 11 / 场景与表达 11 / 组织与制度 11 | v1.2 | data/career-management/terms.md | 2026-11-13 |
| industry-logistics | 物流行业 | LOG | 106 | 行业结构与业态 19 / 企业与市场 18 / 仓储与配送作业 16 / 运输模式与枢纽 16 / 法规与政策 14 / 技术与数字化 12 / 场景与表达 11 | v1.3 | data/industry-logistics/terms.md | 2026-11-13 |
| industry-autonomous | 自动驾驶与自动化 | AUT | 104 | 算法与系统架构 19 / 自动驾驶技术 19 / 法规与标准 18 / 商业化与运营 17 / 车辆与传感器 16 / 场景与表达 15 | v1.3 | data/industry-autonomous/terms.md | 2026-11-13 |
| industry-technology | 技术行业 | TEC | 74 | 岗位与协作 14 / 技术栈与架构 12 / 数据与人工智能 11 / 云与基础设施 10 / 安全与合规 10 / 开发与工程实践 10 / 场景与表达 7 | v1.2 | data/industry-technology/terms.md | 2026-11-13 |
| economy-finance | 经济与财务 | ECF | 73 | 个人财务与税务 14 / 宏观与经济指标 12 / 金融机构与工具 12 / 市场机制与交易 10 / 估值与风险 9 / 监管与政策 9 / 场景与表达 7 | v1.2 | data/economy-finance/terms.md | 2026-11-13 |
| visa-immigration | 签证与移民 | VIS | 69 | 在留资格类型 15 / 申请与审查流程 14 / 永住与归化 12 / 家属与生活 10 / 法规与政策 10 / 场景与表达 8 | v1.2 | data/visa-immigration/terms.md | 2026-11-13 |
| politics-law | 政治与法律 | LAW | 69 | 法律体系与条文 13 / 劳动与民事法律 12 / 政治制度与机构 12 / 行政与司法程序 12 / 场景与表达 10 / 政策与选举 10 | v1.2 | data/politics-law/terms.md | 2026-11-13 |
| education-qualification | 教育与资格 | EDU | 68 | 教育体系与阶段 13 / 考试与备考 12 / 资格与认证 12 / 学费与资助 11 / 场景与表达 10 / 院校与专业 10 | v1.1 | data/education-qualification/terms.md | 2026-11-13 |
| language-japanese | 日语语言 | JPN | 69 | 语言能力与考试 13 / 语法与句型 12 / 词汇与表达 11 / 学习与教学 9 / 场景与表达 8 / 敬语与语体 8 / 职场日语 8 | v1.2 | data/language-japanese/terms.md | 2026-11-13 |
| culture-life | 文化与生活 | CUL | 70 | 公共服务与设施 13 / 文化习俗与节庆 12 / 日常生活与居住 12 / 饮食与消费 12 / 社交与礼仪 11 / 场景与表达 10 | v1.2 | data/culture-life/terms.md | 2026-11-13 |
| regional-info | 地区信息 | REG | 69 | 人口与城市 12 / 地方政策与自治 12 / 行政区划与地理 12 / 地方经济与产业 11 / 场景与表达 11 / 生活成本与设施 11 | v1.2 | data/regional-info/terms.md | 2026-11-13 |
| exit-transition-return | 退出·转型·回国 | ETR | 25 | 转型与在留资格 7 / 税务与住民 5 / 资产与生活清理 4 / 年金与保险 3 / 离境与再入国 3 / 退出与劳动 3 | v1.1 | data/exit-transition-return/terms.md | 2026-11-14 |

合计：14 个主题，1077 条词条。

## 上层对接

- 结构化导出：各主题 `data/<topic>/exports/` 下的 JSON / JSONL / CSV（数据契约见 README 第六节）。
- 检索建议：以词条 ID 为主键，别名与标签作为索引字段，分类作为过滤面。
