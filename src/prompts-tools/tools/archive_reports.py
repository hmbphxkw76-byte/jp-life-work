"""报告归档策略（CI: scheduled-maintenance 的 archive_reports 步骤）。

每条业务线的 reports/ 只保留最新 N 期月度报告（默认 12 期，与阅读器展示
窗口一致），超出的移动到 reports/archives/。报告已统一为 `YYYY-MM-<slug>`
命名，归档按自然月倒序保留。

幂等：重复执行不再移动任何文件。退出码：0 = 成功；1 = 移动失败。
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import detect_month_report, iter_business_dirs  # noqa: E402

# 每主题保留的最新期数（与 build_hub 阅读器默认窗口一致）
KEEP = 12


def select_archives(items, keep: int = KEEP):
    """纯函数：给定 [(period, path)]，返回应归档的 path 列表（保留最新 keep 期）。"""
    entries = sorted(items, key=lambda e: (e[0], e[1].name), reverse=True)
    return [path for _period, path in entries[keep:]]


def main() -> int:
    moved = 0
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        items = []
        for f in sorted(reports.glob("*.html")):
            det = detect_month_report(f.name)
            if det:
                items.append((det[0], f))
        to_archive = select_archives(items)
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
