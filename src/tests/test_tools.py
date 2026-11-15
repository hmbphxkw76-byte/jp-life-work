"""prompts/tools 单元测试（CI: validate.yml 的 unittest 步骤）。

覆盖：
- 纯函数：报告名解析（新月度命名 + 历史命名）、周期解析、任务推导；
- 归档保留策略、lint 检查、活跃度天数计算；
- 三类重构校验场景：命名格式合规性、全量历史数据迁移完整性、跨月对比准确性。

运行：python -m unittest discover -s src/tests -v
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "prompts-tools" / "tools"))

import _common  # noqa: E402
import audit_pipeline  # noqa: E402
import audit_preflight  # noqa: E402
import audit_registry  # noqa: E402
import compliance_check  # noqa: E402
import lint_reports  # noqa: E402
from archive_reports import select_archives  # noqa: E402
from automation_status import days_since_latest  # noqa: E402
from build_hub import build_outputs, normalize_for_check  # noqa: E402
from compliance_check import check_report, cycle_rule, detect_type, load_rules  # noqa: E402
from lint_reports import lint_html  # noqa: E402
from md2html import convert as md2html_convert  # noqa: E402
from report_diff import (  # noqa: E402
    MOD_SIMILARITY,
    diff_blocks,
    extract_blocks,
    render_diffed_body,
    strip_body,
)
from update_planner import build_tasks, default_period, pick_prompt, target_month  # noqa: E402
import info_quality_check  # noqa: E402
from info_quality_check import evaluate, repair, scan_topics, verify  # noqa: E402


# ──────────────────────────────────────────────
# 命名解析
# ──────────────────────────────────────────────

class TestMonthNaming(unittest.TestCase):
    """现行月度命名规范 YYYY-MM-<slug>。"""

    def test_detect_month_report(self):
        self.assertEqual(
            _common.detect_month_report("2026-11-ssw-driver.html"),
            ("2026-11", "ssw-driver", "html"),
        )
        self.assertEqual(
            _common.detect_month_report("2026-12-decision-hub.md"),
            ("2026-12", "decision-hub", "md"),
        )

    def test_detect_rejects_legacy(self):
        for legacy in (
            "2026-11_baseline_report.html",
            "2026-11-13_initial_analysis_report.md",
            "2026-Q4_quarterly.html",
            "2026-11_monthly.html",
            "2026_annual.html",
        ):
            self.assertIsNone(_common.detect_month_report(legacy), legacy)

    def test_detect_rejects_bad_month(self):
        self.assertIsNone(_common.detect_month_report("2026-13-ssw-driver.html"))
        self.assertIsNone(_common.detect_month_report("2026-11-.html"))
        self.assertIsNone(_common.detect_month_report("random.html"))

    def test_topic_slug(self):
        self.assertEqual(_common.topic_slug("01-ssw-driver"), "ssw-driver")
        self.assertEqual(_common.topic_slug("00-decision-hub"), "decision-hub")
        self.assertEqual(_common.topic_slug("exit-transition-return"), "exit-transition-return")

    def test_month_report_name(self):
        self.assertEqual(_common.month_report_name("2026-11", "ssw-driver"), "2026-11-ssw-driver.md")
        self.assertEqual(
            _common.month_report_name("2026-12", "decision-hub", "html"),
            "2026-12-decision-hub.html",
        )

    def test_quarter_to_month(self):
        self.assertEqual(_common.quarter_to_month("2026-Q4"), "2026-12")
        self.assertEqual(_common.quarter_to_month("2027-Q1"), "2027-03")
        self.assertIsNone(_common.quarter_to_month("2026-11"))

    def test_legacy_still_recognised_for_migration(self):
        self.assertEqual(
            _common.detect_legacy_report("2026-11_baseline_report.md"),
            ("baseline", "2026-11", "md"),
        )
        self.assertEqual(
            _common.detect_legacy_report("2026-11-13_initial_analysis_report.md")[0],
            "initial",
        )


class TestDetectReportLegacy(unittest.TestCase):
    """历史命名仍可识别（迁移与归档读取用）。"""

    def test_legacy_patterns(self):
        self.assertEqual(_common.detect_report("2026-11_monthly.html"), ("monthly", "2026-11", "html"))
        self.assertEqual(_common.detect_report("2026-11_baseline_report.html"), ("baseline", "2026-11", "html"))
        self.assertIsNone(_common.detect_report("2026-11-ssw-driver.html"))


# ──────────────────────────────────────────────
# 周期与任务
# ──────────────────────────────────────────────

class TestParsePeriod(unittest.TestCase):
    def test_month(self):
        self.assertEqual(_common.parse_period("2026-11"), ("month", 2026, 11))

    def test_quarter(self):
        self.assertEqual(_common.parse_period("2026-Q3"), ("quarter", 2026, 3))

    def test_year(self):
        self.assertEqual(_common.parse_period("2026"), ("year", 2026, None))

    def test_invalid(self):
        for bad in ("2026-13", "2026-Q5", "26-Q1", "abc", "2026-1"):
            with self.assertRaises(ValueError):
                _common.parse_period(bad)


class TestTasksForPeriod(unittest.TestCase):
    def test_plain_month(self):
        self.assertEqual(_common.tasks_for_period("month", 2026, 11), [("monthly", 2026, 11)])

    def test_quarter_start_month(self):
        self.assertEqual(
            _common.tasks_for_period("month", 2026, 1),
            [("monthly", 2026, 1), ("quarterly", 2026, 1), ("annual", 2025, None)],
        )


class TestDefaultPeriod(unittest.TestCase):
    def test_plain_month(self):
        self.assertEqual(default_period(datetime(2026, 11, 13, tzinfo=timezone.utc)), "2026-11")

    def test_quarter_start_month(self):
        self.assertEqual(default_period(datetime(2026, 1, 1, tzinfo=timezone.utc)), "2026-Q1")
        self.assertEqual(default_period(datetime(2026, 10, 31, tzinfo=timezone.utc)), "2026-Q4")


class TestTargetMonth(unittest.TestCase):
    def test_month_passthrough(self):
        self.assertEqual(target_month("2026-11"), "2026-11")

    def test_quarter_maps_to_last_month(self):
        self.assertEqual(target_month("2026-Q4"), "2026-12")
        self.assertEqual(target_month("2027-Q1"), "2027-03")

    def test_year_maps_to_december(self):
        self.assertEqual(target_month("2026"), "2026-12")


class TestBuildTasks(unittest.TestCase):
    """任务清单推导（hermetic：在临时目录构造业务线，不依赖真实仓库状态）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._root = Path(self._tmp.name)
        self._orig_root = _common.ROOT
        _common.ROOT = self._root

    def tearDown(self):
        _common.ROOT = self._orig_root
        self._tmp.cleanup()

    def _make_business(self, rel, prompts=(), reports=()):
        base = self._root / rel
        (base / "prompts").mkdir(parents=True)
        (base / "reports").mkdir(parents=True)
        for p in prompts:
            (base / "prompts" / p).write_text("", encoding="utf-8")
        for r in reports:
            (base / "reports" / r).write_text("", encoding="utf-8")
        return _common.Business(rel)

    def test_status_done_when_output_exists(self):
        biz = self._make_business(
            "99-demo", prompts=["prompt-baseline-setup.md"], reports=["2026-11-demo.html"]
        )
        tasks = build_tasks("2026-11", [biz])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["output"], "99-demo/reports/2026-11-demo.html")
        self.assertEqual(tasks[0]["status"], "done")
        self.assertEqual(tasks[0]["cycle_label"], "月度")

    def test_pending_when_output_missing(self):
        biz = self._make_business("99-demo", prompts=["prompt-baseline-setup.md"])
        tasks = build_tasks("2026-12", [biz])
        self.assertEqual(tasks[0]["output"], "99-demo/reports/2026-12-demo.html")
        self.assertEqual(tasks[0]["status"], "pending")

    def test_quarter_period_maps_to_last_month_output(self):
        biz = self._make_business("99-demo", prompts=["prompt-quarterly-analysis.md"])
        tasks = build_tasks("2026-Q4", [biz])
        self.assertEqual(tasks[0]["output"], "99-demo/reports/2026-12-demo.html")


class TestPickPrompt(unittest.TestCase):
    """月度任务选取提示词的优先级。"""

    def test_prefers_monthly_monitor(self):
        prompts = [
            "prompt-annual-review.md",
            "prompt-baseline-setup.md",
            "prompt-monthly-monitor.md",
            "prompt-quarterly-analysis.md",
        ]
        self.assertEqual(pick_prompt(prompts), "prompt-monthly-monitor.md")

    def test_update_beats_baseline_setup(self):
        prompts = ["prompt-baseline-setup.md", "prompt-update.md"]
        self.assertEqual(pick_prompt(prompts), "prompt-update.md")

    def test_falls_back_to_sorted_first(self):
        self.assertEqual(pick_prompt(["prompt-zzz.md", "prompt-aaa.md"]), "prompt-aaa.md")

    def test_empty(self):
        self.assertEqual(pick_prompt([]), "")


class TestSelectArchives(unittest.TestCase):
    def test_keep_latest_12(self):
        items = [(f"2026-{m:02d}", Path(f"2026-{m:02d}-demo.html")) for m in range(1, 13)]
        self.assertEqual(select_archives(items), [], "恰好 12 期时不应归档")

    def test_archive_oldest(self):
        items = [(f"2025-{m:02d}", Path(f"2025-{m:02d}-demo.html")) for m in range(1, 13)]
        items.append(("2026-01", Path("2026-01-demo.html")))
        to_archive = select_archives(items)
        self.assertEqual([p.name for p in to_archive], ["2025-01-demo.html"])


# ──────────────────────────────────────────────
# lint / 合规
# ──────────────────────────────────────────────

class TestLintHtml(unittest.TestCase):
    def test_clean_report(self):
        text = (
            "<html><body>"
            '<nav class="report-nav" aria-label="报告导航"></nav>'
            "<table class=\"fixed\"><thead><tr>"
            '<th style="width:20%">A</th><th style="width:20%">B</th><th style="width:20%">C</th>'
            '<th style="width:20%">D</th><th style="width:20%">E</th>'
            "</tr></thead><tbody><tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td></tr></tbody></table>"
            "</body></html>"
        )
        errors = [i for i in lint_html(text) if i[0] == "E"]
        self.assertEqual(errors, [])

    def test_duplicate_tbody_close(self):
        text = (
            "<table><thead><tr><th>A</th></tr></thead>"
            "<tbody><tr><td>1</td></tr></tbody></tbody></table>"
            "<p>示例文本。</p>"
        )
        issues = lint_html(text)
        self.assertTrue(any(i[0] == "E" and "</tbody>" in i[1] for i in issues))

    def test_malformed_th(self):
        text = '<table><thead><tr><th scope="col"ead>A</th></tr></thead></table><p>示例文本。</p>'
        issues = lint_html(text)
        self.assertTrue(any("畸形" in i[1] for i in issues))

    def test_wide_table_missing_width(self):
        ths = "".join(f"<th>列{i}</th>" for i in range(8))
        text = (
            f"<table><thead><tr>{ths}</tr></thead><tbody><tr><td>1</td></tr></tbody></table>"
            "<p>示例文本。</p>"
        )
        issues = lint_html(text)
        self.assertTrue(any(i[0] == "W" and "未声明百分比列宽" in i[1] for i in issues))


class TestComplianceCheck(unittest.TestCase):
    """报告模板合规校验（compliance_check.py）纯函数用例。"""

    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules()
        cls.common = cls.rules["common"]
        cls.monthly_rule, _ = cycle_rule(cls.rules, "market-monitoring", "monthly")

    @staticmethod
    def _html(sections=8, nav=True, ids=True, title="测试报告",
              extra_anchor=None, extra_id=None):
        parts = [f"<html><head><title>{title}</title></head><body>"]
        if nav:
            anchors = "".join(
                f'<a href="#s{i}">节{i}</a>' for i in range(1, sections + (1 if extra_anchor else 0))
            )
            parts.append(f'<nav class="report-nav" aria-label="报告导航">{anchors}</nav>')
        if extra_id:
            parts.append(f'<div id="{extra_id}"></div>')
        for i in range(1, sections + 1):
            id_attr = f' id="s{i}"' if ids else ""
            parts.append(f'<h2 class="sec"{id_attr}>节{i}</h2><p>正文</p>')
        if extra_anchor:
            parts.append('<a href="#missing-anchor">断链</a>')
        parts.append("</body></html>")
        return "".join(parts)

    def test_detect_type_from_config(self):
        text = "继承声明：周期提示词 = [类型模板](../../../report_templates/employment-research/) × 本文件"
        self.assertEqual(detect_type(text), "employment-research")

    def test_clean_cycle_report_passes(self):
        self.assertEqual(check_report(self._html(), self.monthly_rule, self.common), [])

    def test_missing_section_is_error(self):
        issues = check_report(self._html(sections=7), self.monthly_rule, self.common)
        self.assertTrue(any(i[0] == "E" and "结构不完整" in i[1] for i in issues))

    def test_broken_anchor_is_error(self):
        issues = check_report(self._html(extra_anchor=True), self.monthly_rule, self.common)
        self.assertTrue(any(i[0] == "E" and "断头锚点" in i[1] for i in issues))


# ──────────────────────────────────────────────
# 16-exit-transition-return 业务线
# ──────────────────────────────────────────────

class TestExitTransitionReturnTopic(unittest.TestCase):
    """16-exit-transition-return 业务线机制校验。"""

    def test_topic_structure_and_config_contract(self):
        path = _common.ROOT / "16-exit-transition-return"
        config = path / "prompts" / "business-config.md"
        baseline_prompt = path / "prompts" / "prompt-baseline-setup.md"
        review_prompt = path / "prompts" / "prompt-policy-review.md"
        operations = path / "operations-guide.md"

        self.assertTrue(config.is_file())
        self.assertTrue(baseline_prompt.is_file())
        self.assertTrue(review_prompt.is_file())
        self.assertTrue(operations.is_file())

        text = config.read_text(encoding="utf-8")
        for value in (
            "{{REGION}}",
            "日本",
            "{{TOPIC}}",
            "退出·转型·回国",
            "{{BASELINE_DATE}}",
            "2026-11-14",
            "data/exit_transition_return_indicator_registry.md",
            "reports/{{YYYY-MM}}-<slug>.md",
            "退出",
            "转型",
            "回国",
            "07-economy-finance",
            "08-visa-immigration",
            "14-life-operations",
        ):
            self.assertIn(value, text)

    def test_topic_registered_as_policy_analysis(self):
        registry = (_common.TEMPLATE_ROOT / "template-registry.md").read_text(encoding="utf-8")
        policy_row = next(
            line for line in registry.splitlines()
            if line.startswith("| policy-analysis |")
        )
        self.assertIn("jp/16-exit-transition-return", policy_row)


class TestExitTransitionReturnReports(unittest.TestCase):
    """16-exit-transition-return 月度报告内容契约。"""

    MERGED = _common.ROOT / "16-exit-transition-return" / "reports" / "2026-11-exit-transition-return.md"

    def setUp(self):
        if not self.MERGED.is_file():
            self.skipTest("16-exit-transition-return 报告尚不存在")

    def test_report_contains_baseline_sections(self):
        self.assertTrue(self.MERGED.is_file())
        text = self.MERGED.read_text(encoding="utf-8")
        # 基线九节
        for heading in (
            "一、核心结论（摘要）",
            "二、退出·转型·回国制度台账与监测机制",
            "三、制度框架与三段路径",
            "四、退出与转型政策逐条解读",
            "五、个人场景影响矩阵",
            "六、退出·转型·回国行动建议（建议章）",
            "七、制度变更与个人行动时间线",
            "八、数据可靠性与局限说明",
            "九、参考来源清单",
        ):
            self.assertIn(heading, text)
        for value in (
            "退出", "转型", "回国", "退職", "健康保険任意継続", "厚生年金脱退一时金",
            "在留資格取消", "特定活動", "特定技能 2 号", "帰国前確定申告", "再入国許可",
            "みなし再入国", "退室", "⚠ 待核实",
            "（事实）", "（推断）",
        ):
            self.assertIn(value, text)
        self.assertIn("[出入国在留管理庁](https://www.moj.go.jp/isa/)", text)
        self.assertGreaterEqual(text.count("](https://"), 9)

    def test_registry_updated_with_baseline_values(self):
        registry = (_common.ROOT / "16-exit-transition-return" / "data" / "exit_transition_return_indicator_registry.md").read_text(encoding="utf-8")
        self.assertIn("v2026.11.14_1", registry)
        self.assertIn("⚠ 待核实", registry)
        self.assertIn("2026-11-14", registry)


class TestExitTransitionReturnHtml(unittest.TestCase):
    """16-exit-transition-return HTML 交付物校验。"""

    MERGED = _common.ROOT / "16-exit-transition-return" / "reports" / "2026-11-exit-transition-return.html"

    def setUp(self):
        if not self.MERGED.is_file():
            self.skipTest("16-exit-transition-return 报告尚不存在")

    def test_html_report_passes_lint(self):
        self.assertTrue(self.MERGED.is_file())
        text = self.MERGED.read_text(encoding="utf-8")
        self.assertIn("<title>", text)
        self.assertIn('class="report-nav"', text)
        self.assertIn('class="nav-tabs"', text)
        self.assertIn('id="s1"', text)
        self.assertEqual([i for i in lint_html(text) if i[0] == "E"], [])
        self.assertRegex(text, r'<a[^>]+href="https?://[^"]+"')
        self.assertIn('class="fixed"', text)

    def test_html_anchors_resolve(self):
        text = self.MERGED.read_text(encoding="utf-8")
        nav = re.search(r'<div class="nav-tabs">(.*?)</div>', text, re.S)
        self.assertIsNotNone(nav)
        for anchor in re.findall(r'href="#(s\d+)"', nav.group(1)):
            self.assertIn(f'id="{anchor}"', text)


class TestExitTransitionReturnIntegration(unittest.TestCase):
    """16-exit-transition-return 与 00 决策枢纽、根索引的集成校验。"""

    def test_decision_hub_references_topic(self):
        path = _common.ROOT / "00-decision-hub" / "data" / "decision_hub_registry.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("16-exit-transition-return", text)
        self.assertIn("退出·转型·回国", text)
        self.assertIn("已建 16", text)

    def test_root_index_includes_topic(self):
        path = _common.ROOT / "index.html"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("16-exit-transition-return", text)
        self.assertIn("退出·转型·回国", text)
        # 报告链接直达独立报告页（新标签页），不再依赖阅读器
        self.assertIn(
            'href="00-decision-hub/reports/2026-12-decision-hub.html" target="_blank"',
            text,
        )
        self.assertNotIn("reader.html", text)


# ──────────────────────────────────────────────
# 汇总页
# ──────────────────────────────────────────────

class TestBuildHubCheck(unittest.TestCase):
    """汇总页 --check 归一化比对（build_hub.py）用例。"""

    def test_normalize_strips_timestamp(self):
        a = '<p class="muted">最近生成：2026-11-13 01:00 UTC</p>\n<h2>x</h2>'
        b = '<p class="muted">最近生成：2026-11-13 09:30 UTC</p>\n<h2>x</h2>'
        self.assertEqual(normalize_for_check(a), normalize_for_check(b))

    def test_normalize_keeps_other_diffs(self):
        a = '<p class="muted">最近生成：2026-11-13 01:00 UTC</p>\n<h2>x</h2>'
        b = '<p class="muted">最近生成：2026-11-13 01:00 UTC</p>\n<h2>y</h2>'
        self.assertNotEqual(normalize_for_check(a), normalize_for_check(b))

    def test_committed_index_matches_regen_ignoring_timestamp(self):
        if not (_common.ROOT / "index.html").exists():
            self.skipTest("根目录 index.html 尚未生成（build_hub 首建前）")
        committed = (_common.ROOT / "index.html").read_text(encoding="utf-8", errors="replace")
        self.assertEqual(
            normalize_for_check(committed),
            normalize_for_check(build_outputs()["index.html"]),
            "报告清单未变时，已提交 index.html 归一化后应与重算内容一致",
        )

    def test_hub_links_to_independent_report_pages(self):
        """汇总页生成 index.html + search-index.json，报告链接直达各主题 reports/*.html。"""
        outputs = build_outputs()
        self.assertEqual(list(outputs), ["index.html", "search-index.json"])
        self.assertNotIn("reader.html", outputs["index.html"])
        self.assertIn('href="00-decision-hub/reports/2026-12-decision-hub.html" target="_blank"', outputs["index.html"])
        # 搜索索引：覆盖全部报告，且含中文关键词与问题
        index = json.loads(outputs["search-index.json"])
        self.assertGreaterEqual(len(index["reports"]), 20)
        self.assertTrue(all(r["keywords"] for r in index["reports"]))
        self.assertGreaterEqual(len(index["questions"]), 40)


# ──────────────────────────────────────────────
# 三类重构校验场景
# ──────────────────────────────────────────────

class TestNamingCompliance(unittest.TestCase):
    """场景一：命名格式合规性校验。

    全部报告必须符合 `YYYY-MM-<主题slug>.md/.html`，slug 与目录一致，
    且 md / html 成对存在；不得残留历史类型标签命名。
    """

    LEGACY_RE = re.compile(
        r"_(baseline|baseline_report|initial_analysis_report|monthly|quarterly|annual|weekly)"
        r"(\.md|\.html)$"
    )

    def test_all_reports_match_monthly_naming(self):
        checked = 0
        for b in _common.iter_business_dirs():
            reports = b.path / "reports"
            if not reports.is_dir():
                continue
            rs = _common.topic_slug(b.region if not b.property_type else b.property_type)
            for f in reports.iterdir():
                if not f.is_file() or f.suffix not in (".md", ".html"):
                    continue
                det = _common.detect_month_report(f.name)
                self.assertIsNotNone(det, f"{b.rel}/reports/{f.name} 不符合月度命名")
                self.assertEqual(det[1], rs, f"{b.rel}/reports/{f.name} slug 与目录不一致")
                self.assertNotRegex(f.name, self.LEGACY_RE, f"{f.name} 残留历史类型标签")
                checked += 1
        self.assertGreater(checked, 0, "应至少校验到一份报告")

    def test_md_html_pairs_exist(self):
        for b in _common.iter_business_dirs():
            reports = b.path / "reports"
            if not reports.is_dir():
                continue
            for f in reports.glob("*.html"):
                md = f.with_suffix(".md")
                self.assertTrue(md.is_file(), f"{f} 缺少同名 md 源稿")
            for f in reports.glob("*.md"):
                html = f.with_suffix(".html")
                self.assertTrue(html.is_file(), f"{f} 缺少同名 html 交付物")

    def test_no_legacy_report_files_in_topics(self):
        for b in _common.iter_business_dirs():
            reports = b.path / "reports"
            if not reports.is_dir():
                continue
            for f in reports.iterdir():
                if f.is_file() and self.LEGACY_RE.search(f.name):
                    self.fail(f"残留历史命名报告: {b.rel}/reports/{f.name}")


class TestHistoricalMigration(unittest.TestCase):
    """场景二：全量历史数据校验。

    - 迁移清单完整覆盖全部存量来源；
    - 每份来源的归一化全文作为子串出现在目标文件中（内容零丢失）；
    - 目标文件存在且非空。
    """

    MANIFEST = _common.ROOT / "src" / "report-audits" / "report-migration-2026-11.json"
    PATHS = _common.ROOT / "src" / "report-audits" / "report-migration-2026-11-paths.json"

    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(cls.MANIFEST.read_text(encoding="utf-8"))
        cls.results = cls.manifest["results"]
        cls.path_map = json.loads(cls.PATHS.read_text(encoding="utf-8"))
        # 含 .html 变体
        cls.path_map = {**cls.path_map, **{k[:-3] + ".html": v[:-3] + ".html"
                                           for k, v in cls.path_map.items()}}

    def test_manifest_covers_all_sources(self):
        missing = [r["target"] for r in self.results if not Path(r["target"]).is_file()]
        if missing:
            self.skipTest(f"目标报告已由 b42b25c 清空（{len(missing)} 份），待重新产出后恢复")
        self.assertGreaterEqual(len(self.results), 36)
        for r in self.results:
            self.assertTrue(r["content_preserved"], f"{r['source']} 内容未通过留存校验")
            self.assertTrue(Path(r["target"]).is_file(), f"目标文件缺失: {r['target']}")
            self.assertGreater(Path(r["target"]).stat().st_size, 0, f"目标文件为空: {r['target']}")

    def test_every_source_content_preserved_in_target(self):
        """用 git 历史取出旧文件，逐份校验归一化全文已收录进目标文件。"""
        if any(not Path(r["target"]).is_file() for r in self.results):
            self.skipTest("目标报告已由 b42b25c 清空，待重新产出后恢复")
        if not (_common.ROOT / ".git").exists():
            self.skipTest("非 git 仓库，跳过历史内容复核")
        checked = 0
        for r in self.results:
            old_rel = r["target"].rsplit("/reports/", 1)[0] + "/reports/" + r["source"]
            old_text = self._old_content(old_rel)
            if old_text is None:
                continue
            # 迁移后同步修正了报告内的旧路径引用；按同一映射归一化后再比对，
            # 确保「内容零丢失」判定不受路径改名影响。
            for old_path, new_path in self.path_map.items():
                old_text = old_text.replace(old_path, new_path)
            new_text = Path(r["target"]).read_text(encoding="utf-8")
            self.assertIn(
                _normalize(old_text),
                _normalize(new_text),
                f"{old_rel} 的内容未完整保留在 {r['target']}",
            )
            checked += 1
        if checked == 0:
            self.skipTest("git 历史不可用（浅克隆或旧文件不在历史中），跳过历史内容复核")

    @staticmethod
    def _old_content(old_rel: str):
        """从 git 历史中取出旧文件内容；不可用时返回 None。

        `git log -- <path>` 的最新一条可能是**删除**该文件的提交，
        故遍历历史提交，取第一个能成功取出内容的版本。
        """
        try:
            log = subprocess.run(
                ["git", "log", "--all", "--format=%H", "--", old_rel],
                capture_output=True, text=True, cwd=_common.ROOT, timeout=60,
            )
            if log.returncode != 0 or not log.stdout.strip():
                return None
            for rev in log.stdout.split():
                show = subprocess.run(
                    ["git", "show", f"{rev}:{old_rel}"],
                    capture_output=True, text=True, encoding="utf-8",
                    cwd=_common.ROOT, timeout=30,
                )
                if show.returncode == 0:
                    return show.stdout
            return None
        except (OSError, subprocess.SubprocessError):
            return None


# 报告路径引用在迁移中允许改名（旧命名 -> YYYY-MM-<slug>），
# 内容留存校验把 reports/ / handbook/ 之后的路径整体归一，聚焦实质文本比对。
# （2026-11-14 起知识手册拆分至 topics/<slug>/handbook/，跨主题引用允许指向
#  reports/ 或 handbook/，二者统一归一为 <PATH>。）
_DOC_PATH_RE = re.compile(r"(?:reports|handbook)/[^\s`\]\)|）,，、]*")


def _normalize(text: str) -> str:
    """内容留存归一化：去标题标记 / 归一文档路径 / 去空白。"""
    text = re.sub(r"(?m)^\s{0,3}#+\s?", "", text)
    text = _DOC_PATH_RE.sub("<PATH>", text)
    return re.sub(r"\s+", "", text)


class TestDiffAccuracy(unittest.TestCase):
    """场景三：跨月份对比准确性校验。"""

    def test_identical_reports_have_no_changes(self):
        html = "<body><h2>标题</h2><p>内容一致</p></body>"
        body, stats = render_diffed_body(html, html)
        self.assertEqual(stats["new"], 0)
        self.assertEqual(stats["mod"], 0)
        self.assertEqual(stats["del"], 0)
        self.assertGreater(stats["equal"], 0)

    def test_added_block_detected(self):
        prev = "<body><h2>标题</h2><p>旧段落</p></body>"
        curr = "<body><h2>标题</h2><p>旧段落</p><p>新增段落</p></body>"
        body, stats = render_diffed_body(curr, prev)
        self.assertEqual(stats["new"], 1)
        self.assertIn("已更新 · 新增", body)

    def test_modified_block_detected(self):
        prev = "<body><h2>标题</h2><p>旧文案</p></body>"
        curr = "<body><h2>标题</h2><p>旧文案改了一下</p></body>"
        body, stats = render_diffed_body(curr, prev)
        self.assertEqual(stats["mod"], 1)
        self.assertIn("已更新 · 修改", body)

    def test_deleted_block_grouped_and_collapsed(self):
        prev = "<body><h2>标题</h2><p>保留</p><p>被删的段落</p></body>"
        curr = "<body><h2>标题</h2><p>保留</p></body>"
        body, stats = render_diffed_body(curr, prev)
        self.assertEqual(stats["del"], 1)
        self.assertIn("diff-del-group", body)
        self.assertIn("已更新 · 删除", body)

    def test_dissimilar_replace_is_not_modification(self):
        """相似度低于阈值的替换应按「删除 + 新增」处理，不得判为修改。"""
        prev_blocks = extract_blocks("<body><p>" + "甲" * 40 + "</p></body>")
        curr_blocks = extract_blocks("<body><p>" + "乙" * 40 + "</p></body>")
        ops = diff_blocks(prev_blocks, curr_blocks)
        self.assertFalse(any(op == "mod" for op, _b, _o in ops))
        self.assertEqual(sum(1 for op, _b, _o in ops if op == "new"), 1)
        self.assertEqual(sum(1 for op, _b, _o in ops if op == "del"), 1)

    def test_similar_replace_is_modification(self):
        prev_blocks = extract_blocks("<body><p>日本特定技能司机缺口数据</p></body>")
        curr_blocks = extract_blocks("<body><p>日本特定技能司机缺口数据更新</p></body>")
        ops = diff_blocks(prev_blocks, curr_blocks)
        self.assertTrue(any(op == "mod" for op, _b, _o in ops))

    def test_similarity_threshold_value(self):
        self.assertGreater(MOD_SIMILARITY, 0.0)
        self.assertLessEqual(MOD_SIMILARITY, 1.0)

    def test_first_period_has_no_comparison(self):
        html = "<body><h2>首期</h2><p>内容</p></body>"
        body, stats = render_diffed_body(html, None)
        self.assertIsNone(stats["prev"])
        self.assertEqual(body, html)

    def test_strip_body(self):
        self.assertEqual(strip_body("<body><p>x</p></body>"), "<p>x</p>")
        self.assertEqual(strip_body("<p>x</p>"), "<p>x</p>")

    def test_report_page_embeds_diff_for_multi_month_topic(self):
        """多期主题（decision-hub）报告页应带对比摘要 / 高亮标记 / 工具条。"""
        md = _common.ROOT / "00-decision-hub" / "reports" / "2026-12-decision-hub.md"
        if not md.is_file():
            self.skipTest("decision-hub 报告源缺失")
        html = md2html_convert(md)
        self.assertIn("diff-bar", html)
        self.assertIn("与 2026-11 期对比", html)
        self.assertIn("diff-badge", html)
        self.assertIn('id="tg-diff"', html)
        self.assertIn('id="tg-del"', html)
        # 报告页跳转：返回主题 + 返回首页
        self.assertIn('href="../../index.html#topic-00-decision-hub"', html)
        self.assertIn('href="../../index.html"', html)


class TestDaysSinceLatest(unittest.TestCase):
    def test_none_when_empty(self):
        now = datetime(2026, 11, 13, tzinfo=timezone.utc)
        self.assertIsNone(days_since_latest(now, []))

    def test_days(self):
        now = datetime(2026, 11, 13, tzinfo=timezone.utc)
        records = [{"timestamp": "2026-11-10T00:00:00+00:00"}]
        self.assertEqual(days_since_latest(now, records), 3)

    def test_ignores_bad_timestamp(self):
        now = datetime(2026, 11, 13, tzinfo=timezone.utc)
        records = [{"timestamp": "not-a-date"}]
        self.assertIsNone(days_since_latest(now, records))

    def test_naive_treated_as_utc(self):
        now = datetime(2026, 11, 13, tzinfo=timezone.utc)
        records = [{"timestamp": "2026-11-12T00:00:00"}]
        self.assertEqual(days_since_latest(now, records), 1)


class TestInfoQualityCheck(unittest.TestCase):
    """信息质量全量评估与闭环修复（info_quality_check.py）。"""

    TOPIC_FILES = {
        "prompts/business-config.md": "# 示例主题 · 业务配置\n\n{{REGION}} / {{TOPIC}}\n",
        "data/demo_indicator_registry.md": (
            "# 示例主题 · 指标登记册\n\n## 核心指标\n\n"
            "| # | 指标 | 口径 | 研究阶段 | 最新值 / 规则 | 来源机构 | 来源 URL | 版本日期 | 核验日期 | 核验状态 | 关联章节 | 更新时间 |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| 1 | 测试指标 | 测试口径 | 测试 | 1 | 测试机构 | https://example.com | 2026-11-14 | 2026-11-14 | 已核验 | 2 | 2026-11-14 |\n"
        ),
        "operations-guide.md": "# 示例主题 · 操作指南\n\n## 适用范围\n\n测试。\n",
    }

    REPORT = (
        "# 示例主题 · 2026-11 月度报告\n\n"
        "> **版本**：v1.0（2026-11 月度）\n\n"
        "## 一、执行摘要\n\n"
        "结论先行：测试用段落，包含数字 2026。\n\n"
        "## 二、正文\n\n"
        "第一段实质内容，长度需要超过四十字符才能触发重复检测阈值，此处包含数字 123 用于测试。\n\n"
        "第一段实质内容，长度需要超过四十字符才能触发重复检测阈值，此处包含数字 123 用于测试。\n\n"
        "引用失效：[目标](../../03-missing/reports/target.md)。\n\n"
        "## 三、参考来源清单\n\n"
        "- [来源](https://example.com)\n"
    )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()  # noqa: P201
        self.root = Path(self._tmp.name)
        self._orig_common = _common.ROOT
        self._orig_iqc = info_quality_check.ROOT
        _common.ROOT = self.root
        info_quality_check.ROOT = self.root
        (self.root / "01-demo" / "prompts").mkdir(parents=True)
        (self.root / "01-demo" / "data").mkdir(parents=True)
        (self.root / "01-demo" / "reports").mkdir(parents=True)
        for rel, text in self.TOPIC_FILES.items():
            p = self.root / "01-demo" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        (self.root / "01-demo" / "reports" / "2026-11-demo.md").write_text(
            self.REPORT, encoding="utf-8")
        # 链接修复目标的唯一真实位置（02-other 补全必需要素，保证覆盖率门槛可达）
        (self.root / "02-other" / "prompts").mkdir(parents=True)
        (self.root / "02-other" / "data").mkdir(parents=True)
        (self.root / "02-other" / "reports").mkdir(parents=True)
        (self.root / "02-other" / "prompts" / "business-config.md").write_text(
            "# 其他主题 · 业务配置\n", encoding="utf-8")
        (self.root / "02-other" / "data" / "other_indicator_registry.md").write_text(
            "# 其他主题 · 指标登记册\n\n## 核心指标\n\n"
            "| # | 指标 | 口径 | 研究阶段 | 最新值 / 规则 | 来源机构 | 来源 URL | 版本日期 | 核验日期 | 核验状态 | 关联章节 | 更新时间 |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
            "| 1 | 测试指标 | 测试口径 | 测试 | 1 | 测试机构 | https://example.com | 2026-11-14 | 2026-11-14 | 已核验 | 2 | 2026-11-14 |\n", encoding="utf-8")
        (self.root / "02-other" / "operations-guide.md").write_text(
            "# 其他主题 · 操作指南\n", encoding="utf-8")
        (self.root / "02-other" / "reports" / "target.md").write_text(
            "# 目标\n", encoding="utf-8")

    def tearDown(self):
        _common.ROOT = self._orig_common
        info_quality_check.ROOT = self._orig_iqc
        self._tmp.cleanup()

    def _findings(self):
        units = scan_topics()
        return evaluate(units)

    def test_completeness_and_structure_findings(self):
        findings, metrics = self._findings()
        self.assertEqual(metrics.topics_total, 2)   # 01-demo + 02-other（后者缺必需要素）
        codes = {c for c, _ in {(f.code, f.level) for f in findings}}
        self.assertIn("C-06", codes)
        # 01-demo 缺免责声明 → P1
        self.assertTrue(any(
            f.code == "C-06" and f.level == "P1" and "免责声明" in f.detail
            for f in findings))

    def test_disclaimer_autofix_and_idempotent(self):
        findings, _ = self._findings()
        repairs = repair(findings, scan_topics())
        self.assertTrue(any(r.spec == "S-05" for r in repairs))
        text = (self.root / "01-demo" / "reports" / "2026-11-demo.md").read_text(encoding="utf-8")
        self.assertIn("不构成法律意见", text)
        # 复评：免责声明问题已消除
        after, _ = self._findings()
        self.assertFalse(any(
            f.code == "C-06" and "免责声明" in f.detail and f.status == "open"
            for f in after))
        # 幂等：再次修复无新增
        repairs2 = repair(after, scan_topics())
        self.assertFalse(any(r.spec == "S-05" for r in repairs2))

    def test_dedupe_within_file(self):
        findings, _ = self._findings()
        self.assertTrue(any(f.code == "C-03" and f.level == "P1" for f in findings))
        repair(findings, scan_topics())
        text = (self.root / "01-demo" / "reports" / "2026-11-demo.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("第一段实质内容"), 1)

    def test_broken_link_repointed(self):
        findings, _ = self._findings()
        self.assertTrue(any(f.code == "C-09" for f in findings))
        repairs = repair(findings, scan_topics())
        self.assertTrue(any(r.spec == "S-08" for r in repairs))
        text = (self.root / "01-demo" / "reports" / "2026-11-demo.md").read_text(encoding="utf-8")
        self.assertIn("../../02-other/reports/target.md", text)
        self.assertNotIn("03-missing", text)

    def test_verify_passes_after_repair(self):
        findings, before = self._findings()
        repairs = repair(findings, scan_topics())
        after_findings, after = self._findings()
        ver = verify(before, findings, after_findings, after, repairs)
        self.assertTrue(ver["passed"], ver["checks"])

    # ── 判定口径（与项目架构约定对齐）──

    def test_cross_doc_dup_only_for_reports(self):
        """prompts 共享模板句不计缺陷；reports 研究正文交叉重复才计。"""
        boiler = ("本段为共享模板说明，长度需超过一百二十字以触发跨文档重复检测阈值，"
                  "用于验证明自包含业务包内的模板句不被误报为缺陷；该句同时写入两个主题，"
                  "并在研究正文中重复出现，以区分「设计内模板复用」与「正文交叉重复」两类场景，"
                  "确保检测口径与项目架构约定一致，避免误报与漏报同时发生。")
        for topic in ("01-demo", "02-other"):
            p = self.root / topic / "prompts" / "business-config.md"
            p.write_text(p.read_text(encoding="utf-8") + "\n" + boiler + "\n", encoding="utf-8")
        findings, _ = self._findings()
        self.assertFalse(any(f.code == "C-03" and f.location == "跨文档重复" for f in findings))
        # 研究正文出现同样段落 → 应报跨文档重复
        for topic, name in (("01-demo", "2026-11-demo.md"), ("02-other", "target.md")):
            p = self.root / topic / "reports" / name
            p.write_text(p.read_text(encoding="utf-8") + "\n" + boiler + "\n", encoding="utf-8")
        findings, _ = self._findings()
        self.assertTrue(any(f.code == "C-03" and f.location == "跨文档重复" for f in findings))

    def test_source_annotation_forms(self):
        """五类来源标注形式均被认可。"""
        from info_quality_check import _has_source
        for text in ("见 https://example.com", "来源：机构", "[出入国在留管理庁]",
                     "详见登记册 #5", "手册 03 有口径"):
            self.assertTrue(_has_source(text), text)
        self.assertFalse(_has_source("这是一段普通的陈述，没有任何引用。"))

    def test_registry_snapshot_not_counted(self):
        """历史版本快照口径差异不触发 C-10；活值表口径差异才触发。"""
        findings, _ = self._findings()
        self.assertFalse(any(f.code == "C-10" for f in findings))
        reg = self.root / "02-other" / "data" / "other_indicator_registry.md"
        reg.write_text(reg.read_text(encoding="utf-8")
                       + "\n## 历史版本快照（v1.0）\n\n| # | 指标 | 最新值 / 规则（v1.0） | 核验状态 |\n"
                         "|---|---|---|---|\n| 1 | 测试指标 | 快照口径不同 | 复核中 |\n", encoding="utf-8")
        findings, _ = self._findings()
        self.assertFalse(any(f.code == "C-10" for f in findings))
        # 活值表口径改为不同 → 触发 C-10
        reg.write_text(reg.read_text(encoding="utf-8").replace("测试口径", "不同口径"), encoding="utf-8")
        findings, _ = self._findings()
        self.assertTrue(any(f.code == "C-10" for f in findings))

    def test_prompt_system_matches_tool(self):
        """体系文档与程序常量/口径一致（防止文档与实现漂移）。"""
        repo_root = Path(info_quality_check.__file__).resolve().parents[3]
        doc = repo_root / "docs" / "信息质量评估提示词体系.md"
        self.assertTrue(doc.exists(), f"缺少体系文档：{doc}")
        text = doc.read_text(encoding="utf-8")
        self.assertIn("v1.1", text)
        self.assertIn("仅研究正文", text)
        self.assertIn("五类", text)
        self.assertIn("核心指标", text)
        self.assertIn("事实段落来源标注覆盖率门槛", text)
        # 文档声明的来源覆盖率门槛须与程序常量一致
        self.assertEqual(info_quality_check.THRESH_SOURCE_COVERAGE, 0.20)
        self.assertIn("20%", text.split("事实段落来源标注覆盖率门槛")[1].split("\n")[0])


class TestAuditPreflight(unittest.TestCase):
    """落盘前快速自检（audit_preflight.py，左移预防层）。"""

    REL = "01-demo/reports/2026-11-demo.md"

    GOOD = (
        "# 示例主题 · 2026-11 月度报告\n\n"
        "> **版本**：v1.0　|　**数据基准日**：2026-11-01\n\n"
        "> **免责声明**：本报告不构成法律意见。\n\n"
        "## 一、核心结论\n\n"
        "结论：2026 年测试数据 123 条，来源为官方统计（https://example.com）。\n\n"
        "## 二、正文\n\n"
        "实质段落，含数字 456，来源：[机构](https://example.com)。口径：测试口径。\n\n"
        "## 三、后续观察\n\n"
        "- 观察项：无。\n\n"
        "## 四、参考来源清单\n\n"
        "- [来源](https://example.com)\n"
    )

    REG = (
        "# 示例主题 · 指标登记册\n\n## 核心指标\n\n"
        "| # | 指标 | 口径 |\n|---|---|---|\n"
        "| 1 | 测试指标 | 测试口径 |\n"
    )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()  # noqa: P201
        self.root = Path(self._tmp.name)
        self._orig_root = audit_preflight.ROOT
        audit_preflight.ROOT = self.root
        (self.root / "01-demo" / "reports").mkdir(parents=True)
        (self.root / "01-demo" / "reports" / "target.md").write_text("# 目标\n", encoding="utf-8")

    def tearDown(self):
        audit_preflight.ROOT = self._orig_root
        self._tmp.cleanup()

    def _codes(self, text, rel=None, **kw):
        return {f.code for f in audit_preflight.check_text(rel or self.REL, text, **kw)}

    def test_good_report_no_blocking_findings(self):
        # 无 HTML 时仅报 PF-PAIR（P2），其余要素齐全、无 P0/P1
        findings = audit_preflight.check_text(self.REL, self.GOOD)
        self.assertEqual({f.code for f in findings}, {"PF-PAIR"})
        self.assertFalse(any(f.severity in ("P0", "P1") for f in findings))

    def test_naming_slug_mismatch(self):
        codes = self._codes(self.GOOD, rel="01-demo/reports/2026-11-wrong.md")
        self.assertIn("PF-NAME", codes)

    def test_missing_elements(self):
        text = self.GOOD.replace("> **免责声明**：本报告不构成法律意见。\n\n", "")
        text = text.replace("## 一、核心结论", "## 一、引言")
        text = text.replace("## 四、参考来源清单", "## 四、附录")
        codes = self._codes(text)
        self.assertIn("PF-E3", codes)   # 免责声明
        self.assertIn("PF-E4", codes)   # 结论摘要
        self.assertIn("PF-E6", codes)   # 来源章节

    def test_missing_body_section(self):
        text = "# 标题\n\n> **免责声明**：无。\n\n结论。"
        self.assertIn("PF-E5", self._codes(text))

    def test_source_coverage(self):
        unsourced = ("实质段落含数字 789，长度超过四十字符以满足实质性阈值要求，"
                     "但没有任何出处说明，此处仅为测试用途，故不构成已标注事实段落。")
        text = ("# 标题\n\n> **免责声明**：无。\n\n## 一、核心结论\n\n结论。\n\n"
                "## 二、正文\n\n" + unsourced + "\n\n"
                "## 三、参考来源清单\n\n- [来源](https://example.com)\n")
        self.assertIn("PF-E7", self._codes(text))
        self.assertNotIn("PF-E7", self._codes(self.GOOD))

    def test_absolute_wording(self):
        text = self.GOOD + "\n本路线包过，稳过。\n"
        self.assertIn("PF-ABS", self._codes(text))

    def test_caliber_marker(self):
        text = self.GOOD.replace("口径：测试口径。", "").replace("数据基准日", "数据日期")
        self.assertIn("PF-CALIBER", self._codes(text))

    def test_broken_relative_link(self):
        text = self.GOOD + "\n引用失效：[目标](../../99-missing/target.md)。\n"
        self.assertIn("PF-CITE", self._codes(text))
        # 存在的相对引用不报
        text_ok = self.GOOD + "\n引用有效：[目标](target.md)。\n"
        self.assertNotIn("PF-CITE", self._codes(text_ok))

    def test_registry_pointer(self):
        text = self.GOOD + "\n详见登记册 #2。\n"
        self.assertIn("PF-REG", self._codes(text, registry_text=self.REG))
        text_ok = self.GOOD + "\n详见登记册 #1。\n"
        self.assertNotIn("PF-REG", self._codes(text_ok, registry_text=self.REG))
        # 区间指针：#1–#2 而登记册只有 #1
        text_range = self.GOOD + "\n详见登记册 #1–#2。\n"
        self.assertIn("PF-REG", self._codes(text_range, registry_text=self.REG))

    def test_missing_html_pair(self):
        self.assertIn("PF-PAIR", self._codes(self.GOOD))

    def test_check_report_reads_files(self):
        d = self.root / "01-demo" / "reports"
        (d / "2026-11-demo.md").write_text(self.GOOD, encoding="utf-8")
        findings = audit_preflight.check_report(self.REL)
        # 无 HTML → 仅 PF-PAIR；其余要素齐全
        self.assertEqual({f.code for f in findings}, {"PF-PAIR"})

    def test_severity_counts(self):
        fs = [audit_preflight.Finding("PF-X", "P1", "l", "d"),
              audit_preflight.Finding("PF-Y", "P2", "l", "d")]
        self.assertEqual(audit_preflight.severity_counts(fs),
                         {"P0": 0, "P1": 1, "P2": 1})

    def test_prompt_embeds_audit_entry(self):
        """通用基座与主题提示词须嵌入三步审计入口，且命令路径存在。"""
        repo_root = Path(audit_preflight.__file__).resolve().parents[3]
        tools = repo_root / "src" / "prompts-tools" / "tools"
        base = repo_root / "src" / "report_templates" / "prompt-generic-base.md"
        text = base.read_text(encoding="utf-8")
        for cmd in ("audit_preflight.py --report", "audit_check.py --report",
                    "audit_pipeline.py --submit"):
            self.assertIn(cmd, text)
            tool = cmd.split()[0]
            self.assertTrue((tools / tool).is_file(), f"命令指向的工具不存在：{tool}")
        # 4 个 prompt-update 同步嵌入
        for rel in ("01-ssw-driver", "02-career-driver", "03-career-management",
                    "07-economy-finance"):
            t = (repo_root / rel / "prompts" / "prompt-update.md").read_text(encoding="utf-8")
            self.assertIn("audit_pipeline.py --submit", t)
        # 操作指南覆盖（21 个主题）
        guides = list(repo_root.glob("*/operations-guide.md"))
        self.assertGreaterEqual(len(guides), 21)
        missing = [g.as_posix() for g in guides if "audit_preflight.py" not in g.read_text(encoding="utf-8")]
        self.assertEqual(missing, [], f"操作指南未嵌入审计入口：{missing}")


class TestAuditGuard(unittest.TestCase):
    """AuditGuard 契约：登记册双向一致 / 状态机 / 哈希链 / 指纹失效。"""

    REPORT_REL = "01-demo/reports/2026-11-demo.md"
    REPORT_TEXT = (
        "# 示例主题 · 2026-11 月度报告\n\n"
        "> **免责声明**：本报告不构成法律意见。\n\n"
        "## 一、核心结论\n\n结论。\n\n"
        "## 二、参考来源清单\n\n- [来源](https://example.com)\n"
    )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()  # noqa: P201
        self.root = Path(self._tmp.name)
        for sub in ("prompts", "data", "reports"):
            (self.root / "01-demo" / sub).mkdir(parents=True)
        (self.root / "01-demo" / "prompts" / "business-config.md").write_text(
            "# 示例主题 · 业务配置\n\n继承：[职业就业调研型](../../src/report_templates/employment-research/)\n",
            encoding="utf-8")
        self.md = self.root / "01-demo" / "reports" / "2026-11-demo.md"
        self.md.write_text(self.REPORT_TEXT, encoding="utf-8")
        self.audit_dir = self.root / "src" / "report-audits" / "audit"
        self.audit_dir.mkdir(parents=True)

        self._patches = [
            (_common, "ROOT", self.root),
            (audit_registry, "ROOT", self.root),
            (audit_registry, "AUDIT_DIR", self.audit_dir),
            (audit_registry, "REGISTRY_JSON", self.audit_dir / "report-registry.json"),
            (audit_registry, "REGISTRY_MD", self.audit_dir / "report-registry.md"),
            (audit_pipeline, "ROOT", self.root),
            (audit_pipeline, "AUDIT_DIR", self.audit_dir),
            (audit_pipeline, "LEDGER", self.audit_dir / "audit-ledger.jsonl"),
            (audit_pipeline, "STATUS", self.audit_dir / "audit-status.json"),
        ]
        self._saved = [(m, n, getattr(m, n)) for m, n, _ in self._patches]
        for m, n, v in self._patches:
            setattr(m, n, v)

    def tearDown(self):
        for m, n, v in self._saved:
            setattr(m, n, v)
        self._tmp.cleanup()

    def _state(self):
        return audit_pipeline.rebuild_status(audit_pipeline.load_ledger())

    def test_registry_build_and_check(self):
        entries = audit_registry.build()
        self.assertEqual(len(entries), 1)
        n, problems = audit_registry.check()
        self.assertEqual(n, 0)
        # 内容变更 → 指纹失配
        self.md.write_text(self.REPORT_TEXT + "\n追加内容\n", encoding="utf-8")
        n, problems = audit_registry.check()
        self.assertEqual(n, 1)
        self.assertIn("指纹失配", problems[0])
        # 未登记报告 → 遗漏
        (self.root / "01-demo" / "reports" / "2026-12-demo.md").write_text(
            "# 新报告\n", encoding="utf-8")
        n, problems = audit_registry.check()
        self.assertTrue(any("遗漏" in p for p in problems))

    def test_pipeline_state_machine_and_verify(self):
        audit_pipeline.cmd_init()
        self.assertEqual(self._state()[self.REPORT_REL]["state"], "registered")
        audit_pipeline.cmd_submit(None, True, "generator")
        self.assertEqual(self._state()[self.REPORT_REL]["state"], "pending_initial")
        audit_pipeline.cmd_review("initial", None, True, "pass", "", "", None)
        self.assertEqual(self._state()[self.REPORT_REL]["state"], "pending_re_review")
        audit_pipeline.cmd_review("re_review", None, True, "pass", "", "", None)
        self.assertEqual(self._state()[self.REPORT_REL]["state"], "pending_final")
        audit_pipeline.cmd_review("final", None, True, "pass", "", "", None)
        st = self._state()[self.REPORT_REL]
        self.assertEqual(st["state"], "audited")
        self.assertTrue(st["audit_id"].startswith("AUD-"))
        self.assertEqual(audit_pipeline.cmd_verify(), 0)

    def test_ledger_hash_chain_and_tamper(self):
        audit_pipeline.cmd_init()
        audit_pipeline.cmd_submit(None, True, "generator")
        ledger = audit_pipeline.load_ledger()
        self.assertGreaterEqual(len(ledger), 2)
        prev = "0" * 64
        for ev in ledger:
            body = {k: v for k, v in ev.items() if k not in ("seq", "prev_hash", "hash")}
            self.assertEqual(ev["prev_hash"], prev)
            self.assertEqual(audit_pipeline._hash(prev, body), ev["hash"])
            prev = ev["hash"]
        # 篡改末行 → 校验失败
        p = audit_pipeline.LEDGER
        lines = p.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[-1])
        rec["result"] = "fail"
        lines[-1] = json.dumps(rec, ensure_ascii=False)
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertNotEqual(audit_pipeline.cmd_verify(), 0)

    def test_fingerprint_mismatch_marks_stale(self):
        audit_pipeline.cmd_init()
        audit_pipeline.cmd_submit(None, True, "generator")
        for stage in ("initial", "re_review", "final"):
            audit_pipeline.cmd_review(stage, None, True, "pass", "", "", None)
        self.assertEqual(audit_pipeline.cmd_verify(), 0)
        self.md.write_text(self.REPORT_TEXT + "\n变更\n", encoding="utf-8")
        self.assertNotEqual(audit_pipeline.cmd_verify(), 0)
        audit_pipeline.cmd_sync()
        self.assertEqual(self._state()[self.REPORT_REL]["state"], "stale")


class TestNewOnlyGate(unittest.TestCase):
    """新报告阻断 / 历史报告豁免（lint_reports / compliance_check --new-only）。"""

    def test_lint_skip_rules(self):
        old = "01-demo/reports/2026-10-demo.html"
        new = "01-demo/reports/2026-11-demo.html"
        self.assertTrue(lint_reports._skip(old, True, set()))
        self.assertFalse(lint_reports._skip(new, True, set()))
        self.assertTrue(lint_reports._skip(new, True, {new}))
        self.assertFalse(lint_reports._skip(old, False, set()))

    def test_lint_whitelist_loader(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "w.json"
            p.write_text('{"items":[{"report":"a","reason":"r","review_by":"2026-12-01"}]}',
                         encoding="utf-8")
            self.assertEqual(lint_reports.load_whitelist(p), {"a"})
            self.assertEqual(lint_reports.load_whitelist(Path(d) / "missing.json"), set())

    def test_compliance_new_only_filters_old(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "01-demo" / "prompts").mkdir(parents=True)
            (root / "01-demo" / "reports").mkdir(parents=True)
            (root / "01-demo" / "prompts" / "business-config.md").write_text(
                "# 示例\n\n继承：[职业就业调研型](../../src/report_templates/employment-research/)\n",
                encoding="utf-8")
            html = "<html><title>t</title><body><h2>一、x</h2></body></html>"
            (root / "01-demo" / "reports" / "2026-10-demo.html").write_text(html, encoding="utf-8")
            (root / "01-demo" / "reports" / "2026-11-demo.html").write_text(html, encoding="utf-8")
            orig_common, orig_cc = _common.ROOT, compliance_check.ROOT
            _common.ROOT, compliance_check.ROOT = root, root
            try:
                _, _, lines = compliance_check.run_check(None, new_only=True)
                self.assertTrue(all("2026-10" not in l for l in lines))
                _, _, lines2 = compliance_check.run_check(
                    None, new_only=True, whitelist={"01-demo/reports/2026-11-demo.html"})
                self.assertTrue(any("SKIP" in l for l in lines2))
            finally:
                _common.ROOT, compliance_check.ROOT = orig_common, orig_cc


if __name__ == "__main__":
    unittest.main()
