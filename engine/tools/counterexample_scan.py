#!/usr/bin/env python3
"""counterexample_scan.py — 反例 / 绝对化论断扫描（P2-1）。

对每份报告扫描**可证伪的反例候选**：绝对化措辞、以偏概全 / 过度推断、
无来源断言。产出机读清单，供人工补充反例或限定语（「反例可证伪」）。

复用既有的绝对化判定内核（``audit_check.absolute_hits``，已排除否定 / 引述语境），
不新造规则：

- ``ABS``：绝对化措辞命中（绝对 / 必然 / 一定 / 所有 / 全部 / 100% 等）；
- ``GEN``：以偏概全 / 过度推断标记（以偏概全 / 过度推断 / 一概而论 / 都 / 全部）；
- ``NOSRC``：结论式断言句但所在段落无来源标记（``[Source:`` / ``http``）；
- ``单源``：含关键数字的段落仅一个来源标记且无 corroboration / 单源标注（n22）。

输出：``engine/report-audits/audit/counterexample-report.json``（不入库）。

用法：
    python engine/tools/counterexample_scan.py            # 扫描并写清单
    python engine/tools/counterexample_scan.py --check    # 不写文件
    python engine/tools/counterexample_scan.py --json

退出码：0=无命中；1=扫描失败；2=存在反例候选（需人工裁定）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, atomic_write, iter_business_dirs  # noqa: E402
from audit_check import absolute_hits  # noqa: E402

OUT = ROOT / "engine" / "report-audits" / "audit" / "counterexample-report.json"

GEN_RE = re.compile(r"以偏概全|过度推断|一概而论|全部|所有|无一例外")
SENTENCE_RE = re.compile(r"[^。！？\n]{4,80}[。！？]")
SRC_RE = re.compile(r"\[Source:|https?://|来源[：:]")
SINGLE_LABEL_RE = re.compile(r"单源|corroboration|互证|多源")
NUM_RE = re.compile(r"\d")
# 结论性措辞：仅对「关键结论」类句子判定单源，避免普通来源句误报
CLAIM_RE = re.compile(r"结论|判断|表明|意味着|说明|证实|显示|缺口|不足|超过|达到|风险|预计")


def _single_source_sentences(text: str) -> list[str]:
    """段落级单源候选：含数字的结论句，所在段落仅一个来源标记且无 corroboration 标注。"""
    out: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        if not NUM_RE.search(para):
            continue
        if len(SRC_RE.findall(para)) != 1:
            continue
        if SINGLE_LABEL_RE.search(para):
            continue
        for sent in SENTENCE_RE.findall(para):
            if NUM_RE.search(sent) and CLAIM_RE.search(sent):
                out.append(sent.strip()[:160])
                break
    return out


def scan_text(text: str) -> list[dict]:
    """扫描单份报告正文 → 反例候选列表。"""
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for sent in SENTENCE_RE.findall(text):
        s = sent.strip()
        if len(s) < 6:
            continue
        kinds: list[str] = []
        hits = absolute_hits(s)
        if hits:
            kinds.append("ABS")
        if GEN_RE.search(s):
            kinds.append("GEN")
        if not SRC_RE.search(s) and ("必然" in s or "一定" in s or "绝对" in s):
            kinds.append("NOSRC")
        if not kinds:
            continue
        key = (kinds[0], s[:40])
        if key in seen:
            continue
        seen.add(key)
        out.append({"sentence": s[:160], "kinds": kinds, "hits": sorted(set(hits))[:5]})
    # n22：单源候选（段落级）
    for s in _single_source_sentences(text):
        key = ("单源", s[:40])
        if key in seen:
            continue
        seen.add(key)
        out.append({"sentence": s, "kinds": ["单源"], "hits": []})
    return out


def scan() -> list[dict]:
    rows: list[dict] = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        for md in sorted(reports.glob("*.md")):
            rel = md.relative_to(ROOT).as_posix()
            items = scan_text(md.read_text(encoding="utf-8", errors="replace"))
            if items:
                rows.append({"report": rel, "count": len(items), "items": items})
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="反例 / 绝对化论断扫描")
    ap.add_argument("--check", action="store_true", help="不写文件")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    rows = scan()
    total = sum(r["count"] for r in rows)
    if args.json:
        print(json.dumps({"total": total, "reports": rows}, ensure_ascii=False, indent=2))
    else:
        print(f"反例扫描：{len(rows)} 份报告，{total} 条候选")
        for r in rows:
            print(f"  {r['report']}：{r['count']} 条")
            for it in r["items"][:3]:
                print(f"    [{'/'.join(it['kinds'])}] {it['sentence'][:70]}")
        if not args.check and not args.json:
            atomic_write(OUT, json.dumps({"total": total, "reports": rows},
                                        ensure_ascii=False, indent=2))
            print(f"已写入：{OUT.relative_to(ROOT)}")
    if total:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
