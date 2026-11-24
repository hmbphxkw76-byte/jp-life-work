# 规格：md2html 写回换行口径硬化（eol-lf）

> 任务 slug：`fix-md2html-eol`
> 版本：v1.0（2026-11-23）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)
> 前序：同根因修复见 `hardening-write-lf`（generate_registry / sync_vocab）

## 一、动机

实测：任务工作树内跑一次 `md2html.py`，**21 份报告 HTML 全部变成 CRLF 假 dirty**
（`cleanup_workspace.py` 报「行尾规范化 21 项」后才恢复）。根因同 `hardening-write-lf`：
`Path.write_text(html, encoding="utf-8")` 在 Windows 默认 `newline=None`，`\n` 被写成 `\r\n`。

## 二、目标与非目标

**目标**：`md2html.py` 唯一写点产出 LF，消除「重新生成 HTML」造成的假 dirty。

**非目标**：不改 HTML 内容；不修其他写点（`vocab_tool.py` 等另行处理）。

## 三、接口设计

`engine/tools/md2html.py` 第 731 行：`out.write_text(html, encoding="utf-8", newline="\n")`。

测试：`engine/tests/test_write_lf.py` 新增 `test_md2html_emits_lf`（patch `collect_md_reports`
指向临时 md，断言产物不含 `b"\r"`）。

## 四、验收标准

1. 新测试先红后绿；
2. 实跑 `md2html.py` 后 `git status` 无 HTML 假 dirty（仅内容变更的文件出现）；
3. `validate.py` / `unittest` / `ruff` / `mypy` 全绿；测试数变化同步锁定文档。

## 五、边界与约束

只改一行 + 一项测试；工具链流程 S1→S6 不豁免（文件数 > 2）。
