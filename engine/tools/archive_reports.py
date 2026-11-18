"""报告归档策略（scheduled-maintenance.yml 的归档步骤）。

每条业务线的 reports/ 按周期类型保留近 N 期报告（月 18 / 季 24 / 年 60，
由 report_cycles.py 按主题 business-config / prompts 自动识别），超出的移动到
reports/archives/。报告已统一为 `YYYY-MM-<slug>` 命名，归档按自然月倒序保留。

窗口按当前日期滚动计算（近 N 个自然月），与汇总页展示窗口同源。

幂等：重复执行不再移动任何文件。退出码：0 = 成功；1 = 移动失败。
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import detect_month_report, iter_business_dirs  # noqa: E402
from report_cycles import cycle_profile, keep_periods  # noqa: E402


def select_archives(items, keep_months: int, now: str | None = None):
    """纯函数：给定 [(period, path)]，返回应归档的 path 列表（保留近 keep_months 月）。"""
    periods = [p for p, _ in items]
    keep, _archive = keep_periods(periods, keep_months, now)
    keep_set = set(keep)
    return [path for p, path in items if p not in keep_set]


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="报告归档策略（按周期保留近 N 个自然月）")
    ap.add_argument("--now", default=None,
                    help="当前月 YYYY-MM（缺省取系统当前月；用于确定性复现）")
    args = ap.parse_args()

    moved = 0
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        profile = cycle_profile(b)
        items = []
        for f in sorted(reports.glob("*.html")):
            det = detect_month_report(f.name)
            if det:
                items.append((det[0], f))
        to_archive = select_archives(items, profile["keep_months"], now=args.now)
        if not to_archive:
            continue
        archives = reports / "archives"
        archives.mkdir(exist_ok=True)
        for f in to_archive:
            # md 源稿一并归档，保持双格式成对
            pair = [f, f.with_suffix(".md")]
            for src in pair:
                if not src.exists():
                    continue
                try:
                    shutil.move(str(src), str(archives / src.name))
                    print(f"[ARCHIVED] {b.rel}/reports/{src.name} -> archives/")
                    moved += 1
                except OSError as e:
                    print(f"[ERROR] 归档失败 {src.name}: {e}")
                    return 1
    if moved:
        print(f"归档完成：移动 {moved} 份历史报告文件")
    else:
        print("归档策略检查：无超出保留期数的报告，未移动任何文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
