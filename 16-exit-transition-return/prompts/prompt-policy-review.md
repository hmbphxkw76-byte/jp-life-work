# 日本 退出·转型·回国 事件触发解读 / 年度台账复盘提示词（政策法规解读型）

> **用途**：事件触发单份解读（新政策 / 修订 / 配套细则出台后）与年度台账复盘统一入口。可直接复制，替换顶部变量后提交给 AI 执行。
> **产出**：单份解读件 `{{OUTPUT_PATH}}`（`reports/{{YYYY-MM}}-<slug>.md` + 同名 HTML）或年度台账复盘（`reports/{{YYYY-MM}}-<slug>.md` + 同名 HTML）。解读件命名不在标准正则内，validate 仅 WARN 不阻断，属预期。
>
> **继承声明（四层体系）**：本文件 = [通用基座](../../engine/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../engine/report_templates/monitoring-common-spec.md) × [事件触发解读类型模板（政策法规解读型）](../../engine/report_templates/policy-analysis/prompt-policy-review-template.md) × [业务专属配置](./business-config.md)。冲突时以本文件为准。

---

## 运行变量（每次运行前填写）

```
{{CURRENT_DATE}}         = 本次执行日期，格式 YYYY-MM-DD
{{TRIGGER_TYPE}}         = 本次触发类型（新政策 / 修订 / 细则 / 年度台账复盘 / 个人情况变化）
{{PREVIOUS_REPORT_PATH}} = 上期解读 / 复盘路径（如无则空，仅锚定基线）
{{BASELINE_REPORT_PATH}} = reports/{{YYYY-MM}}-<slug>.md
{{REGISTRY_PATH}}        = data/exit_transition_return_indicator_registry.md
{{OUTPUT_PATH}}          = reports/{{YYYY-MM}}-<slug>.md 或 reports/{{YYYY-MM}}-<slug>.md
{{REPORT_VERSION}}       = 本次版本号，格式 vYYYY.MM.DD
```

固定值（不填，读自业务配置第一节）：`{{REGION}}`、`{{TOPIC}}`、`{{FRESHNESS_PRIORITY}}`、`{{SOURCE_LANGUAGE_RULE}}`、`{{REPO_RAW_URL_BASE}}`。

**任务目标**：完成「原文回溯 → 逐条解读 → 影响评估 → 台账更新」闭环；新政策先登记发布与生效日期、官方 URL 后才可进入解读；征求意见稿登记但标注「非最终文本，以正式发布为准」；无触发时不启动新解读，台账标注「截至 {{CURRENT_DATE}} 无更新」。

---

## 一、节拍与触发

事件触发解读 + 年度台账复盘设计见[事件触发解读类型模板第一节](../../engine/report_templates/policy-analysis/prompt-policy-review-template.md)。业务触发器清单（`事件 → 受影响模块`）见[业务配置第七节](./business-config.md）：

```
- 退職・労働条件・雇用保険改定 → 退出模块
- 健康保険任意継続要件 / 期限改定 → 退出模块
- 厚生年金脱退要件 / 手续改定 → 回国模块
- 在留資格取消・変更・特定活動规则改定 → 退出 / 转型模块
- 特定技能 2 号路径 / 业务限制改定 → 转型模块
- 転職・资格外活动规则改定 → 转型模块
- 帰国前確定申告・住民税 / 所得税规则改定 → 回国模块
- 退室・解約・车辆・通信规则改定 → 回国模块
- 个人情况变化 → 个人情况变化件
- 08-visa-immigration / 07-economy-finance 最新报告「已修正事实清单」追加 → 对应文档回写
```

## 二、项目专属硬性约束

1. **官方原文铁律**：媒体转述仅作线索；引用逐条附官方原文 URL 与版本日期。
2. **结论边界**：不构成法律意见或税务意见；应对建议标「建议」；歧义条款多解并列。
3. **术语口径**：退職 ≠ 退去強制；在留資格取消 ≠ 在留資格変更；特定活動 ≠ 技能実習；再入国許可 ≠ みなし再入国；健康保険任意継続 ≠ 国民健康保険。
4. **边界纪律**：法规条文深度解读归 09、税制 / 年金计算归 07、永住 / 归化 / 资格取消制度正文归 08、赴日落地归 14、现场层归 02。
5. **交叉验证锚**：08-visa-immigration / 07-economy-finance 最新报告 / 登记册只读核对；冲突回官方原文复核，由来源主题主责更新，本主题不得独立回写。

## 三、各模块要点

按[业务配置第 3.3 节](./business-config.md)的结构映射逐模块实例化：

- **退出**：退職、雇用保険、健康保険任意継続、被用者保険退出、在留资格状态；
- **转型**：在留資格変更、特定活動、其他就労资格、転職边界、特定技能 2 号限制；
- **回国**：年金脱退执行、帰国前確定申告、在留卡返还、再入国、退室、通信 / 银行 / 车辆。

> 若本期按九节骨架重排：九节标题逐字继承基线（或经批准的骨架），不得增删节或调整顺序；重排须在[业务配置](./business-config.md)版本记录留痕。

## 四、基线锚定与防回退

- 读取 `{{PREVIOUS_REPORT_PATH}}`（如无则空）与 `{{BASELINE_REPORT_PATH}}`，继承监管框架地图、解读规则与全部已核实结论。
- 逐条继承「已修正事实清单」（以来源主题最新报告文首为单一事实源），产生修正后追加（格式见[通用基座第五节](../../engine/report_templates/prompt-generic-base.md)）；严禁重新引入已被推翻的说法；无来源不得入清单。
- 上年趋势判断逐条复判，原文保留；不得删除或改写上年判断。

## 五、追踪表与登记册联动

按[业务配置第八节](./business-config.md)的 12+1 项追踪指标逐项核对并填写「是否更新」；运行前从 `{{REGISTRY_PATH}}` 读台账 → 增量登记 / 状态变更 → 运行后回写。政策变更摘要覆盖本期新增 / 修订 / 生效 / 废止清单及影响方向；未核实项单列「待复核清单」。prompt 模板内不填活值。

## 六、执行方式（建议）

1. 原文回溯先行：完成官方原文登记（URL、版本日期、文本完整性）后才启动逐条解读子代理。
2. 主代理读取 `{{BASELINE_REPORT_PATH}}` 做框架对齐，继承已修正事实清单，应用第三节要点。
3. 与现行制度冲突的解读须并列新旧对照；无法核实项单列「待复核清单」。
4. 回写报告与登记册后运行 `python engine/tools/md2html.py` 重新生成 HTML，并运行 `python engine/tools/lint_reports.py` 校验。

## 七、渲染与交付

- 交付格式：md + 同目录自包含 HTML；年度台账复盘报告含顶部九锚点导航（`.report-nav`），`.nav-url` = `{{REPO_RAW_URL_BASE}}` + `/reports/{本期文件名}`。
- HTML 须通过 `lint_reports.py` 标签配对校验。
- 基线报告常驻 `reports/` 顶层不归档；解读件按保留策略执行（年度复盘保留 5 期，超出移入 `reports/archives/`）。

## 八、质量自检（通用清单之外的本主题专属项）

- [ ] 全部引用回溯官方原文并附 URL；零媒体转述直引
- [ ] 政策台账增量 / 状态变更已回写；prompt 模板无硬编码活值
- [ ] 新旧制度对照完整；歧义条款多解并列
- [ ] 退職 / 退去強制、在留資格取消 / 変更、特定活動 / 技能実習、再入国許可 / みなし再入国未混用
- [ ] 与 08-visa-immigration / 07-economy-finance 最新报告 / 登记册交叉验证一致，未越界回写
- [ ] 建议章与事实分离；不构成法律意见 / 税务意见声明保留
- [ ] 追踪表 12+1 项均已核对并填写「是否更新」
- [ ] `{{REGISTRY_PATH}}` 已读已写，变更摘要与登记册一致
- [ ] 政策变更摘要 + 待复核清单已产出
- [ ] HTML 通过 lint（标签配对）

---

## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 依政策法规解读型事件触发 / 年度台账复盘模板实例化；承接退出·转型·回国执行层触发器与章节更新要点 |
