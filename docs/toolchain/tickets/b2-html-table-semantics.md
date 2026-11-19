# 工单 B2：HTML 表格语义补齐与门禁（P1）

> **来源**：2026-11-19 工程收尾审计（U4）
> **状态**：待实施
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

- diff + 校验退出码（完成后回填）。

## 状态

待实施。
