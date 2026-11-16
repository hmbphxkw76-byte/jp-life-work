#!/usr/bin/env python3
"""测试分片执行（架构优化方向 D / I-5）。

将 `src/tests` 下的测试模块分片到多个进程执行并汇总结果：

- 默认 ``--workers 1``（串行，安全）；
- ``--workers N``：并行执行 N 个测试模块；
- ``--shard i/N``：只执行第 i 片（供 CI 并行分片使用）。

退出码：0 = 全部通过；1 = 存在失败 / 错误。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "src" / "tests"


def _modules() -> list[str]:
    return sorted(p.stem for p in TESTS_DIR.glob("test_*.py"))


def _run_module(mod: str) -> tuple[str, int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "src/tests", "-p", f"{mod}.py"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-3:]
    return mod, proc.returncode, "\n".join(tail)


def main() -> int:
    ap = argparse.ArgumentParser(description="测试分片执行")
    ap.add_argument("--workers", type=int, default=1, help="并行进程数（默认 1=串行）")
    ap.add_argument("--shard", default=None, help="分片 i/N（只执行第 i 片）")
    args = ap.parse_args()

    mods = _modules()
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        mods = [m for idx, m in enumerate(mods) if idx % n == i - 1]
    if not mods:
        print("[run-tests] 无匹配测试模块")
        return 0

    workers = max(1, min(args.workers, len(mods)))
    if workers == 1:
        results = [_run_module(m) for m in mods]
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(_run_module, mods))

    failed = [r for r in results if r[1] != 0]
    for mod, code, tail in results:
        status = "OK" if code == 0 else f"FAIL({code})"
        print(f"[{status}] {mod}")
        if code != 0:
            print("  " + tail.replace("\n", "\n  "))
    print(f"合计 {len(results)} 个模块，失败 {len(failed)} 个")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
