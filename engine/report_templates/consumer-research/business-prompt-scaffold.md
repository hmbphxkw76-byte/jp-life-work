# 业务提示词脚手架（消费者·用户调研型）

> **用途**：为消费者·用户调研型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将 [prompts/](./prompts/) 下的泛用版提示词复制为 `{TOPIC_DIR}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{TOPIC_DIR}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-study.md`（专题调研 / 年度复测统一入口）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立调研设计档案与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 产品 / 营销 / 用户体验团队（TODO：按业务收窄） | 报告须声明受众 |
| 目标人群与抽样框 | 人群定义、抽样方式、配额、样本量下限（TODO） | 样本质量决定可信度 |
| 调研方法组合 | 问卷 / 深访 / 焦点小组 / 行为数据（TODO：按专题选择） | 一手数据为核心证据 |
| 细分维度与画像假设 | 细分维度、每类画像要素（TODO） | 假设须标验证状态 |
| 专题准入 | 年度专题清单与立项标准（TODO） | 项目制触发 |
| 来源优先级 | ① 一手调研（问卷/深访/实测） ② 行为数据 ③ 二手背景（TODO） | 二手仅作交叉验证 |
| 伦理与隐私 | 知情同意、脱敏规则、留存边界（TODO） | 不得采集可识别个人身份的敏感信息 |
| 追踪表 | 调研追踪项 × 方法（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 四、prompt-study.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-study.md](./prompts/prompt-study.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 六、落盘后审计（提交前必做，适用于本脚手架全部提示词）

落盘后依次运行 `python engine/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

> 复制到业务 `prompts/` 后，须在**每一份**业务提示词末尾保留本节（与类型模板同口径）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成消费者·用户调研型业务提示词脚手架 |
| v1.1 | 2026-11-17 | 正文指针化 | 提示词正文统一收口到 `prompts/` 泛用版母版，本脚手架只保留实例化步骤 / business-config 清单 / 审计协议，消除三处同步 |