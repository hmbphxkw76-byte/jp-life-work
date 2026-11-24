"""本地等价 CI 入口测试（local_ci.py）。

覆盖：检查集结构、状态 / 退出码映射、过滤、确定性、CLI、合成失败命中。
hermetic：真实检查只跑 `validate`（快、只读）；失败路径用合成 Check，不改仓库。
运行：python -m unittest discover -s engine/tests
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import local_ci  # noqa: E402


def _result(rid: str, status: str, code: int = 0) -> dict:
    return {"id": rid, "name": rid, "ci": "test", "exit_code": code,
            "status": status, "summary": "ok"}


class CheckRegistryCase(unittest.TestCase):
    def test_ids_unique(self):
        ids = [c.id for c in local_ci.CHECKS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_expected_size(self):
        self.assertEqual(len(local_ci.CHECKS), 33)

    def test_scripts_exist(self):
        for c in local_ci.CHECKS:
            for token in c.cmd:
                if token.endswith(".py"):
                    self.assertTrue((ROOT / token).is_file(), f"缺脚本：{token}")

    def test_no_write_flags(self):
        """只读约束：不得包含回写 / 修复 / 提交 / 推送类开关。"""
        banned = ("--apply", "--write", "--submit", "--sync", "--rebind",
                  "--purge-ghosts", "--backfill-l5", "--external", "git push")
        for c in local_ci.CHECKS:
            for flag in banned:
                self.assertNotIn(flag, c.cmd, f"{c.id} 含非只读开关 {flag}")

    def test_info_quality_is_side_effect_free(self):
        """本地 CI 的信息质量步骤必须走 `--check`，不得刷新跟踪的三清单。

        维护模式（`info-quality.yml --apply` / 手工全量）才写盘并随维护流程提交；
        本地等价 CI 若写盘会让 `engine/report-audits/info-quality/*` 每轮变脏并阻塞 sync。
        """
        c = next(c for c in local_ci.CHECKS if c.id == "info-quality")
        self.assertIn("--check", c.cmd)


class StatusCase(unittest.TestCase):
    def test_mapping(self):
        self.assertEqual(local_ci.status_for_exit(0), "pass")
        self.assertEqual(local_ci.status_for_exit(2), "warn")
        self.assertEqual(local_ci.status_for_exit(1), "fail")

    def test_overall(self):
        p, w, f = _result("p", "pass"), _result("w", "warn"), _result("f", "fail", 1)
        self.assertEqual(local_ci.overall([p, p]), 0)
        self.assertEqual(local_ci.overall([p, w]), 2)
        self.assertEqual(local_ci.overall([p, f]), 1)
        self.assertEqual(local_ci.overall([f, w]), 1)
        self.assertEqual(local_ci.overall([]), 0)


class SelectCase(unittest.TestCase):
    def test_only(self):
        got = local_ci.select(local_ci.CHECKS, only="validate")
        self.assertEqual([c.id for c in got], ["validate"])

    def test_skip(self):
        got = local_ci.select(local_ci.CHECKS, skip="validate")
        self.assertNotIn("validate", [c.id for c in got])
        self.assertEqual(len(got), len(local_ci.CHECKS) - 1)

    def test_unknown_raises(self):
        with self.assertRaises(SystemExit):
            local_ci.select(local_ci.CHECKS, only="nope")


class RunCheckCase(unittest.TestCase):
    def _run(self, code: int) -> dict:
        fake = unittest.mock.Mock(returncode=code, stdout="out", stderr="")
        with unittest.mock.patch.object(local_ci.subprocess, "run", return_value=fake):
            return local_ci.run_check(
                local_ci.Check("x", "x", "ci", (sys.executable, "-c", "pass")))

    def test_pass(self):
        self.assertEqual(self._run(0)["status"], "pass")

    def test_warn(self):
        self.assertEqual(self._run(2)["status"], "warn")

    def test_fail(self):
        self.assertEqual(self._run(1)["status"], "fail")

    def test_timeout_is_fail(self):
        with unittest.mock.patch.object(
                local_ci.subprocess, "run",
                side_effect=subprocess.TimeoutExpired(cmd="x", timeout=1)):
            r = local_ci.run_check(
                local_ci.Check("x", "x", "ci", (sys.executable, "-c", "pass")))
        self.assertEqual(r["status"], "fail")

    def test_launch_error_is_fail(self):
        with unittest.mock.patch.object(
                local_ci.subprocess, "run", side_effect=OSError("boom")):
            r = local_ci.run_check(
                local_ci.Check("x", "x", "ci", (sys.executable, "-c", "pass")))
        self.assertEqual(r["status"], "fail")


class DocumentCase(unittest.TestCase):
    def test_deterministic_and_shape(self):
        results = [_result("a", "pass")]
        d1 = local_ci.build_document(results, "main")
        d2 = local_ci.build_document(results, "main")
        self.assertEqual(d1, d2)
        self.assertEqual(
            set(d1), {"schema_version", "comment", "branch", "checks", "summary"})
        self.assertEqual(d1["summary"], {"total": 1, "pass": 1, "warn": 0, "fail": 0})

    def test_summary_counts(self):
        results = [_result("a", "pass"), _result("b", "warn", 2), _result("c", "fail", 1)]
        s = local_ci.build_document(results, "main")["summary"]
        self.assertEqual(s, {"total": 3, "pass": 1, "warn": 1, "fail": 1})


class CliCase(unittest.TestCase):
    def test_list(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = local_ci.main(["list"])
        self.assertEqual(code, 0)
        self.assertIn("validate", buf.getvalue())

    def test_run_json_single(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = local_ci.main(["run", "--only", "validate", "--json"])
        self.assertIn(code, (0, 2))
        data = json.loads(buf.getvalue())
        self.assertEqual([c["id"] for c in data["checks"]], ["validate"])

    def test_unknown_id_exit_2(self):
        with redirect_stdout(io.StringIO()):
            code = local_ci.main(["run", "--only", "nope"])
        self.assertEqual(code, 2)

    def test_emit_writes_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.json"
            with redirect_stdout(io.StringIO()):
                code = local_ci.main(["run", "--only", "validate", "--emit", str(p)])
            self.assertIn(code, (0, 2))
            self.assertTrue(p.is_file())
            first = p.read_text(encoding="utf-8")
            json.loads(first)
            with redirect_stdout(io.StringIO()):
                local_ci.main(["run", "--only", "validate", "--emit", str(p)])
            self.assertEqual(first, p.read_text(encoding="utf-8"))

    def test_failing_check_exit_1(self):
        bad = local_ci.Check("bad", "bad", "ci",
                             (sys.executable, "-c", "import sys; sys.exit(1)"))
        with unittest.mock.patch.object(local_ci, "CHECKS", (bad,)), \
                redirect_stdout(io.StringIO()):
            code = local_ci.main(["run"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
