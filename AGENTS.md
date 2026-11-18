# AGENTS.md — jp-life-work 会话硬性规约

> 本文件对每一个在本仓库工作的 Agent 会话自动生效，优先级高于个人习惯。
> 与仓库内其它文档冲突时，以「硬性规约」节为准。

## 项目一句话

jp-life-work：围绕日本生活与工作（签证 / 就业 / 行业 / 税制 / 制度政策等 20 个主题方向）
的中文个人知识库；报告按自然月组织（`reports/YYYY-MM-<主题slug>.md` + `.html`），
工具链在 `engine/tools/`。

## 硬性规约：输入润色与确认门禁（必须遵守）

**任务型输入一律先润色、再确认、后执行；不得跳过，不得先执行后补。**

- **触发**：用户输入要求 Agent 执行动作（写码 / 改文件 / 跑命令 / 生成报告 / 调研 / 提交 / 推送等）。
  **不触发（直接回答，不进入本门禁）**——**穷举如下，此外一律视为任务型输入**：
  ① 纯提问；② 确认（「确认」「继续」「好的」）；③ 补充信息；④ 闲聊；
  ⑤ **句末为问号（`？` / `?`）的疑问句**。
- **判定口径**：以输入整体意图为准；「是否要求执行动作」与「句末是否问号」均为**机械判定**，
  不依赖特定工具或模型，任何 IDE（妙手 / Claude Code / Cursor 等）均须一致遵守。
- **三步，缺一不可**：
  1. **润色**：先不执行，把原始输入重构为结构化提示词，含
     【目标】【背景】【约束】【期望输出】【原意核对】五段；可补充必要上下文，**不得改变原意**；
     发现歧义先列出请用户裁定，不擅自假设。
  2. **展示**：完整展示润色后的提示词，请用户「确认执行」或给出修改版；
     展示后**停住**——不调用工具、不执行、不预写文件。
  3. **执行**：仅在用户确认后，严格按**最终确认版**执行；
     不得自行扩展、改写、增补；执行中遇到必须由用户决策的分叉，停下询问。
- **确认的认定**：用户回复「确认 / 执行 / 同意 / 可以」或给出修改版，均视为确认；
  以用户**最后给出**的版本为准。
- **无例外**：用户说「直接做 / 跳过确认」也不能跳过；说明该门禁为硬性规约后，仍需确认一次。
- 模板、展示格式与边界情况见工作区 skill `prompt-polish-confirm`。
- 可移植性（跨 IDE / 跨模型 / 跨机器）：见 `docs/输入门禁可移植性方案.md`；
  新机器 `git clone` 后运行 `python engine/scripts/bootstrap_gate.py --install` 完成部署与自检。

## 硬性规约：并行会话三层隔离（必须遵守）

`main` 是唯一共享可变引用：多个 Agent 会话与 GitHub Actions 同时写它。
**直接改 main、直接 push、在共享检出目录裸跑可变 git 操作，都会造成合并错误。**

工具：`python engine/scripts/workflow_guard.py <命令>`
（详文档 `engine/scripts/README.md`；会话规约 `.meituan-catpaw/5833106238/skills/workflow-guard/SKILL.md`）。

1. **分支隔离（任务间）**——任务一律开分支 + 独立 worktree，不直接在共享检出目录改文件：
   ```bash
   python engine/scripts/workflow_guard.py task start <name>     # 建 task/<name>-<sid> + .worktrees/<name>
   ```
   然后在 `.worktrees/<name>/` 里工作。

2. **串行合并（main 级）**——合并只走 `merge`，禁止直接 push main：
   ```bash
   python engine/scripts/workflow_guard.py merge <name>          # 串行 merge 锁 + 隔离合并 + validate.py + --force-with-lease
   ```
   冲突时保留 `.worktrees/_merge` 供处理，不污染共享目录。

3. **共享检出锁（工作目录级）**——在共享检出目录（仓库根）做任何可变 git 操作前先拿锁：
   ```bash
   python engine/scripts/workflow_guard.py lock run checkout -- git switch <branch>
   python engine/scripts/workflow_guard.py lock run checkout -- git commit -m "..."
   ```
   推荐 `lock run`（结束自动释放）；手工 `lock acquire` 须在 30 分钟内 `lock release`。

4. **不碰别人的改动**——只提交自己任务范围内的文件；发现非本会话的未完成改动，
   原样保留、不暂存、不提交、不推送。

5. **对齐本地 main** 用 `python engine/scripts/workflow_guard.py sync`，不要 `git pull` 硬拉。

6. **分支命名与会话标识**——开发分支一律 `task/<name>-<sid>`（`sid` = 会话标识前 8 位），
   由 `task start` 自动追加；新克隆 / 换机后先装钩子：
   ```bash
   python engine/scripts/workflow_guard.py hooks     # 安装 pre-push / pre-commit
   ```
   规范与异常处理见 `docs/branch-management.md`。

### 禁止事项

- 不要 `git push origin main`（除非用户明确指示，且确认已过校验）。
- 不要 `git checkout/reset --hard`、`git clean`、`git stash` 而不持检出锁。
- 不要在 task 分支未合并时 `task stop`（确需丢弃用 `--force`，且先告知用户）。
- 不要在共享检出目录运行 `build_hub.py` / `md2html.py`；`md2html.py` 可在任务工作树内运行以生成本任务报告的 HTML（`build_hub.py` 仍由主会话统一执行）。
- 不要用 `--no-verify` 绕过分支命名钩子（钩子自身故障除外，且需在提交说明中记录）。
- 本仓库改动仅限本仓库，不跨 repo。

## 交付与审计协议（与提示词规范 / CI 同一口径）

报告交付物 = `reports/YYYY-MM-<slug>.md` 源稿 + 同名自包含 `.html`。落盘后、提交前必须按序完成（缺一不得提交）：

1. **HTML 生成**：`python engine/tools/md2html.py`（任务工作树内；共享检出目录禁止）+ `python engine/tools/lint_reports.py --new-only`；
2. **生成后自动验证（无人值守入口）**：`python engine/tools/auto_verify.py --report <路径>`
   —— 依次执行 V1–V5 规则集（交付物可访问 / 必填字段与要素 / 格式合规 / 数据准确性与一致性 / 关键指标数值范围），
   通过则**幂等写回**报告「## 自动验证结果」章节、重新生成 HTML 并**自动 `audit_pipeline --submit`**；
   失败退出码 1 并打印逐条定位（规则 / 位置 / 详情），不写回、不提交。规则内核复用
   `audit_preflight` / `audit_check` / `compliance_check` / `lint_reports`，运行日志写入
   `engine/report-audits/audit/verify/`（不入库）。可用 `--dry-run`（只验证不写回）/ `--no-submit`；
3. **落盘前自检**：`python engine/tools/audit_preflight.py --report <路径>`（P0/P1 必须修正）；
4. **多层级校验**：`python engine/tools/audit_check.py --report <路径>`（L1–L5，P0/P1 必须修正）；
5. **提交审计**：`python engine/tools/audit_pipeline.py --submit --report <路径>`
   （第 2 步 auto_verify 已通过时自动完成，可复核）。

合并门禁：`python engine/tools/audit_pipeline.py --gate`（PR / main 推送；受检报告须 `audited` + 指纹匹配 + 有效 L5 证据）。
CI 侧：`html-sync` 负责推送后确定性重生成 HTML / 汇总页；`audit-gate` 负责 `--gate` 与 `audit_check --all`。
详见 `engine/report_templates/prompt-generic-base.md` 第八节与《审计报告标准化管理体系》。

## 其它既有纪律（摘要）

- 报告命名 `reports/YYYY-MM-<主题slug>.md` + `.html`；主题目录 `NN-<slug>/`。
- 校验入口：`python engine/tools/validate.py`（退出码 1 阻断 / 2 警告放行）。
- **批量更新唤醒词**：收到「本月报告全量更新」（别名：月度报告批量更新 / 一键更新本月报告 /
  执行本月报告更新 / 月度更新 / 月更 / 全更）→ 读取并严格执行
  `docs/月度批量更新唤醒词.md`（七步流程 + 平台挂载）。
- **工作区卫生**：提交前运行 `python engine/scripts/cleanup_workspace.py`（缓存 / 临时文件 / 运行日志），
  随后 `git status` 应无未跟踪残留；`--check` 可用于自检（发现残留退出码 1）。
  运行日志不入库（`.gitignore`：`engine/vocabulary/data/*.log`）。流水线各阶段由
  `.github/actions/workspace-cleanup` 自动执行前置 / 收尾清理，`validate.yml` 的
  `workspace-hygiene` job 断言零残留。详见 `docs/CI.md` 第十三节与 `engine/scripts/README.md` 第九节。
- CI 流水线与本地协作机制：`docs/CI.md`；信息质量 / 审计体系：`docs/` 下对应文档。
