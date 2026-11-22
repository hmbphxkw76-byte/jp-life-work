# 工单：本地等价 CI 入口（local_ci.py）

> 任务 slug：`local-ci-entry`
> 规格：[local-ci-entry.md](../specs/local-ci-entry.md)
> 每条工单含验收判据；按序实施，TDD 先行。

## T-01 检查集与数据结构

- [ ] `engine/tools/local_ci.py` 定义 `Check`（id / name / ci / cmd / note）与 `CHECKS`（33 项，顺序固定）。
- [ ] 每项 `cmd` 引用的脚本路径存在；`id` 全局唯一。
- **验收**：`local_ci.CHECKS` 长度 33；`list` 子命令退出码 0。

## T-02 执行与退出码

- [ ] `run_check`：`subprocess.run` 执行，超时 / 无法启动 → `fail`。
- [ ] `status_for_exit`：0→pass / 2→warn / 其余→fail；`overall`：fail→1、warn→2、否则 0。
- [ ] 参数错误（未知 `--only/--skip` id）→ 退出码 2。
- **验收**：单测覆盖映射与汇总；`run --only no-such` 退出码 2。

## T-03 输出与确定性

- [ ] `run` 支持默认文本 / `--json` / `--markdown`；`--emit` 落盘。
- [ ] 结果 JSON 无时间戳 / 无耗时；同分支同工作区两次运行逐字节一致。
- **验收**：单测断言 `build_document` 两次相等；`run --json` 可被 `json.loads`。

## T-04 合成工作区命中阻断

- [ ] 用 tempfile 构造最小仓库结构并注入违规，验证对应检查 `fail`、`run` 退出码 1。
- **验收**：单测覆盖「违规 → fail」。

## T-05 登记与文档

- [ ] `engine/tools/README.md` 工具一览表补 `local_ci.py`；`generate_registry.py` 重生成 `registry.json`。
- [ ] `.gitignore` 增 `engine/report-audits/local-ci/`。
- **验收**：`generate_registry.py --check` 通过（工具 49 → 50）。

## T-06 测试

- [ ] `engine/tests/test_local_ci.py`：T-01～T-04 全覆盖。
- **验收**：`python -m unittest discover -s engine/tests` 全绿；`coverage_gate` 达标。
