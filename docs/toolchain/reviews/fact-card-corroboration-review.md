# 双轴评审：事实卡片 corroboration 语义（single-source）

> 工单：[tickets/fact-card-corroboration.md](../tickets/fact-card-corroboration.md)
> 评审日期：2026-11-23
> 评审对象：`engine/tools/fact_card_check.py`、`engine/report_templates/fact-card-standard.md`、
> `00-decision-hub/data/fact_cards.md`、`engine/tests/test_tools.py`、`docs/CI.md`、
> `docs/README.md`、`docs/cross-domain-expert-roles.md`、`engine/tools/README.md`
> 规格：[specs/fact-card-corroboration.md](../specs/fact-card-corroboration.md)

## 一、Standards 轴（规约符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| 信息质量「不虚报」 | **通过** | 未为凑计数加入非独立来源；标准文档明文禁止 |
| 命名 / 退出码契约 | 不涉及 | 未改 CLI 入口与退出码（仍 0/1/2） |
| 复用既有判定内核 | 通过 | 仅在 `check_corroboration` 增加一个显式取值分支 |
| 只读约束 | 通过 | 新增测试使用内存字典，不碰仓库文件 |
| 文档数字双向锁定 | 通过 | 测试数 1186 → 1188 同步 4 处；标准文档升 v1.2 |
| 测试先行 | 通过 | 两项新测试先红（`single-source` 被当 `<2`；在库卡片全为 `1`）后绿 |
| 工具链流程 | 通过 | S1→S6 齐备，文件数 > 2 未豁免 |

## 二、Spec 轴（规格 ↔ 实现映射）

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 三、corroboration 允许 `single-source` | `parse_cards()` 保留原值；`check_corroboration()` 命中即跳过 | `test_corroboration_single_source` |
| 三、空值仍报 P2 | 空分支不变 | `test_corroboration_check` |
| 三、标准文档登记语义 | standard §一 + §四.4 + v1.2 | 文本核对 |
| 三、在库数据合规 | 15 张卡改 `single-source`，头部注明口径与复核待办 | `test_real_cards_corroboration_declared` + `fact_card_check.run()` 零 issue |

## 三、运行证据

```
$ python -m unittest engine.tests.test_tools.TestFactCardCheck
Ran 6 tests ... OK

$ python engine/tools/fact_card_check.py
事实卡片校验：15 张卡片 / 15 个指针
  跨报告事实重复率 1.4%（门槛 10%）
  问题：P0/P1 0 / P2 0

$ python engine/tools/validate.py
结构与规范校验通过
```

## 四、残余风险 / 遗留

- **已识别的复核待办（如实登记，未伪造）**：FC-008 / FC-009 / FC-010 / FC-011 / FC-013 /
  FC-014 / FC-015 / FC-016 可能确有可核验的独立第二源。本次因多数 `.go.jp` / `jpf.go.jp`
  页面在本环境返回 403、无法核验内容，**一律不予引用**；已在卡片头部列为优先复核候选，
  留待人工复核后改为整数计数。
- **风险（低）**：`single-source` 为自述声明、无外部校验。缓解：标准文档限定其适用条件
  （官方统计 / 官方定价），并有守卫测试确保取值只能是 `single-source` 或 ≥2。
- **遗留**：无（本工单范围内）。
