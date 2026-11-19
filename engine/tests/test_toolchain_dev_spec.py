"""工具链开发规约守卫测试（TOOLCHAIN-DEV-SPEC 第九节；mainline 融合 P2）。

断言规约文件、覆盖率单一事实源、运行范围与合并前检查单不被篡改或漏接，
防止「选择性吸收」退化回「无规格 / 无门禁 / 无评审」。
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "engine" / "tools"
sys.path.insert(0, str(TOOLS))

SPEC = ROOT / "docs" / "toolchain" / "TOOLCHAIN-DEV-SPEC.md"
COVERAGE_CONFIG = TOOLS / "coverage-config.json"
COVERAGERC = ROOT / ".coveragerc"
TOOLS_README = TOOLS / "README.md"


class TestSpecExists(unittest.TestCase):
    def test_spec_file_present(self):
        self.assertTrue(SPEC.is_file(), "缺少 TOOLCHAIN-DEV-SPEC.md")

    def test_stage_order_fixed(self):
        text = SPEC.read_text(encoding="utf-8")
        order = [text.find(f"| S{i} |") for i in range(1, 7)]
        self.assertTrue(all(i >= 0 for i in order), "规格缺少 S1–S6 阶段定义")
        self.assertEqual(order, sorted(order), "S1–S6 阶段顺序被改动")

    def test_boundary_declared(self):
        text = SPEC.read_text(encoding="utf-8")
        self.assertIn("适用范围", text)
        self.assertIn("不适用", text)
        self.assertIn("engine/tools/", text)
        self.assertIn("engine/scripts/", text)

    def test_exemption_threshold_declared(self):
        text = SPEC.read_text(encoding="utf-8")
        self.assertIn("≤2 文件", text)
        self.assertIn("免", text)

    def test_threshold_staging_documented(self):
        text = SPEC.read_text(encoding="utf-8")
        self.assertIn("60", text)
        self.assertIn("80", text)


class TestCoverageConfig(unittest.TestCase):
    def test_config_exists_and_shape(self):
        self.assertTrue(COVERAGE_CONFIG.is_file(), "缺少 coverage-config.json")
        data = json.loads(COVERAGE_CONFIG.read_text(encoding="utf-8"))
        self.assertIsInstance(data["threshold"], int)
        self.assertIsInstance(data["enforce"], bool)
        self.assertTrue(data["test_discovery"])

    def test_source_limited_to_toolchain(self):
        text = COVERAGERC.read_text(encoding="utf-8")
        self.assertIn("engine/tools", text)
        self.assertIn("engine/vocabulary/script", text)
        self.assertIn("tools", text)
        # 内容层路径不得进入统计范围
        self.assertNotIn("reports/", text.split("[report]")[0])

    def test_coverage_gate_registered(self):
        self.assertTrue((TOOLS / "coverage_gate.py").is_file())
        self.assertTrue((TOOLS / "review_gate.py").is_file())


class TestMergeChecklist(unittest.TestCase):
    def test_checklist_section_present(self):
        text = TOOLS_README.read_text(encoding="utf-8")
        self.assertIn("合并前检查单", text)

    def test_checklist_has_four_items(self):
        text = TOOLS_README.read_text(encoding="utf-8")
        for kw in ("测试", "validate", "评审", "工作区卫生"):
            self.assertIn(kw, text)


class TestReviewScopeMatchesSpec(unittest.TestCase):
    def test_review_gate_scope(self):
        import review_gate
        for p in ("engine/tools/validate.py",
                  "engine/vocabulary/script/vocab_tool.py",
                  "engine/scripts/workflow_guard.py"):
            self.assertTrue(review_gate.is_toolchain_path(p), p)
        self.assertFalse(review_gate.is_toolchain_path("01-ssw-driver/reports/2026-11-x.md"))


class TestReviewCoverage(unittest.TestCase):
    """T8-b：每个工单 slug 必须有对应评审，或工单内显式标「免评审」。

    规格：docs/toolchain/specs/align-2026-11-19.md。
    判定：slug 出现在 docs/toolchain/reviews/*.md 任一正文，或工单正文含「免评审」。
    """

    TICKETS = ROOT / "docs" / "toolchain" / "tickets"
    REVIEWS = ROOT / "docs" / "toolchain" / "reviews"

    def test_reviews_dir_not_empty(self):
        self.assertTrue(self.REVIEWS.is_dir(), "缺少 docs/toolchain/reviews/")
        self.assertTrue(
            any(p.suffix.lower() == ".md" for p in self.REVIEWS.iterdir()),
            "docs/toolchain/reviews/ 无 .md 评审报告",
        )

    def _review_headers(self) -> str:
        """汇总各评审的标题行与「工单」声明行（覆盖来源）。"""
        parts = []
        for p in sorted(self.REVIEWS.glob("*.md")):
            lines = p.read_text(encoding="utf-8").splitlines()
            keep = [ln for ln in lines
                    if ln.startswith("#")
                    or ln.startswith("> **工单**")
                    or ln.startswith("> 工单")]
            parts.append("\n".join(keep))
        return "\n".join(parts)

    def test_every_ticket_has_review_or_exemption(self):
        headers = self._review_headers()
        missing = []
        for ticket in sorted(self.TICKETS.glob("*.md")):
            slug = ticket.stem
            # 精确匹配：slug 前后不得是 kebab-case 字符，避免 coverage-gate
            # 误命中 n3-close-coverage-gate-t10 之类的子串。
            pattern = re.compile(r"(?<![a-z0-9-])" + re.escape(slug) + r"(?![a-z0-9-])")
            if pattern.search(headers):
                continue
            if "免评审" in ticket.read_text(encoding="utf-8"):
                continue
            missing.append(slug)
        self.assertEqual(
            missing, [],
            f"工单缺少对应评审（或在工单内显式标「免评审」）：{missing}",
        )


if __name__ == "__main__":
    unittest.main()
