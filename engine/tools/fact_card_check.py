"""事实卡片校验：五字段完整性 + 指针可解析 + 跨报告事实重复率。

对应 `engine/report_templates/fact-card-standard.md`：
- 每张事实卡片必含「值 / 统计口径 / 数据时点 / 来源 URL / 版本号」五字段；
- 全库 `[@FC-NNN]` 指针必须能解析到唯一卡片；
- 跨报告事实重复率（复用 info_quality_check.fact_duplication，单一事实源）。

用法：
    python engine/tools/fact_card_check.py           # 控制台报告
    python engine/tools/fact_card_check.py --json    # 机器可读
    python engine/tools/fact_card_check.py --write   # 写入 engine/report-audits/audit/fact-card-report.md

退出码：0 = 通过；1 = 存在 P0/P1；2 = 仅 P2。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import info_quality_check as iqc  # noqa: E402
from _common import ROOT, iter_business_dirs  # noqa: E402

CARD_PATH = ROOT / "00-decision-hub" / "data" / "fact_cards.md"
REPORT_PATH = ROOT / "engine" / "report-audits" / "audit" / "fact-card-report.md"
FIELDS = ("值", "统计口径", "数据时点", "来源 URL", "版本号")
CARD_RE = re.compile(r"^\|\s*(FC-\d{3})\s*\|", re.M)
POINTER_RE = re.compile(r"\[@(FC-\d{3})\]")
# corroboration 来源数（n22）：可选第 7 列，或行内「corroboration: N」/「互证 N」
CORROB_RE = re.compile(r"corroboration\s*[:：]?\s*(\d+)|互证\s*[:：]?\s*(\d+)")


def parse_cards() -> dict[str, dict]:
    """解析事实卡片表 -> {id: {fields...}}。"""
    cards: dict[str, dict] = {}
    if not CARD_PATH.exists():
        return cards
    lines = CARD_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    for ln in lines:
        m = CARD_RE.match(ln.strip())
        if not m:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        cards[m.group(1)] = {"值": cells[1], "统计口径": cells[2], "数据时点": cells[3],
                             "来源 URL": cells[4], "版本号": cells[5], "raw": ln.strip()}
        # n22：corroboration 来源数（可选第 7 列或行内标注）
        corrob = cells[6].strip() if len(cells) > 6 else ""
        if not corrob:
            cm = CORROB_RE.search(ln)
            corrob = (cm.group(1) or cm.group(2)) if cm else ""
        cards[m.group(1)]["corroboration"] = corrob
    return cards


def collect_pointers() -> dict[str, list[str]]:
    """扫描全库 md 的 [@FC-NNN] 指针 -> {id: [位置...]}。"""
    found: dict[str, list[str]] = {}
    for b in iter_business_dirs():
        for md in b.path.rglob("*.md"):
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for pid in POINTER_RE.findall(text):
                found.setdefault(pid, []).append(str(md.relative_to(ROOT)).replace("\\", "/"))
    return found


def check_fields(cards: dict[str, dict]) -> list[dict]:
    """五字段完整性检查。"""
    issues = []
    for cid, c in cards.items():
        missing = [f for f in FIELDS if not c.get(f) or c.get(f) in ("—", "-", "")]
        # 来源 URL 允许「无在线来源」（估算类），但必须显式标注
        if "来源 URL" in missing and ("无在线来源" in c.get("来源 URL", "") or "无在线来源" in c.get("raw", "")):
            missing.remove("来源 URL")
        if missing:
            issues.append({"id": cid, "level": "P1", "issue": "五字段缺失", "detail": "、".join(missing)})
    return issues


def check_corroboration(cards: dict[str, dict]) -> list[dict]:
    """n22：corroboration 来源数登记与多源互证提示（P2）。"""
    issues = []
    for cid, c in sorted(cards.items()):
        v = (c.get("corroboration") or "").strip()
        if not v:
            issues.append({"id": cid, "level": "P2", "issue": "corroboration 未标注",
                           "detail": "事实卡片未登记 corroboration 来源数（n22）"})
        elif v.isdigit() and int(v) < 2:
            issues.append({"id": cid, "level": "P2", "issue": "corroboration 来源数 < 2",
                           "detail": f"当前 {v}，建议多源互证"})
    return issues


def check_pointers(cards: dict[str, dict], pointers: dict[str, list[str]]) -> list[dict]:
    """指针可解析性检查。"""
    issues = []
    for pid, locs in sorted(pointers.items()):
        if pid not in cards:
            issues.append({"id": pid, "level": "P1", "issue": "指针失效",
                           "detail": f"引用位置 {len(locs)} 处，但卡片不存在：{', '.join(locs[:3])}"})
    return issues


def check_orphans(cards: dict[str, dict], pointers: dict[str, list[str]]) -> list[dict]:
    """卡片未被任何指针引用（提示，P2）。"""
    return [{"id": cid, "level": "P2", "issue": "卡片未被引用",
             "detail": "无 [@FC-NNN] 指针引用该卡片"} for cid in sorted(cards) if cid not in pointers]


def run() -> tuple[list[dict], dict]:
    cards = parse_cards()
    pointers = collect_pointers()
    issues = (check_fields(cards) + check_corroboration(cards)
              + check_pointers(cards, pointers) + check_orphans(cards, pointers))

    units = iqc.scan_topics()
    fact_rate, fact_details = iqc.fact_duplication(units)
    if fact_rate > iqc.THRESH_FACT_DUP:
        issues.append({"id": "全库", "level": "P2", "issue": "跨报告事实重复率",
                       "detail": f"{fact_rate:.1%} 超过门槛 {iqc.THRESH_FACT_DUP:.0%}（{len(fact_details)} 组）"})

    summary = {"cards": len(cards), "pointers": len(pointers),
               "fact_dup_ratio": fact_rate, "issues": issues}
    return issues, summary


def render_md(issues: list[dict], summary: dict) -> str:
    rows = [["ID", "级别", "问题", "详情"]]
    for i in issues:
        rows.append([i["id"], i["level"], i["issue"], i["detail"]])
    lines = [
        "# 事实卡片校验报告",
        "",
        f"> 卡片 {summary['cards']} 张　|　指针 {summary['pointers']} 个　|　"
        f"跨报告事实重复率 {summary['fact_dup_ratio']:.1%}（门槛 {iqc.THRESH_FACT_DUP:.0%}）",
        "",
        "## 问题明细",
        "",
    ]
    if len(rows) == 1:
        lines.append("（无问题）")
    else:
        lines.append("| " + " | ".join(rows[0]) + " |")
        lines.append("|" + "---|" * len(rows[0]))
        for r in rows[1:]:
            lines.append("| " + " | ".join(r) + " |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="事实卡片校验")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    issues, summary = run()
    p0p1 = [i for i in issues if i["level"] in ("P0", "P1")]
    p2 = [i for i in issues if i["level"] == "P2"]

    if args.json:
        print(json.dumps({"summary": summary, "issues": issues}, ensure_ascii=False, indent=2))
    else:
        print(f"事实卡片校验：{summary['cards']} 张卡片 / {summary['pointers']} 个指针")
        print(f"  跨报告事实重复率 {summary['fact_dup_ratio']:.1%}（门槛 {iqc.THRESH_FACT_DUP:.0%}）")
        print(f"  问题：P0/P1 {len(p0p1)} / P2 {len(p2)}")
        for i in issues:
            print(f"  [{i['level']}] {i['id']} {i['issue']}：{i['detail']}")

    if args.write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(render_md(issues, summary), encoding="utf-8")
        print(f"报告已写入：{REPORT_PATH.relative_to(ROOT)}")

    if p0p1:
        return 1
    if p2:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
