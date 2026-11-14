"""prompts/tools 单元测试（CI: ci.yml / scheduled-maintenance 的 unittest 步骤）。

覆盖纯函数：报告名解析、周期解析与任务推导、期望输出名、
归档保留策略、lint 检查、活跃度天数计算。
运行：python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
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
from update_planner import build_tasks, default_period  # noqa: E402


class TestDetectReport(unittest.TestCase):
    def test_monthly(self):
        self.assertEqual(_common.detect_report("2026-11_monthly.html"), ("monthly", "2026-11", "html"))

    def test_quarterly(self):
        self.assertEqual(_common.detect_report("2026-Q3_quarterly.html"), ("quarterly", "2026-Q3", "html"))

    def test_annual(self):
        self.assertEqual(_common.detect_report("2026_annual.html"), ("annual", "2026", "html"))

    def test_baseline(self):
        self.assertEqual(
            _common.detect_report("2026-11_baseline_report.html"), ("baseline", "2026-11", "html")
        )
        self.assertEqual(_common.detect_report("2026-11_baseline.html"), ("baseline", "2026-11", "html"))

    def test_md_variant(self):
        self.assertEqual(_common.detect_report("2026-11_monthly.md"), ("monthly", "2026-11", "md"))

    def test_weekly(self):
        # 周报：period 为数据截止日（ISO 日期），与月 / 季 / 年日历周期不同
        self.assertEqual(_common.detect_report("2026-11-13_weekly.html"), ("weekly", "2026-11-13", "html"))
        self.assertEqual(_common.detect_report("2026-02-28_weekly.md"), ("weekly", "2026-02-28", "md"))
        self.assertIsNone(_common.detect_report("2026-13-01_weekly.html"))  # 非法月份
        self.assertIsNone(_common.detect_report("2026-11-13_weekly.txt"))  # 非法扩展名

    def test_non_report(self):
        self.assertIsNone(_common.detect_report("dubai_apartment_indicator_registry_2026-11.xlsx"))
        self.assertIsNone(_common.detect_report("2026-13_monthly.html"))  # 非法月份
        self.assertIsNone(_common.detect_report("random.html"))


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

    def test_quarter_period(self):
        self.assertEqual(_common.tasks_for_period("quarter", 2026, 4), [("quarterly", 2026, 4)])

    def test_year_period(self):
        self.assertEqual(_common.tasks_for_period("year", 2026, None), [("annual", 2026, None)])


class TestExpectedOutput(unittest.TestCase):
    def test_names(self):
        self.assertEqual(_common.expected_output("monthly", 2026, 11), "2026-11_monthly.html")
        self.assertEqual(_common.expected_output("quarterly", 2026, 1), "2026-Q1_quarterly.html")
        self.assertEqual(_common.expected_output("annual", 2026, None), "2026_annual.html")
        self.assertEqual(
            _common.expected_output("baseline", 2026, 11), "2026-11_baseline_report.html"
        )


class TestDefaultPeriod(unittest.TestCase):
    def test_plain_month(self):
        self.assertEqual(default_period(datetime(2026, 11, 13, tzinfo=timezone.utc)), "2026-11")

    def test_quarter_start_month(self):
        self.assertEqual(default_period(datetime(2026, 1, 1, tzinfo=timezone.utc)), "2026-Q1")
        self.assertEqual(default_period(datetime(2026, 10, 31, tzinfo=timezone.utc)), "2026-Q4")


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
            "99-demo", prompts=["prompt-monthly-monitor.md"], reports=["2026-11_monthly.html"]
        )
        tasks = build_tasks("2026-11", [biz])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["output"], "99-demo/reports/2026-11_monthly.html")
        self.assertEqual(tasks[0]["status"], "done")
        self.assertEqual(tasks[0]["cycle"], "monthly")
        self.assertTrue(tasks[0]["prompt"].endswith("prompt-monthly-monitor.md"))

    def test_pending_when_output_missing(self):
        biz = self._make_business("99-demo", prompts=["prompt-monthly-monitor.md"])
        tasks = build_tasks("2026-12", [biz])
        self.assertEqual(tasks[0]["output"], "99-demo/reports/2026-12_monthly.html")
        self.assertEqual(tasks[0]["status"], "pending")


class TestSelectArchives(unittest.TestCase):
    def _paths(self, names):
        return [Path(n) for n in names]

    def test_keep_newest(self):
        items = [
            ("monthly", f"2026-{m:02d}", p)
            for m, p in enumerate(self._paths([f"2026-{m:02d}_monthly.html" for m in range(1, 13)]), start=1)
        ]
        to_archive = select_archives(items, {"monthly": 12})
        self.assertEqual(to_archive, [], "恰好 12 期时不应归档")

    def test_archive_oldest(self):
        names = [f"2025-{m:02d}_monthly.html" for m in range(1, 13)] + ["2026-01_monthly.html"]
        items = [
            ("monthly", n.split("_")[0], p)
            for n, p in zip(names, self._paths(names))
        ]
        to_archive = select_archives(items, {"monthly": 12})
        # 13 期保留最新 12 期，归档最早 1 期（排序为 period 降序）
        self.assertEqual([p.name for p in to_archive], ["2025-01_monthly.html"])


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

    def test_detect_type_none(self):
        self.assertIsNone(detect_type("没有模板引用的配置"))

    def test_cycle_rule_inherits_baseline(self):
        rule, inherited = cycle_rule(self.rules, "competitive-intelligence", "quarterly")
        self.assertTrue(inherited)
        self.assertEqual(rule["sections"], self.rules["types"]["competitive-intelligence"]["cycles"]["baseline"]["sections"])

    def test_clean_cycle_report_passes(self):
        self.assertEqual(check_report(self._html(), self.monthly_rule, self.common), [])

    def test_missing_section_is_error(self):
        issues = check_report(self._html(sections=7), self.monthly_rule, self.common)
        self.assertTrue(any(i[0] == "E" and "结构不完整" in i[1] for i in issues))

    def test_extra_section_is_warning(self):
        issues = check_report(self._html(sections=10), self.monthly_rule, self.common)
        self.assertTrue(any(i[0] == "W" and "超出模板骨架" in i[1] for i in issues))
        self.assertFalse(any(i[0] == "E" for i in issues))

    def test_non_sequential_ids_is_error(self):
        issues = check_report(self._html(ids=False), self.monthly_rule, self.common)
        # 无 id 时不做编号检查（基线形态），此处应无编号错误
        self.assertFalse(any("编号不连续" in i[1] for i in issues))
        html = self._html().replace('id="s3"', 'id="sX"')
        issues = check_report(html, self.monthly_rule, self.common)
        self.assertTrue(any(i[0] == "E" and "编号不连续" in i[1] for i in issues))

    def test_missing_nav_cycle_is_error(self):
        issues = check_report(self._html(nav=False), self.monthly_rule, self.common)
        self.assertTrue(any(i[0] == "E" and "顶部导航" in i[1] for i in issues))

    def test_missing_nav_baseline_is_warning(self):
        issues = check_report(self._html(nav=False), self.baseline_rule, self.common)
        self.assertTrue(any(i[0] == "W" and "缺少简化锚点导航" in i[1] for i in issues))

    def test_missing_disclaimer_is_error(self):
        issues = check_report(self._html(disclaimer=False), self.monthly_rule, self.common)
        self.assertTrue(any(i[0] == "E" and "不构成投资建议" in i[1] for i in issues))

    def test_missing_title_is_error(self):
        issues = check_report(self._html(title=""), self.monthly_rule, self.common)
        self.assertTrue(any(i[0] == "E" and "title" in i[1] for i in issues))

    def test_broken_anchor_is_error(self):
        issues = check_report(self._html(extra_anchor=True), self.monthly_rule, self.common)
        self.assertTrue(any(i[0] == "E" and "断头锚点" in i[1] for i in issues))

    def test_in_page_anchor_with_extra_id_resolves(self):
        html = self._html(extra_anchor=True, extra_id="missing-anchor")
        self.assertEqual(check_report(html, self.monthly_rule, self.common), [])


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
            "reports/2026-11_baseline_report.md",
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
        self.assertIn("v1.23", registry)


class TestExitTransitionReturnVocabulary(unittest.TestCase):
    """16-exit-transition-return 词汇库接入校验。"""

    def test_vocab_topic_registered_and_bound(self):
        config_path = _common.ROOT / "src" / "vocabulary" / "config" / "topics.json"
        sync_path = _common.ROOT / "src" / "vocabulary" / "config" / "sync.json"
        terms_path = _common.ROOT / "src" / "vocabulary" / "data" / "exit-transition-return" / "terms.md"
        index_path = _common.ROOT / "src" / "vocabulary" / "INDEX.md"

        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        self.assertIn("exit-transition-return", config["topics"])
        self.assertEqual(config["topics"]["exit-transition-return"]["id_prefix"], "ETR")

        sync = json.loads(sync_path.read_text(encoding="utf-8-sig"))
        binding = next(b for b in sync["bindings"] if b["topic"] == "exit-transition-return")
        self.assertTrue(binding["targets"])
        self.assertIn("16-exit-transition-return/prompts/business-config.md", binding["targets"][0]["path"])

        self.assertTrue(terms_path.is_file())
        terms = terms_path.read_text(encoding="utf-8")
        self.assertIn("退職", terms)
        self.assertIn("健康保険任意継続", terms)
        self.assertIn("再入国許可", terms)
        self.assertIn("ETR-", terms)
        self.assertIn("exit-transition-return", index_path.read_text(encoding="utf-8"))

    def test_vocab_sync_block_present(self):
        config = (_common.ROOT / "16-exit-transition-return" / "prompts" / "business-config.md").read_text(encoding="utf-8")
        self.assertIn("<!-- VOCAB-SYNC:BEGIN topic=exit-transition-return", config)
        self.assertIn("<!-- VOCAB-SYNC:END -->", config)
        self.assertIn("## 词汇速览：退出·转型·回国（词汇库自动同步）", config)


class TestExitTransitionReturnRegistry(unittest.TestCase):
    """16-exit-transition-return 指标登记册校验。"""

    def test_registry_covers_three_stages_and_required_fields(self):
        path = _common.ROOT / "16-exit-transition-return" / "data" / "exit_transition_return_indicator_registry.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")

        for value in (
            "退職",
            "雇用保険",
            "健康保険任意継続",
            "厚生年金脱退一时金",
            "在留資格取消",
            "特定活動",
            "特定技能2号",
            "特定技能 1 号",
            "転職",
            "帰国前確定申告",
            "再入国許可",
            "みなし再入国",
            "退室",
            "研究边界档案",
            "观察项与触发器状态",
            "v1.0",
        ):
            self.assertIn(value, text)

        rows = [line for line in text.splitlines() if line.startswith("| ") and line.count("|") >= 5]
        self.assertGreaterEqual(len(rows), 20)
        self.assertIn("⚠ 待核实", text)


class TestExitTransitionReturnReports(unittest.TestCase):
    """16-exit-transition-return 基线与初析报告内容契约。"""

    BASELINE = _common.ROOT / "16-exit-transition-return" / "reports" / "2026-11_baseline_report.md"
    INITIAL = _common.ROOT / "16-exit-transition-return" / "reports" / "2026-11-14_initial_analysis_report.md"

    def test_baseline_has_nine_sections_and_three_stages(self):
        self.assertTrue(self.BASELINE.is_file())
        text = self.BASELINE.read_text(encoding="utf-8")
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
            "退出",
            "转型",
            "回国",
            "退職",
            "健康保険任意継続",
            "厚生年金脱退一时金",
            "在留資格取消",
            "特定活動",
            "特定技能2号",
            "帰国前確定申告",
            "再入国許可",
            "みなし再入国",
            "退室",
            "免责声明",
            "不构成投资建议",
            "⚠ 待核实",
            "（事实）",
            "（推断）",
        ):
            self.assertIn(value, text)

    def test_initial_analysis_is_framework_companion(self):
        self.assertTrue(self.INITIAL.is_file())
        text = self.INITIAL.read_text(encoding="utf-8")
        for heading in (
            "一、主题核心概述",
            "二、关键维度拆解",
            "三、当前现状梳理",
            "四、初步结论",
            "五、后续观察方向",
        ):
            self.assertIn(heading, text)
        for value in (
            "退出",
            "转型",
            "回国",
            "免责声明",
            "不构成投资建议",
            "⚠ 待核实",
        ):
            self.assertIn(value, text)

    def test_registry_updated_with_baseline_values(self):
        registry = (_common.ROOT / "16-exit-transition-return" / "data" / "exit_transition_return_indicator_registry.md").read_text(encoding="utf-8")
        self.assertIn("v2026.11.14_1", registry)
        self.assertIn("⚠ 待核实", registry)
        self.assertIn("2026-11-14", registry)


class TestExitTransitionReturnHtml(unittest.TestCase):
    """16-exit-transition-return HTML 交付物校验。"""

    BASELINE = _common.ROOT / "16-exit-transition-return" / "reports" / "2026-11_baseline_report.html"
    INITIAL = _common.ROOT / "16-exit-transition-return" / "reports" / "2026-11-14_initial_analysis_report.html"

    def test_html_reports_exist_and_pass_lint(self):
        for path in (self.BASELINE, self.INITIAL):
            self.assertTrue(path.is_file())
            text = path.read_text(encoding="utf-8")
            self.assertIn("<title>", text)
            self.assertIn("免责声明", text)
            self.assertIn("不构成投资建议", text)
            self.assertIn('<nav aria-label="报告导航">', text)
            self.assertIn('id="s1"', text)
            self.assertEqual([i for i in lint_html(text) if i[0] == "E"], [])

    def test_html_reports_use_fixed_tables(self):
        for path in (self.BASELINE, self.INITIAL):
            text = path.read_text(encoding="utf-8")
            self.assertIn('class="fixed"', text)


class TestExitTransitionReturnIntegration(unittest.TestCase):
    """16-exit-transition-return 与 00 决策枢纽、根索引的集成校验。"""

    def test_decision_hub_references_topic(self):
        path = _common.ROOT / "00-decision-hub" / "data" / "decision_hub_registry.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("16-exit-transition-return", text)
        self.assertIn("退出·转型·回国", text)
        self.assertIn("已建 16", text)
        self.assertIn("具体金额 / 期限 / 要件待核验", text)

    def test_root_index_includes_topic(self):
        path = _common.ROOT / "index.html"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("16-exit-transition-return", text)
        self.assertIn("退出·转型·回国", text)
        self.assertIn("2026-11_baseline_report.html", text)


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

    def test_normalize_noop_without_timestamp(self):
        text = "<html><body><h1>报告</h1></body></html>"
        self.assertEqual(normalize_for_check(text), text)

    def test_committed_index_matches_regen_ignoring_timestamp(self):
        # 真实仓库状态回归：已提交 index.html 与重算内容仅时间戳不同时应判为最新。
        # build_hub 设计允许汇总页尚未生成（全新克隆由定时维护首建），此时前提不成立，跳过。
        if not (_common.ROOT / "index.html").exists():
            self.skipTest("根目录 index.html 尚未生成（build_hub 首建前）")
        committed = (_common.ROOT / "index.html").read_text(encoding="utf-8", errors="replace")
        self.assertEqual(
            normalize_for_check(committed),
            normalize_for_check(build_outputs()["index.html"]),
            "报告清单未变时，已提交 index.html 归一化后应与重算内容一致",
        )


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
