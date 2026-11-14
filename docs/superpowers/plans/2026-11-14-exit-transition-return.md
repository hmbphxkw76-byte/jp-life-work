# 「退出·转型·回国」主题 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 `16-exit-transition-return` 政策执行型研究主题，产出配置、指标登记册、基线报告与框架级初析 companion，并让 00-decision-hub 的第五问可引用其结论。

**Architecture:** 采用 `policy-analysis` 的事件触发单份解读 + 年度台账复盘节拍，但首期只做执行层：退出、转型、回国三段共用一份制度台账与个人行动时间线。报告只引用 07 / 08 / 14 已有的制度结论，不复制其正文；官方来源回溯先行，无来源的金额、期限与要件保留「⚠ 待核实」。

**Tech Stack:** Markdown 报告 + Python 工具链（`validate.py` / `lint_reports.py` / `compliance_check.py` / `build_hub.py` / `md2html.py` / `vocab_tool.py` / `sync_vocab.py`）+ HTML 交付。

**Spec:** [docs/superpowers/specs/2026-11-14-exit-transition-return-design.md](../specs/2026-11-14-exit-transition-return-design.md)

## Global Constraints

- 业务线目录固定为 `16-exit-transition-return/`；报告类型为 `policy-analysis`；基线路径固定为 `reports/2026-11_baseline_report.md`。
- 本主题只做执行层：退出、转型、回国的申请资格、书类、时限、衔接、复核入口；不复制 07 的年金 / 税务制度正文、08 的资格取消 / 再入国制度正文、14 的搬家解约与赴日落地清单。
- 首期不改 07 / 08 / 14 的「不含」清单与交叉引用；只更新 `00-decision-hub/data/decision_hub_registry.md` 的引用与状态。
- 所有金额、期限、要件、申请条件必须回溯官方一手来源；中文媒体只作线索。无官方依据时写「⚠ 待核实」，不得补值或外推。
- 关键结论标注「（事实）」「（推断）」；建议章必须与事实分离；免责声明固定为「本报告仅供参考，不构成投资建议或决策依据。」。
- 报告必须同时交付 md + HTML；HTML 由 `src/prompts-tools/tools/md2html.py` 生成，并满足 `lint_reports.py` 的免责声明与表格结构要求。
- 词汇库新增主题 `exit-transition-return`，前缀 `ETR`，只通过 `vocab_tool.py` / `sync_vocab.py` 维护，不手工编辑 `terms.md`。
- 文件命名遵循仓库约定：基线 `2026-11_baseline_report`；初析 `2026-11-14_initial_analysis_report`；登记册 `exit_transition_return_indicator_registry.md`。

## Review Focus

- **来源缺口**：官方页面只确认制度名称但不能确认金额、期限、要件时，预期行为是保留「⚠ 待核实」并给复核入口，不得把线索写成事实。
- **跨主题越界**：预期 16 不重复 07 / 08 / 14 的制度正文；报告只写退出时点如何申请与衔接。
- **阶段缺失**：预期退出、转型、回国三段都至少在基线与初析中出现，不得把主题写成单纯回国清单。
- **结构合规**：预期 HTML 含免责声明与可点击来源；`compliance_check.py` 不产生本主题错误。
- **索引一致**：预期新增主题与两份报告被 `build_hub.py` 自动发现，`--check` 归一化通过。

## File Structure

```text
16-exit-transition-return/
├── prompts/
│   ├── business-config.md                    # 单一事实源：变量、边界、结构、来源、触发器、追踪表
│   ├── prompt-baseline-setup.md              # 基线建立提示词（永不重跑）
│   └── prompt-policy-review.md               # 事件触发解读 / 年度复盘统一入口
├── data/
│   └── exit_transition_return_indicator_registry.md
├── reports/
│   ├── 2026-11_baseline_report.md
│   ├── 2026-11_baseline_report.html
│   ├── 2026-11-14_initial_analysis_report.md
│   └── 2026-11-14_initial_analysis_report.html
└── operations-guide.md
```

同时修改：

- `src/vocabulary/config/topics.json`（由 `topic-add` 生成）
- `src/vocabulary/config/sync.json`（手工追加 binding，结构照 14/15）
- `src/vocabulary/data/exit-transition-return/terms.md`（由 `topic-add` 生成）
- `src/vocabulary/data/exit-transition-return/imports/2026-11-14_seed-exit-transition-return.md`
- `src/vocabulary/INDEX.md`（由 `index` 生成）
- `src/report_templates/template-registry.md`（登记 16 为 policy-analysis 业务线）
- `00-decision-hub/data/decision_hub_registry.md`（更新引用与状态）
- `index.html`（由 `build_hub.py` 重新生成）

---

### Task 1: 建立业务机制与主题注册

**Files:**
- Create: `16-exit-transition-return/prompts/business-config.md`
- Create: `16-exit-transition-return/prompts/prompt-baseline-setup.md`
- Create: `16-exit-transition-return/prompts/prompt-policy-review.md`
- Create: `16-exit-transition-return/data/.gitkeep`
- Create: `16-exit-transition-return/reports/.gitkeep`
- Create: `16-exit-transition-return/operations-guide.md`
- Modify: `src/report_templates/template-registry.md`

**Interfaces:**
- Consumes: 设计稿第四、五、六、七、八节；`src/report_templates/policy-analysis/prompt-baseline-setup-template.md`；`08-visa-immigration/prompts/business-config.md` 的结构参照。
- Produces: 后续任务读取的固定路径、类型 ID、基线路径、登记册路径、追踪指标编号与官方来源优先级。

- [ ] **Step 1: 创建业务线目录与占位文件**

在 `16-exit-transition-return/` 下建立 `prompts/`、`data/`、`reports/`，并创建空 `data/.gitkeep`、`reports/.gitkeep`。不得手工填写任何来源活值。

- [ ] **Step 2: 写 `business-config.md`**

按 08 的章节骨架写 16 专属配置，至少包含：

1. 运行变量：`{{REGION}} = 日本`、`{{TOPIC}} = 退出·转型·回国`、`{{BASELINE_DATE}} = 2026-11-14`、`{{REGISTRY_PATH}} = data/exit_transition_return_indicator_registry.md`、`{{BASELINE_REPORT_PATH}} = reports/2026-11_baseline_report.md`；
2. 三段研究主轴与「含 / 不含」清单；
3. 结构固化锚：执行摘要 / 退出·转型·回国制度台账与监测机制 / 制度框架与三段路径 / 退出与转型政策逐条解读 / 个人场景影响矩阵 / 退出·转型·回国行动建议（建议章）/ 制度变更与个人行动时间线 / 数据可靠性与局限说明 / 参考来源清单；
4. 术语口径：退職 ≠ 退去強制；在留資格取消 ≠ 在留資格変更；特定活動 ≠ 技能実習；再入国許可 ≠ みなし再入国；
5. 来源优先级：出入国在留管理庁 / 法務省 / e-Gov ＞ 厚生労働省 / 日本年金機構 / ハローワーク ＞ 国税庁 / 地方自治体 ＞ 媒体线索；
6. 跨主题分工：07 / 08 / 14 / 02 / 01 的只读引用关系；
7. 触发器：退職・労働条件・雇用保険改定；健康保険任意継続改定；年金脱退要件改定；在留資格変更・取消・特定活動规则改定；帰国前確定申告・住民税规则改定；退室・解約规则改定；个人情况变化；
8. 追踪表：至少 12 项，覆盖退出、转型、回国、来源治理；
9. 研究边界档案：领域边界、三段分层、主体清单、口径清单；
10. 版本记录 v1.0。

- [ ] **Step 3: 写两份提示词**

`prompt-baseline-setup.md` 要求：官方来源回溯先行；只读取本主题配置与官方原文；不读取虚构上期；产出九节基线并回写登记册；无来源项标「⚠ 待核实」。

`prompt-policy-review.md` 要求：事件触发解读 + 年度台账复盘统一入口；触发器未命中不启动；先读基线 / 上期与登记册，再写增量；来源、影响、建议与局限分离。

- [ ] **Step 4: 写 `operations-guide.md`**

给出基线、事件触发、年度复盘、个人情况变化四类入口、路径、验证命令与「无触发不启动」规则。

- [ ] **Step 5: 在 `template-registry.md` 登记 16**

在 policy-analysis 的「已接入业务线」列追加 `jp/16-exit-transition-return`，并在变更记录追加 v1.23：政策执行层主题接入；事件触发单份解读 + 年度台账复盘；不做 07 / 08 / 14 的制度正文复制。

- [ ] **Step 6: 校验机制**

Run: `python src/prompts-tools/tools/validate.py`
Expected: 本主题目录存在且含 `prompts/business-config.md`；若仍有 WARN，只允许来自既有历史报告，不得来自 16。

- [ ] **Step 7: Commit**

```bash
git add 16-exit-transition-return src/report_templates/template-registry.md
git commit -m "feat: establish exit transition return topic"
```

---

### Task 2: 建立词汇主题并同步到业务配置

**Files:**
- Modify: `src/vocabulary/config/topics.json`（`topic-add` 生成）
- Create: `src/vocabulary/data/exit-transition-return/terms.md`（`topic-add` 生成）
- Create: `src/vocabulary/data/exit-transition-return/imports/2026-11-14_seed-exit-transition-return.md`
- Modify: `src/vocabulary/config/sync.json`
- Modify: `src/vocabulary/INDEX.md`（`index` 生成）
- Modify: `16-exit-transition-return/prompts/business-config.md`（同步区块）

**Interfaces:**
- Consumes: Task 1 的 `business-config.md` 与分类清单。
- Produces: 词汇主题 ID `exit-transition-return`、前缀 `ETR`、分类词表、同步绑定。

- [ ] **Step 1: 注册词汇主题**

Run: `python src/vocabulary/script/vocab_tool.py topic-add --topic exit-transition-return --name 退出·转型·回国 --prefix ETR --categories "退出与劳动;转型与在留资格;年金与保险;税务与住民;离境与再入国;资产与生活清理" --description "在日外国人退出、转型与回国的执行层词汇"`

Expected: 命令成功；`topics.json` 出现 `exit-transition-return`；`data/exit-transition-return/terms.md` 与 imports/exports 目录建立。

- [ ] **Step 2: 写种子导入文件**

在 `src/vocabulary/data/exit-transition-return/imports/2026-11-14_seed-exit-transition-return.md` 写 6 列导入表，至少覆盖：退職、雇用保険、健康保険任意継続、厚生年金脱退一时金、在留資格変更、特定活動、帰国前確定申告、再入国許可、みなし再入国、転出届、退室、车辆处置、来源治理。每条附官方来源名称；无法确认的写「⚠ 待核实」。

- [ ] **Step 3: 导入并校验**

Run: `python src/vocabulary/script/vocab_tool.py import --topic exit-transition-return --file src/vocabulary/data/exit-transition-return/imports/2026-11-14_seed-exit-transition-return.md`
Expected: 新增计数 > 0；无效计数 = 0；重复计数可为 0。

Run: `python src/vocabulary/script/vocab_tool.py check --topic exit-transition-return`
Expected: 0 错误 / 0 警告。

- [ ] **Step 4: 追加同步绑定**

在 `src/vocabulary/config/sync.json` 的 `bindings` 末尾追加：

```json
{
  "topic": "exit-transition-return",
  "targets": [
    {
      "path": "../../16-exit-transition-return/prompts/business-config.md",
      "format": "digest",
      "section_title": "## 词汇速览：退出·转型·回国（词汇库自动同步）",
      "insert_before": "## 十二、版本记录",
      "categories_include": [],
      "tags_include": []
    }
  ]
}
```

若 Task 1 的版本记录标题不是「十二、版本记录」，改用 `business-config.md` 中实际的唯一锚点。

- [ ] **Step 5: 同步并校验**

Run: `python src/vocabulary/script/vocab_tool.py index`
Run: `python src/vocabulary/script/sync_vocab.py sync --topic exit-transition-return`
Run: `python src/vocabulary/script/sync_vocab.py verify --topic exit-transition-return`
Run: `python src/vocabulary/script/vocab_tool.py topic-check`

Expected: INDEX.md 出现主题；verify 通过；topic-check 0 错误 / 0 警告。

- [ ] **Step 6: Commit**

```bash
git add src/vocabulary/config/topics.json src/vocabulary/config/sync.json src/vocabulary/data/exit-transition-return src/vocabulary/INDEX.md 16-exit-transition-return/prompts/business-config.md
git commit -m "feat: add exit transition return vocabulary"
```

---

### Task 3: 建立指标登记册

**Files:**
- Create: `16-exit-transition-return/data/exit_transition_return_indicator_registry.md`

**Interfaces:**
- Consumes: Task 1 的追踪表与结构锚；Task 2 的术语表。
- Produces: 登记册固定字段与至少 12 项指标，供基线报告引用。

- [ ] **Step 1: 写登记册骨架**

按 08 登记册格式写：用途、配套路径、核心指标表（# / 指标 / 优先数据源 / 最新值 / 基准版本）、研究边界档案、观察项与触发器状态、版本记录 v1.0。

- [ ] **Step 2: 填 12 项指标**

至少包含：

1. 退職与労働条件终止规则；
2. 雇用保険 / 失業給付衔接；
3. 健康保険任意継続要件与期限；
4. 国民健康保険 / 被用者保険退出；
5. 厚生年金脱退一时金申请资格、书类、时限与复核入口；
6. 年金・社保后续纳付与永住 / 归化影响；
7. 在留資格取消・変更・特定活動衔接；
8. 特定技能 1 号业务限制与 2 号路径；
9. 転職与资格外活动边界；
10. 帰国前確定申告与住民税 / 所得税；
11. 在留卡返还・再入国許可・みなし再入国；
12. 退室・解約・车辆・通信・银行账户清理。

每项必须附来源机构；没有官方依据的金额 / 期限 / 要件写「⚠ 待核实」。不得复制 07 / 08 / 14 的正文段落。

- [ ] **Step 3: 校验登记册**

Run: `python src/prompts-tools/tools/validate.py`
Expected: 本主题无 ERROR；WARN 仅来自既有历史报告。

- [ ] **Step 4: Commit**

```bash
git add 16-exit-transition-return/data/exit_transition_return_indicator_registry.md
git commit -m "feat: add exit transition return indicator registry"
```

---

### Task 4: 产出基线报告与初析 companion

**Files:**
- Create: `16-exit-transition-return/reports/2026-11_baseline_report.md`
- Create: `16-exit-transition-return/reports/2026-11-14_initial_analysis_report.md`
- Modify: `16-exit-transition-return/data/exit_transition_return_indicator_registry.md`（回写活值与更新时间）

**Interfaces:**
- Consumes: Task 1 结构锚、Task 3 登记册、07 / 08 / 14 的既有结论（只读）。
- Produces: 两份 md 源稿与登记册活值；HTML 在 Task 5 生成。

- [ ] **Step 1: 写基线报告九节**

按 `policy-analysis` 九节骨架写：

1. 执行摘要；
2. 政策台账与监测机制；
3. 制度框架与三段路径；
4. 重点政策逐条解读；
5. 影响对象矩阵；
6. 合规应对建议（建议章）；
7. 生效时间线；
8. 数据治理与局限；
9. 参考来源清单。

内容要求：

- 退出：退職、雇用保険、健康保険任意継続、被用者保険退出、在留资格状态；
- 转型：在留資格変更、特定活動、其他就労资格、転職边界、特定技能 2 号限制；
- 回国：年金脱退执行、帰国前確定申告、在留卡返还、再入国、退室、通信 / 银行 / 车辆；
- 每节关键结论标注「（事实）」「（推断）」；
- 来源清单逐条附官方 URL、版本日期与核验状态；
- 无来源的金额 / 期限 / 要件统一「⚠ 待核实」。

- [ ] **Step 2: 写初析 companion**

按仓库既有惯例写五模块：主题核心概述、关键维度拆解、当前现状梳理、初步结论、后续观察方向；再加核心指标速览、监测机制与触发器、数据可靠性与局限、免责声明、参考来源清单。与基线九节错位，不做单指标 deep-dive。

- [ ] **Step 3: 回写登记册**

将基线中已核实的活值、版本日期与核验状态回写登记册；保留「⚠ 待核实」项；不得把推断写成事实。

- [ ] **Step 4: 校验内容结构**

Run: `python src/prompts-tools/tools/validate.py`
Expected: 本主题无 ERROR；若 `validate.py` 因历史报告返回 exit 2，确认错误列表不含 16。

- [ ] **Step 5: Commit**

```bash
git add 16-exit-transition-return/reports/2026-11_baseline_report.md 16-exit-transition-return/reports/2026-11-14_initial_analysis_report.md 16-exit-transition-return/data/exit_transition_return_indicator_registry.md
git commit -m "feat: add exit transition return baseline and initial analysis"
```

---

### Task 5: 生成 HTML 并验证内容结构

**Files:**
- Create: `16-exit-transition-return/reports/2026-11_baseline_report.html`
- Create: `16-exit-transition-return/reports/2026-11-14_initial_analysis_report.html`

**Interfaces:**
- Consumes: Task 4 的两份 md。
- Produces: 可点击、可 lint 的 HTML 交付物。

- [ ] **Step 1: 生成 HTML**

Run: `python src/prompts-tools/tools/md2html.py 16-exit-transition-return/reports/2026-11_baseline_report.md`
Expected: 生成同名 HTML，含 `.report-nav`、`h2 id="sN"` 与表格列宽。

Run: `python src/prompts-tools/tools/md2html.py 16-exit-transition-return/reports/2026-11-14_initial_analysis_report.md`
Expected: 生成同名 HTML。

> 若 `md2html.py` 不支持单文件参数，则运行全量 `python src/prompts-tools/tools/md2html.py`，但只提交 16 的两份新 HTML，不重生成既有报告。

- [ ] **Step 2: 校验 HTML**

Run: `python src/prompts-tools/tools/lint_reports.py`
Expected: 16 的两份 HTML 无 ERROR；若其他历史报告有既有 WARN，单独记录，不修改历史文件。

Run: `python src/prompts-tools/tools/compliance_check.py --file 16-exit-transition-return/reports/2026-11_baseline_report.html`
Expected: 无 ERROR；若因「h2 节数超出模板骨架」产生 WARN，确认是九节骨架的声明式标题映射，并在报告或配置中留痕。

- [ ] **Step 3: Commit**

```bash
git add 16-exit-transition-return/reports/2026-11_baseline_report.html 16-exit-transition-return/reports/2026-11-14_initial_analysis_report.html
git commit -m "feat: render exit transition return reports"
```

---

### Task 6: 更新 00 状态、重建索引并全量验证

**Files:**
- Modify: `00-decision-hub/data/decision_hub_registry.md`
- Modify: `index.html`

**Interfaces:**
- Consumes: Task 4 的基线与初析；Task 5 的 HTML。
- Produces: 00 引用更新、根索引包含 16、全量验证结果。

- [ ] **Step 1: 更新 00 引用与状态**

在 `00-decision-hub/data/decision_hub_registry.md` 中：

- 将「最坏怎么办 / 退出执行」引用更新为 `16-exit-transition-return` 的基线与初析；
- 将「年金 / 保险衔接」的缺失标记从「建议建退出专题」改为「已建 16，执行层待持续核实」；
- 缺失清单中「退出 · 转型 · 回国」条目标记为已接入，但保留「具体金额 / 期限 / 要件待核验」；
- 不修改 07 / 08 / 14 的正文与边界。

- [ ] **Step 2: 重建根索引**

Run: `python src/prompts-tools/tools/build_hub.py`
Expected: `index.html` 自动发现 `16-exit-transition-return` 与两份报告；主题卡片、报告列表与近 1 年窗口正常。

- [ ] **Step 3: 全量验证**

Run: `python -m unittest discover -s src/tests -v`
Expected: 全部通过；若既有测试因 index 变化失败，先核对是否为 16 导致，再修复。

Run: `python src/prompts-tools/tools/validate.py`
Expected: 无 16 相关 ERROR；WARN 仅来自既有历史报告。

Run: `python src/prompts-tools/tools/lint_reports.py`
Expected: 16 两份 HTML 无 ERROR。

Run: `python src/prompts-tools/tools/compliance_check.py`
Expected: 16 报告无 ERROR；若只有 WARN，记录并确认是结构映射的预期警告。

Run: `python src/prompts-tools/tools/build_hub.py --check`
Expected: exit 0，归一化内容一致。

Run: `python src/vocabulary/script/vocab_tool.py topic-check`
Run: `python src/vocabulary/script/vocab_tool.py check --topic exit-transition-return`
Run: `python src/vocabulary/script/sync_vocab.py verify --topic exit-transition-return`
Expected: 全部 0 错误 / 0 警告。

- [ ] **Step 4: Commit**

```bash
git add 00-decision-hub/data/decision_hub_registry.md index.html
git commit -m "chore: register exit transition return in decision hub and hub index"
```

---

## Self-Review

- **Spec coverage**：业务机制、词汇、登记册、基线、初析、HTML、00 状态与索引均有对应任务；07 / 08 / 14 不修改的约束写入 Global Constraints 与 Task 6。
- **Step scan**：每个任务以可检查命令或明确文件内容收尾；没有要求补写抽象测试。
- **Type consistency**：类型 ID 固定 `policy-analysis`；路径、登记册名、初析名在任务间一致。
- **Review Focus**：来源缺口、跨主题越界、阶段缺失、结构合规、索引一致分别由 Task 3 / Task 4 / Task 5 / Task 6 覆盖。
- **Proportion**：计划聚焦新增主题的首期交付，不展开 07 / 08 / 14 的正文，长度与新增工作量相称。
