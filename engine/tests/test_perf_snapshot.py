"""性能趋势快照测试（架构优化方向 D / I-13，组 D / N14）。

覆盖：
- 规模快照字段与实测口径（报告 md/html 成对、工具数、测试数）；
- 耗时采集（计时 + 退出码）；
- 基线语义（首条为基线、追加不改基线、``--set-baseline`` 覆盖）；
- CLI ``--porcelain`` 输出与退出码。
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import perf_snapshot  # noqa: E402


class TestCollectScale(unittest.TestCase):
    def test_scale_shape_and_counts(self):
        scale = perf_snapshot.collect_scale(ROOT)
        for key in ("repo_files", "repo_bytes", "report_md", "report_html",
                    "report_html_bytes", "index_html_bytes", "search_index_bytes",
                    "tool_count", "test_count"):
            self.assertIn(key, scale, f"规模快照缺字段：{key}")
        self.assertGreater(scale["repo_files"], 0)
        self.assertGreater(scale["repo_bytes"], 0)
        self.assertEqual(scale["report_md"], scale["report_html"], "报告 md / html 未成对")
        self.assertGreater(scale["report_md"], 0)
        actual_tools = len([p for p in (ROOT / "engine" / "tools").glob("*.py")
                            if p.name != "_common.py"])
        self.assertEqual(scale["tool_count"], actual_tools)
        self.assertGreater(scale["test_count"], 0)


class TestRunTimed(unittest.TestCase):
    def test_records_each_command(self):
        commands = {"alpha": [sys.executable, "-c", "pass"],
                    "beta": [sys.executable, "-c", "pass"]}
        fake = type("_P", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        with unittest.mock.patch.object(perf_snapshot.subprocess, "run", return_value=fake):
            result = perf_snapshot.run_timed(commands, ROOT)
        self.assertEqual(set(result), {"alpha", "beta"})
        for entry in result.values():
            self.assertGreaterEqual(entry["sec"], 0.0)
            self.assertEqual(entry["returncode"], 0)


class TestSnapshotSemantics(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.output = Path(self._tmp.name) / "perf-trend.json"
        self._orig_run_timed = perf_snapshot.run_timed
        self._calls = 0

        def fake_run_timed(commands, root):
            self._calls += 1
            return {name: {"sec": float(self._calls), "returncode": 0} for name in commands}

        perf_snapshot.run_timed = fake_run_timed
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(setattr, perf_snapshot, "run_timed", self._orig_run_timed)

    def test_first_snapshot_becomes_baseline(self):
        result = perf_snapshot.snapshot(self.output, ROOT, with_tests=False)
        self.assertEqual(result["baseline"], result["current"])
        data = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(len(data["history"]), 1)
        self.assertEqual(data["baseline"], data["history"][0])

    def test_second_snapshot_appends_and_keeps_baseline(self):
        first = perf_snapshot.snapshot(self.output, ROOT, with_tests=False)
        second = perf_snapshot.snapshot(self.output, ROOT, with_tests=False)
        self.assertEqual(second["baseline"], first["current"])
        self.assertNotEqual(second["current"], second["baseline"])
        data = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(len(data["history"]), 2)

    def test_set_baseline_replaces(self):
        perf_snapshot.snapshot(self.output, ROOT, with_tests=False)
        result = perf_snapshot.snapshot(self.output, ROOT, with_tests=False, set_baseline=True)
        self.assertEqual(result["baseline"], result["current"])
        data = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(data["baseline"], data["history"][-1])


class TestCli(unittest.TestCase):
    def test_porcelain_outputs_json_and_exit_zero(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / "perf-trend.json"
            orig = perf_snapshot.run_timed
            perf_snapshot.run_timed = lambda commands, root: {
                name: {"sec": 0.5, "returncode": 0} for name in commands}
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    rc = perf_snapshot.main(["--porcelain", "--output", str(output)])
            finally:
                perf_snapshot.run_timed = orig
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            self.assertIn("baseline", payload)
            self.assertIn("current", payload)
            self.assertIn("scale", payload["current"])


if __name__ == "__main__":
    unittest.main()
