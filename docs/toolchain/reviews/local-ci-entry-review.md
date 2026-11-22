# 双轴评审：本地等价 CI 入口（local_ci.py）

> 任务 slug：`local-ci-entry`
> 评审日期：2026-11-22
> 评审对象：`engine/tools/local_ci.py`、`engine/tests/test_local_ci.py`、`engine/tools/README.md`、`.github`（未改）
> 规格：[local-ci-entry.md](../specs/local-ci-entry.md)
> 工单：[local-ci-entry.md](../tickets/local-ci-entry.md)

## 一、Standards 轴（规约符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| 命名规范（工具 `engine/tools/<snake_case>.py`；测试 `test_<模块>.py`） | 通过 | `local_ci.py` / `test_local_ci.py` |
| 退出码契约 `0/1/2`；参数错误返回 2 | 通过 | `overall`：fail→1 / warn→2 / 否则 0；未知 id 捕获 `SystemExit` 后返回 2 |
| 异常不静默吞掉 | 通过 | `run_check` 显式处理 `TimeoutExpired` / `OSError`，映射为 `fail` 并保留原因 |
| 复用既有判定内核，不新写规则 | 通过 | 仅 `subprocess` 调用既有 33 个工具；无新增判定常量 |
| 生成物确定性 | 通过 | 结果 JSON 仅含 `schema_version`/`comment`/`branch`/`checks`/`summary`，无时间戳 / 耗时；单测断言两次构建相等 |
| 只读约束 | 通过 | 检查集不含 `--apply/--write/--submit/--sync/--rebind/--external` 等回写开关（单测 `test_no_write_flags` 守卫）；排除 `audit_check --all`、`auto_verify`、`cleanup --check` 并记录原因 |
| 测试先行 | 通过 | `test_local_ci.py` 先红（`ModuleNotFoundError`）后绿（21 项 OK） |
| 双轴评审 + 合并前检查单 | 通过 | 本报告；S6 见 `engine/scripts/README.md` |

## 二、Spec 轴（规格 ↔ 实现映射）

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 3.1 用法 `run` / `list` | `argparse` 子命令；`run` 支持 `--only/--skip/--json/--markdown/--emit/--with-tests/--with-coverage` | `list` 退出码 0；`run --only validate --json` 退出码 0 |
| 3.2 检查集 33 项 | `CHECKS` 33 项（validate 31 + audit-gate 2）；`EXTRA_CHECKS` 2 项可选 | 单测断言 `len(CHECKS)==33`、id 唯一、脚本存在 |
| 3.3 退出码与状态映射 | `status_for_exit` + `overall` | 单测覆盖 pass/warn/fail 与 0/1/2 汇总；`--only nope` 退出码 2 |
| 3.4 确定性 | `build_document` 无时间戳 | 单测两次构建相等；`--emit` 两次运行逐字节一致 |
| 四、验收 3 | 合成失败检查 → `run` 退出码 1 | 单测 `test_failing_check_exit_1` |
| 四、验收 4 | 真实仓库默认集 | `run` = 33 项，通过 23 / 警告 10 / **失败 0**，退出码 2 |
| 四、验收 5 | 登记与全量校验 | `generate_registry --check` 工具 50；unittest / ruff / mypy / validate / coverage / cleanup 全绿 |

## 三、运行证据

```
$ python engine/tools/local_ci.py run
本地等价 CI（本地优先 · 远程兜底）· 分支 task/local-ci-entry-b10d05f2
  ...
汇总：33 项，通过 23 / 警告 10 / 失败 0
退出码 2

$ python -m unittest engine.tests.test_local_ci
Ran 21 tests ... OK

$ python engine/tools/generate_registry.py --check
注册表一致：工具 50 · 类型 12 · 主题 21 · 工作流 8
```

## 四、结论

- **Standards**：无 P0/P1。
- **Spec**：规格三节（接口 / 检查集 / 退出码 / 确定性）与验收 1–5 全部落地。
- **说明**：10 项 `warn` 均为既有工具的正常契约（如 `decision_metrics --check` 的 P2 观察项、
  词库 ID 连续性建议、`source_check` / `counterexample` / `vocab_near` 写可再生报告后返回 2），
  非本工具引入，不阻断。
- **遗留**：无。
