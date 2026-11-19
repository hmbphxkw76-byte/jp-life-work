# 提示词语义对齐独立验证报告（B8）

> **工单**：`docs/toolchain/tickets/b8-prompt-semantic-alignment.md`（P2）
> **验证对象**：`engine/report_templates/` 下 12 个类型目录的「类型模板 / `prompts/` 泛用版 / `business-prompt-scaffold.md`」三处
> **基线**：工作树 `.worktrees/b-semverify`（分支 `task/b-semverify-e1e33a6c`，起始提交 `d51f39a`）
> **日期**：2026-11-19
> **性质**：只读分析；不改动任何模板语义，差异仅登记

---

## 一、范围与方法

### 1.1 覆盖范围

| 类型 | 类型模板 | `prompts/` 泛用版 | 脚手架 | 三处比对 |
|---|---|---|---|---|
| market-monitoring | 4 份（基线/月/季/年） | 无 | 无 | 不适用（仅基座一致性） |
| employment-research | 2 份（基线/周期） | 无 | 无 | 不适用（仅基座一致性） |
| competitive-intelligence | 2 份 | 3 份 | 1 份 | 适用 |
| sentiment-monitoring | 2 份 | 3 份 | 1 份 | 适用 |
| consumer-research | 2 份 | 2 份 | 1 份 | 适用 |
| industry-research | 2 份 | 2 份 | 1 份 | 适用 |
| market-sizing | 2 份 | 2 份 | 1 份 | 适用 |
| investment-research | 2 份 | 2 份 | 1 份 | 适用 |
| policy-analysis | 2 份 | 2 份 | 1 份 | 适用 |
| feasibility-study | 2 份 | 2 份 | 1 份 | 适用 |
| flash-commentary | 2 份 | 2 份 | 1 份 | 适用 |
| whitepaper | 2 份 | 2 份 | 1 份 | 适用 |

- 实有：**10 份脚手架、22 份泛用版、12 个类型目录**（`market-monitoring` / `employment-research` 按注册表第 105 行口径为「已有完整业务线实践」，不设 `prompts/` 与脚手架）。
- 通用参考：`prompt-generic-base.md`、`template-registry.md`、`report-classification.md`、`compliance-rules.json`、`confidence-grade-standard.md`、`engine/tools/prompt_check.py`、`engine/tools/structure_check.py`、`engine/tools/_common.py`。

### 1.2 方法

1. 提取三处语义要素：**槽位 / 变量 / 继承关系 / 口径定义 / 必填·选填**。
2. 逐条比对：类型模板 ↔ 泛用版 ↔ 脚手架；并以通用基座、注册表、合规规则、命名正则（`_common.MONTH_REPORT_RE`）为交叉参照。
3. 差异分级：**实质冲突**（无法同时满足、会改变产出或校验结果）/ **表述差异**（语义等价但措辞、结构、编号或元数据漂移）/ **设计内**（由设计决定、有文档依据）。

### 1.3 语义要素总览（提取结果）

| 类型 | 基线骨架 | 周期骨架 | 类型专属变量 | 继承声明 | 关键口径 |
|---|---|---|---|---|---|
| market-monitoring | 10 节 | 月 8 / 季 10 / 年 10 | `REGISTRY_FILE`、`NEXT_YEAR`、`OUTPUT_REGISTRY` | 四层 | 五态、K/RL 红线、T+1、预算台账 |
| employment-research | 9 节 | 月/季/年 9 节 | `SOURCE_LANGUAGE_RULE` | 四层 | 薪酬「岗位×职级」交叉分层、建议标「建议/推断」 |
| competitive-intelligence | 9 节 | 9 节（月+事件） | `EVENT_NAME` | 四层 | 公开信息边界、关键动作 2 家独立来源 |
| sentiment-monitoring | 9 节 | 9 节（月+预警） | `EVENT_NAME` | 四层 | 言论≠事实、环比口径一致 |
| consumer-research | 8 节 | 8 节（项目制） | `STUDY_TYPE` | 四层 | 一手数据为主、不显著降级「方向性发现」 |
| industry-research | 9 节 | 9 节（年+插刷） | — | 四层 | 中性立场、多口径并列、趋势复判 |
| market-sizing | 9 节 | 9 节（年+插刷） | `OUTPUT_REGISTRY` | 四层 | 区间+三情景、回测归因 |
| investment-research | 8 节 | 8 节（定期+事件） | `TRIGGER_TYPE` | 四层 | 结论必须明确、官方原文、估值留痕 |
| policy-analysis | 9 节 | 9 节（事件+年度） | `TRIGGER_TYPE`、`OUTPUT_REGISTRY` | 四层 | 官方原文铁律、不构成法律意见 |
| feasibility-study | 9 节 | 9 节（项目制） | `PROJECT_TYPE` | 四层 | 单一 Go/No-Go、引用本仓报告 |
| flash-commentary | 8 节（机制） | 四段式 | `EVENT_NAME` | 四层 | 核验先行、初步判断待验证 |
| whitepaper | 8 节 | 8 节（选题制） | `STUDY_TYPE` | 四层 | 观点鲜明、品牌合规审校前置 |

**三处一致的部分（抽样核验，均通过）**：

- 骨架节数：类型模板「N 节固定顺序」与泛用版「产出 N 节」逐类一致（8/9/10 节、四段式均对齐）。
- 继承声明：泛用版统一为「通用基座 × 通用规范 × 类型模板 × 业务配置」，链接深度 `../../engine/report_templates/...` 全部正确；类型模板用 `../`；脚手架用 `../` 与 `./prompts/`。
- 泛用版对类型模板的节号引用（「见第 X 节」）逐条核对无误。
- 脚手架的「实例化步骤 → 复制文件」与 `prompts/` 实有文件名逐类一致；business-config 清单覆盖各类型模板的档案/追踪表要求。
- 审计协议段落（auto_verify → audit_preflight → audit_check → audit_pipeline --submit）在三处逐字一致。
- 硬性约束与结论边界（如「不构成法律意见」「不构成对不特定公众的投资邀约」「公开信息边界」「区间+三情景」）在类型模板与泛用版间口径一致。

---

## 二、总体结论

**结论：三处「结构 / 继承 / 骨架 / 硬性约束」层面语义对齐；但存在 2 项实质冲突（均在「产出命名口径」），需修正后才能称为完全语义对齐。**

- 结构门禁（`prompt_check.py`）与规范校验（`validate.py`）均 **0 违规 / 0 警告**（退出码 0），说明「命名 / 继承 / 槽位」结构层已收口。
- 语义层：12 类的骨架节数、继承关系、类型专属变量、必填/选填（基线无上期、周期读锚）**全部对齐**；脚手架正文指针化（v1.28）已落实，无三处正文漂移。
- 阻断项：**无**（不阻断合并门禁）。但「产出命名口径」在类型模板与泛用版之间、以及在与注册表/合规口径之间存在**实质性冲突**，属必须登记的口径问题，建议优先处理。

---

## 三、差异统计

| 级别 | 数量 | 说明 |
|---|---|---|
| 实质冲突 | **2** | 产出命名口径（1 项三方冲突 + 1 项系统性口径冲突） |
| 表述差异 | **11** | 编号跳跃、计数漂移、版本记录陈旧、变量区/审计段/链接表述等 |
| 设计内 | **7** | 基线与周期差异、类型专属变量、指针化设计、两类无泛用版的类型等 |

---

## 四、实质冲突清单

### C1【实质冲突】consumer-research 专题调研产出命名：模板表 / 泛用版 / 模板注释三方不一致

- **差异**：专题调研（项目制一次性件）的产出文件名，三处口径互不相同：
  - 类型模板命名表写 `reports/{{YYYY-MM}}-<slug>.md`（月度正则形态）；
  - 泛用版运行变量写 `reports/{{YYYY-MM-DD}}-（TODO：主题）.md`（事件正则形态）；
  - 同类型模板注释却写「专题调研命名**不在** `engine/tools` 标准正则内」。
- **文件 + 行号**：
  - `engine/report_templates/consumer-research/prompt-study-template.md:40`（表格行）、`:43`（注释）
  - `engine/report_templates/consumer-research/prompts/prompt-study.md:18`（`{{OUTPUT_PATH}}`）、`:4`（产出说明）
  - 参照：`engine/report_templates/template-registry.md:125`、`engine/tools/_common.py:33`（`MONTH_REPORT_RE` 仅匹配 `YYYY-MM-<slug>`）
- **影响**：同一业务线按模板表与按泛用版复制会得到不同文件名，`validate.py` 的 WARN/阻断判定随之不同；合规校验（`compliance_check.py` 按 `YYYY-MM-DD` 识别 event）也会误判周期。
- **处理建议**：以注册表第 125 行与合规口径为准（`{{YYYY-MM-DD}}-<主题>.md`），修正 `prompt-study-template.md:40` 的表格行与 `:43` 注释，使模板表、泛用版、注释三者一致。

### C2【实质冲突】事件 / 项目制产出命名：模板命名表与泛用版产出用 `YYYY-MM`，却标注「不在标准正则内」

- **差异**：下列 8 类的「事件触发 / 插刷 / 项目论证 / 新选题」产出，在**类型模板命名表**与**泛用版产出说明**中均写 `reports/{{YYYY-MM}}-<slug>.md`（标准月度正则形态），但**同一文件的注释**声明其「命名不在标准正则内」，且注册表第 125 行、`compliance_check` 的 event 识别（`YYYY-MM-DD-<主题>`）均要求事件/项目件用 `YYYY-MM-DD`。模板与泛用版互相一致，但**二者共同与注释 / 注册表 / 合规口径冲突**。
- **文件 + 行号**（模板命名表行 / 泛用版产出行）：
  | 类型 | 类型模板 | 泛用版 |
  |---|---|---|
  | competitive-intelligence | `prompt-monthly-update-template.md:41` | `prompts/prompt-flash-update.md:4` |
  | sentiment-monitoring | `prompt-monthly-update-template.md:41` | `prompts/prompt-flash-warning.md:4` |
  | industry-research | `prompt-annual-refresh-template.md:41` | `prompts/prompt-annual-refresh.md:4` |
  | market-sizing | `prompt-annual-refresh-template.md:40` | `prompts/prompt-annual-refresh.md:4` |
  | investment-research | `prompt-target-update-template.md:41` | `prompts/prompt-target-review.md:4` |
  | policy-analysis | `prompt-policy-review-template.md:40` | `prompts/prompt-policy-review.md:4` |
  | feasibility-study | `prompt-study-template.md:41` | `prompts/prompt-project-study.md:4` |
  | whitepaper | `prompt-topic-study-template.md:42` | `prompts/prompt-topic-study.md:4` |
  - 参照：`template-registry.md:125`、`compliance-rules.json:4`、`engine/tools/compliance_check.py:45`
- **影响**：若按命名表执行，事件/项目件会被 `validate.py` 当作月度件（不 WARN）、被 `compliance_check` 按 monthly 骨架校验，与「事件触发骨架」设计不符；若按注释执行，则与命名表矛盾。
- **处理建议**：统一为 `reports/{{YYYY-MM-DD}}-<主题>.md`（或统一为 `YYYY-MM` 并同步修正注释、注册表第 125 行与 `event_cycle` 口径）。二选一，但必须三处一致；建议采用前者（与注册表/合规现状一致，改动面最小）。

---

## 五、表述差异清单

| 编号 | 差异 | 文件 + 行号 | 处理建议 |
|---|---|---|---|
| D1 | 脚手架章节编号跳跃：8 份脚手架正文为「一、二、三、四、**六**」，缺「五」 | `consumer-research/business-prompt-scaffold.md:39`、`feasibility-study/…:39`、`flash-commentary/…:39`、`industry-research/…:38`、`investment-research/…:38`、`market-sizing/…:38`、`policy-analysis/…:38`、`whitepaper/…:38`（对照 `competitive-intelligence/…:42`、`sentiment-monitoring/…:42` 有「五」） | 统一重排章节号或补「五」占位，消除编号断档 |
| D2 | 注册表计数漂移：正文称「其余 **11** 个类型」「共 **24** 份」，实际 **10** 份脚手架 / **22** 份泛用版；变更记录 v1.26（10→11、22→24）、v1.27（24 份）、v1.29（23→22）自相矛盾 | `template-registry.md:105`、`:106`、`:179`、`:180`、`:182` | 以实有计数为准回改正文与变更记录，校准 v1.28 表述 |
| D3 | `market-monitoring` 三份模板版本记录的骨架节数陈旧：月 9（正文 8）、季 12（正文 10）、年 11（正文 10） | `prompt-monthly-monitor-template.md:75`（正文 `:18`）、`prompt-quarterly-analysis-template.md:150`（正文 `:81`）、`prompt-annual-review-template.md:156`（正文 `:69`） | 更新版本记录为 8 / 10 / 10 |
| D4 | 版本记录残留旧分类口径「现为六族十三类」（周报取消后应为六族十二类） | `competitive-intelligence/prompt-baseline-setup-template.md:73` | 改为「六族十二类」 |
| D5 | 通用基座 §1.1 目录树与 v1.4 记录未登记 `confidence-grade-standard.md`（实有根部文件 10 份，记录称 9 份） | `prompt-generic-base.md:13-37`（树）、`:204`（v1.4 说明） | 目录树补 `confidence-grade-standard.md`，记录改 10 份 |
| D6 | 运行变量区未列全通用基座变量框架：`{{CADENCE}}`/`{{YEAR}}`/`{{YYYY}}` 全库未被任何提示词/模板使用，而基座要求周期提示词变量区含 `{{CADENCE}}`；`{{REGISTRY_FILE}}` 未被任何泛用版/脚手架变量区收录；基线版含 `{{SOURCE_LANGUAGE_RULE}}` 而周期版普遍不含 | 基座 `prompt-generic-base.md:54`、`:60`、`:72`；例：`competitive-intelligence/prompts/prompt-baseline-setup.md:12-21` vs `…/prompt-monthly-monitor.md:12-20` | 明确「运行时填写」与「配置固定值」边界并在基座注明；补齐或显式豁免 `{{CADENCE}}` 等；统一基线/周期的 `{{SOURCE_LANGUAGE_RULE}}` 取舍 |
| D7 | 通用基座「必需要素齐全」（四类二级章节）与类型模板「N 节固定顺序，不得增删节」存在口径张力：骨架普遍不含「置信度标注」「信息差与未核验清单」独立节 | 基座 `prompt-generic-base.md:105`、`:185`；例：`competitive-intelligence/prompt-baseline-setup-template.md:23`；解决依据 `compliance-rules.json:4`、`:9-10` | 在类型模板加一句「跨主题必选节（置信度标注 / 信息差与未核验清单 / 自动验证结果）由合规规则追加，不计入本骨架节数」，消除字面冲突 |
| D8 | 审计协议段落未含 `md2html.py` + `lint_reports.py` 步骤（基座 §八为 5 步，模板/泛用版/脚手架为 4 步） | 基座 `prompt-generic-base.md:167-173`；例：`competitive-intelligence/prompt-baseline-setup-template.md:65-67`、`prompts/prompt-baseline-setup.md:67-69`、`business-prompt-scaffold.md:42-46` | 在审计段补「先 `md2html.py` 生成 HTML 并过 `lint_reports.py --new-only`」，或注明由 `auto_verify` 幂等重生成覆盖 |
| D9 | 脚手架「脚手架内链接均按**复制后位置**书写」在 v1.28 正文指针化后已不适用（现链接为 `./prompts/`，相对脚手架自身位置） | 10 份脚手架 `:3`（例 `consumer-research/business-prompt-scaffold.md:3`） | 改为「指针链接指向同目录 `prompts/` 泛用版母版」 |
| D10 | 类型模板继承声明沿用旧两层路径 `{地区}/{业务类型}/prompts/business-config.md`，与基座 `NN-<slug>/` 口径不一致（基座已声明旧结构兼容） | 例：`competitive-intelligence/prompt-baseline-setup-template.md:5`、`employment-research/prompt-baseline-setup-template.md:5` | 统一为 `NN-<slug>/prompts/business-config.md`，或在基座注明类型模板保留旧写法 |
| D11 | `{{STUDY_TYPE}}` 变量枚举口径不一致：基座枚举为「概念测试 / 满意度复测 / 画像刷新 / 决策路径」（消费者调研），whitepaper 泛用版复用同名变量但枚举为「新选题 / 年度系列 / 框架修订」 | 基座 `prompt-generic-base.md:80`；`whitepaper/prompts/prompt-topic-study.md:15`；对照 `consumer-research/prompts/prompt-study.md:15` | 基座变量登记处注明「同名变量按类型各自枚举」，或为 whitepaper 另起变量名（如 `{{TOPIC_TYPE}}`） |

---

## 六、设计内差异清单

| 编号 | 差异 | 依据 |
|---|---|---|
| S1 | 基线「无上期报告、不读 `{{PREVIOUS_REPORT_PATH}}`、已修正清单为空」 vs 周期「必须读上期 + 基线」 | 基座 `prompt-generic-base.md:61`、`:65`、`:127`；各类型基线/周期模板 |
| S2 | 类型专属变量按类型枚举（`EVENT_NAME` / `PROJECT_TYPE` / `TRIGGER_TYPE` / `OUTPUT_REGISTRY` 等） | 基座 `prompt-generic-base.md:75-84` |
| S3 | 脚手架仅保留实例化步骤 / business-config 清单 / 指针 / 审计协议，不重复正文 | 注册表 `template-registry.md:181`（v1.28） |
| S4 | `market-monitoring` / `employment-research` 不设 `prompts/` 与脚手架 | 注册表 `template-registry.md:105`、`:112-113` |
| S5 | 泛用版「运行变量（每次运行前填写）」仅列运行时变量，配置固定值（`FRESHNESS_PRIORITY` / `SOURCE_LANGUAGE_RULE` / `REPO_RAW_URL_BASE` / `REGISTRY_FORMAT` 等）由 business-config 承载 | 基座 `prompt-generic-base.md:54`；各脚手架 `:19` |
| S6 | 「含 / 不含 / 口径」边界声明集中在「零、模块边界声明」，由 `skeleton_builder.py` 生成时集中，不写入类型模板骨架 | 基座 `prompt-generic-base.md:104`；`engine/tools/skeleton_builder.py:10`、`:139-140` |
| S7 | `handbook-split-standard.md` 使用 `{{TOPIC_DIR}}`/`{{TOPIC_SLUG}}`/`{{DIMENSIONS}}` 等变量，属手册拆分子系统，不在提示词继承变量框架内 | `handbook-split-standard.md:204` |

---

## 七、校验

在工作树 `D:\文档\GitHub\jp-life-work\.worktrees\b-semverify` 内执行：

| 命令 | 输出 | 退出码 |
|---|---|---|
| `python engine/tools/prompt_check.py` | `提示词门禁：0 项违规` / `提示词门禁通过：命名/继承/结构/槽位一致` | **0** |
| `python engine/tools/validate.py` | `结构与规范校验通过：通用层完整、业务线结构齐全、命名合规` | **0** |

> 说明：`prompt_check.py` 仅覆盖命名 / 继承链接 / p1–p5 结构 / business-config 槽位，**不覆盖**本报的语义口径（命名正则、变量枚举、骨架必需要素）——这正是 B8 独立验证的补充价值。

---

## 八、阻塞项与建议

**阻塞项：无。** 两项校验退出码均为 0，不阻断合并门禁；本报告为只读分析，未改动任何模板语义。

**建议处理优先级**：

1. **P1（实质冲突 C1 / C2）**：统一事件 / 项目制产出的命名口径，修正类型模板命名表与泛用版产出，使「模板表 / 泛用版 / 注释 / 注册表 / 合规口径」五者一致。
2. **P2（表述差异 D1 / D2 / D7）**：修复 8 份脚手架的章节编号断档；校准注册表计数（10 / 22）；在类型模板注明跨主题必选节不计入骨架节数。
3. **P3（表述差异 D3–D6、D8–D11）**：清理陈旧版本记录与目录树、明确变量区边界与 `{{CADENCE}}` 处置、补全审计步骤、修正脚手架链接表述、统一 `{{STUDY_TYPE}}` 口径。

---

## 九、证据

- 报告路径：`docs/toolchain/reviews/prompt-semantic-alignment.md`
- 校验命令与退出码：见第七节（`prompt_check.py` = 0；`validate.py` = 0）
- 分析基线：工作树 `.worktrees/b-semverify`，分支 `task/b-semverify-e1e33a6c`，提交前 `HEAD = d51f39a`
