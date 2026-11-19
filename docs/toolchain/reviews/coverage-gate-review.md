# 双轴评审：工具链门禁工具（coverage-gate，补档）

> **任务 slug**：coverage-gate
> **日期**：2026-11-19（T8-b 收口补档；原 T9 要求本文件，历史清理中缺失，现补齐）
> **评审对象**：`docs/toolchain/tickets/coverage-gate.md` T1–T10
> **评审人**：CatPaw（双轴自评）
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**。

## 一、Standards 轴

| 条款 | 结论 | 证据 |
|---|---|---|
| 命名规范 | ✅ | `engine/tools/coverage_gate.py` / `review_gate.py`（snake_case）；测试 `test_coverage_gate.py` / `test_review_gate.py` |
| 单一事实源 | ✅ | 阈值 / 开关只读 `engine/tools/coverage-config.json`；未在 CI 硬编码 |
| 退出码契约 | ✅ | `coverage_gate.py` 达标 0、未达标按 `enforce` 返回 1/2；`review_gate.py` 0/1 |
| 异常不静默 | ✅ | 清单读取失败、参数错误均显式返回非 0；测试覆盖 |
| 测试入 `engine/tests/` | ✅ | `test_coverage_gate.py` / `test_review_gate.py` / `test_toolchain_dev_spec.py` 通过 |
| 工作流复用 | ✅ | `validate.yml` 接覆盖率 job；`audit-gate.yml` 接评审软门禁（P2 观察期口径与规格一致） |
| 合并前检查单 | ✅ | `engine/scripts/README.md` 四项齐备，守卫断言存在 |

## 二、Spec 轴（T1–T10 映射）

| 工单 | 验收判据 | 结论 | 证据 |
|---|---|---|---|
| T1 | `coverage-config.json` 字段类型正确、阈值不硬编码 | ✅ | `test_toolchain_dev_spec.py::TestCoverageConfig` |
| T2 | `.coveragerc` source 限工具链三目录、无 `reports/` | ✅ | `TestCoverageConfig::test_source_limited_to_toolchain` |
| T3 | `requirements.txt` 锁定 `coverage` | ✅ | 依赖可安装，CI 可复现 |
| T4 | `coverage_gate.py` TDD 15 项 | ✅ | `test_coverage_gate.py` 通过 |
| T5 | `review_gate.py` TDD 9 项 | ✅ | `test_review_gate.py` 通过 |
| T6 | `test_toolchain_dev_spec.py` 11 项 | ✅ | 本文件所在测试模块通过 |
| T7 | `validate.yml` / `audit-gate.yml` 接线 | ✅ | 覆盖率 job + 评审软门禁步骤存在 |
| T8 | `engine/scripts/README.md` 登记 + registry 刷新 | ✅ | `test_arch_guard` / `test_registry_generator` 通过 |
| T9 | 双轴评审归档 | ✅ | 本文件（补档） |
| T10 | 覆盖率 ≥80%（enforce=true） | ✅ | `coverage_gate.py` 实测 **90.4%**（阈值 80，enforce=True，rc=0） |

## 三、证据

- `python engine/tools/coverage_gate.py` → `覆盖率 90.4%（阈值 80%，enforce=True）（测试 全绿）` / `[OK] 覆盖率达标`（rc=0）。
- `python -m unittest engine.tests.test_coverage_gate engine.tests.test_review_gate engine.tests.test_toolchain_dev_spec -q` → `OK`（rc=0）。

## 四、备注

- 本文件为 T8-b「工单 100% 评审覆盖」守卫补档，不改变原 T1–T10 结论；原结论见 `docs/toolchain/tickets/coverage-gate.md`。
