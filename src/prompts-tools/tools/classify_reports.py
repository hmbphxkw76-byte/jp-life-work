"""报告自动归位（CI: scheduled-maintenance / content-update 的 classify 步骤）。

扫描散落在业务目录之外（仓库根、report_templates/ 等）的报告文件，
按文件名中的地区 / 物业类型线索判定归属业务线。

用法：
    python prompts/tools/classify_reports.py --apply --unknown-warn
    python prompts/tools/classify_reports.py --check --unknown-warn

退出码：
    0 = 无错位报告
    1 = 存在可自动归位的错位（--check 模式），或 --apply 移动失败
    2 = 存在无法判定归属的报告（--unknown-warn 时不阻断）
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import detect_report, iter_business_dirs, ROOT, TEMPLATE_ROOT  # noqa: E402


def strays() -> list[Path]:
    """收集业务目录之外的报告文件（仓库根一级 + src/report_templates/）。"""
    out: list[Path] = []
    for f in sorted(ROOT.iterdir()):
        if f.is_file() and detect_report(f.name):
            out.append(f)
    tpl = TEMPLATE_ROOT
    if tpl.is_dir():
        for f in sorted(tpl.rglob("*")):
            if f.is_file() and detect_report(f.name):
                out.append(f)
    return out


def owner_of(name: str):
    """按文件名包含的地区 / 物业类型词判定唯一归属业务线；无 / 多归属返回 None。"""
    lower = name.lower()
    hits = [
        b
        for b in iter_business_dirs()
        if any(n and n.lower() in lower for n in (b.region, b.property_type))
    ]
    return hits[0] if len(hits) == 1 else None


def main() -> int:
    ap = argparse.ArgumentParser(description="报告自动归位")
    ap.add_argument("--apply", action="store_true", help="执行移动（缺省仅报告）")
    ap.add_argument("--check", action="store_true", help="只检查：存在可自动归位项时退出码 1")
    ap.add_argument("--unknown-warn", action="store_true", help="无法判定归属时仅告警（退出码 2）")
    args = ap.parse_args()

    files = strays()
    movable: list[tuple[Path, Path]] = []
    unknown: list[Path] = []
    for f in files:
        target = owner_of(f.name)
        if target is None:
            unknown.append(f)
        else:
            movable.append((f, target.path / "reports" / f.name))

    for f in unknown:
        print(f"[UNKNOWN] {f.relative_to(ROOT)}: 无法判定归属业务线")
    for src, dst in movable:
        print(f"[MISPLACED] {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

    if args.apply:
        failed = 0
        for src, dst in movable:
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                print(f"[MOVED] {src.name} -> {dst.relative_to(ROOT)}")
            except OSError as e:
                print(f"[ERROR] 移动失败 {src.name}: {e}")
                failed += 1
        if failed:
            return 1
        if unknown and args.unknown_warn:
            return 2
        return 0

    if movable:
        hint = "运行 python prompts/tools/classify_reports.py --apply 自动归位" if args.check else ""
        print(f"存在 {len(movable)} 份可自动归位的错位报告 {hint}")
        return 1
    if unknown and args.unknown_warn:
        print(f"存在 {len(unknown)} 份需人工确认归属的报告（不阻断）")
        return 2
    print("报告归位检查通过：无错位报告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
