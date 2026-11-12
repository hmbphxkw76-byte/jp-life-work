# jp-life-work

面向日本物流行业的个人知识库与长期规划。

- **初期目标**：以**特定技能司机**进入日本物流行业。
- **中期目标**：转向**仓储运营、运输管理、供应链协调、团队长/管理岗**。
- **长期目标**：进入**物流技术、数字化、自动化、无人驾驶相关岗位**，并规划**在留资格切换（司机分野无 2 号）、永住及长期定居路径**。

## 路线图

### 阶段 1：准备与入场

- 明确目标行业：日本物流、运输、仓储。
- 学习基础日语，准备 JLPT / JFT-Basic。
- 了解特定技能1号、汽车运输业、物流仓库相关制度。
- 整理司机岗位要求、薪资结构、工时与合规风险。
- 准备简历、资格材料、面试话术和求职渠道。

### 阶段 2：司机岗位落地

- 确认工作内容：卡车司机、配送司机、仓储运输、冷链运输等。
- 熟悉日本驾照、车辆类型、安全规范、劳动法规。
- 记录实际工作条件：薪资、加班、路线、公司管理方式。
- 积累物流现场经验，包括装卸、调度、客户对接、异常处理。
- 持续强化物流日语和职场日语。

### 阶段 3：向管理岗过渡

- 学习仓储运营、运输管理、排班调度、安全管理。
- 培养团队长/主任所需能力：沟通、汇报、现场管理、异常处理。
- 积累可量化成果：准点率、事故率、效率提升、成本节约。
- 学习管理岗日语，包括会议、报告、邮件、现场指示。
- 评估从司机转为现场管理、运输管理、仓储管理的路径。

### 阶段 4：向技术/数字化方向扩展

- 了解 WMS、TMS、物流系统、数据报表、自动化设备。
- 关注电商物流、冷链、3PL、绿色物流等行业趋势。
- 学习物流数字化岗位所需技能，如系统操作、数据分析、流程优化。
- 跟踪自动驾驶卡车、仓储自动化、无人配送对岗位结构的影响。
- 评估技术岗、系统岗、运营分析岗的进入门槛（这些岗位是技人国的主要落点）。

### 阶段 5：长期定居与永住规划

- 确认特定技能2号是否适用（结论：司机分野无 2 号，须规划资格切换）。
- 按技人国门槛倒推：大学相关专业或 10 年实务经验（详见 monitors-visa-immigration/05）。
- 关键时点：Y3 转管理/企划岗，Y4 提交在留资格变更，Y5 前完成（1 号上限）。
- 规划在留资格、税务、社保、年金、收入证明。
- 记录连续工作年限、收入水平、职业稳定性。
- 跟踪移民政策、永住条件、家属签证、子女教育。
- 形成可长期维护的个人档案与证据链。

## 目录结构

```text
jp-life-work/
├── README.md                     # 项目总览 + 五阶段路线图 + 目录与体系说明
├── monitors-ssw-driver-logistics/ # 监测项目：特定技能司机·物流·智能驾驶
│   ├── data/                     #   指标登记册（活值）
│   ├── prompts/                  #   动态更新提示词（继承公共三层模板）
│   ├── reports/                  #   基线 + 各版本报告（md + html 同目录）
│   └── reviews/                  #   每期运行复盘
├── monitors-visa-immigration/    # 知识库主题：签证与在留资格
│   ├── prompts/                  #   主题专属配置
│   └── reports/                  #   文档群（00-index + 8 篇）+ 同名 HTML
├── monitors-language/            # 知识库主题：日语学习（同构）
├── monitors-career-driver/       # 知识库主题：司机职业阶段
├── monitors-career-logistics/    # 知识库主题：物流运营/管理阶段
├── monitors-logistics-industry/  # 知识库主题：物流行业研究
├── monitors-autonomous-automation/ # 知识库主题：自动驾驶与自动化
├── monitors-economy/             # 知识库主题：经济与薪资
├── monitors-politics-law/        # 知识库主题：政策与法规
├── monitors-technology-industry/ # 知识库主题：技术与数字化
├── monitors-education/           # 知识库主题：教育与资格
├── monitors-culture-life/        # 知识库主题：文化与生活
├── monitors-regional/            # 知识库主题：地域信息
└── prompts/                      # 公共提示词层（三层继承体系）
    ├── monitoring-common-spec.md #   质量规范（单份，跨类型共享）
    ├── 通用基座/                  #   第 1 层：运行变量/锚定/更新协议/追踪表/执行/输出骨架
    ├── 职业就业调研/              #   第 2 层类型模板：行业调研 + 落地建议类
    ├── 市场指标监测/              #   第 2 层类型模板：指标台账 + 信号判定类
    ├── 知识库主题更新/            #   第 2 层类型模板：monitors-* 主题文档群增量回写类
    └── tools/                    #   全库共用脚本（md2html.py）
```

> 每个 `monitors-*` 统一为 `prompts/ + reports/` 两层；`monitors-ssw-driver-logistics` 另有 `data/`（指标活值）与 `reviews/`（每期复盘）。`data/` 子目录按需创建，不预建空目录。
>
> **保留策略**：`reports/` 顶层只保留最新 3 份（`00-index.md` 固定保留），其余移入 `reports/archives/`；归档上限 7 份，超出删最旧。由 `python prompts/tools/archive_reports.py` 执行，`--dry-run` 可预览。

## 动态更新体系（三层提示词继承）

```text
第 1 层  prompts/通用基座/                        运行变量、基线锚定、更新协议、追踪表、执行与输出骨架
第 2 层  prompts/{职业就业调研|市场指标监测|知识库主题更新}/   类型差异（输出形态、结构模板、专属纪律）
第 3 层  monitors-{主题}/prompts/                专属配置（来源清单、事件触发器、追踪指标、已修正事实）
```

- **监测项目**（monitors-*）：按《职业就业调研》或《市场指标监测》类型模板继承，指标活值存项目 `data/` 登记册，运行复盘存 `reviews/`。
- **知识库主题**（monitors-visa-immigration 等 12 个）：按《知识库主题更新》类型模板继承，动态获取的资料**增量回写**主题文档群，变更摘要与待复核清单记入各主题 `00-index.md`。
- 覆盖规则：主题/项目专属 > 类型模板 > 通用基座 > 《监测报告通用规范》；覆盖须显式声明。
- 质量红线（全层强制）：逐点引用 `[Source: URL, 年份]`、来源优先级五层框架、事实与推断分离、口径标注、禁止编造、空窗期不虚构变化。

### 知识库主题目录说明（monitors-*）

每个主题目录以 `00-index.md` 作为目录导航，其余按编号组织内容；每主题自带 `prompts/prompt-{slug}-update.md`（第 3 层动态更新配置）。

| 目录 | 用途 | 现状 | 动态更新配置 |
|------|------|------|------|
| monitors-visa-immigration | 特定技能1号/2号制度、考试与日语要求、申请流程与材料、育成就劳制度新动向、永住与长期在留规划、政策更新日志 | 3 篇（+6 归档） | prompt-visa-immigration-update.md |
| monitors-language | JLPT N4/N3/N2 分阶段备考计划、JFT-Basic 备用方案、学习资源清单与进度跟踪 | 3 篇（+4 归档） | prompt-language-update.md |
| monitors-career-driver | 司机岗位全景、薪资结构与工时合规、安全规范、现场经验积累、求职渠道与面试、实际工作条件记录 | 3 篇（+4 归档） | prompt-career-driver-update.md |
| monitors-career-logistics | 管理岗地图与路径评估、业务知识体系、管理岗日语与沟通、过渡学习计划、成果档案与晋升材料 | 3 篇（+3 归档） | prompt-career-logistics-update.md |
| monitors-logistics-industry | 日本物流产业概览、EC/冷链/3PL 增长赛道、自动化与技术趋势、行业数据跟踪 | 3 篇（+2 归档） | prompt-logistics-industry-update.md |
| monitors-autonomous-automation | 自动驾驶技术路线与时间表、法规与许可制度、仓储自动化与无人配送、个人技能对接与机会 | 3 篇（+2 归档） | prompt-autonomous-automation-update.md |
| monitors-economy | 日本宏观经济、物流行业薪资行情、生活成本与收入规划 | 3 篇（+2 归档） | prompt-economy-update.md |
| monitors-politics-law | 在留法规框架、政治动向与移民政策环境、维权与合规工具箱 | 3 篇（+1 归档） | prompt-politics-law-update.md |
| monitors-technology-industry | 物流数字化技能地图、数字化岗位与转型路径 | 3 篇 | prompt-technology-industry-update.md |
| monitors-education | 资格地图、学习体系与教育投资 | 3 篇 | prompt-education-update.md |
| monitors-culture-life | 职场文化与人际、生活指南与适应 | 3 篇 | prompt-culture-life-update.md |
| monitors-regional | 地域选择框架、地域生活笔记 | 3 篇 | prompt-regional-update.md |

### 其他目录说明

| 目录 | 用途 |
|------|------|
| prompts/ | 公共提示词层：三层继承体系（通用基座 → 类型模板）+ 质量规范 + `tools/` 共用脚本 |
| monitors-ssw-driver-logistics/ | 监测项目：data/prompts/reports/reviews |
| monitors-{主题}/ | 12 个知识库主题：prompts/ + reports/ |

## 使用约定

- **文档格式**：源文档统一使用 Markdown（`.md`），按主题存放在 `monitors-*` 下。
- **报告输出**：`python prompts/tools/md2html.py` 将各 `reports/` 下的 md 转为同名 HTML，与 md 同目录存放并随源文件入库。
- **脚本环境**：`prompts/tools/` 下的共用脚本基于 Python 运行（依赖见 requirements.txt）。
