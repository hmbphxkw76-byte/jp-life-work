"""``engine/tools/source_check.py`` 单元测试（P1-2）。

覆盖：``_section_body``、``extract_report``（缺章节 / URL 条目 / 缺年份 / 分级声明）、
``collect``、``main`` 退出码（0/1/2）。全部在 ``tempfile`` 临时目录内构造。
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

import _common  # noqa: E402


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sc = _load("source_check", "engine/tools/source_check.py")

SECTION = """## 九、参考来源清单

> 按来源分级分组，完整 URL。

### ① 日本政府官方一手

1. [ISA](https://www.moj.go.jp/isa/) — 出入国在留管理庁, 2026
2. [MLIT](https://www.mlit.go.jp/) — 2025

### ② 行业机构

3. [ClassNK](https://www.classnk.or.jp/) — 最终更新 2026-10-15
"""


class SectionBodyCase(unittest.TestCase):
    def test_body_stops_at_next_h2(self):
        text = SECTION + "\n## 十、交付物\n"
        m = sc.SECTION_RE.search(text)
        body = sc._section_body(text, m)
        self.assertIn("ISA", body)
        self.assertNotIn("交付物", body)


class ExtractCase(unittest.TestCase):
    def test_ok(self):
        r = sc.extract_report("01-x/reports/2026-11-x.md", "# t\n" + SECTION)
        self.assertEqual(r["problems"], [])
        self.assertEqual(len(r["entries"]), 3)
        self.assertTrue(all(e["year"] for e in r["entries"]))
        self.assertTrue(r["graded"])

    def test_missing_section(self):
        r = sc.extract_report("01-x/reports/2026-11-x.md", "# t\n无来源\n")
        self.assertIn("缺来源章节", r["problems"])

    def test_era_year_counts_as_timepoint(self):
        text = "## 参考来源清单\n\n### ① 官方一手（分级）\n\n1. [X](https://x.go.jp/) — 令和 8-07-13 改定\n"
        r = sc.extract_report("r", text)
        self.assertEqual(r["problems"], [])

    def test_marker_counts_as_timepoint(self):
        text = "## 参考来源清单\n\n### ① 官方一手（分级）\n\n1. [X](https://x.go.jp/) — 首页（2026-11 核对）\n"
        r = sc.extract_report("r", text)
        self.assertEqual(r["problems"], [])

    def test_missing_year_warns(self):
        text = "## 参考来源清单\n\n### ① 官方一手（分级）\n\n1. [X](https://x.go.jp/) — 无年份\n"
        r = sc.extract_report("r", text)
        self.assertTrue(any("缺时点年份" in p for p in r["problems"]))

    def test_no_url_entries_warns(self):
        text = "## 参考来源清单\n\n### ① 官方一手（分级）\n\n文字说明，无链接。\n"
        r = sc.extract_report("r", text)
        self.assertTrue(any("无 URL 条目" in p for p in r["problems"]))

    def test_group_captured(self):
        r = sc.extract_report("r", SECTION)
        self.assertTrue(r["entries"][0]["group"])


class CollectAndMainCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _biz(self, rel: str, text: str):
        d = self.root / rel / "reports"
        d.mkdir(parents=True)
        (d / "2026-11-x.md").write_text(text, encoding="utf-8")

    def test_collect(self):
        self._biz("01-x", "# t\n" + SECTION)
        with mock.patch.object(_common, "ROOT", self.root), \
                mock.patch.object(sc, "ROOT", self.root), \
                mock.patch.object(sc, "iter_business_dirs",
                                  return_value=[_common.Business("01-x")]):
            out = sc.collect()
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["report"], "01-x/reports/2026-11-x.md")

    def test_main_exit_1(self):
        with mock.patch.object(sc, "collect",
                               return_value=[{"report": "r", "problems": ["缺来源章节"]}]), \
                mock.patch.object(sys, "argv", ["source_check.py", "--json"]):
            self.assertEqual(sc.main(), 1)

    def test_main_exit_2(self):
        with mock.patch.object(sc, "collect",
                               return_value=[{"report": "r", "problems": ["1 条缺年份"],
                                              "entries": []}]), \
                mock.patch.object(sys, "argv", ["source_check.py", "--json"]):
            self.assertEqual(sc.main(), 2)

    def test_main_exit_0(self):
        with mock.patch.object(sc, "collect",
                               return_value=[{"report": "r", "problems": [], "entries": [1]}]), \
                mock.patch.object(sys, "argv", ["source_check.py", "--json"]):
            self.assertEqual(sc.main(), 0)


class NormalizeCase(unittest.TestCase):
    """n25：来源归一化单一事实源（source_normalize）。"""

    def test_url_strips_trailing_punctuation(self):
        from source_normalize import normalize_url
        self.assertEqual(normalize_url("https://x.go.jp/a).，"), "https://x.go.jp/a")
        self.assertEqual(normalize_url(""), "")

    def test_org_strips_modifier(self):
        from source_normalize import normalize_org
        self.assertEqual(normalize_org("**出入国在留管理庁** · 2026"), "出入国在留管理庁 2026")
        self.assertEqual(normalize_org(""), "")

    def test_year_normalized(self):
        from source_normalize import extract_year, normalize_year
        self.assertEqual(normalize_year("令和 8-07-13 改定"), "令和8年")
        self.assertEqual(normalize_year("最终更新 2026-10-15"), "2026")
        self.assertEqual(extract_year("令和 8-07-13 改定"), "令和8")
        self.assertEqual(normalize_year("无年份"), "")


class CompletenessCase(unittest.TestCase):
    """n25：E5 来源条目字段完整率。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _biz(self, rel: str, text: str):
        d = self.root / rel / "reports"
        d.mkdir(parents=True)
        (d / "2026-11-x.md").write_text(text, encoding="utf-8")

    def test_incomplete_group_warns(self):
        # 有条目但无分级分组 → 完整率 < 100%
        text = ("## 参考来源清单\n\n### 官方一手（分级）\n\n"
                "1. [X](https://x.go.jp/) — 2026\n")
        # 移除分组标记，模拟无 group 行
        text = text.replace("### 官方一手（分级）\n\n", "")
        r = sc.extract_report("r", text)
        self.assertTrue(any("字段完整率" in p for p in r["problems"]))
        self.assertLess(r["field_completeness"], 1.0)

    def test_complete_entries_no_e5(self):
        r = sc.extract_report("r", "# t\n" + SECTION)
        self.assertEqual(r["field_completeness"], 1.0)
        self.assertFalse(any("字段完整率" in p for p in r["problems"]))

    def test_collect_adds_fingerprint(self):
        self._biz("01-x", "# t\n" + SECTION)
        with mock.patch.object(_common, "ROOT", self.root), \
                mock.patch.object(sc, "ROOT", self.root), \
                mock.patch.object(sc, "iter_business_dirs",
                                  return_value=[_common.Business("01-x")]):
            out = sc.collect()
        self.assertTrue(out[0]["fingerprint"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
