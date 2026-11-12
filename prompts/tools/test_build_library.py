# -*- coding: utf-8 -*-
"""主题聚合页面构建器测试。"""

import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_library as library
import validate

ROOT = Path(__file__).resolve().parents[2]


class DisplayConfigTests(unittest.TestCase):
    def test_display_metadata_is_required(self):
        with self.assertRaises(library.BuildError):
            library.require_display_metadata({"id": "02-career-driver", "name": "司机"})

    def test_project_topics_have_display_metadata(self):
        topics = library.load_topics()
        self.assertEqual(13, len(topics))
        self.assertTrue(all(t["category"] and t["description"] for t in topics))


class RenderingTests(unittest.TestCase):
    def test_heading_is_namespaced(self):
        html = '<h2 id="薪资">薪资</h2>'
        result = library.namespace_html(html, "02-career-driver", ROOT / "02-career-driver/reports", {})
        self.assertIn('id="topic-02-career-driver--薪资"', result)

    def test_internal_anchor_is_namespaced(self):
        html = '<h2 id="薪资">薪资</h2><p><a href="#薪资">直达</a></p>'
        result = library.namespace_html(html, "02-career-driver", ROOT / "02-career-driver/reports", {})
        self.assertIn('href="#topic-02-career-driver--薪资"', result)

    def test_cross_topic_html_link_targets_library_anchor(self):
        source = ROOT / "02-career-driver/reports"
        target = ROOT / "08-visa-immigration/reports/日本签证与在留资格知识手册.html"
        result = library.rewrite_href(
            "../../08-visa-immigration/reports/日本签证与在留资格知识手册.html#永住",
            "02-career-driver", source, {target.resolve(): "08-visa-immigration"},
        )
        self.assertEqual("#topic-08-visa-immigration--永住", result)

    def test_relative_link_resolves_from_root(self):
        result = library.rewrite_href(
            "../../02-career-driver/data/ssw-driver-cost-config.md?x=1#记录",
            "02-career-driver", ROOT / "02-career-driver/reports", {},
        )
        self.assertEqual("02-career-driver/data/ssw-driver-cost-config.md?x=1#记录", result)

    def test_external_link_is_unchanged(self):
        href = "https://example.com/a#b"
        self.assertEqual(href, library.rewrite_href(href, "02-career-driver", ROOT, {}))

    def test_table_is_wrapped_for_responsive_scrolling(self):
        result = library.namespace_html("<table><tr><td>A</td></tr></table>", "02-career-driver", ROOT, {})
        self.assertIn('<div class="table-wrap"><table>', result)

    def test_chapter_extraction_filters_meta_headings(self):
        body = (
            '<h2 id="topic-02-career-driver--导航">导航与使用约定</h2>'
            '<h2 id="topic-02-career-driver--索引">02-career-driver 索引</h2>'
            '<h2 id="topic-02-career-driver--薪资">02 薪资结构与工时合规</h2>'
        )
        chapters = library.extract_chapters(body, "02-career-driver")
        self.assertEqual([{"title": "02 薪资结构与工时合规", "id": "topic-02-career-driver--薪资", "level": 2}], chapters)

    def test_missing_source_fails(self):
        config = {"id": "99-missing", "name": "缺失", "kind": "knowledge",
                  "target": "99-missing/reports/缺失.md", "category": "测试", "description": "测试"}
        with self.assertRaises(library.BuildError):
            library.resolve_topic_source(config)

    def test_monitor_source_uses_scheduler_latest_report(self):
        config = library.load_topics()[0]
        expected = ROOT / "01-ssw-driver/reports/日本特定技能司机物流监测报告_v2026.11.12_5.md"
        with patch("build_library.update_scheduler.latest_report", return_value=expected) as latest:
            source, _ = library.resolve_topic_source(config)
        latest.assert_called_once_with(config)
        self.assertEqual(expected, source)

    def test_library_snippet_offsets_from_first_search_match(self):
        self.assertIn("Math.min(...positions) - 42", library.LIBRARY_JS)

    def test_long_source_urls_wrap_within_topic_body(self):
        self.assertIn(
            ".topic-body p, .topic-body li { overflow-wrap: anywhere; }",
            library.LIBRARY_CSS,
        )


class PageBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first = library.build_pages()
        cls.second = library.build_pages()

    def test_output_is_deterministic(self):
        self.assertEqual(self.first, self.second)

    def test_all_topics_have_two_way_links(self):
        index = self.first[Path("index.html")]
        library_html = self.first[Path("library.html")]
        for topic in library.load_topics():
            anchor = library.topic_anchor(topic["id"])
            self.assertIn(f'id="{anchor}"', index)
            self.assertIn(f'id="{anchor}"', library_html)
            self.assertIn(f'href="library.html#{anchor}"', index)
            self.assertIn(f'href="index.html#{anchor}"', library_html)

    def test_index_has_all_categories_and_cards(self):
        index = self.first[Path("index.html")]
        self.assertEqual(13, len(re.findall(r'class="topic-card"', index)))
        self.assertEqual(7, len(re.findall(r'class="category-section"', index)))

    def test_library_retains_source_content(self):
        output = self.first[Path("library.html")]
        self.assertIn("日本司机职业知识手册", output)
        self.assertIn("02 薪资结构与工时合规", output)
        self.assertIn("日本签证与在留资格知识手册", output)

    def test_library_heading_ids_are_unique(self):
        output = self.first[Path("library.html")]
        ids = re.findall(r'<h[1-6] id="([^"]+)"', output)
        self.assertEqual(len(ids), len(set(ids)))


class GeneratedOutputTests(unittest.TestCase):
    def test_committed_pages_are_current(self):
        for relative, expected in library.build_pages().items():
            actual = ROOT / relative
            self.assertTrue(actual.is_file(), f"缺少生成页面: {relative}")
            self.assertEqual(expected, actual.read_text(encoding="utf-8"), f"页面需要重新生成: {relative}")


class CheckModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pages = {Path("index.html"): "expected"}

    def tearDown(self):
        self.temp.cleanup()

    def test_compare_outputs_detects_missing_file(self):
        self.assertEqual([Path("index.html")], library.compare_outputs(self.pages, self.root))

    def test_compare_outputs_detects_stale_file(self):
        (self.root / "index.html").write_text("stale", encoding="utf-8")
        self.assertEqual([Path("index.html")], library.compare_outputs(self.pages, self.root))

    def test_compare_outputs_accepts_current_file(self):
        (self.root / "index.html").write_text("expected", encoding="utf-8")
        self.assertEqual([], library.compare_outputs(self.pages, self.root))


class ValidationIntegrationTests(unittest.TestCase):
    def test_library_validation_accepts_current_pages(self):
        errors = []
        warnings = []

        validate.check_library_pages(errors, warnings)

        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_library_validation_detects_missing_return_link(self):
        topic_id = "02-career-driver"
        anchor = library.topic_anchor(topic_id)
        pages = {
            Path("index.html"): (
                f'<article id="{anchor}">'
                f'<a href="library.html#{anchor}">汇总阅读</a></article>'
            ),
            Path("library.html"): f'<section id="{anchor}"></section>',
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for relative, content in pages.items():
                (root / relative).write_text(content, encoding="utf-8")
            with (
                patch("validate.ROOT", root),
                patch("validate.build_library.load_topics", return_value=[{"id": topic_id}]),
                patch("validate.build_library.build_pages", return_value=pages),
                patch("validate.build_library.compare_outputs", return_value=[]),
            ):
                errors = []
                validate.check_library_pages(errors, [])

        self.assertTrue(any("返回链接" in error for error in errors), errors)


class UpdateMarkerTests(unittest.TestCase):
    def test_body_without_markers_is_unchanged(self):
        body = (
            '<h2 id="topic-02-career-driver--薪资">02 薪资</h2>\n<p>正文。</p>\n'
            '<table><tr><td>A</td></tr></table>'
        )
        result, updates = library.apply_update_markers(body, "02-career-driver")
        self.assertEqual(body, result)
        self.assertEqual([], updates)

    def test_section_marker_adds_badge_and_highlight(self):
        body = (
            '<h2 id="topic-02-career-driver--薪资">02 薪资</h2>\n'
            '<!-- updated: 2026-11-12 | 最低賃金 -->\n\n'
            '<p>正文。</p>\n'
            '<h2 id="topic-02-career-driver--其他">03 其他</h2>\n'
            '<p>未更新。</p>'
        )
        result, updates = library.apply_update_markers(body, "02-career-driver")
        self.assertEqual([{"date": "2026-11-12", "note": "最低賃金"}], updates)
        self.assertIn('<span class="update-badge"', result)
        self.assertIn('title="已更新 2026-11-12：最低賃金"', result)
        self.assertIn('<div class="update-section" data-updated="2026-11-12">', result)
        # 未更新章节保持原样，不被卷入高亮区
        self.assertLess(result.index("</div>"), result.index('<h2 id="topic-02-career-driver--其他"'))
        self.assertTrue(result.endswith("<p>未更新。</p>"))

    def test_block_marker_wraps_following_block(self):
        body = (
            '<p>前言。</p>\n<!-- updated: 2026-11-12 -->\n'
            '<table><tr><td>A</td></tr></table>\n<p>后续。</p>'
        )
        result, updates = library.apply_update_markers(body, "02-career-driver")
        self.assertEqual([{"date": "2026-11-12", "note": ""}], updates)
        self.assertIn('<div class="update-block" data-updated="2026-11-12">', result)
        self.assertIn('<table><tr><td>A</td></tr></table></div>', result)
        self.assertTrue(result.startswith("<p>前言。</p>"))
        self.assertTrue(result.endswith("<p>后续。</p>"))

    def test_marker_before_heading_is_section_level(self):
        body = '<!-- updated: 2026-11-12 | 新增 -->\n<h2 id="a">05 新章节</h2>\n<p>内容。</p>'
        result, updates = library.apply_update_markers(body, "02-career-driver")
        self.assertEqual(1, len(updates))
        self.assertIn('<h2 id="a">05 新章节 <span class="update-badge"', result)
        self.assertIn('<div class="update-section"', result)

    def test_invalid_marker_syntax_is_ignored(self):
        body = '<p>正文。</p>\n<!-- updated: 2026/11/12 -->\n<p>后续。</p>'
        result, updates = library.apply_update_markers(body, "02-career-driver")
        self.assertEqual(body, result)
        self.assertEqual([], updates)

    def test_marker_does_not_change_heading_ids(self):
        body = (
            '<h2 id="topic-x--a">A</h2>\n<!-- updated: 2026-11-12 -->\n<p>1</p>\n'
            '<h3 id="topic-x--b">B</h3>\n<p>2</p>\n<h2 id="topic-x--c">C</h2>\n<p>3</p>'
        )
        result, _ = library.apply_update_markers(body, "x")
        ids = re.findall(r'<h[1-6] id="([^"]+)"', result)
        self.assertEqual(["topic-x--a", "topic-x--b", "topic-x--c"], ids)

    def test_nested_block_marker_inside_section(self):
        body = (
            '<h2 id="a">A</h2>\n<!-- updated: 2026-11-12 -->\n<p>1</p>\n'
            '<!-- updated: 2026-11-12 -->\n<table><tr><td>x</td></tr></table>\n'
        )
        result, updates = library.apply_update_markers(body, "x")
        self.assertEqual(2, len(updates))
        self.assertIn('<div class="update-section"', result)
        self.assertIn('<div class="update-block"', result)

    def test_empty_section_only_adds_heading_badge(self):
        body = '<h2 id="a">A</h2>\n<!-- updated: 2026-11-12 -->\n<h2 id="b">B</h2>\n<p>x</p>'
        result, updates = library.apply_update_markers(body, "x")
        self.assertEqual(1, len(updates))
        self.assertIn('<span class="update-badge"', result)
        self.assertNotIn("update-section", result)


class UpdateDisplayTests(unittest.TestCase):
    def _topic(self, updates):
        return {
            "id": "02-career-driver", "name": "司机岗位", "kind": "knowledge",
            "category": "职业就业", "description": "测试描述", "version": "v1.0",
            "html": ROOT / "02-career-driver/reports/日本司机职业知识手册.html",
            "body": "<p>正文</p>",
            "chapters": [{"title": "02 薪资", "id": "topic-02-career-driver--薪资", "level": 2}],
            "updates": updates,
        }

    def test_index_renders_update_flag(self):
        index = library.render_index([self._topic([{"date": "2026-11-12", "note": ""}])])
        self.assertIn("已更新 1 处", index)
        self.assertIn('class="topic-update-flag"', index)
        self.assertIn("最近更新 2026-11-12", index)

    def test_index_omits_update_flag_for_clean_topic(self):
        index = library.render_index([self._topic([])])
        self.assertNotIn('class="topic-update-flag"', index)

    def test_library_renders_update_flag(self):
        page = library.render_library([self._topic([{"date": "2026-11-12", "note": ""}])])
        self.assertIn("已更新 1 处", page)
        self.assertIn('class="topic-update-flag"', page)

    def test_library_omits_update_flag_for_clean_topic(self):
        page = library.render_library([self._topic([])])
        self.assertNotIn('class="topic-update-flag"', page)


class UpdateMarkerValidationTests(unittest.TestCase):
    def _write(self, root, text):
        reports = root / "02-career-driver" / "reports"
        reports.mkdir(parents=True)
        (reports / "日本司机职业知识手册.md").write_text(text, encoding="utf-8")

    def test_valid_marker_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write(root, "<!-- updated: 2026-11-12 | 最低賃金 -->\n")
            with patch("validate.ROOT", root):
                errors, warnings = [], []
                validate.check_update_markers(errors, warnings)
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_bad_marker_syntax_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write(root, "<!-- updated: 2026/11/12 -->\n")
            with patch("validate.ROOT", root):
                errors, warnings = [], []
                validate.check_update_markers(errors, warnings)
        self.assertTrue(any("语法错误" in e for e in errors), errors)

    def test_inline_marker_warns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._write(root, "说明文字 <!-- updated: 2026-11-12 -->\n")
            with patch("validate.ROOT", root):
                errors, warnings = [], []
                validate.check_update_markers(errors, warnings)
        self.assertEqual([], errors)
        self.assertTrue(any("单独成行" in w for w in warnings), warnings)

    def test_current_sources_pass_marker_validation(self):
        errors, warnings = [], []
        validate.check_update_markers(errors, warnings)
        self.assertEqual([], errors)
        self.assertEqual([], warnings)


if __name__ == "__main__":
    unittest.main()
