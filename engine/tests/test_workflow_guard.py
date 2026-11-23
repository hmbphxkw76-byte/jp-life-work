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
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "engine" / "scripts" / "workflow_guard.py"

# 固定会话 ID：task start 自动追加 sid，保证分支名可断言
SESSION_ID = "11111111-2222-3333-4444-555555555555"
SID = "11111111"
DEMO_BRANCH = f"task/demo-{SID}"

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
    "CATPAW_CONVERSATION_ID": SESSION_ID,  # 固定会话 ID，sid 可断言
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

    def tool(self, *args, check=True, env=None):
        return tool_run(list(args), cwd=self.path, check=check, env=env)

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
            self.repo.git("rev-parse", "--verify", "--quiet", DEMO_BRANCH).returncode, 0
        )
        wt = self.repo.path / ".worktrees" / "demo"
        self.assertTrue(wt.is_dir())
        branch = git_run(["branch", "--show-current"], cwd=wt).stdout.strip()
        self.assertEqual(branch, DEMO_BRANCH)
        tasks = self.repo.tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["name"], "demo")
        self.assertEqual(tasks[0]["branch"], DEMO_BRANCH)
        self.assertEqual(tasks[0]["status"], "active")
        self.assertEqual(tasks[0]["session"], SESSION_ID)

    def test_start_no_worktree_creates_branch_only(self):
        self.repo.tool("task", "start", "demo", "--no-worktree")
        self.assertEqual(
            self.repo.git("rev-parse", "--verify", "--quiet", DEMO_BRANCH).returncode, 0
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
            self.repo.git("rev-parse", "--verify", "--quiet", DEMO_BRANCH,
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

    def test_stop_recorded_merged_task_without_ancestor(self):
        self.repo.tool("task", "start", "demo")
        wt = Repo(self.repo.path / ".worktrees" / "demo")
        wt.write("feat.txt", "x = 1\n")
        wt.commit_all("feat")
        tasks = self.repo.tasks()
        tasks[0]["status"] = "merged"
        tasks[0]["merged_sha"] = "b" * 40
        tasks[0]["merged"] = "2026-11-22T00:00:00+08:00"
        (self.repo.state() / "tasks.json").write_text(
            json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
        # 已登记 merged（含 merged_sha）：即使分支不是 base 祖先（模拟远端已删 / 本地滞后）也可 stop
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

    def test_merge_auto_detects_validate_py(self):
        # 预置仓库自带的校验脚本并推上远端：默认路径应自动识别并执行
        self.repo.write("engine/tools/validate.py", "import sys\nsys.exit(0)\n")
        self.repo.commit_all("预置校验脚本")
        self.repo.git("push", "origin", "main")
        self._make_task()
        proc = self.repo.tool("merge", "demo", check=False)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("合并前校验", proc.stdout)

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
        branch = self.repo.tasks()[0]["branch"]
        wt = Repo(self.repo.path / ".worktrees" / "setup")
        wt.write(name, text)
        wt.commit_all(msg)
        wt.git("push", "origin", f"{branch}:main")
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

    def test_lock_scopes_cover_commit_and_push(self):
        # P2-5：并行锁覆盖 checkout / merge / commit / push，共享检出无裸写。
        self.assertEqual(set(wg.SCOPES), {"checkout", "merge", "commit", "push"})


# ──────────────────────────────────────────────
# PR 传输（merge --transport pr）
# ──────────────────────────────────────────────
FAKE_GH = r'''
import json, os, sys
args = sys.argv[1:]
calls_file = os.environ["FAKE_GH_CALLS"]
calls = []
if os.path.exists(calls_file):
    calls = json.loads(open(calls_file, encoding="utf-8").read())
calls.append(args)
open(calls_file, "w", encoding="utf-8").write(json.dumps(calls))
mode = os.environ.get("FAKE_GH_MODE", "ok")
if args[:2] == ["pr", "create"]:
    print("https://github.com/hmbphxkw76-byte/jp-life-work/pull/7")
elif args[:2] == ["pr", "view"]:
    if mode == "fail":
        rollup = [{"name": "validate", "conclusion": "FAILURE"},
                  {"name": "audit", "conclusion": "SUCCESS"}]
    else:
        rollup = [{"name": "validate", "conclusion": "SUCCESS"},
                  {"name": "audit", "conclusion": "SUCCESS"}]
    print(json.dumps({"state": "OPEN", "mergeable": "MERGEABLE",
                      "mergeStateStatus": "CLEAN", "statusCheckRollup": rollup,
                      "mergeCommit": {"oid": "a" * 40}}))
elif args[:2] == ["pr", "merge"]:
    if mode == "fail":
        sys.stderr.write("merge failed")
        sys.exit(1)
elif args[:2] == ["pr", "list"]:
    if mode == "existing":
        print("7")
'''


class TestPRTransport(TempRepoCase):
    def _setup_task(self):
        self.repo.tool("task", "start", "demo")
        wt = self.repo.path / ".worktrees" / "demo"
        (wt / "foo.txt").write_text("x\n", encoding="utf-8")
        git_run(["add", "."], cwd=wt)
        git_run(["commit", "-m", "change"], cwd=wt)
        return wt

    def _env(self, tmp, mode="ok"):
        fake = Path(tmp) / "fake_gh.py"
        fake.write_text(FAKE_GH, encoding="utf-8")
        calls = Path(tmp) / "calls.json"
        return {**GIT_ENV,
                "WORKFLOW_GUARD_GH": f"{sys.executable} {fake}",
                "FAKE_GH_CALLS": str(calls),
                "FAKE_GH_MODE": mode}, calls

    def test_merge_via_pr_happy(self):
        self._setup_task()
        env, calls = self._env(self._tmp)
        self.repo.tool("merge", "demo", "--transport", "pr", "--no-verify", env=env)
        task = self.repo.tasks()[0]
        self.assertEqual(task["status"], "merged")
        self.assertEqual(task["merged_sha"], "a" * 40)
        self.assertEqual(task["pr"], "7")
        kinds = [c[:2] for c in json.loads(calls.read_text(encoding="utf-8"))]
        self.assertIn(["pr", "create"], kinds)
        self.assertIn(["pr", "view"], kinds)
        self.assertIn(["pr", "merge"], kinds)

    def test_merge_via_pr_reuses_existing(self):
        self._setup_task()
        env, calls = self._env(self._tmp, mode="existing")
        self.repo.tool("merge", "demo", "--transport", "pr", "--no-verify", env=env)
        kinds = [c[:2] for c in json.loads(calls.read_text(encoding="utf-8"))]
        self.assertNotIn(["pr", "create"], kinds)
        self.assertIn(["pr", "merge"], kinds)
        self.assertEqual(self.repo.tasks()[0]["status"], "merged")

    def test_merge_via_pr_check_failure_blocks(self):
        self._setup_task()
        env, _ = self._env(self._tmp, mode="fail")
        proc = self.repo.tool("merge", "demo", "--transport", "pr", "--no-verify",
                              env=env, check=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("校验失败", proc.stdout + proc.stderr)
        self.assertNotEqual(self.repo.tasks()[0]["status"], "merged")

    def test_transport_auto_local_origin_is_direct(self):
        self._setup_task()
        env, calls = self._env(self._tmp)
        self.repo.tool("merge", "demo", "--no-verify", env=env)  # 默认 auto
        self.assertEqual(self.repo.tasks()[0]["status"], "merged")
        self.assertFalse(calls.exists())  # 未触碰 gh


class TestWaitChecks(unittest.TestCase):
    """_gh_pr_wait_checks 必须显式等待 validate / audit，而非依赖分支保护 CLEAN。"""

    @staticmethod
    def _views(rollup, ms="CLEAN"):
        return {"state": "OPEN", "mergeStateStatus": ms, "statusCheckRollup": rollup}

    def test_empty_rollup_clean_waits(self):
        # 回归：移除分支保护必需检查后，空 rollup + CLEAN 不得立即返回
        views = self._views([])
        with mock.patch.object(wg, "_gh_pr_view", return_value=views), \
             mock.patch("time.sleep"), self.assertRaises(wg.GuardError):
            wg._gh_pr_wait_checks("1", timeout=0)

    def test_missing_required_check_waits(self):
        views = self._views([{"name": "validate", "conclusion": "SUCCESS"}])
        with mock.patch.object(wg, "_gh_pr_view", return_value=views), \
             mock.patch("time.sleep"), self.assertRaises(wg.GuardError):
            wg._gh_pr_wait_checks("1", timeout=0)

    def test_required_checks_success_returns(self):
        views = self._views([{"name": "validate", "conclusion": "SUCCESS"},
                             {"name": "audit", "conclusion": "SUCCESS"}])
        with mock.patch.object(wg, "_gh_pr_view", return_value=views):
            wg._gh_pr_wait_checks("1", timeout=0)

    def test_required_check_failure_blocks(self):
        views = self._views([{"name": "validate", "conclusion": "FAILURE"},
                             {"name": "audit", "conclusion": "SUCCESS"}])
        with mock.patch.object(wg, "_gh_pr_view", return_value=views), \
             self.assertRaises(wg.GuardError):
            wg._gh_pr_wait_checks("1", timeout=0)


if __name__ == "__main__":
    unittest.main()
