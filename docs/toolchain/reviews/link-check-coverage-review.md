# 双轴评审：link_check 覆盖率提升（link-check-coverage）

> 评审日期：2026-11-23
> 评审对象：`engine/tests/test_tools.py::TestLinkCheckUnits`
> 说明：本任务为纯测试增强（1 个文件），按 TOOLCHAIN-DEV-SPEC 豁免 S1/S2；仍做双轴评审。

## 一、Standards 轴

| 条款 | 结论 | 证据 |
|---|---|---|
| 测试先行 | 说明 | 新增用例在既有实现上直接通过——属**补覆盖**而非行为变更；被测行为均已由实跑校验背书 |
| 只读约束 | 通过 | 全部在 `tempfile` 临时目录内构造；外链用 mock，不产生真实网络请求 |
| 文档数字锁定 | 通过 | 1197 → 1206 同步 4 处 |

## 二、Spec 轴（目标 ↔ 结果）

| 目标 | 结果 |
|---|---|
| `link_check.py` 覆盖率 ≥75% | **78.5%**（原 65.4%）；全库总覆盖 88.89% → 89.08% |
| 覆盖盲区 | 已补：`_is_external` / `_looks_like_path`、MD/HTML/JSON 候选提取、跳过规则（外链 / `#锚点` / `{{模板}}` / 仓库外）、`SKIP_PREFIXES`、`_check_audit_status` 三种状态、外部 URL 收集与抽检（mock 200 / 500） |

## 三、残余风险 / 遗留

- `check_external` 的真实网络路径仍未在 CI 执行（设计使然，仅 `--external` 手工触发）；已由 mock 覆盖分支逻辑。
- 无其他遗留。
