"""架构守卫测试（ARCH-OPT-2026-11）。

覆盖两类硬性一致性：
- 文档数字 ↔ 代码实测：工具数、测试数、类型数、工作流数（方向 A / I-1）；
- 注册一致性：template-registry.md ↔ _common.TEMPLATE_TYPE_DIRS ↔ compliance-rules.json（方向 A / I-2）。

另含方向 B / C 的基础设施用例：atomic_write 原子性与 resolve_within 越界防护。

运行：python -m unittest discover -s engine/tests -v
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

from _common import (  # noqa: E402
    ROOT as CROOT,
)
from _common import (  # noqa: E402
    TEMPLATE_TYPE_DIRS,
    atomic_write,
    resolve_within,
)

TOOLS_DIR = CROOT / "engine" / "tools"
DOCS_DIR = CROOT / "docs"
WORKFLOWS_DIR = CROOT / ".github" / "workflows"


def _tool_files() -> set[str]:
    """代码中的工具脚本（排除公共内核 _common.py）。"""
    return {p.name for p in TOOLS_DIR.glob("*.py") if p.name != "_common.py"}


def _readme_tool_names() -> set[str]:
    """engine/scripts/README.md「工具一览」表中登记的工具文件名。"""
    lines = (CROOT / "engine" / "tools" / "README.md").read_text(encoding="utf-8").splitlines()
    names: set[str] = set()
    in_section = False
    for ln in lines:
        if ln.startswith("## "):
            if ln.strip() == "## 工具一览":
                in_section = True
                continue
            if in_section:
                break
        elif in_section:
            names.update(re.findall(r"([A-Za-z0-9_]+\.py)", ln))
    return names


class TestDocNumberGuard(unittest.TestCase):
    """方向 A / I-1：文档易变数字与代码实测一致。"""

    def test_tool_count_matches_readme(self):
        actual = _tool_files()
        documented = _readme_tool_names()
        self.assertEqual(
            actual, documented,
            f"工具清单不一致：仅代码 {sorted(actual - documented)}；"
            f"仅文档 {sorted(documented - actual)}",
        )

    def test_workflow_count_matches_ci_doc(self):
        actual = len(list(WORKFLOWS_DIR.glob("*.yml")))
        text = (DOCS_DIR / "CI.md").read_text(encoding="utf-8")
        m = re.search(r"(\d+)\s*条工作流", text)
        self.assertIsNotNone(m, "docs/CI.md 未找到「N 条工作流」表述")
        self.assertEqual(actual, int(m.group(1)), "工作流数量与 docs/CI.md 不一致")

    def test_test_count_matches_ci_doc(self):
        suite = unittest.defaultTestLoader.discover(str(ROOT / "engine" / "tests"))
        actual = suite.countTestCases()
        text = (DOCS_DIR / "CI.md").read_text(encoding="utf-8")
        m = re.search(r"`engine/tests/`\s*，\s*(\d+)\s*项", text)
        self.assertIsNotNone(m, "docs/CI.md 未找到测试数表述")
        self.assertEqual(actual, int(m.group(1)), "测试数与 docs/CI.md 不一致")


class TestRegistrationConsistency(unittest.TestCase):
    """方向 A / I-2：类型注册三处一致。"""

    def test_type_registration_consistent(self):
        common_types = set(TEMPLATE_TYPE_DIRS)
        reg_text = (CROOT / "engine" / "report_templates" / "template-registry.md").read_text(encoding="utf-8")
        m = re.search(r"##\s*二、已注册类型清单(.*?)\n##\s*", reg_text, re.DOTALL)
        self.assertIsNotNone(m, "template-registry.md 未找到第二节")
        registry_types = set(re.findall(r"^\|\s*([a-z][a-z0-9-]*)\s*\|", m.group(1), re.M))
        rules = json.loads(
            (CROOT / "engine" / "report_templates" / "compliance-rules.json").read_text(encoding="utf-8")
        )
        rules_types = set(rules.get("types", {}))
        self.assertEqual(common_types, registry_types,
                         "_common.TEMPLATE_TYPE_DIRS 与 template-registry.md 不一致")
        self.assertEqual(common_types, rules_types,
                         "_common.TEMPLATE_TYPE_DIRS 与 compliance-rules.json 不一致")


class TestAtomicWrite(unittest.TestCase):
    """方向 B：atomic_write 原子性与失败回滚。"""

    def test_atomic_write_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.txt"
            atomic_write(p, "hello\n")
            self.assertEqual(p.read_text(encoding="utf-8"), "hello\n")
            self.assertFalse(p.with_name("a.txt.tmp").exists())

    def test_atomic_write_failure_keeps_original(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.txt"
            p.write_text("orig", encoding="utf-8")
            with unittest.mock.patch("builtins.open", side_effect=OSError("boom")), \
                    self.assertRaises(OSError):
                atomic_write(p, "new")
            self.assertEqual(p.read_text(encoding="utf-8"), "orig")


class TestResolveWithin(unittest.TestCase):
    """方向 C：resolve_within 越界防护。"""

    def test_inside_ok(self):
        p = resolve_within(CROOT, "docs/CI.md")
        self.assertTrue(p.is_file())

    def test_outside_rejected(self):
        with self.assertRaises(ValueError):
            resolve_within(CROOT, "../outside.txt")
