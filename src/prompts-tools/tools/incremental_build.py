#!/usr/bin/env python3
"""增量生成 POC（架构优化方向 D / I-5）。

按 ``git diff`` 选择受影响的报告 md，仅对这些报告执行 md2html 转换；
``build_hub`` / ``build_index`` 仍全量（汇总页需全量重建）。

用法：
    python src/prompts-tools/tools/incremental_build.py [--base main...HEAD] [--dry-run] [--bench]

``--bench``：输出全量 vs 增量的耗时对比 JSON（供 T2.5 基准对比）。

退出码：0 成功；1 失败。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, atomic_write, detect_month_report, iter_business_dirs  # noqa: E402


def changed_reports(base: str) -> list[str]:
    """返回 base...工作区 中变更的月度报告 md 相对路径（排序去重）。"""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", base], cwd=str(ROOT),
            capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    reps = []
    for line in out.splitlines():
        p = line.strip().replace("\\", "/")
        if p.endswith(".md") and "/reports/" in p and detect_month_report(Path(p).name):
            reps.append(p)
    return sorted(set(reps))


def all_reports() -> list[str]:
    """全部月度报告 md 相对路径。"""
    out = []
    for b in iter_business_dirs():
        rd = b.path / "reports"
        if rd.is_dir():
            out.extend(f"{b.rel}/reports/{p.name}" for p in rd.glob("*.md")
                       if detect_month_report(p.name))
    return sorted(out)


def _convert(rel: str) -> None:
    import md2html
    md = ROOT / rel
    atomic_write(md.with_suffix(".html"), md2html.convert(md))


def main() -> int:
    ap = argparse.ArgumentParser(description="增量生成 POC")
    ap.add_argument("--base", default="main...HEAD", help="git diff 基点（默认 main...HEAD）")
    ap.add_argument("--dry-run", action="store_true", help="只列出变更报告，不转换")
    ap.add_argument("--bench", action="store_true", help="输出全量 vs 增量耗时对比 JSON")
    args = ap.parse_args()

    reps = changed_reports(args.base)
    if not reps:
        print("无变更报告，跳过")
        return 0
    print(f"变更报告 {len(reps)} 份：")
    for r in reps:
        print("  " + r)
    if args.dry_run:
        return 0

    import md2html  # noqa: F401  （触发与全量一致的转换路径）

    t0 = time.perf_counter()
    for rel in reps:
        _convert(rel)
    inc = time.perf_counter() - t0

    if args.bench:
        t0 = time.perf_counter()
        for rel in all_reports():
            _convert(rel)
        full = time.perf_counter() - t0
        print(json.dumps({
            "changed": len(reps), "full": len(all_reports()),
            "incremental_sec": round(inc, 3), "full_sec": round(full, 3),
            "speedup": round(full / inc, 2) if inc > 0 else None,
        }, ensure_ascii=False))
    else:
        print(f"已增量生成 {len(reps)} 份 HTML")
    return 0


if __name__ == "__main__":
    sys.exit(main())
