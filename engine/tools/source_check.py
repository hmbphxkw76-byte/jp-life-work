#!/usr/bin/env python3
"""source_check.py — 来源条目 schema 化与格式校验（P1-2，n25 升级）。

把各报告「参考来源清单 / 来源」章节的条目解析为**机读六元组**
（来源文本 / 时点年份 / URL / 分级分组 / 转述层级 / 独立性），产出 `source-index.json`，
并校验来源格式约定：

- E1：报告存在来源章节（P1，阻断）；
- E2：来源章节含 URL 条目（P2，告警；00 决策枢纽等引用型报告可空）；
- E3：URL 条目附 4 位年份（时点）（P2，告警）；
- E4：报告声明来源分级（分级 / 官方一手 / 权威 / 媒体）（P2，告警）；
- E5：来源条目字段完整率（url + 时点 + 分级分组三项齐全）（P2，告警）；
- E6：来源质量字段（转述层级 / 独立性）缺失或判为「不明」（P2，告警，n21）；
- E7：时点年份合理性（西历须落在 1990–2030，P2，告警，P0-1 修复后新增）；
- E8：来源页面语言（中文页建议回溯日文原文，P2，告警，P1-5）；
- E9：来源分组纳入受控词表（P2，告警，P1-4）。

来源分组 / 独立性 / 权威等级 / 语言判定统一复用 ``source_normalize``
（受控词表 ``GROUP_VOCAB`` 单一事实源），不再各报告自由文本直出。

归一化规则集中在本模块引用的 ``source_normalize``（单一事实源），
其他工具复用该模块，不再各写一套。

输出：``engine/report-audits/audit/source-index.json``（schema 化索引；
n25 起为**入库受控产物**，含每份报告内容指纹，可回溯来源条目对应的报告版本）。

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
from audit_registry import content_fingerprint  # noqa: E402
from source_normalize import (  # noqa: E402
    YEAR_MAX,
    YEAR_MIN,
    authority_grade,
    classify_independence,
    detect_language,
    extract_year,
    normalize_group,
    normalize_url,
    year_is_plausible,
)

SECTION_RE = re.compile(r"^##\s+.*(?:参考来源|来源|引用)", re.M)
URL_RE = re.compile(r"https?://[^\s)\]]+")
# 时点：西历 4 位年，或日本年号（令和/平成/昭和 N 年）——抽取交归一化模块
# 明确的核验/改定标记（机构入口页无刊行日的，以此记录核验时点）
MARKER_RE = re.compile(r"核对|改定|换版|最終更新|最终更新")
GRADE_RE = re.compile(r"分级|官方一手|权威|媒体|A 级|B 级|C 级")
GROUP_RE = re.compile(r"^(?:###\s*)?[①②③④⑤]|"   # ① 日本政府官方一手
                      r"^\*\*([ABC])\b|"           # **A 官方一手**
                      r"^\*\*[^*]{2,120}\*\*[：:]?|"  # **官方一手（…）**（冒号可选）
                      r"^###\s+\S")                 # ### 官方一手
# 来源质量初判（n21，信源批评四问的机读化；仅为初判，人工可覆盖）
RELAY_RE = re.compile(r"转引|转载|转述|引自|译自")
NONIND_RE = re.compile(r"门户|挂牌|中介|媒体|转载|转引|转述|聚合")
IND_RE = re.compile(r"官方|政府|省厅|委员会|行业|协会|学会|研究|机构|团体")


def infer_relay_level(text: str) -> str:
    """转述层级初判：含转引 / 转载等标记 → 2，否则 1（一手）。"""
    return "2" if RELAY_RE.search(text or "") else "1"


def infer_independence(text: str) -> str:
    """独立性初判：门户 / 媒体 / 聚合 → 非独立；官方 / 行业机构 → 独立；其余不明。"""
    s = text or ""
    if NONIND_RE.search(s):
        return "非独立"
    if IND_RE.search(s):
        return "独立"
    return "不明"

INDEX_PATH = ROOT / "engine" / "report-audits" / "audit" / "source-index.json"


def _section_body(text: str, match: re.Match) -> str:
    end = text.find("\n## ", match.end())
    return text[match.end(): end if end > 0 else len(text)]


def extract_report(rel: str, text: str) -> dict:
    """解析单份报告的来源章节 → {heading, entries[], graded, field_completeness}。"""
    ms = list(SECTION_RE.finditer(text))
    if not ms:
        return {"report": rel, "heading": "", "entries": [], "graded": False,
                "field_completeness": 0.0, "problems": ["缺来源章节"]}
    sec = ms[-1]
    body = _section_body(text, sec)
    entries: list[dict] = []
    group = ""
    for line in body.splitlines():
        g = GROUP_RE.match(line.strip())
        if g:
            group = line.strip()
        if "http" not in line:
            continue
        url = URL_RE.search(line)
        url_s = normalize_url(url.group(0)) if url else ""
        year = extract_year(line)
        marker = MARKER_RE.search(line)
        canon = normalize_group(group)
        entries.append({
            "text": line.strip()[:200],
            "url": url_s,
            "year": year,
            "marker": marker.group(0) if marker else "",
            "group": group,
            "group_canonical": canon,
            "authority_grade": authority_grade(canon),
            "language": detect_language(url_s),
            "relay_level": infer_relay_level(group + " " + line),
            "independence": classify_independence(line, url_s, group),
        })
    problems: list[str] = []
    if not entries:
        problems.append("来源章节无 URL 条目")
    no_year = sum(1 for e in entries if not e["year"] and not e["marker"])
    if no_year:
        problems.append(f"{no_year} 条 URL 条目缺时点年份")
    complete = sum(1 for e in entries
                   if e["url"] and (e["year"] or e["marker"]) and e["group"])
    rate = (complete / len(entries)) if entries else 1.0
    if entries and complete < len(entries):
        problems.append(f"来源条目字段完整率 {rate:.0%}（{complete}/{len(entries)}）")
    unknown_ind = sum(1 for e in entries if e["independence"] == "不明")
    if unknown_ind:
        problems.append(f"{unknown_ind} 条来源条目独立性判为「不明」（待人工确认）")
    bad_year = sum(1 for e in entries if e["year"] and not year_is_plausible(e["year"]))
    if bad_year:
        problems.append(f"{bad_year} 条来源条目时点年份异常（超出 {YEAR_MIN}-{YEAR_MAX}，疑似 URL 数字误判）")
    zh = sum(1 for e in entries if e["language"] == "zh")
    if zh:
        problems.append(f"{zh} 条来源为中文页面（建议回溯日文原文）")
    no_group = sum(1 for e in entries if not e["group_canonical"])
    if no_group:
        problems.append(f"{no_group} 条来源分组未纳入受控词表（待归一）")
    graded = bool(GRADE_RE.search(body)) or bool(GRADE_RE.search(text))
    if not graded:
        problems.append("未声明来源分级")
    return {"report": rel, "heading": sec.group(0).strip(), "entries": entries,
            "graded": graded, "field_completeness": round(rate, 4),
            "problems": problems}


def collect() -> list[dict]:
    out: list[dict] = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        for md in sorted(reports.glob("*.md")):
            rel = md.relative_to(ROOT).as_posix()
            rec = extract_report(rel, md.read_text(encoding="utf-8", errors="replace"))
            # 与报告内容指纹关联：来源条目可回溯到生成它的报告版本（n25）
            try:
                rec["fingerprint"] = content_fingerprint(md)
            except Exception:
                rec["fingerprint"] = ""
            out.append(rec)
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
        print(json.dumps({"version": 2, "reports": reports, "total_entries": total_entries},
                         ensure_ascii=False, indent=2))
    else:
        print(f"来源 schema：{len(reports)} 份报告，{total_entries} 条 URL 条目；"
              f"阻断 {len(blocking)} 份，告警 {len(warnings)} 份")
        for r in blocking:
            print(f"  [阻断] {r['report']}：{'; '.join(r['problems'])}")
        for r in warnings:
            print(f"  [告警] {r['report']}：{'; '.join(r['problems'])}")
        if not args.check and not args.json:
            atomic_write(INDEX_PATH, json.dumps(
                {"version": 2, "total_entries": total_entries, "reports": reports},
                ensure_ascii=False, indent=2))
            print(f"已写入：{INDEX_PATH.relative_to(ROOT)}")

    if blocking:
        return 1
    if warnings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
