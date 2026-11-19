# 双轴评审：工程硬化（closure-d / N11–N14）

> **任务 slug**：closure-d-hardening
> **日期**：2026-11-19
> **评审对象**：`task/closure-d-93955b6d` 工作树（`.worktrees/closure-d`）
> **工单**：`n11-ruff-cleanup` · `n12-incremental-build-decision` · `n13-i11-platform-guard` · `n14-perf-trend`（组 D，工单源见 `docs/未完成项与对齐状态梳理-2026-11-19.md` 第五节；本分支不重复落工单）
> **评审人**：CatPaw（独立双轴）；收尾复核：2026-11-19（接手 Agent 独立实跑，见第五节）
> **验收口径**：退出码 `0=通过 / 1=阻断 / 2=放行`

---

## 一、Standards 轴（是否符合 TOOLCHAIN-DEV-SPEC / 仓库规范）

| 条款 | 结论 | 证据 |
|---|---|---|
| 适用边界（仅工具链代码） | ✅ | 变更落在 `engine/tools/`、`engine/scripts/`、`engine/tests/`、`.github/workflows/`、根配置（`ruff.toml` / `.gitattributes`）与 `docs/CI.md`；未触碰 `*/reports/`、`*/prompts/`、`*/data/` 内容层 |
| 命名规范 | ✅ | 新增工具 `engine/tools/perf_snapshot.py`（snake_case）；测试 `test_platform_guard.py` / `test_perf_snapshot.py`；评审 `docs/toolchain/reviews/closure-d-hardening-review.md`（kebab-case，无 `YYYY-MM-` 前缀） |
| TDD（先红后绿） | ✅ | `test_perf_snapshot.py` 先行编写并实测 `ModuleNotFoundError`（红），实现后 6 项全绿；`test_platform_guard.py` 9 项为守卫型断言，本地通过 |
| 退出码契约 | ✅ | `perf_snapshot.py` 成功 0 / 输出不可写 1；未引入新退出码语义 |
| 异常处理 | ✅ | `perf_snapshot` 快照加载失败回退空历史（不静默吞错，损坏文件重建）；写入经 `atomic_write` |
| 单一事实源 | ✅ | 未新增阈值；覆盖率阈值仍读 `coverage-config.json`；换行口径收敛到 `.gitattributes` |
| 不切生产默认 / 非破坏性 | ✅ | `incremental_build` 未接默认；`md2html` / `build_hub` / `build_index` 调用未改；ruff 修复均为行为等价重构 |
| 测试无回归 | ✅ | `unittest` 978 → 993 全绿（skipped=4）；`mypy` 0；`validate.py` 0；`generate_registry --check` 0；`cleanup --check` 0 |

**Standards 轴结论：无 P0 / P1。**

## 二、Spec 轴（是否实现工单验收标准）

| 工单 | 验收判据 | 结论 | 证据 |
|---|---|---|---|
| **N11** ruff 存量清零 | `ruff check engine` 0 或全量显式豁免；`unittest` 全绿 | ✅ | 138 → 0，**无显式忽略**（仅保留 `E501`）；`ruff.toml` 注释注明复核日期 2026-11-19；`unittest` 993 OK |
| **N12** 增量构建决策记录 | 文档含「触发条件 / 回滚判据 / 验证口径」；`incremental_build` 仍可用 | ✅ | `docs/CI.md` 第十四节含 14.2 触发条件（4 条）/ 14.3 回滚判据（4 条）/ 14.4 验证口径；结论「不切默认」；`incremental_build.py` 未改 |
| **N13** I-11 平台差异守卫 | 新增守卫测试本地通过；CI 可复现 | ✅ | `engine/tests/test_platform_guard.py` 9 项本地通过；覆盖路径分隔 / 换行 / 命令可用性；`.gitattributes` 固化 LF |
| **N14** 性能趋势机制 | 维护流程追加趋势快照；有基线 + 当前值 | ✅ | `perf_snapshot.py` 接入 `scheduled-maintenance.yml`；`engine/report-audits/toolchain/perf-trend.json` 含基线 + 首次快照（规模 + 耗时，退出码全 0） |

**Spec 轴结论：无 P0 / P1。**

## 三、证据（命令 + 输出摘要）

### 3.1 N11 ruff 存量清零

| 阶段 | 命令 | 结果 |
|---|---|---|
| 存量基线 | `python -m ruff check engine --statistics` | 138 项（SIM117 33 / UP017 20 / UP045 19 / I001 17 / E741 9 / SIM105 7 / SIM108 6 / B904 4 / 其余 23） |
| 自动修复 | `python -m ruff check engine --fix` | 修复 124 项（安全） |
| 复核后应用 unsafe | `python -m ruff check engine --fix --unsafe-fixes` | 再修 22 项（SIM105 / SIM108 / SIM102 / B905 等，逐条人工判断） |
| 人工等价修复 | 手工 | 剩余 24 项：E741 9 / SIM117 4 / B904 4 / E402 3 / E702 2 / SIM102 1 / UP031 1 |
| 终态 | `python -m ruff check engine` | **All checks passed!**（退出码 0） |

**等价性说明**：所有修复均为行为等价重构——
- `UP017`（`datetime.UTC`）、`UP045`（`X | None`）、`I001`（import 排序）、`UP009/UP015/UP032/UP035/UP037`：纯语法 / 风格；
- `SIM117/SIM108/SIM102/SIM105/SIM114`：控制流改写，语义不变；
- `B904`：`raise ... from None` 仅补异常链，不改变控制流；
- `B905`：`zip(..., strict=False)` 显式保持原行为（不改成 `strict=True`，避免长度不等时抛错）；
- `E741`：`l` → `ln` 重命名；`E702`：分号拆行；`E402`：补 `# noqa: E402`；`UP031`：`%` → f-string。

等价性验证：修复前基线 `unittest` 978 OK（skipped=4）；修复后 `unittest` 978 OK、`mypy` 0、`validate.py` 0；最终（含新增测试）`unittest` 993 OK、`mypy` 0、`validate.py` 0。

### 3.2 N13 平台差异守卫

- 差异识别：`git ls-files --eol` 显示工作流 blob 为 `i/lf`，但本机 `core.autocrlf=true` 检出为 `w/crlf` —— 即**仓库是 LF、Windows 工作树是 CRLF**。
- 处置：新增 `.gitattributes`（`* text=auto eol=lf`）固化 LF；守卫测试改校**仓库 blob**（`git show HEAD:<path>`）而非工作树，避免本地误报。
- 守卫测试：`python -m unittest engine.tests.test_platform_guard -q` → **Ran 9 tests, OK**。
- 覆盖：Windows 路径字面量 0 命中；工作流 python 调用全正斜杠；无 `shell=True`；无 PowerShell 专属语法；工作流工具路径全部存在；`atomic_write` 保留 LF。

### 3.3 N14 性能趋势机制

- 工具：`python engine/tools/perf_snapshot.py --with-tests` → 退出码 0，采集
  `validate 0.121s` / `build_hub_check 0.565s` / `build_index_check 0.139s` / `md2html 0.784s` / `unittest 55.727s`（均 0）。
- 规模：仓库 821 文件 / 12,427,672 bytes；报告 md 21 / html 21；工具 44；测试 993。
- 快照：`engine/report-audits/toolchain/perf-trend.json`（`schema=1`，`baseline` = 首次快照，`history` 1 条，保留上限 36）。
- 接线：`scheduled-maintenance.yml` 新增「性能趋势快照（perf_snapshot.py）」步骤；`engine/tools/README.md` 工具一览 + `registry.json`（工具 44）同步。

### 3.4 全量校验退出码

| 校验 | 命令 | 退出码 |
|---|---|---|
| ruff | `python -m ruff check engine` | **0** |
| mypy | `python -m mypy engine/tools engine/vocabulary/script` | **0**（48 文件） |
| unittest | `python -m unittest discover -s engine/tests -q` | **0**（Ran 993, OK, skipped=4） |
| validate | `python engine/tools/validate.py` | **0** |
| registry | `python engine/tools/generate_registry.py --check` | **0**（工具 44 · 类型 12 · 主题 21 · 工作流 8） |
| 工作区卫生 | `python engine/scripts/cleanup_workspace.py --check` | **0** |

## 四、遗留与后续

- **`findings-by-path.json` 缓存键变化**：`info_quality_check.py` 经 ruff 修复后源码字节变化，`audit_check` 的内容哈希键随之失效并重建（`2d416c…` → `c53cf8…`）。属预期失效，非行为回归；该文件定位为运行缓存（`engine/report-audits/README.md` 建议 `.gitignore`），后续可考虑纳入忽略。
- **ruff CI 仍为 warning（`continue-on-error`）**：存量已清零，但未收紧为阻断，避免本次任务夹带门禁语义变更；是否转阻断由后续决策。
- **N12 未切默认**：按工单要求交付决策记录，`incremental_build` 保持 POC；切默认需满足 14.2 四项触发条件。
- **性能基线方差**：`unittest` 耗时受机器负载影响（实测 49–191s），趋势对比须同环境；`perf_snapshot` 已记录每次 `timestamp` 供口径核对。
- **N13 守卫边界**：覆盖路径 / 换行 / 命令可用性三类不变量；未覆盖 shell 语义差异（如 bash `[[` 与 PowerShell 语法），因 CI 固定 bash、本地命令以 `python <正斜杠路径>` 为主，暂不扩面。
- **`engine/report-audits/README.md` 未登记 `toolchain/perf-trend.json`**：该 README「二、新增 / 删除规则」要求新增台账须登记，但 `toolchain/` 目录（存量 `coverage-baseline.json` + 本次新增 `perf-trend.json`）均未登记。建议由组 A / N1 文档对齐统一收口；本任务未改，避免与组 A 改动重叠。
- **`scheduled-maintenance.yml` 头部「维护内容」清单未含性能快照**：正文新增步骤 11，但头部 1–10 项清单未同步（文档漂移，不影响执行）。
- **ruff 忽略口径精确说明**：`ruff.toml` 除全局 `E501` 外，另有 `[lint.per-file-ignores] "engine/tests/*" = ["B"]`（存量口径，非本次为隐藏 138 项而加）。准确表述应为「无用于隐藏存量的显式忽略」。

---

## 五、收尾复核（2026-11-19，接手 Agent 独立实跑）

> 前一实施 Agent 被中断后，接手 Agent 在 `.worktrees/closure-d` 逐项实跑复核，结果与上文一致。

| 复核项 | 命令 | 结果 | 退出码 |
|---|---|---|---|
| 全量单测 | `python -m unittest discover -s engine/tests -q` | `Ran 993 tests` / `OK (skipped=4)` | 0 |
| ruff | `python -m ruff check engine` | All checks passed! | 0 |
| mypy | `python -m mypy engine/tools engine/vocabulary/script` | Success: no issues found in 48 source files | 0 |
| 规范校验 | `python engine/tools/validate.py` | 结构与规范校验通过 | 0 |
| 注册表 | `python engine/tools/generate_registry.py --check` | 工具 44 · 类型 12 · 主题 21 · 工作流 8 | 0 |
| 平台守卫 | `python -m unittest engine.tests.test_platform_guard -q` | Ran 9 tests, OK | 0 |
| 快照单测 | `python -m unittest engine.tests.test_perf_snapshot -q` | Ran 6 tests, OK | 0 |
| 快照工具 | `python engine/tools/perf_snapshot.py --porcelain --output <tmp>` | `baseline == current`；scale 9 字段齐；4 项耗时退出码全 0 | 0 |
| 工作区卫生 | `python engine/scripts/cleanup_workspace.py --check` | 工作区干净，无残留 | 0 |
| 换行事实源 | `git ls-files --eol` | 814 个 index blob 全为 `i/lf`（仅 `.nojekyll` 无换行），`.gitattributes` 不会触发大规模重规范化 | — |

- **等价性复核**：逐文件核对 `engine/tests` 与 `engine/tools` diff，全部为 `with A, B:` 合并、`l → ln`、`timezone.utc → UTC`、import 排序、`contextlib.suppress`、三元 / f-string 改写；**未发现删除或弱化断言**（`test_toolchain_dev_spec` 删除的是未使用的 `import re`）。
- **工作区卫生说明**：复核产生的 6 个 cache-dir（`.mypy_cache` / `.ruff_cache` / 三处 `__pycache__`）已用 `cleanup_workspace.py` 清理，`--check` 恢复 0。
- `git status` 未出现新的未跟踪残留；`perf_snapshot` 验证用 `--output <tmp>`，未改动已跟踪的 `perf-trend.json`。
