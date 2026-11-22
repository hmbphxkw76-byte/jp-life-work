#!/usr/bin/env python3
"""jp-life-work 并行会话三层隔离机制（workflow_guard）。

背景：``main`` 是唯一共享可变引用，而写入者互不知情——多个 Agent 会话直接改写同一
工作目录与同一分支，GitHub Actions 定时任务也写同一仓库，导致推送被拒、互相覆盖、
把别人未提交的改动裹进提交等「合并错误」。

三层隔离：

  1. 分支隔离（任务间）——``task start/list/stop``
     每个任务一条 ``task/<name>-<sid>`` 分支（``sid`` = 会话标识前 8 位，
     规范见 ``docs/branch-management.md``），默认再配一个独立 worktree
     （``.worktrees/<name>``）。任务只碰自己的分支 / 工作树，互不越界。
  2. 串行合并（main 级）——``merge``
     全局 merge 锁保证同一时刻只有一个合并；默认走 PR 传输（推任务分支 → 建 PR →
     等必需检查 → 合并），不动共享检出目录；合并前跑校验。``--transport direct``
     为旧行为（隔离合并工作树 ``.worktrees/_merge`` + 直推 main），仅非 GitHub / 测试用。
  3. 共享检出锁（工作目录级）——``lock``
     在共享检出目录里做 checkout / commit / stash / reset 等可变操作前先拿锁；
     锁带 owner / pid / 时间戳，超时或进程已死自动失效。推荐用 ``lock run`` 短借
     快还，避免长持锁。

状态目录：``<common-git-dir>/workflow-guard/``（不入库、跨 worktree 共享）。

退出码：0 成功；1 失败（含锁被占用、合并冲突、校验阻断）。
本工具只用标准库，Windows / POSIX 通用。
"""
from __future__ import annotations

import argparse
import contextlib
import getpass
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

_TOOL_DIR = Path(__file__).resolve().parent
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

import branch_naming  # noqa: E402 - 同目录模块（分支命名单一事实源）

EXIT_OK = 0
EXIT_ERR = 1

STATE_DIR_NAME = "workflow-guard"
WORKTREE_ROOT = ".worktrees"
MERGE_WORKTREE_NAME = "_merge"

DEFAULT_STALE_TIMEOUT = 1800  # 锁超时（秒）：30 分钟未更新视为失效
DEFAULT_WAIT = 0              # 默认不等待锁，快速失败
DEFAULT_PR_WAIT_TIMEOUT = 1800  # PR 传输等待必需检查的超时（秒）
PR_POLL_INTERVAL = 15           # PR 检查轮询间隔（秒）

TASK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
SCOPES = ("checkout", "merge", "commit", "push")


class GuardError(RuntimeError):
    """用户可见错误（命令失败、锁被占用、合并冲突等）。"""


# ──────────────────────────────────────────────
# 基础工具
# ──────────────────────────────────────────────
def _now() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def _run(cmd: Sequence[str] | str, cwd: Path | None = None, check: bool = True,
         capture: bool = True, shell: bool = False) -> subprocess.CompletedProcess:
    # shell=True 时允许直接传字符串；否则按序列处理（默认关闭）
    argv = cmd if (shell and isinstance(cmd, str)) else list(cmd)
    proc = subprocess.run(
        argv, cwd=str(cwd) if cwd else None, capture_output=capture,
        text=True, encoding="utf-8", errors="replace", shell=shell,
    )
    if check and proc.returncode != 0:
        out = (proc.stderr or proc.stdout or "").strip()
        raise GuardError(f"命令失败（退出码 {proc.returncode}）：{' '.join(cmd)}\n{out}")
    return proc


def git(args: Sequence[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return _run(["git", *args], cwd=cwd, check=check)


def _find_push_script(cwd: Path | None) -> Path | None:
    """定位 ``engine/scripts/git_push.py``：优先当前工作树（如 ``_merge``），再回退本工具目录。"""
    if cwd:
        local_script = Path(cwd) / "engine" / "scripts" / "git_push.py"
        if local_script.exists():
            return local_script
    shared = Path(__file__).resolve().with_name("git_push.py")
    return shared if shared.exists() else None


def push_with_failover(cwd: Path | None, remote: str, refspecs: Sequence[str],
                       fallback: str = "origin-https",
                       force_with_lease: bool = False) -> subprocess.CompletedProcess:
    """经 ``engine/scripts/git_push.py`` 走 ssh / https 双通道 failover 推送。

    主通道失败才切备用通道，每条通道只试一次；两条都失败即返回退出码 1（不重试）。
    仅用于本仓库（GitHub），不使用 GitLab。脚本缺失时退化为单次 ``git push``。
    """
    script = _find_push_script(cwd)
    if script is None:
        print("[workflow-guard] 未找到 engine/scripts/git_push.py，退化为单次 git push（无 failover）。",
              file=sys.stderr)
        cmd = ["push"] + (["--force-with-lease"] if force_with_lease else []) \
            + [remote, *refspecs]
        return git(cmd, cwd=cwd, check=False)
    cmd = [sys.executable, str(script), "--remote", remote, "--fallback", fallback]
    if force_with_lease:
        cmd.append("--force-with-lease")
    cmd.extend(refspecs)
    proc = _run(cmd, cwd=cwd, check=False)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc


# ──────────────────────────────────────────────
# PR 传输（合并走 GitHub PR：推分支 → 建 PR → 等检查 → 合并）
# ──────────────────────────────────────────────
def _remote_url(remote: str, cwd: Path | None = None) -> str:
    p = git(["remote", "get-url", remote], cwd=cwd, check=False)
    return (p.stdout or "").strip()


def _is_github_remote(remote: str, cwd: Path | None = None) -> bool:
    return "github.com" in _remote_url(remote, cwd).lower()


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _resolve_transport(args: argparse.Namespace, root: Path) -> str:
    """选择合并传输：auto / direct / pr。"""
    choice = (getattr(args, "transport", "auto") or "auto").lower()
    if choice not in ("auto", "direct", "pr"):
        raise GuardError(f"未知传输方式：{choice}（可选 auto / direct / pr）")
    if choice == "auto":
        return "pr" if (_is_github_remote(args.remote, root) and _gh_available()) else "direct"
    if choice == "pr" and not _gh_available():
        raise GuardError("未找到 gh，无法使用 pr 传输")
    return choice


def _gh(args: Sequence[str], cwd: Path | None = None,
        check: bool = False) -> subprocess.CompletedProcess:
    # WORKFLOW_GUARD_GH 可覆盖 gh 命令（测试注入 fake gh；默认 "gh"）
    raw = os.environ.get("WORKFLOW_GUARD_GH", "") or "gh"
    base = shlex.split(raw, posix=(os.name != "nt"))  # Windows 路径含反斜杠，需保留
    return _run([*base, *args], cwd=cwd, check=check)


def _gh_pr_find(branch: str, cwd: Path | None = None) -> str | None:
    p = _gh(["pr", "list", "--base", "main", "--head", branch, "--state", "open",
             "--json", "number", "--jq", ".[0].number"], cwd=cwd)
    if p.returncode == 0:
        num = (p.stdout or "").strip()
        if num.isdigit():
            return num
    return None


def _gh_pr_create(branch: str, title: str, body: str, cwd: Path | None = None) -> str:
    existing = _gh_pr_find(branch, cwd)
    if existing:
        print(f"[workflow-guard] PR 已存在：#{existing}")
        return existing
    p = _gh(["pr", "create", "--base", "main", "--head", branch,
             "--title", title, "--body", body], cwd=cwd)
    if p.returncode != 0:
        existing = _gh_pr_find(branch, cwd)
        if existing:
            print(f"[workflow-guard] PR 已存在：#{existing}")
            return existing
        raise GuardError(f"创建 PR 失败：{(p.stderr or p.stdout).strip()}")
    url = (p.stdout or "").strip().splitlines()[-1].strip() if p.stdout.strip() else ""
    num = url.rstrip("/").rsplit("/", 1)[-1] if url else ""
    if not num.isdigit():
        num = _gh_pr_find(branch, cwd) or ""
    if not num.isdigit():
        raise GuardError(f"PR 已创建但无法解析编号：{url}")
    print(f"[workflow-guard] 已创建 PR #{num}：{url}")
    return num


def _gh_pr_view(num: str, cwd: Path | None = None) -> dict:
    p = _gh(["pr", "view", num, "--json",
             "state,mergeable,mergeStateStatus,statusCheckRollup,mergeCommit"], cwd=cwd)
    if p.returncode != 0:
        raise GuardError(f"查询 PR #{num} 失败：{(p.stderr or p.stdout).strip()}")
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError as exc:
        raise GuardError(f"解析 PR #{num} 状态失败：{exc}") from exc


def _gh_pr_wait_checks(num: str, timeout: int, cwd: Path | None = None,
                       interval: int = PR_POLL_INTERVAL) -> None:
    deadline = time.time() + max(0, timeout)
    last = ""
    while True:
        v = _gh_pr_view(num, cwd)
        if v.get("state") != "OPEN":
            return
        ms = v.get("mergeStateStatus") or "UNKNOWN"
        conclusions = [c.get("conclusion") or c.get("state") or "UNKNOWN"
                       for c in (v.get("statusCheckRollup") or [])]
        line = f"mergeState={ms} checks={conclusions}"
        if line != last:
            print(f"[workflow-guard] PR #{num}：{line}")
            last = line
        failed = [c for c in conclusions
                  if c in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT",
                           "ACTION_REQUIRED", "STALE")]
        if failed:
            raise GuardError(f"PR #{num} 校验失败：{conclusions}")
        pending = [c for c in conclusions
                   if c not in ("SUCCESS", "NEUTRAL", "SKIPPED", "COMPLETED")]
        if ms in ("CLEAN", "HAS_HOOKS") and not pending:
            return
        if ms == "BLOCKED" and not pending:
            raise GuardError(f"PR #{num} 被分支保护阻断（必需检查 / 审查未完成）：{conclusions}")
        if time.time() >= deadline:
            raise GuardError(f"等待 PR #{num} 校验超时（{timeout}s）：{line}")
        time.sleep(interval)


def _gh_pr_merge(num: str, cwd: Path | None = None) -> str:
    p = _gh(["pr", "merge", num, "--merge"], cwd=cwd)
    if p.returncode != 0:
        raise GuardError(f"合并 PR #{num} 失败：{(p.stderr or p.stdout).strip()}")
    v = _gh_pr_view(num, cwd)
    sha = (v.get("mergeCommit") or {}).get("oid") or ""
    if not sha:
        raise GuardError(f"PR #{num} 已合并但无法解析合并提交 SHA")
    return sha


def _merge_via_pr(root: Path, state: Path, tasks: list[dict], t: dict | None,
                  branch: str, remote: str, args: argparse.Namespace) -> int:
    """PR 传输合并：推任务分支 → 建 PR → 等必需检查 → 合并 PR。"""
    if not args.no_verify and t:
        task_wt = Path(t.get("worktree") or "")
        if task_wt.exists():
            rc = _run_verify(task_wt, args)
            if rc == 1:
                raise GuardError("合并前校验未通过（退出码 1），已阻断合并。")
            if rc == 2:
                print("[workflow-guard] 校验有警告（退出码 2），按约定放行。")
    p = push_with_failover(root, remote, [f"{branch}:{branch}"], fallback=args.push_fallback)
    if p.returncode != 0:
        raise GuardError(f"推送任务分支失败：{(p.stderr or p.stdout).strip()}")
    print(f"[workflow-guard] 已推送任务分支 {branch} → {remote}")
    num = _gh_pr_create(branch, f"Merge {branch}",
                        "由 workflow_guard merge 自动创建（PR 传输）。", cwd=root)
    _gh_pr_wait_checks(num, args.wait_timeout, cwd=root)
    sha = _gh_pr_merge(num, cwd=root)
    print(f"[workflow-guard] 已合并 PR #{num}（{sha[:10]}）")
    if t:
        t["status"] = "merged"
        t["merged"] = _now()
        t["merged_sha"] = sha
        save_tasks(state, tasks)
    print("  本地 main 如需对齐：python engine/scripts/workflow_guard.py sync")
    return EXIT_OK


def repo_root() -> Path:
    """共享检出（主工作树）根目录。"""
    return Path(git(["rev-parse", "--show-toplevel"]).stdout.strip()).resolve()


def common_git_dir(root: Path) -> Path:
    """所有 worktree 共享的 git 目录（锁与登记表放这里）。"""
    d = Path(git(["rev-parse", "--git-common-dir"], cwd=root).stdout.strip())
    if not d.is_absolute():
        d = root / d
    return d.resolve()


def state_dir(root: Path) -> Path:
    d = common_git_dir(root) / STATE_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def current_owner() -> str:
    """锁的持有者标识：优先 CatPaw 会话 ID，否则 用户@主机。"""
    cid = os.environ.get("CATPAW_CONVERSATION_ID")
    if cid:
        return f"catpaw:{cid}"
    try:
        return f"{getpass.getuser()}@{socket.gethostname()}"
    except Exception:  # noqa: BLE001 - 兜底，不能因取用户名失败而中断
        return f"pid:{os.getpid()}"


# ──────────────────────────────────────────────
# 第 3 层：共享检出锁
# ──────────────────────────────────────────────
class Lock:
    """文件锁：O_CREAT|O_EXCL 原子创建；超过 stale_timeout 未释放即失效。

    注意：本工具每次调用都是独立短命进程，持有者是「会话」而非进程，
    因此不按进程存活判断失效（否则 lock acquire 一退出锁就被抢）；
    pid 仅作为登记信息展示。失效只由时间超时决定，也可 --force 强取。
    """

    def __init__(self, path: Path, scope: str, stale_timeout: int = DEFAULT_STALE_TIMEOUT):
        self.path = path
        self.scope = scope
        self.stale_timeout = stale_timeout

    def read(self) -> dict | None:
        try:
            with self.path.open(encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else None
        except (OSError, ValueError):
            return None

    def _stale(self, data: dict | None) -> bool:
        if data is None:
            return True
        try:
            age = time.time() - self.path.stat().st_mtime
        except OSError:
            return True
        return age > self.stale_timeout

    def _busy_msg(self, data: dict | None) -> str:
        if not data:
            return f"{self.scope} 锁存在但内容不可读：{self.path}"
        return (
            f"{self.scope} 锁被占用：owner={data.get('owner')} pid={data.get('pid')} "
            f"op={data.get('op')} 获取于 {data.get('acquired')}；"
            f"确认无人在跑可用 --force 强取，或等其释放"
        )

    def acquire(self, owner: str, op: str, wait: int = DEFAULT_WAIT,
                force: bool = False) -> dict:
        deadline = time.time() + max(0, wait)
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                data = self.read()
                if force or self._stale(data):
                    with contextlib.suppress(FileNotFoundError):
                        self.path.unlink()
                    continue
                if time.time() >= deadline:
                    raise GuardError(self._busy_msg(data)) from None
                time.sleep(1.0)
                continue
            payload = {
                "scope": self.scope,
                "owner": owner,
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "op": op,
                "acquired": _now(),
            }
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            return payload

    def release(self, owner: str | None = None, force: bool = False) -> None:
        data = self.read()
        if data is None:
            return
        if owner and data.get("owner") != owner and not force:
            raise GuardError(
                f"{self.scope} 锁属于 {data.get('owner')}，{owner} 无权释放（--force 可强取）"
            )
        with contextlib.suppress(FileNotFoundError):
            self.path.unlink()


def _lock_for(state: Path, scope: str, stale_timeout: int) -> Lock:
    if scope not in SCOPES:
        raise GuardError(f"未知锁类型：{scope}（可选 {', '.join(SCOPES)}）")
    return Lock(state / f"{scope}.lock", scope, stale_timeout=stale_timeout)


# ──────────────────────────────────────────────
# 任务登记表（第 1 层的落地）
# ──────────────────────────────────────────────
def _tasks_file(state: Path) -> Path:
    return state / "tasks.json"


def load_tasks(state: Path) -> list[dict]:
    try:
        with _tasks_file(state).open(encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def save_tasks(state: Path, tasks: list[dict]) -> None:
    with _tasks_file(state).open("w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def find_task(tasks: list[dict], name: str) -> dict | None:
    return next((t for t in tasks if t.get("name") == name), None)


def default_base(root: Path, remote: str = "origin") -> str:
    """任务分支的默认基点：优先远端 main（共享真相），否则本地 main。"""
    ref = f"{remote}/main"
    if git(["rev-parse", "--verify", "--quiet", ref], cwd=root, check=False).returncode == 0:
        return ref
    return "main"


def _worktree_path(root: Path, name: str) -> Path:
    return root / WORKTREE_ROOT / name


# ──────────────────────────────────────────────
# 命令：task
# ──────────────────────────────────────────────
def cmd_task_start(args: argparse.Namespace) -> int:
    root = repo_root()
    state = state_dir(root)
    tasks = load_tasks(state)
    name: str = args.name
    if not TASK_NAME_RE.match(name):
        raise GuardError(
            f"任务名不合法：{name!r}（需小写字母或数字开头，仅含小写字母、数字、连字符，≤63 字符）"
        )
    if find_task(tasks, name):
        raise GuardError(f"任务已存在：{name}（先 task stop，或换个名字）")
    session = branch_naming.session_id()
    branch = branch_naming.task_branch(name, session)
    legacy = f"task/{name}"
    if git(["rev-parse", "--verify", "--quiet", branch], check=False).returncode == 0:
        raise GuardError(f"分支已存在：{branch}")
    if git(["rev-parse", "--verify", "--quiet", legacy], check=False).returncode == 0:
        print(f"[workflow-guard] 提示：存在旧格式分支 {legacy}（无会话标识）；"
              f"本任务使用 {branch}", file=sys.stderr)
    base = args.base or default_base(root, args.remote)

    owner = current_owner()
    if args.no_worktree:
        git(["branch", branch, base])
        tasks.append({
            "name": name, "branch": branch, "worktree": None, "base": base,
            "session": session, "owner": owner, "pid": os.getpid(),
            "created": _now(), "status": "active",
        })
        save_tasks(state, tasks)
        print(f"[workflow-guard] 已建分支 {branch}（基于 {base}），未建 worktree。")
        print("  共享检出模式下，git 可变操作请逐次走锁，例如：")
        print(f"    python engine/scripts/workflow_guard.py lock run checkout -- git switch {branch}")
        return EXIT_OK

    wt = _worktree_path(root, name)
    if wt.exists():
        raise GuardError(f"工作树目录已存在：{wt}")
    wt.parent.mkdir(parents=True, exist_ok=True)
    git(["worktree", "add", "-b", branch, str(wt), base])
    tasks.append({
        "name": name, "branch": branch, "worktree": str(wt), "base": base,
        "session": session, "owner": owner, "pid": os.getpid(),
        "created": _now(), "status": "active",
    })
    save_tasks(state, tasks)
    print(f"[workflow-guard] 任务 {name} 已建立：")
    print(f"  分支   {branch}（基于 {base}，sid={branch_naming.session_sid(session)}）")
    print(f"  工作树 {wt}")
    print(f"  在该工作树里工作；完成后 `merge {name}`。")
    return EXIT_OK


def cmd_task_list(args: argparse.Namespace) -> int:
    root = repo_root()
    tasks = load_tasks(state_dir(root))
    if not tasks:
        print("无登记任务。")
    else:
        print(f"{'任务':<20} {'分支':<26} {'工作树':<38} {'状态':<8} 创建时间")
        for t in tasks:
            print(
                f"{t.get('name', '?'):<20} {t.get('branch', '?'):<26} "
                f"{(t.get('worktree') or '—'):<38} {t.get('status', '?'):<8} {t.get('created', '')}"
            )
    print("\nworktree 实况：")
    print(git(["worktree", "list"], cwd=root).stdout.rstrip())
    return EXIT_OK


def cmd_task_stop(args: argparse.Namespace) -> int:
    root = repo_root()
    state = state_dir(root)
    tasks = load_tasks(state)
    t = find_task(tasks, args.name)
    if not t:
        raise GuardError(f"任务不存在：{args.name}")
    branch = t["branch"]
    base = t.get("base") or default_base(root, args.remote)

    merged = git(["merge-base", "--is-ancestor", branch, base], check=False).returncode == 0
    if not merged and not args.force:
        raise GuardError(f"分支 {branch} 尚未合入 {base}；确认可丢弃用 --force")

    wt = t.get("worktree")
    if wt and Path(wt).exists():
        dirty = git(["status", "--porcelain"], cwd=wt, check=False).stdout.strip()
        if dirty and not args.force:
            raise GuardError(f"工作树 {wt} 有未提交改动；确认可丢弃用 --force\n{dirty}")
        git(["worktree", "remove", "--force", wt])

    git(["branch", "-D", branch])
    tasks.remove(t)
    save_tasks(state, tasks)
    print(f"[workflow-guard] 任务 {args.name} 已清理（分支 {branch} 已删）。")
    return EXIT_OK


# ──────────────────────────────────────────────
# 命令：lock
# ──────────────────────────────────────────────
def cmd_lock_acquire(args: argparse.Namespace) -> int:
    root = repo_root()
    lock = _lock_for(state_dir(root), args.scope, args.stale_timeout)
    payload = lock.acquire(current_owner(), args.op or "acquire",
                           wait=args.wait, force=args.force)
    print(f"[workflow-guard] 已取得 {args.scope} 锁：owner={payload['owner']} pid={payload['pid']}")
    print(f"  用完请释放：lock release {args.scope}")
    return EXIT_OK


def cmd_lock_release(args: argparse.Namespace) -> int:
    root = repo_root()
    lock = _lock_for(state_dir(root), args.scope, args.stale_timeout)
    lock.release(current_owner(), force=args.force)
    print(f"[workflow-guard] 已释放 {args.scope} 锁（若存在）。")
    return EXIT_OK


def cmd_lock_status(args: argparse.Namespace) -> int:
    root = repo_root()
    state = state_dir(root)
    for scope in SCOPES:
        lock = _lock_for(state, scope, args.stale_timeout)
        data = lock.read()
        if data:
            stale = "（已失效，可强取）" if lock._stale(data) else ""
            print(f"[锁] {scope:<8} 占用中 owner={data.get('owner')} pid={data.get('pid')} "
                  f"op={data.get('op')} 于 {data.get('acquired')}{stale}")
        else:
            print(f"[锁] {scope:<8} 空闲")
    return EXIT_OK


def cmd_lock_run(args: argparse.Namespace) -> int:
    cmd = list(args.cmd)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        raise GuardError("lock run 需要命令，例如：lock run checkout -- git switch task/x")
    root = repo_root()
    lock = _lock_for(state_dir(root), args.scope, args.stale_timeout)
    owner = current_owner()
    lock.acquire(owner, "run " + " ".join(cmd), wait=args.wait, force=args.force)
    try:
        return _run(cmd, check=False).returncode
    finally:
        lock.release(owner)


# ──────────────────────────────────────────────
# 命令：merge（第 2 层：串行合并）
# ──────────────────────────────────────────────
def _remove_worktree(root: Path, wt: Path) -> None:
    git(["worktree", "remove", "--force", str(wt)], cwd=root, check=False)
    git(["worktree", "prune"], cwd=root, check=False)


def _merge_fail_hint(wt: Path) -> int:
    print(f"  保留合并工作树供处理：{wt}", file=sys.stderr)
    print("  处理完重试：python engine/scripts/workflow_guard.py merge <任务>；"
          "放弃：python engine/scripts/workflow_guard.py merge --cleanup", file=sys.stderr)
    return EXIT_ERR


def _run_verify(wt: Path, args: argparse.Namespace) -> int:
    """合并前校验：默认跑仓库自带的 validate.py；返回进程退出码。"""
    cmd = args.verify_cmd
    if cmd is None:
        default = wt / "engine" / "tools" / "validate.py"
        if default.exists():
            argv = [sys.executable, "engine/tools/validate.py"]
        else:
            print("[workflow-guard] 未发现 engine/tools/validate.py，跳过校验"
                  "（--verify-cmd 可指定）")
            return EXIT_OK
    else:
        argv = shlex.split(cmd)
    print(f"[workflow-guard] 合并前校验：{' '.join(argv)}")
    return _run(argv, cwd=wt, check=False, shell=False).returncode


def cmd_merge(args: argparse.Namespace) -> int:
    root = repo_root()
    state = state_dir(root)

    if args.cleanup:
        wt = _worktree_path(root, MERGE_WORKTREE_NAME)
        if not wt.exists():
            print("无合并工作树需要清理。")
            return EXIT_OK
        _remove_worktree(root, wt)
        print(f"[workflow-guard] 已移除合并工作树：{wt}")
        return EXIT_OK

    tasks = load_tasks(state)
    t = find_task(tasks, args.name)
    branch = t["branch"] if t else args.name
    if git(["rev-parse", "--verify", "--quiet", branch], check=False).returncode != 0:
        raise GuardError(f"分支不存在：{branch}（任务未登记且分支不存在）")

    owner = current_owner()
    remote = args.remote
    lock = _lock_for(state, "merge", args.stale_timeout)
    lock.acquire(owner, f"merge {branch}", wait=args.wait, force=args.force)
    try:
        if _resolve_transport(args, root) == "pr":
            return _merge_via_pr(root, state, tasks, t, branch, remote, args)
        wt = _worktree_path(root, MERGE_WORKTREE_NAME)
        if wt.exists():
            raise GuardError(
                f"合并工作树已存在：{wt}\n"
                f"  上次合并可能未收尾。处理完用 `merge --cleanup` 清理后重试。"
            )
        git(["fetch", remote, "main"], cwd=root)
        remote_main = f"{remote}/main"
        wt.parent.mkdir(parents=True, exist_ok=True)
        git(["worktree", "add", "--detach", str(wt), remote_main], cwd=root)

        keep = False
        try:
            if args.ff_only:
                m = git(["merge", "--ff-only", branch], cwd=wt, check=False)
            else:
                m = git(["merge", "--no-ff", "--no-edit", branch], cwd=wt, check=False)
            if m.returncode != 0:
                keep = True
                print(f"[workflow-guard] 合并 {branch} 冲突：\n{(m.stdout + m.stderr).strip()}",
                      file=sys.stderr)
                return _merge_fail_hint(wt)

            if not args.no_verify:
                rc = _run_verify(wt, args)
                if rc == 1:
                    keep = True
                    print("[workflow-guard] 校验未通过（退出码 1），已阻断合并。", file=sys.stderr)
                    return _merge_fail_hint(wt)
                if rc == 2:
                    print("[workflow-guard] 校验有警告（退出码 2），按约定放行。")

            p = push_with_failover(wt, remote, ["HEAD:main"],
                                   fallback=args.push_fallback, force_with_lease=True)
            if p.returncode != 0:
                # 远端在 fetch 之后又被推进（如 CI）：再整合一次并重试一次
                git(["fetch", remote, "main"], cwd=root)
                m2 = git(["merge", "--no-ff", "--no-edit", remote_main], cwd=wt, check=False)
                if m2.returncode != 0:
                    keep = True
                    print(f"[workflow-guard] 整合远端 main 时冲突：\n"
                          f"{(m2.stdout + m2.stderr).strip()}", file=sys.stderr)
                    return _merge_fail_hint(wt)
                if not args.no_verify and _run_verify(wt, args) == 1:
                    keep = True
                    print("[workflow-guard] 二次校验未通过，已阻断合并。", file=sys.stderr)
                    return _merge_fail_hint(wt)
                p = push_with_failover(wt, remote, ["HEAD:main"],
                                       fallback=args.push_fallback, force_with_lease=True)
                if p.returncode != 0:
                    keep = True
                    raise GuardError(f"推送失败（远端可能被他人推进）：\n"
                                     f"{(p.stderr or p.stdout).strip()}")

            sha = git(["rev-parse", "HEAD"], cwd=wt).stdout.strip()
            print(f"[workflow-guard] 已合并并推送 {branch} → {remote}/main（{sha[:10]}）")
            if t:
                t["status"] = "merged"
                t["merged"] = _now()
                t["merged_sha"] = sha
                save_tasks(state, tasks)
            print("  本地 main 如需对齐：python engine/scripts/workflow_guard.py sync")
            return EXIT_OK
        finally:
            if not keep:
                _remove_worktree(root, wt)
    finally:
        lock.release(owner)


# ──────────────────────────────────────────────
# 命令：sync / status
# ──────────────────────────────────────────────
def cmd_sync(args: argparse.Namespace) -> int:
    root = repo_root()
    state = state_dir(root)
    owner = current_owner()
    lock = _lock_for(state, "checkout", args.stale_timeout)
    lock.acquire(owner, "sync", wait=args.wait, force=args.force)
    try:
        remote = args.remote
        git(["fetch", remote, "main"], cwd=root)
        local = git(["rev-parse", "main"], cwd=root).stdout.strip()
        rsha = git(["rev-parse", f"{remote}/main"], cwd=root).stdout.strip()
        if local == rsha:
            print("本地 main 与远端一致。")
        elif git(["merge-base", "--is-ancestor", "main", f"{remote}/main"],
                 cwd=root, check=False).returncode == 0:
            dirty = git(["status", "--porcelain"], cwd=root, check=False).stdout.strip()
            if dirty:
                raise GuardError("本地工作区有未提交改动，无法快进对齐；"
                                 "请先提交或自行处理（不要用 --force 绕过）")
            git(["merge", "--ff-only", f"{remote}/main"], cwd=root)
            print(f"本地 main 已快进对齐 {remote}/main（{rsha[:10]}）。")
        elif git(["merge-base", "--is-ancestor", f"{remote}/main", "main"],
                 cwd=root, check=False).returncode == 0:
            n = git(["rev-list", "--count", f"{remote}/main..main"], cwd=root).stdout.strip()
            print(f"本地 main 领先远端 {n} 个提交（未推送）。")
            if args.push_local:
                p = push_with_failover(root, remote, ["main"], fallback=args.push_fallback)
                if p.returncode != 0:
                    raise GuardError("推送本地 main 失败（ssh / https 通道均不可用，已停止）。")
                print(f"已推送本地 main → {remote}/main。")
            else:
                print("  如需推送：sync --push-local（注意：此路径不经过合并校验）")
        else:
            raise GuardError("本地 main 与远端已分叉，需人工处理（不要强制覆盖）。")
        return EXIT_OK
    finally:
        lock.release(owner)


def cmd_status(args: argparse.Namespace) -> int:
    root = repo_root()
    state = state_dir(root)
    print(f"仓库      {root}")
    print(f"状态目录  {state}")
    cmd_lock_status(args)
    tasks = load_tasks(state)
    print(f"\n[任务] {len(tasks)} 个")
    for t in tasks:
        print(f"  {t.get('name')}  {t.get('branch')}  {t.get('status')}  "
              f"worktree={t.get('worktree') or '—'}")
    print("\n[worktree]")
    print(git(["worktree", "list"], cwd=root).stdout.rstrip())
    return EXIT_OK


def cmd_hooks(args: argparse.Namespace) -> int:
    """Git 分支命名钩子的安装 / 校验 / 卸载（规范见 docs/branch-management.md）。"""
    ok = branch_naming.install_hooks(check=args.check, uninstall=args.uninstall,
                                     force=args.force)
    if args.check and ok:
        print("[workflow-guard] 分支命名钩子（pre-push / pre-commit）已安装且与源文件一致。")
    return EXIT_OK if ok else EXIT_ERR


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="workflow_guard.py",
        description="jp-life-work 并行会话三层隔离机制（任务分支 / 串行合并 / 共享检出锁）",
    )
    sub = p.add_subparsers(dest="command", required=True, metavar="<command>")

    # task
    task_p = sub.add_parser("task", help="任务（第 1 层：分支隔离）管理")
    task_sub = task_p.add_subparsers(dest="task_command", required=True, metavar="<子命令>")
    ts = task_sub.add_parser("start", help="建任务分支（默认同时建独立 worktree）")
    ts.add_argument("name", help="任务名（小写字母/数字/连字符）")
    ts.add_argument("--no-worktree", action="store_true", help="只建分支，不建 worktree")
    ts.add_argument("--base", help="分支基点（默认 origin/main，缺失时 main）")
    ts.add_argument("--remote", default="origin")
    ts.set_defaults(func=cmd_task_start)
    tl = task_sub.add_parser("list", help="列出任务与 worktree")
    tl.set_defaults(func=cmd_task_list)
    tp = task_sub.add_parser("stop", help="清理任务（删工作树与分支）")
    tp.add_argument("name")
    tp.add_argument("--force", action="store_true", help="未合并 / 有未提交改动也强删")
    tp.add_argument("--remote", default="origin")
    tp.set_defaults(func=cmd_task_stop)

    # lock
    lock_p = sub.add_parser("lock", help="第 3 层：共享检出锁")
    lock_sub = lock_p.add_subparsers(dest="lock_command", required=True, metavar="<子命令>")
    for name, fn, help_text in (
        ("acquire", cmd_lock_acquire, "拿锁"),
        ("release", cmd_lock_release, "放锁"),
        ("status", cmd_lock_status, "查看锁状态"),
    ):
        sp = lock_sub.add_parser(name, help=help_text)
        sp.add_argument("scope", nargs="?", default="checkout", choices=SCOPES)
        if name == "acquire":
            sp.add_argument("--op", help="本次操作说明（记进锁里，便于他人判断）")
        sp.add_argument("--wait", type=int, default=DEFAULT_WAIT, help="等待拿锁的秒数")
        sp.add_argument("--force", action="store_true", help="强取（即使未失效）")
        sp.add_argument("--stale-timeout", type=int, default=DEFAULT_STALE_TIMEOUT,
                        help="锁失效秒数（默认 1800）")
        sp.set_defaults(func=fn)
    lr = lock_sub.add_parser("run", help="持锁执行命令（推荐：短借快还）")
    lr.add_argument("scope", choices=SCOPES)
    lr.add_argument("--wait", type=int, default=DEFAULT_WAIT)
    lr.add_argument("--force", action="store_true")
    lr.add_argument("--stale-timeout", type=int, default=DEFAULT_STALE_TIMEOUT)
    lr.add_argument("cmd", nargs=argparse.REMAINDER, help="要执行的命令（前面加 --）")
    lr.set_defaults(func=cmd_lock_run)

    # merge
    mp = sub.add_parser("merge", help="第 2 层：串行合并入 main")
    mp.add_argument("name", nargs="?", help="任务名（或分支名）")
    mp.add_argument("--cleanup", action="store_true", help="移除遗留的合并工作树后退出")
    mp.add_argument("--no-verify", action="store_true", help="跳过合并前校验")
    mp.add_argument("--verify-cmd", help="自定义校验命令（shlex 拆分为参数数组，默认 validate.py）")
    mp.add_argument("--ff-only", action="store_true", help="只允许快进合并")
    mp.add_argument("--wait", type=int, default=DEFAULT_WAIT, help="等待 merge 锁的秒数")
    mp.add_argument("--force", action="store_true")
    mp.add_argument("--stale-timeout", type=int, default=DEFAULT_STALE_TIMEOUT)
    mp.add_argument("--remote", default="origin")
    mp.add_argument("--push-fallback", default="origin-https",
                    help="推送备用通道 remote（默认 origin-https；传空字符串则不 failover）")
    mp.add_argument("--transport", choices=["auto", "direct", "pr"], default="auto",
                    help="合并传输：auto（GitHub + gh 用 PR）/ direct（直推 main）/ pr（建 PR 合并）")
    mp.add_argument("--wait-timeout", type=int, default=DEFAULT_PR_WAIT_TIMEOUT,
                    help="PR 传输等待必需检查的超时秒数（默认 1800）")
    mp.set_defaults(func=cmd_merge)

    # sync
    sp = sub.add_parser("sync", help="持检出锁对齐本地 main 与远端")
    sp.add_argument("--push-local", action="store_true", help="把本地领先的提交推上去")
    sp.add_argument("--wait", type=int, default=DEFAULT_WAIT)
    sp.add_argument("--force", action="store_true")
    sp.add_argument("--stale-timeout", type=int, default=DEFAULT_STALE_TIMEOUT)
    sp.add_argument("--remote", default="origin")
    sp.add_argument("--push-fallback", default="origin-https",
                    help="推送备用通道 remote（默认 origin-https；传空字符串则不 failover）")
    sp.set_defaults(func=cmd_sync)

    # status
    st = sub.add_parser("status", help="总览（锁 / 任务 / worktree）")
    st.add_argument("--stale-timeout", type=int, default=DEFAULT_STALE_TIMEOUT)
    st.set_defaults(func=cmd_status)

    # hooks
    hp = sub.add_parser("hooks", help="Git 分支命名钩子（安装 / 校验 / 卸载）")
    hp.add_argument("--check", action="store_true", help="只校验是否已安装且与源文件一致")
    hp.add_argument("--uninstall", action="store_true", help="卸载钩子")
    hp.add_argument("--force", action="store_true", help="卸载时允许删除已修改的钩子")
    hp.set_defaults(func=cmd_hooks)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return EXIT_ERR
    try:
        return args.func(args) or EXIT_OK
    except GuardError as exc:
        print(f"[workflow-guard] 错误：{exc}", file=sys.stderr)
        return EXIT_ERR
    except KeyboardInterrupt:
        print("[workflow-guard] 已中断。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
