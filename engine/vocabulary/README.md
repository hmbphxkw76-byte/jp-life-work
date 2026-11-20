# 词汇库子系统（vocabulary）· 标准操作流程（SOP）

> **一句话定位**：仓库级、主题无关的标准化动态词汇子系统，位于 `engine/vocabulary/`。当前登记 **20 个主题、1612 条词条**（每主题 6–7 个受控分类），经交叉校验覆盖各业务线核心指标词，并同步至 **20 条业务线**的 `prompts/business-config.md`。新增任意领域词汇仅需执行一条 `topic-add` 命令，**零代码修改**。

---

## 一、架构与目录

```
engine/vocabulary/
├── README.md                          # 本文件：标准操作流程（SOP）与扩展规范
├── INDEX.md                           # 全主题索引（index 命令自动生成，勿手工编辑）
├── config/
│   ├── topics.json                    # 主题注册表（脚本托管，单一事实源）
│   ├── sync.json                      # 词库 → 业务提示词同步绑定配置
│   ├── verify-exemptions.json         # verify/check 显式豁免清单（B4）
│   └── verification-retention-map.json # 部分核验「分类 → 保留口径」映射（B3）
├── script/                            # 组件目录：主题无关的实现代码
│   ├── vocab_tool.py                  # 核心脚本（仅依赖 Python 标准库）
│   └── sync_vocab.py                  # 同步脚本（标记区间保护 + 增量检测 + 回滚）
├── schema/                            # 类型定义目录：导出数据契约
│   └── export.schema.json             # JSON Schema（JSON / JSONL 字段类型定义）
├── templates/                         # 模板目录：新增主题时复用的文件模板
│   └── topic-import-template.md       # 词汇导入文件模板（6 列格式契约）
└── data/                              # 数据文件目录：每主题一个子目录
    ├── <topic>/                       # 由 topic-add 自动创建，按主题隔离
    │   ├── terms.md                   # 结构化存储（9 列 md-table 契约，脚本统一读写）
    │   ├── imports/                   # 批量导入文件暂存（永久留痕）
    │   └── exports/                   # 导出产物（json / csv / jsonl，供上层对接）
    └── …                              # 现有主题：20 个（与 01–20 业务线对应）
```

### 1.1 目录职责映射

| 需求维度 | 目录 | 职责 | 扩展方式 |
|---|---|---|---|
| 按主题分类的子目录 | `data/<topic>/` | 主题词库、导入留痕、导出产物 | `topic-add` 一条命令自动创建，无需改代码 |
| 组件目录 | `script/` | 主题无关的工具实现与共享逻辑 | 新增功能时加脚本并保持无主题硬编码 |
| 数据文件目录 | `data/` | 全部结构化数据与运行留痕 | 仅通过脚本读写，禁止手工编辑 `terms.md` |
| 类型定义目录 | `schema/` | 导出数据契约（字段、类型、格式约束） | 契约变更时同步更新 Schema 与 README 第六节 |
| 配置目录 | `config/` | 主题注册表、同步绑定 | `topic-add` / `topic-remove` / `sync.json` |
| 模板目录 | `templates/` | 新增主题/导入文件的复用模板 | 新增模板按 `<用途>-template.<ext>` 命名 |

### 1.2 文件命名约定

| 对象 | 约定 | 示例 |
|---|---|---|
| 主题 ID（目录名） | `NN-slug`，与根目录 `00–20` 主题编号一一对应 | `01-ssw-driver`、`07-economy-finance` |
| ID 前缀 | 2–4 位大写字母，全局唯一 | `SSW`、`ECON`、`LOG` |
| 词库文件 | 固定 `terms.md` | `data/01-ssw-driver/terms.md` |
| 导入文件 | `YYYY-MM-DD_<说明>.md`（也支持 `.csv` / `.json`） | `2026-11-13_seed-economy.md` |
| 导出产物 | `{topic}_{YYYY-MM-DD}_export.{json,csv,jsonl}` | `economy_2026-11-13_export.json` |
| 脚本 | 小写 snake_case + `.py` | `vocab_tool.py` |
| Schema | 小写 + `.schema.json` | `export.schema.json` |
| 模板 | `<用途>-template.<ext>` | `topic-import-template.md` |

**三层解耦设计**（主题与实现完全分离的保证）：

| 层 | 载体 | 职责 | 变更频率 |
|---|---|---|---|
| 配置层 | `config/topics.json` | 主题 ID、名称、ID 前缀、三类路径、受控分类词表 | 新增领域时改这里（唯一） |
| 实现层 | `script/vocab_tool.py` | init/import/check/tag/export/index/verify 全部逻辑，不含任何主题知识 | 极少（功能演进才改） |
| 数据层 | `data/<topic>/` | 词库存储、导入留痕、导出产物 | 每次词汇更新 |

**核心不变量**：脚本代码中不出现任何主题名、分类名、词条内容；数据文件中不出现流程逻辑。二者仅通过 `topics.json` 连接。

## 二、快速开始（20 主题词库已就位）

```powershell
python engine/vocabulary/script/vocab_tool.py topics                                          # 查看已注册主题
python engine/vocabulary/script/vocab_tool.py check --topic 01-ssw-driver                        # 质量校验（当前 109 条，0 错误 0 警告）
python engine/vocabulary/script/vocab_tool.py export --topic 01-ssw-driver --format all          # 一键导出 json/csv/jsonl
python engine/vocabulary/script/vocab_tool.py index                                           # 重新生成全主题索引
```

## 三、全链路标准操作流程（六步）

所有命令在仓库根目录执行；退出码约定（对齐 `engine/tools` 工具链）：**0=通过，1=错误（阻断），2=警告（有产出但有瑕疵）**。

### S1 词汇收集

| 项 | 规范 |
|---|---|
| 来源要求 | 对齐仓库来源分级：官方一手优先；无法当场核验的来源填「需核实原文」；每条必须有来源（缺失时 import 自动补标「需核实原文」并告警） |
| 文件落位 | 导入文件放 `data/<topic>/imports/`，命名 `YYYY-MM-DD_说明.md`（或 `.csv` / `.json`） |
| 格式契约 | 6 列：`词条 / 别名 / 分类 / 标签 / 定义 / 来源`（表头中英文均可识别）；别名与标签用半角分号 `;` 分隔；单元格内禁止竖线与换行 |
| 增量语义 | import 天然增量：已存在的词条/别名自动跳过并计数，可安全重跑（幂等） |

**校验标准**：每条必须有词条、分类、定义三要素，否则该行计为无效并告警；import 汇总「新增 / 跳过重复 / 无效」三计数。

### S2 分类归档

| 项 | 规范 |
|---|---|
| 分类 | 必须取自 `topics.json` 该主题的 `categories` 受控词表；词表调整属配置层变更，随主题演进维护 |
| 标签 | 自由自定义（自定义标签分类），分号分隔，一个词条建议 1–3 个；用 `tag` 命令增删 |
| 归档 | 导入文件永久保留在 `imports/` 作为来源留痕，不删除 |

**校验标准**：`check` 对分类越界（不在受控词表）给警告（exit 2），不阻断；正式发布前警告应清零或确认合理。

### S3 去重校验

| 项 | 规范 |
|---|---|
| 归一化规则 | NFKC 折叠 + 空白折叠（多空格合一）+ 忽略大小写 + 全角分号折半 |
| 唯一性范围 | **词条 + 全部别名**共同构成全局唯一索引；词条与自身别名重复视为冗余（警告），跨条目冲突视为错误 |
| 双重防线 | import 时逐条比对已有索引，冲突即跳过（exit 2）；`check` 全库扫描兜底，跨条目重复=错误（exit 1 阻断） |

**校验标准**：`check` 报告「0 项错误」方可交付；冗余别名警告应清理。

### S4 结构化存储

| 项 | 规范 |
|---|---|
| 唯一存储 | `data/<topic>/terms.md`，9 列 md-table 契约：`ID / 词条 / 别名 / 分类 / 标签 / 定义 / 来源 / 首次登记 / 最近更新` |
| ID 规则 | `{id_prefix}-{三位序号}`（如 AIS-001），脚本自动分配、递增不复用 |
| 编辑纪律 | **词汇表禁止手工编辑**——一律走 `import`（新增）/ `tag`（标签）；单元格内竖线写入时自动转全角斜杠「／」 |
| 骨架生成 | `init` 创建空词库（v1.0）与 imports/exports 目录；已存在则跳过（幂等） |

**校验标准**：`check` 校验表头契约、ID 唯一性与序号连续性（不连续仅警告）。

### S5 索引生成与上层对接

| 项 | 规范 |
|---|---|
| 全主题索引 | `index` 命令 → `engine/vocabulary/INDEX.md`（主题 × 词条数 × 分类分布 × 版本 × 存储路径），自动生成勿手工编辑 |
| 结构化导出 | `export` 命令 → `exports/{topic}_{YYYY-MM-DD}_export.{json,csv,jsonl}`；jsonl 每行一个词条对象，适合检索系统逐行摄取 |
| 对接建议 | 以词条 ID 为主键；别名与标签作索引字段；分类作过滤面；JSON 顶层含 `topic / version / generated_at / count / categories` 元数据 |

**校验标准**：每次词汇变更后重跑 `index` + `export`，保证索引与产物同步；导出文件行数 = 词条数。

### S6 版本管理

| 项 | 规范 |
|---|---|
| 词库版本 | `terms.md` 尾部「版本记录」表由脚本自动追加：init 建 v1.0，每次 import / tag 自动递增小版本号并留痕计数 |
| 配置版本 | `topics.json` 的 `version` 字段由 `topic-add` / `topic-remove` 自动递增（每次操作自动备份到 `data/topic-backups/`），并更新 `updated` 日期 |
| git 纪律 | 一次词汇变更一个 commit（含 terms.md + imports 新文件 + 重新生成的 exports/INDEX.md）；提交前 `check` 须 0 错误 |

**校验标准**：任意词条可回溯「首次登记日期 + 引入它的导入文件 + 版本记录行」三要素。

### S7 跨主题概念对齐（n23）

| 项 | 规范 |
|---|---|
| 概念映射 | `config/topics.json` 的 `concept_map`：`CONCEPT-NNN → {name, terms:[{topic,id,term}]}`，登记跨主题同概念（同名词条 / 同定义异名）；人工策划，`vocab_tool` 保留该顶层键 |
| 校验命令 | `vocab_tool.py cross-check`（`--json` 机读）：引用完整性（缺失 → 错误 rc=1）+ 同定义异名 / 同名词条未登记（rc=2，供人工登记） |
| 上层校验 | `info_quality_check` C-15（P2，复用 `cross_check_gaps()` 单一事实源）；`validate.yml` 词库校验步骤接入 |

**校验标准**：`concept_map` 引用全部可解析；新增跨主题共享概念后登记，避免同概念异名口径漂移。

## 四、新增主题扩展指南（一条命令，自动目录关联）

新增主题**无需手工编辑注册表**（topics.json 已降级为脚本托管文件），一条命令完成全部目录关联：

```powershell
python engine/vocabulary/script/vocab_tool.py topic-add --topic smart-logistics --name 智慧物流 --prefix SLG --categories "运输技术;自动化;数据平台;标准与监管" --description "智慧物流领域词汇"
```

命令自动完成（实时同步主题↔目录映射）：

1. **注册表登记**：写入 topics.json（自动备份到 `data/topic-backups/`、注册表版本号自动递增）；`--prefix` 缺省自动派生并查重。
2. **目录结构创建**：`data/<topic>/` 三件套（terms.md 词库骨架 + imports/ + exports/）；若同名目录已存在则**孤儿纳管**（不覆盖既有内容）。
3. **索引同步**：INDEX.md 自动重建。
4. **操作日志**：`data/topic-ops.log` 逐条留痕（动作 / 前缀 / 分类 / 备份文件名 / 结果）。
5. **失败回滚**：任何一步异常自动恢复注册表备份并清理本次新建目录，现有结构不受影响，给出明确错误提示。

### 4.1 新增主题的目录创建规则

| 规则 | 要求 |
|---|---|
| 创建入口 | 只能通过 `topic-add` 创建；禁止手工新建 `data/<topic>/`（手工目录会被 `topic-check` 判为孤儿，且缺少词库骨架） |
| 固定结构 | `data/<topic>/` 下必须且仅含 `terms.md` + `imports/` + `exports/` 三件套 |
| 主题 ID | 小写 kebab-case，与 `config/topics.json` 键、`data/` 子目录名三者完全一致 |
| 分类词表 | `--categories` 必须是该主题的完整受控分类，后续词条分类不得越界 |
| ID 前缀 | 2–4 位大写字母，全局唯一；缺省自动派生并查重 |
| 导入文件 | 复制 `templates/topic-import-template.md` 到 `imports/`，按 `YYYY-MM-DD_<说明>.md` 命名 |
| 新主题验收 | `topic-check` 0 错误；`check --topic <topic>` 0 错误；`index` 后 INDEX.md 出现该主题 |

### 4.2 扩展时的禁止事项

- 禁止在 `script/` 中写死任何主题名、分类名或词条内容（主题知识只能来自 `config/topics.json`）。
- 禁止手工编辑 `terms.md` 与 `topics.json`；词条变更走 `import` / `tag`，主题变更走 `topic-add` / `topic-remove`。
- 禁止删除 `imports/` 中的历史导入文件（来源留痕）；禁止把 `terms.md` 拆成多份零散文件。

辅助命令：

- `topic-check`：一致性审计（前缀冲突、注册缺目录、孤儿目录、缺分类词表），错误 exit 1 / 警告 exit 2。
- `topic-remove [--force] [--delete-data]`：移除注册（词库非空须 `--force` 确认；数据默认保留，`--delete-data` 才删除）；自动提示 sync.json 残留绑定。

⚠️ **手工维护入口已移除**：直接编辑 topics.json 或 terms.md 不再是支持的操作方式；词条级新增仍按第三节 S1 走 `import`（自动触发提示词同步，见第九节）。

## 五、命令参考

| 命令 | 参数 | 用途 | 退出码 |
|---|---|---|---|
| `topics` | `--config`（可选） | 列出已注册主题 | 0 |
| `init` | `--topic` | 创建主题目录与词库骨架（幂等） | 0 |
| `import` | `--topic` `--file` | 批量导入（增量、自动去重跳过） | 0/1/2 |
| `check` | `--topic` | 全库去重与结构校验 | 0/1/2 |
| `tag` | `--topic` `--id` `--add` `--remove` | 词条标签增删（分号分隔，可只给其一） | 0/1 |
| `export` | `--topic` `--format` `--out` | 导出 json/csv/jsonl/all | 0/1 |
| `index` | `--config`（可选） | 生成全主题索引 INDEX.md | 0 |
| `verify` | `--topic`（可选） | 全主题词库校验（重复 / 空值 / 分类 / ID 前缀 / 条目数下限） | 0/1/2 |
| `topic-add` | `--topic` `--name` `--prefix` `--categories` `--description` | 注册新主题并自动创建目录结构（备份回滚 + 日志） | 0/1 |
| `topic-remove` | `--topic` `--force` `--delete-data` | 移除主题注册（数据默认保留） | 0/1 |
| `topic-check` | — | 注册表与目录结构一致性审计 | 0/1/2 |

通用参数：`--config` 指定备用主题注册表（默认 `engine/vocabulary/config/topics.json`）；导入文件路径支持相对仓库根或 `engine/vocabulary/` 根书写。

### 5.1 显式豁免清单（config/verify-exemptions.json）

`check` 与 `verify` 的警告级项可由显式豁免清单跳过，二者口径一致（同读一份清单，由 `check_topic` 统一判定）：

- 清单结构：`exemptions[]`，每项含 `topic`（主题 ID）、`check`（检查项标识）、`reason`（豁免理由）、`evidence`（证据指针）。
- 当前仅豁免 `id_sequence_gap`（ID 序号不连续）：01-ssw-driver / 02-career-driver 因 2026-11-19 删除 22 条无法核验的 npa.go.jp 词条遗留缺号，重排会波及报告引用与生成物（证据见复核记录 §8A.5）。
- 纪律：只豁免已留痕的既有警告；新增警告默认不豁免，须先查因；新增豁免须同步更新清单与本节。
- 清单缺失 / 损坏 / 结构不符时视为无豁免，不阻断校验。

### 5.2 部分核验保留口径映射（config/verification-retention-map.json）

「部分核验」条目的「分类 → 保留口径」100% 映射表（B3）：`clusters` 定义保留簇与保留理由，`categories` 给出全部分类的归属与条数，`coverage` 记录覆盖率，`baseline` 记录工单口径与实测差异。该文件为机读事实源，供定向核验与审计使用；不改变「部分核验」状态，也不新增校验命令。

## 六、数据契约（上层系统对接）

导出 JSON 顶层结构：

```json
{
  "topic": "01-ssw-driver",
  "name": "特定技能司机",
  "version": "v1.5",
  "generated_at": "2026-11-15T15:32:23",
  "count": 109,
  "categories": {"驾驶与运输作业": 21, "在留资格与制度": 19},
  "terms": [
    {"id": "SSW-001", "term": "特定技能", "aliases": ["Specified Skilled Worker"],
     "category": "在留资格与制度", "tags": ["在留资格"],
     "definition": "…", "source": "出入国在留管理庁",
     "first_added": "2026-11-13", "last_updated": "2026-11-15"}
  ]
}
```

- **jsonl**：每行一个 `terms[]` 元素（UTF-8），适合 ES / 向量库逐行摄取。
- **csv**：与存储同列（UTF-8 BOM，Excel 直接可开），适合人工审阅。
- 字段语义以本节为准；`aliases` / `tags` 恒为数组，不存在缺省为 null 的情形。

## 七、质量标准（验收清单）

| 维度 | 标准 | 验证方式 |
|---|---|---|
| 无重复 | 词条+别名归一化后全局唯一，跨条目冲突=0 | `check`（exit 1 即存在重复） |
| 分类准确 | 全部词条分类在受控词表内，越界=0 | `check` 警告清零 |
| 字段完整 | 词条/分类/定义三要素齐全，来源非空 | `import` 无效计数=0 |
| 检索高效 | 导出 jsonl/json 可供检索系统直接摄取；ID 为主键 | `export` 产物行数=词条数 |
| 可追溯 | 每条可回溯引入文件与版本；索引同步 | `terms.md` 版本记录 + `INDEX.md` 更新时间 |
| 幂等安全 | 重复 import 零新增；init 重复执行零覆盖 | 重跑 `import`/`init` 观察输出 |

## 八、异常排查

| 现象 | 原因 | 处置 |
|---|---|---|
| import 报「词库不存在」 | 未初始化 | 先 `init --topic <主题>` |
| import 报「主题未注册」 | topics.json 无该条目 | 按第四节登记后再 init |
| 大量「与已有条目重复，已跳过」 | 重复导入同一文件 | 正常幂等行为（exit 2），确认无新增即结束 |
| check 报跨条目重复 | 不同词条的词条名/别名归一化后相同 | 判定保留方，修正导入文件重新入库（冗余方不再导入） |
| check 报「分类不在受控词表」 | categories 词表滞后于词汇演进 | 核对后二选一：改词条分类，或更新 topics.json 词表 |
| 单元格出现「／」 | 原文含竖线被自动转写 | 属预期消毒；如需保留竖线请改写措辞 |
| INDEX.md 导出时间过期 | 变更后未重跑 index | 重跑 `export` + `index` |
| topic-add 报「ID 前缀冲突」 | 自动派生前缀已被占用 | 换 `--prefix` 指定其他 2–4 位大写字母前缀 |
| topic-check 报「孤儿数据目录」 | data/ 下存在未注册目录 | 确认无用后删除，或用 `topic-add` 纳管（不覆盖既有内容） |
| topic-remove 报「词库含 N 条词条」 | 防误删保护 | 确认后加 `--force`（数据仍保留）；连数据一起删加 `--delete-data` |
| PowerShell 下 `--delete-data` 等开关传参报「缺少参数」 | PS 5.1 对连续 `--` 开关的解析怪癖 | 开关参数放命令最前，或用引号包裹（`"--delete-data"`） |

## 九、自动同步（sync_vocab.py）— 词汇库更新后自动写入业务提示词

词汇库与业务提示词的绑定由 [script/sync_vocab.py](./script/sync_vocab.py) 自动完成：词条以标记区间（`<!-- VOCAB-SYNC:BEGIN topic=... -->` … `<!-- VOCAB-SYNC:END -->`）写入目标提示词文件，**区间外内容字节级零触碰**；增量检测（逐词条 sha256 比对，仅变更条目触发写盘）、写后校验（区间完整性 + 词条覆盖 + 区间外内容与写入前逐字节一致），校验失败**自动回滚备份**。

### 9.1 部署方式（三选一或组合）

| 方式 | 操作 | 适用场景 |
|---|---|---|
| 自动钩子（默认，推荐） | 无需部署：`vocab_tool.py` 的 `import` / `tag` 成功写盘后自动调用同步（`sync.json` 的 `auto_trigger: true` 时生效） | Agent 驱动的常规词汇维护 |
| 常驻监听 | `python engine/vocabulary/script/sync_vocab.py watch`（`--interval N` 调轮询间隔，默认取配置 `watch_interval_sec`） | 词汇库可能被脚本外手段直接修改时 |
| 手动/定时 | `sync` 子命令（也是失败后的重试入口）；可挂 Schedule 定期执行 `sync` | 一次性接入、兜底对账 |

### 9.2 触发条件与配置

- 触发条件：词汇库 `terms.md` 内容发生变化（新增/修改/删除词条，含标签调整），或目标提示词区间被外部改动（结构漂移自动修复）。
- 绑定配置在 [config/sync.json](./config/sync.json)：`bindings[].topic`（须已在 topics.json 注册）、`targets[].path`（目标提示词，相对 vocabulary/ 根）、`insert_before`（区块缺失时的插入锚点，须为目标文件内唯一文本）、`format`（`digest` 按分类紧凑速览 / `table` 三列表格）、`categories_include` / `tags_include`（可选过滤，空 = 全量）。
- 新增绑定只需在 `sync.json` 追加一个 target；词汇库侧零改动。

### 9.3 校验与数据安全

- 同步前：`check` 输出「新增 / 修改 / 删除」逐条差异（含词条名），不写盘。
- 同步后：回读磁盘验证标记配对、词条全覆盖、区间外内容与写入前逐字节一致；任一失败自动回滚到 `data/sync-backups/` 备份（每目标保留最近 `backup_keep` 份）。
- 写入采用临时文件 + 原子替换（os.replace），不存在半写状态；保留原文换行风格（CRLF/LF 自适应）。
- 全部动作追加记录到 `data/sync.log`；同步状态（逐词条 hash）存 `data/sync-state.json`。

### 9.4 常见问题排查

| 现象 | 原因 | 处置 |
|---|---|---|
| `未找到插入锚点「…」` | 目标文件被重构，`insert_before` 文本不再存在 | 更新 sync.json 锚点后重试 `sync` |
| `结构漂移待修复` | 区间被手工编辑或部分删除 | 直接重跑 `sync`，脚本自动整块重写修复 |
| 自动同步提示「未成功（exit 1）」 | 见 `data/sync.log` 中 `[error]` 行 | 修复后手动重试：`sync_vocab.py sync --topic T` |
| `词条未覆盖 N 条`（verify） | 词汇库在同步后又变更 | 重跑 `sync` |
| 首次接入业务线 | 目标尚无标记区间 | 配置 `insert_before` 后跑一次 `sync`（自动插入区块）；并在目标文件版本记录人工登记机制接入（如 business-config v1.2） |
| 想临时停用自动同步 | — | `sync.json` 设 `auto_trigger: false`（watch/手动 sync 不受影响） |

### 9.5 已接入绑定

20 个主题与 01–20 业务线一一绑定，均写入各自 `prompts/business-config.md` 的版本记录之前；2026-11-13 首次写入并通过 `verify`（区间外内容逐字节一致），后续新增主题（14–20）随接入同步。

| 业务线 | 词汇库主题 | 目标提示词 | 区块标题 |
|---|---|---|---|
| 01 | 01-ssw-driver | `01-ssw-driver/prompts/business-config.md` | `## 词汇速览：特定技能司机（词汇库自动同步）` |
| 02 | 02-career-driver | `02-career-driver/prompts/business-config.md` | `## 词汇速览：司机职业发展（词汇库自动同步）` |
| 03 | 03-career-management | `03-career-management/prompts/business-config.md` | `## 词汇速览：职业管理与晋升（词汇库自动同步）` |
| 04 | 04-industry-logistics | `04-industry-logistics/prompts/business-config.md` | `## 词汇速览：物流行业（词汇库自动同步）` |
| 05 | 05-industry-autonomous | `05-industry-autonomous/prompts/business-config.md` | `## 词汇速览：自动驾驶与自动化（词汇库自动同步）` |
| 06 | 06-industry-technology | `06-industry-technology/prompts/business-config.md` | `## 词汇速览：技术行业（词汇库自动同步）` |
| 07 | 07-economy-finance | `07-economy-finance/prompts/business-config.md` | `## 词汇速览：经济与财务（词汇库自动同步）` |
| 08 | 08-visa-immigration | `08-visa-immigration/prompts/business-config.md` | `## 词汇速览：签证与移民（词汇库自动同步）` |
| 09 | 09-politics-law | `09-politics-law/prompts/business-config.md` | `## 词汇速览：政治与法律（词汇库自动同步）` |
| 10 | 10-education-qualification | `10-education-qualification/prompts/business-config.md` | `## 词汇速览：教育与资格（词汇库自动同步）` |
| 11 | 11-language-japanese | `11-language-japanese/prompts/business-config.md` | `## 词汇速览：日语语言（词汇库自动同步）` |
| 12 | 12-culture-life | `12-culture-life/prompts/business-config.md` | `## 词汇速览：文化与生活（词汇库自动同步）` |
| 13 | 13-regional-info | `13-regional-info/prompts/business-config.md` | `## 词汇速览：地区信息（词汇库自动同步）` |
| 14 | 14-life-operations | `14-life-operations/prompts/business-config.md` | `## 词汇速览：在日生活实务（词汇库自动同步）` |
| 15 | 15-health-wellbeing | `15-health-wellbeing/prompts/business-config.md` | `## 词汇速览：医疗·健康·心理（词汇库自动同步）` |
| 16 | 16-exit-transition-return | `16-exit-transition-return/prompts/business-config.md` | `## 词汇速览：退出·转型·回国（词汇库自动同步）` |
| 17 | 17-migration-compliance | `17-migration-compliance/prompts/business-config.md` | `## 词汇速览：劳务输出与中介合规（词汇库自动同步）` |
| 18 | 18-family-parenting | `18-family-parenting/prompts/business-config.md` | `## 词汇速览：家族·育儿·人生事件（词汇库自动同步）` |
| 19 | 19-safety-disaster | `19-safety-disaster/prompts/business-config.md` | `## 词汇速览：防灾·安全·治安（词汇库自动同步）` |
| 20 | 20-overseas-china | `20-overseas-china/prompts/business-config.md` | `## 词汇速览：中国侧行前与回国（词汇库自动同步）` |

> **说明**：同一目标文件绑定多个主题时，须使用不同的 `section_title`，避免区块标题重复。

## 十、路径、别名与工具链约定

### 10.1 路径约定

- 词汇子系统根目录为 `engine/vocabulary/`；下文所有命令均在**仓库根目录**执行。
- 脚本内部以自身位置推导根目录（`Path(__file__).parent.parent`），因此不依赖当前工作目录；`topics.json` / `sync.json` 中的相对路径均相对 `engine/vocabulary/` 解析。
- 仓库级引用建议使用完整相对路径 `engine/vocabulary/...`，避免跨主题目录引用时层级歧义。

### 10.2 路径别名 `@/vocabulary`

本仓库当前为**文档 + Python 工具链**项目，不存在 `package.json` / `tsconfig.json` / `jsconfig.json` / ESLint 配置，也没有 TS/JS 源码，因此**没有可挂载路径别名的配置入口**，本次不新增虚构配置。

若后续引入前端工程（Vite/Next.js 等），按以下映射接入即可，无需改动词汇目录本身：

| 配置项 | 建议值 |
|---|---|
| `compilerOptions.paths`（tsconfig/jsconfig） | `"@/vocabulary/*": ["engine/vocabulary/*"]` |
| Vite `resolve.alias` | `'@': path.resolve(__dirname, 'src')` |
| ESLint 忽略 | `engine/vocabulary/data/**`（数据与导出产物不参与 lint） |

### 10.3 校验与验收

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| 主题注册表 | `python engine/vocabulary/script/vocab_tool.py topics` | 列出全部已注册主题 |
| 注册表/目录一致性 | `python engine/vocabulary/script/vocab_tool.py topic-check` | 0 错误 / 0 警告 |
| 词库质量（逐主题） | `python engine/vocabulary/script/vocab_tool.py check --topic <topic>` | 0 错误 / 0 警告 |
| 脚本语法 | `python -m compileall engine/vocabulary/script` | 无 SyntaxError |
| 构建 / ESLint / TypeScript | 不适用（仓库无对应工具链） | — |

> 说明：新增 `schema/`、`templates/` 仅为静态资源，不参与脚本扫描（`topic-check` 只审计 `data/` 下的主题目录），不会触发任何校验告警。

---

## 版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-13 | 初始版本 | 子系统建立：SOP 六步流程 + vocab_tool.py（7 子命令）+ topics.json 主题注册 + AI 安全种子 47 条（7 分类）入库 v1.1；全链路含幂等/去重/错误路径自检通过 |
| v1.1 | 2026-11-13 | 新增 financial-markets 主题 | 金融市场主体接入：6 分类 49 条种子入库；topics.json v1.1 |
| v1.2 | 2026-11-13 | 自动同步机制 | 新增 sync_vocab.py（sync/check/verify/watch/status 五命令：标记区间保护 + 增量检测 + 写后校验自动回滚 + 日志）与 sync.json 绑定配置；vocab_tool import/tag 增加自动同步钩子；ai-security → business-config.md 绑定接入并实测通过（含 watch 轮询与错误路径自检） |
| v1.3 | 2026-11-13 | 主题管理自动化 | 新增 topic-add / topic-remove / topic-check：新增主题一条命令自动完成注册表登记 + 目录创建 + 索引重建（备份回滚 + topic-ops.log 操作日志，前缀自动派生查重、孤儿目录纳管）；手工编辑 topics.json 降级为非支持入口。正反路径与孤儿纳管实测通过 |
| v1.4 | 2026-11-13 | 新增 cybersecurity 主题与第二条绑定 | cybersecurity 主题接入（6 分类 90 条，两批种子）并绑定同步至 dubai/cybersecurity/prompts/business-config.md（sync.json v1.1）；全库 3 主题 188 条 |
| v1.5 | 2026-11-13 | 第三条绑定（全量覆盖） | financial-markets 绑定同步至 dubai/apartment/prompts/business-config.md；至此三条业务线全部接入自动同步（49+90+49=188 条） |
| v1.6 | 2026-11-13 | 新增 economy 主题与第四条绑定 | economy（经济）主题接入：3 分类（经济体与国家 / 区域经济组织 / 经济概念），种子 17 条入库 + 并行批次扩展至 44 条（v1.2），ECO 前缀；绑定同步至 trends/economy/prompts/business-config.md（sync.json v1.2）；全库 4 主题 |
| v1.7 | 2026-11-13 | 目录规范化与扩展骨架 | 目录迁入 `engine/vocabulary/` 并补齐扩展骨架：新增 `schema/export.schema.json`（导出数据契约）与 `templates/topic-import-template.md`（导入模板）；README 增加目录职责映射、命名约定、新主题目录创建规则、路径/别名/工具链说明与验收命令；脚本内用法示例路径同步修正。现有 config/data/script 结构未改动，4 主题 295 条词条校验 0 错误 0 警告 |
| v1.8 | 2026-11-13 | 同步目标重绑 | sync.json v1.3：financial-markets、economy 重绑至 `07-economy-finance/prompts/business-config.md`（第十二节版本记录前，区块标题区分主题），首次写入并校验通过（49 + 44 条，区间外内容一致）；ai-security、cybersecurity 因 01–13 无对应主题暂不绑定，词库保留 |
| v1.9 | 2026-11-13 | 13 业务线词库重建 | 按 01–13 业务线一一对应重建主题体系：移除 ai-security、cybersecurity、economy、financial-markets 四个历史主题及其数据（含 07 旧同步区块），新建 13 个主题、每主题 68 条，共 884 条（6–7 个受控分类/主题）；13 条 sync.json v2.0 绑定全部写入各自 business-config.md 并通过 verify；`check` 13 主题 0 错误 0 警告，`topic-check` 0 错误 0 警告；vocab_tool.py 允许从空注册表引导 topic-add |
| v2.0 | 2026-11-13 | 4 主题扩展至 102 条 | ssw-driver、career-driver、industry-logistics、industry-autonomous 各新增 34 条扩展种子（imports/2026-11-13_expansion-*.md），零重复、零跳过；4 主题词库 v1.2（各 102 条），全库 13 主题 1020 条；check 0 错误 0 警告，4 个业务线同步区块增量更新并通过 verify |
| v2.1 | 2026-11-13 | 全库交叉校验与缺口补录 | 以 13 条业务线指标登记册核心指标词为基准逐词核对，发现 12 个主题共 32 项指标级缺口（如育成就劳 MOC、SPPI、物流白書、家計調査、時間外労働上限、納期遵守率等），经 imports/2026-11-13_gapfill*.md 全部补录入库（32 条，0 重复）；复核 13/13 主题完整覆盖，全库 1052 条；check / topic-check / sync verify 全部通过 |
| v2.2 | 2026-11-17 | 文档治理更新 | 主题扩展至 20 个（14–20 接入）、全库 1327 条；README 修正主题/词条/绑定计数、补 `verify` 命令、旧路径 `prompts/tools` 与已删除主题示例（ai-security → ssw-driver）、命名约定示例、9.5 绑定表补齐 20 行 |
| v2.3 | 2026-11-18 | 目录对齐 `NN-slug` | `data/` 20 个子目录重命名为 `NN-slug`（与根目录 00–20 主题编号一一对应）；`topics.json` / `sync.json` / 绑定表 / 示例路径同步；全库 1389 条 |
