# AGENTS.md — jp-life-work 会话硬性规约

> 本文件对每一个在本仓库工作的 Agent 会话自动生效，优先级高于个人习惯。
> 与仓库内其它文档冲突时，以「硬性规约」节为准。
> **token 纪律**：本文件只放硬性规约与指针；细则下沉 `docs/`，按需读取，不预读、不批量读。

## 项目一句话

jp-life-work：围绕日本生活与工作（签证 / 就业 / 行业 / 税制 / 制度政策等 20 个主题方向）
的中文个人知识库；报告按自然月组织（`reports/YYYY-MM-<主题slug>.md` + `.html`），
工具链在 `engine/tools/`。规范与审计标准单一入口：`docs/README.md`。

## 硬性规约一：输入润色与确认门禁（必须遵守）

**任务型输入一律先润色、再确认、后执行；不得跳过，不得先执行后补。**

- **触发**：用户输入要求 Agent 执行动作（写码 / 改文件 / 跑命令 / 生成报告 / 调研 / 提交 / 推送等）。
  **不触发**：① 纯提问；② 确认（「确认」「继续」「好的」）；③ 补充信息；④ 闲聊；
  ⑤ 句末为问号（`？` / `?`）的疑问句。
- **判定口径**：以输入整体意图为准；「是否要求执行动作」与「句末是否问号」均为**机械判定**，
  不依赖特定工具或模型，任何 IDE（妙手 / Claude Code / Cursor 等）均须一致遵守。
- **三步**：① **润色**——重构为【目标】【背景】【约束】【期望输出】【原意核对】五段，不改变原意，
  歧义先列出请裁定；② **展示**——完整展示并停住，不调用工具、不执行、不预写文件；
  ③ **执行**——仅在用户确认后严格按最终确认版执行，不自行扩展、改写、增补。
- **确认的认定**：回复「确认 / 执行 / 同意 / 可以」或给出修改版均视为确认，以最后给出的版本为准。
- **无例外**：用户说「直接做 / 跳过确认」也不能跳过。
- 模板与边界：工作区 skill `prompt-polish-confirm`；可移植性：`docs/输入门禁可移植性方案.md`。

## 硬性规约二：并行会话三层隔离（必须遵守）

`main` 是唯一共享可变引用；直接改 main、直接 push、在共享检出目录裸跑可变 git 操作都会造成合并错误。
工具：`python engine/scripts/workflow_guard.py <命令>`。

1. **分支隔离**：任务一律 `python engine/scripts/workflow_guard.py task start <name>` 建分支 + 独立 worktree，
   在 `.worktrees/<name>/` 工作。
2. **串行合并**：只走 `python engine/scripts/workflow_guard.py merge <name>`（默认 PR 传输：推分支 → 建 PR → 等 `validate` / `audit` → 合并），禁止直接 push main（服务端分支保护已启用）。
3. **共享检出锁**：在仓库根做可变 git 操作用 `lock run`；对齐本地 main 用 `sync`，不要 `git pull` 硬拉。
4. **不碰别人的改动**：只提交本任务范围内文件。
5. 规范与异常：`docs/branch-management.md`。

**禁止**：`git push origin main`；无锁 `checkout/reset --hard` / `clean` / `stash`；
`--no-verify` 绕钩子；在共享检出目录跑 `build_hub.py` / `md2html.py`；跨 repo 改动。

## 硬性规约三：交付与审计协议（必须遵守）

报告交付物 = `reports/YYYY-MM-<slug>.md` 源稿 + 同名自包含 `.html`。落盘后、提交前按序：

1. `python engine/tools/md2html.py`（任务工作树内运行以生成本任务报告的 HTML，共享检出目录禁止）
   + `python engine/tools/lint_reports.py --new-only`；
2. `python engine/tools/auto_verify.py --report <路径>`（V1–V5，通过则幂等写回并重生成 HTML、自动提交审计）；
3. `python engine/tools/audit_preflight.py --report <路径>`（P0/P1 必须修正）；
4. `python engine/tools/audit_check.py --report <路径>`（L1–L5）；
5. `python engine/tools/audit_pipeline.py --submit --report <路径>`（第 2 步通过时自动完成）。

合并门禁：`python engine/tools/audit_pipeline.py --gate`。
详见 `docs/审计报告标准化管理体系.md` 与 `engine/report_templates/prompt-generic-base.md` 第八节。

## 文档导航（按需读取，勿预读）

| 需要什么 | 读什么 |
|---|---|
| 规范 / 审计 / 质量 / CI 总入口 | `docs/README.md` |
| 报告生产流程与门禁 | `docs/信息生产全链路执行规范.md` |
| 审计状态机与 L1–L5 | `docs/审计报告标准化管理体系.md` |
| 内容质量 C/S 码 | `docs/信息质量评估提示词体系.md` |
| 主题提示词与核验 | `docs/提示词库体系.md` |
| 报告周期与归档 | `docs/报告周期体系.md` |
| CI / 工作流 / 测试 | `docs/CI.md` |
| 分支与合并 | `docs/branch-management.md` |
| 批量更新本月报告 | `docs/月度批量更新唤醒词.md` |
| 工具链代码交付 | `docs/toolchain/TOOLCHAIN-DEV-SPEC.md` |

## 其它纪律（摘要）

- 报告命名 `reports/YYYY-MM-<主题slug>.md` + `.html`；主题目录 `NN-<slug>/`。
- 校验入口：`python engine/tools/validate.py`（退出码 1 阻断 / 2 警告放行）。
- **工作区卫生**：提交前 `python engine/scripts/cleanup_workspace.py`，`git status` 应无未跟踪残留。
- **批量更新唤醒词**：收到「本月报告全量更新」（别名：月度更新 / 月更 / 全更等）→ 读
  `docs/月度批量更新唤醒词.md` 严格执行。
- 信息质量 / 审计细则：`docs/` 下对应文档；工具链手册：`engine/tools/README.md`、`engine/scripts/README.md`。
