#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""报告归档与保留策略（全库共用）。

常规规则（对每个 NN-*/reports/ 生效）：
- 顶层只保留最新 3 份文档；md 与同名 html 视为一份
- 其余移入 reports/archives/
- archives/ 常规版本最多保留 7 份，超出删除最旧
- *_baseline（当前基线）固定在顶层；历史基线 *_baseline_<period> 留在归档目录
- 历史基线最多保留 12 个周期，超出删除最旧

基线轮换（详见 基线报告管理规则.md）：
    python prompts/tools/archive_reports.py rotate-baseline \
        --topic 01-ssw-driver --period 2026.12 \
        [--source <新基线文件>] [--old-period 2026.11] [--dry-run]

用法:
    python prompts/tools/archive_reports.py --dry-run   # 预览
    python prompts/tools/archive_reports.py             # 执行
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEEP_TOP = 3
KEEP_ARCHIVE = 7
KEEP_BASELINE = 12
KNOWN_SUFFIXES = {".md", ".html"}
PERIOD_SUFFIX = re.compile(
    r"_baseline_(\d{4})(?:\.(\d{2})|Q([1-4])|H([1-2]))?$", re.IGNORECASE)
PERIOD_ARG = re.compile(r"^\d{4}(?:\.\d{2}|Q[1-4]|H[1-2])?$")
VERSION = re.compile(r"_v(\d{4})\.(\d{2})\.(\d{2})(?:_(\d+))?$")


def is_current_baseline(stem: str) -> bool:
    """当前基线（无周期后缀）常驻 reports/ 顶层。"""
    return stem.lower().endswith("_baseline")


def is_historical_baseline(stem: str) -> bool:
    """历史基线（带周期后缀）留在 archives/。"""
    return bool(PERIOD_SUFFIX.search(stem))


def period_key(stem: str):
    """历史基线周期排序键：(年, 类型, 序号)。"""
    m = PERIOD_SUFFIX.search(stem)
    if not m:
        return None
    y, mo, q, h = m.groups()
    if q:
        return (int(y), 1, int(q))
    if h:
        return (int(y), 2, int(h))
    return (int(y), 0, int(mo))


def sort_key(stem: str):
    """版本名按日期+序号排序；历史基线按周期排序；其余按自然顺序。"""
    m = VERSION.search(stem)
    if m:
        y, mo, d, seq = m.groups()
        return (1, int(y), int(mo), int(d), int(seq or 0))
    pk = period_key(stem)
    if pk:
        return (2, pk[0], pk[1], pk[2], 0)
    return (0, tuple((0, int(p)) if p.isdigit() else (1, p.lower())
                     for p in re.split(r"(\d+)", stem) if p))


def stems_in(directory: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for f in directory.iterdir():
        if f.is_file() and f.suffix.lower() in KNOWN_SUFFIXES:
            groups.setdefault(f.stem, []).append(f)
    return groups


def find_reports_dir(topic_id: str) -> Path:
    for reports in sorted(ROOT.glob("[0-9][0-9]-*/reports")):
        if reports.is_dir() and reports.parent.name == topic_id:
            return reports
    raise SystemExit(f"未找到主题目录: {topic_id}")


def detect_period(reports: Path, current: list[Path]):
    """推断当前基线周期：优先读 baseline-meta.json，其次解析内容版本行。"""
    meta = reports / "baseline-meta.json"
    if meta.exists():
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            if data.get("period"):
                return data["period"]
        except (OSError, json.JSONDecodeError):
            pass
    for p in current:
        if p.suffix.lower() == ".md":
            try:
                text = p.read_text(encoding="utf-8")[:2000]
            except OSError:
                continue
            m = re.search(r"v(\d{4})\.(\d{2})\.\d{2}", text)
            if m:
                return f"{m.group(1)}.{m.group(2)}"
    return None


def rotate_baseline(args) -> int:
    if not PERIOD_ARG.match(args.period):
        print(f"周期格式不正确: {args.period}（应为 YYYY.MM / YYYY.QN / YYYY.HN / YYYY）")
        return 1
    reports = find_reports_dir(args.topic)
    archives = reports / "archives"
    current = sorted(p for p in reports.iterdir()
                     if p.is_file() and p.suffix.lower() in KNOWN_SUFFIXES
                     and is_current_baseline(p.stem))
    if not current:
        print(f"[{args.topic}] 未找到当前基线 *_baseline，跳过")
        return 1

    old_period = args.old_period or detect_period(reports, current)
    if old_period is None:
        print(f"[{args.topic}] 无法推断旧基线周期，请用 --old-period 指定")
        return 1

    source = Path(args.source) if args.source else None
    if source is not None and not source.is_absolute():
        source = ROOT / source
    if source is None or not source.exists():
        print(f"[{args.topic}] 新基线文件不存在: {source}")
        return 1

    stem = current[0].stem
    print(f"[{args.topic}] 归档旧基线: {stem} (周期 {old_period}) "
          f"→ archives/{stem}_{old_period}")
    print(f"[{args.topic}] 安装新基线: {source.name} → {stem}{source.suffix}")
    if args.dry_run:
        return 0

    archives.mkdir(exist_ok=True)
    for p in current:
        shutil.move(str(p), str(archives / f"{stem}_{old_period}{p.suffix}"))
    shutil.copy2(str(source), str(reports / f"{stem}{source.suffix}"))
    html = source.with_suffix(".html")
    if html.exists():
        shutil.copy2(str(html), str(reports / f"{stem}.html"))
    (reports / "baseline-meta.json").write_text(
        json.dumps({"period": args.period, "source": source.name},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不移动/删除")
    sub = parser.add_subparsers(dest="command")
    rot = sub.add_parser("rotate-baseline", help="轮换基线：归档旧基线 + 安装新基线")
    rot.add_argument("--topic", required=True, help="主题 id，如 01-ssw-driver")
    rot.add_argument("--period", required=True, help="新基线周期，如 2026.12 或 2026.Q4")
    rot.add_argument("--source", help="新基线文件（md；同名 html 一并复制）")
    rot.add_argument("--old-period", help="旧基线周期（默认从 meta/内容推断）")
    rot.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.command == "rotate-baseline":
        return rotate_baseline(args)

    for reports in sorted(ROOT.glob("[0-9][0-9]-*/reports")):
        if not reports.is_dir():
            continue
        archives = reports / "archives"
        if archives.is_dir():
            for stem, files in stems_in(archives).items():
                if is_current_baseline(stem):
                    print(f"[{reports.relative_to(ROOT)}] 基线版移回顶层: {stem}")
                    if not args.dry_run:
                        for f in files:
                            shutil.move(str(f), str(reports / f.name))
        groups = stems_in(reports)

        ordered = sorted(groups, key=sort_key)
        pinned = [s for s in ordered if is_current_baseline(s)]
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

        # 归档目录按上限裁剪：常规版本与历史基线分别计算
        if archives.is_dir():
            arch_groups = stems_in(archives)
            for label, keep_n in (("常规版本", KEEP_ARCHIVE), ("历史基线", KEEP_BASELINE)):
                sel = {s: f for s, f in arch_groups.items()
                       if (label == "历史基线") == is_historical_baseline(s)}
                ordered = sorted(sel, key=sort_key)
                drop = ordered[:-keep_n] if len(ordered) > keep_n else []
                if drop:
                    print(f"[{reports.relative_to(ROOT)}/archives] 删除最旧 {len(drop)} 份{label}: "
                          f"{', '.join(drop)}")
                    if not args.dry_run:
                        for stem in drop:
                            for f in sel[stem]:
                                f.unlink()

    print("\n预览完成（未改动）" if args.dry_run else "\n完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
