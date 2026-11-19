# 双轴评审：工程硬化收口（harden-engine / T3 + T8）

> **任务 slug**：harden-engine
> **分支**：`task/harden-engine-9a56c316`（worktree `.worktrees/harden-engine`，基线 origin/main @`f04d5c8`）
> **日期**：2026-11-19
> **评审人**：CatPaw（双轴自评）
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**，可进入 S6 合并前检查单。

## 一、范围与改动清单

| # | 文件 | 性质 | 对应 |
|---|---|---|---|
| 1 | `docs/toolchain/specs/align-2026-11-19.md` | 规格（新增） | T8-a / S1 |
| 2 | `engine/tests/test_toolchain_dev_spec.py` | 测试 | T8-b 新增 `TestReviewCoverage`（2 项） |
| 3 | `docs/toolchain/reviews/coverage-gate-review.md` | 评审（补档） | T8-b 补 T9 缺口 |
| 4 | `docs/toolchain/reviews/closure-b-content-review.md` | 评审留痕 | 补组 B 六个工单 slug 声明行 |
| 5 | `docs/CI.md` | 文档 | 测试计数 998 → 1000 + v2.20 |
| 6 | `docs/toolchain/reviews/harden-engine-review.md` | 评审（本文件） | S5 |

**未改动**：`engine/tools/review_gate.py`、`.github/workflows/audit-gate.yml`、`*/reports/*.md`、共享检出目录与其他 worktree。

## 二、Standards 轴（规约符合性）

| 规约条款 | 落实 | 位置 |
|---|---|---|
| 适用边界（仅工具链 / 文档） | ✅ | 改动落在 `docs/toolchain/`、`engine/tests/`、`docs/CI.md`；未触碰 `*/reports/`、`*/prompts/`、`*/data/` |
| 命名规范 | ✅ | 规格 / 评审用 kebab-case，无 `YYYY-MM-` 前缀；未被 `classify_reports.py` 误判 |
| S1 规格先行 | ✅ | 规格含动机 / 接口 / 验收三要素；≤2 文件且无新增工具，按阈值免 S2 工单化（S5/S6 不豁免） |
| TDD（先红后绿） | ✅ | 守卫红态：移除 `coverage-gate-review.md` 后 `TestReviewCoverage` 失败，`missing=['coverage-gate']`（rc=1）；补档后绿（rc=0），见 E5 |
| 退出码契约 | ✅ | 未新增工具 / 退出码；`unittest` / `validate` 均 0 |
| 单一事实源 | ✅ | 未新增阈值；测试计数唯一事实源 `docs/CI.md` 已同步 |
| 测试入 `engine/tests/` | ✅ | 新增 2 项，`docs/CI.md` 998 → 1000，版本记录 v2.20 |
| 文档↔程序一致 | ✅ | 规格判定口径与守卫实现一致（标题 / 工单声明行 + 精确边界匹配） |
| 工作区卫生 | ✅ | `cleanup_workspace.py --check` rc=0，见 E6 |
| 不越权改内核 | ✅ | 未改 `review_gate.py` / CI 工作流；软门禁保持 |

**Standards 结论：无 P0/P1。**

## 三、Spec 轴（规格验收映射）

| 规格验收 | 结论 | 证据 |
|---|---|---|
| T3 `git check-ignore` 命中 | ✅ | `.gitignore:48` 命中，rc=0；`git ls-files --error-unmatch` 确认未跟踪 |
| T3 跑测试后 `git status` 无该文件 | ✅ | 全量 `unittest` 后 `git status --short` 无 `findings-by-path.json`（文件被生成但被忽略） |
| T3 origin/main 事实记录 | ✅ | `git show origin/main:.gitignore` 无该条目（grep 命中 0）；origin/main @`f04d5c8`；本分支 HEAD 已含（`35f0cc9`，经 `ab5ab6b` 合入） |
| T8-a 规格存在且三要素齐备 | ✅ | `docs/toolchain/specs/align-2026-11-19.md` |
| T8-b 18 工单全覆盖或免评审 | ✅ | `TestReviewCoverage` 绿；覆盖来源为 closure-a/b/c/d + coverage-gate-review |
| T8-b `unittest` 全绿 | ✅ | `Ran 1000 tests` / `OK (skipped=4)`，rc=0 |
| T8-b `validate.py` 退出码 0 | ✅ | rc=0 |
| S5 双轴评审产出 | ✅ | 本文件 |

**Spec 结论：无 P0/P1。**

## 四、T3 核实结论与处置

- **核实**：origin/main 的 `.gitignore` **未包含** `engine/report-audits/info-quality/findings-by-path.json` 条目（`git show origin/main:.gitignore | grep -c findings-by-path` = 0）；origin/main 最新 `f04d5c8`。本任务分支 HEAD 已含该条目（提交 `35f0cc9`，经 `ab5ab6b` 合入）。
- **处置**：保留本分支已有条目，不重复新增。跑全量 `unittest`（会写回该缓存）后 `git status --short` 无该文件，`git check-ignore` 命中，T3 收口。
- **合并注意**：`.gitignore` 条目是本分支相对 origin/main 的增量，合并进 main 前不得丢失，否则缓存会重新入库。

## 五、证据（命令 + 输出摘要）

- **E1 全量测试**：`python -m unittest discover -s engine/tests -q` → `Ran 1000 tests` / `OK (skipped=4)`，rc=0。
- **E2 规范校验**：`python engine/tools/validate.py` → `结构与规范校验通过`，rc=0。
- **E3 覆盖率**：`python engine/tools/coverage_gate.py` → `覆盖率 90.4%（阈值 80%，enforce=True）（测试 全绿）` / `[OK] 覆盖率达标`，rc=0。
- **E4 T3 忽略**：`git check-ignore -v engine/report-audits/info-quality/findings-by-path.json` → `.gitignore:48:...`，rc=0；`git ls-files --error-unmatch` → 未跟踪。
- **E5 守卫红绿态**：移除 `coverage-gate-review.md` 后 `python -m unittest ...TestReviewCoverage -q` → `FAILED`，`missing=['coverage-gate']`，rc=1；移回后 → `OK`，rc=0。
- **E6 工作区卫生**：`python engine/scripts/cleanup_workspace.py --check` → `工作区干净，无残留`，rc=0（清理了 unittest 产生的 `__pycache__` / `.coverage`）。
- **E7 origin/main 核实**：`git show origin/main:.gitignore | grep -c findings-by-path` → 0；`git log --oneline -3 origin/main` → `f04d5c8` / `8ad345b` / `66bb692`。

## 六、决策记录：`review_gate` 是否转硬门禁

**本轮不改 `.github/workflows/audit-gate.yml`，保持软门禁（P2 观察期）。** 理由：

1. `review_gate` 当前粒度是「评审目录存在至少一份报告」，不是「本次变更文件 ↔ 对应评审」；直接转硬会因历史工单缺对应评审而阻断 main，误伤面大。
2. 本任务新增的 `TestReviewCoverage` 已把「工单 100% 评审覆盖」变成可执行断言（S4 测试层兜底），CI 硬门禁应建立在该守卫稳定之后。
3. **触发条件**：守卫连续稳定 ≥1 个月，且 `review_gate` 增加「变更文件 ↔ 评审覆盖」粒度后，再把 `audit-gate.yml` 的 `|| code=$?` 容忍改为阻断（退出码 1）。

## 七、残留与风险

- **P3**：`review_gate` 与新增守卫职责部分重叠（前者 CI 存在性、后者仓库级覆盖），已在决策记录中说明演进路径，不阻断。
- **P3**：守卫覆盖来源依赖评审的标题 / 工单声明行格式；新增评审需按 TOOLCHAIN-DEV-SPEC 第七节写明工单清单，否则会被守卫拦下（预期行为）。
