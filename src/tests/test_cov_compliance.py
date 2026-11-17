"""内容合规 / 校验工具的单元级覆盖补强。

只读被测源码 + tempfile / unittest.mock，不改动仓库真实文件、不联网。
覆盖重点（按缺口从大到小）：
  - validate.py：check_templates / check_business_dirs / main（此前 0%）；
  - classify_reports.py：strays / owner_of / main 各分支（此前 0%）；
  - ensure_region_topics.py：main 的 check / 修复 / 通过分支（此前 0%）；
  - compliance_check.py：load_rules / detect_types / cycle_rule / check_report /
    type_of_business / collect_targets / run_check / run_audit / run_scaffold /
    run_list_types / load_whitelist / main；
  - lint_reports.py：lint_html 各规则 / collect_report_htmls / load_whitelist /
    main 退出码分支；
  - fact_card_check.py：parse_cards / check_fields / check_pointers /
    check_orphans / collect_pointers / render_md / main；
  - info_quality_check.py：纯函数、检查函数、修复函数、write_reports / run / main。

导入方式沿用仓库惯例：sys.path.insert(0, ROOT/src/prompts-tools/tools) 后 import。
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "prompts-tools" / "tools"))

import _common  # noqa: E402
import classify_reports  # noqa: E402
import compliance_check  # noqa: E402
import ensure_region_topics  # noqa: E402
import fact_card_check  # noqa: E402
import info_quality_check as iqc  # noqa: E402
import lint_reports  # noqa: E402
import validate  # noqa: E402

_ROOT_MODULES = (
    _common,
    compliance_check,
    lint_reports,
    fact_card_check,
    classify_reports,
    ensure_region_topics,
    validate,
    iqc,
)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _run_main(func, argv):
    """以指定 argv 调用 main()，返回 (退出码, stdout 文本)。"""
    buf = io.StringIO()
    with mock.patch.object(sys, "argv", argv), redirect_stdout(buf):
        code = func()
    return code, buf.getvalue()


def _rules_doc() -> dict:
    return {
        "common": {"require_title": True, "anchor_check": True,
                   "nav_required_cycles": ["monthly"]},
        "types": {
            "demo-type": {
                "name": "演示类型",
                "template_dir": "demo-type",
                "template": "report.html",
                "cycles": {
                    "baseline": {"sections": 2, "section_titles": ["一、基线", "二、正文"]},
                    "monthly": {"sections": 2, "nav": True,
                                "section_titles": ["一、执行摘要", "二、正文"]},
                },
            },
            "evt-type": {
                "name": "事件类型",
                "template_dir": "evt-type",
                "cycles": {"baseline": {"sections": 1}, "event": {"sections": 1, "nav": True}},
                "event_cycle": "event",
            },
            "evt2-type": {
                "name": "事件回落类型",
                "template_dir": "evt2-type",
                "cycles": {"baseline": {"sections": 1}, "flash": {"sections": 1, "nav": True}},
                "event_cycle": "flash",
            },
        },
    }


class _TempRootCase(unittest.TestCase):
    """公共基类：把各模块的 ROOT 指向 tempfile 临时目录。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()  # noqa: P201
        self.root = Path(self._tmp.name)
        self._saved_root = {m: getattr(m, "ROOT", None) for m in _ROOT_MODULES}
        for m in _ROOT_MODULES:
            m.ROOT = self.root
        self._saved_tpl = {m: m.TEMPLATE_ROOT for m in (validate, classify_reports)}
        for m in (validate, classify_reports):
            m.TEMPLATE_ROOT = self.root / "src" / "report_templates"
        self._saved_audit = iqc.AUDIT_DIR
        iqc.AUDIT_DIR = self.root / "audit"
        self.addCleanup(self._restore)

    def _restore(self):
        for m, val in self._saved_root.items():
            m.ROOT = val
        for m, val in self._saved_tpl.items():
            m.TEMPLATE_ROOT = val
        iqc.AUDIT_DIR = self._saved_audit
        self._tmp.cleanup()

    # ── 通用构造 helpers ──
    def _business(self, name: str, config: str | None = None) -> Path:
        d = self.root / name
        (d / "prompts").mkdir(parents=True, exist_ok=True)
        if config is not None:
            _write(d / "prompts" / "business-config.md", config)
        return d

    def _rules_path(self) -> Path:
        return _write(self.root / "compliance-rules.json", json.dumps(_rules_doc(), ensure_ascii=False))


# ══════════════════════════════════════════════════════════════
# validate.py
# ══════════════════════════════════════════════════════════════
class TestCovComplianceValidate(_TempRootCase):
    """结构与规范校验（validate.py）。"""

    def setUp(self):
        super().setUp()
        self._saved_err = validate.ERRORS
        self._saved_warn = validate.WARNINGS
        validate.ERRORS = []
        validate.WARNINGS = []
        self.addCleanup(self._restore_lists)

    def _restore_lists(self):
        validate.ERRORS = self._saved_err
        validate.WARNINGS = self._saved_warn

    def _make_valid_templates(self) -> None:
        tpl = self.root / "src" / "report_templates"
        tpl.mkdir(parents=True, exist_ok=True)
        for name in _common.REQUIRED_TEMPLATE_FILES:
            _write(tpl / name, f"# {name}\n")
        for type_id, files in _common.TEMPLATE_TYPE_DIRS.items():
            for name in files:
                _write(tpl / type_id / name, f"# {type_id}/{name}\n")

    def _make_valid_business(self) -> None:
        d = self._business("01-demo", "{{REGION}} / {{TOPIC}} / {{REGISTRY_PATH}}\n")
        (d / "reports").mkdir(exist_ok=True)
        (d / "data").mkdir(exist_ok=True)
        _write(d / "reports" / "2026-11-demo.md", "# x\n")
        _write(d / "reports" / "2026-11-demo.html", "<html></html>\n")

    def test_check_templates_missing_dir(self):
        validate.TEMPLATE_ROOT = self.root / "nope"
        validate.check_templates()
        self.assertTrue(any("缺少通用模板目录" in e for e in validate.ERRORS))

    def test_check_templates_full_pass(self):
        self._make_valid_templates()
        validate.check_templates()
        self.assertEqual(validate.ERRORS, [])

    def test_check_templates_business_keyword_and_topic_marker(self):
        self._make_valid_templates()
        tpl = self.root / "src" / "report_templates"
        _write(tpl / "extra.md", "迪拜公寓\n")
        type_id = next(iter(_common.TEMPLATE_TYPE_DIRS))
        _write(tpl / type_id / "polluted.md", "卡车司机\n")
        validate.check_templates()
        self.assertTrue(any("业务关键词" in e and "extra.md" in e for e in validate.ERRORS))
        self.assertTrue(any("业务主题词" in e and "polluted.md" in e for e in validate.ERRORS))

    def test_check_business_dirs_no_business_warns(self):
        self._make_valid_templates()
        validate.check_business_dirs()
        self.assertTrue(any("未识别到任何业务线目录" in w for w in validate.WARNINGS))

    def test_check_business_dirs_warnings(self):
        self._make_valid_templates()
        d = self._business("01-demo", "缺变量\n")   # 缺 {{REGION}} 等
        (d / "reports").mkdir(exist_ok=True)
        _write(d / "reports" / "bad-name.md", "# x\n")          # 命名不合规
        _write(d / "reports" / "2026-11-other.md", "# x\n")     # slug 不一致
        _write(d / "reports" / "2026-11-demo.html", "<html></html>\n")  # 缺 md 源稿
        validate.check_business_dirs()
        joined = "\n".join(validate.WARNINGS)
        self.assertIn("缺少变量 {{REGION}}", joined)
        self.assertIn("bad-name.md: 文件名不符合", joined)
        self.assertIn("主题 slug「other」与目录「demo」不一致", joined)
        self.assertIn("缺少对应 md 源稿", joined)
        self.assertIn("缺少 data/ 目录", joined)

    def test_main_pass(self):
        self._make_valid_templates()
        self._make_valid_business()
        code, out = _run_main(validate.main, ["validate.py"])
        self.assertEqual(code, 0)
        self.assertIn("校验通过", out)

    def test_main_errors_return_1(self):
        # 模板目录缺失 → 错误项
        validate.TEMPLATE_ROOT = self.root / "nope"
        code, out = _run_main(validate.main, ["validate.py"])
        self.assertEqual(code, 1)
        self.assertIn("校验失败", out)

    def test_main_warnings_return_2(self):
        self._make_valid_templates()
        self._business("01-demo", "缺变量\n")
        code, out = _run_main(validate.main, ["validate.py"])
        self.assertEqual(code, 2)
        self.assertIn("项警告", out)


# ══════════════════════════════════════════════════════════════
# classify_reports.py
# ══════════════════════════════════════════════════════════════
class TestCovComplianceClassify(_TempRootCase):
    """报告自动归位（classify_reports.py）。"""

    def test_strays_root_and_template(self):
        _write(self.root / "2026-11-demo.md", "# x\n")
        tpl = self.root / "src" / "report_templates"
        _write(tpl / "2026-11-other.md", "# x\n")
        _write(tpl / "sub" / "2026-11-deep.md", "# x\n")
        names = {p.name for p in classify_reports.strays()}
        self.assertEqual(names, {"2026-11-demo.md", "2026-11-other.md", "2026-11-deep.md"})

    def test_owner_of_unique_none_multi(self):
        self._business("01-demo")
        self._business("02-other")
        self.assertEqual(classify_reports.owner_of("2026-11-demo.md").region, "01-demo")
        self.assertIsNone(classify_reports.owner_of("2026-11-nomatch.md"))
        self.assertIsNone(classify_reports.owner_of("not-a-report.md"))
        # 同名 slug 多归属 → None
        self._business("03-demo")
        self.assertIsNone(classify_reports.owner_of("2026-11-demo.md"))

    def test_main_check_movable(self):
        stray = _write(self.root / "2026-11-demo.md", "# x\n")
        self._business("01-demo")
        code, out = _run_main(classify_reports.main, ["classify_reports.py", "--check"])
        self.assertEqual(code, 1)
        self.assertIn("[MISPLACED]", out)
        self.assertIn("2026-11-demo.md", out)
        self.assertTrue(stray.exists())   # check 模式不移动

    def test_main_apply_moves(self):
        stray = _write(self.root / "2026-11-demo.md", "# x\n")
        self._business("01-demo")
        code, out = _run_main(classify_reports.main, ["classify_reports.py", "--apply"])
        self.assertEqual(code, 0)
        self.assertIn("[MOVED]", out)
        self.assertFalse(stray.exists())
        self.assertTrue((self.root / "01-demo" / "reports" / "2026-11-demo.md").exists())

    def test_main_apply_failure_returns_1(self):
        _write(self.root / "2026-11-demo.md", "# x\n")
        self._business("01-demo")
        with mock.patch.object(classify_reports.shutil, "move", side_effect=OSError("boom")):
            code, out = _run_main(classify_reports.main, ["classify_reports.py", "--apply"])
        self.assertEqual(code, 1)
        self.assertIn("[ERROR] 移动失败", out)

    def test_main_unknown_warn_returns_2(self):
        _write(self.root / "2026-11-nomatch.md", "# x\n")
        code, out = _run_main(
            classify_reports.main, ["classify_reports.py", "--unknown-warn"])
        self.assertEqual(code, 2)
        self.assertIn("[UNKNOWN]", out)
        self.assertIn("需人工确认归属", out)

    def test_main_pass(self):
        self._business("01-demo")
        code, out = _run_main(classify_reports.main, ["classify_reports.py"])
        self.assertEqual(code, 0)
        self.assertIn("无错位报告", out)


# ══════════════════════════════════════════════════════════════
# ensure_region_topics.py
# ══════════════════════════════════════════════════════════════
class TestCovComplianceEnsureRegionTopics(_TempRootCase):
    """业务线结构补全（ensure_region_topics.py）。"""

    def test_main_no_business(self):
        code, out = _run_main(ensure_region_topics.main, ["ensure_region_topics.py"])
        self.assertEqual(code, 0)
        self.assertIn("未识别到业务线目录", out)

    def test_main_check_missing_returns_2(self):
        self._business("01-demo")
        code, out = _run_main(
            ensure_region_topics.main, ["ensure_region_topics.py", "--check"])
        self.assertEqual(code, 2)
        self.assertIn("[WARN] 01-demo: 缺少 reports/ 目录", out)
        self.assertIn("[WARN] 01-demo: 缺少 data/ 目录", out)
        self.assertFalse((self.root / "01-demo" / "reports").exists())

    def test_main_fix_creates_dirs(self):
        self._business("01-demo")
        code, out = _run_main(ensure_region_topics.main, ["ensure_region_topics.py"])
        self.assertEqual(code, 0)
        self.assertIn("[FIXED] 01-demo: 已创建 reports/ 目录", out)
        self.assertTrue((self.root / "01-demo" / "reports").is_dir())
        self.assertTrue((self.root / "01-demo" / "data").is_dir())

    def test_main_all_present(self):
        d = self._business("01-demo", "# 配置\n")
        (d / "reports").mkdir(exist_ok=True)
        (d / "data").mkdir(exist_ok=True)
        code, out = _run_main(ensure_region_topics.main, ["ensure_region_topics.py"])
        self.assertEqual(code, 0)
        self.assertIn("结构齐全", out)


# ══════════════════════════════════════════════════════════════
# compliance_check.py
# ══════════════════════════════════════════════════════════════
class TestCovComplianceComplianceCheck(_TempRootCase):
    """报告模板合规校验（compliance_check.py）。"""

    def setUp(self):
        super().setUp()
        self.rules = self._rules_path()
        self._p = mock.patch.object(compliance_check, "RULES_PATH", self.rules)
        self._p.start()
        self.addCleanup(self._p.stop)

    # ── load_rules ──
    def test_load_rules_missing_exits(self):
        with mock.patch.object(compliance_check, "RULES_PATH", self.root / "missing.json"):
            with self.assertRaises(SystemExit) as cm:
                compliance_check.load_rules()
        self.assertEqual(cm.exception.code, 1)

    def test_load_rules_invalid_json_exits(self):
        bad = _write(self.root / "bad.json", "{not json")
        with mock.patch.object(compliance_check, "RULES_PATH", bad):
            with self.assertRaises(SystemExit) as cm:
                compliance_check.load_rules()
        self.assertEqual(cm.exception.code, 1)

    # ── detect_type / detect_types / cycle_rule ──
    def test_detect_type_and_types(self):
        self.assertIsNone(compliance_check.detect_type("无引用"))
        self.assertEqual(
            compliance_check.detect_type("继承：[行业趋势周报型](../../src/report_templates/trend-weekly/)"),
            "trend-weekly")
        self.assertEqual(
            compliance_check.detect_types(
                "a ../../src/report_templates/trend-weekly/ b "
                "../../src/report_templates/employment-research/ c "
                "../../src/report_templates/trend-weekly/"),
            ["trend-weekly", "employment-research"])

    def test_cycle_rule_unregistered(self):
        rules = _rules_doc()
        self.assertEqual(compliance_check.cycle_rule(rules, "nope", "monthly"), (None, False))

    def test_cycle_rule_baseline_fallback_inherited(self):
        rules = _rules_doc()
        rule, inherited = compliance_check.cycle_rule(rules, "demo-type", "weekly")
        self.assertTrue(inherited)
        self.assertEqual(rule["sections"], 2)
        # weekly 不在 nav_required_cycles，baseline 亦未登记 nav → False
        self.assertFalse(rule["nav"])

    def test_cycle_rule_event_cycle_fallback(self):
        rules = _rules_doc()
        rule, inherited = compliance_check.cycle_rule(rules, "evt2-type", "event")
        self.assertFalse(inherited)
        self.assertTrue(rule["nav"])   # flash 周期登记了 nav

    # ── check_report ──
    def test_check_report_fewer_h2_error(self):
        rule = {"sections": 2, "nav": True, "template": "t"}
        common = {"require_title": True, "anchor_check": True}
        text = ("<html><title>T</title><nav aria-label=\"报告导航\"></nav>"
                "<h2 id=\"s1\">一</h2></html>")
        issues = compliance_check.check_report(text, rule, common)
        self.assertTrue(any(lvl == "E" and "结构不完整" in m for lvl, m in issues))

    def test_check_report_more_h2_warning(self):
        rule = {"sections": 2, "nav": True, "template": "t"}
        common = {"require_title": True, "anchor_check": True}
        text = ("<html><title>T</title><nav aria-label=\"报告导航\"></nav>"
                "<h2 id=\"s1\">一</h2><h2 id=\"s2\">二</h2><h2 id=\"s3\">三</h2></html>")
        issues = compliance_check.check_report(text, rule, common)
        self.assertTrue(any(lvl == "W" and "超出模板骨架" in m for lvl, m in issues))

    def test_check_report_noncontiguous_ids_error(self):
        rule = {"sections": 2, "nav": False}
        common = {"require_title": True, "anchor_check": True}
        text = ("<html><title>T</title><h2 id=\"s1\">一</h2><h2 id=\"s3\">三</h2></html>")
        issues = compliance_check.check_report(text, rule, common)
        self.assertTrue(any(lvl == "E" and "编号不连续" in m for lvl, m in issues))

    def test_check_report_missing_title_error(self):
        rule = {"sections": 1, "nav": False}
        common = {"require_title": True, "anchor_check": False}
        text = "<html><h2 id=\"s1\">一</h2></html>"
        issues = compliance_check.check_report(text, rule, common)
        self.assertTrue(any(lvl == "E" and "缺少 <title>" in m for lvl, m in issues))

    def test_check_report_nav_required_missing_error(self):
        rule = {"sections": 1, "nav": True}
        common = {"require_title": True, "anchor_check": False}
        text = "<html><title>T</title><h2 id=\"s1\">一</h2></html>"
        issues = compliance_check.check_report(text, rule, common)
        self.assertTrue(any(lvl == "E" and "顶部导航" in m for lvl, m in issues))

    def test_check_report_nav_optional_missing_warning(self):
        rule = {"sections": 1, "nav": False}
        common = {"require_title": True, "anchor_check": False}
        text = "<html><title>T</title><h2 id=\"s1\">一</h2></html>"
        issues = compliance_check.check_report(text, rule, common)
        self.assertTrue(any(lvl == "W" and "简化锚点导航" in m for lvl, m in issues))

    def test_check_report_broken_anchor_error(self):
        rule = {"sections": 2, "nav": False}
        common = {"require_title": True, "anchor_check": True}
        text = ("<html><title>T</title><h2 id=\"s1\">一</h2><h2 id=\"s2\">二</h2>"
                "<a href=\"#s9\">x</a></html>")
        issues = compliance_check.check_report(text, rule, common)
        self.assertTrue(any(lvl == "E" and "断头锚点" in m for lvl, m in issues))

    def test_check_report_clean(self):
        rule = {"sections": 2, "nav": True}
        common = {"require_title": True, "anchor_check": True}
        text = ("<html><title>T</title><nav aria-label=\"报告导航\">"
                "<a href=\"#s1\">一</a></nav><h2 id=\"s1\">一</h2><h2 id=\"s2\">二</h2></html>")
        self.assertEqual(compliance_check.check_report(text, rule, common), [])

    # ── type_of_business ──
    def test_type_of_business_missing_config(self):
        b = _common.Business("01-demo")
        type_id, note = compliance_check.type_of_business(b)
        self.assertEqual(type_id, "")
        self.assertIn("缺少 prompts/business-config.md", note)

    def test_type_of_business_no_ref(self):
        d = self._business("01-demo", "# 无继承\n")
        b = _common.Business("01-demo")
        type_id, note = compliance_check.type_of_business(b)
        self.assertEqual(type_id, "")
        self.assertIn("未引用 report_templates", note)
        self.assertTrue(d.exists())

    def test_type_of_business_multiple_refs(self):
        self._business(
            "01-demo",
            "a ../../src/report_templates/trend-weekly/ b "
            "../../src/report_templates/employment-research/\n")
        b = _common.Business("01-demo")
        type_id, note = compliance_check.type_of_business(b)
        self.assertEqual(type_id, "trend-weekly")
        self.assertIn("多个类型模板引用", note)

    # ── collect_targets ──
    def test_collect_targets_only_file_cycles(self):
        d = self._business("01-demo", "x ../../src/report_templates/demo-type/\n")
        for name in ("2026-11-demo.html", "2026-11-15_weekly.html",
                     "2026-11-15-事件.html", "foo.html"):
            _write(d / "reports" / name, "<html></html>")
        cases = {}
        for name in ("2026-11-demo.html", "2026-11-15_weekly.html",
                     "2026-11-15-事件.html", "foo.html"):
            targets = compliance_check.collect_targets(f"01-demo/reports/{name}")
            rel, _text, type_id, cycle, note = targets[0]
            cases[name] = (cycle, type_id, note)
        self.assertEqual(cases["2026-11-demo.html"][0], "monthly")
        self.assertEqual(cases["2026-11-15_weekly.html"][0], "weekly")
        self.assertEqual(cases["2026-11-15-事件.html"][0], "event")
        self.assertEqual(cases["foo.html"][0], "")
        self.assertIn("不符合报告命名约定", cases["foo.html"][2])   # 类型已识别，仅命名告警
        self.assertEqual(cases["2026-11-demo.html"][1], "demo-type")

    def test_collect_targets_scan_skips_missing_reports(self):
        self._business("01-demo")   # 无 reports 目录
        self.assertEqual(compliance_check.collect_targets(None), [])

    def test_collect_targets_scan_unknown_name_note(self):
        d = self._business("01-demo", "x ../../src/report_templates/demo-type/\n")
        _write(d / "reports" / "foo.html", "<html></html>")
        targets = compliance_check.collect_targets(None)
        self.assertEqual(len(targets), 1)
        _rel, _text, type_id, cycle, note = targets[0]
        self.assertEqual(type_id, "demo-type")
        self.assertEqual(cycle, "")
        self.assertIn("不符合报告命名约定", note)

    # ── run_check ──
    def test_run_check_no_targets(self):
        errors, warnings, lines = compliance_check.run_check(None)
        self.assertEqual((errors, warnings), (0, 0))
        self.assertIn("未发现报告 HTML", lines[0])

    def _one_target(self, name: str = "2026-11-demo.html",
                    html: str = "<html><title>T</title>"
                               "<nav aria-label=\"报告导航\"></nav>"
                               "<h2 id=\"s1\">一</h2><h2 id=\"s2\">二</h2></html>",
                    config: str = "x ../../src/report_templates/demo-type/\n"):
        d = self._business("01-demo", config)
        _write(d / "reports" / name, html)

    def test_run_check_clean(self):
        self._one_target()
        errors, warnings, lines = compliance_check.run_check(None)
        self.assertEqual((errors, warnings), (0, 0))

    def test_run_check_whitelist_skip(self):
        self._one_target()
        errors, warnings, lines = compliance_check.run_check(
            None, whitelist={"01-demo/reports/2026-11-demo.html"})
        self.assertEqual((errors, warnings), (0, 0))
        self.assertTrue(any("[SKIP]" in l for l in lines))

    def test_run_check_new_only_skips_old(self):
        self._one_target(name="2026-10-demo.html")
        errors, warnings, lines = compliance_check.run_check(None, new_only=True)
        self.assertEqual((errors, warnings), (0, 0))
        self.assertFalse(any("2026-10" in l for l in lines))

    def test_run_check_note_warning(self):
        # 业务配置无继承声明 → note 警告
        self._one_target(config="# 无继承\n")
        errors, warnings, lines = compliance_check.run_check(None)
        self.assertEqual(warnings, 1)
        self.assertTrue(any("[W]" in l for l in lines))

    def test_run_check_unregistered_type_warning(self):
        self._one_target(config="x ../../src/report_templates/unknown-type/\n")
        errors, warnings, lines = compliance_check.run_check(None)
        self.assertEqual(warnings, 1)
        self.assertTrue(any("未在 compliance-rules.json 登记" in l for l in lines))

    def test_run_check_inherited_info(self):
        # weekly 周期未单独登记 → 回落基线（INFO）
        self._one_target(name="2026-11-15_weekly.html")
        errors, warnings, lines = compliance_check.run_check(None)
        self.assertTrue(any("[INFO]" in l and "按基线骨架" in l for l in lines))

    def test_run_check_error_and_warning_counts(self):
        # 节数超出 → W；缺 title → E
        html = ("<html><nav aria-label=\"报告导航\"></nav>"
                "<h2 id=\"s1\">一</h2><h2 id=\"s2\">二</h2><h2 id=\"s3\">三</h2></html>")
        self._one_target(html=html)
        errors, warnings, lines = compliance_check.run_check(None)
        self.assertEqual(errors, 1)      # 缺 <title>
        self.assertEqual(warnings, 1)    # h2 超出

    # ── run_audit ──
    def test_run_audit_writes_report(self):
        self._one_target(html="<html><title>T</title>"
                               "<nav aria-label=\"报告导航\"></nav>"
                               "<h2 id=\"s1\">一</h2></html>")   # 少一节 → 违规
        outdir = self.root / "audit-out"
        total, compliant, violated, path = compliance_check.run_audit(outdir)
        self.assertEqual((total, compliant, violated), (1, 0, 1))
        self.assertTrue(path.exists())
        self.assertIn("1 份报告存在不符合项", path.read_text(encoding="utf-8"))

    # ── run_scaffold / run_list_types ──
    def test_run_scaffold_invalid_type(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = compliance_check.run_scaffold("nope", None)
        self.assertEqual(code, 1)
        self.assertIn("未注册的报告类型", buf.getvalue())

    def test_run_scaffold_invalid_cycle(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = compliance_check.run_scaffold("demo-type", "weekly")
        self.assertEqual(code, 1)
        self.assertIn("无周期", buf.getvalue())

    def test_run_scaffold_valid(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = compliance_check.run_scaffold("demo-type", "monthly")
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("模板自动填充引导", out)
        self.assertIn("报告结构骨架", out)

    def test_run_list_types(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = compliance_check.run_list_types()
        self.assertEqual(code, 0)
        self.assertIn("demo-type", buf.getvalue())

    # ── load_whitelist ──
    def test_load_whitelist_missing_and_invalid(self):
        self.assertEqual(compliance_check.load_whitelist(self.root / "missing.json"), set())
        bad = _write(self.root / "bad.json", "{bad")
        self.assertEqual(compliance_check.load_whitelist(bad), set())

    def test_load_whitelist_expired_and_dict_form(self):
        p = _write(self.root / "w.json", json.dumps({"items": [
            {"report": "a.html", "reason": "r", "review_by": "2000-01-01"},
            {"report": "b.html", "reason": "r", "review_by": "2999-01-01"},
            {"report": "c.html", "reason": "r"},
            "not-a-dict",
        ]}))
        buf = io.StringIO()
        with redirect_stdout(buf):
            active = compliance_check.load_whitelist(p)
        self.assertEqual(active, {"b.html", "c.html"})
        self.assertIn("已逾期", buf.getvalue())

    # ── main ──
    def test_main_list_types(self):
        code, out = _run_main(
            compliance_check.main, ["compliance_check.py", "--list-types"])
        self.assertEqual(code, 0)
        self.assertIn("已注册报告类型", out)

    def test_main_scaffold_bad_usage(self):
        code, out = _run_main(
            compliance_check.main,
            ["compliance_check.py", "--scaffold", "a", "b", "c"])
        self.assertEqual(code, 1)
        self.assertIn("用法", out)

    def test_main_scaffold_invalid(self):
        code, _ = _run_main(
            compliance_check.main, ["compliance_check.py", "--scaffold", "nope"])
        self.assertEqual(code, 1)

    def test_main_audit_violated_returns_2(self):
        self._one_target(html="<html><title>T</title>"
                               "<nav aria-label=\"报告导航\"></nav>"
                               "<h2 id=\"s1\">一</h2></html>")
        audit_dir = self.root / "audit-out"
        with mock.patch.object(compliance_check, "AUDIT_DIR", audit_dir):
            code, out = _run_main(
                compliance_check.main, ["compliance_check.py", "--audit"])
        self.assertEqual(code, 2)
        self.assertIn("审计发现 1 份", out)
        self.assertTrue((audit_dir / "compliance-audit.md").exists())

    def test_main_check_errors_return_1(self):
        self._one_target(html="<html><title>T</title>"
                               "<nav aria-label=\"报告导航\"></nav>"
                               "<h2 id=\"s1\">一</h2></html>")
        wl = self.root / "wl.json"
        code, out = _run_main(
            compliance_check.main,
            ["compliance_check.py", "--whitelist", str(wl)])
        self.assertEqual(code, 1)
        self.assertIn("模板合规校验失败", out)

    def test_main_check_warnings_return_2(self):
        self._one_target(html="<html><title>T</title>"
                               "<nav aria-label=\"报告导航\"></nav>"
                               "<h2 id=\"s1\">一</h2><h2 id=\"s2\">二</h2>"
                               "<h2 id=\"s3\">三</h2></html>")
        wl = self.root / "wl.json"
        code, out = _run_main(
            compliance_check.main,
            ["compliance_check.py", "--whitelist", str(wl)])
        self.assertEqual(code, 2)
        self.assertIn("项警告", out)

    def test_main_check_pass(self):
        self._one_target()
        wl = self.root / "wl.json"
        code, out = _run_main(
            compliance_check.main,
            ["compliance_check.py", "--whitelist", str(wl)])
        self.assertEqual(code, 0)
        self.assertIn("模板合规校验通过", out)


# ══════════════════════════════════════════════════════════════
# lint_reports.py
# ══════════════════════════════════════════════════════════════
class TestCovComplianceLintReports(_TempRootCase):
    """报告内容校验 lint（lint_reports.py）。"""

    def test_lint_html_tag_mismatch_and_extra_tbody(self):
        text = "<html><body><table><thead><tr></tr></body></table></html>"
        issues = lint_reports.lint_html(text)
        self.assertTrue(any(lvl == "E" and "标签不配对" in m for lvl, m in issues))
        text2 = "<table><tbody></tbody></tbody></table>"
        issues2 = lint_reports.lint_html(text2)
        self.assertTrue(any("多余的 </tbody>" in m for _lvl, m in issues2))

    def test_lint_html_malformed_th(self):
        issues = lint_reports.lint_html('<th scope="col"ead>')
        self.assertTrue(any("畸形" in m for _lvl, m in issues))

    def test_lint_html_table_class_and_width(self):
        ths = "".join(f"<th>c{i}</th>" for i in range(6))
        text = f"<table><tr>{ths}</tr></table>"
        issues = lint_reports.lint_html(text)
        self.assertTrue(any("缺少 class=\"fixed\"" in m for _lvl, m in issues))
        self.assertTrue(any("未声明百分比列宽" in m for _lvl, m in issues))

    def test_lint_html_img_alt(self):
        issues = lint_reports.lint_html('<img src="x.png">')
        self.assertTrue(any("缺少 alt" in m for _lvl, m in issues))
        self.assertEqual(lint_reports.lint_html('<img src="x.png" alt="x">'), [])

    def test_collect_report_htmls_skips_missing_reports(self):
        self._business("01-demo")
        self.assertEqual(lint_reports.collect_report_htmls(), [])
        d = self._business("02-other")
        _write(d / "reports" / "2026-11-other.html", "<html></html>")
        out = lint_reports.collect_report_htmls()
        self.assertEqual([rel for rel, _p in out], ["02-other/reports/2026-11-other.html"])

    def test_load_whitelist_invalid_and_expired(self):
        self.assertEqual(lint_reports.load_whitelist(self.root / "missing.json"), set())
        bad = _write(self.root / "bad.json", "{bad")
        self.assertEqual(lint_reports.load_whitelist(bad), set())
        p = _write(self.root / "w.json", json.dumps([
            {"report": "old.html", "review_by": "2000-01-01"},
            {"report": "new.html", "review_by": "2999-01-01"},
        ]))
        buf = io.StringIO()
        with redirect_stdout(buf):
            active = lint_reports.load_whitelist(p)
        self.assertEqual(active, {"new.html"})
        self.assertIn("已逾期", buf.getvalue())

    def _one_report(self, name: str, html: str) -> None:
        d = self._business("01-demo")
        _write(d / "reports" / name, html)

    def test_main_no_targets(self):
        wl = self.root / "wl.json"
        code, out = _run_main(
            lint_reports.main, ["lint_reports.py", "--whitelist", str(wl)])
        self.assertEqual(code, 0)
        self.assertIn("未发现报告 HTML", out)

    def test_main_errors_return_1(self):
        self._one_report("2026-11-demo.html", "<table><tbody></tbody></tbody></table>")
        wl = self.root / "wl.json"
        code, out = _run_main(
            lint_reports.main, ["lint_reports.py", "--whitelist", str(wl)])
        self.assertEqual(code, 1)
        self.assertIn("lint 失败", out)

    def test_main_warnings_return_2(self):
        self._one_report("2026-11-demo.html", '<img src="x.png">')
        wl = self.root / "wl.json"
        code, out = _run_main(
            lint_reports.main, ["lint_reports.py", "--whitelist", str(wl)])
        self.assertEqual(code, 2)
        self.assertIn("不阻断", out)

    def test_main_skip_whitelist_and_new_only(self):
        self._one_report("2026-10-demo.html", "<html></html>")
        wl = self.root / "wl.json"
        code, out = _run_main(
            lint_reports.main,
            ["lint_reports.py", "--whitelist", str(wl), "--new-only"])
        self.assertEqual(code, 0)
        self.assertIn("[SKIP] 01-demo/reports/2026-10-demo.html（历史报告）", out)

    def test_main_whitelist_skip_message(self):
        self._one_report("2026-11-demo.html", "<html></html>")
        wl = _write(self.root / "wl.json", json.dumps(
            [{"report": "01-demo/reports/2026-11-demo.html", "reason": "r",
              "review_by": "2999-01-01"}]))
        code, out = _run_main(
            lint_reports.main, ["lint_reports.py", "--whitelist", str(wl)])
        self.assertEqual(code, 0)
        self.assertIn("（白名单豁免）", out)


# ══════════════════════════════════════════════════════════════
# fact_card_check.py
# ══════════════════════════════════════════════════════════════
class TestCovComplianceFactCardCheck(_TempRootCase):
    """事实卡片校验（fact_card_check.py）。"""

    def setUp(self):
        super().setUp()
        self.card_path = self.root / "cards.md"
        self.report_path = self.root / "card-report.md"
        self._p1 = mock.patch.object(fact_card_check, "CARD_PATH", self.card_path)
        self._p2 = mock.patch.object(fact_card_check, "REPORT_PATH", self.report_path)
        self._p1.start()
        self._p2.start()
        self.addCleanup(self._p1.stop)
        self.addCleanup(self._p2.stop)

    def test_parse_cards_missing_file(self):
        self.assertEqual(fact_card_check.parse_cards(), {})

    def test_parse_cards_short_row_skipped(self):
        _write(self.card_path, "| FC-001 | 仅四列 |\n")
        self.assertEqual(fact_card_check.parse_cards(), {})

    def test_parse_cards_ok(self):
        _write(self.card_path,
               "| FC-001 | 1 | 口径 | 2026-11 | https://x | v1 |\n")
        cards = fact_card_check.parse_cards()
        self.assertEqual(cards["FC-001"]["值"], "1")
        self.assertEqual(cards["FC-001"]["版本号"], "v1")

    def test_check_fields_missing_and_no_online_source(self):
        cards = {
            "FC-001": {"值": "1", "统计口径": "—", "数据时点": "", "来源 URL": "https://x", "版本号": "v1"},
            "FC-002": {"值": "2", "统计口径": "c", "数据时点": "t", "来源 URL": "无在线来源", "版本号": "v1"},
        }
        issues = fact_card_check.check_fields(cards)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["id"], "FC-001")
        self.assertIn("统计口径", issues[0]["detail"])
        self.assertIn("数据时点", issues[0]["detail"])

    def test_check_pointers_broken(self):
        cards = {"FC-001": {}}
        pointers = {"FC-999": ["01-demo/reports/a.md"]}
        issues = fact_card_check.check_pointers(cards, pointers)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["issue"], "指针失效")

    def test_check_orphans(self):
        cards = {"FC-001": {}, "FC-002": {}}
        pointers = {"FC-001": ["a"]}
        issues = fact_card_check.check_orphans(cards, pointers)
        self.assertEqual([i["id"] for i in issues], ["FC-002"])
        self.assertEqual(issues[0]["level"], "P2")

    def test_collect_pointers_oserror_skipped(self):
        bad = mock.Mock()
        bad.read_text.side_effect = OSError("denied")
        b = mock.Mock()
        b.path.rglob.return_value = [bad]
        with mock.patch.object(fact_card_check, "iter_business_dirs", return_value=[b]):
            self.assertEqual(fact_card_check.collect_pointers(), {})

    def test_collect_pointers_ok(self):
        d = self._business("01-demo")
        _write(d / "reports" / "a.md", "见 [@FC-001] 与 [@FC-002]。")
        pointers = fact_card_check.collect_pointers()
        self.assertEqual(set(pointers), {"FC-001", "FC-002"})
        self.assertTrue(pointers["FC-001"][0].endswith("01-demo/reports/a.md"))

    def test_render_md_no_issues(self):
        md = fact_card_check.render_md([], {"cards": 0, "pointers": 0, "fact_dup_ratio": 0.0})
        self.assertIn("（无问题）", md)

    def test_render_md_with_issues(self):
        issues = [{"id": "FC-001", "level": "P1", "issue": "五字段缺失", "detail": "值"}]
        md = fact_card_check.render_md(issues, {"cards": 1, "pointers": 1, "fact_dup_ratio": 0.0})
        self.assertIn("| FC-001 | P1 | 五字段缺失 | 值 |", md)

    def test_main_json(self):
        with mock.patch.object(fact_card_check, "run",
                               return_value=([], {"cards": 1, "pointers": 1, "fact_dup_ratio": 0.0})):
            code, out = _run_main(fact_card_check.main, ["fact_card_check.py", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["summary"]["cards"], 1)

    def test_main_write(self):
        with mock.patch.object(fact_card_check, "run",
                               return_value=([], {"cards": 1, "pointers": 1, "fact_dup_ratio": 0.0})):
            code, out = _run_main(fact_card_check.main, ["fact_card_check.py", "--write"])
        self.assertEqual(code, 0)
        self.assertTrue(self.report_path.exists())
        self.assertIn("报告已写入", out)

    def test_main_exit_codes(self):
        p1 = [{"id": "FC-001", "level": "P1", "issue": "x", "detail": "y"}]
        with mock.patch.object(fact_card_check, "run",
                               return_value=(p1, {"cards": 1, "pointers": 1, "fact_dup_ratio": 0.0})):
            code, _ = _run_main(fact_card_check.main, ["fact_card_check.py"])
        self.assertEqual(code, 1)
        p2 = [{"id": "FC-002", "level": "P2", "issue": "x", "detail": "y"}]
        with mock.patch.object(fact_card_check, "run",
                               return_value=(p2, {"cards": 1, "pointers": 1, "fact_dup_ratio": 0.0})):
            code, _ = _run_main(fact_card_check.main, ["fact_card_check.py"])
        self.assertEqual(code, 2)


# ══════════════════════════════════════════════════════════════
# info_quality_check.py
# ══════════════════════════════════════════════════════════════
class TestCovComplianceInfoQualityPure(_TempRootCase):
    """info_quality_check.py 纯函数。"""

    def test_norm_similar_paragraphs_substantive(self):
        self.assertEqual(iqc._norm("a `b`  c　"), "abc")
        self.assertEqual(iqc._similar("abc", "abc"), 1.0)
        self.assertEqual(iqc._paragraphs("a\n\nb"), ["a", "b"])
        self.assertFalse(iqc._substantive("| a | b |"))
        self.assertFalse(iqc._substantive("## 标题"))
        self.assertTrue(iqc._substantive("x" * 40))
        self.assertFalse(iqc._substantive("短"))

    def test_strip_badges(self):
        text = "> **已审计**：2026-11-01 通过\n正文"
        self.assertEqual(iqc._strip_badges(text), "\n正文")

    def test_fact_units_paras_and_rows(self):
        text = ("含数字 123 的实质段落，长度需要超过四十字符才会被判定为实质性段落，"
                "此处内容足够长以通过阈值判定，包含更多文字。\n\n"
                "| # | 指标 | 值 |\n|---|---|---|\n| 1 | 测试 | 456 |\n")
        paras, rows = iqc._fact_units(text)
        self.assertEqual(len(paras), 1)
        self.assertEqual(len(rows), 1)
        self.assertIn("456", rows[0])

    def test_split_row(self):
        self.assertEqual(iqc._split_row("| a | b |"), ["a", "b"])

    def test_live_table_none_and_skip(self):
        self.assertIsNone(iqc._live_table("无表格"))
        self.assertIsNone(iqc._live_table("| # | 名称 | 值 |\n|---|---|---|\n| 1 | a | 2 |"))
        hdr, rows = iqc._live_table(
            "| # | 指标 | 口径 | 最新值 / 规则 |\n|---|---|---|---|\n| 1 | 测试 | c | 1 |\n")
        self.assertEqual(hdr[1], "指标")
        self.assertEqual(rows, [["1", "测试", "c", "1"]])

    def test_registry_calibers_branches(self):
        self.assertEqual(iqc._registry_calibers("无表格"), {})
        new = ("| # | 指标 | 口径 | 最新值 / 规则 |\n|---|---|---|---|\n"
               "| 1 | 测试 | 口径A | 1 |\n| x | 非数字 | 口径B | 2 |\n"
               "| 2 |  | 空名 | 3 |\n")
        self.assertEqual(iqc._registry_calibers(new), {"测试": "口径A"})
        old = ("| # | 指标 | 优先数据源 | 最新值（来源/年份） | 基准版本 |\n"
               "|---|---|---|---|---|\n| 1 | 测试 | 厚労省 | 341,158 円（口径：现金给与总额） | v2026.11.12_5 |\n")
        self.assertEqual(iqc._registry_calibers(old), {"测试": "厚労省｜现金给与总额"})

    def test_registry_latest_date_branches(self):
        self.assertIsNone(iqc.registry_latest_date("无表格"))
        text = ("| # | 指标 | 口径 | 核验日期 | 版本日期 |\n|---|---|---|---|---|\n"
                "| 1 | 测试 | c | 2026-11-14 | 2026-13-40 |\n")
        self.assertEqual(iqc.registry_latest_date(text), date(2026, 11, 14))

    def test_significant_numbers(self):
        self.assertEqual(iqc._significant_numbers("2026.11 版本 3 与 341,158 円（+4.9%）"),
                         {"341158", "4.9"})

    def test_report_value_rows(self):
        self.assertEqual(iqc._report_value_rows("无表格"), {})
        text = ("## 数据变更摘要\n\n"
                "| # | 指标 | 本版活值（来源 · 时点） | 变更状态 |\n|---|---|---|---|\n"
                "| 1 | 测试 | 341,158 円 | 已更新 |\n")
        self.assertEqual(iqc._report_value_rows(text), {1: "341,158 円"})

    def test_rel_value_error(self):
        outside = Path(self.root).parent / "elsewhere" / "x.md"
        self.assertEqual(iqc._rel(outside), str(outside))

    def test_check_disclaimer(self):
        self.assertFalse(iqc.check_disclaimer("无")[0])
        partial = "免责声明 不构成法律意见 专业人士"
        self.assertFalse(iqc.check_disclaimer(partial)[0])
        full = "免责声明 不构成法律意见 专业人士 税务"
        self.assertTrue(iqc.check_disclaimer(full)[0])

    def test_empty_module_ratio(self):
        self.assertEqual(iqc.empty_module_ratio("无标题"), (0, 0))
        text = "## 一、有\n\n内容\n\n## 二、空\n\n## 三、有\n\n内容\n"
        self.assertEqual(iqc.empty_module_ratio(text), (1, 3))

    def test_fact_blocks_skips_code(self):
        text = ("```\n代码 123\n```\n\n"
                "正文含数字 456，长度需要超过十二字符才被判定为事实片段，此处足够长。")
        blocks = iqc._fact_blocks(text)
        self.assertEqual(len(blocks), 1)
        self.assertIn("456", blocks[0])

    def test_fact_duplication(self):
        self.assertEqual(iqc.fact_duplication([]), (0.0, []))
        d1 = self._business("01-demo")
        d2 = self._business("02-other")
        para = ("跨报告重复事实片段，长度需要超过十二字符才被判定，此处足够长，包含数字 789，"
                "再补充一些文字以确保被识别。")
        _write(d1 / "reports" / "2026-11-demo.md", para)
        _write(d2 / "reports" / "2026-11-other.md", para)
        units = [
            {"topic": "01-demo", "slug": "demo", "path": d1, "reports": [d1 / "reports" / "2026-11-demo.md"]},
            {"topic": "02-other", "slug": "other", "path": d2, "reports": [d2 / "reports" / "2026-11-other.md"]},
        ]
        rate, details = iqc.fact_duplication(units)
        self.assertGreater(rate, 0.0)
        self.assertEqual(len(details), 1)


class TestCovComplianceInfoQualityChecks(_TempRootCase):
    """info_quality_check.py 检查函数。"""

    def test_check_topic_completeness_missing(self):
        u = {"topic": "01-demo", "slug": "demo", "path": self.root / "01-demo",
             "has_config": False, "registry": None, "reports": [], "has_guide": False}
        findings = []
        present, total = iqc.check_topic_completeness(u, findings)
        self.assertEqual((present, total), (0, 4))
        self.assertEqual(len(findings), 4)
        self.assertTrue(all(f.code == "C-06" for f in findings))

    def test_check_topic_completeness_all_present(self):
        d = self._business("01-demo")
        reg = _write(d / "data" / "demo_indicator_registry.md", "# reg\n")
        _write(d / "reports" / "2026-11-demo.md", "# r\n")
        _write(d / "operations-guide.md", "# g\n")
        u = {"topic": "01-demo", "slug": "demo", "path": d, "has_config": True,
             "registry": reg, "reports": [d / "reports" / "2026-11-demo.md"], "has_guide": True}
        findings = []
        present, total = iqc.check_topic_completeness(u, findings)
        self.assertEqual((present, total), (4, 4))
        self.assertEqual(findings, [])

    def _report_unit(self, text: str, registry_text: str | None = None):
        d = self._business("01-demo")
        rp = _write(d / "reports" / "2026-11-demo.md", text)
        _write(d / "reports" / "2026-11-demo.html", "<html></html>")
        reg = None
        if registry_text is not None:
            reg = _write(d / "data" / "demo_indicator_registry.md", registry_text)
        u = {"topic": "01-demo", "slug": "demo", "path": d, "registry": reg}
        return u, rp

    def test_check_report_branches(self):
        reg = ("| # | 指标 | 优先数据源 | 最新值（来源/年份） | 基准版本 |\n"
               "|---|---|---|---|---|\n| 1 | 测试 | 厚労省 | 341,158 円 | v2020.01.01_5 |\n")
        text = (
            "# 标题\n\n"
            "## 一、执行摘要\n\n"
            "结论：测试 123。\n\n"
            "## 二、正文\n\n"
            "第一段含数字 456 但未标注出处，用于触发覆盖率不足，需要足够长度才能被判定为实质段落，此处再补充文字确保超过阈值。\n\n"
            "## 二、正文\n\n"
            "重复标题。\n\n"
            "## 四、后续观察\n\n"
            "内容。\n\n"
            "## 五、参考来源清单\n\n"
            "- [来源](https://example.com)\n")
        u, rp = self._report_unit(text, reg)
        findings = []
        stats = iqc.check_report(u, rp, findings)
        codes = {f.code for f in findings}
        self.assertIn("C-06", codes)   # 免责声明缺失
        self.assertIn("C-02", codes)   # 重复标题
        self.assertIn("C-04", codes)   # 序号跳号
        self.assertIn("C-07", codes)   # 来源覆盖率不足
        self.assertIn("C-08", codes)   # 登记册过期
        self.assertEqual(stats["subs"], 1)
        self.assertEqual(stats["source_cov"], 0.0)

    def test_check_report_slug_mismatch(self):
        u, rp = self._report_unit("# 标题\n\n## 一、结论\n\n结论 1。\n")
        u["slug"] = "other"
        findings = []
        iqc.check_report(u, rp, findings)
        self.assertTrue(any(f.code == "C-05" for f in findings))

    def test_check_grade_annotations(self):
        u = {"topic": "01-demo"}
        text = "## ④ 来源\n\n1. 某来源\n\n## ④ 只读引用\n\n1. 引用\n"
        findings = []
        iqc.check_grade_annotations(u, "01-demo/reports/x.md", text, findings)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "C-14")
        self.assertIn("④", findings[0].detail)

    def test_check_value_sync_branches(self):
        # 无登记册
        u = {"topic": "01-demo", "registry": None}
        findings = []
        iqc.check_value_sync(u, self.root / "x.md", "文本", findings)
        self.assertEqual(findings, [])
        # 登记册无活值表
        reg = _write(self.root / "reg.md", "# 无表\n")
        u = {"topic": "01-demo", "registry": reg}
        findings = []
        iqc.check_value_sync(u, self.root / "x.md", "文本", findings)
        self.assertEqual(findings, [])
        # 活值表无「最新值」列
        reg2 = _write(self.root / "reg2.md", "| # | 指标 | 口径 |\n|---|---|---|\n| 1 | 测试 | c |\n")
        u = {"topic": "01-demo", "registry": reg2}
        findings = []
        iqc.check_value_sync(u, self.root / "x.md", "文本", findings)
        self.assertEqual(findings, [])
        # 数值不一致
        reg3 = _write(self.root / "reg3.md",
                      "| # | 指标 | 口径 | 最新值 / 规则 |\n|---|---|---|---|\n| 1 | 测试 | c | 341,158 円 |\n")
        u = {"topic": "01-demo", "registry": reg3}
        text = ("## 数据变更摘要\n\n"
                "| # | 指标 | 本版活值（来源 · 时点） | 变更状态 |\n|---|---|---|---|\n"
                "| 1 | 测试 | 999,999 円 | 已更新 |\n")
        findings = []
        iqc.check_value_sync(u, self.root / "x.md", text, findings)
        self.assertTrue(any(f.code == "C-13" and "341158" in f.detail for f in findings))

    def test_check_cross_topic_broken_and_skips(self):
        t1 = self._business("01-demo")
        t2 = self._business("02-other")
        md1 = _write(t1 / "prompts" / "a.md",
                     "[a](https://example.com)\n"
                     "[b]({{REGION}}/x.md)\n"
                     "[c](<slug>.md)\n"
                     "[d](  )\n"
                     "[e](#anchor)\n"
                     "[f](../../missing.md)\n"
                     "[g](../../a）b.md)\n")
        units = [
            {"topic": "01-demo", "slug": "demo", "path": t1, "mds": [md1], "reports": [], "registry": None},
            {"topic": "02-other", "slug": "other", "path": t2, "mds": [], "reports": [], "registry": None},
        ]
        findings = []
        stats = iqc.check_cross_topic(units, findings)
        self.assertIn("C-09", [f.code for f in findings])
        self.assertEqual(stats["total_links"], 2)
        self.assertEqual(stats["broken_links"], 2)

    def test_check_cross_topic_c10_conflict(self):
        t1 = self._business("01-demo")
        t2 = self._business("02-other")
        reg1 = _write(t1 / "data" / "demo_indicator_registry.md",
                      "| # | 指标 | 口径 | 最新值 / 规则 |\n|---|---|---|---|\n| 1 | 测试 | 口径A | 1 |\n")
        reg2 = _write(t2 / "data" / "other_indicator_registry.md",
                      "| # | 指标 | 口径 | 最新值 / 规则 |\n|---|---|---|---|\n| 1 | 测试 | 口径B | 1 |\n")
        units = [
            {"topic": "01-demo", "slug": "demo", "path": t1, "mds": [], "reports": [], "registry": reg1},
            {"topic": "02-other", "slug": "other", "path": t2, "mds": [], "reports": [], "registry": reg2},
        ]
        findings = []
        iqc.check_cross_topic(units, findings)
        self.assertTrue(any(f.code == "C-10" for f in findings))

    def test_check_cross_topic_c03_cross_doc(self):
        t1 = self._business("01-demo")
        t2 = self._business("02-other")
        para = ("跨文档重复段落，长度需要超过一百二十字才能触发相似度判定，"
                "此处重复写入两个主题的研究正文，用于验证 C-03 跨文档重复分支，"
                "并确保归一化后相似度达到百分之八十以上的阈值，从而被程序标记为疑似重复，"
                "因此需要再补充一些内容使段落长度超过阈值，保证检测分支被触发。")
        _write(t1 / "reports" / "2026-11-demo.md", para)
        _write(t2 / "reports" / "2026-11-other.md", para)
        units = [
            {"topic": "01-demo", "slug": "demo", "path": t1, "mds": [],
             "reports": [t1 / "reports" / "2026-11-demo.md"], "registry": None},
            {"topic": "02-other", "slug": "other", "path": t2, "mds": [],
             "reports": [t2 / "reports" / "2026-11-other.md"], "registry": None},
        ]
        findings = []
        iqc.check_cross_topic(units, findings)
        self.assertTrue(any(f.code == "C-03" and f.location == "跨文档重复" for f in findings))


class TestCovComplianceInfoQualityRepair(_TempRootCase):
    """info_quality_check.py 修复函数。"""

    def test_insert_disclaimer_ok_returns_none(self):
        p = _write(self.root / "r.md", "免责声明 不构成法律意见 专业人士 税务\n")
        self.assertIsNone(iqc._insert_disclaimer(p))

    def test_dedupe_within_file_none_and_relative(self):
        p = _write(self.root / "r.md", "唯一段落，无重复。\n")
        self.assertIsNone(iqc._dedupe_within_file(p))
        dup = ("重复段落，长度需要超过四十字符才能被判定为实质性段落，此处足够长，包含数字 1，"
               "再补充文字确保通过阈值判定。\n\n"
               "重复段落，长度需要超过四十字符才能被判定为实质性段落，此处足够长，包含数字 1，"
               "再补充文字确保通过阈值判定。\n")
        rel = Path("01-demo/reports/2026-11-demo.md")
        _write(self.root / rel, dup)
        with mock.patch.object(iqc, "_read", return_value=dup):
            rep = iqc._dedupe_within_file(rel)
        self.assertIsNotNone(rep)
        self.assertEqual(rep.spec, "S-02")
        self.assertEqual((self.root / rel).read_text(encoding="utf-8").count("重复段落"), 1)

    def test_repoint_no_change(self):
        p = _write(self.root / "r.md", "无目标\n")
        self.assertIsNone(iqc._repoint(p, "不存在", self.root / "t.md"))

    def test_fix_link_branches(self):
        self.assertIsNone(iqc._fix_link(self.root / "r.md", ""))
        # 精确唯一
        target = _write(self.root / "01-demo" / "reports" / "missing.md", "# t\n")
        p = _write(self.root / "01-demo" / "reports" / "a.md", "[x](../reports/missing.md)\n")
        rep = iqc._fix_link(p, "../reports/missing.md")
        self.assertIsNotNone(rep)
        self.assertIn("missing.md", rep.after)
        # 归档副本回落
        base = _write(self.root / "01-demo" / "reports" / "X.md", "# x\n")
        p2 = _write(self.root / "01-demo" / "reports" / "b.md", "[x](../reports/X-merged-v1.0.md)\n")
        rep2 = iqc._fix_link(p2, "../reports/X-merged-v1.0.md")
        self.assertIsNotNone(rep2)
        self.assertIn("X.md", rep2.after)
        # 无匹配
        p3 = _write(self.root / "01-demo" / "reports" / "c.md", "[x](nope.md)\n")
        self.assertIsNone(iqc._fix_link(p3, "nope.md"))
        self.assertTrue(target.exists() and base.exists())

    def test_os_relpath(self):
        self.assertEqual(iqc.os_relpath(self.root / "a" / "b.md", self.root), "a/b.md")

    def test_topic_slug_of(self):
        self.assertEqual(iqc.topic_slug_of("01-demo"), "demo")
        self.assertEqual(iqc.topic_slug_of("tokyo/office"), "tokyo")

    def _finding(self, code, path, detail, level="P1"):
        return iqc.Finding(code, level, "01-demo", path, "位置", detail, "S-05")

    def test_repair_c06_branches(self):
        # business-config 缺失 → 补建
        f1 = self._finding("C-06", "01-demo/prompts/business-config.md", "缺少业务配置")
        # 登记册缺失 → 补建
        f2 = self._finding("C-06", "01-demo/data/", "缺少指标登记册")
        # 报告缺失 → unfixable
        f3 = self._finding("C-06", "01-demo/reports/", "缺少月度报告")
        # 操作指南缺失 → 补建
        f4 = self._finding("C-06", "01-demo/operations-guide.md", "缺少操作指南")
        # HTML 缺失 → unfixable
        f5 = self._finding("C-06", "01-demo/reports/2026-11-demo.md", "缺少对应 HTML 交付物")
        # 其它 → unfixable
        f6 = self._finding("C-06", "01-demo/other", "其它问题")
        repairs = iqc.repair([f1, f2, f3, f4, f5, f6], [])
        specs = {r.spec for r in repairs}
        self.assertIn("S-05", specs)
        self.assertEqual(len(repairs), 3)   # config / registry / guide
        self.assertTrue((self.root / "01-demo" / "prompts" / "business-config.md").exists())
        self.assertTrue((self.root / "01-demo" / "data" / "demo_indicator_registry.md").exists())
        self.assertTrue((self.root / "01-demo" / "operations-guide.md").exists())
        self.assertEqual(f3.status, "unfixable")
        self.assertEqual(f5.status, "unfixable")
        self.assertEqual(f6.status, "unfixable")

    def test_repair_c03_c09_other(self):
        # C-03 跨文档 → 跳过
        f_cross = self._finding("C-03", "01-demo/reports/a.md", "跨文档重复")
        # C-03 同文档 → 去重
        dup = ("重复段落，长度需要超过四十字符才能被判定为实质性段落，此处足够长，包含数字 2，"
               "再补充文字确保通过阈值判定。\n\n"
               "重复段落，长度需要超过四十字符才能被判定为实质性段落，此处足够长，包含数字 2，"
               "再补充文字确保通过阈值判定。\n")
        _write(self.root / "01-demo" / "reports" / "2026-11-demo.md", dup)
        f_dup = self._finding("C-03", "01-demo/reports/2026-11-demo.md", "同一实质段落在本文件内重复 2 次")
        # C-09 失效引用 → 重指
        _write(self.root / "01-demo" / "reports" / "missing.md", "# t\n")
        _write(self.root / "01-demo" / "reports" / "b.md", "[x](../reports/missing.md)\n")
        f_link = self._finding("C-09", "01-demo/reports/b.md", "引用目标不存在：../reports/missing.md")
        # C-01 → unfixable
        f_other = self._finding("C-01", "01-demo/reports/c.md", "语义问题")
        # 非 open 状态 → 跳过
        f_closed = self._finding("C-06", "01-demo/reports/d.md", "已处理")
        f_closed.status = "fixed"
        repairs = iqc.repair([f_cross, f_dup, f_link, f_other, f_closed], [])
        self.assertEqual(len(repairs), 2)
        self.assertEqual(f_cross.status, "open")
        self.assertEqual(f_dup.status, "fixed")
        self.assertEqual(f_link.status, "fixed")
        self.assertEqual(f_other.status, "unfixable")
        self.assertEqual(f_closed.status, "fixed")

    def test_merge_findings(self):
        f1 = self._finding("C-01", "01-demo/reports/a.md", "问题")
        f2 = self._finding("C-02", "01-demo/reports/b.md", "新问题")
        merged = iqc._merge_findings([f1], [])
        self.assertEqual(merged[0].status, "fixed")
        updated = self._finding("C-01", "01-demo/reports/a.md", "问题")
        updated.level = "P2"
        merged2 = iqc._merge_findings([f1], [updated, f2])
        self.assertEqual(len(merged2), 2)
        self.assertEqual(merged2[0].level, "P2")
        self.assertIn(f2, merged2)

    def test_write_reports(self):
        f = self._finding("C-06", "01-demo/reports/a.md", "缺少免责声明")
        r = iqc.Repair("C-06", "01-demo", "01-demo/reports/a.md", "S-05",
                       "插入免责声明", "（缺失）", "已插入")
        before = iqc.Metrics(topics_total=1, findings_by_level={"P0": 0, "P1": 1, "P2": 0})
        after = iqc.Metrics(topics_total=1, findings_by_level={"P0": 0, "P1": 0, "P2": 0})
        ver = {"checks": {"ok": True}, "passed": True}
        paths = iqc.write_reports([f], [r], before, after, ver, "2026-11-17")
        names = {p.name for p in paths}
        self.assertEqual(names, {"assessment-ledger.md", "repair-ledger.md",
                                 "verification-report.md", "info-quality.json",
                                 "repair-history.md"})
        self.assertIn("信息质量评估台账", (iqc.AUDIT_DIR / "assessment-ledger.md").read_text(encoding="utf-8"))
        payload = json.loads((iqc.AUDIT_DIR / "info-quality.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["run_date"], "2026-11-17")

    def test_run_no_units(self):
        with mock.patch.object(iqc, "scan_topics", return_value=[]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = iqc.run()
        self.assertEqual(code, 1)
        self.assertIn("未扫描到任何主题目录", buf.getvalue())

    def test_run_pass_no_write(self):
        metrics = iqc.Metrics(topics_total=1, findings_by_level={"P0": 0, "P1": 0, "P2": 0})
        with mock.patch.object(iqc, "scan_topics", return_value=[{"topic": "01-demo"}]), \
             mock.patch.object(iqc, "evaluate", return_value=([], metrics)):
            code = iqc.run(apply=False, write=False)
        self.assertEqual(code, 0)

    def test_run_p2_returns_2(self):
        f = self._finding("C-06", "01-demo/reports/a.md", "提示", level="P2")
        metrics = iqc.Metrics(topics_total=1, findings_by_level={"P0": 0, "P1": 0, "P2": 1})
        with mock.patch.object(iqc, "scan_topics", return_value=[{"topic": "01-demo"}]), \
             mock.patch.object(iqc, "evaluate", return_value=([f], metrics)):
            code = iqc.run(apply=False, write=False)
        self.assertEqual(code, 2)

    def test_main(self):
        with mock.patch.object(iqc, "run", return_value=0) as m:
            code, _ = _run_main(iqc.main, ["info_quality_check.py", "--check"])
        self.assertEqual(code, 0)
        m.assert_called_once_with(apply=False, write=False)
        with mock.patch.object(iqc, "run", return_value=1) as m2:
            code, _ = _run_main(iqc.main, ["info_quality_check.py", "--apply"])
        self.assertEqual(code, 1)
        m2.assert_called_once_with(apply=True, write=True)


if __name__ == "__main__":
    unittest.main()
