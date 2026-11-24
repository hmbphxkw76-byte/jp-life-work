# 双轴评审：自动化已合并分支显式清理（auto-branch-prune）

> 工单：[tickets/fix-auto-branch-prune.md](../tickets/fix-auto-branch-prune.md)
> 评审日期：2026-11-24
> 评审对象：`.github/actions/auto-merge-pr/action.yml`、`engine/tests/test_ci_auto_merge.py`、
> `docs/CI.md`、`docs/README.md`、`docs/cross-domain-expert-roles.md`、
> `engine/tools/README.md`、`engine/scripts/README.md`
> 规格：[specs/fix-auto-branch-prune.md](../specs/fix-auto-branch-prune.md)

## 一、Standards 轴（规约符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| 复用既有机制、不新造轮子 | 通过 | 沿用既有复合动作与 `gh` / `GH_TOKEN`，未引入新依赖 |
| 失败必须可见、不静默吞掉 | 通过 | 删分支失败走 `::warning::`；合并失败仍 `::error::` + `exit 1` |
| 生成物 / CI 确定性 | 通过 | 不产生文件改动，只影响分支生命周期 |
| 文档数字双向锁定 | 通过 | 测试计数 1210 → 1211 同步 5 处（CI 节标题 / 合计行 / README 版本头+表 / tools README / scripts README） |
| 测试先行 | 通过 | 守卫先红（原动作无删除逻辑 → 新断言 FAIL）后绿 |
| 过程留痕 | 通过 | 工单 / 规格 / 本评审齐全 |

## 二、Spec 轴（规格 ↔ 实现映射）

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 三、合并成功后删头分支 | `gh api -X DELETE "repos/${GITHUB_REPOSITORY}/git/refs/heads/${PR_BRANCH}"` 位于 `gh pr merge` 成功之后 | 守卫断言顺序 `index("gh pr merge") < index("git/refs/heads/")` |
| 三、删失败告警不静默 | `else` 分支输出 `::warning::…需人工清理`，不改退出码 | 守卫断言含 `::warning::` |
| 三、调用方无需改动 | 未改 6 条工作流；两者均已声明 `contents: write` | `EXPECTED_SITES` 接线测试仍全绿 |
| 四、验收 1 | 远端 3 个残留分支实删成功（退出码 0），`git ls-remote --heads origin` 仅剩 `main` | 命令输出留痕于会话记录 |
| 四、验收 4 | `ruff` / `mypy` / `validate` / 全量 unittest（1211） | 见检查单 §十二 |

## 三、残余风险 / 遗留

- **本机无 `bash`（WSL 未安装）**：未能对提取出的 shell 脚本做 `bash -n`。已用 YAML 解析 +
  结构断言替代，**不宣称已做 shell 语法校验**；首次真实触发该步骤时需关注 CI 日志。
- **隐式自动删除失效的根因未定位**：仓库设置 `delete_branch_on_merge=true` 与实测残留并存，
  具体原因（bot token 合并路径是否被该设置覆盖）未查证。本次以「显式删除」绕过，
  但**没有解释**该设置为何无效——若日后有人误以为设置已足够而回退，问题会复现。
  已在动作 `description` 写明实测依据，降低回退概率。
- **只覆盖 `auto-merge-pr` 路径**：若将来新增不经该复合动作的自动化提交点，仍可能残留分支；
  当前仓库 8 个 PR 点已全部接线（守卫测试覆盖）。
- 无其他未完成项。
