# 双轴评审：工具链门禁工具 + mainline 规范落地（coverage-gate）

> **任务 slug**：coverage-gate
> **日期**：2026-11-17
> **评审对象**：`task/mainline-spec-landing` 分支全量变更
> **规格 / 工单**：[规格](../specs/coverage-gate.md) · [工单](../tickets/coverage-gate.md)
> **评审人**：CatPaw（独立双轴）

---

## 一、Standards 轴（是否符合本规约 / 仓库规范）

| 条款 | 结论 | 证据 |
|---|---|---|
| 适用边界（仅代码） | ✅ | 变更仅落在 `src/`、`tools/`、`.github/workflows/`、根配置与 `docs/toolchain/`；未触碰 `*/reports/`、`*/prompts/`、`*/data/` |
| 六阶段顺序 | ✅ | 规格（S1）→ 工单（S2）→ TDD（S3）→ 实现（S4）→ 双轴评审（S5）→ 合并前检查单（S6）依次留痕；`docs/toolchain/{specs,tickets,reviews}/` 齐备 |
| 命名规范 | ✅ | 工具 `coverage_gate.py` / `review_gate.py`（snake_case）；测试 `test_coverage_gate.py` / `test_review_gate.py` / `test_toolchain_dev_spec.py` |
| 退出码契约 | ✅ | `coverage_gate` 0/1/2 语义与测试断言一致；`review_gate` 0/1 语义与测试断言一致；参数错误返回 1 |
| 异常处理 | ✅ | 配置缺失 / 非法显式报错并返回 1，不静默用默认；基线写入原子化并清理临时文件 |
| 覆盖率单一事实源 | ✅ | 阈值 / 开关仅在 `coverage-config.json`；`.coveragerc` 只约束 `source` / `omit`；CI 脚本无硬编码阈值 |
| 统计范围限定 | ✅ | `.coveragerc` source = 工具链三目录；`omit` 仅排除词库维护 / 一次性迁移 / 本地辅助脚本（依 R2） |
| 不越权改内核 | ✅ | `workflow_guard.py` 语义未改；检查单以文档 + 守卫测试固化 |
| 测试无回归 | ✅ | 全量 803 项全绿（`python -m unittest discover -s src/tests`）；`test_arch_guard` / `test_cleanup` CI 接线契约通过 |

**Standards 轴结论：无 P0 / P1。**

## 二、Spec 轴（是否实现规格与工单的验收标准）

| 验收标准（规格三.1–三.6） | 结论 | 证据 |
|---|---|---|
| 1. `coverage_gate` 读配置采集覆盖率并按阈值返回 0/1/2；测试未全绿一律 1 | ✅ | `test_coverage_gate.py` 15 项（`TestEvaluate` 4 项 + `test_below_enforced_exit_1` / `test_tests_not_green_forces_block`） |
| 2. `--porcelain` 输出五字段 JSON | ✅ | `test_porcelain_json` 断言 `total_percent` / `threshold` / `enforce` / `tests_green` / `exit_code` |
| 3. `review_gate` 工具链变更要求评审、内容层放行 | ✅ | `test_review_gate.py` 9 项（含 `test_content_only_change_passes` / `test_toolchain_change_without_review_blocks`） |
| 4. 单一事实源守卫 | ✅ | `test_toolchain_dev_spec.py::TestCoverageConfig` 3 项 + `test_source_limited_to_toolchain` |
| 5. 守卫测试断言规约 / 配置 / 检查单 / 评审范围 | ✅ | `test_toolchain_dev_spec.py` 11 项 |
| 6. 既有测试无回归 | ✅ | 803 项全绿；本次新增 495 项（15 + 9 + 11 + 69 + 122 + 57 + 111 + 100 + cleanup 1） |

**Spec 轴结论：无 P0 / P1。**

## 三、指标核验

| 指标 | 目标 | 实测 | 结论 |
|---|---|---|---|
| 工具链测试数 | 285 → ≥320 | 803（全仓）/ 本次新增 495 | ✅ |
| 工具链覆盖率 | 0 门禁 → ≥80%（P3 阻断） | 93%（6470 语句，缺 472） | ✅ |
| 评审覆盖 | 工具链变更 100% | 本变更附本评审；`review_gate` 已接入 audit-gate | ✅ |
| audit-gate 绕过 | 零 | `review_gate` 步骤已加入 audit-gate.yml | ✅ |

## 四、遗留与后续

- **P1/P2 观察期已过**：`coverage-config.json` 现为 `threshold=80, enforce=true`（P3 阻断态）；`stage_history` 保留 60→80 轨迹。
- **软门禁硬度**：`audit-gate` 的 `review_gate` 为告警不阻断（软），如需转硬由配置决定；工具退出码语义已按阻断设计。
- **覆盖率为 in-process 口径**：子进程调用的工具不计入（本次补测已大量改为导入直调）；`.coveragerc` 未启用 `parallel`，避免污染测试工作区。
