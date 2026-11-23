# 分支管理规范与操作手册（BRANCH-NAMING v1.1）

> 适用范围：`jp-life-work` 仓库全部本地开发分支与推送操作。
> 上位依据：`AGENTS.md` 硬性规约、`engine/scripts/README.md`（workflow_guard）、`docs/CI.md` 第十节。
> 单一事实源：`engine/scripts/branch_naming.py`（命名 / 校验 / 钩子安装）；钩子源：`engine/scripts/git-hooks/`。

## 一、命名规范

### 1.1 模板

```
task/<task-slug>-<sid>
```

| 组成 | 说明 | 示例 |
|---|---|---|
| `task/` | 开发分支固定前缀 | `task/` |
| `<task-slug>` | 任务名：小写字母 / 数字开头，仅含小写字母、数字、连字符，≤63 字符 | `monthly-update-2026-11` |
| `<sid>` | **会话标识短码**：当前会话 `CATPAW_CONVERSATION_ID`（UUID）前 8 位小写十六进制 | `bcbc4ed7` |

完整示例：`task/monthly-update-2026-11-bcbc4ed7`。

### 1.2 会话标识

- 会话标识 = 环境变量 `CATPAW_CONVERSATION_ID`（CatPaw 会话 UUID）。
- `sid` 派生：UUID 去掉连字符取前 8 位小写十六进制；会话标识缺失时回退
  `用户@主机` 的 SHA-1 前 8 位，并打印告警（短码不稳定，应设置会话 ID）。
- 分支只嵌入短码；**完整会话 ID 记录在任务登记表**（`.git/workflow-guard/tasks.json`
  的 `session` 字段）与本文件台账中，保证可追溯。

### 1.3 校验规则

- 正则：`^task/[a-z0-9][a-z0-9-]{0,60}-[0-9a-f]{8}$`。
- 豁免：`main` / `master` / `HEAD`；远程跟踪引用（`refs/remotes/*`）、tag、
  删除分支操作（local SHA 全 0）不校验。
- 非 `task/` 本地分支：默认放行并打印提示；设置 `BRANCH_NAMING_STRICT=1` 后阻断。
- 分支 `sid` 与当前会话不一致：**仅提示，不阻断**（分支归属创建会话，协作者可推送）。

### 1.4 手工校验

```bash
python engine/scripts/branch_naming.py session                 # 打印会话 ID 与 sid
python engine/scripts/branch_naming.py check task/x-11111111   # 校验分支名（退出码 1 不合规）
```

## 二、Git 钩子

### 2.1 安装（新克隆 / 换机后必做）

```bash
python engine/scripts/branch_naming.py install            # 或：python engine/scripts/workflow_guard.py hooks
python engine/scripts/branch_naming.py install --check    # 校验已安装且与源文件一致
python engine/scripts/branch_naming.py install --uninstall [--force]
```

安装内容：`pre-push`、`pre-commit` 与自包含副本 `branch_naming.py`（仓库无 `engine/scripts/` 时回退）。
安装位置：共享 git hooks 目录（`git rev-parse --git-path hooks`），跨 worktree 生效。
`--uninstall` 遇到被手工修改的钩子会拒绝删除，需 `--force`。

### 2.2 校验行为

| 钩子 | 触发 | 行为 |
|---|---|---|
| `pre-push` | `git push` | 逐条校验 `refs/heads/*`；不合规 `task/*` 阻断（退出码 1）；`main`、删除、非 heads 引用放行 |
| `pre-commit` | `git commit` | 当前分支为不合规 `task/*` 时阻断；`main` 与 detached HEAD（merge / rebase 中）放行 |

- 退出码：通用约定见 [CI](CI.md)；本钩子 `130` 表示中断。
- Python 解释器：依次尝试 `BRANCH_NAMING_PY` → `python` → `python3`；
  都没有则阻断并提示。
- CI 侧（GitHub Actions）在远端 runner 直接推 `main`，不经过本地钩子，不受影响。

## 三、分支生命周期与角色职责

| 角色 | 执行标准 |
|---|---|
| 开发（Agent / 人） | 一律 `python engine/scripts/workflow_guard.py task start <name>` 建分支（自动带 sid）；在 `.worktrees/<name>/` 内工作；不在共享检出目录改文件 |
| 评审 | 只读任务分支 / worktree；不改名、不合并 |
| 合并 | 只走 `python engine/scripts/workflow_guard.py merge <name>`（串行锁 + 校验 + PR 传输：推分支 → 建 PR → 等检查 → 合并）；禁止直接 push `main`（服务端分支保护已启用） |
| 收尾 | `python engine/scripts/workflow_guard.py task stop <name>`（已合并后清理分支与工作树） |
| 仓库维护 | 新克隆 / 换机后安装钩子（§2.1）；每季度核对台账与存量分支命名 |

### 3.1 服务端分支保护（main）

`main` 已启用分支保护：**Require pull request before merging** + **Require status checks**
（`validate` / `audit`）+ **Do not bypass for administrators**（enforce_admins）+ 禁 force-push / 禁删除。
因此 `merge` 默认走 PR 传输（`--transport auto`）：直推 `main` 会被服务端拒绝；
`--transport direct` 仅用于非 GitHub 远端或本地测试。

### 3.2 CI 自动化 PR 免审批自动合并

6 条工作流（8 个提交点）产出的 `[automated]` PR 经复合动作
`.github/actions/auto-merge-pr` 创建并启用自动合并；仓库设置 `allow_auto_merge=true`。
质量门不变：必需检查 `validate` / `audit` 通过后才合入，未通过保持打开。
仓库为纯个人项目、无第三方评审，故不设人工审批（分支保护 `required_approving_review_count=0`）。

## 四、存量分支梳理与映射台账

### 4.1 本次补全（2026-11-17）

对 `task/*` 历史分支按任务登记表的 `owner`（`catpaw:<会话 UUID>`）派生 sid 并重命名，
同步更新 `.git/workflow-guard/tasks.json` 的 `branch` / `session` 字段。
`git branch -m` 由 git 自动更新各 worktree 的 HEAD 引用，无需重建工作树。

| 任务 | 分支（补全后） | sid | 完整会话 ID | 状态 |
|---|---|---|---|---|
| monthly-update-2026-11 | `task/monthly-update-2026-11-bcbc4ed7` | `bcbc4ed7` | `bcbc4ed7-df02-40d5-b832-70055a0aff08` | 已合入 main（登记 active，未走 merge 登记） |
| mainline-integration-assessment | `task/mainline-integration-assessment-c00bdcd2` | `c00bdcd2` | `c00bdcd2-f448-46d0-bd63-8b50c29dbb82` | merged（`ecd7696`） |
| mainline-spec-landing | `task/mainline-spec-landing-88528c9a` | `88528c9a` | `88528c9a-6946-4848-b23c-516a98e6ce43` | merged（`0767ea3`） |
| branch-naming-session-id | `task/branch-naming-session-id-f445e0a2` | `f445e0a2` | `f445e0a2-fb01-46f0-bd36-2dccbb14feaf` | merged（功能提交 `2a633d2`；修正 `597ed3b` / `43f0724`） |

注：`mainline-spec-landing` 的任务登记与本地分支已在合并后清理（`task stop`），
本表保留其历史映射；`monthly-update-2026-11` 登记状态仍为 `active`（分支已合入 main，
未走 `merge` 登记），均未擅自改动其登记。

### 4.2 后续新增分支

一律经 `task start` 生成，无需手工改名；台账以 `.git/workflow-guard/tasks.json`
为唯一数据源，本表只记录跨会话需要追溯的历史条目。

## 五、异常处理方案

| 场景 | 现象 | 处理 |
|---|---|---|
| 推送被 pre-push 拦截 | `阻断推送：分支名不合规…` | 用 `task start` 重建分支；不要绕过钩子（`--no-verify` 仅限钩子自身故障，且需记录） |
| 提交被 pre-commit 拦截 | `阻断提交：分支名不合规…` | 切回合规任务分支或 `main`；不要在不合规分支上继续提交 |
| 钩子误拦截 `main` / 合规分支 | 检查 `python engine/scripts/branch_naming.py check <branch>` | 若仍误判，`python engine/scripts/branch_naming.py install --check` 核对钩子版本；必要时 `install --uninstall` 后重装 |
| 会话标识缺失 | 建分支时告警 `未设置 CATPAW_CONVERSATION_ID` | 设置会话 ID 后重命名分支补 sid（`git branch -m`），并更新台账 |
| 钩子未安装（新克隆） | 不合规分支可推送 | 立即 `python engine/scripts/branch_naming.py install`；存量分支按 §4 流程补全 |
| 分支已推送才发现不合规 | 远端存在旧名分支 | 本地重命名后推新分支，删除远端旧分支（`git push origin --delete <旧名>`），台账登记 |
| 合并冲突 | `merge` 保留 `.worktrees/_merge` | 按 `engine/scripts/README.md` 第四节处理；重命名不影响合并（按任务名查登记） |

## 六、验证清单（本次落地记录）

- [x] 单元测试：`engine/tests/test_branch_naming.py`（19 项：sid 派生 / 校验 / pre-push / pre-commit / 安装器）。
- [x] 既有测试适配：`test_workflow_guard.py`、`test_cov_workflow.py`（固定会话 ID，断言新分支格式）。
- [x] 端到端（临时仓库 + 临时远端）：不合规 `task/bad` push 被拦截；不合规分支提交被拦截；
      合规 `task/good-11111111` 放行；`main` 放行；`task start` 生成分支并推送成功；
      `merge` 合并入临时 `main` 成功。
- [x] 存量 4 条分支补全 sid，worktree HEAD 自动跟随，任务登记表同步更新。
- [x] 全量测试与 `validate.py` 通过（见提交说明）。

## 七、变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-17 | 建立 `task/<slug>-<sid>` 规范、`branch_naming.py`、pre-push / pre-commit 钩子、存量补全与台账 |
| v1.1 | 2026-11-22 | 合并流程 PR 化（`merge --transport pr`：推分支 → 建 PR → 等检查 → 合并）+ `main` 服务端分支保护；新增 §3.1 |
| v1.2 | 2026-11-23 | CI 自动化 PR 免审批自动合并：新增复合动作 `.github/actions/auto-merge-pr`，6 条工作流 8 个提交点接线，仓库设置启用 `allow_auto_merge`；新增 §3.2 |
