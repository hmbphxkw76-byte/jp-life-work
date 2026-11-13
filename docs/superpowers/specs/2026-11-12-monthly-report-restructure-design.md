# 月度滚动报告机制改造设计

- **日期**：2026-11-12
- **状态**：待批准
- **关联**：`基线报告管理规则.md`、`内容更新周期标准.md`、`自动化更新方案.md`、`docs/superpowers/specs/2026-11-12-root-layout-reorg-design.md`（根目录整理，未实施）

## 1. 背景与目标

### 现状

| 主题 | 当前机制 | 现有文件 |
|---|---|---|
| 01 监测 | 每周一份带版本号报告 + `*_baseline.md` 周期基线，旧版入 `archives/` | `..._v2026.11.12_5.md`、`..._baseline.md`、`archives/..._v2026.11.11_3.md` |
| 02–13 知识 | `reports/` 下单份手册，原地增量回写 | `日本XX知识手册.md` |

### 问题

月内多次更新产生多份版本文件，基线轮换规则复杂，月内变更点分散在多个文件里，回溯与阅读成本高。

### 目标

- 每个自然月，每个主题只有一份报告/手册文件（`<base>_YYYY-MM.md`，`base` 为文档基名）。
- 月内所有更新追加到当月文件，并标记**时间戳 + 变更内容**。
- 新月份开始时，以上月最终内容**全量复制**为新月文件的初始基线。
- 完整保留 Web 发布链路（GitHub Actions、HTML+MD 双格式）。

## 2. 已确认决策

| 决策项 | 选择 |
|---|---|
| Web 发布链路 | **完整保留**：三个 GitHub Actions workflow、`md2html`、`build_library`、HTML+MD 双格式均不动 |
| 文件命名 | **带月份文件名**：`<base>_YYYY-MM.md`（+ 同名 `.html`） |
| 更新标记 | **可见块级标记 + 保留 `<!-- updated -->`**：MD 与 HTML 均可直观看到 |

## 3. 文件命名与归档

### 3.1 命名约定

| 主题类型 | 命名 | 示例 |
|---|---|---|
| 监测（01） | `日本特定技能司机物流监测报告_YYYY-MM.md` | `日本特定技能司机物流监测报告_2026-11.md` |
| 知识（02–13） | `日本XX知识手册_YYYY-MM.md` | `日本司机职业知识手册_2026-11.md` |

- HTML 由 `md2html.py` 生成同名 `.html`。
- `schedule.json` 的 `target` 统一为 `reports/` 目录（监测主题已是目录）；工具按 `_YYYY-MM` 后缀解析当月文件。

### 3.2 归档

- 当月文件位于 `reports/` 顶层。
- 跨月时旧月份文件移入 `reports/archives/`，保留月份名。

### 3.3 路径兼容性

- 目录结构不变：`data/`、`prompts/`、`reports/`、`reports/archives/`。
- 跨主题相对链接不变。
- `index.html` / `library.html` 重新生成后链接到当月文件。
- 直接文件路径随月份变化（旧路径失效）——这是「带月份文件名」的固有结果；访问入口以聚合页为准。

## 4. 月度滚动机制

### 4.1 月内更新

- 同一自然月内，所有更新追加到当月文件，**不新建文件**。
- 每次更新插入可见标记（时间戳 + 变更摘要）。

### 4.2 跨月滚动

- 新月份首份更新前，执行 `archive_reports.py rollover`：
  1. 找到当前最新月份文件；
  2. 若其月份 < 当前月份（JST）：全量复制为 `<base>_<当前月份>.md`，并更新头部元数据（版本、数据基准日、月份）；
  3. 旧文件移入 `archives/`；
  4. 重新生成 HTML。
- 若月份相同：无操作。

### 4.3 12 月基线

- 2026-12 初始报告 = 2026-11 最终报告的全量同步（含内容与标记）。

## 5. 增量标记格式

### 5.1 源文档标记

```
<!-- updated: 2026-11-12 | 本次变更摘要 -->
> 🆕 **2026-11-12 更新**：本次变更摘要
```

- 注释：供 `build_library.py` 解析为 HTML 徽标（沿用现有 section/block 逻辑）。
- 可见标记：MD 与 HTML 中均可见，块级引用样式。

### 5.2 放置规则

- 章节级更新：标记置于章节标题前（section 模式）。
- 块级更新：标记置于块前（block 模式）。

### 5.3 校验

- `validate.py` 校验注释语法、可见标记语法、时间戳格式。

## 6. 现有文件迁移

### 6.1 01 监测报告

- `..._v2026.11.12_5.md` → `日本特定技能司机物流监测报告_2026-11.md`（取最新内容）。
- 为 11 月内两次更新（11-11、11-12）补可见标记（依据「本次更新重点」「已修正事实清单」）。
- `*_baseline.md` 退役（见 §7）。
- `archives/..._v2026.11.11_3.md` 保留。

### 6.2 02–13 知识手册

- `日本XX知识手册.md` → `日本XX知识手册_2026-11.md`。
- 为 11 月的合并整理补可见标记（如适用）。

### 6.3 HTML

- 全部重新生成。

## 7. 基线机制处置

- 「周期滚动基线」被月度滚动取代：**上月报告即本月基线**。
- 退役 `*_baseline.md` 文件与 `archive_reports.py rotate-baseline` 子命令。
- `基线报告管理规则.md` 改写为「月度报告管理规范」。

## 8. 工具链适配

| 工具 | 改动 |
|---|---|
| `update_scheduler.py` | 新增 `current_document(topic)` 解析当月文件；`latest_report` / `topic_version` / 看板 / 工单链接改用解析结果 |
| `build_library.py` | `resolve_topic_source` 用解析结果；`collect_report_editions` 解析 `_YYYY-MM`；`build_month_reports` 适配 |
| `validate.py` | `check_single_doc` 改为「当月一份」；`check_update_markers` 校验可见标记 |
| `archive_reports.py` | 新增 `rollover` 子命令；`apply` 适配月份命名；`rotate-baseline` 退役 |
| `md2html.py` | 无需改动（通用转换） |
| `merge_topics.py` | 输出改为当月文件名（或标注为一次性工具） |
| `schedule.json` | `target` 改为 `reports/` 目录 |

## 9. 提示词与文档适配

- `prompts/通用基座/prompt-generic-base.md`：输出路径、标记格式。
- `prompts/知识库主题更新/prompt-knowledge-topic-update-template.md`：「单份手册」→「单月单份」。
- `prompts/职业就业调研/prompt-employment-research-template.md`、`prompts/市场指标监测/prompt-monthly-monitor-template.md`：命名与滚动。
- 13 个主题 prompt：路径与约定。
- 根目录 4 份规范文档 + `README.md`：更新。

## 10. GitHub Actions

- 三个 workflow 逻辑不动（均为通用工具调用）；工具适配后自动生效。

## 11. 验证

- 目录结构完整（13 主题 + prompts + docs）。
- 每个主题 `reports/` 当月仅一份 md + 同名 html。
- 标记可追溯（时间戳 + 摘要）。
- `validate.py` 全通过；`build_library.py --check` 通过。
- 12 月 rollover 逻辑正确（以 11 月最终内容为基线）。

## 12. 开放问题

1. 工作区有大量未提交改动（提示词打磨 + HTML 重生成），是否先提交为基线再动工？
2. `merge_topics.py` 是否保留（章节已合并完毕）？
3. 月末归档由 `rollover` 自动完成还是手动触发？
