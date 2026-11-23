# 规格：阶段闸登记册判据修复（registry-path）

> 任务 slug：`fix-stage-gate-registry-path`
> 版本：v1.0（2026-11-23）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)

## 一、动机

`local_ci` 的 `stage` / `gen-gate` / `info-quality` 三项各报 1 条 P2，同源：
`00-decision-hub` 缺少 `data/*_indicator_registry.md`。但该主题的
`prompts/business-config.md` **已声明** `{{REGISTRY_PATH}} = data/decision_hub_registry.md`
且该文件存在——现行判据只 glob `*_indicator_registry.md`，漏认声明式路径。

## 二、目标与非目标

**目标**：`G1-REGISTRY` 判据改为「glob 未命中时，若 `{{REGISTRY_PATH}}` 已声明且文件存在，则视为有登记册」。

**非目标**：不给单个主题硬编码豁免；不把声明式登记册喂给 `gate2_filter`（其活值表 Schema 与
决策登记册结构不同，会误报 `G2-SCHEMA` P1）。

## 三、接口设计

`engine/tools/stage_gate_check.py` `check_topic()`：

```python
if not regs:
    declared_path = (b.path / declared.group(1).strip()) if declared else None
    if declared_path and declared_path.is_file():
        pass  # 以 {{REGISTRY_PATH}} 声明的登记册为准
    else:
        out.append(Finding("G1-REGISTRY", "P2", "指标登记册",
                           f"缺少 data/{REGISTRY_GLOB}，且未声明可用的 {{{{REGISTRY_PATH}}}}"
                           "（骨架主题可豁免）", "闸1"))
else:
    out += gate2_filter(_read(regs[0]))
```

新增测试：`test_check_topic_declared_registry_without_glob`（声明路径存在但非 glob 命名 → 无 finding）。

## 四、验收标准

1. 新测试先红后绿；既有 `test_check_topic_no_indicator_registry`（未声明路径）仍报 `G1-REGISTRY`。
2. 全库实跑 `stage_gate_check.run_all()`：`P0/P1 = 0`，`00-decision-hub` 不再产生 `G1-REGISTRY`。
3. `validate.py` / `unittest` / `ruff` / `mypy` 全绿；测试数变化同步锁定文档。

## 五、边界与约束

- 仅改判据分支与文案，不改 `gate2_filter` 语义。
- 工具链变更按 S1→S6，文件数 > 2，不豁免。
