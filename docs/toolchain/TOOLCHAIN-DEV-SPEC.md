# 工具链开发规约（TOOLCHAIN-DEV-SPEC）

> **版本**：v1.0（2026-11-17）
> **定位**：jp-life-work **工具链开发域**（代码交付）的开发流程与验收规约，选择性吸收 mainline 11 阶段规范的增量能力。
> **上位依据**：[AGENTS.md](../../AGENTS.md)、[CI.md](../CI.md)（CI-SYSTEM）、[mainline 融合评估报告](mainline融合评估报告-2026-11-17.md)（MAINLINE-INTEGRATION-ASSESSMENT-2026-11）。
> **适用对象**：`src/`、`tools/`、`.github/workflows/` 及根配置（`requirements*.txt`、`.coveragerc`、`coverage-config.json`）的变更。

---

## 一、目的与定位

本规约只解决一件事：**让工具链变更从「能力声明」变成「可合并交付物」**。

报告生产层（内容交付）继续走《信息生产全链路执行规范》五阶段与 AuditGuard 体系，
**本规约不改动、不降级、不替代**内容流程；工具链开发层（代码交付）按本规约执行。
两层「并行且边界清晰」，边界由文件范围天然划分（见第二节）。

## 二、适用范围（硬性边界）

| 层 | 路径 | 是否适用本规约 |
|---|---|---|
| 工具链代码 | `src/prompts-tools/tools/`、`src/vocabulary/script/`、`tools/` | ✅ 适用 |
| 工具链配置 / CI | `.github/workflows/`、`requirements*.txt`、`.coveragerc`、`coverage-config.json`、`mypy.ini`、`ruff.toml` | ✅ 适用 |
| 工具链测试 | `src/tests/` | ✅ 适用 |
| 报告生产内容 | `*/reports/`、`*/prompts/`、`*/handbook/`、`*/data/`、`docs/`（除本规约及 `docs/toolchain/`） | ❌ 不适用，走五阶段 + AuditGuard |

**越界即违规**：内容任务不得被强加代码阶段（规格 / 工单 / TDD / 覆盖率）；
工具链任务不得以「内容流程」名义跳过本规约的阶段与门禁。

> **与编排层的边界（R4 文档互指）**：报告生产编排（S0–S5）见
> [端到端流水线编排系统设计](../端到端流水线编排系统设计-2026-11-17.md)；本规约只管工具链代码变更，二者并行、互不替代。

## 三、阶段定义（顺序固定，不跳不并）

| 阶段 | 名称 | 交付物 | 出口检查（G0） |
|---|---|---|---|
| S1 | 规格先行（轻量 to-spec） | `docs/toolchain/specs/<任务 slug>.md`（≤1 页：动机 / 接口 / 验收标准） | 规格存在且含三要素；触发豁免时记录豁免理由 |
| S2 | 工单化（tracer-bullet） | `docs/toolchain/tickets/<任务 slug>.md`（逐条可验证工单） | ≥2 文件变更已拆工单；每条工单有验收判据 |
| S3 | TDD（红绿重构） | `src/tests/test_<模块>.py` 先行失败用例 | 新用例在实现前失败（红），实现后通过（绿） |
| S4 | 实现 | 代码 + 必要文档 | 测试全绿；`validate.py` 退出码 ∈ {0,2} |
| S5 | 双轴评审 | `docs/toolchain/reviews/<任务 slug>-review.md`（Standards + Spec 双轴结论 + 证据） | 双轴均无 P0/P1；结论含证据（命令 + 输出摘要） |
| S6 | 合并前检查单 | `tools/README.md`「合并前检查单」逐项打勾 | 测试 / validate / 评审报告 / 工作区卫生四项齐备 |

**豁免阈值**：**≤2 文件且无新增工具的变更免 S1 规格**（在任务分支说明中记录豁免理由）；
S2 工单化同步豁免。豁免不得用于规避 S5 双轴评审与 S6 合并前检查单。

## 四、命名规范

- 工具脚本：`src/prompts-tools/tools/<snake_case>.py`（公共内核 `_common.py` 唯一例外）；
- 测试：`src/tests/test_<模块>.py`，类 `Test<模块>`，方法 `test_<行为>`；
- 规格 / 工单 / 评审：`docs/toolchain/{specs,tickets,reviews}/<任务 slug>[-review].md`（kebab-case，**不得**使用 `YYYY-MM-` 报告命名，避免被 `classify_reports.py` 误判为错位报告）；
- 覆盖率配置：单一事实源 `src/prompts-tools/tools/coverage-config.json`；运行配置 `.coveragerc`。

## 五、异常处理与退出码契约

沿用仓库统一契约：**`0` = 通过；`1` = 阻断（P0/P1）；`2` = 仅警告（P2）放行**。

- 校验类工具必须显式返回上述退出码；参数错误返回 `2`。
- 覆盖率未达阈值时：`enforce=true` → `1`（阻断）；`enforce=false` → `2`（观察，不阻断）。
- 工具内部异常不得静默吞掉；失败即停，保留现场（日志 / 临时文件）供定位。
- 不得 `git push origin main`；合并只经 `tools/workflow_guard.py merge`（三层隔离）。

## 六、覆盖率门禁（单一事实源）

- 阈值与开关只读 `coverage-config.json` 的 `threshold` / `enforce`，不得在 CI 脚本硬编码。
- 统计范围限定工具链代码：`src/prompts-tools/tools/`、`src/vocabulary/script/`、`tools/`（`.coveragerc` 同源约束）。
- **分阶段提升**：P1/P2 观察期 `threshold=60, enforce=false`；P3 起 `threshold=80, enforce=true`（阻断）。
- 基线数值入库：`src/report-audits/toolchain/coverage-baseline.json`。
- 门禁入口：`python src/prompts-tools/tools/coverage_gate.py`（`--update-baseline` 刷新基线，`--porcelain` 输出 JSON）。

## 七、双轴评审（Standards + Spec）

每次工具链变更必须产出双轴评审报告，两轴独立结论：

| 轴 | 问题 | 证据要求 |
|---|---|---|
| **Standards** | 是否符合本规约 / 仓库规范（命名、退出码、异常、测试）？ | 逐条引用规约条款 + 代码位置 |
| **Spec** | 是否实现了规格与工单的验收标准？ | 规格条目 ↔ 实现/测试映射 + 运行输出 |

双轴均无 P0/P1 方可进入 S6；评审流于形式（无结论 / 无证据）视为未完成。

## 八、合并前检查单（S6，映射 mainline `pr-push-review`）

`workflow_guard merge` 前逐项确认（文档见 `tools/README.md`，守卫测试断言其存在）：

1. **测试**：`python -m unittest discover -s src/tests` 全绿；
2. **规范校验**：`python src/prompts-tools/tools/validate.py` 退出码 ∈ {0,2}；
3. **评审报告**：本任务 `docs/toolchain/reviews/<任务 slug>-review.md` 存在且双轴无 P0/P1；
4. **覆盖率**：`coverage_gate.py` 达标（P3 起 ≥80% 阻断）；
5. **工作区卫生**：`python tools/cleanup_workspace.py --check` 零残留。

## 九、守卫测试（防漂移）

`src/tests/test_toolchain_dev_spec.py` 断言：

- 本规约文件存在，且阶段顺序（S1→S6）与适用边界（第二节）不被篡改；
- `coverage-config.json` 存在且 `threshold` / `enforce` 类型正确；
- `.coveragerc` 存在且 `source` 只覆盖工具链三目录；
- `tools/README.md` 含「合并前检查单」节，四项齐备。

## 十、验收准则

| 阶段 | 验收 |
|---|---|
| P0 | 本规约审定通过；豁免阈值明确 |
| P1 | CI 可复现覆盖率；基线数值入库 |
| P2 | 试点任务全流程走通（S1→S6）；守卫测试通过；既有测试无回归 |
| P3 | 工具链变更评审覆盖 100%；覆盖率 ≥80%（阻断）；`audit-gate` 零绕过 |

## 版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-17 | 初始版本：依据 mainline 融合评估报告落地，确立适用范围、六阶段、豁免阈值、覆盖率门禁、双轴评审与合并前检查单 |
