# 双轴评审：近义扫描已裁定保留清单（near-exempt）

> 工单：[tickets/vocab-near-exemptions.md](../tickets/vocab-near-exemptions.md)
> 评审日期：2026-11-23
> 评审对象：`engine/vocabulary/script/vocab_near_check.py`、
> `engine/vocabulary/config/near-dup-exemptions.json`、`engine/tests/test_vocab_near_check.py`、
> `engine/vocabulary/README.md`
> 规格：[specs/vocab-near-exemptions.md](../specs/vocab-near-exemptions.md)

## 一、Standards 轴

| 条款 | 结论 | 证据 |
|---|---|---|
| 复用既有机制范式 | 通过 | 与 `verify-exemptions.json` / `concept_map` 同构（清单 + 证据指针） |
| 只读约束 | 通过 | 新增测试全部在临时目录内构造 |
| 文档数字锁定 | 通过 | 1190 → 1194 同步 4 处；README 新增 §5.3 |
| 不虚报 | 通过 | 只登记原裁定覆盖的对；新增疑似默认不豁免 |

## 二、Spec 轴

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 三、load_exemptions | 缺失 / 损坏返回空集 | 2 项单测 |
| 三、filter_exempted | 仅剔除登记对 | `test_filter_only_removes_listed_pair` |
| 四、退出码 | 全豁免 → 0 | `test_main_exit_0_when_all_exempted` |
| 四、输出计数 | `exempted` 字段 | 实跑 `0 对疑似（另 218 对已裁定保留）` |

## 三、运行证据

```
$ python engine/vocabulary/script/vocab_near_check.py
近义扫描：0 对疑似（另 218 对已裁定保留）
```

## 四、残余风险 / 遗留

- **新增疑似需人工裁定**：这是设计使然（避免自动放行导致漏并）；工具会如实报出。
- 218 条清单体积较大（约 60KB），但为机读白名单，可接受。
- 无其他遗留。
