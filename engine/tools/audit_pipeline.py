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
    python audit_pipeline.py --rebind               # 内容未变、仅 HTML 渲染漂移的失效报告重新绑定（→ audited）
    python audit_pipeline.py --sampling-fail <清单>  # 抽检命中 P0/P1 的已审计报告置 stale（G→F 反馈链路）
    python audit_pipeline.py --gate                 # 合并门禁：完整性 + 变更报告审计状态（--strict 全库）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT  # noqa: E402
from audit_registry import (  # noqa: E402
    AUDIT_DIR,
    SPEC_VERSION,
    build as build_registry,
    content_fingerprint,
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
    ("audited", "sampling_fail"): "stale",
    ("stale", "rebind"): "audited",
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

# evidence 版本：v2 起为带版本号的封套（{version, report, verdict, items, notes}）；
# v1（无 version，仅 items）为存量格式，继续认可。
L5_EVIDENCE_VERSION = "2.0"


def validate_l5_evidence(text: str) -> tuple[bool, list[str]]:
    """校验复核证据 JSON（格式见 engine/report_templates/l5-semantic-review.md）。

    返回 (是否有效, 问题列表)。六项缺一不可；no / uncertain 必须给出非空 basis。
    v2 封套可选携带 version / verdict / notes；version 若存在须等于 L5_EVIDENCE_VERSION。
    """
    if not text or not text.strip():
        return False, ["缺少 L5 语义复核证据（--evidence）"]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return False, [f"evidence 不是合法 JSON：{e}"]
    if not isinstance(data, dict):
        return False, ["evidence 顶层须为 JSON 对象"]
    problems: list[str] = []
    ver = data.get("version")
    if ver is not None and ver != L5_EVIDENCE_VERSION:
        problems.append(f"evidence version 非法：{ver!r}（应为 {L5_EVIDENCE_VERSION} 或不填）")
    verdict = data.get("verdict")
    if verdict is not None and verdict not in ("pass", "fail"):
        problems.append(f"evidence verdict 非法：{verdict!r}（仅 pass / fail）")
    items = data.get("items")
    if not isinstance(items, list) or len(items) != len(L5_CHECKLIST):
        return False, [f"evidence.items 须为 {len(L5_CHECKLIST)} 项，实际 "
                        f"{len(items) if isinstance(items, list) else '非列表'}"]
    labels = [x[0] for x in L5_CHECKLIST]
    for i, it in enumerate(items, start=1):
        if not isinstance(it, dict):
            problems.append(f"第 {i} 项不是对象")
            continue
        label = str(it.get("item", "")).strip()
        if label != labels[i - 1]:
            problems.append(f"第 {i} 项 item 标签不符：{label!r}（应为 {labels[i - 1]!r}）")
        res = str(it.get("result", "")).strip().lower()
        basis = it.get("basis")
        basis = basis if isinstance(basis, str) else ""
        basis = basis.strip()
        if res not in ("yes", "no", "uncertain"):
            problems.append(f"第 {i} 项 result 非法：{res!r}")
        if res in ("no", "uncertain") and not basis:
            problems.append(f"第 {i} 项 {res} 缺少 basis 说明")
    return (not problems), problems


def l5_status_from_ledger() -> dict[str, bool]:
    """从台账派生各报告 L5 状态。

    仅当报告处于 audited 且当前指纹与绑定一致、且最近一次 re_review 证据有效时为 True。
    2026-11-15 起 `l5_backfill`（存量补核专项）与 `stage_pass`（复核环节）同等有效。
    """
    state = rebuild_status(load_ledger())
    ledger = load_ledger()
    status: dict[str, bool] = {}
    for rep, v in state.items():
        if v.get("state") != "audited":
            status[rep] = False
            continue
        cur_md, _cur_html = _current_hashes(rep)
        if not cur_md or cur_md != v.get("content_hash"):
            status[rep] = False
            continue
        ok = False
        for ev in ledger:
            if ev.get("report") != rep or ev.get("role") != "reviewer_l2":
                continue
            if ev.get("event") in ("stage_pass", "l5_backfill"):
                ok, _ = validate_l5_evidence(ev.get("evidence", ""))
            elif ev.get("event") == "stage_fail":
                ok = False
        status[rep] = ok
    return status


def _canonical(body: dict) -> str:
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(prev_hash: str, body: dict) -> str:
    return hashlib.sha256((prev_hash + _canonical(body)).encode("utf-8")).hexdigest()


def load_ledger() -> list[dict]:
    """读取台账（跳过损坏行，不崩溃）。"""
    if not LEDGER.is_file():
        return []
    out = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    out.sort(key=lambda e: e.get("seq", 0))
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
        if ev.get("audit_id"):
            cur["audit_id"] = ev["audit_id"]
        elif "审计编号 " in note:
            cur["audit_id"] = note.split("审计编号 ")[-1].split(" ")[0]
        if target == "audited" and ev["event"] != "rebind":
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
    """当前 (md, html) 双指纹；md 缺失时返回 ("", "")（按失配处理）。"""
    md = ROOT / rel
    if not md.is_file():
        return "", ""
    return content_fingerprints(md, md.with_suffix(".html"))


def _last_event(rep: str) -> dict | None:
    """该报告在台账中的最后一条事件（用于环节间连续性校验）。"""
    last = None
    for ev in load_ledger():
        if ev.get("report") == rep:
            last = ev
    return last


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


def _report_arg(rel: str | None) -> str:
    if not rel:
        raise SystemExit("[ERROR] 未指定报告路径")
    rel = rel.replace("\\", "/")
    try:
        resolved = (ROOT / rel).resolve()
        resolved.relative_to(ROOT.resolve())
    except (ValueError, OSError):
        raise SystemExit(f"[ERROR] 路径越出仓库根：{rel}")
    if not resolved.is_file():
        raise SystemExit(f"[ERROR] 报告不存在：{rel}")
    if resolved.suffix != ".md":
        raise SystemExit(f"[ERROR] 请传入 md 源稿路径：{rel}")
    return resolved.relative_to(ROOT.resolve()).as_posix()


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
        # 环节间连续性：自上一环节以来内容不得变更
        prev = _last_event(rep)
        md_h, html_h = _current_hashes(rep)
        if prev:
            if prev.get("content_hash") and md_h and md_h != prev["content_hash"]:
                print(f"[ERROR] {rep}：自上一环节（{prev.get('event')}）以来 md 内容已变更，"
                      f"需重新 submit")
                return 1
            if prev.get("html_hash") and html_h and html_h != prev["html_hash"]:
                print(f"[ERROR] {rep}：自上一环节（{prev.get('event')}）以来 HTML 已变更，"
                      f"需重新 submit")
                return 1
        if stage == "final" and result == "pass" and not html_h:
            print(f"[ERROR] {rep}：终审要求已生成 HTML 交付物（html_hash 为空）")
            return 1
        body_note = note
        audit_id = ""
        if stage == "final" and result == "pass":
            audit_id = _next_audit_id(state)
            body_note = f"{note}；审计编号 {audit_id}"
            state[rep]["audit_id"] = audit_id
        _append({"ts": _now(), "event": event, "report": rep, "actor": actor or DEFAULT_ACTOR[stage],
                 "role": role, "result": result, "note": body_note,
                 "evidence": evidence or "", "content_hash": md_h, "html_hash": html_h,
                 "audit_id": audit_id})
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


def _chain_problems(ledger: list[dict]) -> list[str]:
    """重算台账哈希链，返回问题列表（空 = 完整）。"""
    problems: list[str] = []
    prev = "0" * 64
    for ev in ledger:
        body = {k: v for k, v in ev.items() if k not in ("seq", "prev_hash", "hash")}
        if ev.get("prev_hash") != prev:
            problems.append(f"事件 #{ev.get('seq')} prev_hash 断裂")
        if _hash(prev, body) != ev.get("hash"):
            problems.append(f"事件 #{ev.get('seq')} hash 校验失败（疑似篡改）")
        prev = ev.get("hash", prev)
    return problems


def cmd_verify() -> int:
    ledger = load_ledger()
    problems: list[str] = _chain_problems(ledger)

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
    # 派生状态文件须与台账一致（防止信任分裂）
    if STATUS.is_file():
        try:
            disk = json.loads(STATUS.read_text(encoding="utf-8")).get("reports", {})
        except json.JSONDecodeError:
            disk = None
        if disk is None:
            problems.append("audit-status.json 损坏（非法 JSON）")
        else:
            for rep, v in state.items():
                d = disk.get(rep)
                if not isinstance(d, dict):
                    continue
                if d.get("state") != v.get("state"):
                    problems.append(f"{rep}：audit-status.json 状态 {d.get('state')} "
                                    f"≠ 台账 {v.get('state')}")
                if d.get("audit_id") != v.get("audit_id"):
                    problems.append(f"{rep}：audit-status.json 审计编号与台账不一致")
    if problems:
        for p in problems:
            print(f"[X] {p}")
        print(f"台账校验失败：{len(problems)} 项问题")
        return 1
    print(f"台账校验通过：{len(ledger)} 条事件、{len(state)} 份报告；哈希链完整、指纹绑定一致")
    return 0


def _audited_content_hash(ledger: list[dict], rep: str) -> str:
    """该报告最后一次终审通过（audit_chair stage_pass）时绑定的内容指纹。"""
    h = ""
    for ev in ledger:
        if (ev.get("report") == rep and ev.get("event") == "stage_pass"
                and ev.get("role") == "audit_chair"):
            h = ev.get("content_hash") or h
    return h


def cmd_rebind(all_: bool = True, rel: str | None = None) -> int:
    """对「md 内容未变、仅 HTML 渲染漂移」而失效的报告重新绑定指纹（stale → audited）。

    HTML 是 md 的确定性派生产物：html-sync 重生成会让 HTML 指纹变化，但只要
    md 内容指纹仍等于终审绑定值，原审计结论依然成立，不需重走流程。
    md 内容已变的报告保持 stale，必须重新审计。

    恢复时同步把「已审计」标识注入 md 与 HTML，并按注入后的最终形态绑定双指纹，
    避免「绑定的是注入前 HTML」导致后续校验再次失配。
    """
    from audit_badge import _insert_after_disclaimer, _regenerate_html, _strip_badge, badge_text

    ledger = load_ledger()
    state = rebuild_status(ledger)
    targets = [e["report"] for e in discover()] if all_ else [_report_arg(rel)]
    n = 0
    for rep in targets:
        if state.get(rep, {}).get("state") != "stale":
            continue
        audited_hash = _audited_content_hash(ledger, rep)
        audit_id = state[rep].get("audit_id", "")
        if not audited_hash or not audit_id:
            continue
        cur_md, _ = _current_hashes(rep)
        if cur_md != audited_hash:
            print(f"[SKIP] {rep}：md 内容已变，需重新审计")
            continue
        md = ROOT / rep
        text, _ = _strip_badge(md.read_text(encoding="utf-8"))
        text = _insert_after_disclaimer(
            text, badge_text(audit_id, state[rep].get("finalized_at", ""),
                             cur_md.removeprefix("sha256:")))
        md.write_text(text, encoding="utf-8")
        _regenerate_html(md)
        cur_md, cur_html = _current_hashes(rep)
        _append({"ts": _now(), "event": "rebind", "report": rep, "actor": "system",
                 "role": "system", "result": "ok",
                 "note": "HTML 渲染漂移重新绑定（md 内容未变，原审计结论继续有效）",
                 "content_hash": cur_md, "html_hash": cur_html,
                 "audit_id": audit_id})
        n += 1
    write_status(rebuild_status(load_ledger()))
    build_registry()
    print(f"重新绑定：{n} 份（内容未变，恢复 audited）；其余保持 stale 待重审")
    return 0


def cmd_backfill_l5(rel: str | None, all_: bool, evidence: str | None, actor: str) -> int:
    """存量报告 L5 补核专项：为已审计但缺有效 L5 证据的报告补录证据。

    幂等：已有有效证据者跳过；证据须经 validate_l5_evidence 校验；以独立事件
    l5_backfill（role=reviewer_l2）追加，保持哈希链与审计状态不变。
    """
    if not evidence:
        raise SystemExit("[ERROR] 需要 --evidence <JSON>")
    ok, problems = validate_l5_evidence(evidence)
    if not ok:
        for p in problems:
            print(f"[X] {p}")
        raise SystemExit("[ERROR] evidence 无效，补核未写入")
    ledger = load_ledger()
    state = rebuild_status(ledger)
    l5 = l5_status_from_ledger()
    targets = [e["report"] for e in discover()] if all_ else [_report_arg(rel)]
    n = 0
    for rep in targets:
        cur = state.get(rep, {})
        if cur.get("state") != "audited":
            print(f"[SKIP] {rep}：状态 {cur.get('state') or '未登记'}，非 audited")
            continue
        if l5.get(rep, False):
            print(f"[SKIP] {rep}：已有有效 L5 证据")
            continue
        md_h, html_h = _current_hashes(rep)
        _append({"ts": _now(), "event": "l5_backfill", "report": rep,
                 "actor": actor or "reviewer_l2", "role": "reviewer_l2",
                 "result": "pass",
                 "note": "存量报告 L5 补核专项（一次性，使用新 evidence 格式）",
                 "evidence": evidence, "content_hash": md_h, "html_hash": html_h})
        n += 1
    write_status(rebuild_status(load_ledger()))
    print(f"L5 补核：{n} 份（已追加 l5_backfill 证据）")
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


def mark_sampling_failures(reports: list[str]) -> int:
    """抽检命中 P0/P1：把对应已审计报告置 stale（G→F 反馈链路，规范七）。

    仅处理当前状态为 audited 的报告；其余状态（含已 stale）跳过，避免重复失效。
    事件类型 `sampling_fail`（role=system）经 TRANSITIONS 置 stale，
    之后由 `audit_badge --sync` 撤销标识，报告须重走 submit → 初审 → 复核 → 终审。
    """
    ledger = load_ledger()
    state = rebuild_status(ledger)
    n = 0
    for rep in reports:
        if state.get(rep, {}).get("state") != "audited":
            continue
        cur_md, cur_html = _current_hashes(rep)
        _append({"ts": _now(), "event": "sampling_fail", "report": rep,
                 "actor": "system", "role": "system", "result": "fail",
                 "note": "抽检命中 P0/P1，审计失效（stale），须重新走 submit → 初审 → 复核 → 终审",
                 "content_hash": cur_md, "html_hash": cur_html})
        n += 1
    write_status(rebuild_status(load_ledger()))
    build_registry()
    return n


def _changed_report_paths(base: str, changed_file: str | None) -> list[str]:
    """汇总本次变更的报告 md 相对路径（去重、排序）。

    changed_file 给出时按清单（每行一个路径）；否则对 `base...HEAD` 跑 git diff。
    仅保留 `*/reports/*.md`，HTML / 非报告变更不触发审计门禁。
    """
    raw: list[str] = []
    if changed_file:
        p = Path(changed_file)
        if not p.is_file():
            raise SystemExit(f"[ERROR] 变更清单不存在：{changed_file}")
        raw = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    else:
        import subprocess
        try:
            out = subprocess.run(
                ["git", "diff", "--name-only", f"{base}...HEAD"],
                cwd=str(ROOT), capture_output=True, text=True, check=True,
            )
            raw = [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
        except (OSError, subprocess.CalledProcessError):
            raw = []
    reps = set()
    for rel in raw:
        rel = rel.replace("\\", "/")
        if rel.endswith(".md") and "/reports/" in rel:
            reps.add(rel)
    return sorted(reps)


def _badge_problems() -> list[str]:
    """标识 ⟺ 状态一致性（与 audit_badge.cmd_check 同口径，供门禁复用）。"""
    import audit_badge

    status = audit_badge._load_status()
    problems: list[str] = []
    for e in discover():
        rep = e["report"]
        md = ROOT / rep
        text = md.read_text(encoding="utf-8")
        has = bool(audit_badge.BADGE_RE.search(text))
        v = status.get(rep, {})
        valid = v.get("state") == "audited" and content_fingerprint(md) == v.get("content_hash")
        if has and not valid:
            problems.append(f"{rep}：携带已审计标识但状态为 {v.get('state') or '未登记'} 或指纹失配")
        if valid and not has:
            problems.append(f"{rep}：状态 audited 但缺少已审计标识")
        html = md.with_suffix(".html")
        if html.is_file():
            h_has = 'class="audit-badge"' in html.read_text(encoding="utf-8", errors="replace")
            if h_has != has:
                problems.append(f"{rep}：HTML 标识与 md 标识不一致")
    return problems


def cmd_gate(changed_file: str | None, base: str, strict: bool) -> int:
    """合并门禁：完整性 + 受检报告审计状态（含 L5 证据）。

    阻断条件（任一即退出码 1）：
      - 台账哈希链断裂 / 篡改；
      - 登记册与实际文件不一致；
      - 「已审计」标识与状态不一致；
      - 受检报告（默认本次变更，--strict 全库）未 audited、指纹失配或缺有效 L5 证据。
    """
    import audit_registry

    ledger = load_ledger()
    state = rebuild_status(ledger)
    problems: list[str] = [f"台账：{p}" for p in _chain_problems(ledger)]

    _n, reg = audit_registry.check()
    problems += [f"登记册：{p}" for p in reg]
    problems += [f"标识：{p}" for p in _badge_problems()]

    if strict:
        targets = [e["report"] for e in discover()]
        mode = "全库严格模式"
    else:
        targets = _changed_report_paths(base, changed_file)
        mode = f"增量模式（base={base}）"

    l5 = l5_status_from_ledger()
    blocked: list[str] = []
    for rep in targets:
        v = state.get(rep)
        if not v:
            blocked.append(f"{rep}：未登记审计（无台账事件）")
            continue
        if v.get("state") != "audited":
            blocked.append(f"{rep}：状态 {v.get('state') or '未登记'}（未审计通过）")
            continue
        cur_md, cur_html = _current_hashes(rep)
        if cur_md != v.get("content_hash"):
            blocked.append(f"{rep}：内容指纹失配（审计后内容已变更）")
        elif v.get("html_hash") and cur_html != v["html_hash"]:
            blocked.append(f"{rep}：HTML 指纹失配（交付物已变更）")
        elif not l5.get(rep, False):
            blocked.append(f"{rep}：缺少有效 L5 语义复核证据")

    print(f"审计门禁 · {mode}")
    print(f"  台账事件 {len(ledger)} 条；登记报告 {len(state)} 份；受检报告 {len(targets)} 份")
    for p in problems:
        print(f"  [X] {p}")
    for b in blocked:
        print(f"  [拦截] {b}")
    if problems or blocked:
        print(f"→ 阻断合并：完整性问题 {len(problems)} 项、未通过审计 {len(blocked)} 份")
        return 1
    print("→ 门禁通过：完整性无问题，受检报告均已审计且证据有效")
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
    ap.add_argument("--rebind", action="store_true",
                    help="内容未变、仅 HTML 渲染漂移的失效报告重新绑定（stale → audited）")
    ap.add_argument("--backfill-l5", action="store_true",
                    help="存量报告 L5 补核专项：为已审计但缺证据的报告追加 evidence（新格式）")
    ap.add_argument("--sampling-fail", metavar="清单",
                    help="抽检不合格报告清单（每行一个路径）；命中 P0/P1 的已审计报告置 stale")
    ap.add_argument("--gate", action="store_true",
                    help="合并门禁：完整性 + 受检报告审计状态（缺省仅本次变更）")
    ap.add_argument("--changed", help="变更文件清单（每行一个路径）；缺省用 git diff base...HEAD")
    ap.add_argument("--base", default="origin/main", help="增量比对基线（默认 origin/main）")
    ap.add_argument("--strict", action="store_true", help="门禁检查全库报告（非仅变更）")
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
    if args.rebind:
        return cmd_rebind()
    if args.backfill_l5:
        if not args.report and not args.all:
            ap.error("--backfill-l5 需要 --report <路径> 或 --all")
        return cmd_backfill_l5(args.report, args.all, args.evidence, args.actor or "")
    if args.sampling_fail:
        p = Path(args.sampling_fail)
        if not p.is_file():
            raise SystemExit(f"[ERROR] 清单不存在：{args.sampling_fail}")
        reps = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        n = mark_sampling_failures(reps)
        print(f"抽检不合格处置：{n} 份报告已置 stale（须重走审计流程）")
        return 0
    if args.gate:
        return cmd_gate(args.changed, args.base, args.strict)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
