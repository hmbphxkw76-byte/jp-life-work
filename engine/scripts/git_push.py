#!/usr/bin/env python3
"""GitHub 双通道推送（ssh / https failover），仅用于 jp-life-work。

背景：GitHub 的 ssh 与 https 通道可能各自出现网络抖动（443 被 reset、ssh 不通等），
单通道会在抖动时需要人工重试。本工具把两条通道「同时」纳入配置，推送时：

  1. 先走主通道（默认 ``origin``，ssh）；
  2. 主通道失败 → 切换备用通道（默认 ``origin-https``，https）再试一次；
  3. 两条都失败 → 立即停止，**不重试**（避免把抖动放大成刷屏重试）。

git 原生多 ``pushurl`` 不会 failover（实测 https 被 reset 后直接 fatal，不回退 ssh），
所以这一层必须由外层完成——本工具即该外层，也被 ``engine/scripts/workflow_guard.py`` 的
``merge`` / ``sync`` 推送路径调用。

约定（仅限本 repo）：
  - ``origin``      → ``git@github.com:hmbphxkw76-byte/jp-life-work.git``（ssh）
  - ``origin-https``→ ``https://github.com/hmbphxkw76-byte/jp-life-work.git``（https）
  - 本 repo 永不使用 GitLab；推送 / 合并 / 提交只走 GitHub。

用法：
  python engine/scripts/git_push.py --remote origin [--fallback origin-https]
                           [--force-with-lease] [--dry-run] <refspec...>

退出码：0 成功（任一通道）；1 全部通道失败 / 参数错误。
本工具只用标准库，Windows / POSIX 通用。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence

EXIT_OK = 0
EXIT_ERR = 1

DEFAULT_REMOTE = "origin"
DEFAULT_FALLBACK = "origin-https"


def _run_push(remote: str, refspecs: Sequence[str], force_with_lease: bool,
              dry_run: bool) -> tuple[int, str]:
    """执行一次 ``git push``，返回 (退出码, 合并后的输出)。"""
    cmd = ["git", "push"]
    if force_with_lease:
        cmd.append("--force-with-lease")
    if dry_run:
        cmd.append("--dry-run")
    cmd.append(remote)
    cmd.extend(refspecs)
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def push_with_failover(remote: str, refspecs: Sequence[str],
                       fallback: str | None = DEFAULT_FALLBACK,
                       force_with_lease: bool = False,
                       dry_run: bool = False) -> int:
    """先试主通道，失败切备用通道；都失败即停止，不重试。

    每条通道只调用一次 ``git push``，不做任何内部重试。
    """
    channels = [remote]
    if fallback and fallback != remote:
        channels.append(fallback)

    failures: list[tuple[str, int, str]] = []
    for idx, chan in enumerate(channels):
        code, out = _run_push(chan, refspecs, force_with_lease, dry_run)
        if out:
            print(out, end="" if out.endswith("\n") else "\n")
        if code == 0:
            if idx > 0:
                print(f"[git_push] 主通道 {channels[0]} 不可用，已改用 {chan} 推送成功。")
            return EXIT_OK
        failures.append((chan, code, out))
        if idx == 0 and len(channels) > 1:
            print(
                f"[git_push] 通道 {chan} 推送失败，切换备用通道 {channels[1]}（仅尝试一次）。",
                file=sys.stderr,
            )

    print("[git_push] 所有通道均推送失败，已停止（不重试）。", file=sys.stderr)
    for chan, code, out in failures:
        print(f"--- 通道 {chan}（退出码 {code}）---\n{out.strip()}", file=sys.stderr)
    return EXIT_ERR


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="git_push.py",
        description="GitHub 双通道推送（ssh / https failover，都失败即停止）",
    )
    p.add_argument("--remote", default=DEFAULT_REMOTE,
                   help=f"主通道 remote（默认 {DEFAULT_REMOTE}，ssh）")
    p.add_argument("--fallback", default=DEFAULT_FALLBACK,
                   help=f"备用通道 remote（默认 {DEFAULT_FALLBACK}，https）；"
                        f"传空字符串则不 failover")
    p.add_argument("--force-with-lease", action="store_true",
                   help="推送带 --force-with-lease（防覆盖远端）")
    p.add_argument("--dry-run", action="store_true", help="只演练，不实际推送")
    p.add_argument("refspecs", nargs="+", help="推送的 refspec（如 HEAD:main）")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    fallback = args.fallback.strip() or None
    return push_with_failover(
        remote=args.remote,
        refspecs=args.refspecs,
        fallback=fallback,
        force_with_lease=args.force_with_lease,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
