"""汇总页生成（CI: ci.yml --check 校验 / html-sync、scheduled-maintenance 重新生成）。

生成 index.html（报告枢纽：按业务线分组的报告列表）与 reader.html
（在线阅读壳：侧栏列表 + iframe 加载报告，?report=<路径>）。

--check 模式（ci.yml 使用）：重新计算内容与现有文件比对；
- 文件存在且一致 -> 退出码 0
- 文件存在但过期 -> 退出码 1（阻断合并）
- 文件不存在    -> 退出码 0 并提示（全新克隆尚未生成，由定时维护首建）

比对前对「最近生成」时间戳做归一化（normalize_for_check）：时间戳为分钟级心跳
（随定时维护提交，与 INDEX.md 同理），不参与最新性判定——否则重算内容必然
与已提交文件相差时间戳一行，index.html 恒判过期。

退出码（生成模式）：0 = 成功；1 = 写入失败。
"""
from __future__ import annotations

import argparse
import html as html_mod
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, detect_report, iter_business_dirs, report_title  # noqa: E402

CYCLE_LABEL = {"monthly": "月度", "quarterly": "季度", "annual": "年度", "baseline": "基线", "weekly": "周报"}


def collect_entries():
    """-> {business_rel: [(cycle_label, period, relpath, title)]}，period 降序。"""
    grouped: dict[str, list] = {}
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        for f in sorted(reports.glob("*.html")):
            det = detect_report(f.name)
            if not det:
                continue
            cycle, period, _ = det
            text = f.read_text(encoding="utf-8", errors="replace")
            grouped.setdefault(b.rel, []).append(
                (CYCLE_LABEL.get(cycle, cycle), period, f"{b.rel}/reports/{f.name}", report_title(text))
            )
    for items in grouped.values():
        items.sort(key=lambda e: e[1], reverse=True)
    return grouped


def _style() -> str:
    return (
        "body{max-width:1160px;margin:24px auto;padding:0 16px;"
        'font-family:"Segoe UI","Microsoft YaHei",sans-serif;color:#1a1a2e;line-height:1.6}'
        "h1,h2{color:#16213e}a{color:#1d4ed8;text-decoration:none}a:hover{text-decoration:underline}"
        "table{border-collapse:collapse;width:100%}th,td{border:1px solid #cbd5e1;padding:6px 10px;text-align:left}"
        "th{background:#f1f5f9}.muted{color:#64748b;font-size:.9em}"
    )


def render_hub(grouped, now_iso: str) -> str:
    parts = [
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        "<title>MacroPulse 报告枢纽</title>",
        f"<style>{_style()}</style>\n</head>\n<body>",
        "<h1>MacroPulse 报告枢纽</h1>",
        f'<p class="muted">最近生成：{now_iso}</p>',
    ]
    if not grouped:
        parts.append("<p>暂无已产出报告。</p>")
    for rel, items in grouped.items():
        parts.append(f"<h2>{html_mod.escape(rel)}</h2>")
        parts.append("<table><thead><tr><th>类型</th><th>周期</th><th>报告</th></tr></thead><tbody>")
        for label, period, path, title in items:
            text = html_mod.escape(title or period)
            parts.append(
                f'<tr><td>{label}</td><td>{period}</td>'
                f'<td><a href="{html_mod.escape(path)}">{text}</a></td></tr>'
            )
        parts.append("</tbody></table>")
    parts.append("</body>\n</html>")
    return "\n".join(parts)


def render_reader(grouped) -> str:
    rows = []
    for rel, items in grouped.items():
        for label, period, path, title in items:
            text = html_mod.escape(f"{rel} · {label} {period}")
            rows.append(f'<li><a href="?report={html_mod.escape(path)}">{text}</a></li>')
    body = "<ul>" + "".join(rows) + "</ul>" if rows else "<p>暂无已产出报告。</p>"
    return (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>MacroPulse 阅读器</title>\n"
        "<style>"
        'body{margin:0;font-family:"Segoe UI","Microsoft YaHei",sans-serif;color:#1a1a2e;display:flex;height:100vh}'
        "nav{width:300px;overflow:auto;border-right:1px solid #cbd5e1;padding:16px;box-sizing:border-box}"
        "main{flex:1}iframe{width:100%;height:100%;border:0}"
        "a{color:#1d4ed8;text-decoration:none}a:hover{text-decoration:underline}"
        "</style>\n</head>\n<body>\n"
        f"<nav><h2>报告列表</h2>{body}</nav>\n"
        "<main><iframe id=\"frame\" title=\"报告内容\"></iframe></main>\n"
        "<script>var p=new URLSearchParams(location.search).get('report');"
        "if(p){document.getElementById('frame').src=p;}</script>\n"
        "</body>\n</html>"
    )


def build_outputs() -> dict[str, str]:
    grouped = collect_entries()
    now_iso = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return {"index.html": render_hub(grouped, now_iso), "reader.html": render_reader(grouped)}


GENERATED_TS_RE = re.compile(r'(<p class="muted">最近生成：)[^<]*(</p>)')


def normalize_for_check(text: str) -> str:
    """--check 比对专用归一化：抹平「最近生成」生成时刻时间戳（不参与一致性判定）。

    纯函数，供 tests/ 直接调用。
    """
    return GENERATED_TS_RE.sub(r"\g<1>TIMESTAMP\g<2>", text)


def compare_outputs(outputs: dict[str, str]) -> tuple[list[str], list[str]]:
    """现有汇总页与重算内容比对 -> (stale, missing)。"""
    stale: list[str] = []
    missing: list[str] = []
    for name, content in outputs.items():
        f = ROOT / name
        if not f.exists():
            missing.append(name)
        elif normalize_for_check(f.read_text(encoding="utf-8", errors="replace")) != normalize_for_check(content):
            stale.append(name)
    return stale, missing


def main() -> int:
    ap = argparse.ArgumentParser(description="生成汇总页 index.html / reader.html")
    ap.add_argument("--check", action="store_true", help="校验现有汇总页是否为最新")
    args = ap.parse_args()

    outputs = build_outputs()
    if args.check:
        stale, missing = compare_outputs(outputs)
        if stale:
            print(f"[ERROR] 汇总页已过期：{', '.join(stale)}（运行 python prompts/tools/build_hub.py 重新生成）")
            return 1
        if missing:
            print(f"[WARN] 汇总页尚未生成：{', '.join(missing)}（由定时维护首建，不阻断）")
            return 0
        print("汇总页校验通过：index.html / reader.html 均为最新")
        return 0

    try:
        for name, content in outputs.items():
            (ROOT / name).write_text(content, encoding="utf-8")
    except OSError as e:
        print(f"[ERROR] 写入汇总页失败: {e}")
        return 1
    print("汇总页已生成：index.html / reader.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
