"""``engine/vocabulary/script/vocab_near_check.py`` 单元测试（P2-6）。

覆盖：``_similar``（包含关系 / 反义对不误报）、``_terms`` 解析、``scan``、
``main`` 退出码（0/2）。全部在 ``tempfile`` 临时目录内构造。
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


vnc = _load("vocab_near_check", "engine/vocabulary/script/vocab_near_check.py")

TERMS = """# 词条

| ID | 词条 | 别名 | 定义 | 说明 | 来源 |
|---|---|---|---|---|---|
| 1 | 送金 | 汇款 | 汇款 |  | x |
| 2 | 国際送金 | 国际汇款 | 国际汇款 |  | x |
| 3 | 大型免許 |  | 大型驾照 |  | x |
| 4 | 中型免許 |  | 中型驾照 |  | x |
| 5 | 車検 |  | 车检 |  | x |
"""


class SimilarCase(unittest.TestCase):
    def test_containment(self):
        self.assertEqual(vnc._similar("送金", "国際送金"), "包含关系")

    def test_antonym_not_flagged(self):
        # 编辑距离类规则会误报反义对，本工具只认包含关系。
        self.assertEqual(vnc._similar("大型免許", "中型免許"), "")

    def test_too_short_not_flagged(self):
        self.assertEqual(vnc._similar("a", "ab"), "")

    def test_exact(self):
        self.assertEqual(vnc._similar("x", "x"), "完全相同")


class TermsCase(unittest.TestCase):
    def test_parse(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "terms.md"
            p.write_text(TERMS, encoding="utf-8")
            rows = vnc._terms(p)
        self.assertEqual([t for t, _ in rows][:2], ["送金", "国際送金"])


class ScanCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        d = self.root / "engine" / "vocabulary" / "data" / "01-x"
        d.mkdir(parents=True)
        (d / "terms.md").write_text(TERMS, encoding="utf-8")

    def test_scan_finds_containment(self):
        with mock.patch.object(vnc, "VOCAB_DATA", self.root / "engine" / "vocabulary" / "data"):
            pairs = vnc.scan()
        self.assertTrue(any(p["a"] == "送金" and p["b"] == "国際送金" for p in pairs))
        self.assertFalse(any(p["a"] == "大型免許" for p in pairs))

    def test_main_exit_2(self):
        with mock.patch.object(vnc, "VOCAB_DATA", self.root / "engine" / "vocabulary" / "data"), \
                mock.patch.object(vnc, "ROOT", self.root), \
                mock.patch.object(vnc, "OUT", self.root / "near.json"), \
                mock.patch.object(sys, "argv", ["vocab_near_check.py", "--json"]):
            self.assertEqual(vnc.main(), 2)

    def test_main_exit_0(self):
        only = self.root / "only_data"
        d = only / "02-y"
        d.mkdir(parents=True)
        (d / "terms.md").write_text(
            "# 词条\n\n| ID | 词条 | 别名 | 定义 | 说明 | 来源 |\n"
            "|---|---|---|---|---|---|\n| 1 | 甲 |  | 甲 |  | x |\n"
            "| 2 | 乙 |  | 乙 |  | x |\n", encoding="utf-8")
        with mock.patch.object(vnc, "VOCAB_DATA", only), \
                mock.patch.object(vnc, "ROOT", self.root), \
                mock.patch.object(vnc, "OUT", self.root / "near.json"), \
                mock.patch.object(sys, "argv", ["vocab_near_check.py", "--json"]):
            self.assertEqual(vnc.main(), 0)


if __name__ == "__main__":
    unittest.main()
