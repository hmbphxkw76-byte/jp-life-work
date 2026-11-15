"""审计质量管控流程（AuditGuard 体系）。

实现 docs/审计报告标准化管理体系.md 第五节的状态机与全程留痕：

    registered --submit--> pending_initial --初审 pass--> pending_re_review
        ^                        |                          |
        |                     初审 fail                   复核 pass
        |                        v                          v
        |                    rejected <----任意环节 fail---- pending_final
        |                        |                          |
        +----修改后重新 submit---+                    终审 pass
                                                       v
                                                   audited --内容变更（指纹失配）--> stale

留痕文件：
- `audit-ledger.jsonl`：append-only 事件流，哈希链防篡改（`--verify` 重算全链）；
- `audit-status.json`：由台账派生的当前状态（状态 / 审计编号 / 终审时间 / 绑定指纹）。

用法：
    python audit_pipeline.py --init                 # 登记全部报告（幂等）
    python audit_pipeline.py --submit --all         # 全部提交初审
    python audit_pipeline.py --submit --report <相对路径> [--actor <名称>]
    python audit_pipeline.py --review --stage initial|re_review|final --report <路径> \
        --result pass|fail [--actor <名称>] [--note <说明>] [--evidence <JSON>]
    python audit_pipeline.py --status               # 打印状态表
    python audit_pipeline.py --verify               # 校验台账哈希链 + 指纹绑定
    python audit_pipeline.py --sync                 # 对指纹失配的已审计报告写 revoke（→ stale）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT  # noqa: E402
from audit_registry import (  # noqa: E402
    AUDIT_DIR,
    SPEC_VERSION,
    build as build_registry,
    content_fingerprints,
    discover,
)
from audit_check import L5_CHECKLIST  # noqa: E402  （audit_check 不反向导入 audit_pipeline，无循环）

LEDGER = AUDIT_DIR / "audit-ledger.jsonl"
STATUS = AUDIT_DIR / "audit-status.json"

STAGES = ("initial", "re_review", "final")
ROLE_OF_STAGE = {"initial": "reviewer_l1", "re_review": "reviewer_l2", "final": "audit_chair"}
DEFAULT_ACTOR = {"initial": "reviewer_l1", "re_review": "reviewer_l2", "final": "audit_chair"}

# (当前状态, 事件) -> 目标状态
TRANSITIONS = {
    (None, "register"): "registered",
    ("registered", "submit"): "pending_initial",
    ("rejected", "submit"): "pending_initial",
    ("stale", "submit"): "pending_initial",
    ("pending_initial", "stage_pass"): "pending_re_review",
    ("pending_initial", "stage_fail"): "rejected",
    ("pending_re_review", "stage_pass"): "pending_final",
    ("pending_re_review", "stage_fail"): "rejected",
    ("pending_final", "stage_pass"): "audited",
    ("pending_final", "stage_fail"): "rejected",
    ("audited", "revoke"): "stale",
}

STATE_LABEL = {
    "registered": "已登记", "pending_initial": "待初审", "pending_re_review": "待复核",
    "pending_final": "待终审", "audited": "已审计", "rejected": "已驳回", "stale": "审计失效",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ──────────────────────────────────────────────
# L5 语义复核证据校验
# ──────────────────────────────────────────────

def validate_l5_evidence(text: str) -> tuple[bool, list[str]]:
    """校验复核证据 JSON（格式见 src/report_templates/l5-semantic-review.md）。

    返回 (是否有效, 问题列表)。六项缺一不可；no / uncertain 必须给出 basis。
    """
    if not text or not text.strip():
        return False, ["缺少 L5 语义复核证据（--evidence）"]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return False, [f"evidence 不是合法 JSON：{e}"]
    if not isinstance(data, dict):
        return False, ["evidence 顶层须为 JSON 对象"]
    items = data.get("items")
    if not isinstance(items, list) or len(items) != len(L5_CHECKLIST):
        return False, [f"evidence.items 须为 {len(L5_CHECKLIST)} 项，实际 "
                        f"{len(items) if isinstance(items, list) else '非列表'}"]
    problems: list[str] = []
    for i, it in enumerate(items, start=1):
        if not isinstance(it, dict):
            problems.append(f"第 {i} 项不是对象")
            continue
        res = str(it.get("result", "")).strip().lower()
        basis = str(it.get("basis", "")).strip()
        if res not in ("yes", "no", "uncertain"):
            problems.append(f"第 {i} 项 result 非法：{res!r}")
        if res in ("no", "uncertain") and not basis:
            problems.append(f"第 {i} 项 {res} 缺少 basis 说明")
    return (not problems), problems


def l5_status_from_ledger() -> dict[str, bool]:
    """从台账派生各报告 L5 状态：最近一次 re_review 是否有有效证据。"""
    status: dict[str, bool] = {}
    for ev in load_ledger():
        rep = ev.get("report")
        if not rep:
            continue
        if ev.get("event") == "stage_pass" and ev.get("role") == "reviewer_l2":
            ok, _ = validate_l5_evidence(ev.get("evidence", ""))
            status[rep] = ok
        elif ev.get("event") == "stage_fail" and ev.get("role") == "reviewer_l2":
            status[rep] = False
    return status


def _canonical(body: dict) -> str:
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(prev_hash: str, body: dict) -> str:
    return hashlib.sha256((prev_hash + _canonical(body)).encode("utf-8")).hexdigest()


def load_ledger() -> list[dict]:
    if not LEDGER.is_file():
        return []
    out = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _append(event: dict) -> dict:
    """追加一条事件（计算 seq / prev_hash / hash）。"""
    ledger = load_ledger()
    prev_hash = ledger[-1]["hash"] if ledger else "0" * 64
    body = {k: v for k, v in event.items() if k not in ("seq", "prev_hash", "hash")}
    seq = (ledger[-1]["seq"] + 1) if ledger else 1
    h = _hash(prev_hash, body)
    rec = {"seq": seq, "prev_hash": prev_hash, "hash": h, **body}
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def rebuild_status(ledger: list[dict]) -> dict:
    """由台账派生当前状态。"""
    state: dict[str, dict] = {}
    for ev in ledger:
        rep = ev.get("report")
        if not rep:
            continue
        cur = state.get(rep, {"state": None, "audit_id": "", "finalized_at": "",
                              "content_hash": "", "html_hash": "", "last_seq": 0})
        key = (cur["state"], ev["event"])
        target = TRANSITIONS.get(key)
        if target is None and ev["event"] == "submit" and cur["state"] is None:
            # 容错：缺失 register 事件时，submit 视为自登记直接进入待初审
            target = "pending_initial"
        if target is not None:
            cur["state"] = target
        note = ev.get("note", "") or ""
        if "审计编号 " in note:
            cur["audit_id"] = note.split("审计编号 ")[-1].split(" ")[0]
        if target == "audited":
            cur["finalized_at"] = ev["ts"]
        if ev.get("content_hash"):
            cur["content_hash"] = ev["content_hash"]
        if ev.get("html_hash"):
            cur["html_hash"] = ev["html_hash"]
        cur["last_seq"] = ev["seq"]
        state[rep] = cur
    return state


def write_status(state: dict) -> Path:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"version": SPEC_VERSION, "updated": _now(), "reports": state}
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return STATUS


def _current_hashes(rel: str) -> tuple[str, str]:
    """当前 (md, html) 双指纹；html 缺失时为 ""。"""
    md = ROOT / rel
    return content_fingerprints(md, md.with_suffix(".html"))


def _next_audit_id(state: dict) -> str:
    ym = datetime.now(timezone.utc).strftime("%Y%m")
    used = [v.get("audit_id", "") for v in state.values()]
    n = 1
    while f"AUD-{ym}-{n:03d}" in used:
        n += 1
    return f"AUD-{ym}-{n:03d}"


def cmd_init() -> int:
    ledger = load_ledger()
    registered = {ev["report"] for ev in ledger if ev["event"] == "register"}
    added = 0
    for e in discover():
        if e["report"] in registered:
            continue
        _append({"ts": _now(), "event": "register", "report": e["report"],
                 "actor": "system", "role": "system", "result": "ok",
                 "note": "登记入库（AuditGuard）", "content_hash": e["content_hash"]})
        added += 1
    state = rebuild_status(load_ledger())
    write_status(state)
    build_registry()
    print(f"审计登记：新增 {added} 份，共 {len(state)} 份纳入流程")
    return 0


def _report_arg(rel: str) -> str:
    rel = rel.replace("\\", "/")
    if not (ROOT / rel).is_file():
        raise SystemExit(f"[ERROR] 报告不存在：{rel}")
    if not rel.endswith(".md"):
        raise SystemExit(f"[ERROR] 请传入 md 源稿路径：{rel}")
    return rel


def cmd_submit(rel: str | None, all_: bool, actor: str) -> int:
    ledger = load_ledger()
    state = rebuild_status(ledger)
    targets = [e["report"] for e in discover()] if all_ else [_report_arg(rel)]
    n = 0
    for rep in targets:
        cur = state.get(rep, {}).get("state")
        if cur not in (None, "registered", "rejected", "stale"):
            print(f"[SKIP] {rep}：当前状态 {cur}，不可提交")
            continue
        md_h, html_h = _current_hashes(rep)
        _append({"ts": _now(), "event": "submit", "report": rep, "actor": actor,
                 "role": "generator", "result": "ok", "note": "提交初审",
                 "content_hash": md_h, "html_hash": html_h})
        state[rep] = {"state": "pending_initial", "audit_id": "", "finalized_at": "",
                      "content_hash": md_h, "html_hash": html_h, "last_seq": 0}
        n += 1
    write_status(state)
    build_registry()
    print(f"提交初审：{n} 份")
    return 0


def cmd_review(stage: str, rel: str | None, all_: bool, result: str, actor: str,
               note: str, evidence: str | None) -> int:
    if stage not in STAGES:
        raise SystemExit(f"[ERROR] 非法环节：{stage}（可选 {STAGES}）")
    if result not in ("pass", "fail"):
        raise SystemExit("[ERROR] result 仅支持 pass / fail")
    ledger = load_ledger()
    state = rebuild_status(ledger)
    targets = [e["report"] for e in discover()] if all_ else [_report_arg(rel)]
    role = ROLE_OF_STAGE[stage]
    expected = {"initial": "pending_initial", "re_review": "pending_re_review",
                "final": "pending_final"}[stage]
    event = "stage_pass" if result == "pass" else "stage_fail"
    if stage == "re_review" and result == "pass":
        ok, problems = validate_l5_evidence(evidence or "")
        if not ok:
            for p in problems:
                print(f"[X] {p}")
            print("[ERROR] re_review 通过必须附有效 L5 语义复核证据（见 l5-semantic-review.md）")
            return 1
    n = 0
    for rep in targets:
        cur = state.get(rep, {}).get("state")
        if cur != expected:
            print(f"[SKIP] {rep}：当前状态 {cur or '未登记'}，期望 {expected}")
            continue
        body_note = note
        if stage == "final" and result == "pass":
            audit_id = _next_audit_id(state)
            body_note = f"{note}；审计编号 {audit_id}"
        md_h, html_h = _current_hashes(rep)
        _append({"ts": _now(), "event": event, "report": rep, "actor": actor or DEFAULT_ACTOR[stage],
                 "role": role, "result": result, "note": body_note,
                 "evidence": evidence or "", "content_hash": md_h, "html_hash": html_h})
        n += 1
    state = rebuild_status(load_ledger())
    write_status(state)
    build_registry()
    print(f"{stage} 结论 {result}：{n} 份")
    return 0


def cmd_status() -> int:
    ledger = load_ledger()
    state = rebuild_status(ledger)
    if not state:
        print("审计台账为空（运行 --init 登记）")
        return 0
    rows = [["报告", "状态", "审计编号", "终审时间", "绑定指纹"]]
    for rep in sorted(state):
        v = state[rep]
        rows.append([rep, STATE_LABEL.get(v["state"], v["state"] or "—"),
                     v.get("audit_id") or "—", v.get("finalized_at") or "—",
                     (v.get("content_hash") or "—")[:19]])
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    counts: dict[str, int] = {}
    for v in state.values():
        counts[v["state"]] = counts.get(v["state"], 0) + 1
    print("\n".join(out))
    print("\n状态分布：" + "　".join(f"{STATE_LABEL.get(k, k)} {n}" for k, n in sorted(counts.items())))
    return 0


def cmd_verify() -> int:
    ledger = load_ledger()
    problems: list[str] = []
    prev = "0" * 64
    for ev in ledger:
        body = {k: v for k, v in ev.items() if k not in ("seq", "prev_hash", "hash")}
        if ev.get("prev_hash") != prev:
            problems.append(f"事件 #{ev.get('seq')} prev_hash 断裂")
        if _hash(prev, body) != ev.get("hash"):
            problems.append(f"事件 #{ev.get('seq')} hash 校验失败（疑似篡改）")
        prev = ev.get("hash", prev)

    state = rebuild_status(ledger)
    ids = [v.get("audit_id") for v in state.values() if v.get("audit_id")]
    if len(ids) != len(set(ids)):
        problems.append("审计编号重复")
    for rep, v in sorted(state.items()):
        if v["state"] == "audited":
            cur_md, cur_html = _current_hashes(rep)
            if cur_md != v.get("content_hash"):
                problems.append(f"{rep}：内容指纹失配（当前 {cur_md[:19]} ≠ 绑定 "
                                f"{(v.get('content_hash') or '')[:19]}），审计失效")
            elif v.get("html_hash") and cur_html != v["html_hash"]:
                problems.append(f"{rep}：HTML 指纹失配（当前 {cur_html[:19]} ≠ 绑定 "
                                f"{v['html_hash'][:19]}），审计失效")
    if problems:
        for p in problems:
            print(f"[X] {p}")
        print(f"台账校验失败：{len(problems)} 项问题")
        return 1
    print(f"台账校验通过：{len(ledger)} 条事件、{len(state)} 份报告；哈希链完整、指纹绑定一致")
    return 0


def cmd_sync() -> int:
    ledger = load_ledger()
    state = rebuild_status(ledger)
    n = 0
    for rep, v in sorted(state.items()):
        if v["state"] != "audited":
            continue
        cur_md, cur_html = _current_hashes(rep)
        if cur_md != v.get("content_hash") or (v.get("html_hash") and cur_html != v["html_hash"]):
            _append({"ts": _now(), "event": "revoke", "report": rep, "actor": "system",
                     "role": "system", "result": "ok",
                     "note": "内容指纹失配，审计失效（stale）", "content_hash": cur_md,
                     "html_hash": cur_html})
            n += 1
    state = rebuild_status(load_ledger())
    write_status(state)
    build_registry()
    print(f"同步完成：{n} 份审计失效（stale），需修改后重新走流程")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="审计质量管控流程")
    ap.add_argument("--init", action="store_true", help="登记全部报告")
    ap.add_argument("--submit", action="store_true", help="提交初审")
    ap.add_argument("--review", action="store_true", help="记录环节结论")
    ap.add_argument("--stage", choices=STAGES, help="环节：initial / re_review / final")
    ap.add_argument("--result", choices=["pass", "fail"], help="环节结论")
    ap.add_argument("--report", help="报告相对路径（md 源稿）")
    ap.add_argument("--all", action="store_true", help="作用于全部报告")
    ap.add_argument("--actor", help="执行主体（默认按环节取 reviewer_l1 / reviewer_l2 / audit_chair）")
    ap.add_argument("--note", default="", help="结论说明")
    ap.add_argument("--evidence", help="依据（JSON 或文本，如 audit_check 结论）")
    ap.add_argument("--status", action="store_true", help="打印状态表")
    ap.add_argument("--verify", action="store_true", help="校验台账哈希链与指纹绑定")
    ap.add_argument("--sync", action="store_true", help="同步指纹失配的审计失效报告")
    args = ap.parse_args()

    if args.init:
        return cmd_init()
    if args.submit:
        if not args.report and not args.all:
            ap.error("--submit 需要 --report <路径> 或 --all")
        return cmd_submit(args.report, args.all, args.actor or "generator")
    if args.review:
        if not args.stage or not args.result:
            ap.error("--review 需要 --stage 与 --result")
        if not args.report and not args.all:
            ap.error("--review 需要 --report <路径> 或 --all")
        return cmd_review(args.stage, args.report, args.all, args.result,
                          args.actor or "", args.note, args.evidence)
    if args.status:
        return cmd_status()
    if args.verify:
        return cmd_verify()
    if args.sync:
        return cmd_sync()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
