"""``engine/tools/counterexample_scan.py`` 单元测试（P2-1）。

覆盖：``scan_text``（绝对化 / 以偏概全 / 无来源断言）、``scan``、``main`` 退出码。
全部在 ``tempfile`` 临时目录内构造。
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

import _common  # noqa: E402


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


cs = _load("counterexample_scan", "engine/tools/counterexample_scan.py")


class ScanTextCase(unittest.TestCase):
    def test_absolute_hit(self):
        items = cs.scan_text("该制度必然成功，100% 覆盖。")
        self.assertTrue(any("ABS" in i["kinds"] for i in items))

    def test_generalization_hit(self):
        items = cs.scan_text("本报告所有结论均无需限定。")
        self.assertTrue(any("GEN" in i["kinds"] for i in items))

    def test_clean_text_no_hit(self):
        self.assertEqual(cs.scan_text("该指标 2026-11 为 3.8%（来源：ISA）。"), [])

    def test_dedup(self):
        text = "所有结论均成立。" * 3
        self.assertEqual(len(cs.scan_text(text)), 1)

    def test_single_source_hit(self):
        # 含数字的结论句 + 段落仅一个来源 → 单源候选
        text = "结论：2026 年缺口为 14%（来源：官方统计）。"
        items = cs.scan_text(text)
        self.assertTrue(any("单源" in i["kinds"] for i in items))

    def test_single_source_labeled_not_hit(self):
        text = "结论：2026 年缺口为 14%（单源，来源：官方统计）。"
        items = cs.scan_text(text)
        self.assertFalse(any("单源" in i["kinds"] for i in items))

    def test_single_source_plain_sentence_not_hit(self):
        # 普通来源句（无结论性措辞）不误报
        self.assertFalse(any("单源" in i["kinds"] for i in cs.scan_text(
            "该指标 2026-11 为 3.8%（来源：ISA）。")))


class ScanAndMainCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _biz(self, rel: str, text: str):
        d = self.root / rel / "reports"
        d.mkdir(parents=True)
        (d / "2026-11-x.md").write_text(text, encoding="utf-8")

    def test_scan(self):
        self._biz("01-x", "# t\n该制度必然成功，100% 覆盖。\n")
        with mock.patch.object(_common, "ROOT", self.root), \
                mock.patch.object(cs, "ROOT", self.root), \
                mock.patch.object(cs, "iter_business_dirs",
                                  return_value=[_common.Business("01-x")]):
            rows = cs.scan()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["report"], "01-x/reports/2026-11-x.md")

    def test_main_exit_0(self):
        with mock.patch.object(cs, "scan", return_value=[]), \
                mock.patch.object(sys, "argv", ["counterexample_scan.py", "--json"]):
            self.assertEqual(cs.main(), 0)

    def test_main_exit_2(self):
        with mock.patch.object(cs, "scan",
                               return_value=[{"report": "r", "count": 1,
                                               "items": [{"sentence": "s", "kinds": ["GEN"],
                                                         "hits": []}]}]), \
                mock.patch.object(sys, "argv", ["counterexample_scan.py", "--json"]):
            self.assertEqual(cs.main(), 2)


class AdjudicationCase(unittest.TestCase):
    """裁定清单：命中 (report, sentence) 即不再计为待处理。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _cfg(self, items: list[dict]) -> Path:
        p = self.root / "adj.json"
        p.write_text(json.dumps({"schema_version": "1.0", "adjudications": items},
                                ensure_ascii=False), encoding="utf-8")
        return p

    def test_missing_file_is_empty(self):
        self.assertEqual(cs.load_adjudications(self.root / "nope.json"), {})

    def test_broken_json_is_empty(self):
        p = self.root / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        self.assertEqual(cs.load_adjudications(p), {})

    def test_main_filters_adjudicated(self):
        cfg = self._cfg([{"report": "r", "sentence": "s", "verdict": "保留",
                         "reason": "x", "evidence": "y"}])
        rows = [{"report": "r", "count": 1,
                "items": [{"sentence": "s", "kinds": ["GEN"], "hits": []}]}]
        with mock.patch.object(cs, "scan", return_value=rows), \
                mock.patch.object(cs, "ADJ", cfg), \
                mock.patch.object(sys, "argv", ["counterexample_scan.py", "--json"]):
            self.assertEqual(cs.main(), 0)   # 全部已裁定 → 无待处理


if __name__ == "__main__":
    unittest.main()
