# 日本自动驾驶与自动化研究 · 报告启动操作指引（Agent 可执行版）

> **适用范围**：`05-industry-autonomous` 业务线的基线 / 年度刷新两类周期报告，及重大事件插刷件。
> **使用方式**：本指引可由人类逐步照做，也可整体交给 AI Agent 执行。Agent 执行时须遵守文末「Agent 执行约定」。
> **单一事实源**：业务参数一律以 [prompts/business-config.md](./prompts/business-config.md) 为准，本指引不复制阈值与来源清单，只给路径。

---

## 0. 通用规定（两类报告共用）

### 0.1 目录速查

| 资产 | 路径 |
|---|---|
| 周期提示词（启动入口） | `05-industry-autonomous/prompts/prompt-{baseline-setup|annual-refresh}.md` |
| 业务参数（变量 / 边界 / 来源 / 触发器） | `05-industry-autonomous/prompts/business-config.md` |
| 指标登记册与研究边界档案 | `05-industry-autonomous/data/autonomous_automation_indicator_registry.md` |
| 报告产物 | `05-industry-autonomous/reports/` |
| 报告归档 | `05-industry-autonomous/reports/archives/` |
| 工具链 | `engine/tools/`（退出码：0 过 / 1 错 / 2 警告） |
| 通用层（只读，不改） | `engine/report_templates/` |

### 0.2 两种启动方式

- **手动启动（推荐首次使用）**：打开对应周期提示词 → 填写「运行变量」区块 → 将整份提示词提交给 AI 执行。
- **按年度窗口启动**：本业务线为「一次性深度全景 + 年度刷新」节拍，无月度 / 季度任务；年度窗口建议设在政府路线图或主要白皮书更新后。

### 0.3 通用前置检查（每次启动前必做）

```powershell
# 在仓库根目录执行
python engine/tools/validate.py      # 结构与命名校验，期望：本主题零 WARN / 零 ERROR
python engine/tools/lint_reports.py  # 报告内容校验，期望：0 错误
```

> **退出码说明**：`validate.py` 0 = 通过；1 = 存在错误项；2 = 仅存在警告项（警告应仅来自其他未迁移主题）。`lint_reports.py` 0 = 通过；1 = 存在错误（表格规范等）。

并人工确认三点：

1. 基线报告 `reports/2026-11-industry-autonomous.md` + 同名 HTML 存在（年度刷新的对比锚，缺失则先走第 5 节灾难恢复）。
2. 上期年度刷新报告存在（首年刷新除外），路径记入 `{{PREVIOUS_REPORT_PATH}}`。
3. 对应周期提示词存在，且继承声明指向 [engine/report_templates/industry-research/](../engine/report_templates/industry-research/)。

---

## 1. 基线报告（首期机制建立，一次性）

### 1.1 启动入口与前置条件

- 入口：[prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)
- **重要**：本业务线基线已产出（`reports/2026-11-industry-autonomous.md` v1.0 + 登记册）。**正常运行永不重跑基线**。仅以下两种情形允许再次启动：
  - 报告与登记册全部丢失（灾难恢复）；
  - 九节结构经维护规范批准重排（须在 business-config 版本记录留痕）。
- 前置条件：无上期报告依赖；确认来源清单与官方发布节奏；确认 `{{REGISTRY_PATH}}` 不存在或已获准重建。

### 1.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2026-11-13` |
| `{{BASELINE_DATE}}` | 首期基线日期（重建时改重建日期） | `2026-11-12` |
| `{{OUTPUT_PATH}}` | 固定 `reports/2026-11-industry-autonomous.md` | 同左 |
| `{{REPORT_VERSION}}` | 首期固定 `v1.0`；重建时递增 | `v1.0` |

### 1.3 执行步骤

1. 填写提示词顶部运行变量。
2. 按[业务配置第三节](./prompts/business-config.md)确认研究边界与结构映射。
3. 按四维度（L4 许可与法规 / 路线图与车企时间表 / 仓储自动化 / 商用案例）采集日文官方一手与英文权威来源；每个数字记录「机构 · 统计周期 · 发布日期 · 核验状态」。
4. 撰写报告：首期基线保留现行四章结构（不改正文）；重建场景按九节骨架撰写，标题逐字固化。
5. 首建 / 复核研究边界档案（领域边界、技术分层、主体清单与入选标准、口径清单），回写 `{{REGISTRY_PATH}}`。
6. 回填追踪表 4 项「是否更新」；空清单补记「已修正事实清单」（首期为空）。
7. 落盘 `{{OUTPUT_PATH}}` 与同名 HTML。

### 1.4 结果验证

```powershell
python engine/tools/lint_reports.py
```

人工核对：全篇口径标注完整；基线导航为简化锚点；四章（或九节）结构与声明映射一致。

---

## 2. 年度刷新（主周期）

### 2.1 启动入口与前置条件

- 入口：[prompt-annual-refresh.md](./prompts/prompt-annual-refresh.md)
- 前置条件：通用前置检查通过；年度触发器确认（L4 许可区域扩大 / 新実证批准、政府路线图时间表修订、仓储自动化重大商用化事件、岗位影响新权威研究，见[业务配置第七节](./prompts/business-config.md)）。**无触发且窗口未到 → 不启动，不得虚构变化。**

### 2.2 运行变量（必填）

| 变量 | 填写规则 | 示例（刷新 2027 年） |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-11-15` |
| `{{PREVIOUS_REPORT_PATH}}` | `reports/` 中最近一期年度刷新版（首年为空） | `reports/{{YYYY-MM}}-<slug>.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-industry-autonomous.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md`，年份＝刷新年 | `reports/{{YYYY-MM}}-<slug>.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.11.15` |

固定值（不填，读自业务配置第一节）：`{{REGISTRY_PATH}}`、`{{REPO_RAW_URL_BASE}}` 等。

### 2.3 执行步骤

1. 填变量 → 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，提取「已修正事实清单」全部条目（防回退）。
2. 运行前从登记册读取活值与研究边界档案，填入追踪表。
3. 按四个研究维度采集：①L4 许可与法规制度；②政府路线图与车企量产时间表；③仓储自动化 / 无人配送实证与商用案例；④岗位影响研究。
4. 逐模块更新（技术路线 / 法规制度 / 仓储自动化 / 技能对接），上年趋势判断逐条复判并保留原文。
5. 口径修订留痕与多口径并列；无法核实项单列「待复核清单」。
6. 数据变更摘要覆盖全部研究维度与口径清单。
7. 回写报告与登记册；落盘 md + HTML。

### 2.4 时间范围与数据范围规则

- **刷新对象 = `{{YYYY}}` 年度窗口内可取得的最新公开数据**；未发布的年度值写最近已发布周期并标注，不外推。
- 同一指标多版本并存时以官方最新发布为准，旧值仅作对比锚。
- L4 许可件数（npa）、実证项目数（SOZ / NEDO）、政府路线图目标不得合并或取均值。

### 2.5 结果验证

```powershell
python engine/tools/lint_reports.py
```

人工核对：九锚点（或声明结构）全部跳转准确；上年判断原文保留；口径并列表齐全；登记册与报告变更摘要一致。

---

## 3. 重大事件插刷

### 3.1 触发与入口

命中[业务配置第七节](./prompts/business-config.md)的结构性事件（L4 许可区域大幅扩大 / 政府路线图时间表修订 / 仓储自动化重大商用化 / 技术代际切换）时，按 [prompt-annual-refresh.md](./prompts/prompt-annual-refresh.md) 的协议提前刷新对应模块；只改受影响模块，其余章节不动。

### 3.2 命名与范围

- 追加件命名：`reports/{{YYYY-MM}}-<slug>.md`（+ 同名 HTML）；该命名不在标准正则内，`validate.py` 仅 WARN 不阻断，属预期。
- 追加件须在开头声明触发事件、受影响模块、与基线 / 上期年度版的差异摘要。
- 不替代年度刷新版；年度刷新仍按窗口执行。

---

## 4. 全类型通用收尾（每次报告落盘后必做）

### 4.1 校验

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
- [ ] 锚点跳转准确（年度刷新：`href="#sN"` 与 `<h2 id="sN">` 逐字对应）
- [ ] 浏览器打开无控制台 error

- [ ] 审计自检（preflight / audit_check）无 P0/P1，且已 `audit_pipeline --submit` 提交初审

### 4.2 归档

- 基线报告常驻 `reports/` 顶层，不归档。
- 年度刷新版保留最新 5 期，超出移入 `reports/archives/`；插刷追加件随所属年度版归档。
- 登记册修改采用增量方式：保留历史值，不覆盖。

### 4.3 提交

git 提交报告 + 登记册（建议提交信息：`report: {YYYY} 自动驾驶与自动化年度刷新` 等格式）。

### 4.4 浏览器抽查

打开 HTML，确认导航锚点、表格排版、来源链接与正文数值一致。

---

## 5. 常见异常排查

| 现象 | 原因 | 处置 |
|---|---|---|
| `validate.py` 退出码 1 | 通用层缺文件 / 业务目录结构缺项 / 报告命名不合规 | 按 error 行补齐文件或改命名；不得为过检删除通用层内容 |
| `lint_reports.py` 退出码 1 | 表格规范错误 | 按行修复 HTML |
| `validate.py` 退出码 2 | 存在警告项 | 确认警告仅来自其他未迁移主题；本主题应零 WARN |
| 基线报告缺失 | 误删或未恢复 | **停止年度刷新**，先按 prompt-baseline-setup.md 灾难恢复 |
| 上年判断被改写 | 差异合并时覆盖原文 | 恢复原文，复判结论另起段落并列呈现 |
| 官方页面无新数据 | 发布窗口未开 | 正常情形：按核验型轻运行处理，禁止虚构变化 |
| 口径冲突无法裁决 | 多源口径不同 | 并列呈现并标注来源与年份，不取均值 |
| 内联 JS 报错 | 图表语法错误 | `node --check` 定位；修复后重新落盘 |
| 链接指向旧文件名 | 报告改名后未同步 | 全库 grep 旧报告名 / 旧登记册名并改为新名 |

---

## 6. Agent 执行约定

1. **顺序不可跳**：前置检查 → 填变量 → 触发判定 → 读上期 / 基线 → 采集 → 写报告 → 回写登记册 → 校验 → 收尾。任何前置步骤失败即停，不得带病运行。
2. **单一事实源**：边界、来源、口径、触发器从 business-config.md 与登记册读取，不得凭记忆填写；提示词内严禁预填活值。
3. **防回退**：每次运行必须完整继承「已修正事实清单」；与清单冲突的旧结论不得复活。
4. **不虚构**：无触发器命中时降级为核验型轻运行；「没有数据」写成可核验陈述。
5. **留痕**：所有修正逐条补记清单；登记册更新按「实质修订 / 新增口径记录 / 复核确认 / 未取得维持上期值 / 结论不变」分组。
6. **边界**：只输出「条件 → 判断 → 框架性含义 → 风险提示」，不给投资评级、不给 Go/No-Go 建议；产业规模转 04、技能岗位转 06、管理岗转 03、现场层转 02、在留转 08、法规转 09。

## 语义指标人工核验清单

> 依据《信息质量评估提示词体系》模块四：语义类指标需人工 / LLM 复核，不在自动门槛内。
> `audit_sampling.py` 月度抽检强制覆盖以下 ≥2 项；抽检结果入 `engine/report-audits/info-quality/assessment-ledger.md`。

| 指标 | 核验要点 |
|---|---|
| S-01 | 与 01 登记册 #10 核对 L4 许可件数与实证项目数口径（许可件数不与実证项目数混用）。 |
| S-07 | 核对政府路线图（2027 社会实装 / 2030 年 1 万台）是否修订，NPA 页面访问受限的时点是否标注。 |
| S-10 | 检查车企 L4 量产 / RoboTaxi 日本落地时间（媒体线索）是否标推断、未写入事实层。 |
| C-11 | 检查「缺口 14 万+」来源是否标注待补，避免当作官方统计。 |
