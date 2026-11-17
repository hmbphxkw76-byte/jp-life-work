"""定期合规抽检（AuditGuard 体系）。

依据 docs/审计报告标准化管理体系.md 第七节：
- 分层抽样：按主题分层，每主题至少 1 份，且 ≥ 报告总数的 20%（不足 5 份时全检）；
  同主题多期时按月份轮换，保证 12 个月内每主题至少被抽中 1 次。
- 对抽中报告执行多层级校验（复用 audit_check）+ 审计状态一致性校验。
- 验收门槛：结构合规率 = 100%、要素完整率 ≥ 95%、状态一致率 = 100%、
  抽检合格率 ≥ 95%、P0/P1 = 0。

用法：
    python audit_sampling.py --apply [--period YYYY-MM]   # 执行抽检并写报告（命中 P0/P1 自动置 stale）
    python audit_sampling.py --report [--period YYYY-MM]  # 输出到 stdout（只读，不处置）

退出码：0 = 达到门槛；1 = 未达门槛（P0/P1 或合格率不足）；2 = 仅 P2。
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, link_prefix, md_table  # noqa: E402
from audit_check import check_report, iq_findings_by_path, l5_status, rel as rel_path  # noqa: E402
from audit_registry import AUDIT_DIR, audit_state, discover  # noqa: E402
import compliance_check  # noqa: E402

SAMPLING_DIR = AUDIT_DIR / "sampling"
PENDING_P2 = AUDIT_DIR / "pending-p2.json"

# 验收门槛
TH_STRUCT = 1.00       # 结构合规率
TH_ELEMENT = 0.95      # 要素完整率
TH_CONSIST = 1.00      # 状态一致率
TH_PASS = 0.95         # 抽检合格率
# 说明：四项阈值均为「程序化验收门槛」，直接参与下方 checks 判定，非仅文档口径。


def select_sample(entries: list[dict], period: str) -> list[dict]:
    """分层抽样：每主题至少 1 份；总数 ≥ max(20% × N, min(N, 5))；同主题多期轮换。"""
    by_topic: dict[str, list[dict]] = {}
    for e in entries:
        by_topic.setdefault(e["topic"], []).append(e)
    for v in by_topic.values():
        v.sort(key=lambda x: x["period"])

    n = len(entries)
    target = min(n, max(math.ceil(n * 0.20), min(n, 5)))
    ym = period or datetime.now(timezone.utc).strftime("%Y-%m")
    month_num = int(ym.split("-")[1])

    picked: list[dict] = []
    topics = sorted(by_topic)
    for ti, t in enumerate(topics):
        reps = by_topic[t]
        idx = (month_num + ti) % len(reps)   # 逐期轮换
        picked.append(reps[idx])
    # 补足到目标数量（按主题轮转补齐）
    k = 0
    while len(picked) < target and k < n * 2:
        t = topics[k % len(topics)]
        for e in by_topic[t]:
            if e not in picked:
                picked.append(e)
                break
        k += 1
    picked.sort(key=lambda e: e["report"])
    return picked


def overdue_p2() -> list[dict]:
    """P2 闭环台账中已超过复核期限（review_by < 今日）的条目。"""
    if not PENDING_P2.is_file():
        return []
    try:
        items = json.loads(PENDING_P2.read_text(encoding="utf-8")).get("items", [])
    except json.JSONDecodeError:
        return []
    out = []
    for e in items:
        rb = e.get("review_by", "")
        try:
            overdue = bool(rb) and date.fromisoformat(rb) < date.today()
        except ValueError:
            overdue = True  # 非法期限视为超期
        if overdue:
            out.append(e)
    return out


def run_sample(period: str) -> dict:
    entries = discover()
    sample = select_sample(entries, period)
    iq = iq_findings_by_path()
    l5 = l5_status()
    state = audit_state()
    results = []
    for e in sample:
        rel = e["report"]
        md = ROOT / rel
        html = md.with_suffix(".html")
        res = check_report(rel, md, html, e["type_id"], iq, l5)
        # 状态一致性（双向）：audited ⟺ 标识存在
        st = state.get(rel, {})
        state_label = st.get("state") or st.get("audit_state") or "registered"
        has_badge = "**已审计**" in md.read_text(encoding="utf-8", errors="replace")
        status_ok = (state_label == "audited") == has_badge
        results.append({
            "report": rel, "topic": e["topic"], "period": e["period"],
            "passed": res.passed, "layers": res.layers,
            "severity": res.severity_counts, "status_ok": status_ok,
            "findings": [f for f in res.findings if f.severity in ("P0", "P1")],
        })

    total = len(results)
    struct_ok = sum(1 for r in results if r["layers"].get("L1") == "pass")
    elem_ok = sum(1 for r in results if r["layers"].get("L2") == "pass")
    consist_ok = sum(1 for r in results if r["status_ok"])
    passed = sum(1 for r in results if r["passed"] and r["status_ok"])
    p0 = sum(r["severity"]["P0"] for r in results)
    p1 = sum(r["severity"]["P1"] for r in results)
    p2 = sum(r["severity"]["P2"] for r in results)
    rate = (passed / total) if total else 1.0
    # L5 pending 计入「未完成核验数」并公示（不强制阻断）
    l5_pending = sum(1 for r in results if r["layers"].get("L5") == "pending")
    l5_pending_total = sum(1 for e in entries if not l5.get(e["report"], False))

    checks = {
        "struct_100": (struct_ok / total >= TH_STRUCT) if total else True,
        "element_95": (elem_ok / total >= TH_ELEMENT) if total else True,
        "consistent_100": (consist_ok / total >= TH_CONSIST) if total else True,
        "pass_95": rate >= TH_PASS,
        "p0p1_zero": (p0 + p1) == 0,
    }
    return {
        "period": period, "total_reports": len(entries), "sample_size": total,
        "struct_ok": struct_ok, "elem_ok": elem_ok, "consist_ok": consist_ok,
        "passed": passed, "rate": rate, "p0": p0, "p1": p1, "p2": p2,
        "l5_pending": l5_pending, "l5_pending_total": l5_pending_total,
        "unfinished_verification": l5_pending,
        "overdue_p2_count": len(overdue_p2()),
        "checks": checks, "ok": all(checks.values()),
        "results": results,
    }


def write_report(payload: dict) -> list[Path]:
    SAMPLING_DIR.mkdir(parents=True, exist_ok=True)
    md_path = SAMPLING_DIR / f"sampling-{payload['period']}.md"
    prefix = link_prefix(md_path)
    rows = [["报告", "主题", "期间", "L1", "L2", "L3", "L4", "状态一致", "结论"]]
    for r in payload["results"]:
        ly = r["layers"]
        rows.append([f"[{r['report']}]({prefix}{r['report']})", r["topic"], r["period"],
                     ly.get("L1", "—"), ly.get("L2", "—"), ly.get("L3", "—"), ly.get("L4", "—"),
                     "✓" if r["status_ok"] else "✗",
                     "通过" if (r["passed"] and r["status_ok"]) else "不通过"])
    chk_rows = [[k, "通过" if v else "未通过"] for k, v in payload["checks"].items()]
    md = "\n".join(
        [
            f"# 报告合规抽检报告（{payload['period']}）",
            "",
            f"> 抽检日期：{payload['period']}　|　覆盖：{payload['sample_size']}/{payload['total_reports']} 份"
            f"（分层抽样，每主题至少 1 份）",
            f"> 抽检合格率：{payload['passed']}/{payload['sample_size']}（{payload['rate']:.0%}）　|　"
            f"P0 {payload['p0']} / P1 {payload['p1']} / P2 {payload['p2']}",
            f"> 未完成核验数（L5 pending）：样本 {payload['l5_pending']}/{payload['sample_size']}；"
            f"全库 {payload['l5_pending_total']}/{payload['total_reports']}（公示项，不强制阻断）",
            f"> 依据《审计报告标准化管理体系》第七节验收门槛",
            "",
            "## 验收门槛判定",
            "",
            md_table([["校验项", "结果"]] + chk_rows),
            "",
            "## 抽检明细",
            "",
            md_table(rows),
            "",
            f"**验收结论：{'达标 ✅' if payload['ok'] else '未达标 ⚠️（见未通过校验项）'}**",
            "",
        ]
    )
    p = SAMPLING_DIR / f"sampling-{payload['period']}.md"
    p.write_text(md, encoding="utf-8")
    pj = SAMPLING_DIR / f"sampling-{payload['period']}.json"
    pj.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return [p, pj]


def mark_sampling_failures(payload: dict) -> list[str]:
    """抽检命中 P0/P1：把对应已审计报告置 stale（G→F 反馈链路，规范七）。

    复用 audit_pipeline 的状态机（事件 sampling_fail），不新写判定；返回被处置的
    报告路径列表。仅由 --apply 调用，--report 为只读预演不处置。
    """
    failed = sorted({r["report"] for r in payload["results"]
                     if r["severity"]["P0"] or r["severity"]["P1"]})
    if not failed:
        return []
    try:
        from audit_pipeline import mark_sampling_failures as _mark
    except ImportError:  # noqa: BLE001
        print("[W] 无法导入 audit_pipeline，跳过抽检失效处置")
        return []
    n = _mark(failed)
    print(f"抽检不合格处置：{n} 份报告已置 stale（须重走 submit → 初审 → 复核 → 终审）")
    return failed


def main() -> int:
    ap = argparse.ArgumentParser(description="报告合规抽检")
    ap.add_argument("--apply", action="store_true", help="执行抽检并写报告")
    ap.add_argument("--report", action="store_true", help="输出到 stdout")
    ap.add_argument("--period", help="抽检期间（YYYY-MM，缺省当前月）")
    args = ap.parse_args()

    period = args.period or date.today().isoformat()[:7]
    if not re.fullmatch(r"\d{4}-\d{2}", period):
        print(f"[ERROR] --period 须为 YYYY-MM：{period}", file=sys.stderr)
        return 2
    payload = run_sample(period)
    if args.report:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        # G→F 反馈链路：命中 P0/P1 的已审计报告自动置 stale，标识由工作流 badge --sync 撤销。
        mark_sampling_failures(payload)
        paths = write_report(payload)
        print(f"抽检完成：{payload['sample_size']}/{payload['total_reports']} 份，"
              f"合格率 {payload['rate']:.0%}；P0 {payload['p0']} / P1 {payload['p1']} / P2 {payload['p2']}")
        print(f"  未完成核验数（L5 pending）：样本 {payload['l5_pending']}/{payload['sample_size']}；"
              f"全库 {payload['l5_pending_total']}/{payload['total_reports']}（公示项，不阻断）")
        overdue = overdue_p2()
        if overdue:
            print(f"[W] P2 超期未闭环：{len(overdue)} 项（见 {PENDING_P2.relative_to(ROOT)}）")
        print("  报告已写入：" + ", ".join(rel_path(p) for p in paths))
    if not payload["ok"]:
        return 1
    if payload["p2"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
