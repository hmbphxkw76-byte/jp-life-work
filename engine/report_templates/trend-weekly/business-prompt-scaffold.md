# 业务提示词脚手架（行业趋势周报型）

> **用途**：复制式业务提示词脚手架。建新业务线时：将 [prompts/](./prompts/) 下的泛用版提示词复制到 `{TOPIC_DIR}/prompts/` 对应文件，替换变量与 TODO 项，补齐 `business-config.md` 即可运行。类型方法论见[周期更新类型模板](./prompt-weekly-monitor-template.md)与[基线类型模板](./prompt-baseline-setup-template.md)。

---

## 一、实例化步骤

1. 按[通用基座 1.2 节](../prompt-generic-base.md)建立 `{TOPIC_DIR}/` 目录（prompts / data / reports，可选 sources/）。
2. 撰写 `prompts/business-config.md`（业务单一事实源）：变量区、受众定位、主题矩阵（3 块）、来源优先级实例化、触发器清单、交付格式声明。
3. 将 [prompts/](./prompts/) 下的两份泛用版提示词分别复制为：
   - `prompts/prompt-baseline-setup.md`（基线期，一次性）
   - `prompts/prompt-weekly-monitor.md`（周报运行期）
4. 替换全部变量与 TODO；周期提示词头部继承声明指向 `../../engine/report_templates/trend-weekly/` 下对应类型模板。
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

## 三、prompt-baseline-setup.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 四、prompt-weekly-monitor.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-weekly-monitor.md](./prompts/prompt-weekly-monitor.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 五、落盘后审计（提交前必做，适用于本脚手架全部提示词）

落盘后依次运行 `python engine/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

> 复制到业务 `prompts/` 后，须在**每一份**业务提示词末尾保留本节（与类型模板同口径）。

---

## 六、变更记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 行业趋势周报型复制式业务提示词脚手架（基线 + 周报） |
| v1.1 | 2026-11-17 | 正文指针化 | 提示词正文统一收口到 `prompts/` 泛用版母版，本脚手架只保留实例化步骤 / business-config 清单 / 审计协议，消除三处同步 |