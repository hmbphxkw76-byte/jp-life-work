---
name: workflow-guard
description: jp-life-work 并行会话三层隔离机制（任务分支 / 串行合并 / 共享检出锁）。当本仓库有并行任务、多个会话同时改动、需要提交或推送 git、或要把任务分支合入 main 时使用。确保任务之间、会话之间不互相覆盖，避免合并错误。
---

# jp-life-work 并行协作三层隔离

本仓库的 `main` 是唯一共享可变引用：多个 Agent 会话与 4 个 GitHub Actions 都在写它。
**直接改 main、直接 push、在共享目录里裸跑 git 可变操作，都会造成合并错误。**

工具：`python tools/workflow_guard.py <命令>`（详文档：`tools/README.md`）。

## 硬性规约

1. **任务一律开分支 + 独立 worktree**，不直接在共享检出目录改文件：
   ```bash
   python tools/workflow_guard.py task start <name>     # 建 task/<name>-<sid> + .worktrees/<name>
   ```
   然后在 `.worktrees/<name>/` 里工作。

2. **合并只走 `merge`，禁止直接 push main**：
   ```bash
   python tools/workflow_guard.py merge <name>
   ```
   它串行（merge 锁）、在隔离工作树里合并、跑 `validate.py`、`--force-with-lease` 推送。
   冲突时会保留 `.worktrees/_merge` 供处理，不污染共享目录。

3. **在共享检出目录（仓库根）做任何可变 git 操作前先拿锁**：
   ```bash
   python tools/workflow_guard.py lock run checkout -- git switch <branch>
   python tools/workflow_guard.py lock run checkout -- git commit -m "..."
   ```
   推荐 `lock run`（结束自动释放）；手工 `lock acquire` 必须在 30 分钟内 `lock release`。

4. **不碰别人的改动**：只提交自己任务范围内的文件；发现非本会话的未完成改动，
   原样保留、不暂存、不提交、不推送。

5. **分支命名与会话标识**：开发分支一律 `task/<name>-<sid>`（`sid` = 会话标识前 8 位），
   由 `task start` 自动追加；新克隆 / 换机后先装钩子 `python tools/workflow_guard.py hooks`。
   规范与异常处理见 `docs/branch-management.md`。

6. **对齐本地 main** 用 `sync`，不要 `git pull` 硬拉：
   ```bash
   python tools/workflow_guard.py sync
   ```

## 不要做

- 不要 `git push origin main`（除非用户明确指示，且确认已过校验）。
- 不要 `git checkout/reset --hard`、`git clean`、`git stash` 而不持检出锁。
- 不要用 `lock acquire` 长时间占锁（超过 30 分钟会自动失效，可能被别人强取）。
- 不要用 `--no-verify` 绕过分支命名钩子（钩子自身故障除外，且需记录）。
- 不要在 task 分支未合并时 `task stop`（确需丢弃用 `--force`，且先告知用户）。
- 不要在共享检出目录运行 `build_hub.py` / `md2html.py`；`md2html.py` 可在任务工作树内运行以生成本任务报告的 HTML（`build_hub.py` 仍由主会话统一执行）。交付与审计协议见 `AGENTS.md`。

## 遇到锁被占用

先看是谁：`python tools/workflow_guard.py lock status`。
确认对方已停手再 `--force` 强取；**不要**默认强取。

## 状态总览

```bash
python tools/workflow_guard.py status     # 锁 / 任务 / worktree
```
