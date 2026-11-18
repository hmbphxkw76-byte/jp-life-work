"""输入门禁可移植性脚本测试（check_gate / bootstrap_gate）。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "engine" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import bootstrap_gate  # noqa: E402
import check_gate  # noqa: E402


class TestCheckGate(unittest.TestCase):
    def test_repo_carriers_present(self) -> None:
        results = check_gate.check(ROOT)
        failed = [n for n, ok, _ in results if not ok and "可选" not in n]
        self.assertEqual(failed, [], f"必备检查未通过：{failed}")

    def test_missing_gate_section_detected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("# 无门禁\n", encoding="utf-8")
            flags = {n: ok for n, ok, _ in check_gate.check(root)}
            self.assertFalse(flags["AGENTS.md 含门禁节"])
            self.assertFalse(flags["AGENTS.md 含机械判定口径"])

    def test_find_repo_root(self) -> None:
        self.assertEqual(check_gate.find_repo_root(SCRIPTS), ROOT)


class TestBootstrapGate(unittest.TestCase):
    def test_install_creates_missing_carriers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("## 硬性规约：输入润色与确认门禁\n", encoding="utf-8")
            actions = bootstrap_gate.install(root)
            self.assertTrue((root / "CLAUDE.md").exists())
            self.assertIn("@AGENTS.md", (root / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertTrue((root / ".cursorrules").exists())
            self.assertTrue(actions)

    def test_install_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("## 硬性规约：输入润色与确认门禁\n", encoding="utf-8")
            bootstrap_gate.install(root)
            second = bootstrap_gate.install(root)
            self.assertEqual(second, [])


if __name__ == "__main__":
    unittest.main()
