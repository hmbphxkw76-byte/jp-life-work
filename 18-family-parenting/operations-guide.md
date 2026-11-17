# 日本家族·育儿·人生事件研究 · 报告启动操作指引（Agent 可执行版）

> **适用范围**：`18-family-parenting` 业务线的基线 / 月度核验 / 季度更新 / 年度台账复盘 / 事件触发解读 / 个人情况变化六类节拍。
> **使用方式**：本指引可由人类逐步照做，也可整体交给 AI Agent 执行。Agent 执行时须遵守文末「Agent 执行约定」。
> **单一事实源**：业务参数一律以 [prompts/business-config.md](./prompts/business-config.md) 为准，本指引不复制阈值与来源清单，只给路径。

---

## 0. 通用规定（各节拍共用）

### 0.1 目录速查

| 资产 | 路径 |
|---|---|
| 周期提示词（启动入口） | `18-family-parenting/prompts/prompt-{baseline-setup|policy-review}.md` |
| 业务参数（变量 / 边界 / 来源 / 触发器） | `18-family-parenting/prompts/business-config.md` |
| 指标登记册 | `18-family-parenting/data/family_parenting_indicator_registry.md` |
| 报告产物 | `18-family-parenting/reports/` |
| 报告归档 | `18-family-parenting/reports/archives/` |
| 工具链 | `engine/tools/`（退出码：0 过 / 1 错 / 2 警告） |
| 通用层（只读，不改） | `engine/report_templates/` |

### 0.2 六种启动方式

- **基线**：一次性机制建立；已产出后永不重跑，仅灾难恢复或经批准的结构重排可重启。
- **月度核验**：只核验登记册活值与触发器状态，不重写报告；命中触发器时升级为季度重点更新。
- **季度更新**：全模块刷新，产出九节更新版报告。
- **年度台账复盘**：每年制度年度改定后启动；读最近一期年度复盘与基线。
- **事件触发解读**：官方政策 / 修订 / 细则出台后启动；无触发不启动。
- **个人情况变化**：婚姻 / 生育 / 子女 / 资格 / 收入变化时启动；只写增量与条件化建议。

### 0.3 通用前置检查（每次启动前必做）

```powershell
# 在仓库根目录执行
python engine/tools/validate.py      # 结构与命名校验
python engine/tools/lint_reports.py  # 报告内容校验（HTML）
```

> **退出码说明**：`validate.py` 0 = 通过；1 = 存在错误项；2 = 仅存在警告项。`lint_reports.py` 0 = 通过；1 = 存在错误。

并人工确认三点：

1. 基线报告 `reports/2026-11-family-parenting.md` 存在（解读的对比锚，缺失则先走第 5 节灾难恢复）。
2. 上期报告存在（首期除外），路径记入 `{{PREVIOUS_REPORT_PATH}}`。
3. 对应周期提示词存在，且继承声明指向 [engine/report_templates/employment-research/](../engine/report_templates/employment-research/)。

---

## 1. 基线报告（首期机制建立，一次性）

### 1.1 启动入口与前置条件

- 入口：[prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)
- **重要**：本业务线基线已产出（`reports/2026-11-family-parenting.md` v1.0 + 登记册）。**正常运行永不重跑基线**。仅以下两种情形允许再次启动：①报告与登记册全部丢失（灾难恢复）；②九节结构经维护规范批准重排（须在 business-config 版本记录留痕）。
- 前置条件：无上期报告依赖；确认来源清单与官方发布节奏；确认 `{{REGISTRY_PATH}}` 不存在或已获准重建。

### 1.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2026-11-14` |
| `{{BASELINE_DATE}}` | 首期基线日期（重建时改重建日期） | `2026-11-14` |
| `{{OUTPUT_PATH}}` | 固定 `reports/2026-11-family-parenting.md` | 同左 |
| `{{REPORT_VERSION}}` | 首期固定 `v1.0`；重建时递增 | `v1.0` |

### 1.3 执行步骤

1. 填写提示词顶部运行变量。
2. 按[业务配置第三节](./prompts/business-config.md)确认研究边界与九节结构映射。
3. 按 12+1 项追踪指标采集官方原文来源；每条数据记录「机构 · 发布与生效日期 · 版本日期 · 核验状态」。
4. 撰写报告：九节骨架，标题逐字固化。
5. 首建 / 复核研究边界档案（领域边界、四段分层、主体清单与入选标准、口径清单），回写 `{{REGISTRY_PATH}}`。
6. 回填追踪表 12+1 项「是否更新」；空清单补记「已修正事实清单」（首期为空）。
7. 落盘 `{{OUTPUT_PATH}}`；如需 HTML，用 `md2html.py` 生成。

### 1.4 结果验证

```powershell
python engine/tools/lint_reports.py
```

人工核对：全篇引用回溯官方原文；基线导航为简化锚点；九节结构与声明映射一致。

---

## 2. 月度核验（轻运行）

### 2.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{CYCLE}}` = 月度核验）
- 前置条件：通用前置检查通过；无触发器命中时**不重写报告**，仅在登记册「观察项与触发器状态」登记「截至 {{CURRENT_DATE}} 无更新」。

### 2.2 执行步骤

1. 读 `{{REGISTRY_PATH}}` 与基线，核对 12+1 项活值与触发器状态。
2. 命中任一触发器 → 升级为季度重点更新（第三节）。
3. 未命中 → 登记册标注无更新，落盘（不重写报告）。

---

## 3. 季度更新 / 事件触发解读

### 3.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{CYCLE}}` = 季度更新 / 事件触发）
- 前置条件：通用前置检查通过；触发器确认（家族滞在扶养审查、资格外活動、出産育児一時金、児童手当 / 児童扶養手当、保育 / 教育制度、文科省就学 / 日本語指導发布、婚姻家庭与继承法规、定住者衔接、世帯年収 / 扶养控除口径，见[业务配置第七节](./prompts/business-config.md)）。**无触发且窗口未到 → 不启动，不得虚构变化。**

### 3.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-04-01` |
| `{{TRIGGER_TYPE}}` | 新政策 / 修订 / 细则 / 统计发布 | `修订` |
| `{{PREVIOUS_REPORT_PATH}}` | 上期报告路径（如无则空） | `reports/2027-03-31-家族滞在扶养改定.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-family-parenting.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md` | `reports/2027-04-01-儿童手当改定.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.04.01` |

### 3.3 执行步骤

1. 原文回溯先行：登记官方原文（URL、版本日期、文本完整性）后才进入解读。
2. 填变量 → 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，提取「已修正事实清单」全部条目（防回退）。
3. 逐条解读：条款含义、新旧制度衔接对照、歧义多解、官方答问与细则对照。
4. 影响评估：家庭场景影响矩阵增量、过渡期与合规时点。
5. 应对建议：合规要点、待明确事项清单（标「建议」，与事实分离）。
6. 回写报告与登记册；落盘 md（如需 HTML 用 md2html.py）。

### 3.4 结果验证

```powershell
python engine/tools/lint_reports.py
```

人工核对：解读锚点准确；已修正事实清单无回退；新旧对照完整；登记册与报告变更摘要一致。

---

## 4. 年度台账复盘

### 4.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{CYCLE}}` = 年度复盘）
- 前置条件：通用前置检查通过；年度窗口到达（制度年度改定后）。

### 4.2 运行变量（必填）

| 变量 | 填写规则 | 示例（复盘 2027 年） |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-11-15` |
| `{{PREVIOUS_REPORT_PATH}}` | `reports/` 中最近一期年度复盘（首年为空） | `reports/{{YYYY-MM}}-<slug>.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-family-parenting.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md` | `reports/{{YYYY-MM}}-<slug>.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.11.15` |

### 4.3 执行步骤

1. 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，提取「已修正事实清单」全部条目（防回退）。
2. 台账全量复核：法规清单、发布渠道、生效时间线、家庭场景影响矩阵。
3. 年度监管态势综述；上年判断逐条复判，原文保留。
4. 数据变更摘要覆盖全部研究维度与口径清单。
5. 回写报告与登记册；落盘 md（如需 HTML 用 md2html.py）。

---

## 5. 个人情况变化件

### 5.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{TRIGGER_TYPE}}` = 个人情况变化）
- 前置条件：婚姻 / 生育 / 子女 / 资格 / 收入发生变化；通用前置检查通过。

### 5.2 执行步骤

1. 读基线、最近一期解读与登记册；提取变化前后的条件差异。
2. 只写条件化建议与执行顺序，不给个案法律 / 税务结论。
3. 回写登记册「观察项」；落盘 md（如需 HTML 用 md2html.py）。

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
- [ ] 锚点跳转准确（年度复盘：`href="#sN"` 与 `<h2 id="sN">` 逐字对应）
- [ ] 浏览器打开无控制台 error

### 6.2 归档

- 基线报告常驻 `reports/` 顶层，不归档。
- 年度复盘版保留最新 5 期，超出移入 `reports/archives/`；事件触发解读件随所属年度版归档。
- 登记册修改采用增量方式：保留历史值，不覆盖。

### 6.3 提交

git 提交报告 + 登记册（建议提交信息：`report: {YYYY-MM-DD} 家族育儿事件触发解读` 等格式）。

---

## 7. 常见异常排查

| 现象 | 原因 | 处置 |
|---|---|---|
| `validate.py` 退出码 1 | 通用层缺文件 / 业务目录结构缺项 / 报告命名不合规 | 按 error 行补齐文件或改命名；不得为过检删除通用层内容 |
| `lint_reports.py` 退出码 1 | 表格规范错误 | 按行修复 HTML |
| `validate.py` 退出码 2 | 存在警告项 | 确认警告仅来自其他未迁移主题 |
| 基线报告缺失 | 误删或未恢复 | **停止周期更新**，先按 prompt-baseline-setup.md 灾难恢复 |
| 官方页面无新数据 | 发布窗口未开 | 正常情形：按核验型轻运行处理，禁止虚构变化 |
| 口径冲突无法裁决 | 多源口径不同 | 并列呈现并标注来源与年份，不取均值 |
| 链接指向旧文件名 | 报告改名后未同步 | 全库 grep 旧报告名并改为新名 |

---

## 8. Agent 执行约定

1. **顺序不可跳**：前置检查 → 填变量 → 触发判定 → 原文回溯 → 读上期 / 基线 → 逐条解读 → 回写登记册 → 校验 → 收尾。任何前置步骤失败即停，不得带病运行。
2. **单一事实源**：边界、来源、口径、触发器从 business-config.md 与登记册读取，不得凭记忆填写；提示词内严禁预填活值。
3. **防回退**：每次运行必须完整继承「已修正事实清单」；与清单冲突的旧结论不得复活。
4. **不虚构**：无触发器命中时降级为核验型轻运行；「没有数据」写成可核验陈述。
5. **留痕**：所有修正逐条补记清单；登记册更新按「实质修订 / 新增口径记录 / 复核确认 / 未取得维持上期值 / 结论不变」分组。
6. **边界**：只输出「条件 → 判断 → 框架性含义 → 风险提示」，不给法律 / 税务结论；永住・归化・在留资格制度正文转 08、学制与就学转 10、就医与保险转 15、税制 / 年金转 07、住民与行政转 14、法规条文转 09、防灾转 19。

---

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 建立操作指引：基线 / 月度核验 / 季度更新 / 年度复盘 / 事件触发 / 个人情况变化六类入口 |

- [ ] 审计自检（preflight / audit_check）无 P0/P1，且已 `audit_pipeline --submit` 提交初审
