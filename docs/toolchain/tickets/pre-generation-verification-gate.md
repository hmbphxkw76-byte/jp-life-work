# 工单：生成前信息核验卡点（闸0）+ 提交前内容硬门禁

> 任务 slug：`pre-generation-verification-gate`
> 规格：[pre-generation-verification-gate.md](../specs/pre-generation-verification-gate.md)
> 每条工单含验收判据；按序实施，TDD 先行。

## T-01 `generation_gate.py` 单主题核验（闸0）

- [ ] 新增 `engine/tools/generation_gate.py`，实现 `--topic <name>` / `--all` / `--json`。
- [ ] 检查项复用：`stage_gate_check.check_topic`、`source_language_gate.check_prompts`（过滤本主题）、`verified_content_gate.scan_text`（全层零容忍）、`source_check.extract_report`。
- [ ] 退出码 `0/1/2`；findings 含 code / severity / location / detail。
- **验收**：`python engine/tools/generation_gate.py --topic 01-ssw-driver` 退出码 ∈ {0,2}；`--json` 结构含 `topic` / `passed` / `findings`。

## T-02 `generation_gate.py` 全量与已知 P2

- [ ] `--all` 遍历 `iter_business_dirs()`，汇总 `topics` / `passed` / `failed` / `by_severity`。
- [ ] 已知 P2（`00-decision-hub` G1-REGISTRY）放行，退出码 2。
- **验收**：`--all` 对 21 主题退出码 ∈ {0,2}，无 P0/P1。

## T-03 `precommit_content_gate.py` 暂存内容硬门禁

- [ ] 新增 `engine/scripts/precommit_content_gate.py`，读 `git diff --cached --name-only --diff-filter=ACM`。
- [ ] 暂存 `*/reports/*.md`：`verified_content_gate` + `source_language_gate.check_reports` + `source_check.extract_report`。
- [ ] 暂存 `*/prompts/*.md` / `*/data/*.md` / `*/handbook/*.md`：`verified_content_gate` + 提示词层来源语言。
- [ ] 无暂存报告 / 资产时退出 0。
- **验收**：构造含「待核实」的暂存报告 → 退出码 1 且打印行号；干净报告 → 退出码 0。

## T-04 pre-commit 钩子接线

- [ ] `engine/scripts/git-hooks/pre-commit` 末尾调用 `engine/scripts/precommit_content_gate.py`。
- [ ] 钩子自包含回退（`engine/scripts/` 缺失时用钩子副本目录）。
- **验收**：`branch_naming.install_hooks` 后，暂存含未核验内容的报告提交被阻断；`test_branch_naming` 全绿。

## T-05 提示词基座生成前步骤

- [ ] `prompt-generic-base.md` 新增「阶段4 前置：生成前信息核验（闸0）」：先跑 `generation_gate.py --topic <主题>` 并通过。
- **验收**：`prompt_check.py` 全绿；文档含闸0 步骤。

## T-06 CI 接线（C 兜底）

- [ ] `.github/workflows/validate.yml` 增步骤「生成前信息核验（闸0）」：`python engine/tools/generation_gate.py --all`。
- **验收**：工作流 YAML 合法；`test_platform_guard` / CI 步骤数守卫通过。

## T-07 文档同步

- [ ] `docs/CI.md`：工作流清单与手动命令补闸0 / precommit 内容门禁。
- [ ] `docs/信息生产全链路执行规范.md`：全链路图与门禁表补「闸0 生成前」；版本记录。
- [ ] `engine/tools/README.md`：工具一览表补 `generation_gate.py`。
- [ ] `engine/scripts/README.md`：补 `precommit_content_gate.py` 与钩子说明。
- **验收**：文档↔实现一致；`validate.py` 退出码 ∈ {0,2}。

## T-08 测试

- [ ] `engine/tests/test_generation_gate.py`：单主题 / 全量 / 命中阻断 / 已知 P2 放行。
- [ ] `engine/tests/test_precommit_content_gate.py`：暂存命中阻断 / 干净放行 / 无暂存快速退出。
- **验收**：`python -m unittest discover -s engine/tests` 全绿；覆盖率门禁达标。
