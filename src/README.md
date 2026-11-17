# src/ 引擎层文档治理总纲

> **定位**：`src/` 是 jp-life-work 的引擎层（工具链 / 模板 / 词汇 / 审计 / 检索 / 测试）。
> 本文件是 `src/` 下全部文档的**治理总纲**与**索引**，规定文档分层、命名规范、目录分类、
> 版本更新机制与维护纪律，确保文档与代码实况一致、无冗余、无失效引用。
>
> **上位依据**：`AGENTS.md`（会话硬性规约）、`docs/信息生产全链路执行规范.md`（PIPELINE-FLOW-SPEC）、
> `docs/审计报告标准化管理体系.md`（AuditGuard）。本文件只约束 `src/` 范围，不跨 repo。

---

## 一、目录分类规则

| 目录 | 职责 | 文档形态 | 单一事实源 |
|---|---|---|---|
| `src/report_templates/` | 报告模板通用层（跨类型共享） | 通用基座 / 规范 / 注册表 / 13 个类型目录 | 本目录根部文件 |
| `src/prompts-tools/tools/` | CI 工具链 | `README.md`（工具说明）+ `registry.json`（快照） | 工具代码本身 |
| `src/vocabulary/` | 动态词汇库 | `README.md`（SOP）+ `INDEX.md`（索引）+ `data/*/terms.md` | `config/topics.json` + `terms.md` |
| `src/search/` | 五问检索索引 | `*.json`（源） | `question-index.json` 等 |
| `src/report-audits/` | 审计留痕 | 台账 + 生成物（见 `report-audits/README.md`） | `audit/audit-ledger.jsonl` 等 |
| `src/tests/` | 守卫测试 | `test_*.py`（文档数字 / 注册一致性 / 命名守卫） | 代码实测 |

**分类原则**：新增文件前先归位到上表某目录；跨目录内容不复制，用链接引用。

## 二、文档分层

| 层 | 定义 | 维护方式 | 处置 |
|---|---|---|---|
| **活文档** | 人工维护的 SOP / 规范 / 注册表 / 说明 | 手工修订 + 版本记录 | 修订须同步 `src/tests/` 守卫 |
| **生成物** | 工具从数据源渲染（`INDEX.md` / `*-report.md` / `registry.json` / `status.md` 等） | 脚本生成，**勿手工编辑** | 数据源变更后重跑生成器；正文漂移直接删除重生成 |
| **工作文件** | 一次性导入留痕 / 运行缓存 | 脚本读写 | 按各自规则保留（如 `vocabulary/data/*/imports/` 永久留痕） |
| **历史归档** | 一次性任务留痕 / 已完成方案 / 已迭代版本 | 不维护 | 完成即清理或归档；**无引用即删** |

> **判定顺序**：先查引用（`grep` 全仓，排除 `.worktrees/` `.git/`）→ 无引用且非生成物/工作文件 → 历史归档，删除。

## 三、命名规范

| 对象 | 规则 | 示例 |
|---|---|---|
| 通用规范文档 | `<主题>-standard.md` 或 `<主题>-spec.md` | `handbook-split-standard.md` |
| 类型注册表 | 固定 `template-registry.md` | — |
| 类型模板 | `prompt-<cycle>-template.md`（类型目录内） | `prompt-monthly-monitor-template.md` |
| 泛用版业务提示词 | `prompt-<cycle>.md`（类型目录 `prompts/` 内） | `prompt-baseline-setup.md` |
| 脚手架 | 固定 `business-prompt-scaffold.md`（类型目录内） | — |
| 词汇库 | 固定 `terms.md`；索引 `INDEX.md`；SOP `README.md` | — |
| 工具说明 | 固定 `README.md` + `registry.json` | — |
| 审计报告 | `<工具名>-report.md`（生成物，json 为源） | `audit-check-report.md` |
| 一次性历史报告 | `<主题>-<YYYY-MM>.md`（原则上不新增，直接归档或删除） | 已清理 |

**通用约定**：文件名 kebab-case（中文文档标题可用中文）；同一对象在 `src/` 内只保留一份，避免镜像（历史镜像 `src/search/question-index.md` 已删除，只留 `.json`）。

## 四、版本更新机制

1. **版本记录**：活文档末尾保留「版本记录」表（版本 / 日期 / 变更 / 说明）；结构性修订递增版本号。
2. **易变数字单一事实源**：工具数、测试数、工作流数、类型数、主题数、词条数等**以代码实测为准**，文档不硬编码；受守卫的数字（`docs/CI.md`、`tools/README.md` 工具表、`template-registry.md` 第二节）由测试双向锁定。
3. **生成物标记**：生成物头部注明「自动生成 · 勿手工编辑」；数据源变更后重跑生成器，不手改。
4. **规范修订联动**：修改规范类文档（注册表 / 规范 / 命名）须同步 `src/tests/test_tools.py`、`test_arch_guard.py` 对应守卫；提交前跑 `validate.py` 与全量 `unittest`。
5. **一致性巡检**：每次文档治理或月度维护时，执行「引用检查 + 分层归类 + 计数核对」，清理失效项。

## 五、文档索引

| 文档 | 层级 | 说明 |
|---|---|---|
| `src/README.md` | 活文档 | 本文件（治理总纲） |
| `src/report_templates/prompt-generic-base.md` | 活文档 | 通用基座（第一层继承） |
| `src/report_templates/monitoring-common-spec.md` | 活文档 | 渲染 / 排版 / 交付规范 |
| `src/report_templates/template-registry.md` | 活文档 | 类型注册表（13 类） |
| `src/report_templates/report-classification.md` | 活文档 | 六族十三类选型参考 |
| `src/report_templates/registry-schema.md` | 活文档 | 指标登记册 Schema |
| `src/report_templates/fact-card-standard.md` | 活文档 | 事实卡片标准 |
| `src/report_templates/l5-semantic-review.md` | 活文档 | L5 语义复核提示词 |
| `src/report_templates/handbook-split-standard.md` | 活文档 | 知识手册拆分规范 |
| `src/report_templates/<类型ID>/*` | 活文档 | 13 类模板 + 泛用版提示词 + 脚手架 |
| `src/prompts-tools/tools/README.md` | 活文档 | 工具链使用说明 |
| `src/prompts-tools/tools/registry.json` | 生成物 | 工具 / 类型 / 主题 / 工作流快照 |
| `src/vocabulary/README.md` | 活文档 | 词汇库 SOP |
| `src/vocabulary/INDEX.md` | 生成物 | 全主题词汇索引 |
| `src/vocabulary/data/*/terms.md` | 工作文件 | 结构化词库（脚本托管，勿手改） |
| `src/report-audits/README.md` | 活文档 | 审计留痕分层说明 |
| `src/report-audits/**` | 台账 + 生成物 | 见该目录 README |
| `src/search/*.json` | 源数据 | 五问检索索引 |
| `src/tests/test_*.py` | 活文档（代码） | 文档守卫测试 |

## 六、维护纪律

- 只提交本任务范围内文件；发现他人未完成改动原样保留。
- 删除文档前必须全仓 grep 确认零引用（含 `docs/` 外部引用）；生成物另确认工具可重生成。
- 不跨 repo 修改；`src/` 内文档口径以上位规范为准，冲突时以上位规范为准并互相引用而非复制。


## 七、版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-17 | 初始版本 | 建立 src/ 文档治理总纲：目录分类 / 四层文档分层 / 命名规范 / 版本更新机制 / 文档索引 / 维护纪律 |
