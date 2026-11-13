# -*- coding: utf-8 -*-
"""无障碍合规测试（P0-1 / P0-2 / P0-3）。

对应官方规范（已核对原文）：
- GOV.UK：skip link 置于 body 首位、landmark 骨架、details 结构
- WebAIM：WCAG 2.1 AA 对比度（正文 4.5:1、大字 3:1、非文本含焦点环 3:1）
- BBC GEL：表格容器 role=group / aria-labelledby / tabindex / caption / th[scope]
"""
import unittest
from pathlib import Path

import a11y
import build_library as library
import md2html

ROOT = Path(__file__).resolve().parents[2]


def project_css():
    return "\n".join([md2html.SHELL_CSS, md2html.BASE_CSS, library.LIBRARY_CSS])


class ContrastTests(unittest.TestCase):
    def test_text_palette_meets_wcag_aa(self):
        self.assertEqual([], a11y.check_palette_contrast(project_css()))

    def test_focus_indicator_meets_non_text_contrast(self):
        self.assertEqual([], a11y.check_focus_indicator(project_css()))


class ShellStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = library.build_pages()
        cls.index = cls.pages[Path("index.html")]
        cls.library_html = cls.pages[Path("library.html")]

    def test_page_shell_has_skip_link_and_main(self):
        html = library.page_shell(
            "t", "index-page", '<main id="main-content">x</main>', ""
        )
        self.assertIn(
            '<a class="skip-link" href="#main-content">跳到主要内容</a>', html
        )
        self.assertIn('<main id="main-content">', html)

    def test_source_template_has_skip_link_and_main(self):
        self.assertIn(
            '<a class="skip-link" href="#main-content">跳到主要内容</a>',
            md2html.TEMPLATE,
        )
        self.assertIn('<main id="main-content">', md2html.TEMPLATE)

    def test_index_landmark_skeleton(self):
        self._assert_landmarks(self.index, aside=False)

    def test_library_landmark_skeleton(self):
        self._assert_landmarks(self.library_html, aside=True)

    def _assert_landmarks(self, html, aside=True):
        self.assertRegex(html, r'<main[^>]*id="main-content"')
        self.assertIn('<header class="topbar">', html)
        self.assertIn('<footer class="footer">', html)
        self.assertRegex(html, r'<nav[^>]*aria-label="[^"]+"')
        if aside:
            self.assertRegex(html, r'<aside[^>]*aria-label="[^"]+"')

    def test_index_details_follow_govuk_structure(self):
        self.assertRegex(
            self.index,
            r'<details class="topic-details"><summary><span class="summary-text">',
        )
        self.assertRegex(self.index, r'</summary><div class="details-text">')

    def test_library_details_follow_govuk_structure(self):
        self.assertRegex(
            self.library_html,
            r'<details class="topic-local-toc"><summary><span class="summary-text">',
        )
        self.assertRegex(self.library_html, r'</summary><div class="details-text">')

    def test_source_page_shell_passes_source_checks(self):
        html = (
            '<body><a class="skip-link" href="#main-content">跳到主要内容</a>'
            '<main id="main-content">正文</main></body>'
        )
        self.assertEqual([], a11y.check_html(html, page_kind="source"))

    def test_source_page_without_skip_link_fails(self):
        self.assertTrue(
            a11y.check_html(
                '<body><main id="main-content">正文</main></body>',
                page_kind="source",
            )
        )


class TableStructureTests(unittest.TestCase):
    def test_namespace_wraps_table_with_caption_and_group_role(self):
        body = (
            "<table><thead><tr><th>A</th></tr></thead>"
            "<tbody><tr><td>1</td></tr></tbody></table>"
        )
        result = library.namespace_html(body, "02-career-driver", ROOT, {})
        self.assertRegex(
            result,
            r'<div class="table-wrap" role="group" '
            r'aria-labelledby="table-caption-02-career-driver-1" tabindex="0">',
        )
        self.assertIn(
            '<caption id="table-caption-02-career-driver-1">', result
        )
        self.assertIn('<th scope="col">A</th>', result)

    def test_library_tables_are_accessible(self):
        self.assertEqual([], a11y.check_tables(library.build_pages()[Path("library.html")]))


if __name__ == "__main__":
    unittest.main()
