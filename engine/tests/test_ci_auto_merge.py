"""CI 自动化 PR 免审批自动合并（ci-auto-merge-pr）守卫测试。

断言：
- 复合动作 `.github/actions/auto-merge-pr` 存在且实现「创建 / 复用 PR + 启用自动合并」；
- 6 条工作流的 8 个 PR 点全部经该复合动作接线；
- 仓库内不再有直接 `gh pr create`（防漂移回退到人工合并）。
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / ".github" / "workflows"
ACTION = ROOT / ".github" / "actions" / "auto-merge-pr" / "action.yml"

# 每条工作流预期的 auto-merge 动作引用次数（= 该工作流的 PR 点数）
EXPECTED_SITES = {
    "scheduled-maintenance.yml": 2,
    "html-sync.yml": 1,
    "info-quality.yml": 1,
    "audit-sampling.yml": 1,
    "pipeline-orchestrator.yml": 2,
    "scheduled-report-tasks.yml": 1,
}


class TestAutoMergeAction(unittest.TestCase):
    def test_composite_action_exists(self) -> None:
        self.assertTrue(ACTION.is_file(), f"缺少复合动作：{ACTION}")

    def test_composite_action_enables_auto_merge(self) -> None:
        t = ACTION.read_text(encoding="utf-8")
        self.assertIn("gh pr merge", t)
        self.assertIn("--auto", t)
        self.assertIn("--merge", t)

    def test_composite_action_declares_inputs(self) -> None:
        t = ACTION.read_text(encoding="utf-8")
        for name in ("branch", "title", "body"):
            self.assertIn(f"{name}:", t, f"复合动作缺少输入：{name}")


class TestWorkflowWiring(unittest.TestCase):
    def test_every_automated_workflow_uses_action(self) -> None:
        for name, expected in EXPECTED_SITES.items():
            t = (WF / name).read_text(encoding="utf-8")
            got = t.count("./.github/actions/auto-merge-pr")
            self.assertGreaterEqual(got, expected, f"{name} 接线不足：{got} < {expected}")

    def test_no_direct_gh_pr_create_remains(self) -> None:
        for f in sorted(WF.glob("*.yml")):
            t = f.read_text(encoding="utf-8")
            self.assertNotIn("gh pr create", t,
                             f"{f.name} 仍有直接 gh pr create（应走复合动作）")


if __name__ == "__main__":
    unittest.main()
