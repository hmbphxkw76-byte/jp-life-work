# 业务提示词脚手架（行业深度研究型）

> **用途**：为行业深度研究型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将 [prompts/](./prompts/) 下的泛用版提示词复制为 `{TOPIC_DIR}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{TOPIC_DIR}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-annual-refresh.md`（含重大事件插刷说明）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立研究边界档案与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 战略决策层 / 投资者 / 新进入者（TODO：按业务收窄） | 报告须声明受众 |
| 研究边界 | 行业边界定义（含 / 不含清单）、产业链分层口径（TODO） | 边界档案制度化 |
| 玩家清单 | 入选标准 + 分层清单（TODO） | 进出须留痕 |
| 规模口径清单 | 多口径并列清单（TODO：每口径附来源与假设） | 并列不合并 |
| 插刷触发器 | `事件 → 受影响模块`（TODO：重大并购 / 监管重构 / 技术代际切换） | 命中即提前刷新 |
| 来源优先级 | ① 统计局 / 行业协会 ② 上市公司财报 ③ 第三方研究机构 ④ 专家访谈（TODO：机构清单） | 多源交叉验证 |
| 追踪表 | 研究维度 × 优先来源（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 四、prompt-annual-refresh.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-annual-refresh.md](./prompts/prompt-annual-refresh.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 六、落盘后审计（提交前必做，适用于本脚手架全部提示词）

落盘后依次运行 `python engine/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

> 复制到业务 `prompts/` 后，须在**每一份**业务提示词末尾保留本节（与类型模板同口径）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成行业深度研究型业务提示词脚手架 |
| v1.1 | 2026-11-17 | 正文指针化 | 提示词正文统一收口到 `prompts/` 泛用版母版，本脚手架只保留实例化步骤 / business-config 清单 / 审计协议，消除三处同步 |