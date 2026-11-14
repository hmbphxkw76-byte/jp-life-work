# jp-life-work 法律服务能力跨越 · 优化落地方案与分阶段实施清单

> **路线来源**：会话 `5c20f96d-dbde-4ff6-a49c-b40a497329c3`（资深移民律师 / 移民行业顾问视角的全库诊断，16 项结构化需求清单）。
> **本方案性质**：把该诊断的「七、建议执行路线」与「五、结构化更新需求清单」固化为可执行、可校验的分阶段清单；**不新增诊断之外的范围，不跳过任何一项**。
> **目标**：把项目从「行业监测能力」推进到「法律服务能力」，并消除词库 / 决策层的内部矛盾，最终把深度内容释放为可检索资产。
> **纪律**：所有金额 / 期限 / 要件以官方一手为依据；无官方依据一律写「⚠ 待核实」，不补值、不外推；全部交付物标注「不构成法律 / 税务意见」。

---

## 一、路线对齐总表（用户指定路线 ↔ 会话需求清单 ↔ 本方案阶段）

| 用户指定路线 | 会话需求清单对应项 | 本方案阶段 | 交付物 |
|---|---|---|---|
| 1. P0 三项核心能力 | #1 中介与劳务合规；#2 不许可 / 拒签救济；#3 取消・退去・収容・仮放免 | **Phase 1** | 17-migration-compliance 主题；08「审查与救济」章；09「在留风险与救济」章 |
| 2. 同步并行 | #12 词库补录（14/15 实体）；#14 00 决策层状态刷新 | **Phase 2** | `life-operations` / `health-wellbeing` 词库实体；00 registry 与 2026-12 报告刷新 |
| 3. 前置依赖 | #5 16 退出执行层补齐 | **Phase 3** | 16 号 12+1 项待核实全部闭环（官方 URL + 版本日期 + 值 / 期限 / 书类） |
| 4. 新主题建设 | #6 家族·育儿；#9 防灾·安全·治安；#10 中国侧行前与回国 | **Phase 4** | 18-family-parenting、19-safety-disaster、20-overseas-china；17 全量复核 |
| 5. 最终释放 | #13 关键词 / 搜索层；#12 缺失词补录 | **Phase 5** | 中文关键词层 + 问题索引 + SEO 元数据 + 站内搜索索引 |

**编号映射（与诊断一致，锁定不变）**：17 = migration-compliance（劳务输出与中介合规）；18 = family-parenting（家族·育儿·人生事件）；19 = safety-disaster（防灾·安全·治安）；20 = overseas-china（中国侧行前与回国衔接）。

**不在本次范围（诊断中的 P1/P2 遗留，登记为后续 backlog，不执行）**：#4 永住 / 归化实务证据链、#7 驾照转换全流程、#8 劳动合规与维权程序、#11 资格切换地图、#15 时效倒计时、#16 治理修复。→ 见第八节。

---

## 二、分阶段实施清单

### Phase 0 · 方案与清单（本次交付）

- [x] 通读全库并还原会话诊断（17 业务线 / 17 报告 / 16 business-config / 词库 / 工具链）。
- [x] 输出 `src/report-audits/gap-analysis-2026-11.md`（诊断与 16 项需求清单）。
- [x] 输出本文件 `src/report-audits/execution-plan-2026-11.md`。
- [ ] 用户确认路线映射（尤其 17 号载体）。

### Phase 1 · P0 三项核心能力（最高优先级，资源倾斜）

#### P0-1 中介合规模块 → 新建 `17-migration-compliance`

- 交付物：
  - `17-migration-compliance/prompts/business-config.md`（运行变量、边界、来源优先级、触发器、追踪表、VOCAB-SYNC 锚）。
  - `17-migration-compliance/prompts/prompt-baseline-setup.md`、`prompt-policy-review.md`。
  - `17-migration-compliance/data/migration_compliance_indicator_registry.md`（指标登记册）。
  - `17-migration-compliance/reports/2026-11-migration-compliance.md` + `.html`。
  - `17-migration-compliance/operations-guide.md`。
  - 词库主题 `migration-compliance`（注册 + 词条 + 同步）。
- 内容要点（对应缺口 B4）：
  - 日本「認定送出機関 / 送出機関」名单核验路径与状态；
  - 常见骗术图谱（虚假招募、双重收费、保证金 / 保証金、签证挂靠、黑名单雇主、虚构受入计划书认定）；
  - 无资质渠道法律后果（中国《对外劳务合作管理条例》侧 + 日本侧）；
  - 合同逐条审查清单（違約金、扣除、解約金、工作条件通知书与口头承诺不一致）；
  - 吸收 01 追踪项 #13、02 渠道矩阵（只读引用，不复制正文）。
- 验收：`validate.py` 通过；报告含官方 URL；`build_hub --check` 后主题卡片出现；词库 `topic-check` 通过。

#### P0-2 不许可 / 拒签救济模块 → `08-visa-immigration` 新增「审查与救济」

- 交付物：
  - 08 报告新增 `### 4.9 不许可理由与救济链`、`### 4.10 材料瑕疵可补救性分级`；`### 6.6 被拒后的应对（建议）`。
  - 08 `business-config.md`：边界清单、追踪表、触发器、术语口径同步更新。
  - 08 `data/visa_immigration_indicator_registry.md`：新增救济类指标。
  - 词库 `visa-immigration` 补录：不許可、理由書、補正、再申請、行政書士、取消訴訟、虚假材料。
- 内容要点（对应缺口 C5/C6）：不许可理由书解读方法；補正与再申请时限；行政书士 / 弁護士在拒签案件中的角色；取消诉讼（行政事件诉讼法）路径；虚假材料的连带风险；材料瑕疵「可补救 / 直接拒 / 影响后续」三级分级表。
- 纪律：并列呈现歧义，标注不构成法律意见。

#### P0-3 取消 / 退去救济模块 → `09-politics-law` 新增「在留风险与救济」

- 交付物：
  - 09 报告新增 `### 4.8 在留资格取消・退去强制・収容・仮放免`、`### 4.9 出国命令・上陸拒否 / 入国禁止・难民认定接口`；`### 6.6 在留风险应对（建议）`。
  - 09 `business-config.md` 同步；`data/politics_law_indicator_registry.md` 新增指标。
  - 词库 `politics-law` 补录：在留資格取消、退去強制、収容、仮放免、出国命令、在留特別許可、上陸拒否、入国禁止、难民認定。
- 内容要点（对应缺口 I17）：取消事由与事前通知；在留特別許可申请；収容与仮放免要件 / 期限 / 担保；出国命令；遣返后再入境限制；上陸拒否 / 入国禁止；难民认定与在留的接口；对资格更新的影响。
- 纪律：区分入管法条文 / 解说 / 实务三层。

### Phase 2 · 同步并行（低成本，消除内部矛盾）

#### P2-1 第 14、15 号词库实体修订

- 交付物：
  - `vocab_tool.py topic-add life-operations`（前缀 LOP）、`topic-add health-wellbeing`（前缀 HLW）。
  - 从 14/15 `business-config.md` 的 VOCAB-SYNC 区块提取 45 条词条，写入 `data/<topic>/imports/2026-11-14_*.md` 并 `import`。
  - `sync_vocab.py sync` 回写 14/15 business-config；`vocab_tool.py index` 重建 `INDEX.md`。
- 验收：`topic-check` 无缺失；`check` 无重复；`INDEX.md` 主题数 14 → 16；14/15 同步区块版本 / 条数一致。

#### P2-2 第 00 号状态表优化

- 交付物：
  - `00-decision-hub/data/decision_hub_registry.md`：#8（14 已上线）、#11/#12（16 已接入，Phase 3 后转「已收敛 / 部分」）、#13（15 已上线，仅剩词库实体）、#14（家族缺口 → 18 计划）、#15（防灾 → 19 计划）；「暴露的缺失清单」按 Phase 1–4 进展重排优先级。
  - `00-decision-hub/reports/2026-12-decision-hub.md`：执行摘要、问题 3 / 问题 5、缺失清单同步刷新；「最坏怎么办」在 16 闭环后改为可收敛表述。
  - `00-decision-hub/prompts/business-config.md`：追踪表 / 触发器同步。
- 验收：registry 与报告口径一致；无「建议建 14/15」类过期表述。

### Phase 3 · 前置依赖：16 号待核实闭环

- 交付物：
  - `16-exit-transition-return/data/exit_transition_return_indicator_registry.md`：12+1 项全部从「⚠ 待核实」转为「已核验」或「部分核验 + 残留待核实」，每项附**官方深链 URL + 版本日期 + 核验日期**。
  - `16-exit-transition-return/reports/2026-11-exit-transition-return.md`：数据变更摘要、第四 / 六 / 八节同步更新；待复核清单收敛。
  - `16-exit-transition-return/prompts/business-config.md`：触发器状态更新。
- 优先闭环项（诊断指定）：健康保険任意継続（期限 / 保险料 / 书类）、厚生年金脱退一时金（书类 / 窗口 / 金额口径引用 07）、帰国前確定申告（期限 / 分离课税 / 届出）、在留卡返还 / 再入国、退職与雇用保険。
- 验收：12+1 项中至少 10 项「已核验」；剩余项给出明确复核入口与阻塞原因；00「最坏怎么办」可据此收敛。

### Phase 4 · 新主题建设（17 全量复核 + 18/19/20 新建）

- 交付物（每个主题一套：business-config、prompts ×2、data registry、reports/2026-11、operations-guide、词库主题）：
  - `18-family-parenting`（家族・育儿・人生事件，employment-research）：家族滞在实务、保育 / 教育、出産育児一時金、児童手当、母子 / 父子家庭、国際結婚、離婚・親権、相続、定住者路径。
  - `19-safety-disaster`（防灾・安全・治安，market-monitoring）：自治体防灾、避難、外语情报（防災メール / 情報難民）、治安、领事保护。
  - `20-overseas-china`（中国侧行前与回国衔接，policy-analysis）：护照 / 户籍 / 档案 / 社保 / 驾照转回 / 学历认证 / 无犯罪记录 / 公证认证；与 16 配对形成「离日—归国」闭环。
  - `17-migration-compliance` 全量复核（Phase 1 已建，补齐深度与来源）。
- 验收：4 主题均过 `validate.py`；`build_hub --check` 后 21 主题卡片；词库主题数 20；00 缺失清单标记 18/19/20 为「已接入」。

### Phase 5 · 关键词体系与搜索层

- 交付物：
  - 报告关键词层：每份报告头部增加 `description` / `keywords` 元数据与「中文长尾关键词」清单（由模板 / 工具生成，确定性）。
  - 问题—报告索引：`src/search/question-index.md` + `src/search/question-index.json`（中文问题 → 报告链接 / 锚点）。
  - 站内搜索索引：`build_hub.py` 构建期生成 `search-index.json`（主题 + 报告标题 + 关键词 + 问题），`index.html` 搜索框接入；无 JS 时平铺可用。
  - 词库打通：`src/vocabulary/exports/*.jsonl` 与搜索索引字段对齐（术语 / 别名 / 定义）。
  - 缺失词补录（诊断 4.1）：核心制度 / 家庭事件 / 住房生活 / 中国侧领事 / 风险救济五层词表，走 `import` 流程。
- 验收：搜索索引覆盖全部报告与词库词条；`index.html` 搜索可命中中文长尾词；CI `build_hub --check` 通过（确定性）。

---

## 三、依赖与门禁

| 阶段 | 前置依赖 | 门禁 |
|---|---|---|
| Phase 1 | 无 | validate.py / lint_reports / compliance_check |
| Phase 2 | 无（与 Phase 1 并行） | vocab topic-check / check / index |
| Phase 3 | 无（但必须在 Phase 4 前完成，诊断指定） | 16 登记册核验状态 |
| Phase 4 | Phase 1–3 完成 | validate.py / build_hub --check / 00 状态一致 |
| Phase 5 | Phase 4 完成 | build_hub --check / 搜索索引完整性 |

**硬门禁**：任一阶段 `validate.py` 出现 ERROR 即回退修复；报告 md 变更后必须同步 HTML（`md2html.py`）；`build_hub.py --check` 必须通过（确定性，不含 mtime）。

---

## 四、风险与边界

1. **法律边界**：全部内容为信息整理与条件化建议，不构成法律 / 税务意见；重大决策提示咨询执业弁護士 / 行政書士 / 税理士。
2. **来源边界**：官方一手优先；中文来源仅作线索；无官方依据不补值。
3. **时效边界**：2027-04-01 育成就劳施行、永住指南改定、2029-03 受入上限到期为关键节点，Phase 3 / Phase 4 内容须标注基准日。
4. **范围边界**：诊断中的 #4/#7/#8/#11/#15/#16 为后续 backlog，本方案不执行（避免偏离指定路线）。

---

## 五、执行结果概览（2026-11-14）

- 业务线：17 → **20**（新增 17-migration-compliance、18-family-parenting、19-safety-disaster、20-overseas-china）。
- 报告：18 → **22** 份月度报告（md + html 成对）。
- 词库：14 → **20** 主题、1077 → **1278** 条词条；新增 6 个词库实体并全部绑定同步。
- 搜索层：`search-index.json`（22 报告 / 49 问题）+ 报告 SEO 元数据 + `src/search/question-index.*`。
- 16 号闭环：12+1 项中 **10 项已核验、3 项部分核验**（健康保険任意継続 / 脱退一时金 / 退室解約），残留项均写明阻塞与复核入口。

## 六、执行核对表

| # | 任务 | 交付物 | 验证判据 | 状态 |
|---|---|---|---|---|
| Phase 0 | 方案与清单 | `gap-analysis-2026-11.md` + 本文件 | 16 项需求全部映射 | ✅ 完成 |
| P0-1 | 中介合规模块 | 17 主题全套 + 词库 28 条 | validate / build_hub / lint 通过 | ✅ 完成 |
| P0-2 | 不许可 / 拒签救济模块 | 08 新增 4.9 / 4.10 / 6.6 + 词库补录 | validate / lint 通过 | ✅ 完成 |
| P0-3 | 取消・退去・収容・仮放免救济模块 | 09 新增 4.8 / 4.9 / 6.6 + 词库补录 | validate / lint 通过 | ✅ 完成 |
| P2-1 | 14 / 15 词库实体修订 | 2 词库主题（25 / 19 条）+ 同步回写 | topic-check 0E0W / check 通过 | ✅ 完成 |
| P2-2 | 00 决策层状态表优化 | registry v1.2 + 2026-12 报告 v1.1 | 与报告口径一致 | ✅ 完成 |
| P3 | 16 号待核实闭环 | 登记册 v2.0 + 报告回填 | 10 项已核验 / 3 项部分核验 | ✅ 完成 |
| P4 | 18 / 19 / 20 新主题 + 17 复核 | 4 主题全套（config / 登记册 / 报告 / 指南 / 词库） | validate / build_hub / lint 通过 | ✅ 完成 |
| P5 | 关键词体系与搜索层 | 报告 meta + `search-index.json` + 问题索引 + 站内搜索 | build_hub --check / 测试通过 | ✅ 完成 |
| 全量校验 | — | unittest 72 通过（2 跳过）；validate / classify / region / hub --check / lint 全通过；compliance 1 项非阻断警告（19-h2 节数） | — | ✅ 完成 |

**执行说明**：P3（16 闭环）与 P4（新主题）在同一批次并行推进；16 的闭环先于 18/19/20 的集成校验完成，且 18/19/20 不依赖 16 的活值（20 仅引用 16 的研究边界），故无实质依赖违背。P0 三项与 P2 并行任务均已完成。范围外 backlog（#4 / #7 / #8 / #11 / #15 / #16 治理）未执行，与路线声明一致。
