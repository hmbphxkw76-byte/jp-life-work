"""并行协作 / 清理 / 推送工具的单元级覆盖补强。

只直接调用各 tools/ 脚本的 ``cmd_*`` / 纯函数，用 ``unittest.mock`` 替换 git 与
子进程，或仅在 tempfile 临时目录里构造状态；不触碰真实仓库文件、不发起网络请求。

覆盖重点（按缺口从大到小）：
  - tools/workflow_guard.py：``_run`` / ``git`` / ``push_with_failover`` / ``Lock`` /
    任务登记表 / 各 ``cmd_*`` 分支 / ``main``；
  - tools/git_push.py：``_run_push`` / ``main`` / ``build_parser``；
  - tools/cleanup_workspace.py：``Residue.size`` / ``_tracked_paths`` / ``_is_tracked`` /
    ``_human`` / ``clean`` / ``.git`` 剪枝 / 符号链接跳过；
  - tools/run_tests_parallel.py：``_modules`` / ``_run_module`` / 分片 / 并行 / 汇总。
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "prompts-tools" / "tools"))


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


wg = _load("workflow_guard", "tools/workflow_guard.py")
gp = _load("git_push", "tools/git_push.py")
cw = _load("cleanup_workspace", "tools/cleanup_workspace.py")
rtp = _load("run_tests_parallel", "tools/run_tests_parallel.py")

# 固定会话 ID：task start 自动追加 sid，分支名可断言
SESSION_ID = "11111111-2222-3333-4444-555555555555"
DEMO_BRANCH = "task/demo-11111111"


def cp(rc: int, out: str = "", err: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(["git"], rc, out, err)


class FakeGit:
    """按参数元组返回预设结果的 git 替身。"""

    def __init__(self, responses: dict | None = None, default=(0, "", "")):
        self.responses = {tuple(k): tuple(v) for k, v in (responses or {}).items()}
        self.default = tuple(default)
        self.calls: list[tuple[list[str], object]] = []

    def __call__(self, args, cwd=None, check=True):
        args = list(args)
        self.calls.append((args, cwd))
        rc, out, err = self.responses.get(tuple(args), self.default)
        return cp(rc, out, err)

    def called(self, *args) -> bool:
        return any(c[0] == list(args) for c in self.calls)


def merge_args(**kw) -> argparse.Namespace:
    base = dict(name="demo", cleanup=False, no_verify=True, verify_cmd=None,
                ff_only=False, wait=0, force=False, stale_timeout=1800,
                remote="origin", push_fallback="origin-https")
    base.update(kw)
    return argparse.Namespace(**base)


class TempCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="cov-wf-")
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)


# ──────────────────────────────────────────────
# workflow_guard：基础工具
# ──────────────────────────────────────────────
class TestCovWgRunAndGit(TempCase):
    def test_run_shell_string_passthrough(self):
        with mock.patch.object(wg.subprocess, "run", return_value=cp(0, "ok")) as run:
            proc = wg._run("echo hi", check=False, shell=True)
        self.assertEqual(proc.returncode, 0)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], "echo hi")
        self.assertTrue(run.call_args.kwargs["shell"])

    def test_run_sequence_and_check_raises(self):
        with mock.patch.object(wg.subprocess, "run", return_value=cp(0)) as run:
            wg._run(["git", "status"], cwd=self.root, check=True)
        self.assertEqual(run.call_args.args[0], ["git", "status"])
        with mock.patch.object(wg.subprocess, "run", return_value=cp(2, "", "boom")):
            with self.assertRaises(wg.GuardError):
                wg._run(["git", "nope"], check=True)

    def test_git_wrapper_prefixes_git(self):
        with mock.patch.object(wg, "_run", return_value=cp(0)) as run:
            wg.git(["status"], cwd=self.root, check=False)
        self.assertEqual(run.call_args.args[0], ["git", "status"])
        self.assertEqual(run.call_args.kwargs["cwd"], self.root)
        self.assertFalse(run.call_args.kwargs["check"])

    def test_find_push_script_prefers_cwd(self):
        (self.root / "tools").mkdir()
        local = self.root / "tools" / "git_push.py"
        local.write_text("# local\n", encoding="utf-8")
        self.assertEqual(wg._find_push_script(self.root), local)

    def test_find_push_script_falls_back_to_module_dir(self):
        self.assertEqual(wg._find_push_script(self.root / "nope"),
                         Path(wg.__file__).resolve().with_name("git_push.py"))

    def test_find_push_script_none(self):
        with mock.patch.object(wg.Path, "exists", return_value=False):
            self.assertIsNone(wg._find_push_script(self.root))

    def test_push_with_failover_degrades_without_script(self):
        with mock.patch.object(wg, "_find_push_script", return_value=None), \
                mock.patch.object(wg, "git", return_value=cp(0)) as git:
            proc = wg.push_with_failover(self.root, "origin", ["HEAD:main"],
                                         force_with_lease=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(git.call_args.args[0],
                         ["push", "--force-with-lease", "origin", "HEAD:main"])

    def test_push_with_failover_uses_script(self):
        script = self.root / "git_push.py"
        script.write_text("# script\n", encoding="utf-8")
        with mock.patch.object(wg, "_find_push_script", return_value=script), \
                mock.patch.object(wg, "_run", return_value=cp(0, "out\n", "err\n")) as run:
            proc = wg.push_with_failover(self.root, "origin", ["HEAD:main"],
                                         force_with_lease=True)
        self.assertEqual(proc.returncode, 0)
        argv = run.call_args.args[0]
        self.assertEqual(argv[:2], [sys.executable, str(script)])
        self.assertIn("--force-with-lease", argv)
        self.assertIn("HEAD:main", argv)

    def test_push_with_failover_script_failure_returned(self):
        script = self.root / "git_push.py"
        script.write_text("# script\n", encoding="utf-8")
        with mock.patch.object(wg, "_find_push_script", return_value=script), \
                mock.patch.object(wg, "_run", return_value=cp(1, "", "no net")):
            proc = wg.push_with_failover(self.root, "origin", ["main"])
        self.assertEqual(proc.returncode, 1)

    def test_repo_root_and_common_git_dir(self):
        with mock.patch.object(wg, "git", return_value=cp(0, "/tmp/repo\n")):
            self.assertEqual(wg.repo_root(), Path("/tmp/repo").resolve())
        with mock.patch.object(wg, "git", return_value=cp(0, "../repo.git\n")):
            self.assertEqual(wg.common_git_dir(Path("/tmp/work")), Path("/tmp/repo.git").resolve())

    def test_state_dir_creates_directory(self):
        git_dir = self.root / "repo.git"
        git_dir.mkdir()
        with mock.patch.object(wg, "common_git_dir", return_value=git_dir):
            d = wg.state_dir(self.root)
        self.assertEqual(d, git_dir / "workflow-guard")
        self.assertTrue(d.is_dir())

    def test_current_owner_prefers_conversation_id(self):
        with mock.patch.dict(os.environ, {"CATPAW_CONVERSATION_ID": "abc"}):
            self.assertEqual(wg.current_owner(), "catpaw:abc")

    def test_current_owner_user_host_and_pid_fallback(self):
        env = {k: v for k, v in os.environ.items() if k != "CATPAW_CONVERSATION_ID"}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(wg.getpass, "getuser", return_value="u"), \
                mock.patch.object(wg.socket, "gethostname", return_value="h"):
            self.assertEqual(wg.current_owner(), "u@h")
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(wg.getpass, "getuser", side_effect=OSError("x")):
            self.assertTrue(wg.current_owner().startswith("pid:"))


# ──────────────────────────────────────────────
# workflow_guard：Lock
# ──────────────────────────────────────────────
class TestCovWgLock(TempCase):
    def _lock(self, name="checkout.lock", timeout=1800):
        return wg.Lock(self.root / name, "checkout", stale_timeout=timeout)

    def test_read_invalid_json_and_non_dict(self):
        p = self.root / "a.lock"
        p.write_text("{not json", encoding="utf-8")
        self.assertIsNone(self._lock("a.lock").read())
        p.write_text('["x"]', encoding="utf-8")
        self.assertIsNone(self._lock("a.lock").read())

    def test_stale_missing_and_old_and_fresh(self):
        lock = self._lock("missing.lock")
        self.assertTrue(lock._stale(None))
        p = self.root / "old.lock"
        p.write_text('{"owner": "x"}', encoding="utf-8")
        old = 10_000.0
        os.utime(p, (old, old))
        self.assertTrue(self._lock("old.lock")._stale({"owner": "x"}))
        fresh = self.root / "fresh.lock"
        fresh.write_text('{"owner": "x"}', encoding="utf-8")
        self.assertFalse(self._lock("fresh.lock")._stale({"owner": "x"}))

    def test_stale_stat_oserror(self):
        p = self.root / "s.lock"
        p.write_text('{"owner": "x"}', encoding="utf-8")
        with mock.patch.object(Path, "stat", side_effect=OSError("x")):
            self.assertTrue(self._lock("s.lock")._stale({"owner": "x"}))

    def test_busy_msg_variants(self):
        lock = self._lock()
        self.assertIn("不可读", lock._busy_msg(None))
        msg = lock._busy_msg({"owner": "u", "pid": 1, "op": "op", "acquired": "t"})
        self.assertIn("u", msg)
        self.assertIn("op", msg)

    def test_acquire_creates_payload(self):
        lock = self._lock()
        payload = lock.acquire("owner-x", "测试")
        self.assertEqual(payload["scope"], "checkout")
        self.assertEqual(payload["owner"], "owner-x")
        self.assertEqual(payload["op"], "测试")
        self.assertTrue(lock.path.exists())
        self.assertEqual(lock.read()["owner"], "owner-x")

    def test_acquire_force_replaces_existing(self):
        lock = self._lock()
        lock.acquire("first", "op")
        payload = lock.acquire("second", "op", force=True)
        self.assertEqual(payload["owner"], "second")
        self.assertEqual(lock.read()["owner"], "second")

    def test_acquire_wait_zero_raises_when_busy(self):
        lock = self._lock()
        lock.acquire("first", "op")
        with self.assertRaises(wg.GuardError) as ctx:
            lock.acquire("second", "op", wait=0)
        self.assertIn("被占用", str(ctx.exception))

    def test_acquire_unlink_race_continues(self):
        lock = self._lock()
        lock.acquire("first", "op")
        fd = os.open(self.root / "dummy", os.O_CREAT | os.O_WRONLY)
        self.addCleanup(os.close, fd)
        with mock.patch.object(Path, "unlink", side_effect=FileNotFoundError), \
                mock.patch.object(os, "open", side_effect=[FileExistsError, fd]), \
                mock.patch.object(os, "fdopen", lambda f, *a, **k: open(os.devnull, "w")):
            payload = lock.acquire("second", "op", force=True)
        self.assertEqual(payload["owner"], "second")

    def test_release_variants(self):
        lock = self._lock()
        lock.release("nobody")  # 无文件：静默返回
        lock.acquire("owner-x", "op")
        with self.assertRaises(wg.GuardError):
            lock.release("intruder")
        lock.release("intruder", force=True)
        self.assertFalse(lock.path.exists())

    def test_release_missing_file_is_noop(self):
        lock = self._lock()
        lock.acquire("owner-x", "op")
        with mock.patch.object(Path, "unlink", side_effect=FileNotFoundError):
            lock.release("owner-x")  # 不抛错

    def test_lock_for_unknown_scope(self):
        with self.assertRaises(wg.GuardError):
            wg._lock_for(self.root, "nope", 1800)


# ──────────────────────────────────────────────
# workflow_guard：任务登记表与纯函数
# ──────────────────────────────────────────────
class TestCovWgRegistry(TempCase):
    def test_load_tasks_missing_invalid_nonlist(self):
        self.assertEqual(wg.load_tasks(self.root), [])
        wg.save_tasks(self.root, [{"name": "a"}])
        self.assertEqual(wg.load_tasks(self.root), [{"name": "a"}])
        (self.root / "tasks.json").write_text("{bad", encoding="utf-8")
        self.assertEqual(wg.load_tasks(self.root), [])
        (self.root / "tasks.json").write_text('{"a": 1}', encoding="utf-8")
        self.assertEqual(wg.load_tasks(self.root), [])

    def test_save_tasks_writes_json(self):
        wg.save_tasks(self.root, [{"name": "a", "分支": "任务/a"}])
        data = json.loads((self.root / "tasks.json").read_text(encoding="utf-8"))
        self.assertEqual(data[0]["name"], "a")

    def test_find_task(self):
        tasks = [{"name": "a"}, {"name": "b"}]
        self.assertEqual(wg.find_task(tasks, "b"), {"name": "b"})
        self.assertIsNone(wg.find_task(tasks, "c"))

    def test_worktree_path(self):
        self.assertEqual(wg._worktree_path(Path("/r"), "x"), Path("/r/.worktrees/x"))

    def test_default_base_remote_then_local(self):
        with mock.patch.object(wg, "git", return_value=cp(0)):
            self.assertEqual(wg.default_base(Path("/r")), "origin/main")
        with mock.patch.object(wg, "git", return_value=cp(1)):
            self.assertEqual(wg.default_base(Path("/r")), "main")

    def test_task_name_regex_boundary(self):
        self.assertTrue(wg.TASK_NAME_RE.match("a" * 63))
        self.assertFalse(wg.TASK_NAME_RE.match("a" * 64))
        self.assertTrue(wg.TASK_NAME_RE.match("0-9"))


# ──────────────────────────────────────────────
# workflow_guard：task / lock / status 命令
# ──────────────────────────────────────────────
class WgCmdCase(TempCase):
    def setUp(self) -> None:
        super().setUp()
        self.state = self.root / "workflow-guard"
        self.state.mkdir(parents=True)
        p1 = mock.patch.object(wg, "repo_root", return_value=self.root)
        p2 = mock.patch.object(wg, "state_dir", return_value=self.state)
        p1.start(); p2.start()
        self.addCleanup(p1.stop); self.addCleanup(p2.stop)

    def _ns(self, **kw):
        base = dict(scope="checkout", op=None, wait=0, force=False, stale_timeout=1800)
        base.update(kw)
        return argparse.Namespace(**base)


class TestCovWgTaskCmd(WgCmdCase):
    def setUp(self) -> None:
        super().setUp()
        p = mock.patch.dict(os.environ, {"CATPAW_CONVERSATION_ID": SESSION_ID})
        p.start()
        self.addCleanup(p.stop)

    def _start_args(self, name="demo", no_worktree=False, base=None):
        return argparse.Namespace(name=name, no_worktree=no_worktree,
                                  base=base, remote="origin")

    def test_start_no_worktree(self):
        git = FakeGit({
            ("rev-parse", "--verify", "--quiet", DEMO_BRANCH): (1, "", ""),
            ("rev-parse", "--verify", "--quiet", "task/demo"): (1, "", ""),
        })
        with mock.patch.object(wg, "git", git), \
                mock.patch.object(wg, "default_base", return_value="origin/main"):
            rc = wg.cmd_task_start(self._start_args(no_worktree=True))
        self.assertEqual(rc, 0)
        tasks = wg.load_tasks(self.state)
        self.assertEqual(tasks[0]["branch"], DEMO_BRANCH)
        self.assertEqual(tasks[0]["session"], SESSION_ID)
        self.assertIsNone(tasks[0]["worktree"])
        self.assertEqual(tasks[0]["status"], "active")

    def test_start_with_worktree(self):
        git = FakeGit({
            ("rev-parse", "--verify", "--quiet", DEMO_BRANCH): (1, "", ""),
            ("rev-parse", "--verify", "--quiet", "task/demo"): (1, "", ""),
        })
        with mock.patch.object(wg, "git", git), \
                mock.patch.object(wg, "default_base", return_value="main"):
            rc = wg.cmd_task_start(self._start_args())
        self.assertEqual(rc, 0)
        wt = self.root / ".worktrees" / "demo"
        self.assertEqual(wg.load_tasks(self.state)[0]["worktree"], str(wt))
        self.assertTrue(git.called("worktree", "add", "-b", DEMO_BRANCH, str(wt), "main"))

    def test_start_invalid_name(self):
        with self.assertRaises(wg.GuardError) as ctx:
            wg.cmd_task_start(self._start_args(name="Bad Name"))
        self.assertIn("不合法", str(ctx.exception))

    def test_start_duplicate(self):
        wg.save_tasks(self.state, [{"name": "demo"}])
        with self.assertRaises(wg.GuardError) as ctx:
            wg.cmd_task_start(self._start_args(no_worktree=True))
        self.assertIn("已存在", str(ctx.exception))

    def test_start_branch_exists(self):
        git = FakeGit({
            ("rev-parse", "--verify", "--quiet", DEMO_BRANCH): (0, "", ""),
            ("rev-parse", "--verify", "--quiet", "task/demo"): (1, "", ""),
        })
        with mock.patch.object(wg, "git", git):
            with self.assertRaises(wg.GuardError) as ctx:
                wg.cmd_task_start(self._start_args(no_worktree=True))
        self.assertIn("分支已存在", str(ctx.exception))

    def test_start_worktree_dir_exists(self):
        (self.root / ".worktrees" / "demo").mkdir(parents=True)
        git = FakeGit({
            ("rev-parse", "--verify", "--quiet", DEMO_BRANCH): (1, "", ""),
            ("rev-parse", "--verify", "--quiet", "task/demo"): (1, "", ""),
        })
        with mock.patch.object(wg, "git", git):
            with self.assertRaises(wg.GuardError) as ctx:
                wg.cmd_task_start(self._start_args())
        self.assertIn("工作树目录已存在", str(ctx.exception))

    def test_stop_not_found(self):
        with self.assertRaises(wg.GuardError):
            wg.cmd_task_stop(argparse.Namespace(name="nope", force=False, remote="origin"))

    def test_stop_unmerged_blocked(self):
        wg.save_tasks(self.state, [{"name": "demo", "branch": "task/demo",
                                    "worktree": None, "base": "origin/main"}])
        git = FakeGit({("merge-base", "--is-ancestor", "task/demo", "origin/main"): (1, "", "")})
        with mock.patch.object(wg, "git", git):
            with self.assertRaises(wg.GuardError) as ctx:
                wg.cmd_task_stop(argparse.Namespace(name="demo", force=False, remote="origin"))
        self.assertIn("尚未合入", str(ctx.exception))

    def test_stop_merged_without_worktree(self):
        wg.save_tasks(self.state, [{"name": "demo", "branch": "task/demo",
                                    "worktree": None, "base": "origin/main"}])
        git = FakeGit({("merge-base", "--is-ancestor", "task/demo", "origin/main"): (0, "", "")})
        with mock.patch.object(wg, "git", git):
            rc = wg.cmd_task_stop(argparse.Namespace(name="demo", force=False, remote="origin"))
        self.assertEqual(rc, 0)
        self.assertEqual(wg.load_tasks(self.state), [])
        self.assertTrue(git.called("branch", "-D", "task/demo"))

    def test_stop_dirty_worktree_force(self):
        wt = self.root / ".worktrees" / "demo"
        wt.mkdir(parents=True)
        (wt / "x.txt").write_text("x", encoding="utf-8")
        wg.save_tasks(self.state, [{"name": "demo", "branch": "task/demo",
                                    "worktree": str(wt), "base": "origin/main"}])
        git = FakeGit({
            ("merge-base", "--is-ancestor", "task/demo", "origin/main"): (0, "", ""),
            ("status", "--porcelain"): (0, " M x.txt", ""),
        })
        with mock.patch.object(wg, "git", git):
            with self.assertRaises(wg.GuardError):
                wg.cmd_task_stop(argparse.Namespace(name="demo", force=False, remote="origin"))
            rc = wg.cmd_task_stop(argparse.Namespace(name="demo", force=True, remote="origin"))
        self.assertEqual(rc, 0)
        self.assertTrue(git.called("worktree", "remove", "--force", str(wt)))

    def test_task_list_empty_and_nonempty(self):
        git = FakeGit({("worktree", "list"): (0, "/repo\n", "")})
        with mock.patch.object(wg, "git", git), \
                mock.patch.object(wg, "load_tasks", return_value=[]):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(wg.cmd_task_list(argparse.Namespace()), 0)
        self.assertIn("无登记任务", out.getvalue())
        tasks = [{"name": "demo", "branch": "task/demo", "worktree": None,
                  "status": "active", "created": "2026-01-01"}]
        with mock.patch.object(wg, "git", git), \
                mock.patch.object(wg, "load_tasks", return_value=tasks):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(wg.cmd_task_list(argparse.Namespace()), 0)
        self.assertIn("demo", out.getvalue())


class TestCovWgLockCmd(WgCmdCase):
    def test_acquire_release_status(self):
        rc = wg.cmd_lock_acquire(self._ns(op="测试"))
        self.assertEqual(rc, 0)
        self.assertTrue((self.state / "checkout.lock").exists())
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(wg.cmd_lock_status(self._ns()), 0)
        self.assertIn("占用中", out.getvalue())
        self.assertEqual(wg.cmd_lock_release(self._ns()), 0)
        self.assertFalse((self.state / "checkout.lock").exists())

    def test_release_foreign_owner(self):
        wg.cmd_lock_acquire(self._ns(op="a"))
        with mock.patch.object(wg, "current_owner", return_value="intruder"):
            with self.assertRaises(wg.GuardError):
                wg.cmd_lock_release(self._ns(force=False))
        self.assertTrue((self.state / "checkout.lock").exists())

    def test_run_requires_command(self):
        with self.assertRaises(wg.GuardError):
            wg.cmd_lock_run(self._ns(cmd=[]))

    def test_run_executes_and_releases(self):
        with mock.patch.object(wg, "_run", return_value=cp(0)) as run:
            rc = wg.cmd_lock_run(self._ns(cmd=["--", "echo", "hi"]))
        self.assertEqual(rc, 0)
        self.assertEqual(run.call_args.args[0], ["echo", "hi"])
        self.assertFalse((self.state / "checkout.lock").exists())

    def test_run_returns_child_exit_code(self):
        with mock.patch.object(wg, "_run", return_value=cp(3)):
            self.assertEqual(wg.cmd_lock_run(self._ns(cmd=["false"])), 3)


class TestCovWgStatus(WgCmdCase):
    def test_status_outputs_tasks_and_locks(self):
        wg.save_tasks(self.state, [{"name": "demo", "branch": "task/demo",
                                    "worktree": None, "status": "active"}])
        git = FakeGit({("worktree", "list"): (0, "/repo\n", "")})
        with mock.patch.object(wg, "git", git):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(wg.cmd_status(self._ns()), 0)
        text = out.getvalue()
        self.assertIn("demo", text)
        self.assertIn("checkout", text)


# ──────────────────────────────────────────────
# workflow_guard：merge
# ──────────────────────────────────────────────
class TestCovWgMerge(WgCmdCase):
    def setUp(self) -> None:
        super().setUp()
        self.wt = self.root / ".worktrees" / "_merge"
        self.git = FakeGit()
        self._gp = mock.patch.object(wg, "git", self.git)
        self._gp.start()
        self.addCleanup(self._gp.stop)

    def _save_task(self):
        wg.save_tasks(self.state, [{"name": "demo", "branch": "task/demo",
                                    "worktree": None, "base": "origin/main",
                                    "status": "active"}])

    def test_cleanup_without_worktree(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(wg.cmd_merge(merge_args(cleanup=True)), 0)
        self.assertIn("无合并工作树", out.getvalue())

    def test_cleanup_removes_existing(self):
        self.wt.mkdir(parents=True)
        with mock.patch.object(wg, "_remove_worktree") as rm:
            self.assertEqual(wg.cmd_merge(merge_args(cleanup=True)), 0)
        rm.assert_called_once()

    def test_unknown_branch_rejected(self):
        self.git.responses = {("rev-parse", "--verify", "--quiet", "nope"): (1, "", "")}
        with self.assertRaises(wg.GuardError) as ctx:
            wg.cmd_merge(merge_args(name="nope", no_verify=True))
        self.assertIn("分支不存在", str(ctx.exception))

    def test_existing_merge_worktree_blocks(self):
        self.wt.mkdir(parents=True)
        self.git.responses = {("rev-parse", "--verify", "--quiet", "demo"): (0, "", "")}
        with self.assertRaises(wg.GuardError) as ctx:
            wg.cmd_merge(merge_args())
        self.assertIn("合并工作树已存在", str(ctx.exception))

    def test_merge_happy_path_marks_merged(self):
        self._save_task()
        self.git.responses = {
            ("rev-parse", "--verify", "--quiet", "task/demo"): (0, "", ""),
            ("fetch", "origin", "main"): (0, "", ""),
            ("worktree", "add", "--detach", str(self.wt), "origin/main"): (0, "", ""),
            ("merge", "--no-ff", "--no-edit", "task/demo"): (0, "", ""),
            ("rev-parse", "HEAD"): (0, "abc123def456\n", ""),
        }
        with mock.patch.object(wg, "push_with_failover", return_value=cp(0)) as push:
            rc = wg.cmd_merge(merge_args())
        self.assertEqual(rc, 0)
        task = wg.load_tasks(self.state)[0]
        self.assertEqual(task["status"], "merged")
        self.assertEqual(task["merged_sha"], "abc123def456")
        self.assertTrue(push.call_args.kwargs["force_with_lease"])

    def test_merge_ff_only(self):
        self.git.responses = {
            ("rev-parse", "--verify", "--quiet", "demo"): (0, "", ""),
            ("fetch", "origin", "main"): (0, "", ""),
            ("worktree", "add", "--detach", str(self.wt), "origin/main"): (0, "", ""),
            ("merge", "--ff-only", "demo"): (0, "", ""),
            ("rev-parse", "HEAD"): (0, "sha\n", ""),
        }
        with mock.patch.object(wg, "push_with_failover", return_value=cp(0)):
            self.assertEqual(wg.cmd_merge(merge_args(ff_only=True)), 0)
        self.assertTrue(self.git.called("merge", "--ff-only", "demo"))

    def test_merge_conflict_keeps_worktree(self):
        self.git.responses = {
            ("rev-parse", "--verify", "--quiet", "demo"): (0, "", ""),
            ("fetch", "origin", "main"): (0, "", ""),
            ("worktree", "add", "--detach", str(self.wt), "origin/main"): (0, "", ""),
            ("merge", "--no-ff", "--no-edit", "demo"): (1, "", "conflict"),
        }
        err = io.StringIO()
        with redirect_stderr(err):
            rc = wg.cmd_merge(merge_args())
        self.assertEqual(rc, 1)
        self.assertIn("冲突", err.getvalue())
        self.assertIn("保留合并工作树", err.getvalue())

    def test_merge_verify_rc1_blocks(self):
        self.git.responses = {
            ("rev-parse", "--verify", "--quiet", "demo"): (0, "", ""),
            ("fetch", "origin", "main"): (0, "", ""),
            ("worktree", "add", "--detach", str(self.wt), "origin/main"): (0, "", ""),
            ("merge", "--no-ff", "--no-edit", "demo"): (0, "", ""),
        }
        with mock.patch.object(wg, "push_with_failover") as push, \
                mock.patch.object(wg, "_run", return_value=cp(1)):
            rc = wg.cmd_merge(merge_args(no_verify=False, verify_cmd="check"))
        self.assertEqual(rc, 1)
        push.assert_not_called()

    def test_merge_verify_rc2_warns_and_passes(self):
        self.git.responses = {
            ("rev-parse", "--verify", "--quiet", "demo"): (0, "", ""),
            ("fetch", "origin", "main"): (0, "", ""),
            ("worktree", "add", "--detach", str(self.wt), "origin/main"): (0, "", ""),
            ("merge", "--no-ff", "--no-edit", "demo"): (0, "", ""),
            ("rev-parse", "HEAD"): (0, "sha\n", ""),
        }
        with mock.patch.object(wg, "push_with_failover", return_value=cp(0)), \
                mock.patch.object(wg, "_run", return_value=cp(2)):
            out = io.StringIO()
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                rc = wg.cmd_merge(merge_args(no_verify=False, verify_cmd="check"))
        self.assertEqual(rc, 0)
        self.assertIn("放行", out.getvalue())

    def test_merge_push_fail_then_remote_conflict(self):
        self.git.responses = {
            ("rev-parse", "--verify", "--quiet", "demo"): (0, "", ""),
            ("fetch", "origin", "main"): (0, "", ""),
            ("worktree", "add", "--detach", str(self.wt), "origin/main"): (0, "", ""),
            ("merge", "--no-ff", "--no-edit", "demo"): (0, "", ""),
            ("merge", "--no-ff", "--no-edit", "origin/main"): (1, "", "conflict"),
        }
        with mock.patch.object(wg, "push_with_failover", return_value=cp(1)):
            err = io.StringIO()
            with redirect_stderr(err):
                rc = wg.cmd_merge(merge_args())
        self.assertEqual(rc, 1)
        self.assertIn("整合远端 main 时冲突", err.getvalue())

    def test_merge_push_fail_twice_raises(self):
        self.git.responses = {
            ("rev-parse", "--verify", "--quiet", "demo"): (0, "", ""),
            ("fetch", "origin", "main"): (0, "", ""),
            ("worktree", "add", "--detach", str(self.wt), "origin/main"): (0, "", ""),
            ("merge", "--no-ff", "--no-edit", "demo"): (0, "", ""),
            ("merge", "--no-ff", "--no-edit", "origin/main"): (0, "", ""),
        }
        with mock.patch.object(wg, "push_with_failover", return_value=cp(1)):
            with self.assertRaises(wg.GuardError):
                wg.cmd_merge(merge_args())

    def test_merge_lock_busy(self):
        (self.state / "merge.lock").write_text('{"owner": "x"}', encoding="utf-8")
        self.git.responses = {("rev-parse", "--verify", "--quiet", "task/demo"): (0, "", "")}
        with self.assertRaises(wg.GuardError) as ctx:
            wg.cmd_merge(merge_args())
        self.assertIn("被占用", str(ctx.exception))

    def test_remove_worktree_calls(self):
        wg._remove_worktree(self.root, self.wt)
        self.assertTrue(self.git.called("worktree", "remove", "--force", str(self.wt)))
        self.assertTrue(self.git.called("worktree", "prune"))

    def test_merge_fail_hint(self):
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(wg._merge_fail_hint(self.wt), 1)
        self.assertIn("保留合并工作树", err.getvalue())

    def test_run_verify_default_missing(self):
        args = merge_args()
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(wg._run_verify(self.wt, args), 0)
        self.assertIn("跳过校验", out.getvalue())

    def test_run_verify_default_script(self):
        target = self.wt / "src" / "prompts-tools" / "tools" / "validate.py"
        target.parent.mkdir(parents=True)
        target.write_text("import sys; sys.exit(0)\n", encoding="utf-8")
        with mock.patch.object(wg, "_run", return_value=cp(0)) as run:
            self.assertEqual(wg._run_verify(self.wt, merge_args()), 0)
        self.assertEqual(run.call_args.args[0],
                         [sys.executable, "src/prompts-tools/tools/validate.py"])

    def test_run_verify_custom_cmd(self):
        with mock.patch.object(wg, "_run", return_value=cp(2)) as run:
            rc = wg._run_verify(self.wt, merge_args(no_verify=False,
                                                    verify_cmd="python -c 'pass'"))
        self.assertEqual(rc, 2)
        self.assertEqual(run.call_args.args[0], ["python", "-c", "pass"])


# ──────────────────────────────────────────────
# workflow_guard：sync / main
# ──────────────────────────────────────────────
class TestCovWgSync(WgCmdCase):
    def setUp(self) -> None:
        super().setUp()
        self.git = FakeGit()
        p = mock.patch.object(wg, "git", self.git)
        p.start()
        self.addCleanup(p.stop)

    def _args(self, **kw):
        base = dict(push_local=False, wait=0, force=False, stale_timeout=1800,
                    remote="origin", push_fallback="origin-https")
        base.update(kw)
        return argparse.Namespace(**base)

    def test_sync_up_to_date(self):
        self.git.responses = {
            ("fetch", "origin", "main"): (0, "", ""),
            ("rev-parse", "main"): (0, "sha\n", ""),
            ("rev-parse", "origin/main"): (0, "sha\n", ""),
        }
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(wg.cmd_sync(self._args()), 0)
        self.assertIn("一致", out.getvalue())

    def test_sync_fast_forward(self):
        self.git.responses = {
            ("fetch", "origin", "main"): (0, "", ""),
            ("rev-parse", "main"): (0, "a\n", ""),
            ("rev-parse", "origin/main"): (0, "b\n", ""),
            ("merge-base", "--is-ancestor", "main", "origin/main"): (0, "", ""),
            ("status", "--porcelain"): (0, "", ""),
            ("merge", "--ff-only", "origin/main"): (0, "", ""),
        }
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(wg.cmd_sync(self._args()), 0)
        self.assertIn("快进对齐", out.getvalue())

    def test_sync_dirty_refuses(self):
        self.git.responses = {
            ("fetch", "origin", "main"): (0, "", ""),
            ("rev-parse", "main"): (0, "a\n", ""),
            ("rev-parse", "origin/main"): (0, "b\n", ""),
            ("merge-base", "--is-ancestor", "main", "origin/main"): (0, "", ""),
            ("status", "--porcelain"): (0, " M x", ""),
        }
        with self.assertRaises(wg.GuardError) as ctx:
            wg.cmd_sync(self._args())
        self.assertIn("未提交改动", str(ctx.exception))

    def test_sync_ahead_reports(self):
        self.git.responses = {
            ("fetch", "origin", "main"): (0, "", ""),
            ("rev-parse", "main"): (0, "b\n", ""),
            ("rev-parse", "origin/main"): (0, "a\n", ""),
            ("merge-base", "--is-ancestor", "main", "origin/main"): (1, "", ""),
            ("merge-base", "--is-ancestor", "origin/main", "main"): (0, "", ""),
            ("rev-list", "--count", "origin/main..main"): (0, "2\n", ""),
        }
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(wg.cmd_sync(self._args()), 0)
        self.assertIn("领先远端 2 个提交", out.getvalue())

    def test_sync_push_local(self):
        self.git.responses = {
            ("fetch", "origin", "main"): (0, "", ""),
            ("rev-parse", "main"): (0, "b\n", ""),
            ("rev-parse", "origin/main"): (0, "a\n", ""),
            ("merge-base", "--is-ancestor", "main", "origin/main"): (1, "", ""),
            ("merge-base", "--is-ancestor", "origin/main", "main"): (0, "", ""),
            ("rev-list", "--count", "origin/main..main"): (0, "1\n", ""),
        }
        with mock.patch.object(wg, "push_with_failover", return_value=cp(0)) as push:
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(wg.cmd_sync(self._args(push_local=True)), 0)
        self.assertIn("已推送本地 main", out.getvalue())
        self.assertEqual(push.call_args.args[1:], ("origin", ["main"]))

    def test_sync_push_local_failure(self):
        self.git.responses = {
            ("fetch", "origin", "main"): (0, "", ""),
            ("rev-parse", "main"): (0, "b\n", ""),
            ("rev-parse", "origin/main"): (0, "a\n", ""),
            ("merge-base", "--is-ancestor", "main", "origin/main"): (1, "", ""),
            ("merge-base", "--is-ancestor", "origin/main", "main"): (0, "", ""),
            ("rev-list", "--count", "origin/main..main"): (0, "1\n", ""),
        }
        with mock.patch.object(wg, "push_with_failover", return_value=cp(1)):
            with self.assertRaises(wg.GuardError):
                wg.cmd_sync(self._args(push_local=True))

    def test_sync_diverged(self):
        self.git.responses = {
            ("fetch", "origin", "main"): (0, "", ""),
            ("rev-parse", "main"): (0, "b\n", ""),
            ("rev-parse", "origin/main"): (0, "a\n", ""),
            ("merge-base", "--is-ancestor", "main", "origin/main"): (1, "", ""),
            ("merge-base", "--is-ancestor", "origin/main", "main"): (1, "", ""),
        }
        with self.assertRaises(wg.GuardError) as ctx:
            wg.cmd_sync(self._args())
        self.assertIn("分叉", str(ctx.exception))

    def test_sync_lock_busy(self):
        (self.state / "checkout.lock").write_text('{"owner": "x"}', encoding="utf-8")
        with self.assertRaises(wg.GuardError) as ctx:
            wg.cmd_sync(self._args())
        self.assertIn("被占用", str(ctx.exception))


class TestCovWgMain(unittest.TestCase):
    def test_main_dispatches(self):
        parser = mock.Mock()
        parser.parse_args.return_value = argparse.Namespace(func=lambda a: 7)
        with mock.patch.object(wg, "build_parser", return_value=parser):
            self.assertEqual(wg.main(["x"]), 7)

    def test_main_no_func_prints_help(self):
        parser = mock.Mock()
        parser.parse_args.return_value = argparse.Namespace(func=None)
        with mock.patch.object(wg, "build_parser", return_value=parser):
            self.assertEqual(wg.main(["x"]), 1)
        parser.print_help.assert_called_once()

    def test_main_guard_error(self):
        def boom(_a):
            raise wg.GuardError("bad")

        parser = mock.Mock()
        parser.parse_args.return_value = argparse.Namespace(func=boom)
        err = io.StringIO()
        with mock.patch.object(wg, "build_parser", return_value=parser), \
                redirect_stderr(err):
            self.assertEqual(wg.main(["x"]), 1)
        self.assertIn("bad", err.getvalue())

    def test_main_keyboard_interrupt(self):
        def boom(_a):
            raise KeyboardInterrupt

        parser = mock.Mock()
        parser.parse_args.return_value = argparse.Namespace(func=boom)
        with mock.patch.object(wg, "build_parser", return_value=parser):
            self.assertEqual(wg.main(["x"]), 130)

    def test_build_parser_defaults(self):
        parser = wg.build_parser()
        ns = parser.parse_args(["task", "start", "demo"])
        self.assertIs(ns.func, wg.cmd_task_start)
        self.assertEqual(ns.remote, "origin")
        self.assertFalse(ns.no_worktree)
        ns = parser.parse_args(["lock", "run", "checkout", "--", "git", "status"])
        self.assertIs(ns.func, wg.cmd_lock_run)
        self.assertEqual(ns.cmd, ["git", "status"])
        ns = parser.parse_args(["merge", "demo", "--push-fallback", ""])
        self.assertEqual(ns.push_fallback, "")


# ──────────────────────────────────────────────
# git_push
# ──────────────────────────────────────────────
class TestCovGitPush(unittest.TestCase):
    def test_run_push_command_assembly(self):
        with mock.patch.object(gp.subprocess, "run", return_value=cp(0, "ok")) as run:
            code, out = gp._run_push("origin", ["HEAD:main"], True, True)
        self.assertEqual(code, 0)
        self.assertIn("ok", out)
        self.assertEqual(run.call_args.args[0],
                         ["git", "push", "--force-with-lease", "--dry-run",
                          "origin", "HEAD:main"])

    def test_run_push_failure_output_merged(self):
        with mock.patch.object(gp.subprocess, "run", return_value=cp(1, "", "boom")):
            code, out = gp._run_push("origin", ["main"], False, False)
        self.assertEqual(code, 1)
        self.assertIn("boom", out)

    def test_main_strips_empty_fallback(self):
        with mock.patch.object(sys, "argv", ["git_push.py", "--remote", "origin",
                                             "--fallback", "  ", "HEAD:main"]), \
                mock.patch.object(gp, "push_with_failover", return_value=0) as push:
            self.assertEqual(gp.main(), 0)
        self.assertIsNone(push.call_args.kwargs["fallback"])

    def test_main_default_fallback(self):
        with mock.patch.object(sys, "argv", ["git_push.py", "main"]), \
                mock.patch.object(gp, "push_with_failover", return_value=0) as push:
            self.assertEqual(gp.main(), 0)
        self.assertEqual(push.call_args.kwargs["fallback"], "origin-https")
        self.assertEqual(push.call_args.kwargs["refspecs"], ["main"])

    def test_build_parser_requires_refspec(self):
        with mock.patch.object(sys, "argv", ["git_push.py"]):
            with self.assertRaises(SystemExit):
                gp.build_parser().parse_args([])


# ──────────────────────────────────────────────
# cleanup_workspace
# ──────────────────────────────────────────────
class TestCovCleanupUnits(TempCase):
    def test_residue_size_dir_and_missing(self):
        d = self.root / "cache"
        d.mkdir()
        (d / "a.bin").write_bytes(b"12345")
        self.assertEqual(cw.Residue(d, "cache-dir").size, 5)
        self.assertEqual(cw.Residue(self.root / "nope", "temp-file").size, 0)

    def test_human_units(self):
        self.assertEqual(cw._human(0), "0 B")
        self.assertEqual(cw._human(1023), "1023 B")
        self.assertEqual(cw._human(1024), "1.0 KB")
        self.assertEqual(cw._human(1024 * 1024), "1.0 MB")
        self.assertEqual(cw._human(1024 ** 3), "1.0 GB")

    def test_tracked_paths_failures_return_none(self):
        with mock.patch("subprocess.run", side_effect=OSError("no git")):
            self.assertIsNone(cw._tracked_paths(self.root))
        err = subprocess.CalledProcessError(1, ["git"])
        with mock.patch("subprocess.run", side_effect=err):
            self.assertIsNone(cw._tracked_paths(self.root))

    def test_tracked_paths_parses_nul(self):
        proc = subprocess.CompletedProcess([], 0, b"a.py\0dir/b.py\0", "")
        with mock.patch("subprocess.run", return_value=proc):
            self.assertEqual(cw._tracked_paths(self.root), {"a.py", "dir/b.py"})

    def test_is_tracked(self):
        self.assertFalse(cw._is_tracked("x", None))
        self.assertTrue(cw._is_tracked("dir", {"dir/a.py"}))
        self.assertTrue(cw._is_tracked("dir/a.py", {"dir/a.py"}))
        self.assertFalse(cw._is_tracked("other", {"dir/a.py"}))

    def test_collect_prunes_git_and_collects_rules(self):
        (self.root / ".git" / "__pycache__").mkdir(parents=True)
        (self.root / ".git" / "__pycache__" / "x.pyc").write_text("x", encoding="utf-8")
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__" / "m.pyc").write_text("x", encoding="utf-8")
        (self.root / "desktop.ini").write_text("x", encoding="utf-8")
        (self.root / ".coverage").write_text("x", encoding="utf-8")
        (self.root / "mod$py.class").write_text("x", encoding="utf-8")
        items = cw.collect_residue(self.root)
        rels = {i.path.relative_to(self.root).as_posix() for i in items}
        self.assertNotIn(".git/__pycache__", rels)
        self.assertIn("__pycache__", rels)
        self.assertIn("desktop.ini", rels)
        self.assertIn(".coverage", rels)
        self.assertIn("mod$py.class", rels)

    def test_collect_generated_dirs(self):
        d = self.root / "src" / "vocabulary" / "data" / "sync-backups"
        d.mkdir(parents=True)
        (d / "b.md.bak").write_text("x", encoding="utf-8")
        items = cw.collect_residue(self.root)
        self.assertIn("generated-dir", {i.kind for i in items})

    def test_collect_skips_symlink(self):
        target = self.root / "real.tmp"
        target.write_text("x", encoding="utf-8")
        link = self.root / "link.tmp"
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            self.skipTest("当前平台无法创建符号链接")
        items = cw.collect_residue(self.root)
        rels = {i.path.relative_to(self.root).as_posix() for i in items}
        self.assertNotIn("link.tmp", rels)
        self.assertIn("real.tmp", rels)

    def test_clean_oserror_and_missing(self):
        d = self.root / "cache"
        d.mkdir()
        item = cw.Residue(d, "cache-dir")
        with mock.patch.object(cw, "ROOT", self.root), \
                mock.patch.object(cw.shutil, "rmtree", side_effect=OSError("locked")):
            n, freed, errors = cw.clean([item])
        self.assertEqual((n, freed), (0, 0))
        self.assertEqual(len(errors), 1)
        missing = cw.Residue(self.root / "gone", "temp-file")
        with mock.patch.object(cw, "ROOT", self.root), \
                mock.patch.object(Path, "unlink", side_effect=FileNotFoundError):
            n, freed, errors = cw.clean([missing])
        self.assertEqual((n, freed, errors), (0, 0, []))

    def test_main_check_quiet_with_residue(self):
        (self.root / "__pycache__").mkdir()
        (self.root / "__pycache__" / "m.pyc").write_text("x", encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out):
            code = cw.main(["--check", "--quiet", "--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("发现残留", out.getvalue())

    def test_main_check_quiet_clean(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = cw.main(["--check", "--quiet", "--root", str(self.root)])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "")


# ──────────────────────────────────────────────
# run_tests_parallel
# ──────────────────────────────────────────────
class TestCovRunTestsParallel(TempCase):
    def test_modules_lists_only_test_files(self):
        (self.root / "test_a.py").write_text("x", encoding="utf-8")
        (self.root / "test_b.py").write_text("x", encoding="utf-8")
        (self.root / "notes.txt").write_text("x", encoding="utf-8")
        with mock.patch.object(rtp, "TESTS_DIR", self.root):
            self.assertEqual(rtp._modules(), ["test_a", "test_b"])

    def test_run_module_success(self):
        proc = subprocess.CompletedProcess([], 0, "", "OK\n")
        with mock.patch.object(rtp, "ROOT", self.root), \
                mock.patch.object(rtp.subprocess, "run", return_value=proc) as run:
            mod, code, tail = rtp._run_module("test_a")
        self.assertEqual((mod, code), ("test_a", 0))
        self.assertIn("OK", tail)
        cmd = run.call_args.args[0]
        self.assertIn("-p", cmd)
        self.assertIn("test_a.py", cmd)
        self.assertEqual(run.call_args.kwargs["cwd"], str(self.root))

    def test_run_module_failure_tail(self):
        proc = subprocess.CompletedProcess([], 1, "", "boom\n")
        with mock.patch.object(rtp, "ROOT", self.root), \
                mock.patch.object(rtp.subprocess, "run", return_value=proc):
            mod, code, tail = rtp._run_module("test_a")
        self.assertEqual(code, 1)
        self.assertIn("boom", tail)

    def test_main_shard_selects_modules(self):
        seen: list[str] = []
        with mock.patch.object(rtp, "_modules", return_value=["a", "b", "c"]), \
                mock.patch.object(rtp, "_run_module",
                                  side_effect=lambda m: (seen.append(m) or (m, 0, ""))), \
                mock.patch.object(sys, "argv", ["rtp", "--shard", "1/2"]):
            self.assertEqual(rtp.main(), 0)
        self.assertEqual(seen, ["a", "c"])

    def test_main_no_modules(self):
        with mock.patch.object(rtp, "_modules", return_value=[]), \
                mock.patch.object(sys, "argv", ["rtp"]):
            self.assertEqual(rtp.main(), 0)

    def test_main_failure_exit_code(self):
        with mock.patch.object(rtp, "_modules", return_value=["a"]), \
                mock.patch.object(rtp, "_run_module", return_value=("a", 1, "bad")), \
                mock.patch.object(sys, "argv", ["rtp"]):
            self.assertEqual(rtp.main(), 1)

    def test_main_parallel_uses_executor(self):
        ex = mock.MagicMock()
        ex.__enter__.return_value = ex
        ex.map.return_value = [("a", 0, ""), ("b", 0, "")]
        with mock.patch.object(rtp, "_modules", return_value=["a", "b"]), \
                mock.patch.object(rtp, "ThreadPoolExecutor", return_value=ex) as tpe, \
                mock.patch.object(sys, "argv", ["rtp", "--workers", "2"]):
            self.assertEqual(rtp.main(), 0)
        tpe.assert_called_once_with(max_workers=2)
        ex.map.assert_called_once()


if __name__ == "__main__":
    unittest.main()
