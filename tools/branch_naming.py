#!/usr/bin/env python3
"""分支命名规范与会话标识（BRANCH-NAMING v1.0）。

规范要点（详文档：``docs/branch-management.md``）：

- 开发分支模板：``task/<task-slug>-<sid>``
  例：``task/monthly-update-2026-11-bcbc4ed7``
- ``sid`` = 会话标识（``CATPAW_CONVERSATION_ID``，UUID）前 8 位小写十六进制；
  会话标识缺失时回退 ``用户@主机`` 的 SHA-1 前 8 位（不稳定，会打印告警）。
- 校验正则：``^task/[a-z0-9][a-z0-9-]{0,60}-[0-9a-f]{8}$``。
- 豁免：``main`` / ``master`` / ``HEAD``；远程跟踪引用、tag、删除分支操作不校验。
- 非 ``task/`` 本地分支默认放行并提示；设置 ``BRANCH_NAMING_STRICT=1`` 后阻断。

本模块是 ``tools/workflow_guard.py`` 与 Git 钩子（``tools/git-hooks/``）的单一事实源，
只做命名 / 会话派生，不写仓库状态。纯标准库，Windows / POSIX 通用。
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence

EXIT_OK = 0
EXIT_ERR = 1

SESSION_ENV = "CATPAW_CONVERSATION_ID"
STRICT_ENV = "BRANCH_NAMING_STRICT"
STATE_DIR_NAME = "workflow-guard"

TASK_PREFIX = "task/"
EXEMPT_BRANCHES = frozenset({"main", "master", "HEAD", "FETCH_HEAD"})
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
BRANCH_RE = re.compile(
    rf"^{re.escape(TASK_PREFIX)}(?P<slug>[a-z0-9][a-z0-9-]{{0,60}})-(?P<sid>[0-9a-f]{{8}})$"
)
ZERO_SHA = "0" * 40
HOOK_NAMES = ("pre-push", "pre-commit")
INTERNAL_SCRIPT_NAME = "branch_naming.py"  # 钩子自包含副本（仓库无 tools/ 时回退）


class NamingError(RuntimeError):
    """用户可见的命名 / 安装错误。"""


def _warn(msg: str) -> None:
    print(f"[branch-naming] {msg}", file=sys.stderr)


# ──────────────────────────────────────────────
# 会话标识与分支名
# ──────────────────────────────────────────────
def session_id() -> str:
    """当前会话标识：优先 ``CATPAW_CONVERSATION_ID``（UUID），否则 ``用户@主机``。"""
    raw = os.environ.get(SESSION_ENV, "").strip()
    if raw:
        if UUID_RE.match(raw):
            return raw.lower()
        _warn(f"{SESSION_ENV} 不是 UUID 格式，按原值派生短码：{raw}")
        return raw
    try:
        fallback = f"{getpass.getuser()}@{socket.gethostname()}"
    except Exception:  # noqa: BLE001 - 兜底，取用户名失败不能中断
        fallback = f"pid:{os.getpid()}"
    _warn(f"未设置 {SESSION_ENV}，会话标识回退为 {fallback}（短码不稳定，建议设置会话 ID）")
    return fallback


def session_sid(session: Optional[str] = None) -> str:
    """会话短码：UUID 取前 8 位十六进制；否则 SHA-1 前 8 位。"""
    s = session if session is not None else session_id()
    if UUID_RE.match(s):
        return s.replace("-", "")[:8]
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:8]


def task_branch(name: str, session: Optional[str] = None) -> str:
    """按规范生成任务分支名：``task/<name>-<sid>``。"""
    return f"{TASK_PREFIX}{name}-{session_sid(session)}"


def sid_of(branch: str) -> Optional[str]:
    m = BRANCH_RE.match(branch)
    return m.group("sid") if m else None


def validate_branch(name: str) -> tuple[bool, str]:
    """校验分支名。返回 ``(ok, message)``；豁免分支直接放行。"""
    if name in EXEMPT_BRANCHES:
        return True, f"豁免分支：{name}"
    if not name.startswith(TASK_PREFIX):
        if os.environ.get(STRICT_ENV):
            return False, (
                f"非任务分支：{name}；开发分支须为 {TASK_PREFIX}<slug>-<sid>"
                f"（{BRANCH_RE.pattern}）"
            )
        return True, f"提示：非任务分支 {name}（规范建议 {TASK_PREFIX}<slug>-<sid>）"
    if not BRANCH_RE.match(name):
        return False, (
            f"分支名不合规：{name}；须匹配 {TASK_PREFIX}<slug>-<sid>，"
            f"sid 为会话标识（CATPAW_CONVERSATION_ID）前 8 位小写十六进制"
        )
    return True, "ok"


def session_mismatch(branch: str, session: Optional[str] = None) -> bool:
    """分支 ``sid`` 是否与当前会话不一致（仅提示，不阻断推送）。"""
    sid = sid_of(branch)
    return sid is not None and sid != session_sid(session)


# ──────────────────────────────────────────────
# 钩子入口
# ──────────────────────────────────────────────
def hook_pre_push(lines: Iterable[str]) -> int:
    """校验 ``git push`` 的待推引用（stdin：local_ref local_sha remote_ref remote_sha）。"""
    blocked: list[str] = []
    hints: list[str] = []
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        local_ref, local_sha = parts[0], parts[1]
        if not local_ref.startswith("refs/heads/"):
            continue
        if local_sha == ZERO_SHA:
            continue  # 删除分支
        branch = local_ref[len("refs/heads/"):]
        ok, msg = validate_branch(branch)
        if not ok:
            blocked.append(msg)
        elif branch.startswith(TASK_PREFIX) and session_mismatch(branch):
            hints.append(
                f"分支 {branch} 归属其他会话（sid={sid_of(branch)}，"
                f"当前 sid={session_sid()}）；仅提示，不阻断"
            )
    for h in hints:
        _warn(h)
    if blocked:
        for b in blocked:
            print(f"[branch-naming] 阻断推送：{b}", file=sys.stderr)
        print(
            "[branch-naming] 分支命名不符合规范，已禁止推送。"
            "请改用 `python tools/workflow_guard.py task start <name>` 建分支，"
            "或设置 BRANCH_NAMING_STRICT=0 仅放行非任务分支。",
            file=sys.stderr,
        )
        return EXIT_ERR
    return EXIT_OK


def _git(args: Sequence[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd) if cwd else None, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if check and proc.returncode != 0:
        raise NamingError(f"git {' '.join(args)} 失败：{(proc.stderr or '').strip()}")
    return proc


def hook_pre_commit() -> int:
    """提交前校验当前分支名；detached HEAD（merge / rebase 中）放行。"""
    proc = _git(["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    if proc.returncode != 0:
        return EXIT_OK
    branch = proc.stdout.strip()
    ok, msg = validate_branch(branch)
    if not ok:
        print(f"[branch-naming] 阻断提交：{msg}", file=sys.stderr)
        return EXIT_ERR
    if branch.startswith(TASK_PREFIX) and session_mismatch(branch):
        _warn(
            f"当前分支 {branch} 归属其他会话（sid={sid_of(branch)}，"
            f"当前 sid={session_sid()}）"
        )
    return EXIT_OK


# ──────────────────────────────────────────────
# 钩子安装
# ──────────────────────────────────────────────
def hooks_dir(cwd: Optional[Path] = None) -> Path:
    """共享 git hooks 目录（跨 worktree 生效）。``cwd`` 指定待操作的仓库。"""
    proc = _git(
        ["rev-parse", "--path-format=absolute", "--git-path", "hooks"],
        cwd=cwd, check=False,
    )
    out = proc.stdout.strip() if proc.returncode == 0 else ""
    if not out:
        common = _git(["rev-parse", "--git-common-dir"], cwd=cwd).stdout.strip()
        out = common
    p = Path(out)
    if not p.is_absolute():
        base = cwd.resolve() if cwd else Path.cwd()
        p = base / p
    return p.resolve()


def install_hooks(check: bool = False, uninstall: bool = False,
                  force: bool = False, cwd: Optional[Path] = None) -> bool:
    """把 ``tools/git-hooks/{pre-push,pre-commit}`` 安装到共享 hooks 目录。

    ``check`` 只比对（无差异返回 True）；``uninstall`` 删除（内容被改过需 ``force``）。
    ``cwd`` 指定目标仓库（默认当前目录）。
    """
    src_dir = Path(__file__).resolve().parent / "git-hooks"
    dst_dir = hooks_dir(cwd)
    for name in HOOK_NAMES:
        src = src_dir / name
        if not src.exists():
            raise NamingError(f"钩子源文件缺失：{src}")
        dst = dst_dir / name
        if uninstall:
            if dst.exists():
                if not force and dst.read_bytes() != src.read_bytes():
                    raise NamingError(f"钩子已被修改，未删除：{dst}（确认可删用 --force）")
                dst.unlink()
                print(f"[branch-naming] 已卸载钩子：{dst}")
            continue
        if check:
            if not dst.exists():
                print(f"[branch-naming] 未安装：{dst}")
                return False
            if dst.read_bytes() != src.read_bytes():
                print(f"[branch-naming] 钩子与源文件不一致：{dst}")
                return False
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        dst.chmod(0o755)
        print(f"[branch-naming] 已安装钩子：{dst}")
    # 自包含副本：仓库内无 tools/ 时钩子仍可运行（如临时 / 克隆环境）
    src_internal = Path(__file__).resolve()
    dst_internal = dst_dir / INTERNAL_SCRIPT_NAME
    if uninstall:
        if dst_internal.exists():
            if not force and dst_internal.read_bytes() != src_internal.read_bytes():
                raise NamingError(f"内部脚本已被修改，未删除：{dst_internal}（确认可删用 --force）")
            dst_internal.unlink()
            print(f"[branch-naming] 已卸载内部脚本：{dst_internal}")
    elif check:
        if not dst_internal.exists() or dst_internal.read_bytes() != src_internal.read_bytes():
            print(f"[branch-naming] 内部脚本缺失或不一致：{dst_internal}")
            return False
    else:
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_internal, dst_internal)
        dst_internal.chmod(0o755)
        print(f"[branch-naming] 已部署内部脚本：{dst_internal}")
    return True


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="branch_naming.py",
        description="分支命名规范（task/<slug>-<sid>）与会话标识校验 / 钩子安装",
    )
    sub = p.add_subparsers(dest="command", required=True, metavar="<command>")

    sp = sub.add_parser("session", help="打印当前会话标识与短码")
    sp.set_defaults(func=cmd_session)

    cp = sub.add_parser("check", help="校验分支名（可多个）")
    cp.add_argument("branches", nargs="+")
    cp.set_defaults(func=cmd_check)

    hp = sub.add_parser("hook", help="Git 钩子入口（由 tools/git-hooks/ 调用）")
    hp_sub = hp.add_subparsers(dest="hook_command", required=True, metavar="<钩子>")
    hpp = hp_sub.add_parser("pre-push", help="校验待推分支（读 stdin）")
    hpp.set_defaults(func=cmd_hook_pre_push)
    hpc = hp_sub.add_parser("pre-commit", help="校验当前分支")
    hpc.set_defaults(func=cmd_hook_pre_commit)

    ip = sub.add_parser("install", help="安装 / 校验 / 卸载 Git 钩子")
    ip.add_argument("--check", action="store_true", help="只校验是否已安装且一致")
    ip.add_argument("--uninstall", action="store_true", help="卸载钩子")
    ip.add_argument("--force", action="store_true", help="卸载时允许删除已修改的钩子")
    ip.set_defaults(func=cmd_install)
    return p


def cmd_session(_: argparse.Namespace) -> int:
    sid = session_sid()
    print(f"session_id  {session_id()}")
    print(f"sid         {sid}")
    return EXIT_OK


def cmd_check(args: argparse.Namespace) -> int:
    bad = False
    for name in args.branches:
        ok, msg = validate_branch(name)
        print(f"{'OK ' if ok else 'BAD'} {name}  {msg}")
        bad = bad or not ok
    return EXIT_ERR if bad else EXIT_OK


def cmd_hook_pre_push(_: argparse.Namespace) -> int:
    return hook_pre_push(sys.stdin.read().splitlines())


def cmd_hook_pre_commit(_: argparse.Namespace) -> int:
    return hook_pre_commit()


def cmd_install(args: argparse.Namespace) -> int:
    ok = install_hooks(check=args.check, uninstall=args.uninstall, force=args.force)
    return EXIT_OK if ok else EXIT_ERR


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args) or EXIT_OK
    except NamingError as exc:
        print(f"[branch-naming] 错误：{exc}", file=sys.stderr)
        return EXIT_ERR
    except KeyboardInterrupt:
        print("[branch-naming] 已中断。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
