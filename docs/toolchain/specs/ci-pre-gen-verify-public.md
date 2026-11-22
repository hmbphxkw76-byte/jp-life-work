# 规格：CI 生成前信息核验接入 + public 安全姿态（ci-pre-gen-verify-public）

> **版本**：v1.0（2026-11-22）
> **定位**：工具链变更规格（TOOLCHAIN-DEV-SPEC S1）。≤1 页，只含动机 / 接口 / 验收标准。

## 一、动机

1. **生成 / 发布前缺卡点**：`pipeline-orchestrator.yml`（计划前）与 `html-sync.yml`（HTML 生成 / 发布前）原先不跑信息核验；若提示词或 pre-commit 被绕过，未核验内容可进入计划或生成物。
2. **public 仓库安全姿态**：仓库为 PUBLIC，但密钥扫描 / push protection / Dependabot 安全更新均未启用，无版本更新自动化。

## 二、接口

- 新增复合动作 `.github/actions/content-verify/action.yml`：
  - 步骤 1：`python engine/tools/generation_gate.py --all`（闸0），退出码 ∈ {0,2} 放行，否则失败；
  - 步骤 2：`python engine/tools/verified_content_gate.py --all`（无法核实内容硬门禁），退出码 0 放行，否则失败。
- 接入点：
  - `pipeline-orchestrator.yml`：`安装依赖` 之后、`触发检测` 之前；
  - `html-sync.yml`：`安装依赖` 之后、`md2html.py` 之前。
- public 配置：仓库设置启用 `secret_scanning` / `secret_scanning_push_protection` / `dependabot_security_updates`；新增 `.github/dependabot.yml`（github-actions + pip 周更）。
- 文档：`docs/CI.md` 同步步骤与新增「public 仓库安全姿态」节；总规范闸0 行补注 CI 复合动作。

## 三、验收标准

1. `.github/actions/content-verify/action.yml` 存在，两个步骤命令与退出码口径正确；
2. `pipeline-orchestrator.yml` / `html-sync.yml` 均含 `- uses: ./.github/actions/content-verify`，且位于生成 / 发布步骤之前；
3. 闸0 或内容硬门禁未通过时，对应 job 失败且不生成 HTML / 不进入计划；
4. `.github/dependabot.yml` 存在且 ecosystem 为 `github-actions` / `pip`；
5. `docs/CI.md` 步骤数与工作流实测一致；`unittest` / `validate.py` / `audit_pipeline --gate` 全绿；
6. 仓库设置三项安全能力均为 `enabled`。
