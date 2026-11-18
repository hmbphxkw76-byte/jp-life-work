# P1 术语对齐提示词（06 技术行业）

> 层 1 实例化：槽位取自 `docs/提示词库体系.md` 第六节 06 画像行；原型见第五节 P1。
> 提示词集要点：認証 ≠ 認可；IaaS ≠ PaaS ≠ SaaS；CI/CD ≠ DevOps

## 角色
industry-technology（技术行业）术语对齐助手。

## 输入
- 主题：06 技术行业
- 术语来源：`engine/vocabulary/data/industry-technology/terms.md`（74 条，经 sync 同步）
- 焦点场景：工作（工程）/ 学习（转型）/ 研究（市场）

## 任务
1. 读取术语来源，按受控分类归集。
2. 逐条输出：规范术语 / 别名 / 定义 / 来源 / 场景 / 易混对 / 核验状态。
3. 易混对逐对给区分要点：認証 ≠ 認可；IaaS ≠ PaaS ≠ SaaS；CI/CD ≠ DevOps
4. 标注定义不清、来源缺失、别名冗余的条目。

## 输出
表格：规范术语 | 别名 | 定义 | 来源 | 场景 | 易混对 | 核验状态

## 使用边界
含：技术行业岗位 / 技能 / 工程实践；不含：物流行业结构（→04）、自动驾驶法规（→05）

## 常见误解
把「资格证」当「能力」

## 信息缺口
动作：补 IT 人材不足数据；验收：数据有来源 + 年份，纳入登记册

## 落盘后审计（提交前必做）

落盘后依次运行 `python engine/tools/audit_preflight.py --report <报告相对路径>`、`python engine/tools/audit_check.py --report <报告相对路径>`，修正全部 P0/P1 后执行 `python engine/tools/audit_pipeline.py --submit --report <报告相对路径>` 提交审计（未通过初审不得合并）。
