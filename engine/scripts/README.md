# workflow_guard —— 并行会话三层隔离机制

> 面向 jp-life-work 的多会话 / 多任务并行开发。解决「多个 Agent 会话与 GitHub Actions
> 同时写同一个 `main` 和同一个工作目录」导致的推送被拒、互相覆盖、裹入他人改动等合并错误。
>
> 工具：`engine/scripts/workflow_guard.py`（纯标准库，Windows / POSIX 通用）
> 状态：`.git/workflow-guard/`（不入库、跨 worktree 共享）
> 测试：`engine/tests/test_workflow_guard.py`

## 一、三层隔离

```
第 1 层  分支隔离（任务间）   task start / list / stop
                                  每任务一条 task/<name>-<sid> 分支 + 独立 worktree
        │
第 2 层  串行合并（main 级）  merge
                                  全局 merge 锁 + 隔离合并工作树 + 校验 + force-with-lease
        │
第 3 层  共享检出锁（工作目录级） lock acquire / release / run / status
                                  共享检出目录的 checkout / commit / stash / reset 前先拿锁
```

**为什么是这三层**：`main` 是唯一共享可变引用。第 1 层让任务之间文件级互不越界；
第 3 层让共享目录同一时刻只有一个写入者；第 2 层让「进入 main」这条路只有一条、
串行、可校验、失败不留残局。

## 二、典型工作流

```bash
# 1) 开任务：建分支 + 独立工作树（默认；也可以 --no-worktree 只建分支）
python engine/scripts/workflow_guard.py task start exit-transition-return
cd .worktrees/exit-transition-return        # 在任务工作树里干活

# 2) 干完活：串行合并回 main（自动 fetch → 隔离工作树合并 → 校验 → 推送）
python engine/scripts/workflow_guard.py merge exit-transition-return

# 3) 收尾：删工作树与分支
python engine/scripts/workflow_guard.py task stop exit-transition-return

# 4) 别的会话把本地 main 对齐远端
python engine/scripts/workflow_guard.py sync
```

在**共享检出目录**（仓库根，非任务工作树）里做任何可变 git 操作，先拿锁：

```bash
# 推荐：lock run 短借快还，命令失败也会自动释放
python engine/scripts/workflow_guard.py lock run checkout -- git switch task/x
python engine/scripts/workflow_guard.py lock run checkout -- git commit -m "..."

# 不推荐：手工 acquire 容易忘还（超时 30 分钟后自动失效）
python engine/scripts/workflow_guard.py lock acquire checkout --op "改配置"
python engine/scripts/workflow_guard.py lock release checkout
```

## 三、命令速查

| 命令 | 作用 |
|---|---|
| `task start <name> [--no-worktree] [--base <ref>]` | 建 `task/<name>-<sid>` 分支（`sid`=会话标识前 8 位，默认基于 `origin/main`）+ 独立 worktree |
| `task list` | 列出任务登记与 worktree 实况 |
| `task stop <name> [--force]` | 删工作树与分支（未合并 / 有未提交改动需 `--force`） |
| `lock acquire <checkout\|merge> [--op S] [--wait N] [--force]` | 拿锁 |
| `lock release <checkout\|merge> [--force]` | 放锁（非本人持有需 `--force`） |
| `lock status` | 查看两把锁 |
| `lock run <checkout\|merge> -- <命令...>` | 持锁执行命令，结束自动释放 |
| `merge <name> [--no-verify] [--verify-cmd S] [--ff-only] [--wait N] [--cleanup] [--push-fallback S]` | 串行合并入 main |
| `sync [--push-local] [--push-fallback S]` | 持检出锁对齐本地 main 与远端 |
| `status` | 总览：锁 / 任务 / worktree |
| `hooks [--check] [--uninstall] [--force]` | 安装 / 校验 / 卸载分支命名钩子（pre-push / pre-commit） |
| `python engine/scripts/git_push.py --remote origin [--fallback origin-https] [--force-with-lease] <refspec...>` | ssh / https 双通道推送（都失败即停止） |

退出码：`0` 成功；`1` 失败（锁被占用、合并冲突、校验阻断等）；`130` 中断。

## 四、合并语义（第 2 层细节）

1. **串行**：全局 `merge.lock`，同一时刻只允许一个合并；后来者默认快速失败，
   `--wait N` 可排队等待。
2. **隔离**：合并不动共享检出目录。工具新建 `.worktrees/_merge`（detached，起点
   `origin/main`），在里面合并、校验、推送，成功后自动清理。
3. **校验**：默认在合并工作树里跑 `engine/tools/validate.py`
   （退出码 `1` 阻断、`2` 警告放行）；`--no-verify` 跳过，`--verify-cmd` 自定义。
4. **推送**：经 `engine/scripts/git_push.py` 走 **ssh / https 双通道 failover**——先 `origin`（ssh），
   失败切 `origin-https`（https）；两条都失败即停止、不重试。默认带 `--force-with-lease`。
   远端在 fetch 之后又被 CI 推进时，自动再整合一次并重试一次；仍失败则报错，**绝不覆盖**。
5. **冲突**：保留 `.worktrees/_merge` 供人工处理，远端不受影响。
   处理完重试 `merge <name>`；放弃用 `merge --cleanup`。
6. **不改写任务分支**：默认 `--no-ff`，任务分支历史原样保留。
7. **只合并已提交内容**：未提交的改动不会被带入合并，也不会被推上 main。

## 五、锁语义（第 3 层细节）

- 锁文件：`.git/workflow-guard/{checkout,merge}.lock`，JSON 含 `owner / pid / op / acquired`。
- **失效只由时间决定**：超过 `--stale-timeout`（默认 1800 秒）未释放即视为失效，可强取。
  不按进程存活判断——本工具每次调用都是独立短命进程，持有者是「会话」不是进程。
- `lock run` 在 `finally` 中释放，命令异常也会放锁。
- `owner` 优先取 `CATPAW_CONVERSATION_ID`，否则 `用户@主机`；非本人释放需 `--force`。
  任务登记额外记录 `session`（完整会话 ID），用于分支名 `<sid>` 的反查与台账。
- 两把锁相互独立：`checkout` 保护共享检出目录，`merge` 保护 main 合并。

## 六、与 CI 的关系

GitHub Actions 在远端 runner 上跑，不经过本地锁；它们直接向 `main` 推送。
因此第 2 层的 `--force-with-lease` 是防覆盖的最后一道：CI 推进了远端，本地合并就失败重试，
不会把 CI 的提交冲掉。**不要**用 `sync --push-local` 强行推main，除非你确认那些提交
已经过校验。

## 七、状态与清理

- `.git/workflow-guard/tasks.json`：任务登记表。
- `.git/workflow-guard/*.lock`：锁。
- 二者都在 `.git/` 内，不入库、不进提交、跨 worktree 共享。
- 仓库重置 / 换机后状态自然消失，无需迁移。

## 八、GitHub 双通道推送（ssh / https failover）

- **背景**：GitHub 的 ssh 与 https 通道会各自网络抖动（如 443 被 reset、ssh 不通），
  单通道在抖动时需要人工重试；而 git 原生多 `pushurl` **不会** failover
  （实测 https 被 reset 后直接 fatal，不回退 ssh），所以 failover 必须由外层完成。
- **机制**：`engine/scripts/git_push.py` 先走主通道 `origin`（ssh），失败切备用通道
  `origin-https`（https）；**两条都失败即停止，不重试**（避免把抖动放大成刷屏重试）。
  每条通道只调用一次 `git push`。
- **配置（本 repo 本地 git config，不入库）**：
  - `origin` → `git@github.com:hmbphxkw76-byte/jp-life-work.git`（ssh）
  - `origin-https` → `https://github.com/hmbphxkw76-byte/jp-life-work.git`（https）
- **接入点**：`merge` 与 `sync --push-local` 的推送均经此工具；`--push-fallback` 可覆盖备用通道
  （传空字符串则不 failover）。
- **仅限本 repo**：本 repo 永不使用 GitLab，推送 / 合并 / 提交只走 GitHub。

## 九、工作区标准化清理（`engine/scripts/cleanup_workspace.py`）

流水线各阶段（前置 / 收尾）与本地开发共用的清理入口，规则单点维护。

**清理对象**（仅限未入库产物）：

- 缓存目录：`__pycache__/`、`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、`.hypothesis/`、`.trae-html-share-packages/`、`.screenshots/`；
- 生成备份目录：`engine/vocabulary/data/sync-backups/`、`engine/vocabulary/data/topic-backups/`；
- 单文件：`*.py[cod]`、`*$py.class`、`*.tmp`、`*.temp`、`.DS_Store`、`Thumbs.db`、`desktop.ini`；
- 运行日志：`engine/vocabulary/data/*.log`（作用域限定，其他目录同名文件不动）；
- 覆盖率产物：`.coverage*`（coverage 数据文件）、`htmlcov/`（HTML 报告目录）。

**行尾规范化**（P2-2）：已跟踪的 UTF-8 文本文件若被运行副作用写成 CRLF，写回 LF，
消除 `git status` 的「行尾假 dirty」。仅作用于「已跟踪 + 无 NUL + 可 UTF-8 解码」文件，
只做 CRLF → LF，不改内容语义；`--no-normalize-eol` 可关闭。

**安全约束**：残留清理只清仓库根内路径；已被 `git ls-files` 覆盖的文件 / 目录跳过；
不进入 `.git`；不跟随符号链接。行尾规范化仅改写已跟踪文本文件的行尾，不动其他文件。

```bash
python engine/scripts/cleanup_workspace.py            # 清理
python engine/scripts/cleanup_workspace.py --check    # 只检查，发现残留退出码 1（门禁用）
python engine/scripts/cleanup_workspace.py --dry-run  # 预览
python engine/scripts/cleanup_workspace.py --root <dir>
python engine/scripts/cleanup_workspace.py --no-normalize-eol  # 跳过行尾规范化
```

**CI 接入**：复合动作 `.github/actions/workspace-cleanup/action.yml`；每条工作流在
「checkout + setup-python 之后」与「job 最后一步（`if: always()`）」各调用一次，
`mode: ci` 额外 `pip cache purge`。`validate.yml` 另有 `workspace-hygiene` job
先制造残留再清理、以 `--check` 断言零残留。详见 `docs/CI.md` 第十三节。

**退出码**：0 = 干净或已清理；1 = `--check` 发现残留 / 参数错误 / 删除失败。

## 十、分支命名规范与会话标识（BRANCH-NAMING v1.0）

- 开发分支模板：`task/<name>-<sid>`；`sid` = 会话标识 `CATPAW_CONVERSATION_ID`（UUID）前 8 位小写十六进制。
- `task start` 自动追加 sid，无需手工输入；任务登记表 `session` 字段记录完整会话 ID。
- 手工校验：`python engine/scripts/branch_naming.py check <branch...>`（退出码 1 不合规）。
- 钩子：`python engine/scripts/workflow_guard.py hooks` 安装 pre-push / pre-commit（`--check` / `--uninstall`）；
  新克隆 / 换机后必装。pre-commit 现含两道检查：① 分支命名守卫；② 快速校验子集（暂存 Python 文件 `ruff check --fix` + `engine/tools/validate.py`，退出码 1 阻断、2 放行；ruff 缺失仅告警）。
  规范与异常处理见 `docs/branch-management.md`。

## 十一、报告生成一致性比对（`engine/scripts/verify_report_parity.py`）

引擎层迁移（`src/` → `engine/`、根 `tools/` → `engine/scripts/`）的「报告生成零差异」客观判据：迁移前写基线快照，迁移后归一化逐字节比对。

**比对范围**：`index.html` / `INDEX.md` / `search-index.json` / `automation-status.json` / 各主题 `reports/*.{html,md}`；排除 `**/legacy/**` 与基线目录自身。

**允许差异**：① 旧→新路径文本（`src/`→`engine/`、`tools/`→`engine/scripts/`）；② 生成时间戳（旧「最近生成（构建心跳）」整行、`INDEX.md` 头部「最近生成：… UTC」与报告行构建时间列）；③ JSON 易变键（`generated_at` 等）。其余差异一律判为回归（MISMATCH）。

```bash
python engine/scripts/verify_report_parity.py --write-baseline .migration-baseline   # 迁移前
python engine/scripts/verify_report_parity.py --compare  .migration-baseline          # 迁移后
```

**退出码**：0 全部一致；1 存在 MISMATCH / MISSING；2 用法或基线错误。基线目录不入库，收尾删除。

**测试**：`engine/tests/test_verify_report_parity.py`。（迁移方案为一次性文档，已归档于 git 历史）

## 十二、合并前检查单（TOOLCHAIN-DEV-SPEC §七，本次核对）

> 每次涉及工具链的合并逐项核对；任一项未过不得合并。本节为活文档，随每次任务更新。

| # | 项 | 结果 |
|---|---|---|
| 1 | 测试全绿 | ✅ `python -m unittest discover -s engine/tests -v` 全绿（1095 项） |
| 2 | `validate.py` 通过 | ✅ 退出码 0 |
| 3 | 双轴评审存在且无 P0/P1 | ✅ `docs/toolchain/reviews/w2-ci-cd-hardening-review.md`（W2 / 项 2.1–2.8） |
| 4 | `coverage_gate.py` 达标 | ✅ 90.46%（阈值 80%，enforce=true）；单工具最低阈值 60% |
| 5 | `cleanup_workspace.py --check` 零残留 | ✅ 零残留 |
| 6 | 新增/改动工具已登记 | ✅ 本任务无新增工具；`generate_registry.py --check` 通过（工具 45 / 类型 12 / 主题 21 / 工作流 8） |
| 6b | 决策面板产物一致性 | ✅ `consulting_panel.py --check` 退出码 0（面板 md 与重算一致） |
| 7 | 生成物确定性 | ✅ `build_hub.py --check` / `build_index.py --check` 均退出码 0 |
| 8 | 架构边界 | ✅ `engine/tools/` 无 git 可变操作；`engine/scripts/` 不产出内容；`iter_business_dirs()` = 21 |

## 十三、输入门禁可移植性（`engine/scripts/bootstrap_gate.py` / `check_gate.py`）

> 「输入润色与确认门禁」的跨 IDE / 跨模型 / 跨机器部署与自检。方案见 `docs/输入门禁可移植性方案.md`。

| 命令 | 作用 |
|---|---|
| `python engine/scripts/check_gate.py` | 只读自检：AGENTS.md 门禁节 / 机械判定口径、CLAUDE.md 导入、`.cursorrules`、工作区 skill、设计文档 |
| `python engine/scripts/bootstrap_gate.py` | 校验模式（只读），输出报告 |
| `python engine/scripts/bootstrap_gate.py --install` | 补齐缺失载体（`CLAUDE.md` / `.cursorrules`）并自检 |
| `python engine/scripts/bootstrap_gate.py --install --personal` | 额外部署工作区 skill 到 `~/.meituan-catpaw/<uid>/skills/` |

- 退出码：0 通过 / 1 有必备项缺失 / 2 非本仓库。
- 新机器：`git clone` → `python engine/scripts/bootstrap_gate.py --install`。
- 测试：`engine/tests/test_gate_scripts.py`。
