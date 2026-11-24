# 规格：写回换行口径全量治理（write-eol-all）

> 任务 slug：`fix-all-write-eol-guard`
> 版本：v1.0（2026-11-24）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)
> 前序：`hardening-write-lf`（registry / sync-state）、`fix-md2html-eol`（报告 HTML）

## 一、动机

前两轮只修了 3 处写点；实测 `engine/` 下仍有 **62 处** `write_text()` / `open(...,"w")` 未受控换行，
构成同一根因的残余风险（Windows 下写 CRLF → 跟踪文件假 dirty → 阻塞 `sync`）。

## 二、目标与非目标

**目标**：① 为全部 62 处补 `newline="\n"`；② 新增 **AST 静态守卫**，把「工具源码不得出现未受控文本写回」
固化为契约，防止回潮。

**非目标**：不改测试代码（其写入对象是临时目录、不入库）；不改数据结构与字段；不动生成物内容。

## 三、接口设计

- 守卫：`engine/tests/test_write_eol_guard.py`
  - `scan(root)` 用 `ast` 找出 `Path.write_text(...)`、`Path.open("w"/"a"/"x"/...)`、
    `os.fdopen(fd, "w")`、`open(..., "w")` 中缺少 `newline=` 关键字者；
  - 扫描范围 `engine/tools` / `engine/scripts` / `engine/vocabulary/script`；
  - 文件级豁免表 `EXEMPTIONS`（须写理由），当前为空。
- 修复：仅追加 `newline="\n"` 关键字（不改其他逻辑）。

## 四、验收标准

1. 守卫先红（实测 62 处）后绿；
2. `ruff` / `mypy` / `unittest` 全绿；测试数变化同步锁定文档；
3. 实跑 `vocab_tool verify` / `validate.py` / `local_ci` 后 `git status` **无任何假 dirty**；
4. `cleanup --check` 退出码 0。

## 五、边界与约束

- 批量修补采用 AST + tokenize 定位调用右括号，逐文件核对语法（`compileall`）与静态检查；
- 出现两处插入落点异常（逗号位置）已人工修正，不掩盖。
