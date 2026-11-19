# 日本管理岗过渡 · 报告启动操作指引（Agent 可执行版）

> **适用范围**：`03-career-management` 业务线的基线 / 月度核验 / 季度更新 / 年度复盘四类节拍，及重大事件插刷件。
> **使用方式**：本指引可由人类逐步照做，也可整体交给 AI Agent 执行。Agent 执行时须遵守文末「Agent 执行约定」。
> **单一事实源**：业务参数一律以 [prompts/business-config.md](./prompts/business-config.md) 为准，本指引不复制阈值与来源清单，只给路径。

---

## 0. 通用规定（四类节拍共用）

### 0.1 目录速查

| 资产 | 路径 |
|---|---|
| 周期提示词（启动入口） | `03-career-management/prompts/prompt-{baseline-setup|update}.md` |
| 业务参数（变量 / 边界 / 来源 / 触发器） | `03-career-management/prompts/business-config.md` |
| 指标登记册与研究边界档案 | `03-career-management/data/career_logistics_indicator_registry.md` |
| 报告产物 | `03-career-management/reports/` |
| 报告归档 | `03-career-management/reports/archives/` |
| 工具链 | `engine/tools/`（退出码：0 过 / 1 错 / 2 警告） |
| 通用层（只读，不改） | `engine/report_templates/` |

### 0.2 两种启动方式

- **手动启动（推荐首次使用）**：打开对应周期提示词 → 填写「运行变量」区块 → 将整份提示词提交给 AI 执行。
- **按周期窗口启动**：本业务线为「季度主节拍 + 事件触发；月度核验轻运行；年度复盘」，无固定自动化注册；按需窗口启动。

### 0.3 通用前置检查（每次启动前必做）

```powershell
# 在仓库根目录执行
python engine/tools/validate.py          # 结构与命名校验，期望：本主题零 WARN / 零 ERROR
python engine/tools/lint_reports.py      # 报告内容校验，期望：0 错误
```

> **退出码说明**：`validate.py` 0 = 通过；1 = 存在错误项；2 = 仅存在警告项（警告应仅来自其他未迁移主题）。`lint_reports.py` 0 = 通过；1 = 存在错误（表格规范等）。

并人工确认三点：

1. 基线报告 `reports/2026-11-career-management.md` + 同名 HTML 存在（周期更新的对比锚，缺失则先走第 5 节灾难恢复）。
2. 上期同周期报告存在（首期季度除外），路径记入 `{{PREVIOUS_REPORT_PATH}}`。
3. 对应周期提示词存在，且继承声明指向 [engine/report_templates/employment-research/](../engine/report_templates/employment-research/)。

---

## 1. 基线报告（首期机制建立，一次性）

### 1.1 启动入口与前置条件

- 入口：[prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)
- **重要**：本业务线基线已产出（`reports/2026-11-career-management.md` v1.0 + 登记册）。**正常运行永不重跑基线**。仅以下两种情形允许再次启动：
  - 报告与登记册全部丢失（灾难恢复）；
  - 九节结构经维护规范批准重排（须在 business-config 版本记录留痕）。
- 前置条件：无上期报告依赖；确认来源清单与官方发布节奏；确认 `{{REGISTRY_PATH}}` 不存在或已获准重建。

### 1.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2026-11-13` |
| `{{BASELINE_DATE}}` | 首期基线日期（重建时改重建日期） | `2026-11-12` |
| `{{OUTPUT_PATH}}` | 固定 `reports/2026-11-career-management.md` | 同左 |
| `{{REPORT_VERSION}}` | 首期固定 `v1.0`；重建时递增 | `v1.0` |

### 1.3 执行步骤

1. 填写提示词顶部运行变量。
2. 按[业务配置第三节](./prompts/business-config.md)确认研究边界与结构映射。
3. 按 4 项追踪指标采集日文官方一手与权威来源；每个数字记录「机构 · 统计周期 · 发布日期 · 核验状态」。
4. 撰写报告：首期保留现行结构（不改正文）；重建场景按九节骨架撰写，标题逐字固化。
5. 首建 / 复核研究边界档案（研究对象边界、岗位分层、主体清单与入选标准、口径清单），回写 `{{REGISTRY_PATH}}`。
6. 回填追踪表 4 项「是否更新」；空清单补记「已修正事实清单」（首期为空）。
7. 落盘 `{{OUTPUT_PATH}}` 与同名 HTML。

### 1.4 结果验证

```powershell
python engine/tools/lint_reports.py
```

人工核对：全篇口径标注完整；基线导航为简化锚点；结构与声明映射一致。

---

## 2. 主周期报告（季度更新）

### 2.1 启动入口与前置条件

- 入口：[prompt-update.md](./prompts/prompt-update.md)（`{{CADENCE}}` = 季）
- 前置条件：通用前置检查通过；季度触发器确认（运送事业管理者讲习 / 资格制度变化、目标企业采用条件变化、2024 年問題对策下的管理岗职责变化、个人晋升里程碑，见[业务配置第七节](./prompts/business-config.md)）。**无触发且窗口未到 → 不启动，不得虚构变化。**

### 2.2 运行变量（必填）

| 变量 | 填写规则 | 示例（2027 年 Q1 期） |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-04-15` |
| `{{CADENCE}}` | 固定填 `季` | `季` |
| `{{PREVIOUS_REPORT_PATH}}` | `reports/` 中最近一期季度报告（首期季度为空） | `reports/2026-11-decision-hub.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-career-management.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md`，季度＝数据所属季 | `reports/2027-03-<slug>.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.04.15` |

固定值（不填，读自业务配置第一节）：`{{REGISTRY_PATH}}`、`{{REPO_RAW_URL_BASE}}` 等。

### 2.3 执行步骤

1. 填变量 → 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，提取「已修正事实清单」全部条目（防回退）。
2. 运行前从登记册读取活值与研究边界档案，填入追踪表。
3. 按五个模块采集：①管理岗地图与路径；②业务知识体系；③管理岗日语与沟通；④过渡学习计划；⑤成果档案与晋升材料。
4. 逐模块更新；冲突数据保留双份引用；无法核实项单列「待复核清单」。
5. 数据变更摘要覆盖全部 4 项；回写报告与登记册。
6. 落盘 md + HTML。

### 2.4 时间范围与数据范围规则

- **报告季度 = 数据所属季**（非执行季）。文件名 `2027-03-<slug>.md` 覆盖 2027 年 Q1 窗口内可取得的最新数据。
- T+1 判定：本期与上期发布窗口同日或仅隔 1 日 → 报告明确标注「T+1 刷新」，价值在核验、口径澄清与阈值距离，不制造变化。
- 时效取舍：统计类近 12 个月内优先；求人样本标注采集日期。
- 同一指标多版本并存时以官方最新发布为准，旧值仅作对比锚。

### 2.5 结果验证

```powershell
python engine/tools/lint_reports.py
python engine/tools/classify_reports.py
python engine/tools/audit_preflight.py --report <报告相对路径>
python engine/tools/audit_check.py --report <报告相对路径>
python engine/tools/audit_pipeline.py --submit --report <报告相对路径>
```

人工核对：九锚点（或声明结构）全部跳转准确；已修正事实清单无回退；口径并列表齐全；登记册与报告变更摘要一致。

### 2.6 月度核验轻运行

- 入口：同上 [prompt-update.md](./prompts/prompt-update.md)（`{{CADENCE}}` = 月）。
- **只核验登记册活值与触发器状态，不重写报告**；无触发不启动新报告，仅在登记册「观察项与触发器状态」表标注「截至 {{CURRENT_DATE}} 无更新」。
- 命中任一触发器时升级为季度重点更新（按 2.1–2.5 执行）。

### 2.7 年度复盘

- 入口：同上 [prompt-update.md](./prompts/prompt-update.md)（`{{CADENCE}}` = 年）。
- 运行变量：`{{OUTPUT_PATH}}` = `reports/{{YYYY-MM}}-<slug>.md`；其余同 2.2。
- 执行要点：预测对照（上年判断逐条复判，原文保留）+ 清单复审（已修正事实清单、口径冲突清单、研究边界档案）+ 路线图重排；登记册按「增量留痕」回写，不覆盖历史值。

---

## 3. 重大事件插刷

### 3.1 触发与入口

命中[业务配置第七节](./prompts/business-config.md)的触发器且不在季度窗口内时，按 [prompt-update.md](./prompts/prompt-update.md) 的协议提前刷新对应模块；只改受影响模块，其余章节不动。

### 3.2 命名与范围

- 追加件命名：`reports/{{YYYY-MM}}-<slug>.md`（+ 同名 HTML）；该命名不在标准正则内，`validate.py` 仅 WARN 不阻断，属预期。
- 追加件须在开头声明触发事件、受影响模块、与基线 / 上期报告的差异摘要。
- 不替代季度 / 年度报告；季度 / 年度仍按窗口执行。

---

## 4. 全类型通用收尾（每次报告落盘后必做）

### 4.1 校验

```powershell
python engine/tools/lint_reports.py
python engine/tools/classify_reports.py
```

- [ ] 表格 `<thead>` / `<tbody>` 成对，多列表声明百分比列宽，无竖排塌缩
- [ ] 来源链接可点击，`[Source: 完整URL, 年份]` 完整
- [ ] 图注含单位、来源、统计周期与口径警示
- [ ] 锚点跳转准确（周期报告：`href="#sN"` 与 `<h2 id="sN">` 逐字对应）
- [ ] 浏览器打开无控制台 error

- [ ] 审计自检（preflight / audit_check）无 P0/P1，且已 `audit_pipeline --submit` 提交初审

### 4.2 归档

- 基线报告常驻 `reports/` 顶层，不归档。
- 季度报告保留最新 8 期、年度保留 5 期，超出移入 `reports/archives/`；插刷追加件随所属周期版归档。
- 登记册修改采用增量方式：保留历史值，不覆盖。

### 4.3 提交

git 提交报告 + 登记册（建议提交信息：`report: {YYYY-Qn} 管理岗过渡季度更新` 等格式）。

### 4.4 浏览器抽查

打开 HTML，确认导航锚点、表格排版、来源链接与正文数值一致。

---

## 5. 常见异常排查

| 现象 | 原因 | 处置 |
|---|---|---|
| `validate.py` 退出码 1 | 通用层缺文件 / 业务目录结构缺项 / 报告命名不合规 | 按 error 行补齐文件或改命名；不得为过检删除通用层内容 |
| `lint_reports.py` 退出码 1 | 表格规范错误 | 按行修复 HTML |
| `validate.py` 退出码 2 | 存在警告项 | 确认警告仅来自其他未迁移主题；本主题应零 WARN |
| 基线报告缺失 | 误删或未恢复 | **停止周期更新**，先按 prompt-baseline-setup.md 灾难恢复 |
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
6. **边界**：只输出「条件 → 判断 → 框架性含义 → 风险提示」，不给投资评级、不给 Go/No-Go 建议；制度细节转 08、行业结构转 04、技术制度面转 05、技术数字化转 06、法规转 09、收入环境转 07、日语学习转 11、资格教育转 10、现场层转 02。

## 语义指标人工核验清单

> 依据《信息质量评估提示词体系》模块四：语义类指标需人工 / LLM 复核，不在自动门槛内。
> `audit_sampling.py` 月度抽检强制覆盖以下 ≥2 项；抽检结果入 `engine/report-audits/info-quality/assessment-ledger.md`。

| 指标 | 核验要点 |
|---|---|
| S-01 | 与 08 报告核对资格切换要件 / 在留资格变更口径，与 07 核对管理岗薪资口径。 |
| S-09 | 检查纳期遵守率 / 装载率 / 空驶率是否各自独立、未混用，管理活动数量 ≠ 业务结果。 |
| S-10 | 检查「每 15 台 1 名」运行管理者配置是否标注为施行规则依据待核，未当作既定事实。 |
| C-12 | 检查手册 04 / 05 的讲习费用与晋升档案结构是否与登记册 #1–#4 一一对应。 |
