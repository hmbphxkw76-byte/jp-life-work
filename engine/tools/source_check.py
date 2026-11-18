#!/usr/bin/env python3
"""source_check.py — 来源条目 schema 化与格式校验（P1-2）。

把各报告「参考来源清单 / 来源」章节的条目解析为**机读四元组**
（来源文本 / 时点年份 / URL / 分级分组），产出 `source-index.json`，
并校验来源格式约定：

- E1：报告存在来源章节（P1，阻断）；
- E2：来源章节含 URL 条目（P2，告警；00 决策枢纽等引用型报告可空）；
- E3：URL 条目附 4 位年份（时点）（P2，告警）；
- E4：报告声明来源分级（分级 / 官方一手 / 权威 / 媒体）（P2，告警）。

输出：``engine/report-audits/audit/source-index.json``（schema 化索引）。

用法：
    python engine/tools/source_check.py            # 全量校验并写索引
    python engine/tools/source_check.py --check    # 不写文件
    python engine/tools/source_check.py --json

退出码：0=通过；1=存在来源章节缺失（阻断）；2=仅告警。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, atomic_write, iter_business_dirs  # noqa: E402

SECTION_RE = re.compile(r"^##\s+.*(?:参考来源|来源|引用)", re.M)
URL_RE = re.compile(r"https?://[^\s)\]]+")
YEAR_RE = re.compile(r"(19|20)\d{2}")
GRADE_RE = re.compile(r"分级|官方一手|权威|媒体|A 级|B 级|C 级")
GROUP_RE = re.compile(r"^(?:###\s*)?[①②③④⑤]|"  # ① 日本政府官方一手
                      r"^\*\*([ABC])\b")          # **A 官方一手**


def _section_body(text: str, match: re.Match) -> str:
    end = text.find("\n## ", match.end())
    return text[match.end(): end if end > 0 else len(text)]


def extract_report(rel: str, text: str) -> dict:
    """解析单份报告的来源章节 → {heading, entries[], graded}。"""
    ms = list(SECTION_RE.finditer(text))
    if not ms:
        return {"report": rel, "heading": "", "entries": [], "graded": False,
                "problems": ["缺来源章节"]}
    sec = ms[-1]
    body = _section_body(text, sec)
    entries: list[dict] = []
    group = ""
    for line in body.splitlines():
        g = GROUP_RE.match(line.strip())
        if g:
            group = line.strip()[:24]
        if "http" not in line:
            continue
        url = URL_RE.search(line)
        year = YEAR_RE.search(line)
        entries.append({
            "text": line.strip()[:200],
            "url": url.group(0) if url else "",
            "year": year.group(0) if year else "",
            "group": group,
        })
    problems: list[str] = []
    if not entries:
        problems.append("来源章节无 URL 条目")
    no_year = sum(1 for e in entries if not e["year"])
    if no_year:
        problems.append(f"{no_year} 条 URL 条目缺时点年份")
    graded = bool(GRADE_RE.search(body)) or bool(GRADE_RE.search(text))
    if not graded:
        problems.append("未声明来源分级")
    return {"report": rel, "heading": sec.group(0).strip(), "entries": entries,
            "graded": graded, "problems": problems}


def collect() -> list[dict]:
    out: list[dict] = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        for md in sorted(reports.glob("*.md")):
            rel = md.relative_to(ROOT).as_posix()
            out.append(extract_report(rel, md.read_text(encoding="utf-8", errors="replace")))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="来源条目 schema 化与格式校验")
    ap.add_argument("--check", action="store_true", help="不写文件")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    reports = collect()
    blocking = [r for r in reports if "缺来源章节" in r["problems"]]
    warnings = [r for r in reports if r["problems"] and "缺来源章节" not in r["problems"]]
    total_entries = sum(len(r.get("entries", [])) for r in reports)

    if args.json:
        print(json.dumps({"reports": reports, "total_entries": total_entries},
                         ensure_ascii=False, indent=2))
    else:
        print(f"来源 schema：{len(reports)} 份报告，{total_entries} 条 URL 条目；"
              f"阻断 {len(blocking)} 份，告警 {len(warnings)} 份")
        for r in blocking:
            print(f"  [阻断] {r['report']}：{'; '.join(r['problems'])}")
        for r in warnings:
            print(f"  [告警] {r['report']}：{'; '.join(r['problems'])}")
        if not args.check and not args.json:
            out = ROOT / "engine" / "report-audits" / "audit" / "source-index.json"
            atomic_write(out, json.dumps(
                {"version": 1, "total_entries": total_entries, "reports": reports},
                ensure_ascii=False, indent=2))
            print(f"已写入：{out.relative_to(ROOT)}")

    if blocking:
        return 1
    if warnings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
