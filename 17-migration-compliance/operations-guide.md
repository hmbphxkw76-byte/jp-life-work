# 日本劳务输出与中介合规研究 · 报告启动操作指引（Agent 可执行版）

> **适用范围**：`17-migration-compliance` 业务线的基线 / 事件触发解读 / 季度更新 / 年度台账复盘 / 个人情况变化五类节拍。
> **使用方式**：本指引可由人类逐步照做，也可整体交给 AI Agent 执行。Agent 执行时须遵守文末「Agent 执行约定」。
> **单一事实源**：业务参数一律以 [prompts/business-config.md](./prompts/business-config.md) 为准，本指引不复制阈值与来源清单，只给路径。

---

## 0. 通用规定（五类节拍共用）

### 0.1 目录速查

| 资产 | 路径 |
|---|---|
| 周期提示词（启动入口） | `17-migration-compliance/prompts/prompt-{baseline-setup|policy-review}.md` |
| 业务参数（变量 / 边界 / 来源 / 触发器） | `17-migration-compliance/prompts/business-config.md` |
| 政策台账与指标登记册 | `17-migration-compliance/data/migration_compliance_indicator_registry.md` |
| 报告产物 | `17-migration-compliance/reports/` |
| 报告归档 | `17-migration-compliance/reports/archives/` |
| 工具链 | `engine/tools/`（退出码：0 过 / 1 错 / 2 警告） |
| 通用层（只读，不改） | `engine/report_templates/` |

### 0.2 五种启动方式

- **基线**：一次性机制建立；已产出后永不重跑，仅灾难恢复或经批准的结构重排可重启。
- **事件触发解读**：官方政策 / 修订 / 细则出台后启动；无触发不启动。
- **季度更新**：每季度窗口或任一重大事件触发器命中时，全模块刷新（完整九节更新版）。
- **年度台账复盘**：每年制度年度改定后启动；读最近一期年度复盘与基线。
- **个人情况变化**：签约 / 缴费 / 发现被骗 / 合同变更 / 雇主变化时启动；只写增量与条件化建议。

### 0.3 通用前置检查（每次启动前必做）

```powershell
# 在仓库根目录执行
python engine/tools/validate.py      # 结构与命名校验，期望：本主题零 WARN / 零 ERROR
python engine/tools/lint_reports.py  # 报告内容校验，期望：0 错误
```

> **退出码说明**：`validate.py` 0 = 通过；1 = 存在错误项；2 = 仅存在警告项（警告应仅来自其他未迁移主题）。`lint_reports.py` 0 = 通过；1 = 存在错误（表格规范等）。

并人工确认三点：

1. 基线报告 `reports/2026-11-migration-compliance.md`（+ 同名 HTML）存在（解读的对比锚，缺失则先走第 5 节灾难恢复）。
2. 上期解读 / 季度版 / 年度复盘报告存在（首期除外），路径记入 `{{PREVIOUS_REPORT_PATH}}`。
3. 对应周期提示词存在，且继承声明指向 [engine/report_templates/employment-research/](../engine/report_templates/employment-research/)。

---

## 1. 基线报告（首期机制建立，一次性）

### 1.1 启动入口与前置条件

- 入口：[prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)
- **重要**：本业务线基线已产出（`reports/2026-11-migration-compliance.md` v1.0 + 登记册）。**正常运行永不重跑基线**。仅以下两种情形允许再次启动：
  - 报告与登记册全部丢失（灾难恢复）；
  - 九节结构经维护规范批准重排（须在 business-config 版本记录留痕）。
- 前置条件：无上期报告依赖；确认中日来源清单与官方发布节奏；确认 `{{REGISTRY_PATH}}` 不存在或已获准重建。

### 1.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2026-11-14` |
| `{{BASELINE_DATE}}` | 首期基线日期（重建时改重建日期） | `2026-11-14` |
| `{{OUTPUT_PATH}}` | 固定 `reports/2026-11-migration-compliance.md` | 同左 |
| `{{REPORT_VERSION}}` | 首期固定 `v1.0`；重建时递增 | `v1.0` |

### 1.3 执行步骤

1. 填写提示词顶部运行变量。
2. 按[业务配置第三节](./prompts/business-config.md)确认研究边界与九节结构映射。
3. 按 10+1 项追踪指标采集中日官方原文来源；每条数据记录「机构 · 发布与生效日期 · 版本日期 · 核验状态」。
4. 撰写报告：首期基线保留现行九节结构（不改正文）；重建场景按九节骨架撰写，标题逐字固化。
5. 首建 / 复核研究边界档案（领域边界、三段分层、主体清单与入选标准、口径清单），回写 `{{REGISTRY_PATH}}`。
6. 回填追踪表 10+1 项「是否更新」；空清单补记「已修正事实清单」（首期为空）。
7. 落盘 `{{OUTPUT_PATH}}` 与同名 HTML。

### 1.4 结果验证

```powershell
python engine/tools/lint_reports.py
```

人工核对：全篇引用回溯中日官方原文；基线导航为简化锚点；九节结构与声明映射一致。

---

## 2. 事件触发解读（主周期）

### 2.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{TRIGGER_TYPE}}` = 新政策 / 修订 / 细则）
- 前置条件：通用前置检查通过；触发器确认（对外劳务合作管理条例修订；841 号令与备案办法；ISA 認定送出機関名单；実習法行政処分公示；育成就労 2027-04-01 施行；入管法改正；特定技能運用要領改定；01 / 02 / 08 已修正事实清单追加，见[业务配置第七节](./prompts/business-config.md)）。**无触发且窗口未到 → 不启动，不得虚构变化。**

### 2.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-04-01` |
| `{{TRIGGER_TYPE}}` | 新政策 / 修订 / 细则 | `修订` |
| `{{PREVIOUS_REPORT_PATH}}` | 上期解读 / 复盘路径（如无则空） | `reports/2027-03-31-认定送出机关名单更新.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-migration-compliance.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md` | `reports/2027-04-01-育成就劳施行.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.04.01` |

### 2.3 执行步骤

1. 原文回溯先行：登记官方原文（URL、版本日期、文本完整性）后才进入解读。
2. 填变量 → 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，提取「已修正事实清单」全部条目（防回退）。
3. 逐条解读：条款含义、中日新旧制度衔接对照、歧义多解、官方答问与细则对照。
4. 影响评估：影响对象矩阵增量、过渡期与合规时点。
5. 应对建议：合规要点、待明确事项清单（标「建议」，与事实分离）。
6. 回写报告与登记册；落盘 md + HTML。

### 2.4 时间范围与数据范围规则

- **解读对象 = 触发事件对应的官方文本**；征求意见稿登记但标注「非最终文本，以正式发布为准」。
- 同一政策多版本并存时以官方最新发布为准，旧版仅作对照锚。
- 送出機関 ≠ 認定送出機関；对外劳务合作 ≠ 劳务派遣；保証金 ≠ 違約金 ≠ 解約金；黑名单 ≠ 官方公示等口径不得合并或取均值。

### 2.5 结果验证

```powershell
python engine/tools/lint_reports.py
```

人工核对：解读锚点准确；已修正事实清单无回退；中日新旧对照完整；登记册与报告变更摘要一致。

---

## 3. 季度更新

### 3.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{TRIGGER_TYPE}}` = 季度更新）
- 前置条件：通用前置检查通过；季度窗口到达或任一重大事件触发器命中。

### 3.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-01-15` |
| `{{TRIGGER_TYPE}}` | 固定填 `季度更新` | 同左 |
| `{{PREVIOUS_REPORT_PATH}}` | 上一期季度版或解读（如无则空） | `reports/2026-11-migration-compliance.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-migration-compliance.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md` | `reports/2027-01-中介合规季度更新.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.01.15` |

### 3.3 执行步骤

1. 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，提取「已修正事实清单」全部条目（防回退）。
2. 全模块刷新：中日监管框架、渠道矩阵、骗术图谱、名单与公示、合同清单、救济窗口。
3. 数据变更摘要覆盖 10+1 项追踪指标；未变动项注明「截至 {{CURRENT_DATE}} 无更新」。
4. 回写报告与登记册；落盘 md + HTML。

### 3.4 结果验证

```powershell
python engine/tools/lint_reports.py
```

人工核对：九节结构逐字继承；来源语言规则执行结果已声明；追踪表逐项核对。

---

## 4. 年度台账复盘

### 4.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{TRIGGER_TYPE}}` = 年度台账复盘）
- 前置条件：通用前置检查通过；年度窗口到达（年度制度改定后）。

### 4.2 运行变量（必填）

| 变量 | 填写规则 | 示例（复盘 2027 年） |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-11-15` |
| `{{TRIGGER_TYPE}}` | 固定填 `年度台账复盘` | 同左 |
| `{{PREVIOUS_REPORT_PATH}}` | `reports/` 中最近一期年度复盘（首年为空） | `reports/2026-11-migration-compliance.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-migration-compliance.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md` | `reports/2027-11-中介合规年度复盘.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.11.15` |

### 4.3 执行步骤

1. 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，提取「已修正事实清单」全部条目（防回退）。
2. 台账全量复核：中日法规清单、发布渠道、生效时间线、影响对象矩阵。
3. 年度监管态势综述；上年判断逐条复判，原文保留。
4. 数据变更摘要覆盖全部研究维度与口径清单。
5. 回写报告与登记册；落盘 md + HTML + 登记册年度新版（另存，不覆盖历史）。

### 4.4 结果验证

```powershell
python engine/tools/lint_reports.py
```

人工核对：九锚点（或声明结构）全部跳转准确；上年判断原文保留；台账增量 / 状态变更已回写。

---

## 5. 个人情况变化件

### 5.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{TRIGGER_TYPE}}` = 个人情况变化）
- 前置条件：签约 / 缴费 / 发现被骗 / 合同变更 / 雇主变化 / 在留资格变化；通用前置检查通过。

### 5.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-06-01` |
| `{{TRIGGER_TYPE}}` | 固定填 `个人情况变化` | 同左 |
| `{{PREVIOUS_REPORT_PATH}}` | 最近一期个人情况变化或解读（如无则空） | `reports/2027-03-31-个人情况变化.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-migration-compliance.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md` | `reports/2027-06-01-个人情况变化.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.06.01` |

### 5.3 执行步骤

1. 读基线、最近一期解读与登记册；提取变化前后的条件差异。
2. 只写条件化建议与执行顺序，不给个案法律 / 税务结论。
3. 回写登记册「个人场景影响矩阵」与观察项；落盘 md + HTML。

### 5.4 结果验证

```powershell
python engine/tools/lint_reports.py
```

人工核对：变化前后条件对照清晰；建议标「建议」；未核实项显式标记；登记册与报告一致。

---

## 6. 全类型通用收尾（每次报告落盘后必做）

### 6.1 校验

```powershell
python engine/tools/lint_reports.py
python engine/tools/classify_reports.py
python engine/tools/audit_preflight.py --report <报告相对路径>
python engine/tools/audit_check.py --report <报告相对路径>
python engine/tools/audit_pipeline.py --submit --report <报告相对路径>
```

- [ ] 表格 `<thead>` / `<tbody>` 成对，多列表声明百分比列宽，无竖排塌缩
- [ ] 来源链接可点击，`[Source: 完整URL, 年份]` 完整
- [ ] 图注含单位、来源、统计周期与口径警示
- [ ] 锚点跳转准确（年度复盘：`href="#sN"` 与 `<h2 id="sN">` 逐字对应）
- [ ] 浏览器打开无控制台 error

### 6.2 归档

- 基线报告常驻 `reports/` 顶层，不归档。
- 年度复盘版保留最新 5 期，超出移入 `reports/archives/`；事件触发解读件随所属年度版归档。
- 登记册修改采用增量方式：保留历史值，不覆盖。

### 6.3 提交

git 提交报告 + 登记册（建议提交信息：`report: {YYYY-MM-DD} 劳务输出与中介合规事件触发解读` 等格式）。

### 6.4 浏览器抽查

打开 HTML，确认导航锚点、表格排版、来源链接与正文数值一致。

---

## 7. 常见异常排查

| 现象 | 原因 | 处置 |
|---|---|---|
| `validate.py` 退出码 1 | 通用层缺文件 / 业务目录结构缺项 / 报告命名不合规 | 按 error 行补齐文件或改命名；不得为过检删除通用层内容 |
| `lint_reports.py` 退出码 1 | 表格规范错误 | 按行修复 HTML |
| `validate.py` 退出码 2 | 存在警告项 | 确认警告仅来自其他未迁移主题；本主题应零 WARN |
| 基线报告缺失 | 误删或未恢复 | **停止周期更新**，先按 prompt-baseline-setup.md 灾难恢复 |
| 上年判断被改写 | 差异合并时覆盖原文 | 恢复原文，复判结论另起段落并列呈现 |
| 官方页面无新数据 | 发布窗口未开 | 正常情形：按核验型轻运行处理，禁止虚构变化 |
| 中日口径冲突无法裁决 | 双方法域不同 | 并列呈现并标注来源与年份，不取均值、不换算 |
| 链接指向旧文件名 | 报告改名后未同步 | 全库 grep 旧报告名 / 旧登记册名并改为新名 |
| 金额 / 期限无官方依据 | 仅有媒体或非官方转述 | 一律写「⚠ 待核实」，不得补值、不外推 |

---

## 8. Agent 执行约定

1. **顺序不可跳**：前置检查 → 填变量 → 触发判定 → 原文回溯 → 读上期 / 基线 → 逐条解读 → 回写登记册 → 校验 → 收尾。任何前置步骤失败即停，不得带病运行。
2. **单一事实源**：边界、来源、口径、触发器从 business-config.md 与登记册读取，不得凭记忆填写；提示词内严禁预填活值。
3. **防回退**：每次运行必须完整继承「已修正事实清单」；与清单冲突的旧结论不得复活。
4. **不虚构**：无触发器命中时降级为核验型轻运行；「没有数据」写成可核验陈述。
5. **留痕**：所有修正逐条补记清单；登记册更新按「实质修订 / 新增口径记录 / 复核确认 / 未取得维持上期值 / 结论不变」分组。
6. **边界**：只输出「条件 → 判断 → 框架性含义 → 风险提示」，不给投资评级、不给 Go/No-Go 建议；在留资格制度正文转 08、行业监测 / 薪资转 01、渠道矩阵与雇主生态转 02、法规条文转 09、赴日落地转 14、退出 / 回国转 16。
7. **免责**：全部输出保留「不构成法律意见或税务意见」声明；重大决策提示咨询执业弁護士 / 行政書士 / 税理士 / 律师。

---

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 建立操作指引：基线 / 事件触发 / 季度更新 / 年度复盘 / 个人情况变化五类入口 |

- [ ] 审计自检（preflight / audit_check）无 P0/P1，且已 `audit_pipeline --submit` 提交初审

## 语义指标人工核验清单

> 依据《信息质量评估提示词体系》模块四：语义类指标需人工 / LLM 复核，不在自动门槛内。
> `audit_sampling.py` 月度抽检强制覆盖以下 ≥2 项；抽检结果入 `engine/report-audits/info-quality/assessment-ledger.md`。

| 指标 | 核验要点 |
|---|---|
| S-01 | 一般送出機関 ≠ 認定送出機関；保証金 ≠ 違約金 ≠ 解約金；技能実習 ≠ 特定技能 ≠ 育成就労（2027-04-01 切换）。 |
| S-06 | 日本側認定送出機関中国ステータス、入管法不法就労助長条文番号・金额、技能実習登録清单待补。 |
| S-07 | 核对 620 号令修订草案、育成就労 2027-04-01 施行、入管法改正触发器。 |
| C-11 | 检查特定技能 1 号分野数（19 分野 vs 受入上限对象 12 分野）口径未统一前是否避免计数结论。 |
