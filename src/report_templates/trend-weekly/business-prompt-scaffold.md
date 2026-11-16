# 业务提示词脚手架（行业趋势周报型）

> **用途**：复制式业务提示词脚手架。建新业务线时：复制本文档内两份提示词全文到 `{TOPIC_DIR}/prompts/` 对应文件，替换变量与 TODO 项，补齐 `business-config.md` 即可运行。类型方法论见[周期更新类型模板](./prompt-weekly-monitor-template.md)与[基线类型模板](./prompt-baseline-setup-template.md)。

---

## 一、实例化步骤

1. 按[通用基座 1.2 节](../prompt-generic-base.md)建立 `{TOPIC_DIR}/` 目录（prompts / data / reports，可选 sources/）。
2. 撰写 `prompts/business-config.md`（业务单一事实源）：变量区、受众定位、主题矩阵（3 块）、来源优先级实例化、触发器清单、交付格式声明。
3. 将下文两份提示词全文分别复制为：
   - `prompts/prompt-baseline-setup.md`（基线期，一次性）
   - `prompts/prompt-weekly-monitor.md`（周报运行期）
4. 替换全部变量与 TODO；周期提示词头部继承声明指向 `../../src/report_templates/trend-weekly/` 下对应类型模板。
5. 首期运行基线提示词建立机制文档与台账；业务线注册到 [template-registry.md](../template-registry.md) 第二节。

## 二、business-config 实例化清单

| 配置节 | 必填内容 |
|---|---|
| 变量区 | `{{REGION}}` / `{{TOPIC}}` / `{{BASELINE_REPORT_PATH}}` / `{{REGISTRY_PATH}}` / `{{REPO_RAW_URL_BASE}}` / `{{FRESHNESS_PRIORITY}}` / `{{SOURCE_LANGUAGE_RULE}}` |
| 受众定位 | 受众画像（如技术负责人 / 投资人）与视角；结论边界声明 |
| 主题矩阵 | 三大主题板块定义（对应周报 s2–s4），互不重叠 |
| 来源分级 | 四层来源的机构清单与采信规则实例化 |
| 触发器 | `事件 → 受影响板块` 清单（重大发布 / 监管动作 / 安全事故 / 融资并购等） |
| 交付格式 | md+HTML 双格式，或纯 HTML（md 源稿存 `sources/`，不参与 md2html 自动转换） |

---

## 三、基线提示词全文（复制为 prompt-baseline-setup.md）

```markdown
# {{REGION}} · {{TOPIC}} · 基线机制建立提示词（行业趋势周报型）

> **用途**：首期机制建立（一次性）：建立周报定位、主题矩阵、来源分级、台账与八节报告骨架。
> **继承声明**：本文件 = [通用基座](../../src/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../src/report_templates/monitoring-common-spec.md) × [基线类型模板（行业趋势周报型）](../../src/report_templates/trend-weekly/prompt-baseline-setup-template.md) × 业务专属配置（`./business-config.md`）。

## 运行变量（必填）

{{CURRENT_DATE}} = 本次执行日期
{{CADENCE}} = 固定填「周」（基线不区分节拍）
{{OUTPUT_PATH}} = reports/{{YYYY-MM}}-<slug>.md
{{REPORT_VERSION}} = 固定 v1.0（灾难恢复重建时递增）

## 执行步骤

1. 完成监测范围与主题矩阵调研（TODO：三块板块定义，覆盖受众决策需求、互不重叠）。
2. 完成来源清单与发布节奏调研（TODO：逐机构官方 URL / 频率 / 语言）。
3. 首建台账 {{REGISTRY_PATH}}（数据看板追踪表 / 已修正事实清单 / 来源清单 / 触发器清单 / 版本记录）。
4. 按基线类型模板第二节撰写九节机制文档（顺序标题逐字固化），落盘 {{OUTPUT_PATH}}。

## 结果验证

- python src/prompts-tools/tools/validate.py（0 错误）
- python src/prompts-tools/tools/lint_reports.py（0 错误）
- python src/prompts-tools/tools/build_index.py && python src/prompts-tools/tools/build_hub.py
```

---

## 四、周报提示词全文（复制为 prompt-weekly-monitor.md）

```markdown
# {{REGION}} · {{TOPIC}} · 周报提示词（行业趋势周报型）

> **用途**：周期性（每周）刷新主题板块与数据看板，产出八节周报；触发器命中时对应板块重点更新。
> **继承声明**：本文件 = [通用基座](../../src/report_templates/prompt-generic-base.md) × [监测报告通用规范](../../src/report_templates/monitoring-common-spec.md) × [周期更新类型模板（行业趋势周报型）](../../src/report_templates/trend-weekly/prompt-weekly-monitor-template.md) × 业务专属配置（`./business-config.md`）。

## 运行变量（每次运行前填写）

{{CURRENT_DATE}} = 本次执行日期
{{DATA_CUTOFF}} = 数据截止日（周报命名与标题锚定此日期）
{{PREVIOUS_REPORT_PATH}} = 最近一期周报路径
{{BASELINE_REPORT_PATH}} = 固定值，见 business-config.md
{{REGISTRY_PATH}} = 固定值，见 business-config.md
{{OUTPUT_PATH}} = reports/{{DATA_CUTOFF}}_weekly.md
{{REPORT_VERSION}} = 本次版本号，格式 vYYYY.MM.DD

## 任务目标

以公开来源为依据、以上期周报为对比锚，完成「采集 → 核验 → 看板刷新 → 可执行启示」闭环；八节结构与基线逐字一致；继承已修正事实清单；无实质变化时降级为核验轻运行，不得虚构变化；T+1 在报告头部标注。

## 八节固定结构（不得增删节、调整顺序）

1. 本周要点 Top5（每条 = 结论 + 关键数字 + 来源；【事实】/【预测】显式标注）
2. 主题板块一（TODO：按 business-config 主题矩阵实例化）
3. 主题板块二（TODO）
4. 主题板块三（TODO）
5. 数据看板（指标 × 上期值 × 本期值 × 变化 × 来源 × 口径，与台账联动）
6. 风险与不确定性（来源可靠性 / 反向证据 / 口径冲突 / 基准自报）
7. 可执行启示（面向受众，标「推断」，只给条件 → 判读 → 框架性含义 → 风险提示）
8. 参考来源（逐条 URL；转述标「需核实原文」）

## 执行步骤

1. 读 {{PREVIOUS_REPORT_PATH}} 与基线，继承已修正事实清单（防回退）。
2. 按来源分级采集本周新事实（TODO：按 business-config 来源清单与渠道分工）。
3. 逐块更新主题板块；数据看板逐行核对并回写台账（逐项填「是否更新」）。
4. 撰写八节周报，落盘 {{OUTPUT_PATH}}。

## 结果验证

- python src/prompts-tools/tools/lint_reports.py && python src/prompts-tools/tools/classify_reports.py
- python src/prompts-tools/tools/compliance_check.py --file {{OUTPUT_PATH}}
- python src/prompts-tools/tools/build_index.py && python src/prompts-tools/tools/build_hub.py
```

---

## 五、落盘后审计（提交前必做，适用于本脚手架全部提示词）

落盘后依次运行 `python src/prompts-tools/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python src/prompts-tools/tools/audit_preflight.py --report <报告相对路径>`、`python src/prompts-tools/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python src/prompts-tools/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

> 复制到业务 `prompts/` 后，须在**每一份**业务提示词末尾保留本节（与类型模板同口径）。

---

## 六、变更记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 行业趋势周报型复制式业务提示词脚手架（基线 + 周报） |
