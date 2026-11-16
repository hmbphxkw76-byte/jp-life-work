"""GitHub 双通道推送（git_push.py）测试。

用 mock 的 ``subprocess.run`` 精确验证调用序列：主通道成功只推一次；
主通道失败切备用通道；两条都失败时**恰好各试一次**（不重试）。
不触碰真实网络，也不触碰本仓库工作区。
"""
from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "git_push.py"

spec = importlib.util.spec_from_file_location("git_push", TOOL)
assert spec and spec.loader
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)


def _proc(rc: int, out: str = "", err: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], rc, out, err)


class TestPushWithFailover(unittest.TestCase):
    def _run(self, results, **kwargs):
        """返回 (push_with_failover 返回码, 实际调用命令列表)。"""
        calls: list[list[str]] = []

        def fake_run(cmd, **_kw):
            calls.append(list(cmd))
            idx = min(len(calls) - 1, len(results) - 1)
            rc, out, err = results[idx]
            return _proc(rc, out, err)

        with mock.patch.object(gp.subprocess, "run", side_effect=fake_run):
            code = gp.push_with_failover(**kwargs)
        return code, calls

    def test_primary_success_single_attempt(self):
        code, calls = self._run(
            [(0, "ok\n", "")], remote="origin", refspecs=["HEAD:main"],
            fallback="origin-https", force_with_lease=True,
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 1, "主通道成功时不应触碰备用通道")
        self.assertIn("origin", calls[0])
        self.assertIn("--force-with-lease", calls[0])
        self.assertIn("HEAD:main", calls[0])

    def test_failover_to_https_when_ssh_fails(self):
        code, calls = self._run(
            [(1, "", "ssh reset"), (0, "ok\n", "")],
            remote="origin", refspecs=["HEAD:main"], fallback="origin-https",
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 2)
        self.assertIn("origin", calls[0])
        self.assertIn("origin-https", calls[1])

    def test_both_fail_stops_without_retry(self):
        code, calls = self._run(
            [(1, "", "ssh reset"), (1, "", "https timeout")],
            remote="origin", refspecs=["HEAD:main"], fallback="origin-https",
        )
        self.assertEqual(code, 1)
        self.assertEqual(len(calls), 2, "两条通道各试一次后必须停止，不得重试")

    def test_no_fallback_single_attempt(self):
        code, calls = self._run(
            [(1, "", "boom")], remote="origin", refspecs=["main"], fallback=None,
        )
        self.assertEqual(code, 1)
        self.assertEqual(len(calls), 1)

    def test_dry_run_flag_forwarded(self):
        code, calls = self._run(
            [(0, "", "")], remote="origin", refspecs=["HEAD:main"],
            fallback="origin-https", dry_run=True,
        )
        self.assertEqual(code, 0)
        self.assertIn("--dry-run", calls[0])

    def test_default_remote_and_fallback(self):
        code, calls = self._run([(0, "", "")], remote="origin", refspecs=["main"])
        # 默认 fallback=origin-https，主通道成功故只推一次
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
