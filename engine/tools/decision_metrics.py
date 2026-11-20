#!/usr/bin/env python3
"""decision_metrics.py — 五问 / 缺失决策度量（P1-6）。

从 ``00-decision-hub`` 的结构化登记册与决策日志计算可跨月对比的决策指标：

- 指标收敛率：五问指标状态表中「已收敛」占比；
- 五问判定率：五问判定中「是 / 否」（非待定）占比；
- 缺失条目数：指标状态表中缺失标记非「—」的条目；
- 决策变化次数：``decision_log.md`` 状态变化条目数；
- 件套齐备度：决策支持件套状态表中「已建」占比。

历史序列写入 ``engine/report-audits/audit/decision-metrics-history.jsonl``
（每期一条快照），供跨月趋势对比（P2-2 复用同一序列）。

用法：
    python engine/tools/decision_metrics.py            # 计算并写报告（不追加历史）
    python engine/tools/decision_metrics.py --history  # 追加一条历史快照
    python engine/tools/decision_metrics.py --trend    # 与上一快照对比
    python engine/tools/decision_metrics.py --check    # 仅校验可解析，不写文件

退出码：0=正常；1=结构解析失败（阻断）；2=存在待定 / 缺失（仅告警）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, atomic_write  # noqa: E402

REGISTRY = ROOT / "00-decision-hub" / "data" / "decision_hub_registry.md"
LOG = ROOT / "00-decision-hub" / "data" / "decision_log.md"
OUT_JSON = ROOT / "engine" / "report-audits" / "audit" / "decision-metrics.json"
OUT_MD = ROOT / "engine" / "report-audits" / "audit" / "decision-metrics.md"
HISTORY = ROOT / "engine" / "report-audits" / "audit" / "decision-metrics-history.jsonl"

ROW_RE = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|(.+)\|\s*$", re.M)
CONVERGED = "已收敛"


def vocab_fingerprint() -> str:
    """词表内容指纹（n26）：读 `vocab_tool.vocab_hash()`；失败返回空串。"""
    try:
        sys.path.insert(0, str(ROOT / "engine" / "vocabulary" / "script"))
        import vocab_tool  # type: ignore
        cfg = vocab_tool.load_config(vocab_tool.DEFAULT_CONFIG)
        return vocab_tool.vocab_hash(cfg)[0]
    except Exception:
        return ""


def _rows(text: str, section_re: re.Pattern, numeric_first: bool = True) -> list[list[str]]:
    """提取指定章节内的 markdown 表格行（单元格列表）。

    ``numeric_first=False`` 用于首列非编号的表格（如件套清单）。
    """
    m = section_re.search(text)
    if not m:
        return []
    body = m.group(1)
    rows: list[list[str]] = []
    seen_header = False
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.match(r"^\|[\s\-|]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or not cells[0]:
            continue
        if not seen_header:
            seen_header = True
            continue
        if numeric_first and not re.fullmatch(r"\d+", cells[0]):
            continue
        rows.append(cells)
    return rows


def collect() -> dict:
    """计算当前决策指标快照。"""
    text = REGISTRY.read_text(encoding="utf-8", errors="replace")

    ind_rows = _rows(text, re.compile(r"##\s*一、五问指标状态表(.*?)(?=\n##\s*|\Z)", re.DOTALL))
    ind_total = len(ind_rows)
    converged = sum(1 for r in ind_rows if len(r) >= 6 and r[5] == CONVERGED)
    gaps = sum(1 for r in ind_rows if len(r) >= 7 and r[6] not in ("—", "-", ""))

    judge_rows = _rows(text, re.compile(r"###\s*4\.1[^\n]*\n(.*?)(?=\n#{2,3}\s*|\Z)", re.DOTALL))
    judge_total = len(judge_rows)
    decided = sum(1 for r in judge_rows if len(r) >= 3 and r[2] in ("是", "否"))

    kit_rows = _rows(text, re.compile(r"###\s*4\.2[^\n]*\n(.*?)(?=\n#{2,3}\s*|\Z)", re.DOTALL),
                     numeric_first=False)
    kit_total = len(kit_rows)
    kit_ready = sum(1 for r in kit_rows if len(r) >= 3 and "已建" in r[2])

    log_n = len(ROW_RE.findall(LOG.read_text(encoding="utf-8"))) if LOG.is_file() else 0

    return {
        "updated": datetime.now(UTC).isoformat(timespec="seconds"),
        "period": date.today().isoformat()[:7],
        "indicator_total": ind_total,
        "indicator_converged": converged,
        "indicator_convergence_rate": round(converged / ind_total, 4) if ind_total else 0.0,
        "gap_entries": gaps,
        "question_total": judge_total,
        "question_decided": decided,
        "question_decision_rate": round(decided / judge_total, 4) if judge_total else 0.0,
        "kit_total": kit_total,
        "kit_ready": kit_ready,
        "kit_readiness_rate": round(kit_ready / kit_total, 4) if kit_total else 0.0,
        "decision_log_entries": log_n,
        "vocab_hash": vocab_fingerprint(),
    }


def _history() -> list[dict]:
    if not HISTORY.is_file():
        return []
    out = []
    for line in HISTORY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def append_history(snap: dict) -> None:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snap, ensure_ascii=False) + "\n")


def trend(snap: dict) -> dict:
    """与上一条历史快照对比，返回关键指标增量。"""
    hist = _history()
    if not hist:
        return {"available": False, "reason": "无历史快照"}
    prev = hist[-1]
    keys = ("indicator_converged", "gap_entries", "question_decided",
            "kit_ready", "decision_log_entries")
    return {"available": True, "prev_period": prev.get("period"),
            "delta": {k: snap.get(k, 0) - prev.get(k, 0) for k in keys}}


def render_md(snap: dict, tr: dict | None = None) -> str:
    lines = [
        "# 五问 / 缺失决策度量",
        "",
        "> 由 `engine/tools/decision_metrics.py` 生成（P1-6）。",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        f"| 指标收敛率 | {snap['indicator_convergence_rate']:.0%}"
        f"（{snap['indicator_converged']}/{snap['indicator_total']}） |",
        f"| 五问判定率 | {snap['question_decision_rate']:.0%}"
        f"（{snap['question_decided']}/{snap['question_total']}） |",
        f"| 缺失条目数 | {snap['gap_entries']} |",
        f"| 件套齐备度 | {snap['kit_readiness_rate']:.0%}"
        f"（{snap['kit_ready']}/{snap['kit_total']}） |",
        f"| 决策变化次数 | {snap['decision_log_entries']} |",
        "",
    ]
    if tr and tr.get("available"):
        lines += ["## 跨月变化", "",
                  f"对比上期（{tr['prev_period']}）：" + "；".join(
                      f"{k} {v:+d}" for k, v in tr["delta"].items()) + "。", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="五问 / 缺失决策度量")
    ap.add_argument("--history", action="store_true", help="追加历史快照")
    ap.add_argument("--trend", action="store_true", help="与上一快照对比")
    ap.add_argument("--check", action="store_true", help="仅校验可解析，不写文件")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        snap = collect()
    except FileNotFoundError as e:
        print(f"[阻断] 决策登记册缺失：{e}", file=sys.stderr)
        return 1

    tr = trend(snap) if args.trend else None
    if args.json:
        print(json.dumps({"metrics": snap, "trend": tr}, ensure_ascii=False, indent=2))
    else:
        print(f"决策度量：指标收敛率 {snap['indicator_convergence_rate']:.0%}、"
              f"五问判定率 {snap['question_decision_rate']:.0%}、"
              f"缺失 {snap['gap_entries']} 条、决策变化 {snap['decision_log_entries']} 次")
        if tr and tr.get("available"):
            print(f"  跨月（对比 {tr['prev_period']}）：" +
                  "；".join(f"{k} {v:+d}" for k, v in tr["delta"].items()))

    if not args.check and not args.json:
        atomic_write(OUT_JSON, json.dumps({"metrics": snap, "trend": tr},
                                         ensure_ascii=False, indent=2))
        atomic_write(OUT_MD, render_md(snap, tr))
        if args.history:
            append_history(snap)
        print(f"已写入：{OUT_JSON.relative_to(ROOT)}、{OUT_MD.relative_to(ROOT)}"
              + ("（含历史快照）" if args.history else ""))

    if snap["indicator_total"] == 0 or snap["question_total"] == 0:
        return 1
    if snap["gap_entries"] or snap["question_decided"] < snap["question_total"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
