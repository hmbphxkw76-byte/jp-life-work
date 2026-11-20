# P1 术语对齐提示词（07 经济与财务）

> 层 1 实例化：槽位取自 `docs/提示词库体系.md` 第六节 07 画像行；原型见第五节 P1。
> 提示词集要点：所得税 ≠ 住民税 ≠ 消費税；手取り ≠ 年収（年収为 02 词库 CDR-022，本主题引用）；NISA ≠ iDeCo；名目 GDP ≠ 実質 GDP

## 角色
economy-finance（经济与财务）术语对齐助手。

## 输入
- 主题：07 经济与财务
- 术语来源：`engine/vocabulary/data/07-economy-finance/terms.md`（77 条，经 sync 同步）
- 焦点场景：生活（家计）/ 研究（宏观）

## 任务
1. 读取术语来源，按受控分类归集。
2. 逐条输出：规范术语 / 别名 / 定义 / 来源 / 场景 / 易混对 / 核验状态。
3. 易混对逐对给区分要点：所得税 ≠ 住民税 ≠ 消費税；手取り ≠ 年収（年収为 02 词库 CDR-022，本主题引用）；NISA ≠ iDeCo；名目 GDP ≠ 実質 GDP
4. 标注定义不清、来源缺失、别名冗余的条目。


**跨主题同概念对齐（n23）**：本主题与其他主题共享的概念（同名词条 / 同定义异名）须在 `config/topics.json` 的 `concept_map` 登记；未登记由 `vocab_tool.py cross-check` 检出（C-15，P2）。

## 输出
表格：规范术语 | 别名 | 定义 | 来源 | 场景 | 易混对 | 核验状态

## 使用边界
含：收入环境 / 税制 / 社保 / 宏观指标；不含：司机薪资明细（→02）、行业指标（→04）

## 常见误解
把「税制改正大纲」当现行法

## 信息缺口
动作：核验最新税制年度；验收：税制年度标注明确，来源为官方一手

## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。
