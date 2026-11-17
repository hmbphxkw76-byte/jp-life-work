"""工具链变更评审软门禁测试（TOOLCHAIN-DEV-SPEC 第七节；mainline 融合 P3）。

hermetic：以临时目录构造变更清单与评审目录，不触碰真实仓库。
"""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "prompts-tools" / "tools"))

import review_gate  # noqa: E402


class TestScopeDetection(unittest.TestCase):
    def test_toolchain_path_in_scope(self):
        self.assertTrue(review_gate.is_toolchain_path("src/prompts-tools/tools/validate.py"))
        self.assertTrue(review_gate.is_toolchain_path("src/vocabulary/script/vocab_tool.py"))
        self.assertTrue(review_gate.is_toolchain_path("tools/workflow_guard.py"))

    def test_content_path_out_of_scope(self):
        self.assertFalse(review_gate.is_toolchain_path("01-ssw-driver/reports/2026-11-ssw-driver.md"))
        self.assertFalse(review_gate.is_toolchain_path("docs/toolchain/TOOLCHAIN-DEV-SPEC.md"))
        self.assertFalse(review_gate.is_toolchain_path("README.md"))

    def test_backslash_normalized(self):
        self.assertTrue(review_gate.is_toolchain_path("src\\prompts-tools\\tools\\validate.py"))


class TestGate(unittest.TestCase):
    def _write(self, d: Path, name: str, text: str) -> Path:
        p = d / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_no_changed_files_passes(self):
        with tempfile.TemporaryDirectory() as d:
            changed = self._write(Path(d), "changed.txt", "")
            code = review_gate.gate(changed, Path(d) / "reviews")
            self.assertEqual(code, 0)

    def test_content_only_change_passes(self):
        with tempfile.TemporaryDirectory() as d:
            changed = self._write(Path(d), "changed.txt", "01-ssw-driver/reports/2026-11-x.md\n")
            code = review_gate.gate(changed, Path(d) / "reviews")
            self.assertEqual(code, 0)

    def test_toolchain_change_without_review_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            changed = self._write(Path(d), "changed.txt", "src/prompts-tools/tools/validate.py\n")
            out = io.StringIO()
            with redirect_stdout(out):
                code = review_gate.gate(changed, Path(d) / "reviews")
            self.assertEqual(code, 1)
            self.assertIn("评审", out.getvalue())

    def test_toolchain_change_with_review_passes(self):
        with tempfile.TemporaryDirectory() as d:
            changed = self._write(Path(d), "changed.txt", "src/prompts-tools/tools/validate.py\n")
            self._write(Path(d), "reviews/pilot-review.md", "# review\n")
            code = review_gate.gate(changed, Path(d) / "reviews")
            self.assertEqual(code, 0)


class TestMain(unittest.TestCase):
    def test_main_reads_changed_file(self):
        with tempfile.TemporaryDirectory() as d:
            changed = Path(d) / "changed.txt"
            changed.write_text("tools/workflow_guard.py\n", encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = review_gate.main(["--changed", str(changed),
                                         "--reviews-dir", str(Path(d) / "reviews")])
            self.assertEqual(code, 1)

    def test_main_missing_changed_file_exit_1(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = review_gate.main(["--changed", "no-such.txt",
                                     "--reviews-dir", "reviews"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
