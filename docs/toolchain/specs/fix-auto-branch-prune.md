# 规格：自动化已合并分支显式清理（auto-branch-prune）

> 任务 slug：`fix-auto-branch-prune`
> 版本：v1.0（2026-11-24）
> 适用规约：[TOOLCHAIN-DEV-SPEC](../toolchain/TOOLCHAIN-DEV-SPEC.md)
> 前序：v2.32「清理 26 个 `auto/html-sync-*` 僵尸分支」（同类残留复发）

## 一、动机

仓库设置 `delete_branch_on_merge=true` 已开启（`gh api repos/{owner}/{repo}` 实测），
但远端仍残留 3 个**已合并**的自动化分支：

| 分支 | PR | 合并时点 |
|---|---|---|
| `auto/info-quality-20261123-105550` | #23 | 2026-11-23T10:55:57Z |
| `auto/html-sync-20261123-132331` | #27 | 2026-11-23T13:23:38Z |
| `auto/html-sync-20261124-003341` | #35 | 2026-11-24T00:33:48Z |

三者均经 `git merge-base --is-ancestor <branch> origin/main` 验证合入。
根因：`.github/actions/auto-merge-pr/action.yml` 合并后即结束，**无任何删分支动作**，
把清理完全寄托于仓库设置的隐式行为——该行为在 bot token 合并路径上不可靠。
自动化每轮新建 `auto/*-<时间戳>` 分支，不补机制则残留持续再生。

## 二、目标与非目标

**目标**：① 清理现存 3 个残留分支；② 让复合动作在合并成功后**显式删除** PR 头分支，
并在删除失败时以 `::warning::` 暴露（不静默）；③ 加回归守卫，防止回退到「只依赖隐式删除」。

**非目标**：不改 CI 门禁语义与分支保护策略；不新增定时清理调度（评估后认为显式步骤已足够）；
不动 `html-sync.yml` / `info-quality.yml` 等调用方（它们已具备 `contents: write`）。

## 三、接口设计

- 改动文件：`.github/actions/auto-merge-pr/action.yml`
  - 在 `gh pr merge "$num" --merge` 成功分支之后追加：
    `gh api -X DELETE "repos/${GITHUB_REPOSITORY}/git/refs/heads/${PR_BRANCH}"`
    - 成功：`echo "已删除头分支 ${PR_BRANCH}"`
    - 失败：`echo "::warning::头分支 ... 删除失败（PR 已合并），需人工清理"`（不 `exit 1`）
  - `description` 补一行说明该机制与实测依据。
- 守卫测试：`engine/tests/test_ci_auto_merge.py` 增 `test_composite_action_deletes_merged_head_branch`
  （断言 DELETE 调用存在、位于 `gh pr merge` 之后、失败路径有 `::warning::`）。

## 四、验收标准

1. 远端 `auto/*` 残留清零（本次即时删除 3 个，`git ls-remote --heads origin` 仅剩 `main`）；
2. 删除用 API 形式经本地实证可用（对上述分支实删成功，退出码 0）；
3. `action.yml` YAML 可解析，`runs.steps[0].run` 脚本含删除逻辑且顺序正确；
4. `ruff` / `mypy` / `validate.py` / 全量 `unittest` 通过；测试计数 1210 → 1211 同步锁定文档；
5. 走任务分支 + PR + 门禁 SUCCESS 后合并。

## 五、边界与约束

- 本机无 `bash`（WSL 未安装），无法对提取出的脚本做 `bash -n`；改以 YAML 解析 + 结构断言 +
  既有守卫测试覆盖，**不外推**为「已做 shell 语法校验」。
- 远端删除范围严格限定为规格表格中的 3 个分支。
