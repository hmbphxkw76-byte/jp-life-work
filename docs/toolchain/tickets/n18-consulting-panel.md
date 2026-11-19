# 工单 N18：赴日决策标准咨询面板（consulting-panel）

> **来源**：用户任务「把 00-decision-hub 的参数模板做成标准咨询面板 + 决策引擎」
> **状态**：进行中
> **验收判据**：见各条「验收」；全部完成后回填状态与证据。

---

## N18-1 配置与字段（决策支持）

- **目标**：在 `engine/config/decision-tools.json` 新增 `consulting_panel` 段，承载 17 字段、驾照映射、参考值与来源；代码不写死。
- **验收**：`test_consulting_panel.ConfigCase::test_schema` / `test_single_source_consumption` 通过；`test_decision_config.DriftGuardCase` 对 `consulting_panel.py` 的硬编码字面量断言通过。
- **证据**：`engine/config/decision-tools.json` diff；`python -m unittest engine.tests.test_consulting_panel engine.tests.test_decision_config` 全绿。

## N18-2 派生与五问判定

- **目标**：实现 `derive()`（PF-03 / PF-14）与 `evaluate()`（Q1–Q5），空白输入全「待定」，已填输入可判「是」，Q1 具备三态。
- **验收**：`DeriveCase` / `EvaluateCase` 全通过；`--demo` 输出标注「非真实个人数据」。
- **证据**：`engine/tools/consulting_panel.py`；`--demo` 输出。

## N18-3 行动方案与面板渲染

- **目标**：`build_plan()` 输出驾照路径 / 时间线 / 预算 / 中介核验 / 核验清单；`render_panel_md()` 确定性生成面板 md。
- **验收**：`--render-panel` + `--check` 退出码 0；`RenderCase` 通过。
- **证据**：`00-decision-hub/data/consulting_panel.md`。

## N18-4 工具登记与文档

- **目标**：`generate_registry.py --write` 登记工具；`engine/tools/README.md` 两张表补行；S1 规格 / S5 评审落盘。
- **验收**：`generate_registry.py --check` 一致（工具 45）；`docs/toolchain/specs/consulting-panel.md`、`reviews/consulting-panel-review.md` 存在。
- **证据**：`engine/tools/registry.json`；`engine/tools/README.md`。

## N18-5 全量门禁

- **目标**：`unittest discover` / `validate.py` / `coverage_gate.py` / `cleanup_workspace.py --check` 全过。
- **验收**：退出码满足 TOOLCHAIN-DEV-SPEC §八 检查单。
- **证据**：命令输出。
