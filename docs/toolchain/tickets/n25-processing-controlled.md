# 工单 N25：· 加工层受控中间产物（source-index 入册）（P2，组 C）

> **来源**：情报科学五框架分析（会话，2026-11-20）· 差距 G7（情报周期·加工）
> **状态**：已入库
> **验收判据**：见下方「验收判据」节；完成后回填状态与证据。

---

· 加工层受控中间产物（source-index 入册）（P2，组 C）

- **目标**：把 `source-index.json` 从「校验副产物」提升为**入库受控加工产物**，并把散落各工具的机构名 / URL / 日期归一化规则集中到单一事实源，解决加工一致性依赖人工的问题。
- **验收判据**：
  1. `engine/report-audits/source-index.json` 纳入入库受控产物，变更留痕，并与报告内容指纹关联（可回溯「哪次报告变更引入了哪条来源」）。
  2. `engine/tools/source_check.py` 集中机构名 / URL / 日期归一化规则，供 `counterexample_scan.py` / `info_quality_check.py` 复用；其他工具不再各写一套。
  3. `source_check.py` 增 `E5` 来源条目字段完整率检查（四元组 + 新增字段）。
  4. `.gitignore` 与 `engine/report-audits/README.md` 明确 `source-index.json` 的入库口径与变更留痕规则。
  5. `engine/tests/test_tools.py` 增守卫测试；`unittest` 全绿；`validate.yml` 的 `source_check --check` 行为不变或同步。
- **实施步骤**：① 定义 source-index 入库位置与留痕字段；② 抽出归一化公共函数（单一事实源）；③ 接入 `counterexample_scan` / `info_quality_check`；④ 增 E5；⑤ 更新 .gitignore / report-audits README；⑥ 测试与回填。
- **涉及文件**：`engine/tools/source_check.py`、`engine/tools/counterexample_scan.py`、`engine/tools/info_quality_check.py`、`engine/report-audits/source-index.json`、`.gitignore`、`engine/report-audits/README.md`、`engine/tests/test_tools.py`。
- **风险与依赖**：入库后 `validate.yml --check` 需同步；须避免与 `report-audits` 既有忽略口径（如 `audit/verify/`）冲突。
- **证据**：
  - 新增 `engine/tools/source_normalize.py`（`normalize_url` / `normalize_org` / `normalize_year` / `extract_year`，纯函数）；`source_check.py` 改用 `normalize_url` + `extract_year`。
  - `source_check.py` 增 E5 字段完整率（url + 时点 + 分组三项），并扩展 `GROUP_RE` 识别 `**官方一手（…）**` / `### 官方一手` 等真实分组头；`source-index.json` 每份报告增 `fingerprint`（复用 `audit_registry.content_fingerprint`），`version` 升 2。
  - `engine/report-audits/audit/source-index.json` 移出 `.gitignore`，在 `engine/report-audits/README.md` 活台账表登记（v1.2）。
  - 测试：`test_source_check.py` 18 项 OK（新增归一化 3 项 + E5/指纹 3 项）；`source_check.py` 全量 21 份报告 / 458 条，阻断 0、告警 1（00 决策枢纽无 URL 条目，预期）；`validate.py` rc=0；ruff 通过。
  - 说明：`counterexample_scan.py` / `info_quality_check.py` 当前无独立机构名 / URL / 日期归一化逻辑，故仅提供共享模块供 n21 / n22 复用，未为改而改。
  - 路径校正：实际受控产物为 `engine/report-audits/audit/source-index.json`（工具既有输出路径），非工单初稿的 `engine/report-audits/source-index.json`。
- **状态**：已入库（实施完成并合并推送至 `origin/main`；证据见上）。
