# 报告模板类型注册表（template-registry）

> **定位**：`report_templates/` 通用层的**类型分类注册表**。记录已注册的报告类型维度、各类型的模板清单与适用业务线，并规定新增类型 / 新增业务线的动态接入步骤。通用基座与跨类型渲染规范常驻本目录根部，类型专属模板按类型 ID 分目录存放——新增类型只加目录、不改既有结构。行业主流类型的**全谱系分类与选型参考**见 [report-classification.md](./report-classification.md)（六族十三类，本注册表只登记其中已模板化的类型）；登记册结构标准见 [registry-schema.md](./registry-schema.md)。

---

## 一、目录分类架构

```
report_templates/
├── prompt-generic-base.md        # 通用基座（类型中立，全部类型共享）
├── monitoring-common-spec.md     # 渲染/排版/交付通用规范（跨类型共享最低标准）
├── handbook-split-standard.md    # 知识手册拆分操作规范 + 可复用提示词模板（跨主题共享）
├── template-registry.md          # 本注册表（类型接入点）
├── report-classification.md      # 行业主流分类体系（六族十三类，新增类型选型参考）
├── registry-schema.md            # 指标登记册 Schema 规范（v1/v2 活值表与 C-08/C-10/C-13 判定）
├── compliance-rules.json         # 合规校验规则（13 类结构骨架 × 周期，CI 阻断式校验关卡依据）
├── fact-card-standard.md         # 事实卡片标准（五字段 / [@FC-NNN] 指针 / 跨报告重复率）
├── l5-semantic-review.md         # L5 语义复核提示词（审计 L5 六项清单）
├── market-monitoring/            # 类型一：市场指标监测型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-monthly-monitor-template.md
│   ├── prompt-quarterly-analysis-template.md
│   └── prompt-annual-review-template.md
├── trend-weekly/                 # 类型十三：行业趋势周报型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-weekly-monitor-template.md
│   ├── business-prompt-scaffold.md
│   └── prompts/
│       ├── prompt-baseline-setup.md
│       └── prompt-weekly-monitor.md
├── employment-research/          # 类型二：职业就业调研型
│   ├── prompt-baseline-setup-template.md
│   └── prompt-update-template.md
├── competitive-intelligence/     # 类型三：竞争情报监测型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-monthly-update-template.md
│   ├── business-prompt-scaffold.md
│   └── prompts/                  # 泛用版业务提示词（变量化，建业务线复制后填值）
│       ├── prompt-baseline-setup.md
│       ├── prompt-monthly-monitor.md
│       └── prompt-flash-update.md
├── sentiment-monitoring/         # 类型四：舆情传播监测型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-monthly-update-template.md
│   ├── business-prompt-scaffold.md
│   └── prompts/
│       ├── prompt-baseline-setup.md
│       ├── prompt-monthly-monitor.md
│       └── prompt-flash-warning.md
├── consumer-research/            # 类型五：消费者·用户调研型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-study-template.md
│   ├── business-prompt-scaffold.md
│   └── prompts/
│       ├── prompt-baseline-setup.md
│       └── prompt-study.md
├── industry-research/            # 类型六：行业深度研究型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-annual-refresh-template.md
│   ├── business-prompt-scaffold.md
│   └── prompts/
│       ├── prompt-baseline-setup.md
│       └── prompt-annual-refresh.md
├── market-sizing/                # 类型七：市场规模测算与预测型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-annual-refresh-template.md
│   ├── business-prompt-scaffold.md
│   └── prompts/
│       ├── prompt-baseline-setup.md
│       └── prompt-annual-refresh.md
├── investment-research/          # 类型八：投资分析与尽调型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-target-update-template.md
│   ├── business-prompt-scaffold.md
│   └── prompts/
│       ├── prompt-baseline-setup.md
│       └── prompt-target-review.md
├── policy-analysis/              # 类型九：政策法规解读型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-policy-review-template.md
│   ├── business-prompt-scaffold.md
│   └── prompts/
│       ├── prompt-baseline-setup.md
│       └── prompt-policy-review.md
├── feasibility-study/            # 类型十：可行性与市场进入型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-study-template.md
│   ├── business-prompt-scaffold.md
│   └── prompts/
│       ├── prompt-baseline-setup.md
│       └── prompt-project-study.md
├── flash-commentary/             # 类型十一：快评·事件点评型
│   ├── prompt-baseline-setup-template.md
│   ├── prompt-flash-note-template.md
│   ├── business-prompt-scaffold.md
│   └── prompts/
│       ├── prompt-baseline-setup.md
│       └── prompt-flash-note.md
└── whitepaper/                   # 类型十二：白皮书·专题深度型
    ├── prompt-baseline-setup-template.md
    ├── prompt-topic-study-template.md
    ├── business-prompt-scaffold.md
    └── prompts/
        ├── prompt-baseline-setup.md
        └── prompt-topic-study.md
```

- **根部共享**：通用基座定义跨类型质量规则、变量框架、来源分级、锚定与台账协议；渲染规范定义 HTML 报告的最低渲染标准；合规规则文件登记各类型各周期的结构骨架校验规则（节数 / 必填字段 / 内容格式），供 `src/prompts-tools/tools/compliance_check.py` 的 CI 阻断式校验关卡与定期合规审计消费。任何类型的模板与业务提示词均继承根部文件。
- **类型目录**：目录名 = 类型 ID（小写 kebab-case）；每类型必备一份基线类型模板（`prompt-baseline-setup-template.md`），周期模板按类型的节拍设计自定（文件名以 `prompt-` 开头、以 `-template.md` 结尾）。
- **业务提示词脚手架**：market-monitoring 与 employment-research 已有完整业务线实践；其余 11 个类型各含一份 `business-prompt-scaffold.md`——复制式业务提示词脚手架（实例化步骤 + business-config 实例化清单 + 提示词正文指针，链接按复制到 `{TOPIC_DIR}/prompts/` 后的位置书写，即 `../../src/report_templates/...`）。新增业务线时复制脚手架、填变量与 TODO 项即可运行；脚手架自身为类型中立文件，不含业务关键词。
- **泛用版业务提示词（prompts/ 子目录）**：上述 11 个类型另将脚手架拆分为独立可运行的泛用版业务提示词，存放于 `report_templates/<类型ID>/prompts/`（`prompt-baseline-setup.md` + 各周期提示词 + 可选事件触发专项，共 24 份）。泛用版 = 绑定类型的业务提示词母版：变量区（{{REGION}}/{{TOPIC}} 等）+ 类型模板引用 + TODO 业务项；建新业务线时整目录复制到业务 `prompts/`、填变量与 TODO、补 `business-config.md` 即可运行。**要点一致**：周期提示词的任务目标 / 硬性约束 / 骨架引用须与类型模板同口径；修改时同步类型模板与 prompts/ 泛用版两处（脚手架仅保留实例化指南，不再重复正文）。审计协议（落盘后审计节）在脚手架 / 泛用版层级承载，复制后须逐份保留。

## 二、已注册类型清单

| 类型 ID | 类型名称 | 基线模板 | 周期模板 | 节拍设计 | 已接入业务线 |
|---|---|---|---|---|---|
| market-monitoring | 市场指标监测型 | prompt-baseline-setup-template.md | monthly / quarterly / annual（三份独立） | 月 / 季 / 年三周期 | 13-regional-info, 19-safety-disaster |
| trend-weekly | 行业趋势周报型 | prompt-baseline-setup-template.md | prompt-weekly-monitor-template.md | 周报主节拍（数据截止日命名）+ 事件触发板块升级 | 暂无 |
| employment-research | 职业就业调研型 | prompt-baseline-setup-template.md | prompt-update-template.md（一份覆盖三档节拍） | 季度主节拍 + 事件触发；月度核验轻运行；年度复盘 | 00-decision-hub, 01-ssw-driver, 02-career-driver, 03-career-management, 07-economy-finance, 10-education-qualification, 11-language-japanese, 12-culture-life, 14-life-operations, 15-health-wellbeing, 17-migration-compliance, 18-family-parenting |
| competitive-intelligence | 竞争情报监测型 | prompt-baseline-setup-template.md | prompt-monthly-update-template.md（覆盖两档） | 月度主更新（动态矩阵刷新）+ 事件触发升级 | 暂无 |
| sentiment-monitoring | 舆情传播监测型 | prompt-baseline-setup-template.md | prompt-monthly-update-template.md（覆盖两档） | 月度舆情月报 + 事件触发预警升级 | 暂无 |
| consumer-research | 消费者·用户调研型 | prompt-baseline-setup-template.md | prompt-study-template.md（项目制） | 项目制专题调研 + 年度满意度复测 | 暂无 |
| industry-research | 行业深度研究型 | prompt-baseline-setup-template.md | prompt-annual-refresh-template.md | 一次性深度全景 + 年度刷新（重大事件可插刷） | 04-industry-logistics, 05-industry-autonomous, 06-industry-technology |
| market-sizing | 市场规模测算与预测型 | prompt-baseline-setup-template.md | prompt-annual-refresh-template.md | 一次性测算建模 + 年度假设刷新与回测（失效信号可插刷） | 暂无 |
| investment-research | 投资分析与尽调型 | prompt-baseline-setup-template.md | prompt-target-update-template.md | 首次覆盖 + 定期复核 + 事件触发结论修订 | 暂无 |
| policy-analysis | 政策法规解读型 | prompt-baseline-setup-template.md | prompt-policy-review-template.md（覆盖两档） | 事件触发单份解读 + 年度台账复盘 | 08-visa-immigration, 09-politics-law, 16-exit-transition-return, 20-overseas-china |
| feasibility-study | 可行性与市场进入型 | prompt-baseline-setup-template.md | prompt-study-template.md（项目制） | 项目制一次性论证 + 项目复盘 | 暂无 |
| flash-commentary | 快评·事件点评型 | prompt-baseline-setup-template.md（机制文档） | prompt-flash-note-template.md | 事件触发 72h 快评（基线期为机制建立，不出正文） | 暂无 |
| whitepaper | 白皮书·专题深度型 | prompt-baseline-setup-template.md | prompt-topic-study-template.md（选题制） | 新选题白皮书 + 年度系列篇 + 框架修订篇 | 暂无 |

> **命名兼容性说明**：节拍为月度 / 季度 / 年度 / 周度的类型，产出命名与 `src/prompts-tools/tools` 标准正则（monthly / quarterly / annual / baseline / weekly）兼容；项目制与事件触发类型（consumer-research、feasibility-study、flash-commentary、policy-analysis、investment-research、whitepaper 的一次性件）使用 `{{YYYY-MM-DD}}-主题.md` 通用命名，`validate.py` 仅提示 WARN 不阻断，属预期行为。

## 三、动态接入步骤

### 3.1 新增报告类型（不改动既有结构）

0. 先查 [report-classification.md](./report-classification.md)：确认目标报告类型在六族十三类中的归属与边界（避免与既有类型交叉重叠），并参考第四节选型优先级决定是否模板化。
1. 在 `report_templates/` 下新建类型目录（类型 ID，小写 kebab-case），撰写该类型的基线类型模板与周期类型模板（头部继承声明指向根部通用基座与渲染规范）。
2. 模板内**严禁**出现任何业务关键词（地区 / 机构 / 专属指标，校验见 `src/prompts-tools/tools/validate.py`）。
3. 在本注册表第二节清单登记：类型 ID、名称、模板文件、节拍设计。
4. 在 `src/prompts-tools/tools/_common.py` 的 `TEMPLATE_TYPE_DIRS` 中登记类型 ID 与必备文件清单（供 validate.py 校验）。
5. 在 `report_templates/compliance-rules.json` 登记该类型各周期结构骨架规则（节数 / 节名参考 / 模板文件），供合规校验关卡与审计消费（未登记的类型其报告按警告处理）。

### 3.2 已有类型下新增业务线

1. 按[通用基座第 1.2 节](./prompt-generic-base.md)执行：建立 `{地区}/{业务类型}/` 目录（prompts / data / reports），撰写 `business-config.md`（业务单一事实源）。
2. 按类型节拍设计建立业务周期提示词，头部继承声明指向 `../../src/report_templates/<类型ID>/` 下对应类型模板。
3. 首期运行基线提示词，建立登记册与基线锚；业务线注册到本注册表第二节「已接入业务线」列。

### 3.3 类型退役 / 合并

1. 业务线迁移完成后，从第二节清单移除并在「变更记录」留痕；类型目录归档前须确认无业务线引用（全仓 grep 类型 ID）。
2. 不物理删除历史类型目录，除非版本记录中明确批准。

## 四、变更记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 建立双类型分类架构（market-monitoring / employment-research）与动态接入规程 |
| v1.1 | 2026-11-13 | 新增 report-classification.md | 通用层补充行业主流分类体系（六族十二类，历史口径）作为新增类型选型参考；3.1 接入流程前置选型步骤 |
| v1.2 | 2026-11-13 | 全类型模板骨架接入 | 依 report-classification.md 将其余 10 个主流类型全部模板化并注册（competitive-intelligence / sentiment-monitoring / consumer-research / industry-research / market-sizing / investment-research / policy-analysis / feasibility-study / flash-commentary / whitepaper），每类型基线 + 周期模板各一份；_common.py TEMPLATE_TYPE_DIRS 同步登记；新增命名兼容性说明 |
| v1.3 | 2026-11-13 | 业务提示词脚手架 | 其余 10 个类型各新增 business-prompt-scaffold.md（复制式业务提示词脚手架：实例化步骤 + business-config 清单 + 各周期提示词全文脚手架），对接通用基座 1.2 节新增业务线流程 |
| v1.4 | 2026-11-13 | 合规校验规则接入 | 新增根部共享文件 compliance-rules.json（12 类 × 周期结构骨架校验规则）；src/prompts-tools/tools/compliance_check.py 提供 CI 阻断式模板合规校验关卡、--scaffold 模板自动填充引导与 --audit 历史报告合规审计；3.1 接入流程追加第 5 步（合规规则登记） |
| v1.5 | 2026-11-13 | 泛用版业务提示词 | 其余 10 个类型各新增 prompts/ 子目录（共 22 份独立泛用版业务提示词：基线 + 主周期 + 竞争情报 / 舆情事件触发专项），由 business-prompt-scaffold.md 拆分；建新业务线时整目录复制填值即用 |
| v1.6 | 2026-11-13 | 新增类型十三：行业趋势周报型（trend-weekly） | 注册周节拍类型（基线机制文档 + 八节周报模板 + scaffold + 泛用 prompts ×2）；_common.py TEMPLATE_TYPE_DIRS 登记；compliance-rules.json 登记八节骨架；周报命名 `{YYYY-MM-DD}_weekly`（日期 = 数据截止日）纳入标准正则；首条业务线 trends/ai-security 接入 |
| v1.7 | 2026-11-13 | 首条 industry-research 业务线接入 | jp/04-industry-logistics 接入（基线已产出 2026-11，年度刷新节拍）；其现行四章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续刷新按九节骨架执行 |
| v1.8 | 2026-11-13 | 第二条 employment-research 业务线接入 | jp/01-ssw-driver 接入（基线已产出 2026-11，季度主节拍 + 事件触发；月度核验轻运行；年度复盘）；其现行八章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续报告按九节骨架执行 |
| v1.9 | 2026-11-13 | 第三条 employment-research 业务线接入 | jp/02-career-driver 接入（基线已产出 2026-11，季度主节拍 + 事件触发；月度核验轻运行；年度复盘）；其现行六章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续报告按九节骨架执行 |
| v1.10 | 2026-11-13 | 第四条 employment-research 业务线接入 | jp/03-career-management 接入（基线已产出 2026-11，季度主节拍 + 事件触发；月度核验轻运行；年度复盘）；其现行六章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续报告按九节骨架执行 |
| v1.11 | 2026-11-13 | 第二条 industry-research 业务线接入 | jp/05-industry-autonomous 接入（基线已产出 2026-11，一次性深度全景 + 年度刷新）；其现行四章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续刷新按九节骨架执行 |
| v1.12 | 2026-11-13 | 第三条 industry-research 业务线接入 | jp/06-industry-technology 接入（基线已产出 2026-11，一次性深度全景 + 年度刷新）；其现行三章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续刷新按九节骨架执行 |
| v1.13 | 2026-11-13 | 第五条 employment-research 业务线接入 | jp/07-economy-finance 接入（基线已产出 2026-11，薪酬与生活成本对标，季度主节拍 + 事件触发；月度核验轻运行；年度复盘）；其现行四章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续报告按九节骨架执行 |
| v1.14 | 2026-11-13 | 首条 policy-analysis 业务线接入 | jp/08-visa-immigration 接入（基线已产出 2026-11，事件触发单份解读 + 年度台账复盘）；其现行九章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续解读 / 复盘按九节骨架执行 |
| v1.15 | 2026-11-13 | 第二条 policy-analysis 业务线接入 | jp/09-politics-law 接入（基线已产出 2026-11，事件触发单份解读 + 年度台账复盘）；其现行三章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续解读 / 复盘按九节骨架执行 |
| v1.16 | 2026-11-13 | 第六条 employment-research 业务线接入 | jp/10-education-qualification 接入（基线已产出 2026-11，季度主节拍 + 事件触发；月度核验轻运行；年度复盘）；其现行四章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续报告按九节骨架执行 |
| v1.17 | 2026-11-13 | 第七条 employment-research 业务线接入 | jp/11-language-japanese 接入（基线已产出 2026-11，季度主节拍 + 事件触发；月度核验轻运行；年度复盘）；其现行六章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续报告按九节骨架执行 |
| v1.18 | 2026-11-13 | 第八条 employment-research 业务线接入 | jp/12-culture-life 接入（基线已产出 2026-11，季度主节拍 + 事件触发；月度核验轻运行；年度复盘）；其现行五章结构与九节骨架的映射在业务 business-config 第三、九节声明，后续报告按九节骨架执行 |
| v1.19 | 2026-11-13 | 第二条 market-monitoring 业务线接入 | jp/13-regional-info 接入（基线已产出 2026-11，月 / 季 / 年三周期）；其现行两章结构与十节骨架的映射在业务 business-config 第三、九节声明，后续报告按十节骨架执行；因属个人地域决策支持场景，K/RL 阈值信号与供给情景机制不适用的适配在 business-config 第 3.2 节声明 |
| v1.20 | 2026-11-14 | 跨主题决策层接入 | jp/00-decision-hub 接入（employment-research 型，跨主题综合层：五问框架 / 只读消费纪律 / 缺失清单；不落研究正文）；结构映射在 business-config 第三节声明 |
| v1.21 | 2026-11-14 | 第九条 employment-research 业务线接入 | jp/14-life-operations 接入（基线已产出 2026-11，季度复核 + 事件触发）；个人执行层（在留 / 住民 / 住房 / 交通 / 通信 / 银行 / 水电 / 90 天清单）；结构映射在 business-config 第 3.2 节声明 |
| v1.22 | 2026-11-14 | 第十条 employment-research 业务线接入 | jp/15-health-wellbeing 接入（基线已产出 2026-11，季度复核 + 事件触发）；个人健康管理（医保 / 就医 / 多语言通译 / 牙科精神科 / 心理 / 体检 / 介護）；结构映射在 business-config 第 3.2 节声明 |
| v1.23 | 2026-11-14 | 第三条 policy-analysis 业务线接入 | jp/16-exit-transition-return 接入（基线已产出 2026-11，事件触发单份解读 + 年度台账复盘）；政策执行层（退出 / 转型 / 回国）；不做 07 / 08 / 14 的制度正文复制；结构映射在 business-config 第 3.3 节声明 |
| v1.24 | 2026-11-14 | 新增根部共享操作规范 handbook-split-standard.md | 沉淀 12-culture-life 手册拆分实践（提交 4d3e200）为跨主题可复用标准化提示词模板：双产物分离原则、编号即接口约束、归属映射/边界裁定表、执行清单 ①–⑧、链接锚点规范、验证清单（含 URL 守恒与仓库测试）、提交规范、HTML 预览页设计系统；供其余含合并附录手册的主题统一执行 |
| v1.25 | 2026-11-15 | 归类为十三类标准 + 登记册 Schema | report-classification 统一为「六族十三类」；新增根部 registry-schema.md（v1/v2 活值表 Schema 与 C-08/C-10/C-13 判定规则），根部共享清单同步 |
| v1.26 | 2026-11-16 | 模板合规整改 | 脚手架计数 10→11、泛用版计数 22→24；链接口径统一为「复制后位置 `{TOPIC_DIR}/prompts/` → `../../src/report_templates/...`」；「内容与脚手架正文一致」改为「要点一致」并明确审计协议承载层级 |
| v1.27 | 2026-11-17 | 文档治理校准 | 目录树补齐 `fact-card-standard.md` / `l5-semantic-review.md`（两份根部文档此前未登记）；「12 类」更正为 13 类；第二节「已接入业务线」列更新为实际 21 主题目录（00–20）；补记 17–20 主题接入；泛用版计数校准为 24 份 |
| v1.28 | 2026-11-17 | 脚手架正文指针化 | 11 份 `business-prompt-scaffold.md` 的提示词正文统一收口到各类型 `prompts/` 泛用版母版（24 份），脚手架只保留实例化步骤 / business-config 清单 / 审计协议，消除「类型模板 / prompts/ / 脚手架」三处同步 |
| v1.29 | 2026-11-17 | 交叉核查校准 | 校准 v1.5 泛用版计数（23→22）与 v1.27 主题目录数（20→21）；补齐根部活文档版本记录 |
