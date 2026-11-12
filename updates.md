# 周期更新看板

> **自动生成**：由 `prompts/tools/update_scheduler.py` 生成，请勿手工编辑（手工改动会在下次调度时被覆盖）。
> **生成时间**：2026-11-12 14:58 JST　**排期配置**：[schedule.json](prompts/schedule.json)　**调度工作流**：[scheduled-update.yml](.github/workflows/scheduled-update.yml)

## 总览

- 主题总数：**13**　已到期：**0**　7 天内到期：**0**　正常：**13**
- 调度节奏：每周一 09:15 JST 自动巡检；各主题节奏见下表（由 schedule.json 驱动）。
- 到期后自动创建 GitHub Issue 工单（标签 `update-task`），由 AI IDE 或本人执行内容更新。

## 主题状态

| 主题 | 类型 | 节奏 | 上次更新 | 下次到期 | 状态 | 当前版本 | 入口 |
|---|---|---|---|---|---|---|---|
| 01-ssw-driver 特定技能司机·物流·智能驾驶监测 | 监测 | 30 天 | 2026-11-12（d9c530a） | 2026-12-12 | 正常 | v2026.11.12_5 | [报告](01-ssw-driver/reports/日本特定技能司机物流监测报告_v2026.11.12_5.md) · [HTML](01-ssw-driver/reports/日本特定技能司机物流监测报告_v2026.11.12_5.html) · [历史](01-ssw-driver/reports/archives/) · [提示词](01-ssw-driver/prompts/prompt-ssw-driver-logistics-update.md) |
| 02-career-driver 司机岗位执行手册 | 知识 | 90 天 | 2026-11-12（b2ee225） | 2027-02-10 | 正常 | v1.0 | [手册](02-career-driver/reports/日本司机职业知识手册.md) · [HTML](02-career-driver/reports/日本司机职业知识手册.html) · [历史](02-career-driver/reports/archives/) · [提示词](02-career-driver/prompts/prompt-career-driver-update.md) |
| 03-career-management 管理岗过渡手册 | 知识 | 90 天 | 2026-11-12（f9100d9） | 2027-02-10 | 正常 | v1.0 | [手册](03-career-management/reports/日本管理岗过渡知识手册.md) · [HTML](03-career-management/reports/日本管理岗过渡知识手册.html) · [历史](03-career-management/reports/archives/) · [提示词](03-career-management/prompts/prompt-career-logistics-update.md) |
| 04-industry-logistics 物流产业与赛道 | 知识 | 90 天 | 2026-11-12（f9100d9） | 2027-02-10 | 正常 | v1.0 | [手册](04-industry-logistics/reports/日本物流行业知识手册.md) · [HTML](04-industry-logistics/reports/日本物流行业知识手册.html) · [历史](04-industry-logistics/reports/archives/) · [提示词](04-industry-logistics/prompts/prompt-logistics-industry-update.md) |
| 05-industry-autonomous 自动驾驶与自动化 | 知识 | 90 天 | 2026-11-12（9054f92） | 2027-02-10 | 正常 | v1.0 | [手册](05-industry-autonomous/reports/日本自动驾驶与自动化知识手册.md) · [HTML](05-industry-autonomous/reports/日本自动驾驶与自动化知识手册.html) · [历史](05-industry-autonomous/reports/archives/) · [提示词](05-industry-autonomous/prompts/prompt-autonomous-automation-update.md) |
| 06-industry-technology 技术与数字化 | 知识 | 90 天 | 2026-11-12（f54b0de） | 2027-02-10 | 正常 | v1.0 | [手册](06-industry-technology/reports/日本技术与数字化知识手册.md) · [HTML](06-industry-technology/reports/日本技术与数字化知识手册.html) · [历史](06-industry-technology/reports/archives/) · [提示词](06-industry-technology/prompts/prompt-technology-industry-update.md) |
| 07-economy-finance 经济与财务 | 知识 | 90 天 | 2026-11-12（9054f92） | 2027-02-10 | 正常 | v1.0 | [手册](07-economy-finance/reports/日本经济与财务知识手册.md) · [HTML](07-economy-finance/reports/日本经济与财务知识手册.html) · [历史](07-economy-finance/reports/archives/) · [提示词](07-economy-finance/prompts/prompt-economy-update.md) |
| 08-visa-immigration 签证与在留资格 | 知识 | 90 天 | 2026-11-12（f4d5fd4） | 2027-02-10 | 正常 | v1.0 | [手册](08-visa-immigration/reports/日本签证与在留资格知识手册.md) · [HTML](08-visa-immigration/reports/日本签证与在留资格知识手册.html) · [历史](08-visa-immigration/reports/archives/) · [提示词](08-visa-immigration/prompts/prompt-visa-immigration-update.md) |
| 09-politics-law 政治与法规 | 知识 | 90 天 | 2026-11-12（42f90dd） | 2027-02-10 | 正常 | v1.0 | [手册](09-politics-law/reports/日本政治与法规知识手册.md) · [HTML](09-politics-law/reports/日本政治与法规知识手册.html) · [历史](09-politics-law/reports/archives/) · [提示词](09-politics-law/prompts/prompt-politics-law-update.md) |
| 10-education-qualification 资格与教育投资 | 知识 | 90 天 | 2026-11-12（f54b0de） | 2027-02-10 | 正常 | v1.1 | [手册](10-education-qualification/reports/日本资格与教育投资知识手册.md) · [HTML](10-education-qualification/reports/日本资格与教育投资知识手册.html) · [历史](10-education-qualification/reports/archives/) · [提示词](10-education-qualification/prompts/prompt-education-update.md) |
| 11-language-japanese 日语学习 | 知识 | 90 天 | 2026-11-12（9054f92） | 2027-02-10 | 正常 | v1.0 | [手册](11-language-japanese/reports/日本日语学习知识手册.md) · [HTML](11-language-japanese/reports/日本日语学习知识手册.html) · [历史](11-language-japanese/reports/archives/) · [提示词](11-language-japanese/prompts/prompt-language-update.md) |
| 12-culture-life 文化与生活 | 知识 | 90 天 | 2026-11-12（f54b0de） | 2027-02-10 | 正常 | v1.0 | [手册](12-culture-life/reports/日本文化与生活知识手册.md) · [HTML](12-culture-life/reports/日本文化与生活知识手册.html) · [历史](12-culture-life/reports/archives/) · [提示词](12-culture-life/prompts/prompt-culture-life-update.md) |
| 13-regional-info 地域信息 | 知识 | 90 天 | 2026-11-12（f54b0de） | 2027-02-10 | 正常 | v1.0 | [手册](13-regional-info/reports/日本地域信息知识手册.md) · [HTML](13-regional-info/reports/日本地域信息知识手册.html) · [历史](13-regional-info/reports/archives/) · [提示词](13-regional-info/prompts/prompt-regional-update.md) |

## 到期队列

当前无到期主题。

## 查阅与追溯

| 追溯对象 | 入口 | 说明 |
|---|---|---|
| 监测报告版本链 | [01-ssw-driver/reports](01-ssw-driver/reports/) · [archives](01-ssw-driver/reports/archives/) | 文件名含版本号，基线常驻顶层 |
| 知识手册历次版本 | 各主题 `reports/` 下的手册 → GitHub 文件 History | 单文档增量回写；变更摘要记入手册「更新日志」 |
| 更新工单 | [update-task](issues?q=is%3Aissue+label%3Aupdate-task) | 每个到期主题一个工单，关闭即完成 |
| 调度异常 | [ops-alert](issues?q=is%3Aissue+label%3Aops-alert) | 由失败的工作流自动创建 |
| 规范校验 | [validate.py](prompts/tools/validate.py) | 提交前与 CI 双重执行 |

## 使用说明

1. **定期查阅**：打开本页 → 看「到期队列」→ 进入对应提示词执行更新。
2. **手机查阅**：在 GitHub 仓库首页点 `updates.md` 即可阅读；HTML 版适合本地双击打开。
3. **回溯历史**：监测报告直接打开 `archives/`；知识手册用 GitHub History 对比任意两次提交。
4. **调整节奏**：编辑 `prompts/schedule.json` 中对应主题的 `cadence_days`，下次调度自动生效。
