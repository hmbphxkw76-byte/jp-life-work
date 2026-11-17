"""分支命名规范与会话标识测试（BRANCH-NAMING v1.0）。

覆盖：会话短码派生、分支名生成与校验、pre-push / pre-commit 钩子入口、
钩子安装器（真实临时 git 仓库）。运行：python -m unittest discover -s engine/tests
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "engine" / "scripts" / "branch_naming.py"

spec = importlib.util.spec_from_file_location("branch_naming", TOOL)
assert spec and spec.loader
bn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bn)

UUID = "11111111-2222-3333-4444-555555555555"


class SidCase(unittest.TestCase):
    def test_uuid_sid_is_first8(self):
        self.assertEqual(bn.session_sid(UUID), "11111111")

    def test_non_uuid_sid_is_sha1_prefix(self):
        import hashlib
        self.assertEqual(
            bn.session_sid("user@host"),
            hashlib.sha1(b"user@host").hexdigest()[:8],
        )

    def test_task_branch_format(self):
        self.assertEqual(bn.task_branch("demo", UUID), "task/demo-11111111")

    def test_sid_of(self):
        self.assertEqual(bn.sid_of("task/demo-11111111"), "11111111")
        self.assertIsNone(bn.sid_of("task/demo"))
        self.assertIsNone(bn.sid_of("main"))


class ValidateCase(unittest.TestCase):
    def test_valid(self):
        ok, msg = bn.validate_branch("task/demo-11111111")
        self.assertTrue(ok, msg)

    def test_invalid_shapes(self):
        for bad in (
            "task/demo",                # 缺 sid
            "task/demo-1111111",        # sid 少一位
            "task/demo-111111111",      # sid 多一位
            "task/demo-G1111111",       # sid 非十六进制
            "task/Demo-11111111",       # slug 大写
            "task/-demo-11111111",      # slug 以连字符开头
            "task/demo_1-11111111",     # slug 含下划线
            "task/demo-11111111-extra", # 多余段
        ):
            ok, _ = bn.validate_branch(bad)
            self.assertFalse(ok, bad)

    def test_exempt(self):
        for name in ("main", "master", "HEAD"):
            ok, _ = bn.validate_branch(name)
            self.assertTrue(ok, name)

    def test_non_task_default_allow_with_strict_block(self):
        ok, _ = bn.validate_branch("feature/x")
        self.assertTrue(ok)
        os.environ[bn.STRICT_ENV] = "1"
        try:
            ok, msg = bn.validate_branch("feature/x")
            self.assertFalse(ok)
            self.assertIn("非任务分支", msg)
        finally:
            os.environ.pop(bn.STRICT_ENV, None)

    def test_session_mismatch(self):
        self.assertTrue(bn.session_mismatch("task/demo-aaaaaaaa", UUID))
        self.assertFalse(bn.session_mismatch("task/demo-11111111", UUID))


class PrePushCase(unittest.TestCase):
    def _run(self, lines):
        return bn.hook_pre_push(lines)

    def test_block_invalid_task_branch(self):
        rc = self._run([
            "refs/heads/task/demo 1111111111111111111111111111111111111111 "
            "refs/heads/main 2222222222222222222222222222222222222222"
        ])
        self.assertEqual(rc, 1)

    def test_allow_valid_task_and_main(self):
        rc = self._run([
            "refs/heads/task/demo-11111111 " + "1" * 40 + " refs/heads/main " + "2" * 40,
            "refs/heads/main " + "1" * 40 + " refs/heads/main " + "2" * 40,
        ])
        self.assertEqual(rc, 0)

    def test_allow_delete_and_non_head_refs(self):
        rc = self._run([
            "refs/heads/task/demo " + "0" * 40 + " refs/heads/demo " + "0" * 40,
            "(delete) " + "0" * 40 + " refs/tags/v1 " + "0" * 40,
        ])
        self.assertEqual(rc, 0)

    def test_strict_blocks_non_task(self):
        os.environ[bn.STRICT_ENV] = "1"
        try:
            rc = self._run([
                "refs/heads/feature/x " + "1" * 40 + " refs/heads/main " + "2" * 40
            ])
            self.assertEqual(rc, 1)
        finally:
            os.environ.pop(bn.STRICT_ENV, None)


class HookInstallCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="branch-naming-test-")
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        subprocess.run(["git", "init", "-q", "-b", "main", self._tmp], check=True)
        self.hooks = bn.hooks_dir(Path(self._tmp))

    def test_install_check_uninstall(self):
        self.assertTrue(bn.install_hooks(cwd=Path(self._tmp)))
        self.assertTrue((self.hooks / "pre-push").is_file())
        self.assertTrue((self.hooks / "pre-commit").is_file())
        self.assertTrue(bn.install_hooks(check=True, cwd=Path(self._tmp)))
        self.assertTrue(bn.install_hooks(uninstall=True, cwd=Path(self._tmp)))
        self.assertFalse((self.hooks / "pre-push").exists())
        self.assertFalse(bn.install_hooks(check=True, cwd=Path(self._tmp)))

    def test_uninstall_refuses_modified(self):
        bn.install_hooks(cwd=Path(self._tmp))
        (self.hooks / "pre-push").write_text("# 改过\n", encoding="utf-8")
        with self.assertRaises(bn.NamingError):
            bn.install_hooks(uninstall=True, cwd=Path(self._tmp))
        self.assertTrue((self.hooks / "pre-push").exists())
        self.assertTrue(bn.install_hooks(uninstall=True, force=True, cwd=Path(self._tmp)))
        self.assertFalse((self.hooks / "pre-push").exists())


class HookPreCommitCase(unittest.TestCase):
    """真实临时仓库：当前分支名校验。"""

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="branch-naming-commit-")
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        env = {**os.environ, "CATPAW_CONVERSATION_ID": UUID}
        subprocess.run(["git", "init", "-q", "-b", "main", self._tmp], check=True, env=env)
        self._cwd = os.getcwd()
        os.chdir(self._tmp)
        self.addCleanup(os.chdir, self._cwd)

    def test_main_allowed(self):
        self.assertEqual(bn.hook_pre_commit(), 0)

    def test_invalid_task_branch_blocked(self):
        subprocess.run(["git", "checkout", "-q", "-b", "task/bad"], check=True)
        self.assertEqual(bn.hook_pre_commit(), 1)

    def test_valid_task_branch_allowed(self):
        subprocess.run(["git", "checkout", "-q", "-b", "task/ok-11111111"], check=True)
        self.assertEqual(bn.hook_pre_commit(), 0)


class CliCase(unittest.TestCase):
    def test_session_and_check(self):
        env = {**os.environ, "CATPAW_CONVERSATION_ID": UUID}
        proc = subprocess.run(
            [sys.executable, str(TOOL), "session"], capture_output=True, text=True, env=env
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("11111111", proc.stdout)

        proc = subprocess.run(
            [sys.executable, str(TOOL), "check", "task/ok-11111111", "task/bad"],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("BAD task/bad", proc.stdout)


if __name__ == "__main__":
    unittest.main()
