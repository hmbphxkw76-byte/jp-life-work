# 双轴评审：赴日决策标准咨询面板（consulting-panel）

> **工单**：`docs/toolchain/tickets/n18-consulting-panel.md`
> **规格**：`docs/toolchain/specs/consulting-panel.md`
> **日期**：2026-11-18
> **范围**：`engine/tools/consulting_panel.py`（新增）、`engine/config/decision-tools.json`、`engine/tests/test_consulting_panel.py`（新增）、`engine/tests/test_decision_config.py`、`engine/tools/README.md`、`engine/tools/registry.json`、`00-decision-hub/data/consulting_panel.md`、`docs/CI.md`

## 一、Standards 轴（是否符合仓库规范）

| 检查 | 结论 | 证据 |
|---|---|---|
| 命名规范（工具 snake_case / 文档 kebab-case） | 通过 | `consulting_panel.py`；`consulting-panel.md` / `n18-consulting-panel.md` |
| 退出码契约 0/1/2 | 通过 | 模块 docstring + `main()`；`--check` 不一致返回 2 |
| 异常不静默 | 通过 | 配置缺失经 `load_decision_config` 抛 `ValueError`；写入失败返回 1 |
| 单一事实源（配置不外泄字面量） | 通过 | 参考值全部经 `REF` / `LICENSE_MAP`；`test_decision_config.DriftGuardCase` 对 `consulting_panel.py` 断言无 `62,500 / 310,975 / 324,381 / 0.33` 字面量 |
| 测试先行与覆盖 | 通过 | `test_consulting_panel.py` 15 项；`unittest discover` 1023 项 |
| 工具登记与文档同步 | 通过 | `generate_registry.py --check` 一致（工具 45）；`engine/tools/README.md` 两表补行；`docs/CI.md` 测试数 1008→1023 |
| 工作区卫生 | 通过 | `cleanup_workspace.py --check` 无跟踪残留（`__pycache__` 为 gitignored） |
| 不跨层越界 | 通过 | 未改报告生产流程；`personal_finance_model.py` / `pending_verification.py` 未动 |

**Standards 结论：无 P0/P1。**

## 二、Spec 轴（是否实现规格验收标准）

| 验收标准 | 实现 | 证据 |
|---|---|---|
| 面板确定性生成，`--check` 退出码 0 | `render_panel_md()` 纯函数；`--check` 比对 | `python engine/tools/consulting_panel.py --render-panel && --check` → 「校验通过」 |
| 17 字段与 PF-01…PF-17 对应；固定/派生标注 | `FIELDS` 17 项；`FIXED` 6 项；`derive()` 2 项 | `ConfigCase::test_schema`；`--demo` 参数状态表 |
| 空白 → 全待定；已填 → Q2/Q3/Q4 是；Q1 三态 | `evaluate()` + `_q1` | `EvaluateCase` 4 项（含 `test_q1_yes_and_no`） |
| 参考值读配置，无硬编码 | `REF` / `LICENSE_MAP` | `DriftGuardCase` 扩展通过 |
| `--demo` 标注非真实数据 | `render_output_md(demo=True)` | `test_demo_labeled` 断言含「演示」「非真实个人数据」 |
| S5 双轴评审 | 本文件 | Standards / Spec 均无 P0/P1 |
| 全量门禁 | 见下 | unittest 1023 全绿；validate 退出码 0；覆盖率 90.2%（≥80%）；cleanup 零残留 |

**Spec 结论：无 P0/P1。**

## 三、门禁证据（命令 + 输出摘要）

| 命令 | 结果 |
|---|---|
| `python -m unittest discover -s engine/tests` | Ran 1023 tests，OK（4 skipped 为既有） |
| `python engine/tools/validate.py` | 退出码 0，「结构与规范校验通过」 |
| `python engine/tools/consulting_panel.py --check` | 退出码 0，「咨询面板校验通过：与重算一致」 |
| `python engine/tools/generate_registry.py --check` | 一致：工具 45 · 类型 12 · 主题 21 · 工作流 8 |
| `python engine/tools/coverage_gate.py` | 覆盖率 90.2%（阈值 80%，enforce=True） |
| `python engine/scripts/cleanup_workspace.py --check` | 无跟踪残留 |

## 四、残留与后续

- **部分核验项**（非本工具缺陷，属知识库待办）：外免切替合格率原文、中国准驾车型官方 1:1 对照、中型教习所均价、候选地域岗位/支援、単身世帯生活成本。已在面板「核验清单」与 `pending-verification` 台账中跟踪。
- **个人参数未填**：`personal_profile.json` 尚不存在，面板当前输出全「待定」；引擎能力由 `--demo` 演示，未写入真实值。
- **未接入 CI**：本工具为手动入口，未加入工作流；如需周期性刷新面板 md，再评估接入 `validate.yml` / `scheduled-maintenance.yml`。
