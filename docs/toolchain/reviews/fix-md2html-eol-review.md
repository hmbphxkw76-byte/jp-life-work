# 双轴评审：md2html 写回换行硬化（eol-lf）

> 工单：[tickets/fix-md2html-eol.md](../tickets/fix-md2html-eol.md)
> 评审日期：2026-11-23
> 评审对象：`engine/tools/md2html.py`、`engine/tests/test_write_lf.py`、
> `docs/CI.md`、`docs/README.md`、`docs/cross-domain-expert-roles.md`、`engine/tools/README.md`
> 规格：[specs/fix-md2html-eol.md](../specs/fix-md2html-eol.md)

## 一、Standards 轴

| 条款 | 结论 | 证据 |
|---|---|---|
| 跨平台换行（`.gitattributes eol=lf`） | 通过 | 唯一写点加 `newline="\n"` |
| 复用既有内核 | 通过 | 与 `hardening-write-lf` 同构，未新造机制 |
| 只读约束 | 通过 | 测试在仓库内 `.tmp_test_write_lf/` 建临时件并清理 |
| 文档数字锁定 | 通过 | 1188 → 1189 同步 4 处 |
| 测试先行 | 通过 | 新测试先红（实测产物含 CR）后绿 |

## 二、Spec 轴

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 三、唯一写点 LF | `out.write_text(html, encoding="utf-8", newline="\n")` | `test_md2html_emits_lf` |
| 四、验收 2 | 实跑 `md2html.py` 后仅内容变更文件出现 | 见下节 |

## 三、运行证据

```
$ python -m unittest engine.tests.test_write_lf
Ran 3 tests ... OK
```

## 四、残余风险 / 遗留

- **同类写点仍存**：`engine/vocabulary/script/vocab_tool.py` 等处仍有未经 `newline=` 的
  `write_text`，属潜在 CRLF 源；本次按规格范围未纳入，留待后续工单。
- **遗留**：无（本工单范围内）。
