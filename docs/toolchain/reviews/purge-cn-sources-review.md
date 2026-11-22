# 中文来源严格清零 · 双轴评审（purge-cn-sources，2026-11-22）

> **范围**：`task/purge-cn-sources-6b916f70` worktree（`D:\文档\GitHub\jp-life-work\.worktrees\purge-cn-sources`）。
> **基线**：`origin/main = 173487a`。
> **触发**：核验残留「`neea.cn` 政策清单缺口」；经用户裁定按现政策**严格清零**。
> **结论**：**Standards 无 P0/P1；Spec 闭环**。全量报告来源语言门禁 0 违规；`source_check` 中文页 7 → 1。

---

## 一、改动清单

| 类别 | 文件 | 改动 |
|---|---|---|
| 政策 | `engine/config/source-policy.json` | `blocked_domains` 增 `neea.cn`（`edu.cn` 原已覆盖 `neea.edu.cn`） |
| 报告 | `01-ssw-driver/reports/2026-11-ssw-driver.md` | 移除 NEEA 来源 62 与 JLPT 中国专属条目；费用速算去「JLPT 450 元」；「信息差与未核验清单」增缺口行；`prometric /zh-CHS/` → `/ja/` |
| 报告 | `11-language-japanese/reports/2026-11-language-japanese.md` | 来源规则去 `jlpt.neea.edu.cn` |
| 提示词 | `11-language-japanese/prompts/business-config.md` | 来源优先级与监测表去 NEEA |
| 登记册 | `11-…/data/language_indicator_registry.md`、`08-…/data/visa_immigration_indicator_registry.md` | 去 NEEA / 中文页链接 |
| 手册 | `01`（00-navigation / 00a-reference-sources / 01-visa-system / 05-employment-landing）、`08`（00-navigation / 01-ssw-overview / 02-ssw1-driver / 03-exams-japanese / 04-application / 05-ssw2-upgrade / 07-permanent-residence / 08-family / 09-policy-log）、`11`（01-learning-roadmap / 05-resources） | `ssw.go.jp/cn/*` → 日文页；`prometric /zh-CHS/` → `/ja/`；`fresc_cn.html` → `fresc.html`；去 NEEA 引用 |
| 派生 | `*/reports/*.html`、`source-index.json`、审计台账 / 状态 / 登记册 | 重新生成 / 重走审计 |

---

## 二、轴一：Standards（规范符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| 分支 / worktree / 串行合并 | ✅ | 全程 `.worktrees/purge-cn-sources`；合并走 `workflow_guard.py merge` |
| 不编造 URL | ✅ | 替换目标（ssw 日文页 / `/ja/ssw/` / `fresc.html`）均经 `web_fetch` 实测；NEEA 无替代即移除，不编造 |
| 来源语言政策 | ✅ | `source_language_gate`（提示词层 + `--all` 报告层）**0 违规** |
| 单一事实源 | ✅ | 域名清单收敛于 `source-policy.json` |
| 静态检查 | ✅ | `ruff` / `mypy` 通过 |
| 审计协议 | ✅ | 01 / 11 重走 `md2html → auto_verify → 初审 → 复核（L5）→ 终审 → badge`，21/21 `audited` |

**Standards 结论：无 P0 / P1。**

---

## 三、轴二：Spec（严格清零验收）

| 验收标准 | 实现 | 证据 |
|---|---|---|
| 清单缺口闭环 | `neea.cn` 入黑名单 | `source-policy.json` |
| 报告层清零 | 全量 21 份报告无黑名单域名 | `source_language_gate --all` 0 违规 |
| NEEA 引用清除 | 报告 / 手册 / 提示词 / 登记册全清 | `grep neea` 仅剩历史审计记录与「停用」说明 |
| 仅中文来源事实处置 | JLPT 中国日程 / 费用转「信息差与未核验清单」 | 01 报告缺口行；08 手册标「未纳入」 |
| 中文页数下降 | `source_check` 中文页 7 → 1 | 余 1 为重庆领馆页（站点拦截，见残留） |

**Spec 结论：严格清零闭环。**

---

## 四、残留

1. **重庆领馆中文页**（`itpr_zh`）：站点拦截，日文原文未能核实，保留并标注（沿用前任务结论）。
2. **历史审计记录**：`engine/report-audits/toolchain/l5-independence-review-2026-11-20.md` 仍列 `neea.cn` 为来源域——历史快照，不改写。
3. `01` 手册 `00a-reference-sources` 保留「原 neea.cn 中文页按来源规则停用」说明（停用记录，非引用）。
