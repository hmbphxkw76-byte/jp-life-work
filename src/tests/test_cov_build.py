"""生成类工具链补充单元测试（覆盖率补齐）。

只读被测源码 + tempfile / unittest.mock，不改动仓库真实文件、不联网。
覆盖 build_hub / md2html / skeleton_builder / build_index /
archive_reports / incremental_build / generate_registry / report_diff
中此前未覆盖的纯函数与 CLI 分支。
"""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "prompts-tools" / "tools"))

import _common  # noqa: E402
import archive_reports  # noqa: E402
import build_hub  # noqa: E402
import build_index  # noqa: E402
import generate_registry  # noqa: E402
import incremental_build  # noqa: E402
import md2html  # noqa: E402
import report_diff  # noqa: E402
import skeleton_builder  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(argv, func):
    """以指定 argv 调用 CLI main()，返回 (返回码, stdout)。"""
    buf = io.StringIO()
    with mock.patch("sys.argv", argv), contextlib.redirect_stdout(buf):
        rc = func()
    return rc, buf.getvalue()


# ──────────────────────────────────────────────
# build_hub.py
# ──────────────────────────────────────────────

class TestCovBuildHub(unittest.TestCase):
    def test_classify_month_report(self):
        self.assertEqual(
            build_hub.classify_month_report("2026-11-ssw-driver.html"),
            ("2026-11", "ssw-driver", "2026-11-30"),
        )
        # 2026 非闰年，2 月月末 28 日
        self.assertEqual(build_hub.classify_month_report("2026-02-x.html")[2], "2026-02-28")
        self.assertIsNone(build_hub.classify_month_report("README.md"))
        self.assertIsNone(build_hub.classify_month_report("2026-13-x.html"))

    def test_load_topic_registry(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "topics.json"
            with mock.patch.object(build_hub, "TOPIC_REGISTRY", p):
                self.assertEqual(build_hub.load_topic_registry(), {})
                _write(p, "{ not json")
                self.assertEqual(build_hub.load_topic_registry(), {})
                _write(p, json.dumps({"topics": ["not", "dict"]}))
                self.assertEqual(build_hub.load_topic_registry(), {})
                _write(p, json.dumps({"topics": {"demo": {"name": "演示"}}}))
                self.assertEqual(build_hub.load_topic_registry(), {"demo": {"name": "演示"}})

    def test_load_type_labels_fallback_and_parse(self):
        with tempfile.TemporaryDirectory() as d:
            tmpl = Path(d)
            with mock.patch.object(build_hub, "TEMPLATE_ROOT", tmpl):
                labels = build_hub.load_type_labels()
                self.assertEqual(labels["policy-analysis"], "政策法规解读型")
                _write(tmpl / "template-registry.md",
                       "## 二、已注册类型清单\n\n| id | 名称 |\n|---|---|\n"
                       "| policy-analysis | 自定义名 |\n| foo-bar | 测试类型 |\n\n## 三、其他\n")
                labels = build_hub.load_type_labels()
                self.assertEqual(labels["policy-analysis"], "自定义名")
                self.assertEqual(labels["foo-bar"], "测试类型")
                # 回退表仍保留
                self.assertEqual(labels["market-monitoring"], "市场指标监测型")

    def test_fallback_name_and_topic_type(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "01-demo" / "prompts" / "business-config.md",
                   "# 演示主题 · 业务专属配置\n\nsrc/report_templates/policy-analysis/\n")
            b = _common.Business("01-demo")
            with mock.patch.object(_common, "ROOT", root):
                self.assertEqual(build_hub._fallback_name(b), "演示主题")
                self.assertEqual(build_hub._topic_type(b), "policy-analysis")
            # 缺失配置回退
            with mock.patch.object(_common, "ROOT", root):
                b2 = _common.Business("99-none")
                self.assertEqual(build_hub._fallback_name(b2), "99-none")
                self.assertEqual(build_hub._topic_type(b2), "")

    def test_collect_topic_sorts_and_marks_latest(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "01-demo" / "prompts" / "business-config.md",
                   "# 演示主题\n\nsrc/report_templates/policy-analysis/\n")
            _write(root / "01-demo" / "reports" / "2026-10-demo.html", "<title>十月</title>")
            _write(root / "01-demo" / "reports" / "2026-11-demo.html", "<title>十一月</title>")
            _write(root / "01-demo" / "reports" / "2026-11-other.html", "<title>其他</title>")
            _write(root / "01-demo" / "reports" / "notes.md", "x")
            b = _common.Business("01-demo")
            registry = {"demo": {"name": "演示", "description": "描述"}}
            with mock.patch.object(_common, "ROOT", root):
                t = build_hub.collect_topic(b, registry, {"policy-analysis": "政策法规解读型"})
            self.assertEqual(t["slug"], "01-demo")
            self.assertEqual(t["rs"], "demo")
            self.assertEqual(t["num"], "01")
            self.assertEqual(t["name"], "演示")
            self.assertEqual(t["desc"], "描述")
            self.assertEqual(t["type_label"], "政策法规解读型")
            self.assertEqual([r["period"] for r in t["reports"]], ["2026-11", "2026-10"])
            self.assertTrue(t["reports"][0]["is_latest"])
            self.assertFalse(t["reports"][1]["is_latest"])
            self.assertEqual(t["reports"][0]["path"], "01-demo/reports/2026-11-demo.html")
            self.assertEqual(t["reports"][0]["title"], "十一月")

    def test_collect_topics_skips_empty_and_sorts(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "02-b" / "prompts" / "business-config.md", "# B\n")
            # 01-a 既无报告也无配置 -> 跳过
            (root / "01-a").mkdir(parents=True)
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(build_hub, "iter_business_dirs",
                                      lambda: [_common.Business("02-b"), _common.Business("01-a")]), \
                    mock.patch.object(build_hub, "load_topic_registry", lambda: {}), \
                    mock.patch.object(build_hub, "load_type_labels", lambda: {}):
                topics = build_hub.collect_topics()
            self.assertEqual([t["slug"] for t in topics], ["02-b"])

    def test_md_text_and_headings(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "01-demo" / "reports" / "2026-11-demo.md",
                   "## 甲 `*乙*`\n## 丙\n# 丁\n")
            with mock.patch.object(build_hub, "ROOT", root):
                self.assertEqual(build_hub._md_text("01-demo/reports/2026-11-demo.md"),
                                 "## 甲 `*乙*`\n## 丙\n# 丁\n")
                self.assertEqual(build_hub._md_text("missing.md"), "")
                self.assertEqual(build_hub._md_headings("## 甲 `*乙*`\n## 丙\n# 丁\n"),
                                 ["甲 乙", "丙"])

    def test_report_keywords(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "01-demo" / "reports" / "2026-11-demo.md",
                   "## 章节一\n\n关键词：甲, 乙\n\n正文含词条A与别名B。\n")
            vocab = [("词条A", "01-demo", ""), ("长词条", "01-demo", "别名B"), ("未出现", "x", "")]
            with mock.patch.object(build_hub, "ROOT", root):
                kws = build_hub._report_keywords(
                    "01-demo/reports/2026-11-demo.md", "演示", "政策法规解读型",
                    "2026-11", vocab, extra=["额外语"])
            for k in ["演示", "政策法规解读型", "2026-11", "章节一", "甲", "乙",
                      "词条A", "别名B", "额外语"]:
                self.assertIn(k, kws)
            self.assertNotIn("未出现", kws)
            self.assertLessEqual(len(kws), 24)

    def test_load_keywords_and_five_questions(self):
        with tempfile.TemporaryDirectory() as d:
            kd = Path(d) / "keywords.json"
            fq = Path(d) / "five.json"
            with mock.patch.object(build_hub, "KEYWORDS_PATH", kd), \
                    mock.patch.object(build_hub, "FIVEQ_PATH", fq):
                self.assertEqual(build_hub.load_keywords(), {})
                self.assertEqual(build_hub.load_five_questions(), [])
                _write(kd, "{ bad")
                _write(fq, json.dumps({"questions": {"x": 1}}))
                self.assertEqual(build_hub.load_keywords(), {})
                self.assertEqual(build_hub.load_five_questions(), [])
                _write(kd, json.dumps({"topics": {"demo": ["甲"]}}))
                _write(fq, json.dumps({"questions": [{"label": "去不去"}]}))
                self.assertEqual(build_hub.load_keywords(), {"demo": ["甲"]})
                self.assertEqual(build_hub.load_five_questions(), [{"label": "去不去"}])

    def test_collect_search_index_attaches_questions(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            search = root / "search"
            _write(search / "question-index.json",
                   json.dumps({"questions": [
                       {"q": "问题一", "path": "01-demo/reports/2026-11-demo.html",
                        "anchor": "a", "group": "g"},
                       {"q": "", "path": "01-demo/reports/2026-11-demo.html"},
                   ]}))
            _write(root / "01-demo" / "reports" / "2026-11-demo.md", "## 章节\n内容\n")
            topics = [{"slug": "01-demo", "rs": "demo", "name": "演示",
                       "type": "policy-analysis", "type_label": "政策法规解读型",
                       "reports": [{"title": "十一月", "period": "2026-11",
                                    "path": "01-demo/reports/2026-11-demo.html",
                                    "is_latest": True}]}]
            with mock.patch.object(build_hub, "ROOT", root), \
                    mock.patch.object(build_hub, "SEARCH_DIR", search), \
                    mock.patch.object(build_hub, "KEYWORDS_PATH", search / "keywords.json"), \
                    mock.patch.object(build_hub, "FIVEQ_PATH", search / "five.json"):
                idx = build_hub.collect_search_index(topics)
            self.assertEqual(idx["version"], 2)
            self.assertEqual(idx["reports"][0]["questions"], ["问题一"])
            self.assertEqual(len(idx["questions"]), 1)
            self.assertEqual(idx["questions"][0]["anchor"], "a")

    def test_embed_json_escapes(self):
        out = build_hub.embed_json({"x": "</script><script>alert(1)</script>"})
        self.assertIn("\\u003c", out)
        self.assertNotIn("</script>", out)

    def test_render_topic_card_and_detail(self):
        topic = {"slug": "01-demo", "num": "01", "name": "演示", "desc": "描述",
                 "type": "policy-analysis", "type_label": "政策法规解读型",
                 "reports": [{"title": "十一月", "period": "2026-11",
                              "path": "01-demo/reports/2026-11-demo.html", "is_latest": True}]}
        card = build_hub.render_topic_card(topic)
        self.assertIn("tcard", card)
        self.assertIn("最新报告", card)
        self.assertIn('data-type="policy-analysis"', card)
        detail = build_hub.render_topic_detail(topic)
        self.assertIn('id="topic-01-demo"', detail)
        self.assertIn('class="rnew"', detail)
        empty = dict(topic, reports=[])
        self.assertIn("is-empty", build_hub.render_topic_card(empty))
        self.assertIn("empty-note", build_hub.render_topic_detail(empty))

    def test_render_sidebar_chips_and_five(self):
        topics = [
            {"slug": "01-demo", "num": "01", "name": "演示", "type": "policy-analysis",
             "type_label": "政策法规解读型", "reports": []},
            {"slug": "02-x", "num": "02", "name": "乙", "type": "industry-research",
             "type_label": "行业深度研究型", "reports": []},
        ]
        sidebar = build_hub.render_sidebar(topics)
        self.assertIn("#topic-01-demo", sidebar)
        chips = build_hub.render_type_chips(topics)
        self.assertIn("全部类型", chips)
        self.assertIn('data-type="industry-research"', chips)
        self.assertEqual(chips.count("data-type"), 3)  # all + 2 类型
        self.assertEqual(build_hub.render_five_questions([]), "")
        five = build_hub.render_five_questions(
            [{"label": "去不去", "judgment": "可去", "basis": "依据", "confidence": "高",
              "todo": "无", "links": ["https://example.com"]}])
        self.assertIn("fq-card", five)
        self.assertIn("可去", five)

    def test_compare_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            outputs = {"index.html": "X", "search-index.json": "Y"}
            with mock.patch.object(build_hub, "ROOT", root):
                self.assertEqual(build_hub.compare_outputs(outputs), ([], ["index.html", "search-index.json"]))
                (root / "index.html").write_text("X", encoding="utf-8")
                self.assertEqual(build_hub.compare_outputs(outputs), ([], ["search-index.json"]))
                (root / "index.html").write_text("Z", encoding="utf-8")
                stale, missing = build_hub.compare_outputs(outputs)
                self.assertEqual(stale, ["index.html"])
                self.assertEqual(missing, ["search-index.json"])

    def test_main_check_and_generate(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            outputs = {"index.html": "X", "search-index.json": "Y"}
            with mock.patch.object(build_hub, "ROOT", root), \
                    mock.patch.object(build_hub, "build_outputs", lambda: outputs):
                rc, out = _run(["build_hub.py", "--check"], build_hub.main)
                self.assertEqual(rc, 0)
                self.assertIn("尚未生成", out)
                _write(root / "index.html", "X")
                _write(root / "search-index.json", "Y")
                rc, out = _run(["build_hub.py", "--check"], build_hub.main)
                self.assertEqual(rc, 0)
                self.assertIn("校验通过", out)
                _write(root / "index.html", "STALE")
                rc, out = _run(["build_hub.py", "--check"], build_hub.main)
                self.assertEqual(rc, 1)
                self.assertIn("已过期", out)
                # 生成模式
                rc, out = _run(["build_hub.py"], build_hub.main)
                self.assertEqual(rc, 0)
                self.assertTrue((root / "index.html").exists())
                self.assertIn("已生成", out)
                # 写入失败
                with mock.patch.object(build_hub, "atomic_write",
                                       side_effect=OSError("disk full")):
                    rc, out = _run(["build_hub.py"], build_hub.main)
                self.assertEqual(rc, 1)
                self.assertIn("写入汇总页失败", out)


# ──────────────────────────────────────────────
# md2html.py
# ──────────────────────────────────────────────

class TestCovMd2Html(unittest.TestCase):
    def test_slug_with_width_and_tables(self):
        self.assertEqual(md2html._slug("<h2>日本 <code>特定技能</code>·司机</h2>"),
                         "日本-特定技能司机")
        self.assertIn("width:30%", md2html._with_width("<th>x</th>", 30))
        self.assertEqual(md2html._with_width('<th style="width:10%">x</th>', 30),
                         '<th style="width:10%">x</th>')
        self.assertIn("width:30%", md2html._with_width('<th style="color:red">x</th>', 30))
        fixed = md2html._fix_tables("<table><tr><th>A</th><th>B</th></tr></table>")
        self.assertIn('class="fixed"', fixed)
        self.assertEqual(fixed.count("width:50%"), 2)
        once = md2html._fix_tables('<table class="fixed"><tr><th>A</th></tr></table>')
        self.assertEqual(once.count('class="fixed"'), 1)
        no_th = md2html._fix_tables("<table><tr><td>A</td></tr></table>")
        self.assertNotIn("width:", no_th)

    def test_fix_headings_and_anchors(self):
        html = "<h1>T</h1><h2>甲</h2><p>x</p><h2>乙</h2>"
        out = md2html._fix_headings(html)
        self.assertIn('aria-label="报告导航"', out)
        self.assertIn('href="#s1"', out)
        self.assertIn('href="#s2"', out)
        self.assertEqual(md2html._fix_headings("<h1>T</h1>"), "<h1>T</h1>")
        # 已有 id 的 h2 被重编号
        numbered = md2html._fix_headings('<h2 id="x">甲</h2><h2 id="y">乙</h2>')
        self.assertIn('id="s1"', numbered)
        self.assertIn('id="s2"', numbered)
        anchored = md2html._fix_heading_anchors("<h2>日本 特定技能</h2><h2>日本 特定技能</h2>")
        self.assertIn('id="日本-特定技能"', anchored)
        self.assertIn('id="日本-特定技能-1"', anchored)

    def test_parse_meta_truncates(self):
        bq = ("<blockquote><p><strong>版本</strong>：v0.1<br>"
              "<strong>数据基准日</strong>：2026-11-14</p></blockquote>")
        lines = md2html._parse_meta(bq)
        self.assertIn("<b>版本</b>：v0.1", lines)
        self.assertIn("<b>数据基准日</b>：2026-11-14", lines)
        long_bq = "<blockquote><p>摘要：" + "字" * 200 + "</p></blockquote>"
        out = md2html._parse_meta(long_bq)[0]
        self.assertIn("…", out)
        self.assertLess(len(out), 200)

    def test_split_body(self):
        body = ('<h1>标题</h1><blockquote><p><strong>版本</strong>：v0.1</p></blockquote>'
                '<p>前言</p><h2 id="x">甲</h2><p>a</p><h2 id="y">乙</h2><p>b</p>')
        h1, bq, pre, sections = md2html._split_body(body)
        self.assertIn("标题", h1)
        self.assertIn("版本", bq)
        self.assertIn("前言", pre)
        self.assertEqual(len(sections), 2)
        self.assertIn('class="sec"', sections[0])
        self.assertIn('id="s1"', sections[0])
        h1b, bqb, preb, secb = md2html._split_body("<h1>T</h1><p>x</p>")
        self.assertEqual(secb, [])
        self.assertIn("x", preb)

    def test_extract_audit_badge(self):
        body = "<p><strong>已审计</strong> ✅ 2026-11-14 通过</p><p>x</p>"
        new, text = md2html._extract_audit_badge(body)
        self.assertEqual(text, "2026-11-14 通过")
        self.assertEqual(new, "<p>x</p>")
        same, empty = md2html._extract_audit_badge("<p>x</p>")
        self.assertEqual(same, "<p>x</p>")
        self.assertEqual(empty, "")

    def test_topic_meta_and_prev_md(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "01-demo" / "prompts" / "business-config.md",
                   "# 演示 · 业务专属配置\n\nsrc/report_templates/policy-analysis/\n")
            name, label = md2html._topic_meta(root / "01-demo")
            self.assertEqual(name, "演示")
            self.assertEqual(label, "政策法规解读型")
            name2, label2 = md2html._topic_meta(root / "99-none")
            self.assertEqual(name2, "99-none")
            self.assertEqual(label2, "")
            rd = root / "01-demo" / "reports"
            for n in ("2026-11-x.md", "2026-10-x.md", "2026-09-x.md", "2026-11-y.md"):
                _write(rd / n, "# x\n")
            self.assertEqual(md2html._prev_md(rd / "2026-11-x.md"), rd / "2026-10-x.md")
            self.assertIsNone(md2html._prev_md(rd / "not-a-report.md"))

    def test_back_url(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            md = root / "01-demo" / "reports" / "2026-11-demo.md"
            with mock.patch.object(md2html, "ROOT", root):
                self.assertEqual(md2html._back_url(md, "01-demo"),
                                 "../../index.html#topic-01-demo")

    def test_render_page_with_diff_and_audit(self):
        base = dict(title="标题<>&", topic_name="演示", type_label="政策法规解读型",
                    period="2026-11", rel_path="01-demo/reports/2026-11-demo.html",
                    blockquote="<blockquote><p><strong>版本</strong>：v0.1</p></blockquote>",
                    sections=["<h2 class=\"sec\" id=\"s1\">甲</h2><p>a</p>"],
                    back_url="../../index.html#topic-01-demo")
        page = md2html.render_page(**base)
        self.assertIn("skip-link", page)
        self.assertIn("标题&lt;&gt;&amp;", page)
        self.assertNotIn('class="diff-bar"', page)
        self.assertNotIn('id="tg-diff"', page)
        page2 = md2html.render_page(**base, audit="2026-11-14",
                                    diff=(["<p>x</p>"],
                                          {"new": 1, "mod": 0, "del": 0, "equal": 0, "prev": 2},
                                          "2026-10"))
        self.assertIn("audit-badge", page2)
        self.assertIn('class="diff-bar"', page2)
        self.assertIn("与 2026-10 期对比", page2)

    def test_convert_single_and_with_prev(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "01-demo" / "prompts" / "business-config.md",
                   "# 演示主题\n\nsrc/report_templates/policy-analysis/\n")
            md = root / "01-demo" / "reports" / "2026-11-demo.md"
            _write(md, "# 演示月度报告\n\n> **版本**：v0.1\n\n## 一、核心结论\n\n甲\n\n## 二、趋势\n\n乙\n")
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(md2html, "ROOT", root):
                html = md2html.convert(md)
                self.assertIn("演示月度报告", html)
                self.assertIn('01-demo/reports/2026-11-demo.html', html)
                self.assertIn("../../index.html#topic-01-demo", html)
                self.assertNotIn('class="diff-bar"', html)
                self.assertNotIn('id="tg-diff"', html)
                prev = root / "01-demo" / "reports" / "2026-10-demo.md"
                _write(prev, "# 演示月度报告\n\n> **版本**：v0.1\n\n## 一、核心结论\n\n旧内容\n\n## 二、趋势\n\n乙\n")
                html2 = md2html.convert(md)
                self.assertIn('class="diff-bar"', html2)
                self.assertIn("与 2026-10 期对比", html2)

    def test_collect_md_reports(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "01-demo" / "reports" / "2026-11-demo.md", "# x\n")
            _write(root / "02-x" / "reports" / "2026-10-x.md", "# y\n")
            _write(root / "01-demo" / "reports" / "notes.md", "n")
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(md2html, "iter_business_dirs",
                                      lambda: [_common.Business("01-demo"), _common.Business("02-x")]):
                out = md2html.collect_md_reports()
            self.assertEqual([p.name for p in out],
                             ["2026-11-demo.md", "notes.md", "2026-10-x.md"])

    def test_main_branches(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            md = root / "01-demo" / "reports" / "2026-11-demo.md"
            _write(md, "# x\n")
            with mock.patch.object(md2html, "ROOT", root):
                with mock.patch.object(md2html, "collect_md_reports", lambda: []):
                    rc, out = _run(["md2html.py"], md2html.main)
                    self.assertEqual(rc, 0)
                    self.assertIn("无 md 报告源", out)
                with mock.patch.object(md2html, "collect_md_reports", lambda: [md]), \
                        mock.patch.object(md2html, "convert", side_effect=RuntimeError("boom")):
                    rc, out = _run(["md2html.py"], md2html.main)
                    self.assertEqual(rc, 1)
                    self.assertIn("转换失败", out)
                with mock.patch.object(md2html, "collect_md_reports", lambda: [md]), \
                        mock.patch.object(md2html, "convert", lambda p: "<html>x</html>"):
                    rc, out = _run(["md2html.py"], md2html.main)
                    self.assertEqual(rc, 0)
                    self.assertEqual(md.with_suffix(".html").read_text(encoding="utf-8"),
                                     "<html>x</html>")
                # --changed：命中变更
                with mock.patch.object(md2html, "collect_md_reports", lambda: [md]), \
                        mock.patch.object(incremental_build, "changed_reports",
                                          lambda base: ["01-demo/reports/2026-11-demo.md"]), \
                        mock.patch.object(md2html, "convert", lambda p: "<html>y</html>"):
                    rc, out = _run(["md2html.py", "--changed"], md2html.main)
                    self.assertEqual(rc, 0)
                    self.assertEqual(md.with_suffix(".html").read_text(encoding="utf-8"),
                                     "<html>y</html>")
                # --changed：无变更
                with mock.patch.object(md2html, "collect_md_reports", lambda: [md]), \
                        mock.patch.object(incremental_build, "changed_reports", lambda base: []):
                    rc, out = _run(["md2html.py", "--changed"], md2html.main)
                    self.assertEqual(rc, 0)
                    self.assertIn("无变更报告", out)


# ──────────────────────────────────────────────
# skeleton_builder.py
# ──────────────────────────────────────────────

class TestCovSkeletonBuilder(unittest.TestCase):
    CFG = ("# 演示主题\n\nsrc/report_templates/policy-analysis/\n\n"
           "**含**：\n- 甲事项\n- 乙事项\n\n"
           "**不含**\n| 主题 | 说明 |\n|---|---|\n| 丙 | 不含丙 |\n\n"
           "## 口径清单\n\n| 口径 | 指标 | 说明 |\n|---|---|---|\n| 甲 | 乙 | 丙 |\n\n- 口径丁\n")

    def test_extract_boundary(self):
        inc, exc, cal = skeleton_builder._extract_boundary(self.CFG)
        self.assertEqual(inc, ["甲事项", "乙事项"])
        self.assertEqual(exc, ["丙 → 不含丙"])
        self.assertIn("甲 ≠ 乙", cal)
        self.assertIn("口径丁", cal)

    def test_extract_sections_and_type(self):
        cfg = "结构固化锚\n| 现行章节 | 说明 |\n|---|---|\n| 甲章 | x |\n| 乙章 | y |\n"
        self.assertEqual(skeleton_builder._extract_sections(cfg), ["甲章", "乙章"])
        self.assertEqual(skeleton_builder._extract_sections("无锚"),
                         list(skeleton_builder.DEFAULT_SECTIONS))
        self.assertEqual(skeleton_builder._extract_type(self.CFG), "policy-analysis")
        self.assertEqual(skeleton_builder._extract_type("无引用"), "")

    def test_section_helper(self):
        self.assertIn("口径丁", skeleton_builder._section(self.CFG, "口径"))
        self.assertEqual(skeleton_builder._section(self.CFG, "不存在"), "")

    def _topic(self, root):
        _write(root / "01-demo" / "prompts" / "business-config.md", self.CFG)
        return _common.Business("01-demo")

    def test_build_skeleton_full_compact_default_period(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            b = self._topic(root)
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(skeleton_builder, "_find_topic", lambda t: b):
                full = skeleton_builder.build_skeleton("01-demo", "full", "2026-11")
                self.assertIn("# 演示主题 · 2026-11 月度报告（骨架）", full)
                self.assertIn("## 一、核心结论（摘要）", full)
                self.assertIn("- 甲事项", full)
                self.assertIn("- 丙 → 不含丙", full)
                self.assertIn("主题类型**：policy-analysis", full)
                compact = skeleton_builder.build_skeleton("01-demo", "compact", "2026-11")
                self.assertIn("## 待补模块（合并）", compact)
                self.assertIn("- 二、行业与政策发展趋势（待补）", compact)
            with mock.patch.object(skeleton_builder, "_find_topic", lambda t: None):
                with self.assertRaises(SystemExit):
                    skeleton_builder.build_skeleton("nope")

    def test_build_skeleton_default_period_uses_today(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            b = self._topic(root)
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(skeleton_builder, "_find_topic", lambda t: b), \
                    mock.patch.object(skeleton_builder, "date") as fake:
                fake.today.return_value = date(2026, 12, 1)
                out = skeleton_builder.build_skeleton("01-demo", "compact", "")
            self.assertIn("2026-12 月度报告", out)

    def test_merge_empty_modules_extra(self):
        text, n = skeleton_builder.merge_empty_modules("# T\n\n内容\n")
        self.assertEqual(n, 0)
        self.assertEqual(text, "# T\n\n内容\n")
        new, n = skeleton_builder.merge_empty_modules("## 甲\n\n## 乙\n\n## 丙\n\n内容\n")
        self.assertEqual(n, 1)
        self.assertIn("甲 等 2 节", new)
        new2, n2 = skeleton_builder.merge_empty_modules("## 甲\n\n## 乙\n\n尾部\n")
        self.assertEqual(n2, 0)
        self.assertIn("尾部", new2)

    def test_main_merge_and_build(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / "r.md"
            _write(p, "# T\n\n## 一、空\n\n## 二、空\n\n## 三、有\n\n内容\n")
            rc, out = _run(["skeleton_builder.py", "--merge", str(p)], skeleton_builder.main)
            self.assertEqual(rc, 0)
            self.assertIn("可合并空模块 1 节", out)
            rc, out = _run(["skeleton_builder.py", "--merge", str(p), "--apply"],
                           skeleton_builder.main)
            self.assertEqual(rc, 0)
            self.assertIn("已合并空模块 1 节", out)
            self.assertIn("待补模块（合并）", p.read_text(encoding="utf-8"))
            rc, out = _run(["skeleton_builder.py", "--merge", str(root / "nope.md")],
                           skeleton_builder.main)
            self.assertEqual(rc, 1)
            self.assertIn("文件不存在", out)
            # build --out
            b = self._topic(root)
            out_file = root / "out" / "skeleton.md"
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(skeleton_builder, "_find_topic", lambda t: b):
                rc, out = _run(["skeleton_builder.py", "--topic", "01-demo",
                                "--mode", "compact", "--out", str(out_file)],
                               skeleton_builder.main)
            self.assertEqual(rc, 0)
            self.assertTrue(out_file.exists())
            self.assertIn("骨架已生成", out)
            with mock.patch.object(skeleton_builder, "_find_topic", lambda t: None):
                rc, out = _run(["skeleton_builder.py", "--topic", "nope"],
                               skeleton_builder.main)
            self.assertEqual(rc, 1)
            self.assertIn("未找到主题", out)


# ──────────────────────────────────────────────
# build_index.py
# ──────────────────────────────────────────────

class TestCovBuildIndex(unittest.TestCase):
    def test_render_index_empty_and_grouped(self):
        self.assertIn("暂无已产出报告。", build_index.render_index([], "2026-11-01 00:00 UTC"))
        m = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
        entries = [
            ("01-demo", "2026-11", "01-demo/reports/2026-11-demo.html", "十一月", m),
            ("01-demo", "2026-10", "01-demo/reports/2026-10-demo.html", "十月", m),
            ("02-x", "2026-11", "02-x/reports/2026-11-x.html", "乙", m),
        ]
        text = build_index.render_index(entries, "2026-11-01 00:00 UTC")
        self.assertIn("## 01-demo", text)
        self.assertIn("## 02-x", text)
        self.assertIn("[2026-11-demo.html](01-demo/reports/2026-11-demo.html)", text)
        self.assertIn("2026-11-01 12:00", text)

    def test_collect_entries(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "01-demo" / "reports" / "2026-11-demo.html", "<title>演示</title>")
            _write(root / "01-demo" / "reports" / "notes.md", "x")
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(build_index, "iter_business_dirs",
                                      lambda: [_common.Business("01-demo")]):
                entries = build_index.collect_entries()
            self.assertEqual(len(entries), 1)
            rel, period, path, title, _mtime = entries[0]
            self.assertEqual((rel, period, path, title),
                             ("01-demo", "2026-11", "01-demo/reports/2026-11-demo.html", "演示"))

    def test_main_check_and_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "01-demo" / "reports" / "2026-11-demo.html", "<title>演示</title>")
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(build_index, "ROOT", root), \
                    mock.patch.object(build_index, "iter_business_dirs",
                                      lambda: [_common.Business("01-demo")]):
                rc, out = _run(["build_index.py", "--check"], build_index.main)
                self.assertEqual(rc, 2)
                self.assertIn("不存在", out)
                rc, out = _run(["build_index.py"], build_index.main)
                self.assertEqual(rc, 0)
                self.assertTrue((root / "INDEX.md").exists())
                rc, out = _run(["build_index.py", "--check"], build_index.main)
                self.assertEqual(rc, 0)
                self.assertIn("一致", out)
                _write(root / "INDEX.md", "# 过期\n")
                rc, out = _run(["build_index.py", "--check"], build_index.main)
                self.assertEqual(rc, 1)
                self.assertIn("已过期", out)

    def test_main_write_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "INDEX.md").mkdir()
            with mock.patch.object(build_index, "ROOT", root), \
                    mock.patch.object(build_index, "iter_business_dirs", lambda: []):
                rc, out = _run(["build_index.py"], build_index.main)
            self.assertEqual(rc, 1)
            self.assertIn("写入 INDEX.md 失败", out)


# ──────────────────────────────────────────────
# archive_reports.py
# ──────────────────────────────────────────────

class TestCovArchiveReports(unittest.TestCase):
    def test_select_archives_tie_and_fewer(self):
        items = [("2026-11", Path("b.html")), ("2026-11", Path("a.html")),
                 ("2026-10", Path("c.html"))]
        self.assertEqual([p.name for p in archive_reports.select_archives(items, keep=2)],
                         ["c.html"])
        self.assertEqual(archive_reports.select_archives(items[:2], keep=12), [])

    def _make_reports(self, root):
        rd = root / "01-demo" / "reports"
        for i in range(1, 13):
            _write(rd / f"2025-{i:02d}-demo.html", "<html></html>")
        _write(rd / "2026-01-demo.html", "<html></html>")
        _write(rd / "2025-01-demo.md", "# oldest")
        return rd

    def test_main_moves_and_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rd = self._make_reports(root)
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(archive_reports, "iter_business_dirs",
                                      lambda: [_common.Business("01-demo")]):
                rc, out = _run(["archive_reports.py"], archive_reports.main)
                self.assertEqual(rc, 0)
                self.assertIn("归档完成", out)
                rc2, out2 = _run(["archive_reports.py"], archive_reports.main)
                self.assertEqual(rc2, 0)
                self.assertIn("无超出", out2)
            arch = rd / "archives"
            self.assertTrue((arch / "2025-01-demo.html").exists())
            self.assertTrue((arch / "2025-01-demo.md").exists())
            self.assertFalse((rd / "2025-01-demo.html").exists())
            self.assertEqual(len(list(rd.glob("*.html"))), 12)

    def test_main_move_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._make_reports(root)
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(archive_reports, "iter_business_dirs",
                                      lambda: [_common.Business("01-demo")]), \
                    mock.patch.object(archive_reports.shutil, "move",
                                      side_effect=OSError("locked")):
                rc, out = _run(["archive_reports.py"], archive_reports.main)
            self.assertEqual(rc, 1)
            self.assertIn("归档失败", out)


# ──────────────────────────────────────────────
# incremental_build.py
# ──────────────────────────────────────────────

class TestCovIncrementalBuild(unittest.TestCase):
    def test_changed_reports_filters_and_dedupes(self):
        stdout = ("01-x/reports/2026-11-x.md\n"
                  "README.md\n"
                  "01-x/reports/notes.txt\n"
                  "01-x/reports/2026-11-x.md\n"
                  "02-y\\reports\\2026-10-y.md\n"
                  "01-x/reports/2026-13-z.md\n")
        with mock.patch.object(incremental_build.subprocess, "run",
                               return_value=mock.Mock(stdout=stdout)):
            self.assertEqual(
                incremental_build.changed_reports("HEAD"),
                ["01-x/reports/2026-11-x.md", "02-y/reports/2026-10-y.md"],
            )

    def test_changed_reports_subprocess_error(self):
        with mock.patch.object(incremental_build.subprocess, "run",
                               side_effect=subprocess.CalledProcessError(1, "git")):
            self.assertEqual(incremental_build.changed_reports("HEAD"), [])

    def test_all_reports(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(root / "01-x" / "reports" / "2026-11-x.md", "# x\n")
            _write(root / "01-x" / "reports" / "2026-10-x.md", "# y\n")
            _write(root / "01-x" / "reports" / "notes.md", "n")
            with mock.patch.object(_common, "ROOT", root), \
                    mock.patch.object(incremental_build, "iter_business_dirs",
                                      lambda: [_common.Business("01-x")]):
                self.assertEqual(incremental_build.all_reports(),
                                 ["01-x/reports/2026-10-x.md", "01-x/reports/2026-11-x.md"])

    def test_convert_uses_atomic_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = "01-x/reports/2026-11-x.md"
            with mock.patch.object(incremental_build, "ROOT", root), \
                    mock.patch.object(incremental_build, "atomic_write") as aw, \
                    mock.patch.object(md2html, "convert", lambda p: "HTML"):
                incremental_build._convert(rel)
            aw.assert_called_once_with(root / "01-x" / "reports" / "2026-11-x.html", "HTML")

    def test_main_no_changes_dry_run_and_bench(self):
        with mock.patch.object(incremental_build, "changed_reports", lambda base: []):
            rc, out = _run(["incremental_build.py"], incremental_build.main)
            self.assertEqual(rc, 0)
            self.assertIn("无变更报告", out)
        rels = ["01-x/reports/2026-11-x.md"]
        with mock.patch.object(incremental_build, "changed_reports", lambda base: rels), \
                mock.patch.object(incremental_build, "_convert") as conv:
            rc, out = _run(["incremental_build.py", "--dry-run"], incremental_build.main)
            self.assertEqual(rc, 0)
            conv.assert_not_called()
            self.assertIn("变更报告 1 份", out)
        with mock.patch.object(incremental_build, "changed_reports", lambda base: rels), \
                mock.patch.object(incremental_build, "_convert") as conv:
            rc, out = _run(["incremental_build.py"], incremental_build.main)
            self.assertEqual(rc, 0)
            conv.assert_called_once()
            self.assertIn("已增量生成 1 份", out)
        with mock.patch.object(incremental_build, "changed_reports", lambda base: rels), \
                mock.patch.object(incremental_build, "all_reports", lambda: rels + ["b.md"]), \
                mock.patch.object(incremental_build, "_convert"):
            rc, out = _run(["incremental_build.py", "--bench"], incremental_build.main)
            self.assertEqual(rc, 0)
            data = json.loads(out.strip().splitlines()[-1])
            self.assertIn("incremental_sec", data)
            self.assertIn("full_sec", data)
            self.assertEqual(data["changed"], 1)


# ──────────────────────────────────────────────
# generate_registry.py
# ──────────────────────────────────────────────

class TestCovGenerateRegistry(unittest.TestCase):
    def _seed(self, root: Path):
        tools = root / "src" / "prompts-tools" / "tools"
        _write(tools / "_common.py", "")
        _write(tools / "b.py", "")
        _write(tools / "a.py", "")
        _write(root / "src" / "report_templates" / "compliance-rules.json",
               json.dumps({"types": {"policy-analysis": {}, "industry-research": {}}}))
        (root / "02-x").mkdir(parents=True, exist_ok=True)
        (root / "01-demo").mkdir(parents=True, exist_ok=True)
        _write(root / ".github" / "workflows" / "y.yml", "")
        _write(root / ".github" / "workflows" / "x.yml", "")
        return tools

    def test_counts_and_render_snapshot(self):
        reg = {"tools": ["a"], "types": ["t"], "topics": ["p"], "workflows": ["w"]}
        self.assertEqual(generate_registry.counts(reg), "工具 1 · 类型 1 · 主题 1 · 工作流 1")
        snap = generate_registry.render_snapshot(reg)
        self.assertTrue(snap.startswith(generate_registry.BEGIN))
        self.assertIn(generate_registry.END, snap)
        self.assertIn("工具 1", snap)

    def test_scan_hermetic(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tools = self._seed(root)
            with mock.patch.object(generate_registry, "ROOT", root), \
                    mock.patch.object(generate_registry, "TOOLS_DIR", tools):
                reg = generate_registry.scan()
            self.assertEqual(reg["version"], 1)
            self.assertEqual(reg["tools"], ["a.py", "b.py"])
            self.assertEqual(reg["types"], ["industry-research", "policy-analysis"])
            self.assertEqual(reg["topics"], ["01-demo", "02-x"])
            self.assertEqual(reg["workflows"], ["x.yml", "y.yml"])

    def test_check_missing_mismatch_and_ok(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tools = self._seed(root)
            reg_json = tools / "registry.json"
            readme = tools / "README.md"
            _write(readme, "<!-- REGISTRY:BEGIN -->\nold\n<!-- REGISTRY:END -->\n")
            with mock.patch.object(generate_registry, "ROOT", root), \
                    mock.patch.object(generate_registry, "TOOLS_DIR", tools), \
                    mock.patch.object(generate_registry, "REGISTRY_JSON", reg_json), \
                    mock.patch.object(generate_registry, "README", readme):
                rc, out = _run(["generate_registry.py", "--check"], generate_registry.main)
                self.assertEqual(rc, 1)
                self.assertIn("缺少 registry.json", out)
                reg = generate_registry.scan()
                _write(reg_json, json.dumps({**reg, "tools": ["wrong.py"]}))
                rc, out = _run(["generate_registry.py", "--check"], generate_registry.main)
                self.assertEqual(rc, 1)
                self.assertIn("tools 不一致", out)
                _write(readme, "无标记\n")
                rc, out = _run(["generate_registry.py", "--check"], generate_registry.main)
                self.assertEqual(rc, 1)
                self.assertIn("缺少注册表标记区间", out)
                _write(reg_json, json.dumps(reg, ensure_ascii=False))
                _write(readme, "头\n" + generate_registry.render_snapshot(reg) + "\n尾\n")
                rc, out = _run(["generate_registry.py", "--check"], generate_registry.main)
                self.assertEqual(rc, 0)
                self.assertIn("注册表一致", out)

    def test_write_creates_and_replaces(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tools = self._seed(root)
            reg_json = tools / "registry.json"
            readme = tools / "README.md"
            _write(readme, "# 工具表\n\n正文\n")
            with mock.patch.object(generate_registry, "ROOT", root), \
                    mock.patch.object(generate_registry, "TOOLS_DIR", tools), \
                    mock.patch.object(generate_registry, "REGISTRY_JSON", reg_json), \
                    mock.patch.object(generate_registry, "README", readme):
                rc, out = _run(["generate_registry.py", "--write"], generate_registry.main)
                self.assertEqual(rc, 0)
                self.assertTrue(reg_json.exists())
                text = readme.read_text(encoding="utf-8")
                self.assertIn(generate_registry.BEGIN, text)
                self.assertIn("工具 2", text)
                # 再次 write：替换标记区间而非追加
                rc, out = _run(["generate_registry.py", "--write"], generate_registry.main)
                self.assertEqual(rc, 0)
                self.assertEqual(readme.read_text(encoding="utf-8").count(generate_registry.BEGIN), 1)

    def test_main_default_is_check(self):
        with mock.patch.object(generate_registry, "check", return_value=0) as chk:
            rc, _ = _run(["generate_registry.py"], generate_registry.main)
        self.assertEqual(rc, 0)
        chk.assert_called_once()


# ──────────────────────────────────────────────
# report_diff.py
# ──────────────────────────────────────────────

class TestCovReportDiff(unittest.TestCase):
    def test_extract_blocks_kinds(self):
        html = ("<body><h2>标题</h2><p>段落</p><ul><li>项</li></ul>"
                "<table><tr><td>x</td></tr></table><pre>代码</pre><hr>"
                "<div><strong>粗</strong>文本</div>裸文本</body>")
        blocks = report_diff.extract_blocks(html)
        tags = {b.tag for b in blocks}
        self.assertIn("h2", tags)
        self.assertIn("p", tags)
        self.assertIn("li", tags)
        self.assertIn("table", tags)
        self.assertIn("pre", tags)
        self.assertIn("hr", tags)
        self.assertIn("strong", tags)
        self.assertIn("#text", tags)
        tbl = next(b for b in blocks if b.tag == "table")
        self.assertIn("x", tbl.text)

    def test_mark_branches(self):
        li = report_diff._mark("<li>x</li>", "li", "new")
        self.assertIn('class="diff-new"', li)
        self.assertIn("已更新 · 新增", li)
        tr = report_diff._mark("<tr><td>x</td></tr>", "tr", "mod")
        self.assertIn('class="diff-mod"', tr)
        self.assertIn("已更新 · 修改", tr)
        self.assertEqual(report_diff._mark("<hr>", "hr", "new"), "<hr>")
        p = report_diff._mark("<p>x</p>", "p", "del")
        self.assertIn('class="diff-block diff-del"', p)
        self.assertIn("已更新 · 删除", p)

    def test_strip_section_ids_and_group_del(self):
        out = report_diff._strip_section_ids('<h2 id="s3">x</h2><p id="keep">y</p>')
        self.assertNotIn('id="s3"', out)
        self.assertIn('id="keep"', out)
        group = report_diff._group_del([report_diff.Block("p", "x", "<p>x</p>")])
        self.assertIn("diff-del-group", group)
        self.assertIn("已更新 · 删除 1 处", group)

    def test_diff_summary_and_similarity(self):
        stats = {"new": 1, "mod": 2, "del": 3, "equal": 4}
        self.assertEqual(report_diff.diff_summary(stats, "2026-11", None),
                         "2026-11 期为首期报告，无上期对比。")
        s = report_diff.diff_summary(stats, "2026-11", "2026-10")
        self.assertIn("新增 1 处、修改 2 处、删除 3 处，未变更 4 处", s)
        self.assertEqual(report_diff._similarity("", ""), 1.0)
        self.assertEqual(report_diff._normalize_text("  a   b  "), "a b")

    def test_serialize_escapes(self):
        blocks = report_diff.extract_blocks("<p>a &amp; b</p><p>&lt;x&gt;</p>")
        self.assertEqual(blocks[0].html, "<p>a &amp; b</p>")
        self.assertEqual(blocks[1].html, "<p>&lt;x&gt;</p>")

    def test_diff_blocks_uneven_replace(self):
        prev = report_diff.extract_blocks("<body><p>甲</p><p>乙</p></body>")
        curr = report_diff.extract_blocks("<body><p>丙</p></body>")
        ops = [op for op, _b, _o in report_diff.diff_blocks(prev, curr)]
        self.assertEqual(ops.count("del"), 2)
        self.assertEqual(ops.count("new"), 1)
        prev2 = report_diff.extract_blocks("<body><p>甲</p></body>")
        curr2 = report_diff.extract_blocks("<body><p>乙</p><p>丙</p></body>")
        ops2 = [op for op, _b, _o in report_diff.diff_blocks(prev2, curr2)]
        self.assertEqual(ops2.count("del"), 1)
        self.assertEqual(ops2.count("new"), 2)

    def test_render_diffed_body_mod_counts_old_as_del(self):
        body, stats = report_diff.render_diffed_body(
            "<body><h2>标题</h2><p>旧文案改了一下</p></body>",
            "<body><h2>标题</h2><p>旧文案</p></body>",
        )
        self.assertEqual(stats["mod"], 1)
        self.assertEqual(stats["del"], 1)
        self.assertIn("diff-del-group", body)


if __name__ == "__main__":
    unittest.main()
