# W2 CI/CD 加固 · 双轴评审（Standards / Spec）

> **工单**：优化方案 W2（`docs/优化方案与实施清单-2026-11-19.md` §C1 / 阶段 2，项 2.1–2.8）
> **分支**：`task/w2-ci-cd-052aad0f`（提交 `f02ddec`）
> **评审日期**：2026-11-19
> **评审口径**：Standards（仓库规范符合性）+ Spec（方案要求覆盖度）

## 一、Standards 轴（规范符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 单一事实源 | 通过 | 覆盖率阈值仍只在 `engine/tools/coverage-config.json`；cron 只定义在 workflow；退出码约定仍指向 `docs/CI.md`；未新增复述 |
| 退出码约定 | 通过 | `coverage_gate.evaluate` 保持 0/1/2；新增单工具阈值不改变语义；workflow 判定显式允许 {0,2} |
| 生成物只由生成器产出 | 通过 | 未手改 `index.html` / `search-index.json`；`build_hub --check` 退出码 0 |
| 跨平台 | 通过 | 工作流无 PowerShell 专属语法；`test_platform_guard` 9 项通过；blob LF |
| worktree 隔离 | 通过 | 全程在 `.worktrees/w2-ci-cd/` 工作；未直推 main；提交仅含本任务路径（23 文件） |
| 工具登记 | 通过 | 未新增工具；`generate_registry --check` 通过（工具 45 / 类型 12 / 主题 21 / 工作流 8） |
| 测试同步 | 通过 | 新增 5 项（`test_coverage_gate` 单工具阈值）；全量 1045 项全绿 |
| 文档↔数字同步 | 通过 | `test_arch_guard` 全绿；CI.md / 总规范 / README / tools README / expert-roles 已同步 |
| 静态检查 | 通过 | `ruff check engine` 0；`mypy engine/tools engine/vocabulary/script engine/scripts` 0 |

## 二、Spec 轴（方案覆盖度）

| 项 | 要求 | 实现 | 结论 |
|---|---|---|---|
| 2.1 | `requirements-dev.txt` 固定 + lock | 固定 `ruff==0.17.5` / `mypy==2.4.1`；新增 `requirements-dev.lock`（含传递依赖） | 覆盖 |
| 2.2 | cache + timeout | 8 条工作流均加 `actions/cache@v4`（pip，key 随 requirements 哈希）；validate 主 job 30 / html-sync 15，其余原有 timeout 保留 | 覆盖 |
| 2.3 | 定时任务改分支 + PR | 5 条定时工作流提交步骤改为推 `auto/*` 分支 + `gh pr create`（`[automated]` 标记，保留 bot 身份）；`html-sync` 为 push 触发不在范围 | 覆盖 |
| 2.4 | schedule 错峰 ≥30 分钟 | 00:15 / 00:45 / 01:15 / 01:45（info-quality 每周一 02:20 与月度不冲突）；同步 `test_tools` 与总规范 | 覆盖 |
| 2.5 | pre-commit 增 ruff --fix + validate | `engine/scripts/git-hooks/pre-commit` 增加暂存 py 的 `ruff check --fix` + `validate.py`（退出码 1 阻断、2 放行；ruff 缺失告警不阻断） | 覆盖 |
| 2.6 | mypy 覆盖 engine/scripts；ruff 阻断 | validate.yml：mypy 扩展至三目录；ruff 删除 `continue-on-error`；先修复既有 3 处 mypy 错误 | 覆盖 |
| 2.7 | run_tests_parallel 接入分片 | validate.yml 新增 `tests` job，matrix 4 分片 `--shard i/4`，`fail-fast: false` | 覆盖 |
| 2.8 | 覆盖率单工具阈值 + upload-artifact | `coverage-config.json` 增 `per_tool_min: 60`；`coverage_gate` 双重判定 + 基线/输出；coverage job 上传 `coverage-gate.json` | 覆盖 |

## 三、风险与遗留

1. **PR 合并节拍**：定时任务不再直推 main 后，自动生成物需人工评审合并；若 PR 积压，`automation_status` 心跳仍能反映断档（手动 / 按需入口）。
2. **pre-commit 本地生效**：新钩子需 `python engine/scripts/workflow_guard.py hooks` 重装才在本地生效；未重装时仅旧的分支守卫生效。
3. **单工具阈值口径**：`per_tool_min=60` 为当前最低工具（`link_check.py` 65.4%）留有余量；后续若新增低覆盖工具，需先补测试再合入。
4. **分片成本**：契约测试 4 分片会成倍安装依赖；已用 pip 缓存缓解，跨月可通过 `perf-trend.json` 观察耗时。

## 四、结论

Standards 与 Spec 两轴均通过，无 P0/P1；可进入合并流程。
