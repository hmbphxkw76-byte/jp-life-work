# prompts/tools 使用文档

CI 工具链使用说明。所有工具基于仓库根目录相对路径运行（自动定位仓库根），
在仓库根目录执行即可；通用层 + 业务层（`{地区}/{物业类型}/`）结构见
[report_templates/prompt-generic-base.md](../../report_templates/prompt-generic-base.md) 第 1.1 节。

## 环境准备

```bash
pip install -r requirements.txt   # openpyxl + markdown
python -m unittest discover -s tests -v   # 单元测试（47 项）
```

## 退出码约定（校验类工具统一）

| 退出码 | 含义 | CI 行为 |
|---|---|---|
| 0 | 通过（含空清单 / 无可处理项） | 继续 |
| 1 | 存在错误项 | 阻断 |
| 2 | 仅警告项 / 需人工确认 | 不阻断 |

## 工具一览

| 工具 | 类别 | 对应 CI 工作流步骤 |
|---|---|---|
| validate.py | 校验 | ci.yml / scheduled-maintenance「规范校验」 |
| lint_reports.py | 校验 | ci.yml / scheduled-maintenance / content-update「报告内容校验」 |
| compliance_check.py | 校验+引导+审计 | ci.yml / content-update「报告模板合规校验」；scheduled-maintenance「报告合规性审计」 |
| classify_reports.py | 校验+修复 | scheduled-maintenance / content-update「报告自动归位」 |
| ensure_region_topics.py | 校验+修复 | ci.yml / scheduled-maintenance「结构补全」 |
| md2html.py | 生成 | html-sync / scheduled-maintenance「HTML 同步」 |
| archive_reports.py | 生成 | scheduled-maintenance「归档策略」 |
| build_index.py | 生成 | scheduled-maintenance「生成全局索引」 |
| build_hub.py | 生成 | ci.yml --check / html-sync、scheduled-maintenance「汇总页」 |
| update_planner.py | 编排 | content-update「生成任务清单」 |
| automation_status.py | 编排 | content-update / scheduled-maintenance「状态记录与活跃度」 |

## 校验类

### validate.py — 结构与规范校验

```bash
python prompts/tools/validate.py
```

检查项：通用层根部 3 份共享文件齐全（`prompt-generic-base.md` / `monitoring-common-spec.md` /
`template-registry.md`）；各类型模板目录必备文件齐全（`market-monitoring/`、
`employment-research/`，清单见 `_common.TEMPLATE_TYPE_DIRS`，与
[report_templates/template-registry.md](../../report_templates/template-registry.md) 第二节登记一致）；
通用层全目录（含类型子目录）无业务关键词
（迪拜/公寓/Dubai/UAE/DLD/CBUAE/EIBOR 等，清单见 `_common.BUSINESS_KEYWORDS`）；
业务线目录结构（`prompts/business-config.md` 及其 `{{REGION}}/{{TOPIC}}/{{REGISTRY_PATH}}`
变量区）；`reports/` 内文件命名符合约定。

### lint_reports.py — 报告内容校验

```bash
python prompts/tools/lint_reports.py
```

扫描全部业务线 `reports/*.html`。**错误项（退出码 1）**：thead/tbody/table 标签不配对、
重复 `</tbody>`、畸形 `<th scope="col"ead>`、缺免责声明（须含「免责声明」节 +
「不构成投资建议」表述，兼容两种固定原文措辞）。**警告项（退出码 2）**：
≥6 列表格 `<th>` 未声明百分比列宽、表格缺 `class="fixed"`、`<img>` 缺 alt。
纯函数 `lint_html(text)` 可被测试直接调用。

### compliance_check.py — 报告模板合规校验 / 模板引导 / 合规审计

校验规则与 12 类报告类型模板骨架一一对应，规则文件为
[report_templates/compliance-rules.json](../../report_templates/compliance-rules.json)
（与 [template-registry.md](../../report_templates/template-registry.md) 第二节登记一致；
周期未单独登记的类型按「结构逐字继承基线」回落校验）。报告类型自动识别：读取业务线
`prompts/business-config.md` 继承声明中的 `report_templates/<类型ID>/` 引用。

```bash
python prompts/tools/compliance_check.py --check        # 全量校验（CI 阻断式关卡）
python prompts/tools/compliance_check.py --file <路径>   # 校验单份报告（开发自查）
python prompts/tools/compliance_check.py --list-types   # 列出已注册类型与模板引用入口
python prompts/tools/compliance_check.py --scaffold market-monitoring monthly   # 模板自动填充引导
python prompts/tools/compliance_check.py --audit        # 历史报告合规审计（写审计报告，不阻断）
```

**校验口径**（结构完整性 / 必填字段 / 内容格式三类）：

- **错误项（阻断合并）**：h2 节数少于类型模板骨架（结构缺失）、章节编号 `id="sN"`
  不连续或不有序、缺 `<title>`、缺「免责声明」节或「不构成投资建议」表述、
  月/季/年周期报告缺顶部导航、锚点 `href="#x"` 无对应 id（断头锚点）。
- **警告项（不阻断）**：h2 节数超出骨架（如为业务固化锚需人工确认）、基线报告缺简化
  锚点导航、文件名不符合命名约定（无法识别周期）、业务线未注册类型。
- `--audit` 对全部历史报告执行同口径校验，匹配度汇总与逐项明细写入
  `report-audits/compliance-audit.md`（定时维护提交留痕），发现不符合项退出码 2 并转
  预警 Issue，不阻断维护流水线。
- 纯函数 `check_report(text, rule, common)` / `detect_type(config_text)` /
  `cycle_rule(rules, type_id, cycle)` 可被测试直接调用。

### classify_reports.py — 报告自动归位

```bash
python prompts/tools/classify_reports.py --check --unknown-warn   # 只检查
python prompts/tools/classify_reports.py --apply --unknown-warn   # 执行移动
```

扫描散落在业务目录之外（仓库根、`report_templates/` 全目录含类型子目录）的报告文件，
按文件名中地区/业务类型词判定归属并移入对应业务线 `reports/`；无法判定归属的报警告警
（`--unknown-warn` 时退出码 2）。

### ensure_region_topics.py — 结构补全（幂等）

```bash
python prompts/tools/ensure_region_topics.py --check   # 只报告缺失
python prompts/tools/ensure_region_topics.py           # 创建缺失子目录
```

为每条业务线补齐 `prompts/`、`reports/`、`data/` 三个子目录；缺
business-config.md 时告警。重复执行无副作用。

## 生成类

### md2html.py — md → HTML 同步

```bash
python prompts/tools/md2html.py
```

将业务线 `reports/*.md` 转换为同名自包含 HTML（内置样式：表格边框、图片自适应）。
纯图表型简报（只出 HTML 的业务线）无 md 源时自动跳过。依赖 markdown 包。

### archive_reports.py — 滚动归档（幂等）

```bash
python prompts/tools/archive_reports.py
```

每类报告保留最新 N 期（monthly 12 / quarterly 8 / annual 5 / baseline 3），
超出部分移入业务目录内 `reports/archives/`。保留策略为纯函数
`select_archives(items, keep_map)`。

### build_index.py — 全局索引

```bash
python prompts/tools/build_index.py
```

按业务线汇总全部报告，生成根目录 `INDEX.md`（含「最近生成」时间戳，作为
content-update 工作流的活跃度心跳）。

### build_hub.py — 汇总页

```bash
python prompts/tools/build_hub.py          # 生成 index.html + reader.html
python prompts/tools/build_hub.py --check  # 校验是否为最新
```

`index.html` 为主题报告索引（自包含静态页，可直接 file:// 打开；**无顶栏**，进入主题后靠左侧「← 返回主题总览」回首页）：
- Hero 只保留居中标题 + 统计行（主题数 / 报告总数）；
- 主题卡片总览（编号 / 类型 / 简介 / 报告数 / 最新报告），支持关键词搜索与类型筛选；
- 点击「进入主题」进入该主题的报告列表（hash 路由 `#topic-<slug>`，左侧 266px 主题导航），
  报告按时间倒序排列，默认只展示近 1 年（窗口由浏览器端按查看日期动态计算），
  可一键展开更早报告；无 JavaScript 时全部内容平铺可用。
- 主题与报告均按目录自动发现（`iter_business_dirs` + `reports/*.html`，含插刷件等
  非标准命名），新增主题 / 报告后重新生成即自动扩展；主题显示名与简介取自
  `src/vocabulary/config/topics.json`，类型名取自 `src/report_templates/template-registry.md`。
  完全空白的骨架目录（无报告且无 business-config）不占位，待其有内容后自动出现。

`reader.html` 为阅读壳（侧栏 + iframe，`?report=<路径>` 直达）。
`--check`：过期退出码 1；文件缺失（全新克隆）退出码 0 并提示，由定时维护首建。
比对前对两侧做归一化——抹平「最近生成」生成时刻时间戳（分钟级心跳，不参与最新性判定），
其余部分逐字节比对。

## 编排类

### update_planner.py — 内容更新任务清单

```bash
# porcelain JSON（content-update 工作流用于判断清单是否为空）
python prompts/tools/update_planner.py --porcelain --pending-only > tasks.json
# 人读 md 清单
python prompts/tools/update_planner.py --pending-only > tasks.md
# 限定项目 / 周期
python prompts/tools/update_planner.py --project dubai/apartment --period 2026-Q4
```

- `--period` 接受 `YYYY-MM` / `YYYY-Qn` / `YYYY`；缺省按当前 UTC 日期推导
  （季首月用季度标识，与工作流逻辑一致）。
- 周期推导规则：月度期 → 月度任务；季首月追加季度任务；1 月追加上一自然年年度任务。
- 任务状态：期望输出（如 `reports/2026-12_monthly.html`）已存在 → done，否则 pending；
  `--pending-only` 只留 pending。参数错误退出码 2。

### automation_status.py — 自动化状态与活跃度

```bash
# 记录一次执行（工作流 always 步骤调用）
python prompts/tools/automation_status.py record --phase content-update \
    --result success --run-url "<运行链接>"

# 活跃度检查（scheduled-maintenance 用于 >45 天预警）
python prompts/tools/automation_status.py activity --threshold 45 --porcelain   # 输出天数或 unknown
python prompts/tools/automation_status.py activity --threshold 45               # 人读说明
```

状态写入根目录 `automation-status.json`（追加式，工作流提交）。

## 常见场景速查

| 场景 | 命令 |
|---|---|
| 提交前本地自查 | `validate.py && lint_reports.py && compliance_check.py --check && build_hub.py --check` |
| CI 报「汇总页已过期」 | 运行 `build_hub.py` 重新生成后提交 |
| CI 报 lint 错误 | 按 `[E] 文件: 原因` 修复报告 HTML（多为标签不配对 / 缺免责声明） |
| CI 报模板合规错误 | 按 `[E] 文件: [类型/周期] 不符合项` 对照类型模板补齐（结构缺失 / 必填字段 / 断头锚点） |
| 新报告开写前取骨架 | `compliance_check.py --scaffold <类型ID> [周期]` 输出骨架与自检要点 |
| 查历史报告合规匹配度 | `compliance_check.py --audit` 后看 `report-audits/compliance-audit.md` |
| 新增业务线后首跑 | `ensure_region_topics.py` → 补 business-config.md → 首期基线报告 |
| 手动补跑月度任务清单 | `update_planner.py --project dubai/apartment --period 2026-12` |

## 注意事项

- 所有路径均为仓库内相对路径，业务线整体迁移（改目录名）不影响工具运行。
- `archive_reports.py` 会移动历史报告到 `reports/archives/`——基线是对比锚，
  保留策略已含 baseline 3 份；如需永久保留请自行调整 `_common` 之外的 KEEP 表。
- lint 的免责声明检查兼容两种固定原文（历史报告「以上内容基于公开数据…」与
  通用模板「本报告仅供参考…」），两种都判合格。
