# 工单：CI 生成前信息核验接入 + public 安全姿态（ci-pre-gen-verify-public）

> **版本**：v1.0（2026-11-22）
> **规格**：[specs/ci-pre-gen-verify-public.md](../specs/ci-pre-gen-verify-public.md)
> **分支**：`task/ci-pre-gen-verify-public-<sid>`
> **状态**：进行中

## 工单

### T1 · 新增 content-verify 复合动作

- **验收**：`.github/actions/content-verify/action.yml` 存在；步骤 1 为 `generation_gate.py --all`（允许 0/2），步骤 2 为 `verified_content_gate.py --all`（仅 0）；未通过输出 `::error::` 并非零退出。
- **状态**：已完成

### T2 · pipeline-orchestrator 接入生成前核验

- **验收**：`安装依赖` 与 `触发检测` 之间含 `- uses: ./.github/actions/content-verify`；头部注释含步骤 0 说明。
- **状态**：已完成

### T3 · html-sync 接入发布前核验

- **验收**：`安装依赖` 与 `重新生成报告 HTML（md2html.py）` 之间含 `- uses: ./.github/actions/content-verify`；头部注释说明发布前核验。
- **状态**：已完成

### T4 · public 安全配置

- **验收**：仓库 `security_and_analysis` 的 `secret_scanning` / `secret_scanning_push_protection` / `dependabot_security_updates` 均为 `enabled`；`.github/dependabot.yml` 存在，含 `github-actions` 与 `pip` 两个 ecosystem。
- **状态**：已完成

### T5 · 文档同步

- **验收**：`docs/CI.md` §2.2 / §2.8 步骤数与工作流实测一致，新增「public 仓库安全姿态」节与版本记录；总规范闸0 行补注 CI 复合动作。
- **状态**：进行中

## 合并前检查单（S6）

- [ ] `python -m unittest discover -s engine/tests` 全绿
- [ ] `python engine/tools/validate.py` 退出码 ∈ {0,2}
- [ ] 评审报告 `docs/toolchain/reviews/ci-pre-gen-verify-public-review.md` 存在且双轴无 P0/P1
- [ ] `coverage_gate.py` 达标
- [ ] `cleanup_workspace.py --check` 零残留
