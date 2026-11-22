"""提交前内容硬门禁测试（precommit_content_gate.py）。

覆盖：暂存报告命中阻断、干净放行、中文来源域名、缺来源章节、提示词层违规、
无暂存快速退出、main 退出码。hermetic：tempfile + mock，不改真实仓库。
运行：python -m unittest discover -s engine/tests
"""
from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "scripts"))
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import precommit_content_gate as pcg  # noqa: E402

GOOD_REPORT = """# 测试报告

## 结论

数值 1（来源：官方统计，2026-11 核对）。

## 参考来源清单

- 官方统计 https://example.go.jp/a (2026)
"""

BAD_MARKER = GOOD_REPORT.replace("数值 1", "数值待核实 1")
BAD_DOMAIN = GOOD_REPORT.replace("https://example.go.jp/a", "https://gov.cn/a")
NO_SOURCE = "# 测试报告\n\n## 结论\n\n数值 1。\n"


class GateEntriesCase(unittest.TestCase):
    def test_clean_report_passes(self):
        self.assertEqual(pcg.gate_entries([("01-x/reports/2026-11-x.md", "report", GOOD_REPORT)]), [])

    def test_unverified_marker_blocks(self):
        f = pcg.gate_entries([("01-x/reports/2026-11-x.md", "report", BAD_MARKER)])
        self.assertTrue(any(x.code == "PC-CONTENT" and x.severity == "P1" for x in f))

    def test_blocked_domain_blocks(self):
        f = pcg.gate_entries([("01-x/reports/2026-11-x.md", "report", BAD_DOMAIN)])
        self.assertTrue(any(x.code == "PC-LANG" for x in f))

    def test_missing_source_section_blocks(self):
        f = pcg.gate_entries([("01-x/reports/2026-11-x.md", "report", NO_SOURCE)])
        self.assertTrue(any(x.code == "PC-SOURCE" for x in f))

    def test_prompt_forbidden_pattern_blocks(self):
        bad_prompt = "# 提示词\n\n来源可引用中文一手资料。\n"
        f = pcg.gate_entries([("01-x/prompts/business-config.md", "other", bad_prompt)])
        self.assertTrue(any(x.code == "PC-LANG" for x in f))

    def test_prompt_marker_not_content_scanned(self):
        # prompts 为指令文本，合法含标记词；不做内容层扫描（只做来源语言层）。
        prompt = "# 提示词\n\n本文含待核实内容。\n"
        f = pcg.gate_entries([("01-x/prompts/business-config.md", "other", prompt)])
        self.assertFalse(any(x.code == "PC-CONTENT" for x in f))

    def test_non_prompt_doc_not_language_scanned(self):
        # 工具 README / CI 文档等讨论政策本身不视为违规（与 check_prompts 同口径）。
        doc = "# 工具文档\n\n本文讨论「中文一手」政策。\n"
        f = pcg.gate_entries([("engine/tools/README.md", "other", doc)])
        self.assertFalse(any(x.code == "PC-LANG" for x in f))

    def test_empty_entries(self):
        self.assertEqual(pcg.gate_entries([]), [])


class MainCase(unittest.TestCase):
    def test_main_blocks_on_hit(self):
        entries = [("01-x/reports/2026-11-x.md", "report", BAD_MARKER)]
        buf = io.StringIO()
        with mock.patch.object(pcg, "staged_entries", return_value=entries), redirect_stdout(buf):
            code = pcg.main()
        self.assertEqual(code, 1)
        self.assertIn("PC-CONTENT", buf.getvalue())

    def test_main_passes_clean(self):
        entries = [("01-x/reports/2026-11-x.md", "report", GOOD_REPORT)]
        buf = io.StringIO()
        with mock.patch.object(pcg, "staged_entries", return_value=entries), redirect_stdout(buf):
            code = pcg.main()
        self.assertEqual(code, 0)

    def test_main_no_staged(self):
        buf = io.StringIO()
        with mock.patch.object(pcg, "staged_entries", return_value=[]), redirect_stdout(buf):
            code = pcg.main()
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
