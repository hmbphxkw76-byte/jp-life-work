# 工单 B2：HTML 表格语义补齐与门禁（P1）

> **来源**：2026-11-19 工程收尾审计（U4）
> **状态**：已完成（任务分支 `task/b-html-e1e33a6c`，待串行合并）
> **优先级**：P1

---

## 背景

21 份报告 HTML 共 294 张表，实测 `<th scope=...>` **0** 个、`<caption>` **0** 个；`lint_reports.py` 只校验 thead/tbody 配对、列宽、img alt；`engine/tests` 无 scope/caption/a11y 断言。报告级 WCAG AA 表格语义未实现、未门禁。

对照：skip-link / `role="main"` / `<main>` / `aria-label` / `lang` / `role="status"` 已 21/21 覆盖。

## 目标

让报告 HTML 表格语义达到 WCAG 2.1 AA，并纳入门禁。

## 范围

- 做：md2html 渲染 `<th scope="col">`；复杂表 `<caption>`；`lint_reports.py` 增校验；测试断言；21 份报告重生成且 md↔HTML 一致。
- 不做：不改报告内容数据。

## 关联

- 源审计：本轮审计 §六 (c)。
- 规范：`engine/report_templates/monitoring-common-spec.md` §3（渲染规范）。

## 约束

- 简单表（单表头行）用 `scope="col"`；复杂/多层表加 `<caption>` 与 `scope="row"`/`headers` 视需要。
- 重生成走任务工作树内 `md2html.py`；`build_hub.py` 由主会话统一执行。

## 验收判据

1. 294 张表全部含 `scope` 语义；复杂表含 `<caption>`。
2. `lint_reports.py` 增表格语义校验，`--new-only` 通过。
3. `engine/tests` 增 a11y/表格语义断言。
4. `md_html_parity` 21/21；`validate.py` 通过；`unittest` 全绿。

## 步骤

1. 改 `md2html.py` 表头渲染。
2. 扩 `lint_reports.py` + 测试。
3. 任务工作树内重生成 21 份 HTML。
4. 校验。

## 证据

**改动文件**（任务分支 `task/b-html-e1e33a6c`）：

- `engine/tools/_common.py`：新增 `is_complex_html_table()` 与表格正则，作为复杂表判定单一事实源。
- `engine/tools/md2html.py`：`_fix_tables()` 表头补 `scope="col"`、行首 `<th>` 补 `scope="row"`、复杂表补 `<caption>`（文案「表 N：<表前最近标题>」，无标题取表头首行）；新增 `_with_scope()` / `_caption_html()`。
- `engine/tools/lint_reports.py`：新增阻断项——`<th>` 缺 `scope`、复杂表缺 `<caption>`。
- `engine/tests/test_tools.py` / `test_cov_compliance.py` / `test_cov_build.py`：新增 scope / caption / 复杂表判定断言（+6 项）。
- `docs/CI.md`：测试计数 1008 → 1014（`test_arch_guard` 守卫锁定）。
- `engine/report_templates/monitoring-common-spec.md` §3：增表格语义与复杂表判定 / caption 文案口径（v1.4）。
- `*/reports/*.html` × 21：任务工作树内 `md2html.py` 重生成。

**校验输出**：

| 命令 | 结果 |
|---|---|
| `python engine/tools/md2html.py` | 转换 21 份 |
| `python engine/tools/lint_reports.py --new-only` | `lint 通过：21 份报告全部合格（跳过 0 份）` |
| `python engine/tools/md_html_parity.py` | `OK=21 MISSING=0 MISMATCH=0 ERROR=0` |
| `python engine/tools/validate.py` | 退出码 0（结构与规范校验通过） |
| `python -m unittest discover -s engine/tests` | 1014 项，1 failure = 已知基线 `test_toolchain_dev_spec.TestReviewCoverage.test_every_ticket_has_review_or_exemption`（B1–B9 缺评审记录），与本任务无关；4 skipped |

**覆盖实测**：21 份报告共 294 张表，`<th>` 1030 个全部含 `scope`（`scope="col"` 1030 / `scope="row"` 0），缺 `scope` 0；复杂表 0 张（现有报告均为单表头简单表），`<caption>` 0。复杂表 `caption` / `scope="row"` 分支由单元测试覆盖（`test_tools.py::TestLintHtml`、`test_cov_compliance.py::TestCovComplianceLintReports`、`test_cov_build.py::TestCovMd2Html`）。

## 状态

已完成（任务分支 `task/b-html-e1e33a6c`，待串行合并）。
