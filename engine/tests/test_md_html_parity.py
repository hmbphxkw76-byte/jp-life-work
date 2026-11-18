"""``engine/tools/md_html_parity.py`` 单元测试。

覆盖：``_normalize``（换行统一）、``check_report``（OK / MISSING / MISMATCH /
ERROR）、``check``（多份汇总）、``main`` 参数分发与退出码（0 / 1 / 2）。

渲染函数 ``convert`` 以 mock 注入（其真实实现由 md2html 自身测试覆盖），
本测试聚焦一致性判定逻辑。全部在 ``tempfile`` 临时目录内构造。
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mhp = _load("md_html_parity", "engine/tools/md_html_parity.py")


class NormalizeCase(unittest.TestCase):
    def test_crlf_and_cr_unify(self) -> None:
        self.assertEqual(mhp._normalize("a\r\nb\rc\nd"), "a\nb\nc\nd")

    def test_other_bytes_unchanged(self) -> None:
        self.assertEqual(mhp._normalize("x  y\n"), "x  y\n")


class CheckReportCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _md(self, rel: str, html: str | None) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# t\n", encoding="utf-8", newline="")
        if html is not None:
            with open(p.with_suffix(".html"), "w", encoding="utf-8", newline="") as f:
                f.write(html)
        return p

    def _run(self, md: Path, rendered: str):
        with mock.patch.object(mhp, "ROOT", self.root), \
                mock.patch.object(mhp, "convert", return_value=rendered):
            return mhp.check_report(md)

    def test_ok(self) -> None:
        md = self._md("t/reports/2026-11-a.md", "<html>a</html>")
        self.assertEqual(self._run(md, "<html>a</html>")["status"], "OK")

    def test_missing_html(self) -> None:
        md = self._md("t/reports/2026-11-a.md", None)
        self.assertEqual(self._run(md, "<html>a</html>")["status"], "MISSING")

    def test_mismatch_reports_first_diff(self) -> None:
        md = self._md("t/reports/2026-11-a.md", "<html>BBB</html>")
        r = self._run(md, "<html>AAA</html>")
        self.assertEqual(r["status"], "MISMATCH")
        self.assertIn("@6", r["detail"])

    def test_render_error(self) -> None:
        md = self._md("t/reports/2026-11-a.md", "<html>a</html>")
        with mock.patch.object(mhp, "ROOT", self.root), \
                mock.patch.object(mhp, "convert", side_effect=RuntimeError("boom")):
            r = mhp.check_report(md)
        self.assertEqual(r["status"], "ERROR")
        self.assertIn("boom", r["detail"])

    def test_crlf_difference_is_ok(self) -> None:
        md = self._md("t/reports/2026-11-a.md", "<html>a\r\nb</html>")
        self.assertEqual(self._run(md, "<html>a\nb</html>")["status"], "OK")


class CheckAndMainCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _make(self, rel: str, html: str | None) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# t\n", encoding="utf-8", newline="")
        if html is not None:
            with open(p.with_suffix(".html"), "w", encoding="utf-8", newline="") as f:
                f.write(html)
        return p

    def _patch(self, mds, render_map):
        return (mock.patch.object(mhp, "ROOT", self.root),
                mock.patch.object(mhp, "collect_md_reports", return_value=mds),
                mock.patch.object(mhp, "convert", side_effect=lambda p: render_map[p.name]))

    def test_check_aggregates(self) -> None:
        a = self._make("t/reports/a.md", "<html>a</html>")
        b = self._make("t/reports/b.md", "<html>b</html>")
        c = self._make("t/reports/c.md", None)
        p1, p2, p3 = self._patch([a, b, c], {"a.md": "<html>a</html>",
                                             "b.md": "<html>B</html>", "c.md": ""})
        with p1, p2, p3:
            out = mhp.check()
        self.assertEqual([r["status"] for r in out], ["OK", "MISMATCH", "MISSING"])

    def test_main_exit_1_on_drift(self) -> None:
        a = self._make("t/reports/a.md", "<html>a</html>")
        p1, p2, p3 = self._patch([a], {"a.md": "<html>A</html>"})
        with p1, p2, p3, mock.patch.object(sys, "argv", ["md_html_parity.py"]):
            self.assertEqual(mhp.main(), 1)

    def test_main_warn_exit_2(self) -> None:
        a = self._make("t/reports/a.md", "<html>a</html>")
        p1, p2, p3 = self._patch([a], {"a.md": "<html>A</html>"})
        with p1, p2, p3, mock.patch.object(sys, "argv", ["md_html_parity.py", "--warn"]):
            self.assertEqual(mhp.main(), 2)

    def test_main_json_exit_0(self) -> None:
        a = self._make("t/reports/a.md", "<html>a</html>")
        p1, p2, p3 = self._patch([a], {"a.md": "<html>a</html>"})
        with p1, p2, p3, mock.patch.object(sys, "argv", ["md_html_parity.py", "--json"]):
            self.assertEqual(mhp.main(), 0)

    def test_main_single_report(self) -> None:
        a = self._make("t/reports/a.md", "<html>a</html>")
        with mock.patch.object(mhp, "ROOT", self.root), \
                mock.patch.object(mhp, "convert", return_value="<html>a</html>"), \
                mock.patch.object(sys, "argv",
                                  ["md_html_parity.py", "--report", str(a)]):
            self.assertEqual(mhp.main(), 0)

    def test_main_missing_html_exit_1(self) -> None:
        a = self._make("t/reports/a.md", None)
        p1, p2, p3 = self._patch([a], {"a.md": ""})
        with p1, p2, p3, mock.patch.object(sys, "argv", ["md_html_parity.py"]):
            self.assertEqual(mhp.main(), 1)


if __name__ == "__main__":
    unittest.main()
