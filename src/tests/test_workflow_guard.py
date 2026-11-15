"""workflow_guard 三层隔离机制测试。

在临时目录里搭「裸 origin + 克隆」的最小仓库，真实跑 git，不触碰本仓库工作区。
覆盖：任务分支 / worktree、共享检出锁（占用 / 释放 / 强取 / 失效）、
串行合并（ happy path / 冲突保留工作树 / 校验阻断 / 清理 ）、sync（快进 / 脏拒绝 / 领先上报）。
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "workflow_guard.py"

spec = importlib.util.spec_from_file_location("workflow_guard", TOOL)
assert spec and spec.loader
wg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wg)

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Guard Test",
    "GIT_AUTHOR_EMAIL": "guard@example.com",
    "GIT_COMMITTER_NAME": "Guard Test",
    "GIT_COMMITTER_EMAIL": "guard@example.com",
    "CATPAW_CONVERSATION_ID": "",  # 让 owner 走 用户@主机 分支，避免宿主会话串味
}


def git_run(args, cwd=None, check=True, env=None):
    cmd = ["git", "-c", "user.name=Guard Test", "-c", "user.email=guard@example.com", *args]
    proc = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env or GIT_ENV,
    )
    if check and proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} 失败：{proc.stderr.strip()}")
    return proc


def tool_run(args, cwd, check=True, env=None):
    proc = subprocess.run(
        [sys.executable, str(TOOL), *args], cwd=str(cwd), capture_output=True,
        text=True, encoding="utf-8", errors="replace", env=env or GIT_ENV,
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"workflow_guard {' '.join(args)} 失败（{proc.returncode}）\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


class Repo:
    def __init__(self, path: Path):
        self.path = path

    def git(self, *args, check=True):
        return git_run(list(args), cwd=self.path, check=check)

    def tool(self, *args, check=True):
        return tool_run(list(args), cwd=self.path, check=check)

    def write(self, name: str, text: str) -> Path:
        p = self.path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def read(self, name: str) -> str:
        return (self.path / name).read_text(encoding="utf-8")

    def commit_all(self, msg: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-m", msg)

    def state(self) -> Path:
        return self.path / ".git" / "workflow-guard"

    def tasks(self) -> list[dict]:
        f = self.state() / "tasks.json"
        if not f.exists():
            return []
        return json.loads(f.read_text(encoding="utf-8"))


def make_repo(tmp: Path) -> Repo:
    """裸 origin + 克隆，origin/main 上有一个初始提交。"""
    origin = tmp / "origin.git"
    git_run(["init", "--bare", "-b", "main", str(origin)], cwd=tmp)
    seed = tmp / "seed"
    seed.mkdir()
    git_run(["init", "-b", "main"], cwd=seed)
    (seed / "README.md").write_text("# seed\n", encoding="utf-8")
    git_run(["add", "."], cwd=seed)
    git_run(["commit", "-m", "init"], cwd=seed)
    git_run(["remote", "add", "origin", str(origin)], cwd=seed)
    git_run(["push", "-u", "origin", "main"], cwd=seed)
    shutil.rmtree(seed, ignore_errors=True)
    work = tmp / "work"
    git_run(["clone", str(origin), str(work)], cwd=tmp)
    return Repo(work)


class TempRepoCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="wf-guard-test-")
        self.repo = make_repo(Path(self._tmp))

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)


# ──────────────────────────────────────────────
# 第 1 层：任务 / 分支隔离
# ──────────────────────────────────────────────
class TestTaskIsolation(TempRepoCase):
    def test_name_validation(self):
        for bad in ("Bad Name", "Upper", "", "a" * 64, "a_b"):
            proc = self.repo.tool("task", "start", bad, check=False)
            self.assertEqual(proc.returncode, 1, bad)
            self.assertIn("不合法", proc.stderr)

    def test_start_creates_branch_and_worktree(self):
        self.repo.tool("task", "start", "demo")
        self.assertEqual(
            self.repo.git("rev-parse", "--verify", "--quiet", "task/demo").returncode, 0
        )
        wt = self.repo.path / ".worktrees" / "demo"
        self.assertTrue(wt.is_dir())
        branch = git_run(["branch", "--show-current"], cwd=wt).stdout.strip()
        self.assertEqual(branch, "task/demo")
        tasks = self.repo.tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["name"], "demo")
        self.assertEqual(tasks[0]["branch"], "task/demo")
        self.assertEqual(tasks[0]["status"], "active")

    def test_start_no_worktree_creates_branch_only(self):
        self.repo.tool("task", "start", "demo", "--no-worktree")
        self.assertEqual(
            self.repo.git("rev-parse", "--verify", "--quiet", "task/demo").returncode, 0
        )
        self.assertFalse((self.repo.path / ".worktrees" / "demo").exists())
        self.assertIsNone(self.repo.tasks()[0]["worktree"])

    def test_duplicate_task_rejected(self):
        self.repo.tool("task", "start", "demo")
        proc = self.repo.tool("task", "start", "demo", check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("已存在", proc.stderr)

    def test_stop_blocks_unmerged(self):
        self.repo.tool("task", "start", "demo")
        wt = Repo(self.repo.path / ".worktrees" / "demo")
        wt.write("feat.txt", "x\n")
        wt.commit_all("feat")
        proc = self.repo.tool("task", "stop", "demo", check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("尚未合入", proc.stderr)

    def test_stop_force_removes_worktree_and_branch(self):
        self.repo.tool("task", "start", "demo")
        self.repo.tool("task", "stop", "demo", "--force")
        self.assertEqual(
            self.repo.git("rev-parse", "--verify", "--quiet", "task/demo",
                       check=False).returncode, 1
        )
        self.assertFalse((self.repo.path / ".worktrees" / "demo").exists())
        self.assertEqual(self.repo.tasks(), [])

    def test_stop_after_merge_ok(self):
        self.repo.tool("task", "start", "demo")
        wt = Repo(self.repo.path / ".worktrees" / "demo")
        wt.write("feat.txt", "x = 1\n")
        wt.commit_all("feat")
        self.repo.tool("merge", "demo", "--no-verify")
        self.repo.tool("task", "stop", "demo")
        self.assertEqual(self.repo.tasks(), [])


# ──────────────────────────────────────────────
# 第 3 层：共享检出锁
# ──────────────────────────────────────────────
class TestCheckoutLock(TempRepoCase):
    def test_acquire_release(self):
        self.repo.tool("lock", "acquire", "checkout", "--op", "测试")
        lock = self.repo.state() / "checkout.lock"
        self.assertTrue(lock.exists())
        data = json.loads(lock.read_text(encoding="utf-8"))
        self.assertEqual(data["op"], "测试")
        self.assertEqual(data["scope"], "checkout")
        self.repo.tool("lock", "release", "checkout")
        self.assertFalse(lock.exists())

    def test_second_acquire_busy(self):
        self.repo.tool("lock", "acquire", "checkout")
        proc = self.repo.tool("lock", "acquire", "checkout", check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("被占用", proc.stderr)

    def test_force_steal(self):
        self.repo.tool("lock", "acquire", "checkout")
        self.repo.tool("lock", "acquire", "checkout", "--force")
        self.repo.tool("lock", "release", "checkout", "--force")

    def test_stale_by_mtime(self):
        self.repo.tool("lock", "acquire", "checkout")
        lock = self.repo.state() / "checkout.lock"
        old = time.time() - 10_000
        os.utime(lock, (old, old))
        proc = self.repo.tool("lock", "acquire", "checkout", check=False)
        self.assertEqual(proc.returncode, 0)

    def test_release_foreign_owner_needs_force(self):
        self.repo.tool("lock", "acquire", "checkout")
        other = {**GIT_ENV, "CATPAW_CONVERSATION_ID": "other-session"}
        proc = tool_run(["lock", "release", "checkout"], cwd=self.repo.path,
                        check=False, env=other)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("无权释放", proc.stderr)
        self.repo.tool("lock", "release", "checkout", "--force")

    def test_lock_run_executes_and_releases(self):
        proc = self.repo.tool("lock", "run", "checkout", "--",
                              "git", "rev-parse", "--verify", "HEAD")
        self.assertEqual(proc.returncode, 0)
        self.assertFalse((self.repo.state() / "checkout.lock").exists())

    def test_lock_run_releases_on_failure(self):
        proc = self.repo.tool("lock", "run", "checkout", "--",
                              "git", "rev-parse", "--verify", "--quiet",
                              "no-such-ref", check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse((self.repo.state() / "checkout.lock").exists())

    def test_lock_status_reports(self):
        self.repo.tool("lock", "status")
        self.repo.tool("lock", "acquire", "merge")
        proc = self.repo.tool("lock", "status")
        self.assertIn("占用中", proc.stdout)
        self.assertIn("空闲", proc.stdout)


# ──────────────────────────────────────────────
# 第 2 层：串行合并
# ──────────────────────────────────────────────
class TestSerialMerge(TempRepoCase):
    def _make_task(self, name="demo", filename="feat.txt", content="x = 1\n"):
        self.repo.tool("task", "start", name)
        wt = Repo(self.repo.path / ".worktrees" / name)
        wt.write(filename, content)
        wt.commit_all(f"feat: {name}")
        return wt

    def test_merge_happy_path(self):
        self._make_task()
        self.repo.tool("merge", "demo", "--no-verify")
        # 远端 main 收到任务的提交
        self.repo.git("fetch", "origin", "main")
        files = git_run(["ls-tree", "--name-only", "origin/main"], cwd=self.repo.path).stdout
        self.assertIn("feat.txt", files)
        # 合并工作树已清理
        self.assertFalse((self.repo.path / ".worktrees" / "_merge").exists())
        # 任务登记为 merged
        self.assertEqual(self.repo.tasks()[0]["status"], "merged")

    def test_merge_conflict_keeps_worktree(self):
        self._make_task(filename="README.md", content="task 侧改动\n")
        # 主检出推进同一文件并推送，制造冲突
        self.repo.write("README.md", "main 侧改动\n")
        self.repo.commit_all("main 侧改动")
        self.repo.git("push", "origin", "main")
        proc = self.repo.tool("merge", "demo", "--no-verify", check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("冲突", proc.stderr)
        self.assertTrue((self.repo.path / ".worktrees" / "_merge").exists())
        # 远端未被改动
        self.repo.git("fetch", "origin", "main")
        remote = git_run(["show", "origin/main:README.md"], cwd=self.repo.path).stdout
        self.assertEqual(remote, "main 侧改动\n")

    def test_merge_conflict_cleanup(self):
        self._make_task(filename="README.md", content="task 侧改动\n")
        self.repo.write("README.md", "main 侧改动\n")
        self.repo.commit_all("main 侧改动")
        self.repo.git("push", "origin", "main")
        self.repo.tool("merge", "demo", "--no-verify", check=False)
        self.repo.tool("merge", "--cleanup")
        self.assertFalse((self.repo.path / ".worktrees" / "_merge").exists())

    def test_merge_verify_failure_blocks(self):
        self._make_task()
        proc = self.repo.tool("merge", "demo", "--verify-cmd", "python -c \"import sys; sys.exit(1)\"",
                              check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("校验未通过", proc.stderr)
        self.repo.git("fetch", "origin", "main")
        files = git_run(["ls-tree", "--name-only", "origin/main"], cwd=self.repo.path).stdout
        self.assertNotIn("feat.txt", files)

    def test_merge_verify_warn_passes(self):
        self._make_task()
        proc = self.repo.tool("merge", "demo", "--verify-cmd", "python -c \"import sys; sys.exit(2)\"",
                              check=False)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("放行", proc.stdout + proc.stderr)

    def test_merge_existing_worktree_blocks(self):
        self._make_task(filename="README.md", content="task 侧改动\n")
        self.repo.write("README.md", "main 侧改动\n")
        self.repo.commit_all("main 侧改动")
        self.repo.git("push", "origin", "main")
        self.repo.tool("merge", "demo", "--no-verify", check=False)
        proc = self.repo.tool("merge", "demo", "--no-verify", check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("合并工作树已存在", proc.stderr)

    def test_merge_unknown_branch_rejected(self):
        proc = self.repo.tool("merge", "nope", "--no-verify", check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("分支不存在", proc.stderr)

    def test_merge_lock_serializes(self):
        self._make_task()
        self.repo.tool("lock", "acquire", "merge", "--op", "模拟他人合并中")
        proc = self.repo.tool("merge", "demo", "--no-verify", check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("被占用", proc.stderr)

    def test_merge_wait_then_succeeds_after_release(self):
        self._make_task()
        self.repo.tool("lock", "acquire", "merge")
        # 等待锁：先起一个后台释放，再让 merge 等
        import threading
        threading.Timer(1.0, lambda: self.repo.tool("lock", "release", "merge")).start()
        proc = self.repo.tool("merge", "demo", "--no-verify", "--wait", "10", check=False)
        self.assertEqual(proc.returncode, 0)


# ──────────────────────────────────────────────
# sync / status
# ──────────────────────────────────────────────
class TestSyncAndStatus(TempRepoCase):
    def _advance_origin(self, name, text, msg):
        """从任务工作树直接推一个提交到 origin/main（仅测试装配用）。"""
        self.repo.tool("task", "start", "setup")
        wt = Repo(self.repo.path / ".worktrees" / "setup")
        wt.write(name, text)
        wt.commit_all(msg)
        wt.git("push", "origin", "task/setup:main")
        self.repo.tool("task", "stop", "setup", "--force")

    def test_sync_up_to_date(self):
        self.repo.tool("sync")

    def test_sync_fast_forward(self):
        self._advance_origin("from-origin.txt", "y\n", "远端推进")
        self.repo.tool("sync")
        self.assertEqual(self.repo.read("from-origin.txt"), "y\n")

    def test_sync_refuses_when_dirty(self):
        self._advance_origin("from-origin.txt", "y\n", "远端推进")
        self.repo.write("README.md", "本地未提交\n")
        proc = self.repo.tool("sync", check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("未提交改动", proc.stderr)

    def test_sync_reports_ahead(self):
        self.repo.write("local.txt", "z\n")
        self.repo.commit_all("本地提交")
        proc = self.repo.tool("sync")
        self.assertIn("领先远端 1 个提交", proc.stdout)

    def test_sync_push_local(self):
        self.repo.write("local.txt", "z\n")
        self.repo.commit_all("本地提交")
        self.repo.tool("sync", "--push-local")
        self.repo.git("fetch", "origin", "main")
        files = git_run(["ls-tree", "--name-only", "origin/main"], cwd=self.repo.path).stdout
        self.assertIn("local.txt", files)

    def test_status_runs(self):
        self.repo.tool("task", "start", "demo")
        proc = self.repo.tool("status")
        self.assertIn("demo", proc.stdout)
        self.assertIn("checkout", proc.stdout)


# ──────────────────────────────────────────────
# 纯函数
# ──────────────────────────────────────────────
class TestPureFunctions(unittest.TestCase):
    def test_task_name_regex(self):
        for ok in ("demo", "a", "0-x", "exit-transition-return"):
            self.assertTrue(wg.TASK_NAME_RE.match(ok), ok)
        for bad in ("Demo", "a_b", "-x", "a" * 64, ""):
            self.assertFalse(wg.TASK_NAME_RE.match(bad), bad)

    def test_default_base_prefers_remote_main(self):
        with tempfile.TemporaryDirectory(prefix="wf-guard-base-") as tmp:
            repo = make_repo(Path(tmp))
            self.assertEqual(wg.default_base(repo.path), "origin/main")


if __name__ == "__main__":
    unittest.main()
