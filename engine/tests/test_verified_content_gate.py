"""``engine/tools/verified_content_gate.py`` 单元测试。

覆盖：策略加载（schema / 缺字段）、内容层命中、记录层章节豁免、
表格状态列豁免、行级豁免，以及主入口退出码（0 / 1 / 2）。

全部在 ``tempfile`` 临时目录内构造，不触碰真实仓库文件。
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


vcg = _load("verified_content_gate", "engine/tools/verified_content_gate.py")


def _policy(tmp: Path, **over) -> Path:
    data = {
        "schema": "1.0",
        "markers": ["待核实", "未核实", "需核实原文"],
        "record_sections": {"report": ["置信度标注", "信息差与未核验清单"], "registry": [], "handbook": [], "vocab": []},
        "status_columns": ["核验状态", "置信度"],
        "excluded_files": ["source-backlog.md"],
        "excluded_lines": ["来源规则"],
    }
    data.update(over)
    p = tmp / "verified-content-policy.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def _scan(text: str, kind: str = "report", policy: dict | None = None):
    pol = policy or {
        "markers": ["待核实", "未核实", "需核实原文"],
        "record_sections": {"report": ["置信度标注", "信息差与未核验清单"], "registry": [], "handbook": [], "vocab": []},
        "status_columns": ["核验状态", "置信度"],
        "excluded_files": ["source-backlog.md"],
        "excluded_lines": ["来源规则"],
    }
    return vcg.scan_text(text, kind, pol)


class PolicyCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_load_ok(self) -> None:
        p = _policy(self.root)
        with mock.patch.object(vcg, "POLICY_PATH", p):
            data = vcg.load_policy()
        self.assertEqual(data["schema"], "1.0")

    def test_load_bad_schema(self) -> None:
        p = _policy(self.root, schema="9.9")
        with mock.patch.object(vcg, "POLICY_PATH", p), self.assertRaises(vcg.PolicyError):
            vcg.load_policy()

    def test_load_missing_field(self) -> None:
        p = _policy(self.root)
        data = json.loads(p.read_text(encoding="utf-8"))
        data.pop("markers")
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        with mock.patch.object(vcg, "POLICY_PATH", p), self.assertRaises(vcg.PolicyError):
            vcg.load_policy()

    def test_load_missing_file(self) -> None:
        with mock.patch.object(vcg, "POLICY_PATH", self.root / "nope.json"), self.assertRaises(vcg.PolicyError):
            vcg.load_policy()


class ScanCase(unittest.TestCase):
    def test_content_hit(self) -> None:
        hits = _scan("正文一句。\n\n- 某数值 ⚠ 待核实。\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["line"], 3)
        self.assertIn("待核实", hits[0]["markers"])

    def test_record_section_exempt(self) -> None:
        text = "## 一、正文\n\n- 可核实事实。\n\n## 置信度标注\n\n| 结论 | 状态 |\n|---|---|\n| 某结论 | 待核实 |\n"
        self.assertEqual(_scan(text), [])

    def test_record_section_ends_at_next_same_level(self) -> None:
        text = "## 置信度标注\n\n| a | 待核实 |\n\n## 二、正文\n\n- 某数值 ⚠ 待核实。\n"
        hits = _scan(text)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["line"], 7)

    def test_status_column_exempt(self) -> None:
        text = "| 词条 | 核验状态 | 置信度 |\n|---|---|---|\n| X | 待核实 | 待评 |\n"
        self.assertEqual(_scan(text, kind="vocab"), [])

    def test_table_content_column_hit(self) -> None:
        text = "| 词条 | 核验状态 | 定义 |\n|---|---|---|\n| X | 已核验 | 口径待核实 |\n"
        hits = _scan(text, kind="vocab")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["line"], 3)

    def test_excluded_line(self) -> None:
        text = "> **来源规则**：仅英 / 日来源，相关数值暂标「待核实」。\n\n- 可核实事实。\n"
        self.assertEqual(_scan(text), [])

    def test_multiple_markers_reported(self) -> None:
        hits = _scan("- 甲待核实、乙未核实。\n")
        self.assertEqual(set(hits[0]["markers"]), {"待核实", "未核实"})


class KindCase(unittest.TestCase):
    def test_kind_of(self) -> None:
        self.assertEqual(vcg.kind_of("01-x/reports/2026-11-x.md"), "report")
        self.assertEqual(vcg.kind_of("01-x/handbook/00-navigation.md"), "handbook")
        self.assertEqual(vcg.kind_of("01-x/data/x_indicator_registry.md"), "registry")
        self.assertEqual(vcg.kind_of("engine/vocabulary/data/01-x/terms.md"), "vocab")


class ExitCodeCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.root / "01-x" / "reports").mkdir(parents=True)
        self.rel = "01-x/reports/2026-11-x.md"

    def _run(self, text: str, *args: str) -> int:
        (self.root / self.rel).write_text(text, encoding="utf-8")
        policy = _policy(self.root)
        with mock.patch.object(vcg, "POLICY_PATH", policy), \
             mock.patch.object(vcg, "ROOT", self.root), \
             mock.patch.object(vcg, "iter_targets", return_value=[(self.rel, "report")]), \
             mock.patch.object(sys, "argv", ["verified_content_gate", *args]):
            return vcg.main(["--all", *args])

    def test_exit_0_clean(self) -> None:
        self.assertEqual(self._run("- 可核实事实。\n"), 0)

    def test_exit_1_hit(self) -> None:
        self.assertEqual(self._run("- 某数值 ⚠ 待核实。\n"), 1)

    def test_exit_2_warn(self) -> None:
        self.assertEqual(self._run("- 某数值 ⚠ 待核实。\n", "--warn"), 2)


if __name__ == "__main__":
    unittest.main()
