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


if __name__ == "__main__":
    unittest.main()
