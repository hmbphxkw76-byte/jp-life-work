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

# 2026-11-19 过程留痕文档（在库、不纳入 14 份规范清单）
PROCESS_TRACE_DOCS = (
    "docs/登记册待核实项复核记录-2026-11-19.md",
    "docs/门户URL核验深化方案-2026-11-19.md",
    "docs/核验证据包-2026-11-19",
    "docs/未完成项与对齐状态梳理-2026-11-19.md",
)


def _job_step_names(path: Path) -> dict[str, list[str]]:
    """解析 workflow 的 ``jobs:`` 块，返回 ``{job: [step name, ...]}``。

    仅用标准库按缩进解析，不引入 YAML 依赖；步骤名取 ``- name:`` 后的文本。
    """
    jobs: dict[str, list[str]] = {}
    current: str | None = None
    in_jobs = False
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ln.strip() == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue
        m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", ln)
        if m:
            current = m.group(1)
            jobs[current] = []
            continue
        if current is not None:
            m = re.match(r"^\s*-\s*name:\s*(.*?)\s*$", ln)
            if m:
                jobs[current].append(m.group(1))
    return jobs


def _section(text: str, heading_prefix: str) -> str:
    """按 ``###`` 标题切分文档，返回以 ``heading_prefix`` 开头的节。"""
    for part in re.split(r"(?m)^###\s+", text):
        if part.startswith(heading_prefix):
            return part
    return ""


_CN_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
             "六": 6, "七": 7, "八": 8, "九": 9}


def _cn_to_int(s: str) -> int:
    """中文数字（十 / 十二 / 十三 等）转整数。"""
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + _CN_DIGITS[s[1:]]
    if s.endswith("十"):
        return _CN_DIGITS[s[0]] * 10
    if "十" in s:
        a, b = s.split("十", 1)
        return _CN_DIGITS[a] * 10 + _CN_DIGITS[b]
    return _CN_DIGITS[s]


def _vocab_term_count() -> int:
    """实测词库条数：汇总 ``engine/vocabulary/data/*/terms.md`` 的 ``| XXX-NNN`` 行。"""
    total = 0
    for terms in sorted((CROOT / "engine" / "vocabulary" / "data").glob("*/terms.md")):
        total += sum(
            1 for ln in terms.read_text(encoding="utf-8").splitlines()
            if re.match(r"^\|\s*[A-Z]{3}-\d+", ln)
        )
    return total


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


class TestDocImplAlignmentGuard(unittest.TestCase):
    """文档 ↔ 实现对齐守卫（2026-11-19 审计漂移整改）。

    锁定五类易变数字 / 声明：类型数、词库条数、CI 步骤数 ↔ workflow 实测、
    覆盖率基线 ↔ `engine/scripts/README.md`、`docs/README.md` 一次性文档声明。
    """

    def test_type_count_docs_match_registry(self):
        actual = len(TEMPLATE_TYPE_DIRS)
        readme = (CROOT / "engine" / "README.md").read_text(encoding="utf-8")
        prompt_doc = (DOCS_DIR / "提示词库体系.md").read_text(encoding="utf-8")
        checks = (
            (readme, r"(\d+)\s*个类型目录"),
            (readme, r"类型注册表（(\d+)\s*类）"),
            (readme, r"(\d+)\s*类模板"),
            (prompt_doc, r"(\d+)\s*类模板"),
        )
        for text, pat in checks:
            found = re.findall(pat, text)
            self.assertTrue(found, f"未找到类型数表述：{pat}")
            for raw in found:
                self.assertEqual(int(raw), actual,
                                 f"类型数漂移：{pat} → {raw}，实测 {actual}")
        m = re.search(r"六族([一二三四五六七八九十]+)类", readme)
        self.assertIsNotNone(m, "engine/README.md 未找到「六族N类」表述")
        self.assertEqual(_cn_to_int(m.group(1)), actual,
                         "engine/README.md 六族类数与实测不符")

    def test_vocab_term_count_docs_match_terms(self):
        actual = _vocab_term_count()
        prompt_doc = (DOCS_DIR / "提示词库体系.md").read_text(encoding="utf-8")
        roles_doc = (DOCS_DIR / "cross-domain-expert-roles.md").read_text(encoding="utf-8")
        for m in re.finditer(r"(\d+)\s*主题\s*/\s*(\d+)\s*条", prompt_doc):
            self.assertEqual(int(m.group(2)), actual,
                             f"提示词库体系.md 词条数漂移：{m.group(2)}，实测 {actual}")
        for m in re.finditer(r"(\d+)\s*主题\s+(\d+)\s*条", roles_doc):
            self.assertEqual(int(m.group(2)), actual,
                             f"cross-domain-expert-roles.md 词条数漂移：{m.group(2)}，实测 {actual}")

    def test_ci_step_counts_match_workflows(self):
        ci = (DOCS_DIR / "CI.md").read_text(encoding="utf-8")
        flow = (DOCS_DIR / "信息生产全链路执行规范.md").read_text(encoding="utf-8")
        validate_names = _job_step_names(WORKFLOWS_DIR / "validate.yml")["validate"]
        maintenance_names = _job_step_names(WORKFLOWS_DIR / "scheduled-maintenance.yml")["maintain"]
        audit_names = _job_step_names(WORKFLOWS_DIR / "audit-gate.yml")["audit"]

        def named(names: list[str]) -> list[str]:
            return [n for n in names if n != "安装依赖"]

        sec = _section(ci, "1. `validate.yml`")
        m = re.search(
            r"主 job\s*\*\*(\d+)\s*个命名步骤\*\*.*?主 job 实际共\s*(\d+)\s*个\s*`-\s*name:`\s*步骤",
            sec, re.DOTALL,
        )
        self.assertIsNotNone(m, "docs/CI.md 二.1 未找到 validate 步骤数表述")
        self.assertEqual(int(m.group(1)), len(named(validate_names)),
                         "validate 命名步骤数与 workflow 实测不符")
        self.assertEqual(int(m.group(2)), len(validate_names),
                         "validate `- name:` 步骤数与 workflow 实测不符")

        m2 = re.search(r"主 job\s+(\d+)\s*个命名步骤", flow)
        self.assertIsNotNone(m2, "总规范 §三 未找到 validate 步骤数表述")
        self.assertEqual(int(m2.group(1)), len(named(validate_names)),
                         "总规范 §三 validate 步骤数与实测不符")

        sec3 = _section(ci, "3. `scheduled-maintenance.yml`")
        m3 = re.search(r"共\s*\*\*(\d+)\s*步\*\*", sec3)
        self.assertIsNotNone(m3, "docs/CI.md 二.3 未找到 maintenance 步骤数表述")
        self.assertEqual(int(m3.group(1)), len(named(maintenance_names)),
                         "maintenance 步骤数与 workflow 实测不符")

        sec6 = _section(ci, "6. `audit-gate.yml`")
        m6 = re.search(r"共\s*\*\*(\d+)\s*步\*\*", sec6)
        self.assertIsNotNone(m6, "docs/CI.md 二.6 未找到 audit-gate 步骤数表述")
        self.assertEqual(int(m6.group(1)), len(named(audit_names)),
                         "audit-gate 步骤数与 workflow 实测不符")

    def test_coverage_baseline_matches_scripts_readme(self):
        readme = (CROOT / "engine" / "scripts" / "README.md").read_text(encoding="utf-8")
        m = re.search(r"(\d+(?:\.\d+)?)%\s*（阈值\s*(\d+)%，enforce=(true|false)）", readme)
        self.assertIsNotNone(m, "engine/scripts/README.md §十二 未找到覆盖率表述")
        config = json.loads((TOOLS_DIR / "coverage-config.json").read_text(encoding="utf-8"))
        baseline = json.loads(
            (CROOT / "engine" / "report-audits" / "toolchain" / "coverage-baseline.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(int(m.group(2)), config["threshold"],
                         "阈值与 coverage-config.json 不符")
        self.assertEqual(m.group(3), str(config["enforce"]).lower(),
                         "enforce 与 coverage-config.json 不符")
        documented = float(m.group(1))
        self.assertLessEqual(
            abs(documented - float(baseline["total_percent"])), 0.5,
            f"覆盖率基线漂移：scripts/README {documented}% vs baseline {baseline['total_percent']}%",
        )
        self.assertGreaterEqual(documented, config["threshold"],
                                "文档覆盖率低于阈值")

    def test_docs_readme_process_docs_statement(self):
        for rel in PROCESS_TRACE_DOCS:
            self.assertTrue((CROOT / rel).exists(), f"过程留痕文档缺失：{rel}")
        text = (DOCS_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("过程留痕", text, "docs/README.md 未声明过程留痕文档")
        self.assertIn("保留在库", text, "docs/README.md 未声明过程留痕文档保留在库")
        for stale in ("随一次性记录删除", "未纳入版本库", "git 全历史无记录"):
            self.assertNotIn(stale, text,
                             f"docs/README.md 仍含与实库不符的声明：{stale}")
        m = re.search(r"##\s*一、文档清单（(\d+)\s*份规范）", text)
        self.assertIsNotNone(m, "docs/README.md 未找到文档清单标题")
        self.assertEqual(int(m.group(1)), 14, "docs/README.md 规范清单份数应为 14")
        sec = re.search(r"##\s*一、文档清单.*?(?=\n##\s*二、)", text, re.DOTALL)
        self.assertIsNotNone(sec, "docs/README.md 未找到文档清单节")
        rows = re.findall(r"^\|\s*\[", sec.group(0), re.M)
        self.assertEqual(len(rows), 14,
                         f"docs/README.md 规范清单实际 {len(rows)} 行，应 14")


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
