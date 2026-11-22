# 咨询面板门禁一致性 · 双轴评审（panel-gate-consistency，2026-11-22）

> **范围**：`task/fix-panel-gate-consistency-6b916f70` worktree（`D:\文档\GitHub\jp-life-work\.worktrees\fix-panel-gate-consistency`）。
> **基线**：`origin/main = 6b6e722`。
> **触发**：P0-P2 核验残留 ①——`test_consulting_panel` 非密闭写真实文件，且 `render_panel_md()` 输出 `[待核实]` 与 `verified_content_gate --all` 冲突。
> **结论**：**Standards 无 P0/P1；Spec 项闭环**。

---

## 一、改动清单

| 类别 | 文件 | 改动 |
|---|---|---|
| 工具 | `engine/tools/consulting_panel.py` | `build_plan()` 的 `checklist` 移除 5 条 `待核实` 项（保留 部分核验 / 已核验）；面板「核验清单」下新增记录层指针 |
| 内容 | `00-decision-hub/data/consulting_panel.md` | 重新生成（移除 5 条标记 + 指针行）；`verified_content_gate --all` 命中 5 → 0 |
| 内容 | `00-decision-hub/data/source-backlog.md` | 新增「三、咨询面板核验清单缺口（记录层）」5 条（P1–P5，含主责主题 / 性质 / 状态） |
| 测试 | `engine/tests/test_consulting_panel.py` | `test_panel_roundtrip` 改密闭临时目录（`mock.patch.object(cp, "OUT_PATH", tmp)`）；新增 `test_panel_no_unverified_markers` |
| 文档 | `docs/CI.md`、`docs/README.md`、`docs/cross-domain-expert-roles.md`、`engine/tools/README.md` | 测试计数 1127 → 1128、版本记录 v2.28 / v2.12 |

---

## 二、轴一：Standards（规范符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| AGENTS.md 硬性规约二：分支 / worktree / 串行合并 | ✅ | 全程在 `.worktrees/fix-panel-gate-consistency`；合并走 `workflow_guard.py merge` |
| 工具链开发规约：TDD / 双轴评审 | ✅ | 先加标记回归测试再改实现；本评审为双轴评审 |
| 单一事实源 | ✅ | 面板内容由 `consulting_panel.py` 生成，`--check` 一致；缺口统一入 record-layer backlog |
| 内容硬门禁 | ✅ | `verified_content_gate --all` 160 份 0 命中（改动前 5 命中） |
| 测试密闭性 | ✅ | `test_panel_roundtrip` 不再写真实文件；跑测试后 `consulting_panel.md` 不再被写脏 |
| 静态检查 | ✅ | `ruff` / `mypy` 通过 |
| 文档↔实现对齐守卫 | ✅ | `test_arch_guard` 通过（测试 1128） |

**Standards 结论：无 P0 / P1。**

---

## 三、轴二：Spec（残留 ① 验收）

| 验收标准 | 实现 | 证据 |
|---|---|---|
| 消除非密闭写真实文件 | `test_panel_roundtrip` 写临时目录 | 跑 `test_consulting_panel` 后 `git status` 无 `consulting_panel.md` |
| 面板不再输出无法核实标记 | `checklist` 移除 5 条 `待核实`；新增标记回归 | `test_panel_no_unverified_markers` 通过；面板标记计数 0 |
| 与 668c37f 清理态一致 | 重新生成后面板仅新增指针行 | `git diff` 仅指针行 |
| 缺口不丢失 | 5 条转入 `source-backlog.md` 第三节 | 该节 5 行，含主责主题 / 状态 |

**Spec 结论：残留 ① 闭环。**

---

## 四、残留

- 其余非密闭测试（写 `*/reports/*.html`、`engine/tools/README.md`、`registry.json`、`sync-state.json`）不在本任务范围，另行开单。
- `render_output_md` 的 `intermediary` 仍含「待核实」字样，仅用于个人输出文件（不入库、不被门禁扫描），暂不处理。
