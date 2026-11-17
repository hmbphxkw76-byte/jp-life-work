# 业务提示词脚手架（舆情传播监测型）

> **用途**：为舆情传播监测型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将 [prompts/](./prompts/) 下的泛用版提示词复制为 `{TOPIC_DIR}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{TOPIC_DIR}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-monthly-monitor.md`；复制第五节 → `prompts/prompt-flash-warning.md`（可选，预警专项）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立舆情台账与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 品牌公关 / 政府事务 / IR（TODO：按业务收窄） | 报告须声明受众 |
| 渠道清单 | 监测渠道与覆盖声明（TODO：逐渠道） | 声量结构以渠道为维 |
| 议题与关键词 | 议题编号 + 关键词组（TODO） | 环比口径以关键词组固定为前提 |
| 预警触发器 | `信号命中 → 受影响模块`（TODO：声量阈值 / 情感阈值 / 突发负面） | 命中即升级 |
| 来源优先级 | ① 媒体数据库 ② 社交平台 ③ 公开抓取（附抓取时间）（TODO：渠道清单） | 舆情热度 ≠ 事实，须交叉验证 |
| 情感判定 | 工具 + 人工复核混合方法与抽样比例（TODO） | 误差边界须声明 |
| 追踪表 | 监测议题 × 优先渠道（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 四、prompt-monthly-monitor.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-monthly-monitor.md](./prompts/prompt-monthly-monitor.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 五、prompt-flash-warning.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-flash-warning.md](./prompts/prompt-flash-warning.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 六、落盘后审计（提交前必做，适用于本脚手架全部提示词）

落盘后依次运行 `python src/prompts-tools/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python src/prompts-tools/tools/audit_preflight.py --report <报告相对路径>`、`python src/prompts-tools/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python src/prompts-tools/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

> 复制到业务 `prompts/` 后，须在**每一份**业务提示词末尾保留本节（与类型模板同口径）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成舆情传播监测型业务提示词脚手架 |
| v1.1 | 2026-11-17 | 正文指针化 | 提示词正文统一收口到 `prompts/` 泛用版母版，本脚手架只保留实例化步骤 / business-config 清单 / 审计协议，消除三处同步 |