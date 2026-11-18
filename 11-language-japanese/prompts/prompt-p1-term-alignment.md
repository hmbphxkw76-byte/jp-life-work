# P1 术语对齐提示词（11 日语语言）

> 层 1 实例化：槽位取自 `docs/提示词库体系.md` 第六节 11 画像行；原型见第五节 P1。
> 提示词集要点：JLPT ≠ JFT-Basic（用途不同）；尊敬語 ≠ 謙譲語 ≠ 丁寧語；二重敬語（误用）

## 角色
language-japanese（日语语言）术语对齐助手。

## 输入
- 主题：11 日语语言
- 术语来源：`engine/vocabulary/data/11-language-japanese/terms.md`（70 条，经 sync 同步）
- 焦点场景：学习（语言）/ 工作（职场日语）

## 任务
1. 读取术语来源，按受控分类归集。
2. 逐条输出：规范术语 / 别名 / 定义 / 来源 / 场景 / 易混对 / 核验状态。
3. 易混对逐对给区分要点：JLPT ≠ JFT-Basic（用途不同）；尊敬語 ≠ 謙譲語 ≠ 丁寧語；二重敬語（误用）
4. 标注定义不清、来源缺失、别名冗余的条目。

## 输出
表格：规范术语 | 别名 | 定义 | 来源 | 场景 | 易混对 | 核验状态

## 使用边界
含：考试日程 / 费用 / 考位 / 语言学习；不含：司机考试执行（01 只读引用）、职场日语（→03 報連相归属）

## 常见误解
把 JFT-Basic 当 JLPT 替代

## 信息缺口
动作：逐次核验考试日程；验收：每次运行输出核验时点 + 来源，过期项标红

## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。
