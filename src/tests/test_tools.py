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
from archive_reports import select_archives  # noqa: E402
from automation_status import days_since_latest  # noqa: E402
from build_hub import build_outputs, normalize_for_check  # noqa: E402
from compliance_check import check_report, cycle_rule, detect_type, load_rules  # noqa: E402
from lint_reports import lint_html  # noqa: E402
from report_diff import (  # noqa: E402
    MOD_SIMILARITY,
    diff_blocks,
    extract_blocks,
    render_diffed_body,
    strip_body,
)
from update_planner import build_tasks, default_period, target_month  # noqa: E402


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
            "<h2>免责声明</h2><p>本报告仅供参考，不构成投资建议或决策依据。</p>"
            "</body></html>"
        )
        errors = [i for i in lint_html(text) if i[0] == "E"]
        self.assertEqual(errors, [])

    def test_duplicate_tbody_close(self):
        text = (
            "<table><thead><tr><th>A</th></tr></thead>"
            "<tbody><tr><td>1</td></tr></tbody></tbody></table>"
            "<p>本报告仅供参考。</p>"
        )
        issues = lint_html(text)
        self.assertTrue(any(i[0] == "E" and "</tbody>" in i[1] for i in issues))

    def test_malformed_th(self):
        text = '<table><thead><tr><th scope="col"ead>A</th></tr></thead></table><p>本报告仅供参考。</p>'
        issues = lint_html(text)
        self.assertTrue(any("畸形" in i[1] for i in issues))

    def test_missing_disclaimer(self):
        text = "<table><thead><tr><th>A</th></tr></thead><tbody><tr><td>1</td></tr></tbody></table>"
        issues = lint_html(text)
        self.assertTrue(any(i[0] == "E" and "免责声明" in i[1] for i in issues))

    def test_wide_table_missing_width(self):
        ths = "".join(f"<th>列{i}</th>" for i in range(8))
        text = (
            f"<table><thead><tr>{ths}</tr></thead><tbody><tr><td>1</td></tr></tbody></table>"
            "<p>本报告仅供参考。</p>"
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
        cls.baseline_rule, _ = cycle_rule(cls.rules, "market-monitoring", "baseline")

    @staticmethod
    def _html(sections=9, nav=True, ids=True, title="测试报告", disclaimer=True,
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
        if disclaimer:
            parts.append("<p>免责声明：本报告仅供参考，不构成投资建议或决策依据。</p>")
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

    def test_missing_disclaimer_is_error(self):
        issues = check_report(self._html(disclaimer=False), self.monthly_rule, self.common)
        self.assertTrue(any(i[0] == "E" and "不构成投资建议" in i[1] for i in issues))

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
    """16-exit-transition-return 月度报告内容契约（首月合并版）。"""

    MERGED = _common.ROOT / "16-exit-transition-return" / "reports" / "2026-11-exit-transition-return.md"

    def test_merged_report_contains_framework_and_baseline(self):
        self.assertTrue(self.MERGED.is_file())
        text = self.MERGED.read_text(encoding="utf-8")
        # 初析（主体）五节
        for heading in (
            "一、主题核心概述",
            "二、关键维度拆解",
            "三、当前现状梳理",
            "四、初步结论",
            "五、后续观察方向",
        ):
            self.assertIn(heading, text)
        # 基线（附录）九节
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
            "在留資格取消", "特定活動", "特定技能2号", "帰国前確定申告", "再入国許可",
            "みなし再入国", "退室", "免责声明", "不构成投资建议", "⚠ 待核实",
            "（事实）", "（推断）", "附录说明",
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

    def test_html_report_passes_lint(self):
        self.assertTrue(self.MERGED.is_file())
        text = self.MERGED.read_text(encoding="utf-8")
        self.assertIn("<title>", text)
        self.assertIn("免责声明", text)
        self.assertIn("不构成投资建议", text)
        self.assertIn('<nav aria-label="报告导航">', text)
        self.assertIn('id="s1"', text)
        self.assertEqual([i for i in lint_html(text) if i[0] == "E"], [])
        self.assertRegex(text, r'<a[^>]+href="https?://[^"]+"')
        self.assertIn('class="fixed"', text)

    def test_html_anchors_resolve(self):
        text = self.MERGED.read_text(encoding="utf-8")
        nav = re.search(r'<nav aria-label="报告导航">(.*?)</nav>', text, re.S)
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
        # 索引报告链接已改为阅读器路由（主题 + 月份）
        self.assertIn("reader.html#topic=exit-transition-return&month=2026-11", text)


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

    def test_reader_embeds_all_topics_and_months(self):
        outputs = build_outputs()
        self.assertIn("reader.html", outputs)
        m = re.search(
            r'<script id="report-data" type="application/json">(.*?)</script>',
            outputs["reader.html"],
            re.S,
        )
        self.assertIsNotNone(m)
        data = json.loads(m.group(1))
        self.assertGreaterEqual(len(data), 15)
        # 每个主题至少一期，且 body 非空
        for rs, t in data.items():
            self.assertTrue(t["months"], rs)
            for period, rec in t["months"].items():
                self.assertTrue(rec["body"], f"{rs}/{period}")


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
        self.assertGreaterEqual(len(self.results), 36)
        for r in self.results:
            self.assertTrue(r["content_preserved"], f"{r['source']} 内容未通过留存校验")
            self.assertTrue(Path(r["target"]).is_file(), f"目标文件缺失: {r['target']}")
            self.assertGreater(Path(r["target"]).stat().st_size, 0, f"目标文件为空: {r['target']}")

    def test_every_source_content_preserved_in_target(self):
        """用 git 历史取出旧文件，逐份校验归一化全文已收录进目标文件。"""
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
        self.assertGreater(checked, 0, "应至少复核到一份历史来源")

    @staticmethod
    def _old_content(old_rel: str):
        """从 git 历史中取出旧文件内容；不可用时返回 None。"""
        try:
            log = subprocess.run(
                ["git", "log", "--all", "--format=%H", "-1", "--", old_rel],
                capture_output=True, text=True, cwd=_common.ROOT, timeout=30,
            )
            if log.returncode != 0 or not log.stdout.strip():
                return None
            rev = log.stdout.strip().splitlines()[0]
            show = subprocess.run(
                ["git", "show", f"{rev}:{old_rel}"],
                capture_output=True, text=True, encoding="utf-8", cwd=_common.ROOT, timeout=30,
            )
            return show.stdout if show.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None


# 报告路径引用在迁移中允许改名（旧命名 -> YYYY-MM-<slug>），
# 内容留存校验把 reports/ 之后的路径整体归一，聚焦实质文本比对。
_REPORT_PATH_RE = re.compile(r"reports/[^\s`\]\)|）,，、]*")


def _normalize(text: str) -> str:
    """内容留存归一化：去标题标记 / 归一报告路径 / 去空白。"""
    text = re.sub(r"(?m)^\s{0,3}#+\s?", "", text)
    text = _REPORT_PATH_RE.sub("reports/<PATH>", text)
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

    def test_reader_diff_data_present_for_multi_month_topic(self):
        """多期主题（ssw-driver）在阅读器数据中应带对比摘要与高亮标记。"""
        outputs = build_outputs()
        m = re.search(
            r'<script id="report-data" type="application/json">(.*?)</script>',
            outputs["reader.html"],
            re.S,
        )
        data = json.loads(m.group(1))
        months = data["ssw-driver"]["months"]
        self.assertIn("2026-11", months)
        self.assertIn("2026-12", months)
        self.assertIn("与 2026-11 期对比", months["2026-12"]["summary"])
        self.assertIn("diff-badge", months["2026-12"]["body"])


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


if __name__ == "__main__":
    unittest.main()
