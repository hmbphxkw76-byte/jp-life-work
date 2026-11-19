# review_gate 转硬评估框架（B5）

> **来源工单**：[b5-review-gate-hardening](../toolchain/tickets/b5-review-gate-hardening.md)
> **状态**：计划（未切换门禁）
> **优先级**：P2（时间门控）
> **创建日期**：2026-11-19
> **最近评估日期**：2026-11-19
> **下次评估日期**：2026-12-19

---

## 一、背景

`audit-gate.yml` 的 `review_gate`（`engine/tools/review_gate.py`）当前为**软门禁**：
工具链变更缺双轴评审时仅 `::warning::` 告警，不阻断合并。

`docs/toolchain/specs/align-2026-11-19.md` §四决策：**守卫稳定 ≥1 个月 + 粒度升级后**再评估转硬；
禁止在未验证时切换。本文件把该决策固化为可检查的评估框架，**不改变现行门禁语义**。

## 二、转硬条件（须全部满足）

| # | 条件 | 判定口径 |
|---|---|---|
| C1 | 评审守卫稳定运行 **≥1 个月** | 以 `engine/tests/test_toolchain_dev_spec.py::TestReviewCoverage` 连续通过、无回归为准；自 2026-11-19 引入起算，最早 2026-12-19 评估 |
| C2 | `review_gate.py` 粒度从「评审目录非空」升级到「**变更文件 ↔ 评审覆盖**」 | 变更涉及的具体文件 / 工单须在 `docs/toolchain/reviews/*.md` 中有对应评审；测试同步 |
| C3 | 存量工单评审覆盖补齐 | `TestReviewCoverage` 全绿（当前 B1–B9 工单缺评审，见下表） |
| C4 | 回滚预案就绪 | 转硬后若误伤，可恢复 `::warning::` 容忍（见第五节） |

## 三、当前状态记录表

| 日期 | 里程碑 | `review_gate.py` 粒度 | 稳定性 | 备注 |
|---|---|---|---|---|
| 2026-11-19 | T8 新增 `TestReviewCoverage`（文档层「工单 ↔ 评审」守卫） | 评审目录存在至少一份 `.md`（`has_review`） | < 1 个月 | B1–B9 工单缺评审，该守卫 1 项失败；`review_gate.py` 本体粒度未升级 |
| 2026-11-19 | 本计划建档 | 同上 | < 1 个月 | 首次评估：条件 C1/C2/C3 均未满足 |
| 2026-12-19（计划） | 首次满 1 个月评估 | 待升级 | ≥ 1 个月 | 若 C2/C3 完成则评估转硬；否则顺延 |

### 3.1 现状细节

- **范围**：`SCOPE_DIRS = engine/tools/`、`engine/vocabulary/script/`、`engine/scripts/`。
- **粒度**：`gate()` 仅判断 `has_review(reviews_dir)`（目录存在至少一份 `.md`），**不**校验变更文件与评审的对应关系。
- **CI 语义**：`audit-gate.yml`「工具链评审软门禁」步骤对退出码非 0 仅 `::warning::`，不 `exit 1`。
- **文档层守卫**：`TestReviewCoverage` 已按工单 slug 断言评审覆盖（含「免评审」豁免口径），但**不等于** `review_gate.py` 的运行时粒度。

## 四、转硬步骤（条件达成后执行，届时另开工单）

1. `review_gate.py` 升级粒度：按变更清单匹配 `docs/toolchain/reviews/*.md` 的「工单 / 文件」声明，缺失即退出码 1；同步 `test_review_gate.py`。
2. `audit-gate.yml` 把 `::warning::` 改为 `::error::` + `exit 1`（移除容忍）。
3. `docs/CI.md` 二.6 / 十一节同步为「阻断」。
4. 留版本记录（`docs/CI.md` / `engine/tools/README.md`）。

## 五、风险与回滚

- **误伤风险**：粒度升级前若转硬，历史工单缺评审会阻断 main 推送（`align-2026-11-19.md` §四已警示）。
- **回滚判据**：转硬后出现非预期阻断（评审存在但粒度误判）→ 恢复 `audit-gate.yml` 的 `::warning::` 容忍，保留 `review_gate.py` 新粒度，待修复后再转硬。

## 六、声明

本文件仅为评估计划，**未切换门禁**：`audit-gate.yml` 与 `engine/tools/review_gate.py` 现状不变，
评审步骤维持软门禁。
