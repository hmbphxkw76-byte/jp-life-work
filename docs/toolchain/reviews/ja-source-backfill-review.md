# 中文页回溯日文原文 · 双轴评审（ja-source-backfill，2026-11-22）

> **范围**：`task/backfill-ja-sources-6b916f70` worktree（`D:\文档\GitHub\jp-life-work\.worktrees\backfill-ja-sources`）。
> **基线**：`origin/main = 6d4b7b3`。
> **触发**：P0-P2 核验残留 ②——7 条日本官方中文页（含新发现 2 条）回溯日文原文。
> **结论**：**Standards 无 P0/P1；Spec 项闭环**。中文页 7 → 1（余 1 条站点拦截无法核验）。

---

## 一、改动清单

| 类别 | 文件 | 改动 |
|---|---|---|
| 内容 | `01-ssw-driver/reports/2026-11-ssw-driver.md` | 来源 125/126/127 改指日文页；正文 L126/L390 改指日文页；来源 40（FRESC）/60（Prometric）改指日文页；分组 ⑥ 标题去除「中文页」字样 |
| 内容 | `08-visa-immigration/reports/2026-11-visa-immigration.md` | 来源 10 与正文 L19/L48/L64/L88/L101 的 SSW `/cn/` 链接改指日文页 |
| 内容 | `11-language-japanese/reports/2026-11-language-japanese.md` | 来源 9 与入口表 SSW `/cn/` 改指日文顶页 |
| 内容 | `18-family-parenting/reports/2026-11-family-parenting.md` | 来源 19 与正文 L98 改指日文页；「官方中文站表述」改「官方表述」 |
| 工具 | `engine/tools/source_normalize.py` | `detect_language` 扩展：`/zh-CHS/`、`xxx_cn.html` |
| 测试 | `engine/tests/test_source_check.py` | `test_detect_language` 增 2 条回归断言 |
| 派生 | `*/reports/*.html`、`source-index.json`、审计台账 / 状态 / 登记册 | 重新生成 / 重走审计 |

---

## 二、轴一：Standards（规范符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| 分支 / worktree / 串行合并 | ✅ | 全程 `.worktrees/backfill-ja-sources`；合并走 `workflow_guard.py merge` |
| 不编造 URL | ✅ | 6 条 SSW 与 FRESC / Prometric 日文页均经 `web_fetch` 实测存在（HTTP 200 内容匹配）；重庆领馆页站点拦截，未编造替代 |
| 来源语言政策 | ✅ | 替换后仅余 1 条中文页（重庆），`source_language_gate --changed` 通过 |
| TDD | ✅ | `detect_language` 扩展同步补回归断言 |
| 静态检查 | ✅ | `ruff` / `mypy` 通过 |
| 审计协议 | ✅ | 4 份改动报告重走 `md2html → auto_verify → 初审 → 复核（L5）→ 终审 → badge`，21/21 `audited` |

**Standards 结论：无 P0 / P1。**

---

## 三、轴二：Spec（残留 ② 验收）

| 验收标准 | 实现 | 证据 |
|---|---|---|
| 7 条中文页回溯日文原文 | 6 条 SSW + 新发现 2 条（FRESC / Prometric）改指日文页 | `source-index` `language=zh` 由 7 → **1** |
| 不编造 | 重庆领馆页 `itpr_ja` 返回 Not found / 站点拦截 | 保留原中文页 + 标注，标「未能核验」 |
| 检测无遗漏 | `detect_language` 覆盖 `/zh-CHS/`、`_cn.html` | 新断言通过；新发现 2 条被正确识别 |
| 报告重新审计 | 4 份报告重走全流程 | `audit_pipeline --status` 21/21；`--gate` 通过 |

**Spec 结论：残留 ② 闭环。**

---

## 四、残留

1. **重庆领馆中文页**（`itpr_zh`）：站点 Akamai 拦截 + `itpr_ja` 路径 Not found，日文原文未能核实，保留中文页并标注。
2. **新发现（未处理）**：`01` 报告来源 62 `jlpt.neea.cn`（中国教育考试网）为中文域名，不在 `source-policy.json` `blocked_domains` 内，故未被来源语言门禁拦截；属政策清单缺口，建议后续裁定（中国专属报名信息，可能需例外口径）。
3. 报告内对「ssw.go.jp 中文页 24,500 未同步」的文字表述为**口径观察**（非引用），保留。
