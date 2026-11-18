#!/usr/bin/env python3
"""l5_meta_check.py — L5 语义复核证据元评估（P1-4）。

对全库已审计报告的 L5 证据做**独立元评估**（不复用抽检结论），产出可机读的
证据质量指标，作为「证据质量门槛」：

- 覆盖率：已审计报告中持有有效 L5 证据的比例（门槛 100%）；
- 合格率：证据通过 ``validate_l5_evidence`` 六项结构校验的比例；
- basis 缺失：no / uncertain 结论缺依据说明的条目数（门槛 0）；
- 依据充分度：basis 平均字数（< 20 字告警）；
- 否决项：verdict=fail 的证据数（提示复核结论为否决的报告）。

输出：``engine/report-audits/audit/l5-meta-report.{json,md}``。

用法：
    python engine/tools/l5_meta_check.py            # 全量元评估
    python engine/tools/l5_meta_check.py --json     # 仅打印 JSON
    python engine/tools/l5_meta_check.py --check    # 不写文件

退出码：0=达标；1=存在覆盖缺口 / 无效证据 / basis 缺失（阻断）；2=仅告警。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, atomic_write  # noqa: E402
from audit_pipeline import (  # noqa: E402
    l5_status_from_ledger,
    load_ledger,
    rebuild_status,
    validate_l5_evidence,
)

OUT_JSON = ROOT / "engine" / "report-audits" / "audit" / "l5-meta-report.json"
OUT_MD = ROOT / "engine" / "report-audits" / "audit" / "l5-meta-report.md"

MIN_BASIS_CHARS = 20


def _latest_evidence(ledger: list[dict], report: str) -> str:
    """取某报告最近一次有效来源的 L5 证据（stage_pass / l5_backfill）。"""
    ev = ""
    for e in ledger:
        if e.get("report") != report or e.get("role") != "reviewer_l2":
            continue
        if e.get("event") in ("stage_pass", "l5_backfill"):
            ev = e.get("evidence", "")
        elif e.get("event") == "stage_fail":
            ev = ""
    return ev


def evaluate() -> dict:
    """对全库已审计报告做 L5 证据元评估。"""
    ledger = load_ledger()
    state = rebuild_status(ledger)
    l5 = l5_status_from_ledger()

    audited = [r for r, v in state.items() if v.get("state") == "audited"]
    per_report: list[dict] = []
    valid = 0
    basis_missing = 0
    basis_chars: list[int] = []
    verdict_fail = 0

    for rep in sorted(audited):
        ev = _latest_evidence(ledger, rep)
        ok, ev_problems = validate_l5_evidence(ev) if ev else (False, ["无 L5 证据"])
        if ok:
            valid += 1
        data = json.loads(ev) if ev else {}
        items = data.get("items", []) if isinstance(data, dict) else []
        for it in items:
            if not isinstance(it, dict):
                continue
            res = str(it.get("result", "")).strip().lower()
            basis = it.get("basis")
            basis = basis if isinstance(basis, str) else ""
            if res in ("no", "uncertain") and not basis.strip():
                basis_missing += 1
            if basis.strip():
                basis_chars.append(len(basis.strip()))
        if isinstance(data, dict) and data.get("verdict") == "fail":
            verdict_fail += 1
        per_report.append({"report": rep, "valid": ok, "problems": ev_problems,
                           "l5_status": l5.get(rep, False)})

    n = len(audited)
    coverage = (valid / n) if n else 1.0
    avg_basis = round(sum(basis_chars) / len(basis_chars), 1) if basis_chars else 0.0
    problems: list[str] = []
    if n == 0:
        problems.append("无已审计报告，无法评估")
    if coverage < 1.0:
        problems.append(f"L5 证据覆盖率 {coverage:.0%}（门槛 100%）")
    if basis_missing:
        problems.append(f"no/uncertain 结论缺 basis {basis_missing} 条（门槛 0）")
    warnings: list[str] = []
    if n and avg_basis < MIN_BASIS_CHARS:
        warnings.append(f"basis 平均字数 {avg_basis} < {MIN_BASIS_CHARS}（依据偏简）")

    return {
        "updated": datetime.now(UTC).isoformat(timespec="seconds"),
        "audited": n,
        "with_valid_evidence": valid,
        "coverage": round(coverage, 4),
        "evidence_valid_rate": round(valid / n, 4) if n else 1.0,
        "basis_missing": basis_missing,
        "avg_basis_chars": avg_basis,
        "verdict_fail": verdict_fail,
        "problems": problems,
        "warnings": warnings,
        "reports": per_report,
    }


def render_md(rep: dict) -> str:
    lines = [
        "# L5 语义复核证据元评估",
        "",
        "> 由 `engine/tools/l5_meta_check.py` 生成（P1-4 证据质量门槛）。",
        "",
        "## 汇总",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        f"| 已审计报告 | {rep['audited']} |",
        f"| 有效 L5 证据 | {rep['with_valid_evidence']} |",
        f"| 覆盖率 | {rep['coverage']:.0%} |",
        f"| 证据合格率 | {rep['evidence_valid_rate']:.0%} |",
        f"| basis 缺失 | {rep['basis_missing']} |",
        f"| basis 平均字数 | {rep['avg_basis_chars']} |",
        f"| verdict=fail | {rep['verdict_fail']} |",
        "",
    ]
    if rep["problems"]:
        lines += ["## 阻断项", ""] + [f"- {p}" for p in rep["problems"]] + [""]
    if rep["warnings"]:
        lines += ["## 告警项", ""] + [f"- {w}" for w in rep["warnings"]] + [""]
    lines += ["## 逐报告", "", "| 报告 | 证据有效 | L5 状态 | 问题 |", "|---|---|---|---|"]
    for r in rep["reports"]:
        lines.append(f"| {r['report']} | {'✓' if r['valid'] else '✗'} | "
                     f"{'✓' if r['l5_status'] else '✗'} | {'；'.join(r['problems']) or '—'} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="L5 语义复核证据元评估")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true", help="不写文件")
    args = ap.parse_args(argv)

    rep = evaluate()
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"L5 元评估：已审计 {rep['audited']} 份，有效证据 {rep['with_valid_evidence']} 份，"
              f"覆盖率 {rep['coverage']:.0%}，basis 缺失 {rep['basis_missing']}，"
              f"verdict=fail {rep['verdict_fail']}")
        for p in rep["problems"]:
            print(f"  [阻断] {p}")
        for w in rep["warnings"]:
            print(f"  [告警] {w}")
        if not args.check:
            atomic_write(OUT_JSON, json.dumps(rep, ensure_ascii=False, indent=2))
            atomic_write(OUT_MD, render_md(rep))
            print(f"已写入：{OUT_JSON.relative_to(ROOT)}、{OUT_MD.relative_to(ROOT)}")

    if rep["problems"]:
        return 1
    if rep["warnings"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
