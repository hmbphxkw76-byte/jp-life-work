# 规格：工具链门禁工具（覆盖率门禁 + 评审软门禁）

> **任务 slug**：coverage-gate
> **日期**：2026-11-17
> **依据**：TOOLCHAIN-DEV-SPEC v1.0 第六 / 七节；mainline 融合评估报告 P1 / P3
> **范围**：新增 2 个工具 + 1 份单一事实源配置 + CI 接线 + 守卫测试（≥2 文件，不适用豁免）

## 一、动机

- 工具链变更长期无覆盖率视图（285 项测试只证明「有测试」，不证明「测得够」）；
- 工具链变更无独立双轴评审载体，评审覆盖 0%；
- mainline 融合评估结论要求「选择性吸收覆盖率门禁与双轴评审」。

## 二、接口

| 工具 | 入口 | 退出码 |
|---|---|---|
| `coverage_gate.py` | 无参（门禁）/ `--update-baseline` / `--porcelain` | 0 达标；1 未达标且 enforce 或测试失败；2 观察期未达标 |
| `review_gate.py` | `--changed <清单> [--reviews-dir <目录>]` | 0 通过；1 工具链变更缺评审或参数错误 |

**单一事实源**：`coverage-config.json` 承载 `threshold` / `enforce` / `test_discovery` / `baseline`；
`.coveragerc` 承载 `source` / `omit`。CI 不硬编码阈值。

## 三、验收标准

1. `coverage_gate` 读取配置并运行契约测试采集覆盖率，按阈值返回 0/1/2；测试未全绿一律 1；
2. `coverage_gate --porcelain` 输出含 `total_percent` / `threshold` / `enforce` / `tests_green` / `exit_code` 的 JSON；
3. `review_gate` 对工具链路径变更要求 `docs/toolchain/reviews/` 存在 `.md`，内容层变更放行；
4. 单一事实源守卫：阈值只在 `coverage-config.json`，`.coveragerc` 的 `source` 只限工具链三目录；
5. 守卫测试 `test_toolchain_dev_spec.py` 断言规约 / 配置 / 检查单 / 评审范围不漂移；
6. 既有 308 项测试无回归。

## 四、边界

- 不改动 `workflow_guard` 内核合并语义；
- 不改动报告生产五阶段 / AuditGuard；
- 不引入 PR 通道（本 repo 无 PR，评审软门禁为映射实现）。
