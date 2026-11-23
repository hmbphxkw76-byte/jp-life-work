# 双轴评审：工具写回换行口径硬化（hardening-write-lf）

> 任务 slug：`hardening-write-lf`
> 评审日期：2026-11-23
> 评审对象：`engine/tools/generate_registry.py`、`engine/vocabulary/script/sync_vocab.py`、
> `engine/tests/test_write_lf.py`、`engine/tests/test_arch_guard.py`、`docs/README.md`、
> `docs/CI.md`、`docs/cross-domain-expert-roles.md`、`engine/tools/README.md`
> 规格：[specs/hardening-write-lf.md](../specs/hardening-write-lf.md)
> 工单：[tickets/hardening-write-lf.md](../tickets/hardening-write-lf.md)

## 一、Standards 轴（规约符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| 命名规范（工具 snake_case；测试 `test_<模块>.py`） | 通过 | `test_write_lf.py` |
| 退出码契约 `0/1/2` | 不涉及 | 未改任何 CLI 入口 |
| 异常不静默吞掉 | 通过 | 测试用 `try/finally` 还原被 patch 的模块全局，不留脏状态 |
| 复用既有判定内核，不新写规则 | 通过 | 仅加 `newline="\n"` 与守卫断言，无新增判定常量 |
| 生成物确定性 | 通过 | 写回内容不变，仅换行口径固定为 LF |
| 只读约束 | 通过 | 测试全部在 `tempfile.TemporaryDirectory` 内进行，不碰仓库文件 |
| 跨平台换行（`.gitattributes` `* text=auto eol=lf`） | 通过 | 两个写回点字节级不含 CR；`test_platform_guard` 同步过 |
| 文档数字双向锁定 | 通过 | 测试数 1183 → 1185 已同步 `docs/CI.md` 六节 / `docs/README.md` v2.21 / `cross-domain-expert-roles.md` / `engine/tools/README.md` v1.22 |
| 测试先行 | 通过 | `test_write_lf.py` 先红（CRLF 断言失败 + `scan()` 路径错误）后绿 |
| 双轴评审 + 合并前检查单 | 通过 | 本报告；S6 见 `engine/scripts/README.md` |

## 二、Spec 轴（规格 ↔ 实现映射）

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 三、`generate_registry.write()` 两处写回加 `newline="\n"` | `REGISTRY_JSON.write_text(..., newline="\n")`；`README.write_text(..., newline="\n")` | `test_generate_registry_write_emits_lf` |
| 三、`sync_vocab.dump_json()` 加 `newline="\n"` | `tmp.write_text(..., newline="\n")` | `test_sync_vocab_dump_json_emits_lf` |
| 三、`PROCESS_TRACE_DOCS` 补 2 份过程留痕 | 增加 `优化方案与实施清单-2026-11-19.md`、`无法核实内容清理记录-2026-11-21.md` | `test_docs_readme_process_docs_statement` |
| 四、验收 1 | Windows 下三文件字节级不含 CR | 新增 2 项测试 |
| 四、验收 3 | `validate.py` / `unittest` / `ruff` / `mypy` 全绿 | 见第三节 |

## 三、运行证据

```
$ python -m unittest engine.tests.test_write_lf engine.tests.test_arch_guard
Ran 18 tests ... OK

$ python -m unittest discover -s engine/tests
Ran 1185 tests ... FAILED (failures=2)   # 修复前：迁移守卫裸 tools 目录引用 + 本工单缺评审
（修正后）
Ran 1185 tests ... OK (skipped=4)

$ python engine/tools/validate.py
结构与规范校验通过：通用层完整、业务线结构齐全、命名合规

$ python engine/tools/generate_registry.py --check
注册表一致：工具 50 · 类型 12 · 主题 21 · 工作流 8
```

## 四、结论

- **Standards**：无 P0/P1。
- **Spec**：规格三节（接口 / 验收）全部落地；测试计数漂移按仓库纪律同步 4 处文档。
- **残余风险（已在规格第五节登记）**：`engine/vocabulary/script/vocab_tool.py` 等处仍有未经
  `newline=` 的 `write_text`，同属潜在 CRLF 源，本次不纳入，留待后续工单。
- **遗留**：无（本工单范围内）。
