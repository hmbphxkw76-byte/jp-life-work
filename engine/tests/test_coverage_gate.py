"""覆盖率门禁测试（TOOLCHAIN-DEV-SPEC 第六节；mainline 融合 P1 / P3）。

hermetic：不运行真实测试套件，全部以 mock 注入测量结果；
仅 load_config 读取真实 coverage-config.json（只读）。
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "engine" / "tools"
sys.path.insert(0, str(TOOLS))

import coverage_gate  # noqa: E402


class TestLoadConfig(unittest.TestCase):
    def test_real_config_shape(self):
        cfg = coverage_gate.load_config()
        self.assertIsInstance(cfg["threshold"], int)
        self.assertIsInstance(cfg["enforce"], bool)
        self.assertIsInstance(cfg["test_discovery"], str)
        self.assertTrue(cfg["test_discovery"])
        self.assertIsInstance(cfg["per_tool_min"], int)

    def test_missing_threshold_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.json"
            p.write_text(json.dumps({"enforce": True, "test_discovery": "engine/tests"}),
                         encoding="utf-8")
            with self.assertRaises(ValueError):
                coverage_gate.load_config(p)

    def test_non_object_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.json"
            p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
            with self.assertRaises(ValueError):
                coverage_gate.load_config(p)

    def test_missing_file_rejected(self):
        with self.assertRaises(OSError):
            coverage_gate.load_config(Path("no-such-config.json"))


class TestEvaluate(unittest.TestCase):
    def test_at_threshold_passes(self):
        self.assertEqual(coverage_gate.evaluate(80.0, 80, True), 0)

    def test_above_threshold_passes(self):
        self.assertEqual(coverage_gate.evaluate(92.5, 80, True), 0)

    def test_below_threshold_enforced_blocks(self):
        self.assertEqual(coverage_gate.evaluate(79.9, 80, True), 1)

    def test_below_threshold_observe_warns(self):
        self.assertEqual(coverage_gate.evaluate(55.0, 60, False), 2)

    def test_per_tool_below_enforced_blocks(self):
        self.assertEqual(coverage_gate.evaluate(90.0, 80, True, 60, {"a.py": 50.0}), 1)

    def test_per_tool_below_observe_warns(self):
        self.assertEqual(coverage_gate.evaluate(90.0, 80, False, 60, {"a.py": 50.0}), 2)

    def test_per_tool_above_passes(self):
        self.assertEqual(coverage_gate.evaluate(90.0, 80, True, 60, {"a.py": 70.0}), 0)


class TestWriteBaseline(unittest.TestCase):
    def test_writes_json_atomically(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "sub" / "baseline.json"
            coverage_gate.write_baseline(p, {"total_percent": 81.5, "enforce": True})
            data = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(data["total_percent"], 81.5)
            self.assertTrue(p.exists())
            self.assertFalse(p.with_name(p.name + ".tmp").exists())


class TestMeasure(unittest.TestCase):
    def test_measure_returns_total_and_report(self):
        class FakeCov:
            def __init__(self, *a, **k):
                pass

            def start(self):
                pass

            def stop(self):
                pass

            def save(self):
                pass

            def report(self, file=None):
                file.write("fake report\n")
                return 91.25

        with unittest.mock.patch("coverage.Coverage", FakeCov), \
                unittest.mock.patch.object(coverage_gate, "run_tests", return_value=True):
            total, report, ok = coverage_gate.measure(
                {"test_discovery": "engine/tests"}
            )
        self.assertEqual(total, 91.25)
        self.assertIn("fake report", report)
        self.assertTrue(ok)


class TestMain(unittest.TestCase):
    def _run(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = coverage_gate.main(list(argv) if argv else [])
        return code, out.getvalue()

    def test_pass_exit_0(self):
        with unittest.mock.patch.object(coverage_gate, "measure",
                                        return_value=(85.0, "r", True)):
            code, out = self._run()
        self.assertEqual(code, 0)
        self.assertIn("达标", out)

    def test_below_enforced_exit_1(self):
        with unittest.mock.patch.object(coverage_gate, "measure",
                                        return_value=(70.0, "r", True)):
            code, out = self._run()
        self.assertEqual(code, 1)
        self.assertIn("阻断", out)

    def test_tests_not_green_forces_block(self):
        with unittest.mock.patch.object(coverage_gate, "measure",
                                        return_value=(99.0, "r", False)):
            code, _ = self._run()
        self.assertEqual(code, 1)

    def test_per_tool_below_blocks(self):
        with unittest.mock.patch.object(coverage_gate, "measure",
                                        return_value=(90.0, "r", True)), \
                unittest.mock.patch.object(coverage_gate, "per_tool_coverage",
                                           return_value={"a.py": 40.0}):
            code, out = self._run()
        self.assertEqual(code, 1)
        self.assertIn("低于单工具阈值", out)

    def test_per_tool_above_passes(self):
        with unittest.mock.patch.object(coverage_gate, "measure",
                                        return_value=(90.0, "r", True)), \
                unittest.mock.patch.object(coverage_gate, "per_tool_coverage",
                                           return_value={"a.py": 70.0}):
            code, out = self._run()
        self.assertEqual(code, 0)
        self.assertNotIn("低于单工具阈值", out)

    def test_porcelain_json(self):
        with unittest.mock.patch.object(coverage_gate, "measure",
                                        return_value=(85.0, "r", True)):
            code, out = self._run("--porcelain")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["total_percent"], 85.0)
        self.assertEqual(data["threshold"], 80)
        self.assertTrue(data["tests_green"])
        self.assertEqual(data["per_tool_min"], 60)

    def test_invalid_config_exit_1(self):
        with unittest.mock.patch.object(coverage_gate, "load_config",
                                        side_effect=ValueError("bad")):
            code, _ = self._run()
        self.assertEqual(code, 1)


class TestPerToolCoverage(unittest.TestCase):
    """P2-3：逐工具覆盖率明细。"""

    def _fake_cov(self, files):
        data = unittest.mock.Mock()
        data.measured_files.return_value = list(files)
        cov = unittest.mock.Mock()
        cov.get_data.return_value = data
        cov.analysis2.side_effect = lambda f: (f, [1, 2, 3, 4], [], [4], "")
        return cov

    def test_per_tool_filters_and_sorts(self):
        root = ROOT
        files = [
            str(root / "engine" / "tools" / "bbb.py"),
            str(root / "engine" / "tools" / "aaa.py"),
            str(root / "engine" / "scripts" / "ccc.py"),
            str(root / "engine" / "tools" / "_common.py"),
        ]
        with unittest.mock.patch.dict("sys.modules", {"coverage": unittest.mock.Mock()}):
            import coverage as _cov_mod
            with unittest.mock.patch.object(_cov_mod, "Coverage",
                                            return_value=self._fake_cov(files)):
                out = coverage_gate.per_tool_coverage()
        self.assertEqual(set(out), {"aaa.py", "bbb.py"})
        self.assertEqual(list(out), sorted(out, key=lambda k: out[k]))

    def test_per_tool_empty_on_no_data(self):
        with unittest.mock.patch.dict("sys.modules", {"coverage": unittest.mock.Mock()}):
            import coverage as _cov_mod
            cov = unittest.mock.Mock()
            cov.load.side_effect = Exception("no data")
            with unittest.mock.patch.object(_cov_mod, "Coverage", return_value=cov):
                self.assertEqual(coverage_gate.per_tool_coverage(), {})


if __name__ == "__main__":
    unittest.main()
