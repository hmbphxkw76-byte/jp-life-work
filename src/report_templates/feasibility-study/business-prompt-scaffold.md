# 业务提示词脚手架（可行性与市场进入型）

> **用途**：为可行性与市场进入型业务线批量实例化业务提示词的**复制模板**。执行[通用基座第 1.2 节](../prompt-generic-base.md)新增业务线步骤时，将 [prompts/](./prompts/) 下的泛用版提示词复制为 `{TOPIC_DIR}/prompts/` 下的对应文件，填入变量与业务实例化内容（标注 TODO 的项）后即可运行。脚手架内链接均按**复制后位置**书写，脚手架自身不是直接执行入口。

---

## 一、实例化步骤

1. 建目录：`{TOPIC_DIR}/` 下建 `prompts/`、`data/`、`reports/`。
2. 撰写 `business-config.md`：按第二节清单逐项实例化。
3. 复制第三节 → `prompts/prompt-baseline-setup.md`；复制第四节 → `prompts/prompt-project-study.md`（项目论证 + 项目复盘统一入口）。
4. 替换变量区、删除 TODO 指引、补齐业务链接与固化锚。
5. 首期运行基线提示词，建立评估框架档案与基线锚。

## 二、business-config.md 需实例化清单

| 节 | 内容 | 本类型要求 |
|---|---|---|
| 变量区 | {{REGION}}、{{TOPIC}}、{{REGISTRY_PATH}}、{{REGISTRY_FORMAT}}、{{BASELINE_REPORT_PATH}}、{{FRESHNESS_PRIORITY}}、{{SOURCE_LANGUAGE_RULE}}、{{REPO_RAW_URL_BASE}} | 固定值一次填写 |
| 受众定位 | 企业决策层 / 项目发起人（TODO：明确授权决策方） | 不构成对不特定公众的建议 |
| 评估维度与权重 | 市场 / 技术 / 财务 / 法规 / 运营各维度权重（TODO） | 框架档案制度化 |
| Go/No-Go 判定标准 | 阈值与打分规则（TODO） | 建议必须逐项对照打分 |
| 财务测算假设 | 投资额 / 成本 / 收入假设与依据（TODO） | 全假设可审计，三情景 |
| 可引用报告清单 | 本仓行业 / 规模 / 政策 / 竞争报告清单（TODO） | 引用注明来源报告与口径 |
| 复盘时点 | 项目实施后复盘窗口（TODO） | 假设回验必执行 |
| 来源优先级 | ① 本仓类型报告引用 ② 实地 / 当地访谈 ③ 二手行业数据 ④ 财务假设（TODO） | 缺口项标「本项目专项调研」 |
| 追踪表 | 评估维度 × 判定标准 × 结论（TODO） | 回写 {{REGISTRY_PATH}} |

---

## 三、prompt-baseline-setup.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-baseline-setup.md](./prompts/prompt-baseline-setup.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 四、prompt-project-study.md（指针 · 正文见 prompts/）
> **正文单一维护入口**：[prompts/prompt-project-study.md](./prompts/prompt-project-study.md)（泛用版母版）。
> 建新业务线时复制该文件至 `{TOPIC_DIR}/prompts/` 并填变量与 TODO；本文档不重复维护正文，避免三处同步漂移。

## 六、落盘后审计（提交前必做，适用于本脚手架全部提示词）

落盘后依次运行 `python src/prompts-tools/tools/auto_verify.py --report <报告相对路径>`（生成后自动验证 V1–V5，幂等写回「## 自动验证结果」并自动提交审计）、`python src/prompts-tools/tools/audit_preflight.py --report <报告相对路径>`、`python src/prompts-tools/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python src/prompts-tools/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。

> 复制到业务 `prompts/` 后，须在**每一份**业务提示词末尾保留本节（与类型模板同口径）。

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 依类型模板与业务提示词体例生成可行性与市场进入型业务提示词脚手架 |
| v1.1 | 2026-11-17 | 正文指针化 | 提示词正文统一收口到 `prompts/` 泛用版母版，本脚手架只保留实例化步骤 / business-config 清单 / 审计协议，消除三处同步 |