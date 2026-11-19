# 规格：赴日决策标准咨询面板（consulting-panel）

> **任务 slug**：consulting-panel
> **日期**：2026-11-18
> **适用**：TOOLCHAIN-DEV-SPEC S1（新增工具，不适用 ≤2 文件豁免；S1→S6 全走）

## 一、动机

- 00-decision-hub 五问当前 0/5 收敛，根因是**个人参数（PF-01…PF-17）缺失**，而非事实缺失。缺一个把「参数采集 → 五问判定 → 条件化方案」固化下来的可执行入口。
- 现有 `personal_profile.md` 是静态表格，无派生（PF-03 / PF-14）、无判定逻辑、无方案输出；`personal_finance_model.py` 只算净储蓄率，不覆盖驾照路径与时间线。
- 用户要求：**空白面板 + 填写指引**（人用）与**决策引擎**（程序用）两者都要；参考值须经外部核验；个人未提供值保持空、不补值。

## 二、接口

| 项 | 内容 |
|---|---|
| 新增工具 | `engine/tools/consulting_panel.py` |
| 配置 | `engine/config/decision-tools.json` 新增 `consulting_panel` 段（17 字段 / license_map / reference / sources） |
| 面板产物 | `00-decision-hub/data/consulting_panel.md`（`--render-panel` 生成，`--check` 校验） |
| 输入 | `00-decision-hub/data/personal_profile.json`（键 = `profile_fields[].key`，缺失补 `null`） |
| 输出 | 五问判定（是/否/待定 + 依据 + 关联参数）+ 行动方案（驾照路径 / 时间线 / 预算 / 中介核验 / 核验清单） |
| CLI | `--render-panel` / `--check` / `--profile <json>` / `--out <md>` / `--json` / `--demo` |
| 退出码 | 0 成功 / 1 缺参或写入失败 / 2 `--check` 不一致（仅警告） |
| 测试 | `engine/tests/test_consulting_panel.py`（15 项）+ `test_decision_config.py` 漂移守卫扩展 |
| 不改项 | `personal_finance_model.py`、`pending_verification.py`、报告生产流程 |

## 三、验收标准

1. 面板 md 由工具确定性生成，`--check` 退出码 0；无 mtime / 随机性。
2. 17 项参数字段与 `personal_profile.md` 的 PF-01…PF-17 一一对应；固定项（PF-04/05/09/10/12/15）标「主题事实」，派生项（PF-03/14）自动算。
3. 空白输入 → 五问全「待定」；已填输入 → 至少 Q2/Q3/Q4 可判「是」；Q1 有「是 / 否 / 待定」三态用例。
4. 参考值（初期费用 / 生活成本 / 教习费 / UR 口径 / 驾照映射）读自配置，代码内无硬编码字面量（`test_decision_config` 漂移守卫覆盖）。
5. `--demo` 输出显式标注「演示用假设值，非真实个人数据」。
6. S5 双轴评审 `docs/toolchain/reviews/consulting-panel-review.md`，Standards / Spec 均无 P0/P1。
7. `unittest discover -s engine/tests` 全绿；`validate.py` 退出码 ∈ {0,2}；`coverage_gate.py` ≥80%；`cleanup_workspace.py --check` 零残留。

## 四、参考值核验结论（2026-11 外部抽查）

| 项 | 结论 | 状态 |
|---|---|---|
| 受入上限 22,100（令和 8 年 1 月 23 日阁议） | 与法务省 ISA 页一致 | 已核验 |
| 外免切替 知识/技能合格率 42.8% / 13.1% | 中文转引警察庁，原文待补 | 部分核验 |
| 初期费用 2.5–7 个月房租 | 区间成立，口径须注明含前家賃·保険 | 已核验 |
| UR 收入基准（単身 / 世帯） | 仓库仅単身口径，补世帯口径（82,500→33 万） | 已核验 |
| 中国驾照 → 日本类别 | 仅 C1/C2 可切替；B2/B1/A1/A2 须重考 | 部分核验（无官方 1:1 表） |
