---
name: local-first-remote-fallback
description: jp-life-work 工作三原则「本地优先、远程兜底、结果分享」的可复用流程。当任务涉及本地与远程协作、git 提交/推送、结果交付与分享时使用；也可作为默认交付策略。
---

# 本地优先、远程兜底、结果分享

> 一句话流程：**先在本地的任务工作树把事做完并验证 → 远端（GitHub）只作备份 / 容灾与兜底通道 → 完成后按门禁合并、推送、把结果分享出去。**

本 skill 把三原则固化为可复用流程，与 `AGENTS.md` 硬性规约、`workflow-guard`、`git_push.py`、
交付与审计协议对齐。**细则不在此复述**，一律以指针指向的规范为准（单一事实源）。

## 一、三原则

| 原则 | 定义 | 硬性判据 |
|---|---|---|
| **本地优先** | 本地是工作与事实源：任务一律在 `.worktrees/<name>/` 内完成并验证；共享检出目录（仓库根）只做只读或持锁操作 | 未在共享检出目录裸改文件；本地校验通过才算完成 |
| **远程兜底** | 远端（GitHub）不是主路径：作备份 / 容灾；本地主通道失败才切远端备用通道 | 推送先 `origin`（ssh），失败才 `origin-https`（https）；两通道都失败即停止、不重试 |
| **结果分享** | 完成即按门禁交付：串行合并入 `main` 并推送，产出可浏览 / 可分享产物（报告 HTML、文档、索引页） | 只走 `workflow_guard merge`；产物随提交入库 |

## 二、标准流程（四阶段）

### 阶段 0 · 判定与确认

- 判断输入是否为任务型（要求执行动作）。任务型 → 先走输入门禁
  （skill `prompt-polish-confirm` / `docs/输入润色与确认门禁.md`）：**润色 → 展示 → 等确认 → 执行**，不得跳过、不得自行扩展。
- 不可逆或影响共享状态的操作（push、删文件、改 main、发外部消息）**强制确认**。

### 阶段 1 · 本地优先（完成 + 验证）

```bash
python engine/scripts/workflow_guard.py task start <name>     # 建 task/<name>-<sid> + .worktrees/<name>
cd .worktrees/<name>                                          # 在任务工作树内工作
# ... 改动 ...
python engine/tools/validate.py                                # 结构与规范校验（退出码 1 阻断 / 2 放行）
python engine/scripts/cleanup_workspace.py --check             # 工作区卫生零残留
# 视任务补充：lint_reports.py --new-only / unittest / 报告类门禁（AGENTS.md 硬性规约三）
```

- 只提交本任务范围内文件；**不碰他人的改动**（发现非本会话的未完成改动，原样保留、不暂存、不提交、不推送）。
- 本地校验未通过 → 不进入阶段 2 / 3。

### 阶段 2 · 远程兜底（提交 + 双通道推送）

```bash
git add <本任务文件> && git commit -m "..."
# 需要显式推送时（merge 会自动推送，一般无需单独执行）：
python engine/scripts/git_push.py --remote origin [--fallback origin-https] [--force-with-lease] HEAD:<branch>
```

- 通道语义：主通道 `origin`（ssh）；失败切 `origin-https`（https）；两条都失败即停止、**不重试**。
- **仅限本 repo**：推送 / 合并 / 提交只走 GitHub，永不使用 GitLab。

### 阶段 3 · 结果分享（合并 + 交付）

```bash
python engine/scripts/workflow_guard.py merge <name>          # 串行合并入 main（校验 + force-with-lease 推送）
python engine/scripts/workflow_guard.py task stop <name>       # 收尾：删工作树与分支
```

- `merge` 冲突 → 保留 `.worktrees/_merge` 供人工处理；放弃用 `merge --cleanup`。
- 产物（报告 md + html / 文档 / 索引页）随合并入库，完成分享。

## 三、检查清单（提交前逐项）

- [ ] 输入已过门禁（任务型已确认）
- [ ] 在任务 worktree 内工作，未在共享检出目录裸改
- [ ] 本地校验通过（`validate.py` 退出码 ∈ {0,2}）
- [ ] 报告类产物已走交付与审计协议（`md2html.py` / `auto_verify.py` / `audit_preflight.py` / `audit_check.py` / `audit_pipeline.py`）
- [ ] `cleanup_workspace.py --check` 零残留
- [ ] 只提交本任务文件
- [ ] 合并走 `merge`，未直推 main

## 四、边界与禁止

- 禁止 `git push origin main`；禁止无锁 `checkout / reset --hard / clean / stash`；禁止 `--no-verify` 绕钩子（钩子自身故障除外且需记录）。
- 禁止在共享检出目录运行 `build_hub.py` / `md2html.py`（`md2html.py` 可在任务工作树内运行以生成本任务报告的 HTML）。
- 禁止跨 repo 修改。
- 网络：两通道都失败即停止并如实报告，不刷屏重试。
- 结果分享以事实为准：不虚报校验结果；未验证的项标注「未核验」。

## 五、指针（细则不在此复述）

- 三层隔离 / 合并 / 锁 / 双通道推送：`engine/scripts/README.md`、`docs/branch-management.md`、skill `workflow-guard`
- 输入门禁：skill `prompt-polish-confirm`、`docs/输入润色与确认门禁.md`
- 交付与审计协议：`AGENTS.md` 硬性规约三、`docs/审计报告标准化管理体系.md`
- 工作区卫生：`engine/scripts/cleanup_workspace.py`
