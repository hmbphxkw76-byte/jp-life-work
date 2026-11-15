"""报告内容校验 lint（validate.yml 的 lint 步骤（建议级，continue-on-error））。

扫描各业务线 reports/*.html，执行监测报告通用规范的人工校验清单（第 9 节）中
可程序化的项目。退出码：0 = 通过；1 = 存在错误项；2 = 仅存在警告项。

错误项（阻断）：
- thead / tbody / table 标签不配对、重复 </tbody>
- 畸形 <th scope="col"ead> 写法

警告项（不阻断）：
- 多列表（≥6 列）<th> 未声明百分比列宽
- <img> 缺少 alt 属性
- <table> 缺少 class="fixed"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, detect_month_report, iter_business_dirs  # noqa: E402

# 新报告认定：期间 >= NEW_FROM 视为新报告，纳入阻断级校验；历史报告由豁免清单管理。
NEW_FROM = "2026-11"
DEFAULT_WHITELIST = ROOT / "src" / "report-audits" / "audit" / "lint-whitelist.json"

TABLE_RE = re.compile(r"<table\b.*?</table>", re.DOTALL)
TH_RE = re.compile(r"<th\b[^>]*>", re.DOTALL)


def lint_html(text: str) -> list[tuple[str, str]]:
    """对单份 HTML 文本执行 lint -> [(level, message), ...]，level in {'E','W'}。"""
    issues: list[tuple[str, str]] = []

    # 标签配对（注意 '<tbody' 不会误匹配 '</tbody'）
    for tag in ("thead", "tbody", "table"):
        open_n = len(re.findall(rf"<{tag}\b", text))
        close_n = len(re.findall(rf"</{tag}>", text))
        if open_n != close_n:
            issues.append(("E", f"<{tag}> 标签不配对（开 {open_n} / 闭 {close_n}）"))
    if text.count("</tbody>") > len(re.findall(r"<tbody\b", text)):
        issues.append(("E", "存在多余的 </tbody>（疑似重复闭合）"))

    # 畸形 th 写法
    if re.search(r'<th[^>]*scope="col"ead', text):
        issues.append(("E", '存在畸形 <th scope="col"ead> 写法'))

    # 逐表检查
    for i, tbl in enumerate(TABLE_RE.findall(text), start=1):
        if 'class="fixed"' not in tbl:
            issues.append(("W", f"第 {i} 张表格缺少 class=\"fixed\"（列宽声明规范）"))
        ths = TH_RE.findall(tbl)
        if len(ths) >= 6:
            no_width = [t for t in ths if "width:" not in t]
            if no_width:
                issues.append(
                    ("W", f"第 {i} 张表格（{len(ths)} 列）有 {len(no_width)} 个 <th> 未声明百分比列宽")
                )

    # 图片可访问性
    for m in re.finditer(r"<img\b[^>]*>", text):
        if "alt=" not in m.group(0):
            issues.append(("W", "<img> 缺少 alt 属性（可访问性）"))

    return issues


def collect_report_htmls():
    """收集全部业务线 reports/*.html -> [(relpath, Path)]。"""
    out = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        for f in sorted(reports.glob("*.html")):
            out.append((f"{b.rel}/reports/{f.name}", f))
    return out


def load_whitelist(path: Path) -> set[str]:
    """读取豁免清单（JSON 数组，每项含 report / reason / review_by）-> 报告路径集合。"""
    if not path.is_file():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if isinstance(data, dict):
        data = data.get("items", [])
    return {e.get("report", "") for e in data if isinstance(e, dict)}


def _period(rel: str) -> str:
    det = detect_month_report(Path(rel).name)
    return det[0] if det else ""


def _skip(rel: str, new_only: bool, whitelist: set[str]) -> bool:
    """是否跳过该报告（白名单豁免或历史报告且 --new-only）。"""
    if rel in whitelist:
        return True
    if new_only:
        period = _period(rel)
        if period and period < NEW_FROM:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="报告内容校验 lint")
    ap.add_argument("--new-only", action="store_true",
                    help=f"仅校验期间 >= {NEW_FROM} 的新报告（历史报告跳过）")
    ap.add_argument("--whitelist", default=str(DEFAULT_WHITELIST),
                    help="历史遗留豁免清单（JSON）")
    args = ap.parse_args()

    whitelist = load_whitelist(Path(args.whitelist))
    targets = collect_report_htmls()
    if not targets:
        print("lint：未发现报告 HTML，跳过")
        return 0
    errors = warnings = skipped = 0
    for rel, path in targets:
        if _skip(rel, args.new_only, whitelist):
            print(f"[SKIP] {rel}（{'白名单豁免' if rel in whitelist else '历史报告'}）")
            skipped += 1
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        issues = lint_html(text)
        if not issues:
            print(f"[OK] {rel}")
            continue
        for level, msg in issues:
            print(f"[{level}] {rel}: {msg}")
            if level == "E":
                errors += 1
            else:
                warnings += 1
    if errors:
        print(f"lint 失败：{errors} 项错误，{warnings} 项警告")
        return 1
    if warnings:
        print(f"lint 存在 {warnings} 项警告（无错误，不阻断）；跳过 {skipped} 份")
        return 2
    print(f"lint 通过：{len(targets) - skipped} 份报告全部合格（跳过 {skipped} 份）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
