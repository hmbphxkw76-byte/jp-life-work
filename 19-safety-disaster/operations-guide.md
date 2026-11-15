# 日本防灾·安全·治安研究 · 报告启动操作指引（Agent 可执行版）

> **适用范围**：`19-safety-disaster` 业务线的基线 / 月度监测 / 事件触发解读 / 年度台账复盘 / 个人情况变化五类节拍。
> **使用方式**：本指引可由人类逐步照做，也可整体交给 AI Agent 执行。Agent 执行时须遵守文末「Agent 执行约定」。
> **单一事实源**：业务参数一律以 [prompts/business-config.md](./prompts/business-config.md) 为准，本指引不复制阈值与来源清单，只给路径。

---

## 0. 通用规定（各节拍共用）

### 0.1 目录速查

| 资产 | 路径 |
|---|---|
| 周期提示词（启动入口） | `19-safety-disaster/prompts/prompt-{baseline-setup|policy-review}.md` |
| 业务参数（变量 / 边界 / 来源 / 触发器） | `19-safety-disaster/prompts/business-config.md` |
| 指标登记册 | `19-safety-disaster/data/safety_disaster_indicator_registry.md` |
| 报告产物 | `19-safety-disaster/reports/` |
| 报告归档 | `19-safety-disaster/reports/archives/` |
| 工具链 | `src/prompts-tools/tools/`（退出码：0 过 / 1 错 / 2 警告） |
| 通用层（只读，不改） | `src/report_templates/` |

### 0.2 五种启动方式

- **基线**：一次性机制建立；已产出后永不重跑，仅灾难恢复或经批准的结构重排可重启。
- **月度监测**：核验与判定为主，产出月度监测简报（八节骨架）；无触发降级为核验 / 收敛型轻运行。
- **事件触发解读**：大规模灾害 / 突发事件 / 官方政策修订后启动；无触发不启动。
- **年度台账复盘**：每年固定窗口启动；读最近一期年度复盘与基线。
- **个人情况变化**：定居地 / 通勤路线 / 家庭构成变化时启动；只写增量与条件化建议。

### 0.3 通用前置检查（每次启动前必做）

```powershell
# 在仓库根目录执行
python src/prompts-tools/tools/validate.py      # 结构与命名校验
python src/prompts-tools/tools/lint_reports.py  # 报告内容校验（HTML）
```

> **退出码说明**：`validate.py` 0 = 通过；1 = 存在错误项；2 = 仅存在警告项。`lint_reports.py` 0 = 通过；1 = 存在错误。

并人工确认三点：

1. 基线报告 `reports/2026-11-safety-disaster.md` 存在（解读的对比锚，缺失则先走第 5 节灾难恢复）。
2. 上期报告存在（首期除外），路径记入 `{{PREVIOUS_REPORT_PATH}}`。
3. 对应周期提示词存在，且继承声明指向 [src/report_templates/market-monitoring/](../src/report_templates/market-monitoring/)。

---

## 1. 基线报告（首期机制建立，一次性）

### 1.1 启动入口与前置条件

- 入口：[prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)
- **重要**：本业务线基线已产出（`reports/2026-11-safety-disaster.md` v1.0 + 登记册）。**正常运行永不重跑基线**。仅以下两种情形允许再次启动：①报告与登记册全部丢失（灾难恢复）；②十节结构经维护规范批准重排（须在 business-config 版本记录留痕）。
- 前置条件：无上期报告依赖；确认来源清单与官方发布节奏；确认 `{{REGISTRY_PATH}}` 不存在或已获准重建。

### 1.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2026-11-14` |
| `{{BASELINE_DATE}}` | 首期基线日期（重建时改重建日期） | `2026-11-14` |
| `{{OUTPUT_PATH}}` | 固定 `reports/2026-11-safety-disaster.md` | 同左 |
| `{{REPORT_VERSION}}` | 首期固定 `v1.0`；重建时递增 | `v1.0` |

### 1.3 执行步骤

1. 填写提示词顶部运行变量。
2. 按[业务配置第三节](./prompts/business-config.md)确认研究边界与十节结构映射。
3. 按 12+1 项追踪指标采集官方原文来源；每条数据记录「机构 · 发布与生效日期 · 版本日期 · 核验状态」。
4. 撰写报告：十节骨架，标题逐字固化；覆盖防灾体制、避难与情报、治安与人身、领事保护、应急联络五维。
5. 首建 / 复核研究边界档案（领域边界、五维分层、主体清单与入选标准、口径清单），回写 `{{REGISTRY_PATH}}`。
6. 回填追踪表 12+1 项「是否更新」；空清单补记「已修正事实清单」（首期为空）。
7. 落盘 `{{OUTPUT_PATH}}`；如需 HTML，用 `md2html.py` 生成。

### 1.4 结果验证

```powershell
python src/prompts-tools/tools/lint_reports.py
```

人工核对：全篇引用回溯官方原文；基线导航为简化锚点；十节结构与声明映射一致。

---

## 2. 月度监测

### 2.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{CYCLE}}` = 月度监测）
- 前置条件：通用前置检查通过；按 T+0 / T+1 判定核对官方最新一期；无触发器命中时降级为核验 / 收敛型轻运行。

### 2.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-04-01` |
| `{{PREVIOUS_REPORT_PATH}}` | 上一期月度报告路径 | `reports/2027-03-safety-disaster.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-safety-disaster.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md` | `reports/2027-04-safety-disaster.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.04.01` |

### 2.3 执行步骤

1. 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，提取「已修正事实清单」全部条目（防回退）。
2. 按八节骨架产出月度监测简报：结论先行 → 关键数字卡 → 月度指标逐项对比 → 信号灯判定 → 与首期基线的偏离 → 数据缺口与未核验项 → 下期观察清单 → 台账更新编号与来源。
3. 逐项核对 12+1 项追踪指标并填「是否更新」；未核实项单列「待复核清单」。
4. 回写报告与登记册；如需 HTML 用 `md2html.py` 生成并过 `lint_reports.py`。

### 2.4 结果验证

```powershell
python src/prompts-tools/tools/lint_reports.py
```

人工核对：T+0 / T+1 判定明确；信号计数与规则一致；登记册与报告变更摘要一致。

---

## 3. 事件触发解读

### 3.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{CYCLE}}` = 事件触发）
- 前置条件：通用前置检查通过；触发器确认（気象警報・警戒レベル、自治体防災計画与防災メール、多言語防災気象情報 / 情報難民、救急安心センター、警察庁统计 / 特殊诈欺、外務省海外安全、大规模灾害 / 突发事件，见[业务配置第七节](./prompts/business-config.md)）。**无触发且窗口未到 → 不启动，不得虚构变化。**

### 3.2 运行变量（必填）

| 变量 | 填写规则 | 示例 |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-08-15` |
| `{{TRIGGER_TYPE}}` | 新政策 / 修订 / 细则 / 统计发布 / 大规模灾害 | `大规模灾害` |
| `{{PREVIOUS_REPORT_PATH}}` | 上期报告路径（如无则空） | `reports/2027-07-safety-disaster.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-safety-disaster.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md` | `reports/2027-08-15-台风避难.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.08.15` |

### 3.3 执行步骤

1. 原文回溯先行：登记官方原文（URL、版本日期、文本完整性）后才进入解读。
2. 填变量 → 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，提取「已修正事实清单」全部条目（防回退）。
3. 逐条解读：预警级别、避难行动、外语情报可用性、应急联络与领事保护口径。
4. 影响评估：个人接收清单、避难路线、安否联络。
5. 应对建议：条件化建议（标「建议」，与事实分离）。
6. 回写报告与登记册；如需 HTML 用 `md2html.py` 生成。

---

## 4. 年度台账复盘

### 4.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{CYCLE}}` = 年度复盘）
- 前置条件：通用前置检查通过；年度窗口到达。

### 4.2 运行变量（必填）

| 变量 | 填写规则 | 示例（复盘 2027 年） |
|---|---|---|
| `{{CURRENT_DATE}}` | 本次执行日期 | `2027-11-15` |
| `{{PREVIOUS_REPORT_PATH}}` | `reports/` 中最近一期年度复盘（首年为空） | `reports/{{YYYY-MM}}-<slug>.md` |
| `{{BASELINE_REPORT_PATH}}` | 固定 `reports/2026-11-safety-disaster.md` | 同左 |
| `{{OUTPUT_PATH}}` | `reports/{{YYYY-MM}}-<slug>.md` | `reports/{{YYYY-MM}}-<slug>.md` |
| `{{REPORT_VERSION}}` | `v` + 执行日期 | `v2027.11.15` |

### 4.3 执行步骤

1. 读 `{{PREVIOUS_REPORT_PATH}}` 与基线，提取「已修正事实清单」全部条目（防回退）。
2. 台账全量复核：五维指标、口径清单、来源清单、监测日历。
3. 年度复盘：信号规则 S01–S06 阈值回测；上年判断逐条复判，原文保留。
4. 数据变更摘要覆盖全部研究维度与口径清单。
5. 回写报告与登记册；如需 HTML 用 `md2html.py` 生成。

---

## 5. 个人情况变化件

### 5.1 启动入口与前置条件

- 入口：[prompt-policy-review.md](./prompts/prompt-policy-review.md)（`{{TRIGGER_TYPE}}` = 个人情况变化）
- 前置条件：定居地 / 通勤路线 / 家庭构成发生变化；通用前置检查通过。

### 5.2 执行步骤

1. 读基线、最近一期解读与登记册；提取变化前后的条件差异。
2. 登记第三层个人接收清单（防災メール、避難所、安否联络方式）。
3. 只写条件化建议与执行顺序，不给个案法律结论。
4. 回写登记册「观察项」；如需 HTML 用 `md2html.py` 生成。

---

## 6. 全类型通用收尾（每次报告落盘后必做）

### 6.1 校验

```powershell
python src/prompts-tools/tools/lint_reports.py
python src/prompts-tools/tools/classify_reports.py
python src/prompts-tools/tools/audit_preflight.py --report <报告相对路径>
python src/prompts-tools/tools/audit_check.py --report <报告相对路径>
python src/prompts-tools/tools/audit_pipeline.py --submit --report <报告相对路径>
```

- [ ] 表格 `<thead>` / `<tbody>` 成对，多列表声明百分比列宽，无竖排塌缩
- [ ] 来源链接可点击，`[Source: 完整URL, 年份]` 完整
- [ ] 锚点跳转准确（`href="#sN"` 与 `<h2 id="sN">` 逐字对应）
- [ ] 浏览器打开无控制台 error

### 6.2 归档

- 基线报告常驻 `reports/` 顶层，不归档。
- 月度报告保留最新 12 期，超出移入 `reports/archives/`；年度复盘保留最新 5 期。
- 登记册修改采用增量方式：保留历史值，不覆盖。

### 6.3 提交

git 提交报告 + 登记册（建议提交信息：`report: {YYYY-MM-DD} 防灾安全事件触发解读` 等格式）。

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
| 电话口径错误 | 号码混用 | 以警察庁 / 消防庁最新页为准，回写登记册 |

---

## 8. Agent 执行约定

1. **顺序不可跳**：前置检查 → 填变量 → 触发判定 → 原文回溯 → 读上期 / 基线 → 逐条解读 → 回写登记册 → 校验 → 收尾。任何前置步骤失败即停，不得带病运行。
2. **单一事实源**：边界、来源、口径、触发器从 business-config.md 与登记册读取，不得凭记忆填写；提示词内严禁预填活值。
3. **防回退**：每次运行必须完整继承「已修正事实清单」；与清单冲突的旧结论不得复活。
4. **不虚构**：无触发器命中时降级为核验型轻运行；「没有数据」写成可核验陈述。
5. **留痕**：所有修正逐条补记清单；登记册更新按「实质修订 / 新增口径记录 / 复核确认 / 未取得维持上期值 / 结论不变」分组。
6. **边界**：只输出「条件 → 判断 → 框架性含义 → 风险提示」；不替代官方预警与应急指令；就医与急救医疗转 15、在留风险转 08 / 09、地域防灾渠道转 13、多文化共生转 12、家族带同转 18。

---

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 建立操作指引：基线 / 月度监测 / 事件触发 / 年度复盘 / 个人情况变化五类入口 |

- [ ] 审计自检（preflight / audit_check）无 P0/P1，且已 `audit_pipeline --submit` 提交初审
