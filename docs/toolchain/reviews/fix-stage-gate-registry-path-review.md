# 双轴评审：阶段闸登记册判据修复（registry-path）

> 工单：[tickets/fix-stage-gate-registry-path.md](../tickets/fix-stage-gate-registry-path.md)
> 评审日期：2026-11-23
> 评审对象：`engine/tools/stage_gate_check.py`、`engine/tests/test_tools.py`、
> `docs/CI.md`、`docs/README.md`、`docs/cross-domain-expert-roles.md`、`engine/tools/README.md`
> 规格：[specs/fix-stage-gate-registry-path.md](../specs/fix-stage-gate-registry-path.md)

## 一、Standards 轴（规约符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| 命名 / 退出码契约 | 不涉及 | 未改 CLI 入口与退出码语义（仍为 0/1/2） |
| 复用既有判定内核 | 通过 | 仅调整 `G1-REGISTRY` 分支，未新写规则常量 |
| 只读约束 | 通过 | 新增测试全部在 `TemporaryDirectory` 内，不碰仓库文件 |
| 生成物确定性 | 不涉及 | 无生成物 |
| 文档数字双向锁定 | 通过 | 测试数 1185 → 1186 已同步 4 处（CI 六节 / docs README v2.22 / cross-domain-expert-roles / tools README v1.23） |
| 测试先行 | 通过 | 新测试先红（实测输出 `G1-REGISTRY` P2）后绿 |
| 工具链流程 | 通过 | S1→S6 齐备；本工单文件数 > 2，未豁免 |

## 二、Spec 轴（规格 ↔ 实现映射）

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 三、glob 未命中且声明路径存在 → 视为有登记册 | `if not regs and declared and (b.path / declared.group(1).strip()).is_file(): pass` | `test_check_topic_declared_registry_without_glob` |
| 三、不把声明式登记册喂给 `gate2_filter` | 走 `pass` 分支，不进 `else` | 该测试断言 `check_topic(b) == []`（无 `G2-SCHEMA`） |
| 三、文案更新 | 「…且未声明可用的 `{{REGISTRY_PATH}}`（骨架主题可豁免）」 | 既有 `test_check_topic_no_indicator_registry` 仍命中 `G1-REGISTRY` |
| 四、验收 2 | `run_all()` 21 主题 P2 归零 | 实跑 `P0 0 / P1 0 / P2 0` |

## 三、运行证据

```
$ python -m unittest engine.tests.test_tools.TestStageGateCheck
Ran 15 tests ... OK

$ python engine/tools/stage_gate_check.py
阶段闸检查：21 个主题，通过 21 / 不通过 0
  P0 0 / P1 0 / P2 0

$ python engine/tools/validate.py
结构与规范校验通过
```

## 四、残余风险 / 遗留

- **风险（低）**：声明式登记册路径存在但内容为空 / 结构不符时，本判据不再报 P2。当前唯一使用者
  是 `00-decision-hub`（决策层），其内容纪律由 `decision_metrics.py` 与五问机制约束；标准主题
  仍走 glob + `gate2_filter`。若日后有主题改用声明式路径规避活值表校验，需另加约束。
- **遗留**：无（本工单范围内）。
