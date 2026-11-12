#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""报告归档与保留策略（全库共用）。

规则（对每个 monitors-*/reports/ 生效）：
- 顶层只保留最新 3 份文档；md 与同名 html 视为一份
- 其余移入 reports/archives/
- archives/ 最多保留 7 份，超出删除最旧
- *_baseline（基线版）固定在顶层，永不归档；归档目录中的基线版会被移回顶层

用法:
    python prompts/tools/archive_reports.py --dry-run   # 预览
    python prompts/tools/archive_reports.py             # 执行
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEEP_TOP = 3
KEEP_ARCHIVE = 7
KNOWN_SUFFIXES = {".md", ".html"}


def is_pinned(stem: str) -> bool:
    """基线版常驻 reports/ 顶层。"""
    return stem.lower().endswith("_baseline")
VERSION = re.compile(r"_v(\d{4})\.(\d{2})\.(\d{2})(?:_(\d+))?$")


def sort_key(stem: str):
    """版本名按日期+序号排序；其余按自然顺序。"""
    m = VERSION.search(stem)
    if m:
        y, mo, d, seq = m.groups()
        return (1, int(y), int(mo), int(d), int(seq or 0))
    return (0, tuple((0, int(p)) if p.isdigit() else (1, p.lower())
                     for p in re.split(r"(\d+)", stem) if p))


def stems_in(directory: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for f in directory.iterdir():
        if f.is_file() and f.suffix.lower() in KNOWN_SUFFIXES:
            groups.setdefault(f.stem, []).append(f)
    return groups


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不移动/删除")
    args = parser.parse_args()

    for reports in sorted(ROOT.glob("monitors-*/reports")):
        if not reports.is_dir():
            continue
        archives = reports / "archives"
        if archives.is_dir():
            for stem, files in stems_in(archives).items():
                if is_pinned(stem):
                    print(f"[{reports.relative_to(ROOT)}] 基线版移回顶层: {stem}")
                    if not args.dry_run:
                        for f in files:
                            shutil.move(str(f), str(reports / f.name))
        groups = stems_in(reports)

        ordered = sorted(groups, key=sort_key)
        pinned = [s for s in ordered if is_pinned(s)]
        others = [s for s in ordered if s not in pinned]
        keep = pinned + others[-(KEEP_TOP - len(pinned)):] if len(ordered) > KEEP_TOP else ordered
        move = [s for s in ordered if s not in keep]

        if move:
            print(f"\n[{reports.relative_to(ROOT)}] 归档 {len(move)} 份: {', '.join(move)}")
            if not args.dry_run:
                archives.mkdir(exist_ok=True)
                for stem in move:
                    for f in groups[stem]:
                        shutil.move(str(f), str(archives / f.name))

        # 归档目录按上限裁剪
        if archives.is_dir():
            arch_groups = stems_in(archives)
            arch_ordered = sorted(arch_groups, key=sort_key)
            drop = arch_ordered[:-KEEP_ARCHIVE] if len(arch_ordered) > KEEP_ARCHIVE else []
            if drop:
                print(f"[{reports.relative_to(ROOT)}/archives] 删除最旧 {len(drop)} 份: {', '.join(drop)}")
                if not args.dry_run:
                    for stem in drop:
                        for f in arch_groups[stem]:
                            f.unlink()

    print("\n预览完成（未改动）" if args.dry_run else "\n完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
