# 双轴评审：反例扫描裁定清单（ce-adjudications）

> 工单：[tickets/counterexample-adjudications.md](../tickets/counterexample-adjudications.md)
> 评审日期：2026-11-23
> 评审对象：`engine/tools/counterexample_scan.py`、
> `engine/config/counterexample-adjudications.json`、`engine/tests/test_counterexample_scan.py`
> 规格：[specs/counterexample-adjudications.md](../specs/counterexample-adjudications.md)

## 一、Standards 轴

| 条款 | 结论 | 证据 |
|---|---|---|
| 复用既有裁定范式 | 通过 | 与 `near-dup-exemptions.json` / `verify-exemptions.json` 同构 |
| 只读约束 | 通过 | 新增测试全部在临时目录内构造 |
| 不虚报 | **通过（关键）** | 「单源」39 条**未登记**，继续可见；只在补第二来源后才消解 |
| 文档数字锁定 | 通过 | 1194 → 1198 同步 4 处 |
| 测试先行 | 通过 | 新增用例先红（无裁定时全量待处理）后绿 |

## 二、Spec 轴

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 三、load_adjudications | 缺失 / 损坏返回空 | 2 项单测 |
| 三、过滤 + adjudicated 计数 | main 分类输出 | `test_main_filters_adjudicated` |
| 四、单源不豁免 | 配置不含单源条目 | 实跑 39 条待处理全部为 `[单源]` |
| 四、退出码语义 | 仅由待处理决定 | 既有 `test_main_exit_2` 保持 |

## 三、运行证据

```
$ python engine/tools/counterexample_scan.py
反例扫描：18 份报告，39 条待处理（另 22 条已裁定）
```

## 四、残余风险 / 遗留

- **39 条「单源」是真实内容欠账**：本工单刻意不豁免，需逐条补第二来源或显式降级；
  这也是 `counterexample` 仍WARN（退出码 2=放行）的原因——属预期，不是缺陷。
- 无其他遗留。
