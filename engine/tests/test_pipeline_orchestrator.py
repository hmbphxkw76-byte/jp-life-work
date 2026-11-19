"""端到端流水线编排系统测试（任务 1：状态层基础设施）。

覆盖 `_common` 状态层：状态 shape、save / load 往返、损坏 / 版本不符报错。
后续任务（触发检测 / 编排器 / 监控 / CI 接线）在同一文件追加用例。

运行：python -m unittest discover -s engine/tests -v
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import _common  # noqa: E402
import pipeline_runner  # noqa: E402
import pipeline_status  # noqa: E402
import trigger_watch  # noqa: E402


class TestPipelineStateLayer(unittest.TestCase):
    """任务 1：状态层基础设施（schema 校验用例 ≥ 3）。"""

    def test_new_state_shape(self):
        s = _common.new_state("2026-11")
        self.assertEqual(s["schema_version"], "1.0")
        self.assertEqual(s["period"], "2026-11")
        self.assertEqual(s["stages"], {})
        self.assertEqual(s["updated"], "")

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            _common.save_state("2026-11", _common.new_state("2026-11"))
            self.assertTrue((Path(d) / "state-2026-11.json").is_file())
            loaded = _common.load_state("2026-11")
            self.assertEqual(loaded["period"], "2026-11")
            self.assertEqual(loaded["schema_version"], "1.0")

    def test_load_corrupt_raises(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            (Path(d) / "state-2026-11.json").write_text("{not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                _common.load_state("2026-11")

    def test_load_version_mismatch_raises(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            p = Path(d) / "state-2026-11.json"
            bad_payloads = [
                {"schema_version": "0.9", "period": "2026-11", "stages": {}},
                {"period": "2026-11", "stages": {}},
            ]
            for bad in bad_payloads:
                p.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
                with self.assertRaises(ValueError):
                    _common.load_state("2026-11")


class TestTriggerWatch(unittest.TestCase):
    """任务 2：触发检测（watchlist 派生 / freshness / 幂等 / 只读默认）。"""

    def test_build_watchlist_derived_from_business_config(self):
        wl = trigger_watch.build_watchlist()
        self.assertTrue(any(w["topic"] == "01-ssw-driver" for w in wl))
        entry = next(w for w in wl if w["topic"] == "01-ssw-driver")
        # 接口契约：每项含 topic / trigger / source / last_verified
        for key in ("topic", "trigger", "source", "last_verified"):
            self.assertIn(key, entry)
        self.assertTrue(entry["trigger"].strip())

    def test_scan_empty_when_no_window_due(self):
        out = trigger_watch.scan("2026-11")
        self.assertTrue(set(out) >= {"window_due", "stale", "candidates"})
        # 2026-11 全部 21 个主题报告已产出 -> 无窗口到期
        self.assertEqual(out["window_due"], [])

    def test_scan_is_idempotent(self):
        self.assertEqual(
            trigger_watch.scan("2026-11"), trigger_watch.scan("2026-11")
        )

    def test_cli_report_is_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            snap = Path(d) / "trigger-watch.json"
            with unittest.mock.patch.object(trigger_watch, "SNAPSHOT", snap):
                rc = trigger_watch.main_argv(["--report", "--period", "2026-11"])
            self.assertEqual(rc, 0)
            self.assertFalse(snap.exists())

    def test_cli_apply_writes_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            snap = Path(d) / "trigger-watch.json"
            with unittest.mock.patch.object(trigger_watch, "SNAPSHOT", snap):
                rc = trigger_watch.main_argv(["--apply", "--period", "2026-11"])
            self.assertEqual(rc, 0)
            self.assertTrue(snap.is_file())

    def test_load_non_object_raises(self):
        # T1 评审 N3：schema 非对象（如 []）负例
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            (Path(d) / "state-2026-11.json").write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                _common.load_state("2026-11")


class TestPipelineStatus(unittest.TestCase):
    """任务 4：统一监控视图（空状态 / 阻塞定位 / 渲染字段）。"""

    def test_collect_empty_state(self):
        p = pipeline_status.collect("2099-01")
        self.assertEqual(p["stages"], {})
        self.assertIsNone(p["blocking"])

    def test_render_md_contains_key_fields(self):
        md = pipeline_status.render_md({"period": "2026-11", "stages": {}, "blocking": None})
        self.assertIn("2026-11", md)
        self.assertIn("阻塞", md)

    def test_collect_reports_blocking_stage(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            st = _common.new_state("2026-11")
            st["stages"] = {
                "S0_detect": {"status": "completed"},
                "S1_plan": {"status": "running"},
                "S2_author": {"status": "pending"},
            }
            _common.save_state("2026-11", st)
            p = pipeline_status.collect("2026-11")
            self.assertEqual(p["blocking"], "S1_plan")

    def test_collect_corrupt_state_surfaces_error(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            (Path(d) / "state-2026-11.json").write_text("{bad", encoding="utf-8")
            p = pipeline_status.collect("2026-11")
            self.assertIn("state_error", p)
            self.assertTrue(p["state_error"])


class TestPipelineRunner(unittest.TestCase):
    """任务 3：六阶段编排器（顺序固定 / S2 闸门 / 续跑 / 损坏终止）。"""

    def test_stages_order_fixed(self):
        self.assertEqual(pipeline_runner.STAGES[:3], ("S0_detect", "S1_plan", "S2_author"))

    def test_run_pauses_at_author_gate(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            rc = pipeline_runner.run("2026-11", dry_run=True)
            self.assertEqual(rc, 0)
            st = _common.load_state("2026-11")
            self.assertEqual(st["stages"]["S1_plan"]["status"], "completed")
            self.assertEqual(st["stages"]["S2_author"]["status"], "pending")

    def test_resume_from_s3_continues(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            pipeline_runner.run("2026-11", dry_run=True)
            rc = pipeline_runner.run("2026-11", from_stage="S3_build", dry_run=True)
            self.assertEqual(rc, 0)
            self.assertEqual(
                _common.load_state("2026-11")["stages"]["S5_monitor"]["status"],
                "completed",
            )

    def test_corrupt_state_aborts(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            (Path(d) / "state-2026-11.json").write_text("{bad", encoding="utf-8")
            rc = pipeline_runner.run("2026-11")
            self.assertEqual(rc, 1)

    def test_invalid_period_rejected(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            self.assertEqual(pipeline_runner.run("2026-13", dry_run=True), 2)

    def test_run_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            pipeline_runner.run("2026-11", dry_run=True)
            first = _common.load_state("2026-11")["stages"]
            pipeline_runner.run("2026-11", dry_run=True)
            second = _common.load_state("2026-11")["stages"]
            self.assertEqual(
                {k: v["status"] for k, v in first.items()},
                {k: v["status"] for k, v in second.items()},
            )


class TestPipelineWorkflow(unittest.TestCase):
    """任务 5：CI 工作流接线（定时 + 手动触发，不含撰写步骤）。"""

    def test_workflow_exists_and_scheduled(self):
        wf = (_common.ROOT / ".github" / "workflows" / "pipeline-orchestrator.yml").read_text(encoding="utf-8")
        self.assertIn("trigger_watch.py", wf)
        self.assertIn("pipeline_runner.py", wf)
        self.assertIn("cron:", wf)
        self.assertIn("workflow_dispatch:", wf)

    def test_workflow_has_no_authoring_step(self):
        # 纪律：CI 不得包含研究正文撰写步骤（S2 为唯一人工环节）
        wf = (_common.ROOT / ".github" / "workflows" / "pipeline-orchestrator.yml").read_text(encoding="utf-8")
        self.assertNotIn("md2html.py", wf)
        self.assertNotIn("auto_verify.py", wf)
        self.assertNotIn("audit_pipeline.py", wf)


class TestPipelineEndToEnd(unittest.TestCase):
    """任务 7：全链路 S0→S5（合成状态 + dry-run），断言 S2 闸门与幂等。"""

    def test_full_flow_with_author_gate(self):
        with tempfile.TemporaryDirectory() as d, unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
            # 第一轮：S0 → S1 → S2 人工闸门（停）
            self.assertEqual(pipeline_runner.run("2026-11", dry_run=True), 0)
            st = _common.load_state("2026-11")
            self.assertEqual(st["stages"]["S0_detect"]["status"], "completed")
            self.assertEqual(st["stages"]["S1_plan"]["status"], "completed")
            self.assertEqual(st["stages"]["S2_author"]["status"], "pending")
            # S2 只产出待撰写清单，不产出正文
            self.assertEqual(st["stages"]["S2_author"]["summary"]["gate"], "author")
            self.assertIsInstance(st["stages"]["S2_author"]["summary"]["todo"], list)

            # 人工完成 S2 后：S3 → S4 → S5 自动续跑
            self.assertEqual(
                pipeline_runner.run("2026-11", from_stage="S3_build", dry_run=True), 0
            )
            st = _common.load_state("2026-11")
            for name in pipeline_runner.STAGES:
                self.assertEqual(st["stages"][name]["status"], "completed", name)

            # 幂等：再次从 S3 续跑，状态不变
            self.assertEqual(
                pipeline_runner.run("2026-11", from_stage="S3_build", dry_run=True), 0
            )
            st2 = _common.load_state("2026-11")
            self.assertEqual(
                {k: v["status"] for k, v in st["stages"].items()},
                {k: v["status"] for k, v in st2["stages"].items()},
            )


if __name__ == "__main__":
    unittest.main()
