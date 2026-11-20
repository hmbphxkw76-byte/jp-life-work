# 双轴评审：加工层受控中间产物（source-index 入册）（n25-processing-controlled）

> **工单**：n25-processing-controlled（docs/toolchain/tickets/n25-processing-controlled.md）
> **评审日期**：2026-11-20
> **评审口径**：Standards（TOOLCHAIN-DEV-SPEC / 仓库规范符合性）+ Spec（工单设计完备性：目标 / 验收判据 / 涉及文件 / 风险与依赖）
> **证据来源**：工单设计文本 + 规约条款 + 涉及文件存在性核对；**不核验实施产物**
> **结论**：**Standards 无 P0/P1；Spec 无 P0/P1**

## 一、Standards 轴（规约符合性）

| 检查项 | 结论 | 证据 |
|---|---|---|
| 命名规范（§四） | 通过 | slug `n25-processing-controlled` kebab-case，无 `YYYY-MM-` 前缀 |
| 适用边界（§二） | 通过 | 主体 `engine/tools/source_check.py`、`engine/tools/counterexample_scan.py`、`engine/tools/info_quality_check.py`（工具链）；`source-index.json` / `.gitignore` / `engine/report-audits/README.md` 为配置与文档 |
| 退出码契约（§五） | 通过 | `source_check` 增 E5；`validate.yml` 的 `source_check --check` 行为不变或同步 |
| 异常不静默（§五） | 通过 | 归一化规则集中，其他工具不再各写一套；E5 显式统计完整率 |
| 单一事实源（§六） | 通过 | 新增 `engine/tools/source_normalize.py` 集中 `normalize_url` / `normalize_org` / `normalize_year` / `extract_year`；`source-index.json` 入库受控 + 内容指纹关联 |
| 测试（S3） | 通过 | 验收第 5 条守卫测试 + `unittest` 全绿 |
| 隔离与顺序（AGENTS.md 规约二） | 通过 | 批 1 基础，n21 / n22 依赖；状态注明 worktree `n25-processing-controlled` |

**Standards 结论：无 P0/P1。**

## 二、Spec 轴（工单设计完备性）

| 验收判据 | 设计可验证性 | 结论 | 证据 |
|---|---|---|---|
| 1. `source-index.json` 入库受控 + 指纹关联 | 产物路径 + 指纹字段 | 覆盖 | 与 `audit_registry.content_fingerprint` 关联，可回溯报告变更 |
| 2. 归一化集中复用 | 公共模块 + 复用点 | 覆盖 | 证据说明 `counterexample_scan` / `info_quality_check` 当前无独立归一化逻辑，未为改而改（诚实） |
| 3. E5 字段完整率 | 检查项 + 计数 | 覆盖 | url + 时点 + 分组三项；`GROUP_RE` 覆盖真实分组头 |
| 4. `.gitignore` / README 入库口径 | 文档 + 忽略规则 | 覆盖 | 明确活台账口径与变更留痕规则 |
| 5. 守卫测试 + `unittest` + `validate` 行为 | 命令退出码 | 覆盖 | `source_check --check` 行为不变或同步 |

**Spec 结论：无 P0/P1。**

## 三、设计观察（P2，不阻断）

1. **路径初稿与实际不一致**：`涉及文件` 写 `engine/report-audits/source-index.json`，`证据` 校正为 `engine/report-audits/audit/source-index.json`；建议工单正文统一为实际路径，避免后续维护者误改。
2. **入库口径冲突需合并时确认**：`source-index.json` 入库后与 `report-audits` 既有忽略口径（如 `audit/verify/`）可能冲突（工单风险已声明）；建议合并前跑 `validate.py` 与 `git status` 核对残留。

## 四、证据清单

- 工单：`docs/toolchain/tickets/n25-processing-controlled.md` §目标 / §验收判据 1–5 / §涉及文件 / §风险与依赖 / §证据。
- 规约：`docs/toolchain/TOOLCHAIN-DEV-SPEC.md` 第二节、第三节、第五节、第七节。
- 一致性核对（只读）：`engine/tools/source_check.py`、`engine/tools/counterexample_scan.py`、`engine/tools/info_quality_check.py`、`engine/tools/source_normalize.py`、`engine/report-audits/audit/source-index.json`、`engine/report-audits/README.md` 存在；`engine/report-audits/source-index.json` 不存在（见观察 1）。
