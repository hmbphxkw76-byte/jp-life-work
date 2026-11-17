"""编排 / 决策支持工具链补充单元测试（覆盖率缺口）。

只读、hermetic：全部用 tempfile + unittest.mock，不写真实仓库、不联网。
覆盖 pipeline_runner / pipeline_status / trigger_watch / update_planner /
automation_status / decision_log / stage_gate_check / pending_verification /
personal_finance_model / _common 中尚未被既有测试触及的纯函数与 CLI 分支。

运行：python -m unittest src.tests.test_cov_pipeline -v
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
import unittest.mock
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "prompts-tools" / "tools"))

import _common  # noqa: E402
import automation_status  # noqa: E402
import decision_log  # noqa: E402
import pending_verification  # noqa: E402
import personal_finance_model  # noqa: E402
import pipeline_runner  # noqa: E402
import pipeline_status  # noqa: E402
import stage_gate_check  # noqa: E402
import trigger_watch  # noqa: E402
import update_planner  # noqa: E402

UTC = timezone.utc


def _capture(argv, func, *args, **kwargs):
    """以指定 argv 调用 CLI 入口，返回 (返回码, stdout, stderr)。"""
    out, err = io.StringIO(), io.StringIO()
    with unittest.mock.patch.object(sys, "argv", argv), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = func(*args, **kwargs)
    return rc, out.getvalue(), err.getvalue()


# ──────────────────────────────────────────────
# _common：周期解析 / 命名 / 状态层 / 渲染
# ──────────────────────────────────────────────
class TestCovPipelineCommon(unittest.TestCase):
    def test_month_to_date_end_of_month(self):
        self.assertEqual(_common.month_to_date("2026-11"), "2026-11-30")
        self.assertEqual(_common.month_to_date("2026-02"), "2026-02-28")
        self.assertEqual(_common.month_to_date("2024-02"), "2024-02-29")

    def test_month_to_date_invalid(self):
        for bad in ("2026-13", "2026-00", "2026-1", "abc", ""):
            self.assertEqual(_common.month_to_date(bad), "", bad)

    def test_report_title(self):
        self.assertEqual(_common.report_title("<title>Hello</title>"), "Hello")
        self.assertEqual(_common.report_title("<title>  A\n   B </title>"), "A B")
        self.assertEqual(_common.report_title("<html><body>x</body></html>"), "")

    def test_md_table(self):
        out = _common.md_table([["a", "b"], ["1", "2"], ["3", "4"]])
        lines = out.splitlines()
        self.assertEqual(lines[0], "| a | b |")
        self.assertEqual(lines[1], "|---|---|")
        self.assertEqual(lines[2], "| 1 | 2 |")
        self.assertEqual(lines[3], "| 3 | 4 |")

    def test_link_prefix(self):
        self.assertEqual(_common.link_prefix(_common.ROOT / "index.md"), "")
        deep = _common.ROOT / "src" / "report-audits" / "pipeline" / "status.md"
        self.assertEqual(_common.link_prefix(deep), "../../../")

    def test_business_single_level(self):
        b = _common.Business("01-ssw-driver")
        self.assertEqual(b.region, "01-ssw-driver")
        self.assertEqual(b.property_type, "")
        self.assertEqual(b.rel, "01-ssw-driver")
        self.assertEqual(b.path, _common.ROOT / "01-ssw-driver")

    def test_business_two_level(self):
        b = _common.Business("region", "type")
        self.assertEqual(b.rel, "region/type")
        self.assertEqual(b.path, _common.ROOT / "region" / "type")

    def test_iter_business_dirs_temp_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "01-demo" / "prompts").mkdir(parents=True)
            (root / "02-two" / "reports").mkdir(parents=True)
            (root / "03-nested" / "sub" / "data").mkdir(parents=True)
            (root / "04-cfg" / "prompts").mkdir(parents=True)
            (root / "04-cfg" / "prompts" / "business-config.md").write_text("", encoding="utf-8")
            (root / "src").mkdir()
            (root / ".git").mkdir()
            with unittest.mock.patch.object(_common, "ROOT", root):
                rels = [b.rel for b in _common.iter_business_dirs()]
        self.assertIn("01-demo", rels)
        self.assertIn("02-two", rels)
        self.assertIn("03-nested/sub", rels)
        self.assertIn("04-cfg", rels)
        self.assertNotIn("src", rels)
        self.assertNotIn(".git", rels)

    def test_iter_business_dirs_missing_root(self):
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(_common, "ROOT", Path(d) / "nope"):
                self.assertEqual(_common.iter_business_dirs(), [])

    def test_detect_legacy_special(self):
        self.assertEqual(
            _common.detect_legacy_report("2026-11-13_flash-note.md"),
            ("special", "2026-11-13", "md"),
        )
        self.assertEqual(
            _common.detect_legacy_report("2026-11-13_initial_analysis_report.md")[0],
            "initial",
        )

    def test_quarter_to_month_invalid(self):
        self.assertIsNone(_common.quarter_to_month(""))
        self.assertIsNone(_common.quarter_to_month("2026-Q5"))
        self.assertIsNone(_common.quarter_to_month("2026-11"))

    def test_tasks_for_period_quarter_and_year(self):
        self.assertEqual(
            _common.tasks_for_period("quarter", 2026, 3),
            [("quarterly", 2026, 3)],
        )
        self.assertEqual(
            _common.tasks_for_period("year", 2026, None),
            [("annual", 2026, None)],
        )


# ──────────────────────────────────────────────
# pipeline_status：监控视图
# ──────────────────────────────────────────────
class TestCovPipelineStatus(unittest.TestCase):
    def test_latest_period(self):
        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d)
            (pdir / "state-2026-09.json").write_text("{}", encoding="utf-8")
            (pdir / "state-2026-11.json").write_text("{}", encoding="utf-8")
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", pdir):
                self.assertEqual(pipeline_status._latest_period(), "2026-11")

    def test_latest_period_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
                self.assertEqual(pipeline_status._latest_period(), "")

    def test_audit_distribution(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "audit-status.json"
            f.write_text(json.dumps({"reports": {
                "a.md": {"state": "audited"},
                "b.md": {"state": "pending"},
                "c.md": {"state": "audited"},
                "d.md": {},
                "e.md": "notdict",
            }}), encoding="utf-8")
            with unittest.mock.patch.object(pipeline_status, "AUDIT_STATUS_PATH", f):
                dist = pipeline_status._audit_distribution()
        self.assertEqual(dist["total"], 5)
        self.assertEqual(dist["states"], {"audited": 2, "pending": 1, "unknown": 1})

    def test_audit_distribution_missing_and_corrupt(self):
        with tempfile.TemporaryDirectory() as d:
            missing = Path(d) / "none.json"
            with unittest.mock.patch.object(pipeline_status, "AUDIT_STATUS_PATH", missing):
                self.assertEqual(
                    pipeline_status._audit_distribution(), {"total": 0, "states": {}})
            corrupt = Path(d) / "bad.json"
            corrupt.write_text("{bad", encoding="utf-8")
            with unittest.mock.patch.object(pipeline_status, "AUDIT_STATUS_PATH", corrupt):
                self.assertEqual(
                    pipeline_status._audit_distribution(), {"total": 0, "states": {}})
            nondict = Path(d) / "arr.json"
            nondict.write_text("[]", encoding="utf-8")
            with unittest.mock.patch.object(pipeline_status, "AUDIT_STATUS_PATH", nondict):
                self.assertEqual(
                    pipeline_status._audit_distribution(), {"total": 0, "states": {}})

    def test_latest_heartbeat(self):
        records = {"records": [
            {"phase": "a", "result": "success", "timestamp": "2026-01-01T00:00:00+00:00"},
            {"phase": "b", "result": "failure", "timestamp": "2026-02-01T00:00:00+00:00"},
        ]}
        with unittest.mock.patch.object(automation_status, "load_status", return_value=records):
            hb = pipeline_status._latest_heartbeat()
        self.assertEqual(hb["phase"], "b")
        self.assertEqual(hb["result"], "failure")
        self.assertEqual(hb["timestamp"], "2026-02-01T00:00:00+00:00")

    def test_latest_heartbeat_empty(self):
        with unittest.mock.patch.object(
                automation_status, "load_status", return_value={"records": []}):
            self.assertIsNone(pipeline_status._latest_heartbeat())

    def test_collect_defaults_to_latest_period(self):
        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d)
            st = _common.new_state("2026-11")
            st["stages"] = {"S0_detect": {"status": "completed"}}
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", pdir):
                _common.save_state("2026-11", st)
                payload = pipeline_status.collect()
        self.assertEqual(payload["period"], "2026-11")
        self.assertEqual(payload["blocking"], "S1_plan")

    def test_render_md_state_error_and_heartbeat(self):
        md = pipeline_status.render_md({
            "period": "2026-11",
            "blocking": "S1_plan",
            "state_error": "损坏",
            "stages": {"S0_detect": {"status": "completed", "completed": "t"}},
            "audit": {"total": 2, "states": {"audited": 2}},
            "heartbeat": {"phase": "pipeline", "result": "success", "timestamp": "ts"},
        })
        self.assertIn("状态文件异常", md)
        self.assertIn("pipeline / success @ ts", md)
        self.assertIn("audited", md)
        self.assertIn("S1_plan", md)

    def test_main_writes_status_files(self):
        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d)
            sj, sm = pdir / "status.json", pdir / "status.md"
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", pdir), \
                    unittest.mock.patch.object(pipeline_status, "STATUS_JSON", sj), \
                    unittest.mock.patch.object(pipeline_status, "STATUS_MD", sm), \
                    unittest.mock.patch.object(
                        pipeline_status, "AUDIT_STATUS_PATH", pdir / "audit-status.json"), \
                    unittest.mock.patch.object(
                        automation_status, "load_status", return_value={"records": []}):
                rc, out, _ = _capture(
                    ["pipeline_status.py", "--period", "2099-01"], pipeline_status.main)
            self.assertEqual(rc, 0)
            self.assertTrue(sj.is_file())
            self.assertTrue(sm.is_file())
            self.assertEqual(json.loads(sj.read_text(encoding="utf-8"))["period"], "2099-01")
            self.assertIn("2099-01", out)

    def test_main_porcelain(self):
        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d)
            sj, sm = pdir / "status.json", pdir / "status.md"
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", pdir), \
                    unittest.mock.patch.object(pipeline_status, "STATUS_JSON", sj), \
                    unittest.mock.patch.object(pipeline_status, "STATUS_MD", sm), \
                    unittest.mock.patch.object(
                        pipeline_status, "AUDIT_STATUS_PATH", pdir / "audit-status.json"), \
                    unittest.mock.patch.object(
                        automation_status, "load_status", return_value={"records": []}):
                rc, out, _ = _capture(
                    ["pipeline_status.py", "--period", "2099-01", "--porcelain"],
                    pipeline_status.main)
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(out)["period"], "2099-01")


# ──────────────────────────────────────────────
# pipeline_runner：编排器
# ──────────────────────────────────────────────
class TestCovPipelineRunner(unittest.TestCase):
    def test_run_tool_success(self):
        proc = unittest.mock.Mock(stdout="out\n", stderr="", returncode=0)
        with unittest.mock.patch.object(
                pipeline_runner.subprocess, "run", return_value=proc) as m:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = pipeline_runner._run_tool("md2html.py")
        self.assertEqual(rc, 0)
        self.assertIn("out", buf.getvalue())
        cmd = m.call_args[0][0]
        self.assertEqual(cmd[0], sys.executable)
        self.assertEqual(cmd[1], str(pipeline_runner.TOOLS_DIR / "md2html.py"))

    def test_run_tool_failure_prints_stderr(self):
        proc = unittest.mock.Mock(stdout="", stderr="boom\n", returncode=3)
        with unittest.mock.patch.object(
                pipeline_runner.subprocess, "run", return_value=proc):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = pipeline_runner._run_tool("auto_verify.py", ["--report", "x"])
        self.assertEqual(rc, 3)
        self.assertIn("boom", err.getvalue())

    def _root_with_reports(self, root):
        for name in ("01-demo", "02-other"):
            d = root / name / "reports"
            d.mkdir(parents=True)
            (d / f"2026-11-{name.split('-')[1]}.md").write_text("", encoding="utf-8")

    def test_period_reports(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._root_with_reports(root)
            with unittest.mock.patch.object(_common, "ROOT", root):
                out = pipeline_runner._period_reports("2026-11", None)
        self.assertEqual(out, [
            "01-demo/reports/2026-11-demo.md",
            "02-other/reports/2026-11-other.md",
        ])

    def test_period_reports_project_filter(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._root_with_reports(root)
            with unittest.mock.patch.object(_common, "ROOT", root):
                out = pipeline_runner._period_reports("2026-11", "02-other")
        self.assertEqual(out, ["02-other/reports/2026-11-other.md"])

    def test_s0_detect_counts(self):
        payload = {"window_due": [{"project": "a"}, {"project": "b"}],
                   "stale": [1], "candidates": [1, 2, 3]}
        with unittest.mock.patch.object(trigger_watch, "scan", return_value=payload):
            ok, summary = pipeline_runner._s0_detect("2026-11", None, False)
        self.assertTrue(ok)
        self.assertEqual(summary, {"window_due": 2, "stale": 1, "candidates": 3})

    def test_s0_detect_project_filter(self):
        payload = {"window_due": [{"project": "a"}, {"project": "b"}],
                   "stale": [], "candidates": []}
        with unittest.mock.patch.object(trigger_watch, "scan", return_value=payload):
            ok, summary = pipeline_runner._s0_detect("2026-11", "a", False)
        self.assertTrue(ok)
        self.assertEqual(summary["window_due"], 1)

    def test_s1_plan_pending_count(self):
        tasks = [{"status": "pending", "project": "a"},
                 {"status": "done", "project": "b"}]
        with unittest.mock.patch.object(update_planner, "build_tasks", return_value=tasks), \
                unittest.mock.patch.object(_common, "iter_business_dirs", return_value=[]):
            ok, summary = pipeline_runner._s1_plan("2026-11", None, False)
        self.assertTrue(ok)
        self.assertEqual(summary["pending_count"], 1)
        self.assertEqual(len(summary["pending"]), 1)

    def test_s2_author_todo(self):
        tasks = [
            {"status": "pending", "project": "a", "output": "a/reports/x.html",
             "prompt": "a/prompts/p.md"},
            {"status": "done", "project": "b", "output": "b/reports/y.html",
             "prompt": "b/prompts/q.md"},
        ]
        with unittest.mock.patch.object(update_planner, "build_tasks", return_value=tasks), \
                unittest.mock.patch.object(_common, "iter_business_dirs", return_value=[]):
            ok, summary = pipeline_runner._s2_author("2026-11", None, False)
        self.assertTrue(ok)
        self.assertEqual(summary["gate"], "author")
        self.assertEqual(len(summary["todo"]), 1)
        self.assertEqual(summary["todo"][0]["project"], "a")

    def test_s3_build_dry_run(self):
        with unittest.mock.patch.object(
                pipeline_runner, "_period_reports", return_value=["a.md"]):
            ok, summary = pipeline_runner._s3_build("2026-11", None, True)
        self.assertTrue(ok)
        self.assertEqual(summary["skipped"], ["md2html", "auto_verify"])

    def test_s3_build_no_reports(self):
        with unittest.mock.patch.object(
                pipeline_runner, "_period_reports", return_value=[]):
            ok, summary = pipeline_runner._s3_build("2026-11", None, False)
        self.assertTrue(ok)
        self.assertEqual(summary["note"], "无待生成报告")

    def test_s3_build_md2html_failure(self):
        with unittest.mock.patch.object(
                pipeline_runner, "_period_reports", return_value=["a.md"]), \
                unittest.mock.patch.object(pipeline_runner, "_run_tool", return_value=1):
            ok, summary = pipeline_runner._s3_build("2026-11", None, False)
        self.assertFalse(ok)
        self.assertEqual(summary["stage"], "md2html")

    def test_s3_build_verify_failure(self):
        def fake(name, extra=None):
            if name == "md2html.py":
                return 0
            return 0 if extra and extra[1] == "a.md" else 1

        with unittest.mock.patch.object(
                pipeline_runner, "_period_reports", return_value=["a.md", "b.md"]), \
                unittest.mock.patch.object(pipeline_runner, "_run_tool", side_effect=fake):
            ok, summary = pipeline_runner._s3_build("2026-11", None, False)
        self.assertFalse(ok)
        self.assertEqual(summary["stage"], "auto_verify")
        self.assertEqual(summary["failed"], ["b.md"])

    def test_s3_build_success(self):
        with unittest.mock.patch.object(
                pipeline_runner, "_period_reports", return_value=["a.md"]), \
                unittest.mock.patch.object(pipeline_runner, "_run_tool", return_value=0):
            ok, summary = pipeline_runner._s3_build("2026-11", None, False)
        self.assertTrue(ok)
        self.assertEqual(summary["reports"], ["a.md"])

    def test_s4_audit_dry_run_and_no_reports(self):
        with unittest.mock.patch.object(
                pipeline_runner, "_period_reports", return_value=["a.md"]):
            ok, summary = pipeline_runner._s4_audit("2026-11", None, True)
        self.assertTrue(ok)
        self.assertEqual(summary["skipped"], ["audit_pipeline --submit"])
        with unittest.mock.patch.object(
                pipeline_runner, "_period_reports", return_value=[]):
            ok, summary = pipeline_runner._s4_audit("2026-11", None, False)
        self.assertTrue(ok)
        self.assertEqual(summary["note"], "无待审计报告")

    def test_s4_audit_failure(self):
        with unittest.mock.patch.object(
                pipeline_runner, "_period_reports", return_value=["a.md"]), \
                unittest.mock.patch.object(pipeline_runner, "_run_tool", return_value=1):
            ok, summary = pipeline_runner._s4_audit("2026-11", None, False)
        self.assertFalse(ok)
        self.assertEqual(summary["stage"], "audit_pipeline")
        self.assertEqual(summary["failed"], ["a.md"])

    def test_s5_monitor(self):
        payload = {"blocking": "S2_author", "audit": {"total": 7}}
        with unittest.mock.patch.object(pipeline_status, "collect", return_value=payload):
            ok, summary = pipeline_runner._s5_monitor("2026-11", None, False)
        self.assertTrue(ok)
        self.assertEqual(summary["blocking"], "S2_author")
        self.assertEqual(summary["audit_total"], 7)

    def test_run_invalid_from_stage(self):
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
                self.assertEqual(
                    pipeline_runner.run("2026-11", from_stage="S9_nope"), 2)

    def test_run_stage_failure_returns_1(self):
        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d)
            fake = {"S0_detect": lambda *a: (False, {"err": 1})}
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", pdir), \
                    unittest.mock.patch.object(pipeline_runner, "_STAGE_FUNCS", fake):
                rc = pipeline_runner.run("2026-11")
                self.assertEqual(rc, 1)
                self.assertEqual(
                    _common.load_state("2026-11")["stages"]["S0_detect"]["status"],
                    "failed")

    def test_status_cold_start(self):
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
                st = pipeline_runner.status("2099-01")
        self.assertEqual(st["period"], "2099-01")
        self.assertEqual(st["stages"], {})

    def test_status_reads_saved(self):
        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d)
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", pdir):
                st = _common.new_state("2026-11")
                st["stages"] = {"S0_detect": {"status": "completed"}}
                _common.save_state("2026-11", st)
                loaded = pipeline_runner.status("2026-11")
        self.assertEqual(loaded["stages"]["S0_detect"]["status"], "completed")

    def test_main_status_porcelain(self):
        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d)
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", pdir), \
                    unittest.mock.patch.object(
                        pipeline_status, "AUDIT_STATUS_PATH", pdir / "audit-status.json"), \
                    unittest.mock.patch.object(
                        automation_status, "load_status", return_value={"records": []}):
                rc, out, _ = _capture(
                    ["pipeline_runner.py", "status", "--period", "2099-01", "--porcelain"],
                    pipeline_runner.main)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["period"], "2099-01")

    def test_main_run_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            pdir = Path(d)
            fake = {"S0_detect": lambda *a: (True, {}),
                    "S1_plan": lambda *a: (True, {})}
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", pdir), \
                    unittest.mock.patch.object(pipeline_runner, "_STAGE_FUNCS", fake), \
                    unittest.mock.patch.object(
                        pipeline_runner, "_s2_author", return_value=(True, {"todo": []})):
                rc, out, _ = _capture(
                    ["pipeline_runner.py", "run", "--period", "2026-11", "--dry-run"],
                    pipeline_runner.main)
        self.assertEqual(rc, 0)
        self.assertIn("S2_author", out)

    def test_main_resume_delegates(self):
        with unittest.mock.patch.object(pipeline_runner, "run", return_value=0) as m:
            rc, _, _ = _capture(
                ["pipeline_runner.py", "resume", "--period", "2026-11",
                 "--from-stage", "S3_build"],
                pipeline_runner.main)
        self.assertEqual(rc, 0)
        m.assert_called_once_with("2026-11", None, False, "S3_build")


# ──────────────────────────────────────────────
# trigger_watch：触发检测
# ──────────────────────────────────────────────
class TestCovPipelineTriggerWatch(unittest.TestCase):
    def test_parse_triggers_code_fence(self):
        text = (
            "# 配置\n\n"
            "## 七、触发器\n\n"
            "```\n"
            "- 触发器A\n"
            "- 触发器B\n"
            "```\n\n"
            "- 围栏外不收录\n\n"
            "## 八、其它\n\n"
            "```\n"
            "- 别节不收录\n"
            "```\n"
        )
        self.assertEqual(trigger_watch._parse_triggers(text), ["触发器A", "触发器B"])

    def test_parse_triggers_no_section(self):
        self.assertEqual(trigger_watch._parse_triggers("# 配置\n\n- x\n"), [])

    def test_max_column_date(self):
        text = ("| # | 指标 | 核验日期 |\n|---|---|---|\n"
                "| 1 | A | 2026-01-05 |\n| 2 | B | 2026-03-09 |\n")
        self.assertEqual(trigger_watch._max_column_date(text, "核验日期"), "2026-03-09")

    def test_max_column_date_none_and_table_end(self):
        self.assertIsNone(trigger_watch._max_column_date(
            "| # | 指标 |\n|---|---|\n| 1 | A |", "核验日期"))
        text = ("| # | 核验日期 |\n|---|---|\n| 1 | 2026-01-01 |\n\n"
                "后续文字 2027-01-01\n")
        self.assertEqual(trigger_watch._max_column_date(text, "核验日期"), "2026-01-01")

    def test_registry_last_verified_new_format(self):
        text = "| # | 指标 | 核验日期 |\n|---|---|---|\n| 1 | A | 2026-05-06 |\n"
        self.assertEqual(trigger_watch._registry_last_verified(text), "2026-05-06")

    def test_registry_last_verified_version_fallback(self):
        self.assertEqual(
            trigger_watch._registry_last_verified("基准版本 v2026.03.04_3；旧版 v2025.12.01_1"),
            "2026-03-04",
        )

    def test_registry_last_verified_none(self):
        self.assertIsNone(trigger_watch._registry_last_verified("无日期"))

    def test_find_registry(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = root / "01-demo" / "data"
            data.mkdir(parents=True)
            reg = data / "demo_indicator_registry.md"
            reg.write_text("", encoding="utf-8")
            b = _common.Business("01-demo")
            with unittest.mock.patch.object(_common, "ROOT", root):
                self.assertEqual(trigger_watch._find_registry(b), reg)

    def test_find_registry_no_data_dir(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "01-demo").mkdir(parents=True)
            b = _common.Business("01-demo")
            with unittest.mock.patch.object(_common, "ROOT", root):
                self.assertIsNone(trigger_watch._find_registry(b))

    def test_find_registry_no_match(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = root / "01-demo" / "data"
            data.mkdir(parents=True)
            (data / "other.md").write_text("", encoding="utf-8")
            b = _common.Business("01-demo")
            with unittest.mock.patch.object(_common, "ROOT", root):
                self.assertIsNone(trigger_watch._find_registry(b))

    def test_registry_candidates(self):
        text = ("# 登记册\n\n## 观察项与触发器状态\n\n"
                "| 状态项 | 说明 |\n|---|---|\n"
                "| A | 预计 12 月发布 |\n"
                "| B | 已取得数据 |\n"
                "| C | 未同步 |\n\n## 其它\n")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = root / "01-demo" / "data"
            data.mkdir(parents=True)
            (data / "demo_indicator_registry.md").write_text(text, encoding="utf-8")
            b = _common.Business("01-demo")
            with unittest.mock.patch.object(_common, "ROOT", root):
                out = trigger_watch._registry_candidates(b)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["trigger"], "A：预计 12 月发布")
        self.assertIn("预计", out[0]["keywords"])
        self.assertEqual(out[1]["trigger"], "C：未同步")
        self.assertEqual(out[0]["source"], "01-demo/data/demo_indicator_registry.md")

    def test_registry_candidates_no_section(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = root / "01-demo" / "data"
            data.mkdir(parents=True)
            (data / "demo_indicator_registry.md").write_text("# 登记册\n", encoding="utf-8")
            b = _common.Business("01-demo")
            with unittest.mock.patch.object(_common, "ROOT", root):
                self.assertEqual(trigger_watch._registry_candidates(b), [])

    def test_build_watchlist_temp(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            base = root / "01-demo"
            (base / "prompts").mkdir(parents=True)
            (base / "data").mkdir(parents=True)
            (base / "prompts" / "business-config.md").write_text(
                "## 七、触发器\n\n```\n- 触发器X\n```\n", encoding="utf-8")
            (base / "data" / "demo_indicator_registry.md").write_text(
                "| # | 核验日期 |\n|---|---|\n| 1 | 2026-01-02 |\n", encoding="utf-8")
            with unittest.mock.patch.object(_common, "ROOT", root):
                wl = trigger_watch.build_watchlist()
        self.assertEqual(len(wl), 1)
        self.assertEqual(wl[0]["topic"], "01-demo")
        self.assertEqual(wl[0]["trigger"], "触发器X")
        self.assertEqual(wl[0]["source"], "01-demo/prompts/business-config.md")
        self.assertEqual(wl[0]["last_verified"], "2026-01-02")

    def test_scan_stale(self):
        now = datetime(2026, 12, 20, tzinfo=UTC)
        wl = [{"topic": "01-demo", "trigger": "t", "source": "s",
               "last_verified": "2025-01-01"}]
        with unittest.mock.patch.object(trigger_watch, "build_watchlist", return_value=wl), \
                unittest.mock.patch.object(trigger_watch, "iter_business_dirs", return_value=[]), \
                unittest.mock.patch.object(update_planner, "build_tasks", return_value=[]):
            out = trigger_watch.scan("2026-11", now=now)
        self.assertEqual(len(out["stale"]), 1)
        self.assertEqual(out["stale"][0]["topic"], "01-demo")
        self.assertEqual(out["stale"][0]["threshold_days"], trigger_watch.STALE_DAYS)
        self.assertGreater(out["stale"][0]["age_days"], trigger_watch.STALE_DAYS)

    def test_scan_skips_bad_date(self):
        now = datetime(2026, 12, 20, tzinfo=UTC)
        wl = [{"topic": "01-demo", "trigger": "t", "source": "s",
               "last_verified": "not-a-date"}]
        with unittest.mock.patch.object(trigger_watch, "build_watchlist", return_value=wl), \
                unittest.mock.patch.object(trigger_watch, "iter_business_dirs", return_value=[]), \
                unittest.mock.patch.object(update_planner, "build_tasks", return_value=[]):
            out = trigger_watch.scan("2026-11", now=now)
        self.assertEqual(out["stale"], [])

    def test_scan_collects_candidates(self):
        text = ("# 登记册\n\n## 观察项与触发器状态\n\n"
                "| 状态项 | 说明 |\n|---|---|\n| A | 待核实 |\n")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = root / "01-demo" / "data"
            data.mkdir(parents=True)
            (data / "demo_indicator_registry.md").write_text(text, encoding="utf-8")
            with unittest.mock.patch.object(_common, "ROOT", root), \
                    unittest.mock.patch.object(update_planner, "build_tasks", return_value=[]):
                out = trigger_watch.scan(
                    "2026-11", now=datetime(2026, 12, 20, tzinfo=UTC))
        self.assertEqual(len(out["candidates"]), 1)
        self.assertEqual(out["candidates"][0]["topic"], "01-demo")

    def test_main_with_argv(self):
        payload = {"period": "2026-11", "window_due": [], "stale": [], "candidates": []}
        with unittest.mock.patch.object(trigger_watch, "scan", return_value=payload):
            rc, out, _ = _capture(
                ["trigger_watch.py", "--period", "2026-11", "--report"], trigger_watch.main)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["period"], "2026-11")


# ──────────────────────────────────────────────
# update_planner：任务清单
# ──────────────────────────────────────────────
class TestCovPipelineUpdatePlanner(unittest.TestCase):
    def test_audit_states(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "audit-status.json"
            f.write_text(json.dumps({"reports": {"a.md": {"state": "audited",
                                                          "audit_id": "A1"}}}),
                         encoding="utf-8")
            with unittest.mock.patch.object(update_planner, "AUDIT_STATUS_PATH", f):
                self.assertEqual(
                    update_planner.audit_states(),
                    {"a.md": {"state": "audited", "audit_id": "A1"}})

    def test_audit_states_missing_corrupt_non_dict(self):
        with tempfile.TemporaryDirectory() as d:
            missing = Path(d) / "none.json"
            with unittest.mock.patch.object(update_planner, "AUDIT_STATUS_PATH", missing):
                self.assertEqual(update_planner.audit_states(), {})
            corrupt = Path(d) / "bad.json"
            corrupt.write_text("{bad", encoding="utf-8")
            with unittest.mock.patch.object(update_planner, "AUDIT_STATUS_PATH", corrupt):
                self.assertEqual(update_planner.audit_states(), {})
            nondict = Path(d) / "arr.json"
            nondict.write_text("[]", encoding="utf-8")
            with unittest.mock.patch.object(update_planner, "AUDIT_STATUS_PATH", nondict):
                self.assertEqual(update_planner.audit_states(), {})

    def test_decision_changes(self):
        entries = [{"日期": "2026-01-01"}]
        with unittest.mock.patch.object(
                decision_log, "entries", return_value=entries) as m:
            self.assertEqual(update_planner.decision_changes(limit=3), entries)
            m.assert_called_once_with(limit=3)

    def test_decision_changes_exception(self):
        with unittest.mock.patch.object(
                decision_log, "entries", side_effect=RuntimeError("boom")):
            self.assertEqual(update_planner.decision_changes(), [])

    def test_main_decisions(self):
        entries = [{"日期": "2026-01-01", "决策问题": "去不去", "字段": "判定",
                    "变化前": "待定", "变化后": "是"}]
        with unittest.mock.patch.object(
                update_planner, "decision_changes", return_value=entries):
            rc, out, _ = _capture(["update_planner.py", "--decisions"], update_planner.main)
        self.assertEqual(rc, 0)
        self.assertIn("去不去", out)

    def test_main_unknown_project(self):
        with unittest.mock.patch.object(update_planner, "iter_business_dirs", return_value=[]):
            rc, _, err = _capture(
                ["update_planner.py", "--project", "nope"], update_planner.main)
        self.assertEqual(rc, 2)
        self.assertIn("未找到业务线", err)

    def test_main_invalid_period(self):
        with unittest.mock.patch.object(update_planner, "iter_business_dirs", return_value=[]):
            rc, _, err = _capture(
                ["update_planner.py", "--period", "2026-13"], update_planner.main)
        self.assertEqual(rc, 2)
        self.assertIn("无法识别的周期", err)

    def test_main_porcelain_empty(self):
        with unittest.mock.patch.object(update_planner, "iter_business_dirs", return_value=[]):
            rc, out, _ = _capture(
                ["update_planner.py", "--porcelain", "--period", "2026-11"],
                update_planner.main)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out), [])

    def test_main_pending_only(self):
        tasks = [{"project": "a", "status": "pending", "cycle_label": "月度",
                  "period": "2026-11", "prompt": "p", "output": "o", "audit": "未审计"},
                 {"project": "b", "status": "done", "cycle_label": "月度",
                  "period": "2026-11", "prompt": "p", "output": "o", "audit": "已审计"}]
        with unittest.mock.patch.object(update_planner, "iter_business_dirs", return_value=[]), \
                unittest.mock.patch.object(update_planner, "build_tasks", return_value=tasks), \
                unittest.mock.patch.object(update_planner, "decision_changes", return_value=[]):
            rc, out, _ = _capture(
                ["update_planner.py", "--pending-only", "--period", "2026-11"],
                update_planner.main)
        self.assertEqual(rc, 0)
        self.assertIn("a ·", out)
        self.assertNotIn("b ·", out)


# ──────────────────────────────────────────────
# automation_status：状态记录与活跃度
# ──────────────────────────────────────────────
class TestCovPipelineAutomationStatus(unittest.TestCase):
    def test_load_status_missing(self):
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(
                    automation_status, "STATUS_FILE", Path(d) / "none.json"):
                self.assertEqual(automation_status.load_status(), {"records": []})

    def test_load_status_valid(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "automation-status.json"
            f.write_text(json.dumps({"records": [{"phase": "pipeline"}]}), encoding="utf-8")
            with unittest.mock.patch.object(automation_status, "STATUS_FILE", f):
                self.assertEqual(
                    automation_status.load_status(), {"records": [{"phase": "pipeline"}]})

    def test_load_status_corrupt_non_dict_bad_records(self):
        with tempfile.TemporaryDirectory() as d:
            corrupt = Path(d) / "bad.json"
            corrupt.write_text("{bad", encoding="utf-8")
            with unittest.mock.patch.object(automation_status, "STATUS_FILE", corrupt):
                self.assertEqual(automation_status.load_status(), {"records": []})
            nondict = Path(d) / "arr.json"
            nondict.write_text("[]", encoding="utf-8")
            with unittest.mock.patch.object(automation_status, "STATUS_FILE", nondict):
                self.assertEqual(automation_status.load_status(), {"records": []})
            badrec = Path(d) / "badrec.json"
            badrec.write_text(json.dumps({"records": "x"}), encoding="utf-8")
            with unittest.mock.patch.object(automation_status, "STATUS_FILE", badrec):
                self.assertEqual(automation_status.load_status(), {"records": []})

    def test_record_appends(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "automation-status.json"
            with unittest.mock.patch.object(automation_status, "STATUS_FILE", f):
                self.assertEqual(
                    automation_status.record("pipeline", "success", "http://x"), 0)
                self.assertEqual(
                    automation_status.record("maintenance", "failure", ""), 0)
                data = json.loads(f.read_text(encoding="utf-8"))
        self.assertEqual(len(data["records"]), 2)
        self.assertEqual(data["records"][0]["phase"], "pipeline")
        self.assertEqual(data["records"][0]["result"], "success")
        self.assertEqual(data["records"][0]["run_url"], "http://x")
        self.assertIn("timestamp", data["records"][0])

    def test_activity_no_records(self):
        with unittest.mock.patch.object(
                automation_status, "load_status", return_value={"records": []}):
            rc, out, _ = _capture([], lambda: automation_status.activity(45, True))
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "unknown")

    def test_activity_days(self):
        ts = (datetime.now(UTC) - timedelta(days=10)).isoformat()
        with unittest.mock.patch.object(
                automation_status, "load_status",
                return_value={"records": [{"timestamp": ts}]}):
            rc, out, _ = _capture([], lambda: automation_status.activity(45, True))
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "10")

    def test_activity_over_threshold(self):
        ts = (datetime.now(UTC) - timedelta(days=60)).isoformat()
        with unittest.mock.patch.object(
                automation_status, "load_status",
                return_value={"records": [{"timestamp": ts}]}):
            rc, out, _ = _capture([], lambda: automation_status.activity(45, False))
        self.assertEqual(rc, 0)
        self.assertIn("已超阈值", out)

    def test_main_record(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "automation-status.json"
            with unittest.mock.patch.object(automation_status, "STATUS_FILE", f):
                rc, out, _ = _capture(
                    ["automation_status.py", "record", "--phase", "pipeline",
                     "--result", "success"],
                    automation_status.main)
            self.assertEqual(rc, 0)
            self.assertTrue(f.is_file())
            self.assertIn("已记录", out)

    def test_main_activity(self):
        with unittest.mock.patch.object(
                automation_status, "load_status", return_value={"records": []}):
            rc, out, _ = _capture(
                ["automation_status.py", "activity", "--porcelain"], automation_status.main)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "unknown")

    def test_main_invalid_phase_exits(self):
        with self.assertRaises(SystemExit):
            _capture(
                ["automation_status.py", "record", "--phase", "bogus",
                 "--result", "success"],
                automation_status.main)


# ──────────────────────────────────────────────
# decision_log：决策日志
# ──────────────────────────────────────────────
class TestCovPipelineDecisionLog(unittest.TestCase):
    def test_main_add_missing_args(self):
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(
                    decision_log, "LOG_PATH", Path(d) / "decision_log.md"):
                rc, _, _ = _capture(
                    ["decision_log.py", "--add", "--question", "q"], decision_log.main)
        self.assertEqual(rc, 1)

    def test_main_add_and_list(self):
        with tempfile.TemporaryDirectory() as d:
            lp = Path(d) / "decision_log.md"
            with unittest.mock.patch.object(decision_log, "LOG_PATH", lp):
                rc, _, _ = _capture(
                    ["decision_log.py", "--add", "--question", "去不去",
                     "--field", "判定", "--new", "是", "--date", "2026-01-02"],
                    decision_log.main)
                self.assertEqual(rc, 0)
                self.assertIn("去不去", lp.read_text(encoding="utf-8"))
                rc2, out, _ = _capture(["decision_log.py", "--list"], decision_log.main)
            self.assertEqual(rc2, 0)
            self.assertIn("去不去", out)

    def test_main_timeline(self):
        with tempfile.TemporaryDirectory() as d:
            lp = Path(d) / "decision_log.md"
            with unittest.mock.patch.object(decision_log, "LOG_PATH", lp):
                _capture(
                    ["decision_log.py", "--add", "--question", "Q",
                     "--field", "F", "--new", "N"],
                    decision_log.main)
                rc, out, _ = _capture(["decision_log.py", "--timeline"], decision_log.main)
        self.assertEqual(rc, 0)
        self.assertIn("决策时间线", out)
        self.assertIn("Q", out)

    def test_entries_reverse_and_limit(self):
        text = ("| 2026-01-01 | Q1 | F | a | b | basis | src |\n"
                "| 2026-02-01 | Q2 | F | a | b | basis | src |\n"
                "| bad row |\n")
        with tempfile.TemporaryDirectory() as d:
            lp = Path(d) / "decision_log.md"
            lp.write_text(text, encoding="utf-8")
            with unittest.mock.patch.object(decision_log, "LOG_PATH", lp):
                rows = decision_log.entries()
                limited = decision_log.entries(limit=1)
        self.assertEqual([r["日期"] for r in rows], ["2026-02-01", "2026-01-01"])
        self.assertEqual(len(limited), 1)
        self.assertEqual(limited[0]["日期"], "2026-02-01")

    def test_ensure_header_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            lp = Path(d) / "decision_log.md"
            with unittest.mock.patch.object(decision_log, "LOG_PATH", lp):
                first = decision_log._ensure_header("")
                second = decision_log._ensure_header(first)
                lp.write_text(first, encoding="utf-8")
                third = decision_log._ensure_header(first)
        self.assertEqual(first, second)
        self.assertEqual(third, first)
        self.assertEqual(first.count("# 决策日志"), 1)

    def test_entries_short_row_skipped(self):
        text = "| 2026-01-01 | only | three | cells |\n"
        with tempfile.TemporaryDirectory() as d:
            lp = Path(d) / "decision_log.md"
            lp.write_text(text, encoding="utf-8")
            with unittest.mock.patch.object(decision_log, "LOG_PATH", lp):
                self.assertEqual(decision_log.entries(), [])


# ──────────────────────────────────────────────
# stage_gate_check：阶段闸
# ──────────────────────────────────────────────
class TestCovPipelineStageGate(unittest.TestCase):
    def _topic(self, root, name="01-demo", config=None, registry=None):
        d = root / name
        (d / "prompts").mkdir(parents=True, exist_ok=True)
        (d / "data").mkdir(parents=True, exist_ok=True)
        if config is not None:
            (d / "prompts" / "business-config.md").write_text(config, encoding="utf-8")
        if registry is not None:
            (d / "data" / "x_indicator_registry.md").write_text(registry, encoding="utf-8")
        return _common.Business(name)

    _GOOD_CFG = ("继承：prompt-generic-base.md × "
                 "src/report_templates/employment-research/\n"
                 "{{REGION}} = 日本\n{{TOPIC}} = T\n"
                 "{{REGISTRY_PATH}} = data/x_indicator_registry.md\n")
    _GOOD_REG = ("| # | 指标 | 口径 | 核验日期 |\n|---|---|---|---|\n"
                 "| 1 | A | B | {} |\n".format(date.today().isoformat()))

    def test_main_topic_not_found(self):
        with unittest.mock.patch.object(stage_gate_check, "iter_business_dirs", return_value=[]):
            rc, _, err = _capture(
                ["stage_gate_check.py", "--topic", "nope"], stage_gate_check.main)
        self.assertEqual(rc, 1)
        self.assertIn("未找到主题", err)

    def test_main_topic_json_p1(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg = "继承：prompt-generic-base.md\n{{REGION}} = 日本\n{{TOPIC}} = T\n"
            b = self._topic(root, config=cfg,
                            registry="| # | 指标 | 口径 |\n|---|---|---|\n| 1 | A | B |\n")
            with unittest.mock.patch.object(_common, "ROOT", root), \
                    unittest.mock.patch.object(
                        stage_gate_check, "iter_business_dirs", return_value=[b]):
                rc, out, _ = _capture(
                    ["stage_gate_check.py", "--topic", "01-demo", "--json"],
                    stage_gate_check.main)
            self.assertEqual(rc, 1)
            data = json.loads(out)
            self.assertEqual(data["topic"], "01-demo")
            self.assertGreaterEqual(data["severity"]["P1"], 1)

    def test_main_topic_p2_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg = ("继承：prompt-generic-base.md × "
                   "src/report_templates/employment-research/\n{{TOPIC}} = T\n")
            b = self._topic(root, config=cfg,
                            registry="| # | 指标 | 口径 |\n|---|---|---|\n| 1 | A | B |\n")
            with unittest.mock.patch.object(_common, "ROOT", root), \
                    unittest.mock.patch.object(
                        stage_gate_check, "iter_business_dirs", return_value=[b]):
                rc, out, _ = _capture(
                    ["stage_gate_check.py", "--topic", "01-demo"],
                    stage_gate_check.main)
            self.assertEqual(rc, 2)
            self.assertIn("P2 1", out)

    def test_main_topic_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            b = self._topic(root, config=self._GOOD_CFG, registry=self._GOOD_REG)
            with unittest.mock.patch.object(_common, "ROOT", root), \
                    unittest.mock.patch.object(
                        stage_gate_check, "iter_business_dirs", return_value=[b]):
                rc, out, _ = _capture(
                    ["stage_gate_check.py", "--topic", "01-demo"],
                    stage_gate_check.main)
            self.assertEqual(rc, 0)
            self.assertIn("通过", out)

    def test_run_all_summary_sorted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            b1 = self._topic(root, name="01-good", config=self._GOOD_CFG,
                             registry=self._GOOD_REG)
            b2 = self._topic(root, name="02-bad", config="无继承\n", registry=self._GOOD_REG)
            with unittest.mock.patch.object(_common, "ROOT", root), \
                    unittest.mock.patch.object(
                        stage_gate_check, "iter_business_dirs", return_value=[b2, b1]):
                results, summary = stage_gate_check.run_all()
        self.assertEqual([r["topic"] for r in results], ["01-good", "02-bad"])
        self.assertEqual(summary["topics"], 2)
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertGreaterEqual(summary["by_severity"]["P1"], 1)

    def test_main_all_json_empty(self):
        with unittest.mock.patch.object(stage_gate_check, "iter_business_dirs", return_value=[]):
            rc, out, _ = _capture(["stage_gate_check.py", "--json"], stage_gate_check.main)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["summary"]["topics"], 0)


# ──────────────────────────────────────────────
# pending_verification：待核实项闭环
# ──────────────────────────────────────────────
class TestCovPipelinePendingVerification(unittest.TestCase):
    def test_parse_no_registry(self):
        with unittest.mock.patch.object(
                pending_verification, "iter_business_dirs", return_value=[]):
            row = pending_verification._parse("14-life-operations")
        self.assertEqual(row["status"], "未登记")
        self.assertIsNone(row["deadline"])
        self.assertEqual(row["entries"], 0)

    def test_parse_overdue_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = root / "14-life-operations" / "data"
            data.mkdir(parents=True)
            (data / "x_indicator_registry.md").write_text(
                "首轮核验截止：2020-01-01\n\n- ⚠ 待核实A\n- ⚠ 待核实A\n",
                encoding="utf-8")
            b = _common.Business("14-life-operations")
            with unittest.mock.patch.object(_common, "ROOT", root), \
                    unittest.mock.patch.object(pending_verification, "ROOT", root), \
                    unittest.mock.patch.object(
                        pending_verification, "iter_business_dirs", return_value=[b]):
                row = pending_verification._parse("14-life-operations")
        self.assertEqual(row["status"], "已逾期")
        self.assertEqual(row["deadline"], "2020-01-01")
        self.assertEqual(row["entries"], 1)
        self.assertEqual(row["registry"], "14-life-operations/data/x_indicator_registry.md")

    def test_parse_due_soon_and_in_progress(self):
        today = date.today()
        soon = (today + timedelta(days=10)).isoformat()
        later = (today + timedelta(days=60)).isoformat()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name, deadline in (("14-a", soon), ("14-b", later)):
                data = root / name / "data"
                data.mkdir(parents=True)
                (data / "x_indicator_registry.md").write_text(
                    f"首轮核验截止：{deadline}\n", encoding="utf-8")

            def fake_iter():
                return [_common.Business("14-a"), _common.Business("14-b")]

            with unittest.mock.patch.object(_common, "ROOT", root), \
                    unittest.mock.patch.object(pending_verification, "ROOT", root), \
                    unittest.mock.patch.object(
                        pending_verification, "iter_business_dirs", side_effect=fake_iter):
                r1 = pending_verification._parse("14-a")
                r2 = pending_verification._parse("14-b")
        self.assertEqual(r1["status"], "临近")
        self.assertEqual(r2["status"], "进行中")

    def test_parse_registered_no_deadline(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = root / "14-a" / "data"
            data.mkdir(parents=True)
            (data / "x_indicator_registry.md").write_text("无截止字段\n", encoding="utf-8")
            b = _common.Business("14-a")
            with unittest.mock.patch.object(_common, "ROOT", root), \
                    unittest.mock.patch.object(pending_verification, "ROOT", root), \
                    unittest.mock.patch.object(
                        pending_verification, "iter_business_dirs", return_value=[b]):
                row = pending_verification._parse("14-a")
        self.assertEqual(row["status"], "未登记")
        self.assertIsNone(row["deadline"])

    def test_run_summary_counts(self):
        rows = [
            {"topic": "a", "deadline": "2026-12-31", "status": "进行中", "pending": []},
            {"topic": "b", "deadline": None, "status": "未登记", "pending": ["x"]},
            {"topic": "c", "deadline": "2020-01-01", "status": "已逾期", "pending": []},
            {"topic": "d", "deadline": "2026-12-31", "status": "临近", "pending": []},
        ]
        with unittest.mock.patch.object(
                pending_verification, "TOPICS", ("a", "b", "c", "d")), \
                unittest.mock.patch.object(
                    pending_verification, "_parse", side_effect=rows):
            out_rows, summary = pending_verification.run()
        self.assertEqual(len(out_rows), 4)
        self.assertEqual(summary["topics"], 4)
        self.assertEqual(summary["registered"], 3)
        self.assertEqual(summary["overdue"], 1)
        self.assertEqual(summary["due_soon"], 1)
        self.assertEqual(summary["unregistered"], 1)
        self.assertEqual(summary["pending_items"], 1)

    def test_main_check_no_write(self):
        rows = [{"topic": "a", "deadline": None, "status": "未登记", "pending": []}]
        summary = {"topics": 1, "registered": 0, "overdue": 0, "due_soon": 0,
                   "unregistered": 1, "pending_items": 0}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "pending-verification.json"
            with unittest.mock.patch.object(pending_verification, "ROOT", root), \
                    unittest.mock.patch.object(pending_verification, "OUT_PATH", out), \
                    unittest.mock.patch.object(
                        pending_verification, "run", return_value=(rows, summary)):
                rc, _, _ = _capture(
                    ["pending_verification.py", "--check"], pending_verification.main)
            self.assertEqual(rc, 1)
            self.assertFalse(out.exists())

    def test_main_writes_json(self):
        rows = [{"topic": "a", "deadline": "2026-12-31", "status": "进行中",
                 "pending": []}]
        summary = {"topics": 1, "registered": 1, "overdue": 0, "due_soon": 0,
                   "unregistered": 0, "pending_items": 0}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "pending-verification.json"
            with unittest.mock.patch.object(pending_verification, "ROOT", root), \
                    unittest.mock.patch.object(pending_verification, "OUT_PATH", out), \
                    unittest.mock.patch.object(
                        pending_verification, "run", return_value=(rows, summary)):
                rc, _, _ = _capture(
                    ["pending_verification.py"], pending_verification.main)
            self.assertEqual(rc, 0)
            self.assertTrue(out.is_file())
            self.assertEqual(
                json.loads(out.read_text(encoding="utf-8"))["summary"]["topics"], 1)


# ──────────────────────────────────────────────
# personal_finance_model：个人财务模型
# ──────────────────────────────────────────────
class TestCovPipelinePersonalFinance(unittest.TestCase):
    def test_yen(self):
        self.assertEqual(personal_finance_model._yen("1,234 円"), 1234.0)
        self.assertEqual(personal_finance_model._yen("62,500円"), 62500.0)
        self.assertIsNone(personal_finance_model._yen("100 USD"))

    def test_yen_range(self):
        self.assertEqual(
            personal_finance_model._yen_range("4–7 万円"), (40000.0, 70000.0))
        self.assertEqual(
            personal_finance_model._yen_range("1,000–2,500 円"), (1000.0, 2500.0))
        self.assertIsNone(personal_finance_model._yen_range("3 万円"))

    def test_sum_yen(self):
        self.assertEqual(
            personal_finance_model._sum_yen("1,000 円 + 2,500 円"), 3500.0)
        self.assertIsNone(personal_finance_model._sum_yen("无"))

    def test_read_rows(self):
        text = ("| # | 指标 | 口径 | 值 |\n|---|---|---|---|\n"
                "| 1 | A | B | 100 |\n"
                "| x | 非数字 | | |\n")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "reg.md"
            p.write_text(text, encoding="utf-8")
            rows = personal_finance_model._read_rows(p)
        self.assertEqual(rows[1], ["1", "A", "B", "100"])
        self.assertEqual(list(rows), [1])

    def test_cell(self):
        rows = {1: ["1", "A", "B"]}
        self.assertEqual(personal_finance_model._cell(rows, 1, 2), "B")
        self.assertEqual(personal_finance_model._cell(rows, 1, 5), "")
        self.assertEqual(personal_finance_model._cell(rows, 9, 0), "")

    def test_main_json_ok(self):
        model = {"missing": [], "inputs": {}, "metrics": {}}
        with unittest.mock.patch.object(
                personal_finance_model, "build_model", return_value=model):
            rc, out, _ = _capture(
                ["personal_finance_model.py", "--json"], personal_finance_model.main)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out), model)

    def test_main_json_missing(self):
        model = {"missing": ["x"], "inputs": {}, "metrics": None}
        with unittest.mock.patch.object(
                personal_finance_model, "build_model", return_value=model):
            rc, _, _ = _capture(
                ["personal_finance_model.py", "--json"], personal_finance_model.main)
        self.assertEqual(rc, 1)

    def test_main_check_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "model.md"
            with unittest.mock.patch.object(
                    personal_finance_model, "build_model",
                    return_value={"missing": [], "inputs": {}}), \
                    unittest.mock.patch.object(
                        personal_finance_model, "render_md", return_value="CONTENT"):
                rc, _, _ = _capture(
                    ["personal_finance_model.py", "--check", "--out", str(out)],
                    personal_finance_model.main)
        self.assertEqual(rc, 1)

    def test_main_check_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "model.md"
            out.write_text("OLD", encoding="utf-8")
            with unittest.mock.patch.object(
                    personal_finance_model, "build_model",
                    return_value={"missing": [], "inputs": {}}), \
                    unittest.mock.patch.object(
                        personal_finance_model, "render_md", return_value="NEW"):
                rc, _, _ = _capture(
                    ["personal_finance_model.py", "--check", "--out", str(out)],
                    personal_finance_model.main)
        self.assertEqual(rc, 2)

    def test_main_check_match(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "model.md"
            out.write_text("SAME", encoding="utf-8")
            with unittest.mock.patch.object(
                    personal_finance_model, "build_model",
                    return_value={"missing": [], "inputs": {}}), \
                    unittest.mock.patch.object(
                        personal_finance_model, "render_md", return_value="SAME"):
                rc, _, _ = _capture(
                    ["personal_finance_model.py", "--check", "--out", str(out)],
                    personal_finance_model.main)
        self.assertEqual(rc, 0)

    def test_main_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "sub" / "model.md"
            with unittest.mock.patch.object(personal_finance_model, "ROOT", root), \
                    unittest.mock.patch.object(
                        personal_finance_model, "build_model",
                        return_value={"missing": [], "inputs": {}}), \
                    unittest.mock.patch.object(
                        personal_finance_model, "render_md", return_value="CONTENT"):
                rc, out_text, _ = _capture(
                    ["personal_finance_model.py", "--out", str(out)],
                    personal_finance_model.main)
            self.assertEqual(rc, 0)
            self.assertEqual(out.read_text(encoding="utf-8"), "CONTENT")
            self.assertIn("model.md", out_text)
            self.assertIn("sub", out_text)


if __name__ == "__main__":
    unittest.main()
