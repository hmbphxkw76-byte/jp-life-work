"""全局报告索引（scheduled-maintenance.yml 的索引步骤）。

汇总全部业务线 reports/ 下的月度报告，生成仓库根 INDEX.md
（scheduled-maintenance.yml 提交该文件，其「最近生成」时间戳用作活跃度心跳）。

退出码：0 = 成功；1 = 写入失败。
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, detect_month_report, iter_business_dirs, report_title  # noqa: E402

# --check 归一化：抹平「最近生成」时间戳与文件系统 mtime 列（后者随检出时间漂移）。
GENERATED_TS_RE = re.compile(r"> 最近生成：[^\n]*")
MTIME_RE = re.compile(r"\| \d{4}-\d{2}-\d{2} \d{2}:\d{2} \|")


def normalize_for_check(text: str) -> str:
    """--check 比对专用归一化（纯函数，供 tests 调用）。"""
    text = GENERATED_TS_RE.sub("> 最近生成：<TS>", text)
    return "\n".join(MTIME_RE.sub("| <MTIME> |", ln) for ln in text.splitlines())


def collect_entries():
    """-> [(business_rel, period, relpath, title, mtime_iso)]，period 降序。"""
    entries = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        for f in sorted(reports.glob("*.html")):
            det = detect_month_report(f.name)
            if not det:
                continue
            period = det[0]
            text = f.read_text(encoding="utf-8", errors="replace")
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            entries.append(
                (b.rel, period, f"{b.rel}/reports/{f.name}", report_title(text), mtime)
            )
    entries.sort(key=lambda e: (e[0], e[1]), reverse=True)
    return entries


def render_index(entries, now_iso: str) -> str:
    lines = [
        "# 日本生活与工作 · 报告索引",
        "",
        f"> 最近生成：{now_iso}（由 engine/tools/build_index.py 自动维护）",
        "",
    ]
    if not entries:
        lines.append("暂无已产出报告。")
        return "\n".join(lines) + "\n"
    current = None
    for rel, period, path, title, mtime in entries:
        if rel != current:
            current = rel
            lines += [f"## {rel}", "", "| 月份 | 报告 | 标题 | 更新时间 (UTC) |", "|---|---|---|---|"]
        name = Path(path).name
        lines.append(f"| {period} | [{name}]({path}) | {title or '—'} | {mtime:%Y-%m-%d %H:%M} |")
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="生成全局报告索引 INDEX.md")
    ap.add_argument("--check", action="store_true",
                    help="校验 INDEX.md 是否与当前生成结果一致（忽略时间戳 / mtime）")
    args = ap.parse_args(argv)
    entries = collect_entries()
    now_iso = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = render_index(entries, now_iso)
    if args.check:
        p = ROOT / "INDEX.md"
        if not p.exists():
            print("[WARN] INDEX.md 不存在（由定时维护生成），跳过校验")
            return 2
        cur = p.read_text(encoding="utf-8")
        if normalize_for_check(cur) == normalize_for_check(text):
            print(f"INDEX.md 与生成结果一致（{len(entries)} 份报告）")
            return 0
        print("[ERROR] INDEX.md 已过期：请运行 python engine/tools/build_index.py 重新生成后提交")
        return 1
    try:
        (ROOT / "INDEX.md").write_text(text, encoding="utf-8")
    except OSError as e:
        print(f"[ERROR] 写入 INDEX.md 失败: {e}")
        return 1
    print(f"索引已生成：INDEX.md（{len(entries)} 份报告，{len({e[0] for e in entries})} 条业务线）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
