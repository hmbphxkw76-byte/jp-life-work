# 工单 N23：· 受控词表跨主题同概念对齐（P2，组 B）

> **来源**：情报科学五框架分析（会话，2026-11-20）· 差距 G5（受控词表）
> **状态**：已入库
> **验收判据**：见下方「验收判据」节；完成后回填状态与证据。

---

· 受控词表跨主题同概念对齐（P2，组 B）

- **目标**：补齐受控词表的**跨主题语义对齐**，解决 C-10 只能比对「同名指标」口径、抓不到「同概念异名」的问题；为跨主题口径一致提供机读检测。
- **验收判据**：
  1. `engine/vocabulary/config/topics.json` 增跨主题概念映射（`concept_id → 各主题词条 ID 列表`），先覆盖 `01-ssw-driver` / `04-industry-logistics` / `08-visa-residence` / `16-exit-transition-return` 等高频主题。
  2. `engine/vocabulary/script/vocab_tool.py` 增 `cross-check` 子命令：检测跨主题「同定义 / 同别名 / 同概念异名」；退出码契约 0=通过 / 1=错误 / 2=警告。
  3. `engine/tools/info_quality_check.py` 增 `C-15`（跨主题同概念异名，P2，仅告警不阻断）。
  4. `.github/workflows/validate.yml` 词库校验增 `cross-check` 步骤；`engine/tests/test_tools.py` 增守卫测试。
  5. 各主题 `prompts/prompt-p1-term-alignment.md` 增「跨主题同概念对齐」步骤（可先文档后工具）；`unittest` 全绿。
- **实施步骤**：① 定义 `concept_id` 命名与映射字段；② `topics.json` 试点映射；③ `vocab_tool cross-check` 实现；④ `info_quality_check` C-15；⑤ 工作流步骤 + 守卫测试；⑥ 提示词扩展；⑦ 回填。
- **涉及文件**：`engine/vocabulary/config/topics.json`、`engine/vocabulary/script/vocab_tool.py`、`engine/tools/info_quality_check.py`、`.github/workflows/validate.yml`、各主题 `prompts/prompt-p1-term-alignment.md`、`engine/tests/test_tools.py`。
- **风险与依赖**：`concept_id` 维护责任方须明确——**先只读检测、后人工登记映射**，不自动合并词条；映射缺失时 `cross-check` 告警而非阻断。
- **证据**：
  - 配置：`engine/vocabulary/config/topics.json` 增 `concept_map`（20 条 `CONCEPT-NNN`，覆盖 01/04/08/16 等高频主题；54 个登记词条，含同定义异名「健康保険組合 / 健保組合」）；`vocab_tool` 的 `topic-add` 保留该顶层键。
  - 工具：`vocab_tool.py` 新增 `cross_check_gaps()`（纯函数）+ `cross-check` 命令（`--json`）：引用完整性（缺失 → 错误 rc=1）、同定义异名 / 同名词条未登记（rc=2）；实测 20 概念 / 118 同名词条组 / 99 未登记 / 0 错误 / 20 警告（rc=2）。
  - 上层：`info_quality_check.py` 新增 `vocab_cross_gaps()` + C-15（P2，复用 `cross_check_gaps()` 单一事实源）；`audit_check.C_TO_LAYER` 增 C-15 → L4；`validate.yml` 词库校验步骤接入 `cross-check`。
  - 提示词：21 个主题 `prompts/prompt-p1-term-alignment.md` 增「跨主题同概念对齐（n23）」段。
  - 测试：`test_tools.py` 238 项 OK（新增 cross-check 4 项 + C-15 来源 1 项）；`validate.py` / `prompt_check.py` / ruff 全绿。
  - 文档：`docs/信息质量评估提示词体系.md` v1.6（C-15）、`docs/审计报告标准化管理体系.md` v1.8（C-15 映射 L4）、`engine/vocabulary/README.md` S7。
- **状态**：已入库（实施完成并合并推送至 `origin/main`；证据见上）。
