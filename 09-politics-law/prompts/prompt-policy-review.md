# 日本 · 政治与法规 · 事件触发解读 / 年度台账复盘提示词（政策法规解读型）

> **用途**：事件触发单份解读（新政策 / 修订 / 配套细则出台后）与年度台账复盘统一入口。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：单份解读件 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md` + 同名 HTML）或年度台账复盘（`reports/{{YYYY-MM}}-<slug>.md` + 同名 HTML）。解读件命名不在标准正则内，validate 仅 WARN 不阻断，属预期。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../engine/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../engine/report_templates/monitoring-common-spec.md) × [事件触发解读类型模板（政策法规解读型）](../../engine/report_templates/policy-analysis/prompt-policy-review-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

---

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期，格式 YYYY-MM-DD
{{TRIGGER_TYPE}}         = 本次触发类型（新政策 / 修订 / 细则 / 年度台账复盘）
{{PREVIOUS_REPORT_PATH}} = 上期解读 / 复盘路径（如无则空，仅锚定基线）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}        = data/politics_law_indicator_registry.md
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md 或 reports/{{YYYY-MM}}-<slug>.md
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

固定值（不填，读自业务配置第一节）：`{{REGION}}`、`{{TOPIC}}`、`{{FRESHNESS_PRIORITY}}`、`{{SOURCE_LANGUAGE_RULE}}`、`{{REPO_RAW_URL_BASE}}`。

**任务目标**：完成「原文回溯 → 逐条解读 → 影响评估 → 台账更新」闭环；新政策先登记发布与生效日期、官方 URL 后才可进入解读；征求意见稿登记但标注「非最终文本，以正式发布为准」；无触发时不启动新解读，台账标注「截至 {{CURRENT_DATE}} 无更新」。

---

## 一、节拍与触发

事件触发解读 + 年度台账复盘设计见[事件触发解读类型模板第一节](../../engine/report_templates/policy-analysis/prompt-policy-review-template.md)。业务触发器清单（`事件 → 受影响模块`）见[业务配置第七节](./business-config.md)：

```
- 入管法 / 相关法令改正（e-Gov 公布） → 01 在留法规框架
- 移民政策重大动向（受入方针、政党政策变化） → 02 政治动向与移民政策环境
- 大选 / 党首更替（主要政党对外国人材政策口径变化） → 02 光谱小节
- 外国人权利相关法案·制度动向（地方参政权、行政手续多语言化等） → 02 观察点小节
- 劳动维权渠道 / 热线变化 → 03 维权与合规工具箱
- 01-ssw-driver 修正清单涉及维权条目（ITJ / GFP 类） → 03
```

## 二、项目专属硬性约束

1. **官方原文铁律**：法规类须 e-Gov / 官方原文；媒体转述仅作线索。法令条文 / 政府解说页 / 媒体转述三层须分别标注。
2. **结论边界**：不构成法律意见；应对建议标「建议」；歧义条款多解并列；政治动向影响判断一律标「推断」。
3. **术语口径**：入管法 ≠ 関係法令；在留资格种类引用须注明制度（与 08 口径一致）。
4. **边界纪律**：签证实务归 08、劳动合规细节归 02、自动驾驶法规归 05、永住年收财务归 07、地域信息归 13。
5. **交叉验证锚**：ITJ / GFP 等维权渠道结论与 01-ssw-driver 最新报告文首「已修正事实清单」只读核对；冲突回官方原文复核，由 01 主责更新，本主题不得独立回写。

## 三、各模块要点

按[业务配置第 3.2 节](./business-config.md)的结构映射逐模块实例化：

- **在留法规框架（对应监管框架总览 / 重点政策逐条解读）**：入管法及关系法令改正、8 部法律栈、个人必熟 Top 5 条款、法规检索入口。
- **政治动向与移民政策环境（对应影响对象矩阵 / 生效时间线）**：三条政策主线、政党移民政策光谱（立场列为推断，须实际打开验证）、外国人权利动向观察点、跟踪清单；政策更新日志统一写入 08 手册 09-政策更新日志。
- **维权与合规工具箱（对应合规应对建议）**：劳动纠纷五级阶梯、在留问题咨询、证据留存规则、紧急情况速查。

> 若本期按九节骨架重排：九节标题逐字继承基线（或经批准的骨架），不得增删节或调整顺序；重排须在[业务配置](./business-config.md)版本记录留痕。

## 四、基线锚定与防回退

- 读取 `{{PREVIOUS_REPORT_PATH}}`（如无则空）与 `{{BASELINE_REPORT_PATH}}`，继承监管框架地图、解读规则与全部已核实结论。
- 逐条继承「已修正事实清单」（ITJ / GFP 类以 01-ssw-driver 报告文首为单一事实源），产生修正后追加（格式见[通用基座第五节](../../engine/report_templates/prompt-generic-base.md)）；严禁重新引入已被推翻的说法；无来源不得入清单。
- 上年趋势判断逐条复判，原文保留；不得删除或改写上年判断。

## 五、追踪表与登记册联动

按[业务配置第八节](./business-config.md)的 5 项追踪指标逐项核对并填写「是否更新」；运行前从 `{{REGISTRY_PATH}}` 读台账 → 增量登记 / 状态变更 → 运行后回写。政策变更摘要覆盖本期新增 / 修订 / 生效 / 废止清单及影响方向；未核实项单列「待复核清单」。prompt 模板内不填活值。

## 六、执行方式（建议）

1. 原文回溯先行：完成官方原文登记（URL、版本日期、文本完整性）后再启动逐条解读子代理。
2. 主代理读取 `{{BASELINE_REPORT_PATH}}` 做框架对齐，继承已修正事实清单，应用第三节要点。
3. 与现行制度冲突的解读须并列新旧对照；无法核实项单列「待复核清单」。
4. 回写报告与登记册后运行 `python engine/tools/md2html.py` 重新生成 HTML，并运行 `python engine/tools/lint_reports.py` 校验。

## 七、渲染与交付

- 交付格式：md + 同目录自包含 HTML；年度台账复盘报告含顶部九锚点导航（`.report-nav`），`.nav-url` = `{{REPO_RAW_URL_BASE}}` + `/reports/{本期文件名}`。
- HTML 须通过 `lint_reports.py` 标签配对校验。
- 基线报告常驻 `reports/` 顶层不归档；解读件按保留策略执行（年度复盘保留 5 期，超出移入 `reports/archives/`）。

## 八、质量自检（通用清单之外的本主题专属项）

- [ ] 全部引用回溯官方原文并附 URL；零媒体转述直引
- [ ] 法令条文（e-Gov 原文）、政府解说页、媒体转述三层已分别标注
- [ ] 在留资格种类引用与 08-visa-immigration 口径一致
- [ ] 政治动向影响判断均标注为推断；未验证官网的政党未写立场
- [ ] 未出现已修正的 ITJ 窗口 / GFP 官方支持机构引用
- [ ] 政策台账增量 / 状态变更已回写；prompt 模板无硬编码活值
- [ ] 建议章与事实分离；不构成法律意见声明保留
- [ ] 追踪表 5 项均已核对并填写「是否更新」
- [ ] `{{REGISTRY_PATH}}` 已读已写，变更摘要与登记册一致
- [ ] 政策变更摘要 + 待复核清单已产出
- [ ] HTML 通过 lint（标签配对）

---

## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依政策法规解读型事件触发 / 年度台账复盘模板实例化；承接原 `prompt-politics-law-update.md` 的触发器与章节更新要点，改按事件触发 + 年度台账复盘节拍组织 |
