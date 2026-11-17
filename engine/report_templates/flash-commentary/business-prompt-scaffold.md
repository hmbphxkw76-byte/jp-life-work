# 业务提示词脚手架（快评·事件点评型）

> **用途**：为快评·事件点评型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将 [prompts/](./prompts/) 下的泛用版提示词复制为 `{TOPIC_DIR}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{TOPIC_DIR}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`（**基线期只建机制，不出快评正文**）；复制第四节 → `prompts/prompt-flash-note.md`（快评正文统一入口）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立事件日历与预期台账。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 需要快速反应的决策者 / 投资者（TODO：按业务收窄） | 报告须声明受众 |
| 事件监测日历 | 定期事件（数据发布 / 会议 / 财报窗口：名称 / 频次 / 窗口 / 官方渠道 URL）+ 不定期事件类型（TODO） | 逐渠道附 URL |
| 预期台账 | 事件类型 → 共识预期 / 官方目标值 → 依据来源 → 更新时效（TODO） | 无可靠预期登记「无预期」，不虚构共识值 |
| 时效标准 | 72h 上限内目标时效（TODO） | 宁可延迟，不可转述直引 |
| 升级规则 | 偏离阈值 → 快评升级为深度报告 / 期报联动（TODO） | 快评只登记偏离信号 |
| 篇幅上限 | 快评正文上限（TODO：一般 1–3 页） | 四段式固定结构 |
| 来源优先级 | ① 官方发布稿 / 财报原文（唯一即时采信） ② 预期台账 ③ 媒体转述禁单源直引（TODO） | 事后补验流程须登记 |
| 追踪表 | 事件类型 × 预期来源 × 更新时效（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 四、prompt-flash-note.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-flash-note.md](./prompts/prompt-flash-note.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 六、落盘后审计（提交前必做，适用于本脚手架全部提示词）

落盘后依次运行 `python engine/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

> 复制到业务 `prompts/` 后，须在**每一份**业务提示词末尾保留本节（与类型模板同口径）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成快评·事件点评型业务提示词脚手架 |
| v1.1 | 2026-11-17 | 正文指针化 | 提示词正文统一收口到 `prompts/` 泛用版母版，本脚手架只保留实例化步骤 / business-config 清单 / 审计协议，消除三处同步 |