#!/usr/bin/env python3
"""counterexample_scan.py — 反例 / 绝对化论断扫描（P2-1）。

对每份报告扫描**可证伪的反例候选**：绝对化措辞、以偏概全 / 过度推断、
无来源断言。产出机读清单，供人工补充反例或限定语（「反例可证伪」）。

复用既有的绝对化判定内核（``audit_check.absolute_hits``，已排除否定 / 引述语境），
不新造规则：

- ``ABS``：绝对化措辞命中（绝对 / 必然 / 一定 / 所有 / 全部 / 100% 等）；
- ``GEN``：以偏概全 / 过度推断标记（以偏概全 / 过度推断 / 一概而论 / 都 / 全部）；
- ``NOSRC``：结论式断言句但所在段落无来源标记（``[Source:`` / ``http``）；
- ``单源``：含关键数字的段落仅一个来源标记且无 corroboration / 单源标注（n23）。
  n23 收紧：仅当该来源标记指向**外部一手来源**时才判定；来源括注为报告内部指针
  （本报告 / 本主题登记册 / 主题登记册 / business-config / 基线报告 / 来源清单）的段落不参与，
  疑问句与「（建议）」类操作建议句亦不参与。

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
# 裁定清单：命中 (report, sentence) 即不再计为候选（新增候选默认不豁免）
ADJ = ROOT / "engine" / "config" / "counterexample-adjudications.json"

GEN_RE = re.compile(r"以偏概全|过度推断|一概而论|全部|所有|无一例外")
SENTENCE_RE = re.compile(r"[^。！？\n]{4,80}[。！？]")
SRC_RE = re.compile(r"\[Source:|https?://|来源[：:]")
SINGLE_LABEL_RE = re.compile(r"单源|corroboration|互证|多源")
NUM_RE = re.compile(r"\d")
# 结论性措辞：仅对「关键结论」类句子判定单源，避免普通来源句误报
CLAIM_RE = re.compile(r"结论|判断|表明|意味着|说明|证实|显示|缺口|不足|超过|达到|风险|预计")
# 内部指针：来源括注指向报告自身章节 / 登记册 / 配置，不构成外部来源
SRC_TAIL_RE = re.compile(r"来源[：:]\s*([^）)\n]*)")
INTERNAL_TOKENS = ("本报告", "本主题登记册", "本主题", "主题登记册", "business-config",
                   "基线报告", "来源清单")
SECTION_PTR_RE = re.compile(r"第?[一二三四五六七八九十百\d]+节|详见|见来源清单|官方原文回溯")
GENERIC_WORDS = ("建议章", "推断", "事实", "建议", "结论", "实证", "说明", "解读", "报告期", "依据")
NUM_CHARS_RE = re.compile(r"[第一二三四五六七八九十百千\d]")
PUNCT_CHARS = " 　/·、，,。（）():：-"
ADVICE_MARK = "（建议）"


def _internal_source_only(para: str) -> bool:
    """段落的所有「来源：」尾注是否均为内部指针（无外部机构信息）。

    仅剔除可识别为报告自身的字样与泛化词；尾部只要残留任何实质名词
    （机构 / 主题 / 模式等），即视为含外部成分，不排除该段。
    """
    tails = SRC_TAIL_RE.findall(para)
    if not tails:
        return False
    for raw in tails:
        s = raw
        for tok in INTERNAL_TOKENS:
            s = s.replace(tok, "")
        s = SECTION_PTR_RE.sub("", s)
        for word in GENERIC_WORDS:
            s = s.replace(word, "")
        s = NUM_CHARS_RE.sub("", s).strip(PUNCT_CHARS)
        if s:
            return False
    return True


def _single_source_sentences(text: str) -> list[str]:
    """段落级单源候选：含数字的结论句，所在段落仅一个【外部】来源标记且无 corroboration 标注。

    n23 收紧：内部指针段落、疑问句、「（建议）」操作建议句不参与。
    """
    out: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        if not NUM_RE.search(para):
            continue
        if len(SRC_RE.findall(para)) != 1:
            continue
        if SINGLE_LABEL_RE.search(para):
            continue
        if _internal_source_only(para):
            continue
        for sent in SENTENCE_RE.findall(para):
            if NUM_RE.search(sent) and CLAIM_RE.search(sent) \
                    and not sent.rstrip().endswith(("？", "?")) \
                    and ADVICE_MARK not in sent:
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


def load_adjudications(path: Path | None = None) -> dict[tuple[str, str], dict]:
    """读取裁定清单：{(report, sentence): {verdict, reason, evidence}}。缺失 / 损坏返回空。"""
    p = path or ADJ
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out: dict[tuple[str, str], dict] = {}
    for e in data.get("adjudications", []):
        if not isinstance(e, dict):
            continue
        key = (e.get("report", ""), e.get("sentence", ""))
        out[key] = {k: e.get(k, "") for k in ("verdict", "reason", "evidence")}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="反例 / 绝对化论断扫描")
    ap.add_argument("--check", action="store_true", help="不写文件")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    adj = load_adjudications()
    rows: list[dict] = []
    n_adj = 0
    for r in scan():
        items, kept_adj = [], []
        for it in r["items"]:
            hit = adj.get((r["report"], it["sentence"]))
            if hit:
                n_adj += 1
                it = dict(it, verdict=hit.get("verdict", ""), reason=hit.get("reason", ""))
                kept_adj.append(it)
            else:
                items.append(it)
        if items or kept_adj:
            rows.append({"report": r["report"], "count": len(items),
                         "adjudicated": len(kept_adj), "items": items})
    total = sum(r["count"] for r in rows)
    if args.json:
        print(json.dumps({"total": total, "adjudicated": n_adj, "reports": rows},
                         ensure_ascii=False, indent=2))
    else:
        print(f"反例扫描：{len(rows)} 份报告，{total} 条待处理（另 {n_adj} 条已裁定）")
        for r in rows:
            print(f"  {r['report']}：{r['count']} 条待处理 / {r['adjudicated']} 条已裁定")
            for it in r["items"][:3]:
                print(f"    [{'/'.join(it['kinds'])}] {it['sentence'][:70]}")
        if not args.check and not args.json:
            atomic_write(OUT, json.dumps({"total": total, "adjudicated": n_adj,
                                        "reports": rows}, ensure_ascii=False, indent=2))
            print(f"已写入：{OUT.relative_to(ROOT)}")
    if total:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
