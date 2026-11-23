# 规格：CI 自动化 PR 免审批自动合并（ci-auto-merge-pr）

> **版本**：v1.0（2026-11-23）
> **定位**：工具链变更规格（TOOLCHAIN-DEV-SPEC S1）。≤1 页，只含动机 / 接口 / 验收标准。

## 一、动机

1. 仓库为纯个人项目，无第三方评审需求；质量唯一门是 CI（`validate` + `audit`）。
2. 现状：6 条工作流共 8 个 `gh pr create` 点，PR 正文写「请评审后合并」，合并依赖人工点击，
   形成 PR 积压与摩擦。
3. `main` 分支保护 `required_approving_review_count = 0`（无强制评审数），
   「审批门」实为人工合并动作，可消除；`validate` / `audit` 两个必需检查保留不动。

## 二、接口

- 新增复合动作 `.github/actions/auto-merge-pr/action.yml`：
  - 输入：`branch`（已推送的 PR 头分支）、`title`、`body`、`token`（缺省 `github.token`）。
  - 行为：定位 / 创建 `main ← branch` 的开放 PR → `gh pr merge <num> --auto --merge`；
    `branch` 为空（无变更跳过提交）或 PR 不存在时幂等跳过；失败以 `::error::` 输出并退出 1。
- 6 条工作流共 8 个提交点：提交步骤把分支名写入 `$GITHUB_OUTPUT`，随后新增一步
  `uses: ./.github/actions/auto-merge-pr`。
- 仓库设置：启用 `allow_auto_merge`（一次性，`gh repo edit --enable-auto-merge`）。
- **分支保护不变**：必需检查 `validate` / `audit`，评审数 0。CI 未通过的 PR 不合并
  （数据完整底线不变）。
- 文档：`docs/CI.md`、`docs/branch-management.md`、`engine/scripts/README.md`。

## 三、验收标准

1. 8 个 PR 点全部经复合动作创建并启用自动合并；仓库内无残留的直接 `gh pr create`。
2. `allow_auto_merge = true`；`main` 分支保护必需检查仍为 `validate` / `audit`。
3. 新增守卫测试断言上述接线；`unittest` 全绿。
4. `validate.py` 退出码 ∈ {0,2}；`audit_pipeline --gate` 通过；`coverage_gate` 达标；
   `cleanup_workspace --check` 零残留。
5. 端到端：任一条工作流产出的 PR 在 `validate` + `audit` 通过后自动合入 `main`。
