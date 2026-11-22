# 规格：生成前信息核验卡点（闸0）+ 提交前内容硬门禁

> 任务 slug：`pre-generation-verification-gate`
> 版本：v1.0（2026-11-22）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)
> 上位依据：[AGENTS.md](../../../AGENTS.md)、[CI.md](../../CI.md)、[信息生产全链路执行规范](../../信息生产全链路执行规范.md)

## 一、动机

仓库现有 48 个工具 / 8 条工作流的核验体系，**卡点全部位于「落盘后 / 推送后」**：

- 阶段4 生成报告 → 阶段5 输出 → 交付门禁 F（`validate.yml` + `audit-gate.yml`，push/PR 触发）；
- `audit_preflight` / `verified_content_gate` / `source_language_gate` / `source_check` 均接在 CI（push 后）；
- 本地 pre-commit 只做 `ruff + validate.py`（结构层），**不含任何内容核验**。

**缺口**：报告正文写完之前没有强制核验；未核验信息可被本地提交，直到 CI 才拦截。
本规格把核验左移，形成「生成前 → 提交前 → 推送后」三道卡点，保证未核验信息不进入报告库。

## 二、目标与非目标

**目标**
1. 生成前：新增「闸0」信息核验，确认主题的信息输入与既有内容满足「可生成」条件。
2. 提交前：pre-commit 内容硬门禁，暂存报告含未核验信息即禁止提交。
3. 推送后：CI 增闸0 步骤，与既有内容门禁兜底。
4. 流程：提示词基座把「生成前核验」固化为阶段4 前置步骤。

**非目标**
- 不改动报告研究内容、不改动既有判定内核（全部复用）。
- 不新增来源语言政策、不放宽任何既有门禁。
- 不替代 AuditGuard L1–L5 与交付与审计协议。

## 三、接口设计

### 3.1 `engine/tools/generation_gate.py`（闸0：生成前信息核验）

- 用法：
  - `python engine/tools/generation_gate.py --topic <主题目录名>`（单主题）
  - `python engine/tools/generation_gate.py --all`（全量）
  - `--json`（结果输出 stdout）
- 检查项（全部复用既有内核，不新写判定）：
  - **G0-STRUCT**：`stage_gate_check.check_topic`（闸1-3，P0/P1 阻断）。
  - **G0-LANG**：`source_language_gate.check_prompts` 过滤本主题（违规阻断）。
  - **G0-CONTENT**：`verified_content_gate.scan_text`（全层零容忍）扫本主题 `prompts/`、`data/`、`handbook/`、`reports/`。
  - **G0-SOURCE**：`source_check.extract_report` 对本主题既有报告（「缺来源章节」阻断）。
- 输出：每主题 `passed` + findings；退出码 `0` 可生成 / `1` 阻断 / `2` 仅 P2 告警。
- 不写状态文件（按需实时执行；避免时间戳入库）。

### 3.2 `engine/scripts/precommit_content_gate.py`（提交前内容硬门禁）

- 无参数；读暂存区（`git diff --cached --name-only --diff-filter=ACM`）。
- 对暂存的 `*/reports/*.md`，逐份执行：
  - `verified_content_gate.scan_text`（全层零容忍）；
  - `source_language_gate.check_reports`；
  - `source_check.extract_report`（缺来源章节阻断）。
- 对暂存的 `*/prompts/*.md` / `*/data/*.md` / `*/handbook/*.md`，执行 `verified_content_gate.scan_text` + 提示词层来源语言（命中即阻断）。
- 无暂存报告 / 资产时立即退出 0（零开销）。
- 退出码：`0` 通过 / `1` 命中（阻断提交）。

### 3.3 pre-commit 钩子扩展

- 在 `engine/scripts/git-hooks/pre-commit` 末尾调用 `engine/scripts/precommit_content_gate.py`。
- 钩子源文件修改后需 `python engine/scripts/branch_naming.py install` 重装。

### 3.4 提示词基座

- `engine/report_templates/prompt-generic-base.md` 新增「阶段4 前置：生成前信息核验（闸0）」步骤，要求生成者先跑 `generation_gate.py --topic <主题>` 并通过。

### 3.5 CI（C 兜底）

- `.github/workflows/validate.yml` 增步骤「生成前信息核验（闸0）」：`python engine/tools/generation_gate.py --all`（退出码 1 阻断）。

## 四、验收标准

1. `generation_gate.py --all` 对当前 21 主题输出可生成（除已知 P2 观察项），退出码 ∈ {0,2}。
2. `precommit_content_gate.py` 对含「待核实 / 未核实 / 需核实原文 / 待核验 / 待补来源」的暂存报告退出 1 并打印行号定位。
3. pre-commit 钩子在暂存干净报告时放行、在暂存含未核验内容时阻断（契约测试覆盖）。
4. `validate.yml` 含闸0 步骤；`validate.py` 退出码 ∈ {0,2}；`unittest` 全绿。
5. 文档同步：`docs/CI.md`、`docs/信息生产全链路执行规范.md`、`engine/tools/README.md`、`engine/scripts/README.md`。

## 五、边界与约束

- 退出码契约：`0` 通过 / `1` 阻断 / `2` 告警。
- 复用既有判定内核，不新写规则；单一事实源（`source-policy.json` / `verified-content-policy.json`）不变。
- 生成物确定性：不写时间戳、不写入库状态文件。
- 工具链变更走 TOOLCHAIN-DEV-SPEC S1→S6；双轴评审 + 合并前检查单不可豁免。
