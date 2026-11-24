# 双轴评审：写回换行全量治理（write-eol-all）

> 工单：[tickets/fix-all-write-eol-guard.md](../tickets/fix-all-write-eol-guard.md)
> 评审日期：2026-11-24
> 评审对象：`engine/{tools,scripts,vocabulary/script}` 下 24 个源文件（62 处写点）、
> `engine/tests/test_write_eol_guard.py`、`docs/CI.md`、`docs/README.md`、
> `docs/cross-domain-expert-roles.md`、`engine/tools/README.md`
> 规格：[specs/fix-all-write-eol-guard.md](../specs/fix-all-write-eol-guard.md)

## 一、Standards 轴（规约符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| 命名 / 退出码契约 | 不涉及 | 仅追加关键字参数，未改 CLI 与退出码 |
| 复用既有判定内核 | 通过 | 守卫用 `ast` 判定，未新造写回路径 |
| 只读约束 | 通过 | 守卫只读源码；修补脚本逐文件核对语法 |
| 生成物确定性 | 通过 | 产物内容不变，仅换行字节固定为 LF |
| 文档数字双向锁定 | 通过 | 测试计数 1208 → 1210 同步 4 处 |
| 测试先行 | 通过 | 守卫先红（实测列出 **62 处**）后绿 |

## 二、Spec 轴（规格 ↔ 实现映射）

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 三、AST 扫描 | `_targets()` 覆盖 `write_text` / `Path.open` / `os.fdopen` / 内建 `open`；`_writing_mode()` 识别 w/a/x/+ | 首跑命中 62 处，与 grep 清单一致 |
| 三、豁免表 | `EXEMPTIONS`（空）+ 豁免须写理由的断言 | `test_exemptions_are_documented` |
| 四、验收 3 | 见下方运行证据 | 实跑无假 dirty |

## 三、运行证据

```
$ python -m unittest engine.tests.test_write_eol_guard
Ran 2 tests ... OK

$ python -m compileall -q engine/tools engine/scripts engine/vocabulary/script
（无输出）

$ python -m ruff check engine
All checks passed!
$ python -m mypy engine
Success: no issues found in 63 source files
```

**修补过程诚实记录**：批量插入由 AST + tokenize 定位右括号完成；首轮因转义问题产生真实换行，
导致 24 个文件语法损坏——已从 HEAD 逐一还原并重做（改用 `chr(92)` 构造）；第二轮出现 **2 处**
逗号落点异常（`local_ci.py`、`migrate_monthly_reports.py`），均已人工修正。**未掩盖失败**。

## 四、残余风险 / 遗留

- **测试代码未纳入扫描范围**：`engine/tests/**` 的写点写入临时目录、不入库，不产生假 dirty；
  若日后测试改为写仓库内文件，需扩范围。已在规格写明。
- **非上述目录的写点**（如根级一次性脚本）不在扫描范围；当前仓库无此类目录。
- 无其他遗留。
