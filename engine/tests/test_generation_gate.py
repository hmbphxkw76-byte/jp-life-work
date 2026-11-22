"""生成前信息核验（闸0）测试（generation_gate.py）。

覆盖：单主题核验、命中阻断、全量汇总、已知 P2 放行、CLI 退出码。
hermetic：合成主题用 tempfile，真实主题只读。
运行：python -m unittest discover -s engine/tests
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import generation_gate  # noqa: E402
from _common import iter_business_dirs  # noqa: E402

GOOD_CONFIG = """# 业务配置

继承：prompt-generic-base.md × engine/report_templates/market-monitoring/
{{REGION}} = 日本
{{TOPIC}} = 测试
{{REGISTRY_PATH}} = data/test_indicator_registry.md
{{SOURCE_LANGUAGE_RULE}} = 仅英文 / 日文来源，杜绝中文来源
"""

GOOD_REGISTRY = """# 指标登记册

| 指标 | 口径 | 活值 | 核验日期 |
|---|---|---|---|
| 测试指标 | 口径A | 1 | 2026-11-01 |
"""

GOOD_REPORT = """# 测试报告

## 结论

数值 1（来源：官方统计，2026-11 核对）。

## 参考来源清单

- 官方统计 https://example.go.jp/a (2026)
"""


def _make_topic(root: Path, rel: str, report_text: str = GOOD_REPORT,
               config_text: str = GOOD_CONFIG) -> SimpleNamespace:
    """构造合成主题目录。"""
    base = root / rel
    (base / "prompts").mkdir(parents=True)
    (base / "data").mkdir(parents=True)
    (base / "reports").mkdir(parents=True)
    (base / "prompts" / "business-config.md").write_text(config_text, encoding="utf-8")
    (base / "data" / "test_indicator_registry.md").write_text(GOOD_REGISTRY, encoding="utf-8")
    (base / "reports" / "2026-11-test.md").write_text(report_text, encoding="utf-8")
    return SimpleNamespace(path=base, rel=rel, region=rel)


class CheckTopicCase(unittest.TestCase):
    def test_clean_topic_passes(self):
        with tempfile.TemporaryDirectory() as d:
            b = _make_topic(Path(d), "99-test")
            findings = generation_gate.check_topic(b)
            codes = {f.code for f in findings}
            self.assertNotIn("G0-CONTENT", codes)
            self.assertNotIn("G0-SOURCE", codes)
            self.assertFalse(any(f.severity in ("P0", "P1") for f in findings))

    def test_unverified_marker_blocks(self):
        bad = GOOD_REPORT.replace("数值 1", "数值待核实 1")
        with tempfile.TemporaryDirectory() as d:
            b = _make_topic(Path(d), "99-test", report_text=bad)
            findings = generation_gate.check_topic(b)
            self.assertTrue(any(f.code == "G0-CONTENT" and f.severity == "P1"
                                for f in findings))

    def test_missing_source_section_blocks(self):
        no_src = "# 测试报告\n\n## 结论\n\n数值 1。\n"
        with tempfile.TemporaryDirectory() as d:
            b = _make_topic(Path(d), "99-test", report_text=no_src)
            findings = generation_gate.check_topic(b)
            self.assertTrue(any(f.code == "G0-SOURCE" for f in findings))

    def test_real_topic_no_blocking(self):
        b = next(b for b in iter_business_dirs() if b.rel == "01-ssw-driver")
        findings = generation_gate.check_topic(b)
        self.assertFalse(any(f.severity in ("P0", "P1") for f in findings))


class RunAllCase(unittest.TestCase):
    def test_summary_shape(self):
        results, summary = generation_gate.run_all()
        self.assertEqual(summary["topics"], len(results))
        self.assertEqual(summary["topics"],
                         summary["passed"] + summary["failed"])
        self.assertIn("by_severity", summary)
        self.assertFalse(any(r["severity"]["P0"] or r["severity"]["P1"]
                             for r in results))


class CliCase(unittest.TestCase):
    def test_json_topic(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = generation_gate.main(["--topic", "01-ssw-driver", "--json"])
        self.assertIn(code, (0, 2))
        data = json.loads(buf.getvalue())
        self.assertEqual(data["topic"], "01-ssw-driver")
        self.assertIn("passed", data)

    def test_json_all(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = generation_gate.main(["--all", "--json"])
        self.assertIn(code, (0, 2))
        data = json.loads(buf.getvalue())
        self.assertIn("summary", data)


if __name__ == "__main__":
    unittest.main()
