"""``engine/scripts/verify_report_parity.py`` 单元测试。

覆盖：``normalize``（路径重写 / 时间戳 / JSON 易变键 / 换行统一）、``discover``
（glob 命中与排除）、``_repo_root`` 回退、``write_baseline``（manifest + 拷贝 +
覆盖清空）、``compare``（一致 / 仅路径 / 仅时间戳 / MISMATCH / MISSING / NEW /
基线缺失退出码 2）、``main`` 参数分发。

全部在 ``tempfile`` 临时目录内构造，不触碰真实仓库文件、不发起网络请求。
"""
from __future__ import annotations

import importlib.util
import json
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


vp = _load("verify_report_parity", "engine/scripts/verify_report_parity.py")


class NormalizeCase(unittest.TestCase):
    def test_path_rewrite(self) -> None:
        self.assertEqual(vp.normalize("x.md", "见 tools/workflow_guard.py"),
                         "见 engine/scripts/workflow_guard.py")

    def test_timestamp_stripped(self) -> None:
        self.assertEqual(vp.normalize("INDEX.md", "最近生成（构建心跳）：2026-01-01 00:00:00"),
                         "最近生成（构建心跳）：<TIMESTAMP>")

    def test_index_header_timestamp_stripped(self) -> None:
        a = "> 最近生成：2026-11-15 08:50 UTC（由 engine/tools/build_index.py 自动维护）"
        b = "> 最近生成：2026-11-17 07:59 UTC（由 engine/tools/build_index.py 自动维护）"
        self.assertEqual(vp.normalize("INDEX.md", a), vp.normalize("INDEX.md", b))

    def test_index_date_column_stripped(self) -> None:
        a = "| 2026-11 | [x.html](x.html) | 标题 | 2026-11-15 08:50 |"
        b = "| 2026-11 | [x.html](x.html) | 标题 | 2026-11-17 07:59 |"
        self.assertEqual(vp.normalize("INDEX.md", a), vp.normalize("INDEX.md", b))

    def test_new_engine_path_not_corrupted(self) -> None:
        # `tools/` 兜底项不得命中新布局路径 engine/tools/
        self.assertEqual(vp.normalize("x.md", "见 engine/tools/validate.py"),
                         "见 engine/tools/validate.py")
        self.assertEqual(vp.normalize("x.md", "见 engine/scripts/git_push.py"),
                         "见 engine/scripts/git_push.py")

    def test_json_volatile_keys_dropped(self) -> None:
        a = '{"generated_at": "x", "b": 1, "a": [{"timestamp": "t", "c": 2}]}'
        b = '{"b": 1, "a": [{"c": 2}]}'
        self.assertEqual(vp.normalize("a.json", a), vp.normalize("a.json", b))

    def test_newline_unified(self) -> None:
        self.assertEqual(vp.normalize("x.md", "a\r\nb"), vp.normalize("x.md", "a\nb"))

    def test_invalid_json_falls_back_to_text(self) -> None:
        # 非合法 JSON 的 .json 走文本归一化，不做路径重写以外的处理
        self.assertEqual(vp.normalize("a.json", "src/"), "engine/")

    def test_nested_volatile_dropped(self) -> None:
        obj = {"generated": "x", "list": [{"built_at": "y", "k": 1}]}
        self.assertEqual(vp._drop_volatile(obj), {"list": [{"k": 1}]})


class RepoRootCase(unittest.TestCase):
    def test_fallback_real_layout(self) -> None:
        # git 不可用时按布局回退：engine/scripts/ -> parents[2]
        with mock.patch.object(vp.subprocess, "run", side_effect=OSError("no git")):
            self.assertEqual(vp._repo_root(), ROOT)

    def test_fallback_layout_scripts(self) -> None:
        fake = mock.Mock()
        fake.parent = mock.Mock()
        fake.parent.name = "scripts"
        fake.parent.parent = mock.Mock()
        fake.parent.parent.name = "engine"
        fake.parents = [None, None, Path("/fake/root")]
        with mock.patch.object(vp, "_HERE", fake), \
                mock.patch.object(vp.subprocess, "run", side_effect=OSError("no git")):
            self.assertEqual(vp._repo_root(), Path("/fake/root"))


class DiscoverCase(unittest.TestCase):
    def test_discover_and_exclude(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "index.html").write_text("x", encoding="utf-8")
            (root / "01-x" / "reports").mkdir(parents=True)
            (root / "01-x" / "reports" / "a.html").write_text("x", encoding="utf-8")
            (root / "01-x" / "reports" / "legacy").mkdir()
            (root / "01-x" / "reports" / "legacy" / "old.html").write_text("x", encoding="utf-8")
            (root / ".migration-baseline").mkdir()
            (root / ".migration-baseline" / "manifest.json").write_text("{}", encoding="utf-8")
            rels = vp.discover(root)
            self.assertIn("index.html", rels)
            self.assertIn("01-x/reports/a.html", rels)
            self.assertNotIn("01-x/reports/legacy/old.html", rels)
            self.assertNotIn(".migration-baseline/manifest.json", rels)


class BaselineCase(unittest.TestCase):
    def test_write_baseline_manifest_and_copy(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            base = Path(d) / "base"
            (root / "01-x" / "reports").mkdir(parents=True)
            (root / "index.html").write_text("idx", encoding="utf-8")
            (root / "01-x" / "reports" / "a.html").write_text("A", encoding="utf-8")
            self.assertEqual(vp.main(["--root", str(root), "--write-baseline", str(base)]), 0)
            manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(set(manifest["files"]), {"index.html", "01-x/reports/a.html"})
            self.assertEqual((base / "index.html").read_text(encoding="utf-8"), "idx")

    def test_write_baseline_clears_stale(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            base = Path(d) / "base"
            root.mkdir()
            base.mkdir()
            (base / "stale.txt").write_text("old", encoding="utf-8")
            self.assertEqual(vp.main(["--root", str(root), "--write-baseline", str(base)]), 0)
            self.assertFalse((base / "stale.txt").exists())


class CompareCase(unittest.TestCase):
    def _repo_with(self, d: str, files: dict[str, str]):
        root = Path(d) / "repo"
        base = Path(d) / "base"
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        return root, base

    def test_identical(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root, base = self._repo_with(d, {"index.html": "x"})
            vp.main(["--root", str(root), "--write-baseline", str(base)])
            self.assertEqual(vp.main(["--root", str(root), "--compare", str(base)]), 0)

    def test_path_rewrite_ok(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root, base = self._repo_with(d, {"index.html": "engine/report-audits/a"})
            vp.main(["--root", str(root), "--write-baseline", str(base)])
            (root / "index.html").write_text("engine/report-audits/a", encoding="utf-8")
            self.assertEqual(vp.main(["--root", str(root), "--compare", str(base)]), 0)

    def test_timestamp_ok(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root, base = self._repo_with(d, {"INDEX.md": "最近生成（构建心跳）：A"})
            vp.main(["--root", str(root), "--write-baseline", str(base)])
            (root / "INDEX.md").write_text("最近生成（构建心跳）：B", encoding="utf-8")
            self.assertEqual(vp.main(["--root", str(root), "--compare", str(base)]), 0)

    def test_json_volatile_ok(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root, base = self._repo_with(
                d, {"automation-status.json": '{"generated_at": "A", "n": 1}'})
            vp.main(["--root", str(root), "--write-baseline", str(base)])
            (root / "automation-status.json").write_text(
                '{"generated_at": "B", "n": 1}', encoding="utf-8")
            self.assertEqual(vp.main(["--root", str(root), "--compare", str(base)]), 0)

    def test_mismatch_rc1(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root, base = self._repo_with(d, {"index.html": "AAA"})
            vp.main(["--root", str(root), "--write-baseline", str(base)])
            (root / "index.html").write_text("BBB", encoding="utf-8")
            self.assertEqual(vp.main(["--root", str(root), "--compare", str(base)]), 1)

    def test_missing_rc1(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root, base = self._repo_with(d, {"index.html": "x"})
            vp.main(["--root", str(root), "--write-baseline", str(base)])
            (root / "index.html").unlink()
            self.assertEqual(vp.main(["--root", str(root), "--compare", str(base)]), 1)

    def test_binary_mismatch_rc1(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            base = Path(d) / "base"
            root.mkdir()
            (root / "index.html").write_bytes(b"\xff\xfeA")
            vp.main(["--root", str(root), "--write-baseline", str(base)])
            (root / "index.html").write_bytes(b"\xff\xfeB")
            self.assertEqual(vp.main(["--root", str(root), "--compare", str(base)]), 1)

    def test_new_is_reported_but_rc0(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root, base = self._repo_with(d, {"index.html": "x"})
            vp.main(["--root", str(root), "--write-baseline", str(base)])
            (root / "search-index.json").write_text("y", encoding="utf-8")
            self.assertEqual(vp.main(["--root", str(root), "--compare", str(base)]), 0)

    def test_missing_manifest_rc2(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "repo"
            root.mkdir()
            self.assertEqual(
                vp.main(["--root", str(root), "--compare", str(Path(d) / "nope")]), 2)


class MainCase(unittest.TestCase):
    def test_no_args_is_error(self) -> None:
        with self.assertRaises(SystemExit):
            vp.main([])

    def test_root_override(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertEqual(vp.main(["--root", str(root), "--write-baseline",
                                      str(Path(d) / "b")]), 0)


if __name__ == "__main__":
    unittest.main()
