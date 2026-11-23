# 规格：工具写回换行口径硬化（write-lf）

> 任务 slug：`hardening-write-lf`
> 版本：v1.0（2026-11-23）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)
> 上位依据：[AGENTS.md](../../../AGENTS.md)、[.gitattributes](../../../.gitattributes)

## 一、动机

2026-11-23 仓库对齐体检发现：运行 `validate.py` / 词库同步后，三个**跟踪文件**在 Windows
工作区变为 CRLF（内容零差异）：

- `engine/tools/registry.json`
- `engine/tools/README.md`
- `engine/vocabulary/data/sync-state.json`

后果：`git status` 长期假 dirty，且 `workflow_guard.py sync` 直接拒绝（「本地工作区有未提交
改动，无法快进对齐」）。根因：`Path.write_text()` / `open(..., "w")` 在 Windows 默认
`newline=None`，写入时把 `\n` 翻译为 `os.linesep`（CRLF），违反 `.gitattributes`
的 `* text=auto eol=lf` 单一换行口径。

## 二、目标与非目标

**目标**

1. 上述三个写回点在 Windows 下产出 **LF**，消除假 dirty 与 sync 阻塞。
2. 补守卫测试，把「写回产物不得含 CR」固化为可执行契约。
3. 顺手加固：把已在库的 2 份过程留痕纳入 `test_arch_guard.PROCESS_TRACE_DOCS`。

**非目标**

- 不修改仓库换行口径（仍为 LF），不引入第三方库。
- 不重构全部 `write_text` 写点（`vocab_tool.py` 等另行处理，见第五节残余风险）。
- 不处理内容侧警告（五问判定率、FC-015、词库序号等），那些需内容决策。

## 三、接口设计

| 位置 | 变更 |
|---|---|
| `engine/tools/generate_registry.py` `write()` | `REGISTRY_JSON.write_text(..., newline="\n")`；`README.write_text(..., newline="\n")` |
| `engine/vocabulary/script/sync_vocab.py` `dump_json()` | `tmp.write_text(..., newline="\n")` |
| `engine/tests/test_arch_guard.py` | `PROCESS_TRACE_DOCS` 增加 `优化方案与实施清单-2026-11-19.md`、`无法核实内容清理记录-2026-11-21.md` |
| `engine/tests/test_write_lf.py`（新增） | 断言两处写回产物字节级不含 `b"\r"` |

不新增工具、不改数据结构、不改字段、不改退出码契约。

## 四、验收标准

1. Windows 上执行 `generate_registry.py --write` 与 `sync_vocab.py sync` 后，三个目标文件
   **字节级不含 CR**。
2. 新增测试在修复前失败（红）、修复后通过（绿）。
3. `validate.py` / `unittest` / `ruff check` / `mypy engine` 全绿；测试数若有变化，
   同步 `docs/README.md` 版本行数字。

## 五、边界与约束

- 只改「写回换行参数」与「守卫元组」，不涉及数据与流程。
- **残余风险（登记备查）**：`engine/vocabulary/script/vocab_tool.py` 等处仍有未经
  `newline=` 的 `write_text`，同属潜在 CRLF 源；本次不纳入，留待后续工单。
- 工具链变更按 TOOLCHAIN-DEV-SPEC 走 S1→S6，本任务文件数 > 2，**不豁免**任何阶段。
