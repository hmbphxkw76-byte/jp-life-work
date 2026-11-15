# 赴日决策仪表盘 · 报告操作指引（Agent 可执行版）

> **适用范围**：`00-decision-hub` 的季度复核 / 事件触发复核 / 落地清单 / 定居地档案。
> **单一事实源**：业务参数以 [prompts/business-config.md](./prompts/business-config.md) 为准；事实与数据一律引用 01–13 主题报告 / 登记册。

---

## 0. 通用规定

### 0.1 目录速查

| 资产 | 路径 |
|---|---|
| 业务参数 | `00-decision-hub/prompts/business-config.md` |
| 指标登记册（状态 / 引用 / 缺失） | `00-decision-hub/data/decision_hub_registry.md` |
| 季度复核报告 | `00-decision-hub/reports/{{YYYY-MM}}-<slug>.md` |
| 落地清单 | `00-decision-hub/reports/{{YYYY-MM}}-decision-hub.md` |
| 定居地档案 | `00-decision-hub/reports/{{YYYY-MM}}-decision-hub.md` |
| 工具链 | `src/prompts-tools/tools/` |

### 0.2 前置检查

```powershell
python src/prompts-tools/tools/validate.py
python src/prompts-tools/tools/lint_reports.py
```

---

## 1. 季度复核

- **入口**：按[业务配置第六节](./prompts/business-config.md)的触发器判定；无触发不启动。
- **运行变量**：`{{CADENCE}}` = 季；`{{OUTPUT_PATH}}` = `reports/{{YYYY-MM}}-<slug>.md`。
- **执行步骤**：
  1. 读取 01–13 各主题最新一期报告 / 登记册；
  2. 逐项刷新五问（结论 / 来源 / 缺失）；
  3. 更新登记册「五问指标状态表」与「暴露的缺失清单」；
  4. 落盘 md + HTML，过 lint。
- **结果验证**：`lint_reports.py`；人工核对五问均有来源标注、缺失项显式标记。

---

## 2. 事件触发复核

- **触发**：个人情况变化（家属 / 资金 / 日语 / 时间窗口）或来源主题重大更新。
- **输出**：`reports/{{YYYY-MM}}-decision-hub.md`。
- **范围**：只刷新受影响的问题，其余不动。

---

## 3. 落地清单与定居地档案

- **落地清单**：随 14-life-operations 等专题的补全而增量更新；每次更新在文末版本记录留痕。
- **定居地档案**：确定居住地后复制改名填写；个人记录与事实分离。

---

## 4. Agent 执行约定

1. **不新增一手来源**：只引用 01–13；缺失标「⚠ 缺失」，不补值、不外推。
2. **防回退**：来源主题的已修正事实清单须继承。
3. **边界**：不给硬性 Go/No-Go、不给投资评级；只给「条件 → 判读 → 框架性含义 → 风险提示」。
4. **留痕**：五问状态与缺失清单逐次更新。

---

## 5. 落盘后审计（提交前必做）

```powershell
python src/prompts-tools/tools/audit_preflight.py --report <报告相对路径>
python src/prompts-tools/tools/audit_check.py --report <报告相对路径>
python src/prompts-tools/tools/audit_pipeline.py --submit --report <报告相对路径>
```

- [ ] 审计自检（preflight / audit_check）无 P0/P1，且已 `audit_pipeline --submit` 提交初审

---

## 6. 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-14 | 初始版本 | 建立跨主题决策层操作指引 |
