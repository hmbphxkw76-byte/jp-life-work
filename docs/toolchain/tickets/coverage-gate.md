# 工单：工具链门禁工具（coverage-gate）

> **拆分工单（tracer-bullet）**：每个工单可独立验证；按序完成。
> **登记载体**：任务分支 `task/mainline-spec-landing` 说明 + 本文件。

| # | 工单 | 验收判据 | 状态 |
|---|---|---|---|
| T1 | 新增 `coverage-config.json` 单一事实源（threshold/enforce/test_discovery/baseline + 分阶段历史） | JSON 可解析；字段类型正确；阈值不在 CI 硬编码 | ✅ |
| T2 | 新增 `.coveragerc`（source 三目录 + omit 非现行脚本） | 守卫测试断言 source 限工具链、无 `reports/` | ✅ |
| T3 | `requirements.txt` 固定 `coverage` 版本 | 版本锁定；CI 可安装 | ✅ |
| T4 | TDD 实现 `coverage_gate.py`（红→绿） | `test_coverage_gate.py` 15 项通过 | ✅ |
| T5 | TDD 实现 `review_gate.py`（红→绿） | `test_review_gate.py` 9 项通过 | ✅ |
| T6 | 守卫测试 `test_toolchain_dev_spec.py` | 11 项通过 | ✅ |
| T7 | `validate.yml` 接入覆盖率 job；`audit-gate.yml` 接入评审软门禁 | CI 接线含前置 / 收尾清理；步骤可执行 | ✅ |
| T8 | `engine/scripts/README.md` 登记工具 + 合并前检查单；刷新 registry | `test_arch_guard` / `test_registry_generator` 通过 | ✅ |
| T9 | 双轴评审报告归档 | `docs/toolchain/reviews/coverage-gate-review.md` 双轴无 P0/P1 | ✅ |
| T10 | 工具链覆盖率达 ≥80%（enforce=true） | `coverage_gate.py` 退出码 0 | ✅ 已完成 |

## T10 闭环证据（2026-11-19）

- **实测命令**：`python engine/tools/coverage_gate.py`
- **实测结果**：**90.4%**（阈值 80%，`enforce=true`，测试全绿），退出码 `0`，末行 `[OK] 覆盖率达标`。
- **实测环境**：`task/closure-a-93955b6d` 工作树（main @`fb1a38b`）。
- **说明**：本工单文件在原 `docs` 清理（`14706bb`，2026-11-19 12:52）中随一次性过程记录一并删除；为闭环 N3 工单恢复本文件并回填 T10 状态。
