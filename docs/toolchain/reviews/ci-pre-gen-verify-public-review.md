# 双轴评审：CI 生成前信息核验接入 + public 安全姿态（ci-pre-gen-verify-public）

> **版本**：v1.0（2026-11-22）
> **分支**：`task/ci-pre-gen-verify-public-<sid>`
> **规格 / 工单**：[specs/ci-pre-gen-verify-public.md](../specs/ci-pre-gen-verify-public.md) / [tickets/ci-pre-gen-verify-public.md](../tickets/ci-pre-gen-verify-public.md)
> **评审结论**：Standards 无 P0/P1；Spec 无 P0/P1。

## 一、Standards 轴（规约符合性）

| 条款 | 结论 | 证据 |
|---|---|---|
| 适用范围（TOOLCHAIN-DEV-SPEC 二） | 通过 | 变更位于 `.github/workflows/`、`.github/actions/`、`.github/dependabot.yml` 与 `docs/`，属工具链 / CI 域 |
| 命名（四） | 通过 | 复合动作目录 `content-verify`（kebab-case）；规格 / 工单 / 评审 slug 一致 |
| 退出码契约（五） | 通过 | 动作内显式允许闸0 退出码 {0,2}，其余非零失败；内容硬门禁仅 0 放行 |
| 单一事实源 | 通过 | 复用 `generation_gate.py` / `verified_content_gate.py` 内核，未新写判定；CI.md 第十六节为 public 姿态唯一说明 |
| 工作流最小权限 / 清理接线 | 通过 | 未改 `permissions`；`test_cleanup.TestCiWiring` 51 项全绿（前置 + 收尾 always 清理仍在） |
| 文档↔实现对齐 | 通过 | `test_arch_guard` 全绿；CI.md §2.2 / §2.8 步骤数与工作流实测一致 |
| 生成物确定性 | 通过 | 未改生成器；无时间戳 |

## 二、Spec 轴（验收标准映射）

| 验收 | 结论 | 证据 |
|---|---|---|
| 1. 复合动作存在且步骤 / 退出码正确 | 通过 | `.github/actions/content-verify/action.yml`：步骤 1 `generation_gate.py --all`（0/2 放行），步骤 2 `verified_content_gate.py --all`（仅 0）；未通过输出 `::error::` |
| 2. 两工作流接入且位于生成 / 发布前 | 通过 | `pipeline-orchestrator.yml`：`安装依赖` → `content-verify` → `触发检测`；`html-sync.yml`：`安装依赖` → `content-verify` → `md2html.py` |
| 3. 未通过则失败且不生成 | 通过 | 动作非零退出即复合步骤失败，后续步骤不再执行（`set -e` + 显式 exit） |
| 4. dependabot.yml | 通过 | `.github/dependabot.yml` 含 `github-actions` / `pip`，interval=weekly |
| 5. 文档同步 + 回归全绿 | 通过 | CI.md v2.31（§2.2 8 步 / §2.8 6 步 / 第十六节）；总规范 v1.12；`validate.py` 退出码 0；定向 51 项测试 OK |
| 6. 仓库三项安全能力 enabled | 通过 | `gh api repos/hmbphxkw76-byte/jp-life-work` → `secret_scanning.enabled` / `secret_scanning_push_protection.enabled` / `dependabot_security_updates.enabled` |

## 三、实跑证据（摘要）

```
$ python engine/tools/generation_gate.py --all
生成前信息核验（闸0）：21 个主题，可生成 21 / 阻断 0
  P0 0 / P1 0 / P2 1
gen_exit=2

$ python engine/tools/verified_content_gate.py --all
无法核实内容门禁：受检 160 份，命中 0 处（全层零容忍）
vc_exit=0

$ python engine/tools/validate.py
结构与规范校验通过：通用层完整、业务线结构齐全、命名合规
validate_exit=0

$ python -m unittest engine.tests.test_arch_guard engine.tests.test_cleanup engine.tests.test_tools.TestProcessReuse
Ran 51 tests ... OK
```

## 四、残留与说明

- **服务端分支保护未启用**：GitHub Free 公共仓库支持分支保护，但 `workflow_guard merge` 直推 `origin/main`，启用 required status checks / PR 门禁需先改造合并流程；当前依赖本地 `workflow_guard` + pre-commit 内容硬门禁 + `validate.yml` / `audit-gate.yml`。已记入 CI.md 第十六节。
- **GitHub Pages 保持 public**：与 PUBLIC 仓库一致，提供 `index.html` 在线阅读；未改。
- **历史过程留痕未删除**：`docs/toolchain/{tickets,reviews,specs}` 与 `docs/` 下 2026-11-19 过程留痕按仓库「保留在库、不纳入规范清单」规则保留，本次不清理（避免破坏 `review_gate` / `TestReviewCoverage` 等守卫）。
