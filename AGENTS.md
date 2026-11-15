# AGENTS.md — jp-life-work 会话硬性规约

> 本文件对每一个在本仓库工作的 Agent 会话自动生效，优先级高于个人习惯。
> 与仓库内其它文档冲突时，以「硬性规约」节为准。

## 项目一句话

jp-life-work：围绕日本生活与工作（签证 / 就业 / 行业 / 税制 / 制度政策等 20 个主题方向）
的中文个人知识库；报告按自然月组织（`reports/YYYY-MM-<主题slug>.md` + `.html`），
工具链在 `src/prompts-tools/tools/`。

## 硬性规约：并行会话三层隔离（必须遵守）

`main` 是唯一共享可变引用：多个 Agent 会话与 GitHub Actions 同时写它。
**直接改 main、直接 push、在共享检出目录裸跑可变 git 操作，都会造成合并错误。**

工具：`python tools/workflow_guard.py <命令>`
（详文档 `tools/README.md`；会话规约 `.meituan-catpaw/5833106238/skills/workflow-guard/SKILL.md`）。

1. **分支隔离（任务间）**——任务一律开分支 + 独立 worktree，不直接在共享检出目录改文件：
   ```bash
   python tools/workflow_guard.py task start <name>     # 建 task/<name> + .worktrees/<name>
   ```
   然后在 `.worktrees/<name>/` 里工作。

2. **串行合并（main 级）**——合并只走 `merge`，禁止直接 push main：
   ```bash
   python tools/workflow_guard.py merge <name>          # 串行 merge 锁 + 隔离合并 + validate.py + --force-with-lease
   ```
   冲突时保留 `.worktrees/_merge` 供处理，不污染共享目录。

3. **共享检出锁（工作目录级）**——在共享检出目录（仓库根）做任何可变 git 操作前先拿锁：
   ```bash
   python tools/workflow_guard.py lock run checkout -- git switch <branch>
   python tools/workflow_guard.py lock run checkout -- git commit -m "..."
   ```
   推荐 `lock run`（结束自动释放）；手工 `lock acquire` 须在 30 分钟内 `lock release`。

4. **不碰别人的改动**——只提交自己任务范围内的文件；发现非本会话的未完成改动，
   原样保留、不暂存、不提交、不推送。

5. **对齐本地 main** 用 `python tools/workflow_guard.py sync`，不要 `git pull` 硬拉。

### 禁止事项

- 不要 `git push origin main`（除非用户明确指示，且确认已过校验）。
- 不要 `git checkout/reset --hard`、`git clean`、`git stash` 而不持检出锁。
- 不要在 task 分支未合并时 `task stop`（确需丢弃用 `--force`，且先告知用户）。
- 不要在共享检出目录运行 `build_hub.py` / `md2html.py`；`md2html.py` 可在任务工作树内运行以生成本任务报告的 HTML（`build_hub.py` 仍由主会话统一执行）。
- 本仓库改动仅限本仓库，不跨 repo。

## 交付与审计协议（与提示词规范 / CI 同一口径）

报告交付物 = `reports/YYYY-MM-<slug>.md` 源稿 + 同名自包含 `.html`。落盘后、提交前必须按序完成（缺一不得提交）：

1. **HTML 生成**：`python src/prompts-tools/tools/md2html.py`（任务工作树内；共享检出目录禁止）+ `python src/prompts-tools/tools/lint_reports.py --new-only`；
2. **落盘前自检**：`python src/prompts-tools/tools/audit_preflight.py --report <路径>`（P0/P1 必须修正）；
3. **多层级校验**：`python src/prompts-tools/tools/audit_check.py --report <路径>`（L1–L5，P0/P1 必须修正）；
4. **提交审计**：`python src/prompts-tools/tools/audit_pipeline.py --submit --report <路径>`。

合并门禁：`python src/prompts-tools/tools/audit_pipeline.py --gate`（PR / main 推送；受检报告须 `audited` + 指纹匹配 + 有效 L5 证据）。
CI 侧：`html-sync` 负责推送后确定性重生成 HTML / 汇总页；`audit-gate` 负责 `--gate` 与 `audit_check --all`。
详见 `src/report_templates/prompt-generic-base.md` 第八节与《审计报告标准化管理体系》。

## 其它既有纪律（摘要）

- 报告命名 `reports/YYYY-MM-<主题slug>.md` + `.html`；主题目录 `NN-<slug>/`。
- 校验入口：`python src/prompts-tools/tools/validate.py`（退出码 1 阻断 / 2 警告放行）。
- CI 流水线与本地协作机制：`docs/CI.md`；信息质量 / 审计体系：`docs/` 下对应文档。
