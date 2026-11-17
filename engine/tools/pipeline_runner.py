"""端到端流水线编排器（PIPELINE-ORCHESTRATOR 六阶段状态机）。

对应 `docs/端到端流水线编排系统设计-2026-11-17.md` §5.2 与
`docs/流水线编排实施计划-2026-11-17.md` 任务 3。

阶段：`S0_detect → S1_plan → S2_author（人工闸门）→ S3_build → S4_audit → S5_monitor`。

纪律：
- **唯一人工环节 = S2 研究正文撰写**；编排器只置 `pending` 并产出待撰写清单，
  绝不自动产出正文；
- 断点续跑：`run` 从 `S0` 起（遇 S2 暂停）；`resume --from-stage S3_build`
  表示人工已完成 S2，自动续跑 S3–S5；
- 幂等：每阶段可重复执行；状态写回走 `_common.atomic_write`；
- 损坏 / schema 不符的状态文件直接终止（退出码 1），不静默续跑；
- 提交 / 合并仍走 `engine/scripts/workflow_guard.py`，编排器不直接 push `main`。

用法：
    python engine/tools/pipeline_runner.py run --period 2026-11 [--dry-run]
    python engine/tools/pipeline_runner.py resume --period 2026-11 --from-stage S3_build
    python engine/tools/pipeline_runner.py status --period 2026-11

退出码：0 = 正常（含 S2 暂停）；1 = 阶段失败 / 状态损坏；2 = 参数错误。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402
import pipeline_status  # noqa: E402
import trigger_watch  # noqa: E402
import update_planner  # noqa: E402

# 六阶段 canonical 顺序（复用监控层常量，避免双份事实源）
STAGES: tuple[str, ...] = pipeline_status.STAGES

TOOLS_DIR = _common.ROOT / "engine" / "tools"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _run_tool(name: str, extra: list[str] | None = None) -> int:
    """调用既有工具（只调用，不修改其规则）；返回其退出码。"""
    cmd = [sys.executable, str(TOOLS_DIR / name), *(extra or [])]
    proc = subprocess.run(
        cmd, cwd=str(_common.ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.returncode != 0 and proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    return proc.returncode


def _period_reports(period: str, project: str | None) -> list[str]:
    """该周期（目标自然月）应产出的报告 md 相对路径（按主题 slug）。"""
    month = update_planner.target_month(period)
    out: list[str] = []
    for b in _common.iter_business_dirs():
        if project and b.rel != project:
            continue
        slug = _common.topic_slug(b.region if not b.property_type else b.property_type)
        name = _common.month_report_name(month, slug, "md")
        p = b.path / "reports" / name
        if p.is_file():
            out.append(p.relative_to(_common.ROOT).as_posix())
    return out


# ──────────────────────────────────────────────
# 阶段函数：签名 (period, project, dry_run) -> (ok, summary)
# ──────────────────────────────────────────────
def _s0_detect(period: str, project: str | None, dry_run: bool) -> tuple[bool, dict]:
    payload = trigger_watch.scan(period)
    if project:
        payload["window_due"] = [
            t for t in payload["window_due"] if t.get("project") == project
        ]
    return True, {
        "window_due": len(payload["window_due"]),
        "stale": len(payload["stale"]),
        "candidates": len(payload["candidates"]),
    }


def _s1_plan(period: str, project: str | None, dry_run: bool) -> tuple[bool, dict]:
    tasks = update_planner.build_tasks(period, _common.iter_business_dirs())
    pending = [t for t in tasks if t.get("status") == "pending"]
    if project:
        pending = [t for t in pending if t.get("project") == project]
    return True, {"pending_count": len(pending), "pending": pending}


def _s2_author(period: str, project: str | None, dry_run: bool) -> tuple[bool, dict]:
    """人工闸门：只产出待撰写清单，不产出正文（纪律硬约束）。"""
    tasks = update_planner.build_tasks(period, _common.iter_business_dirs())
    todo = [
        {"project": t.get("project"), "output": t.get("output"), "prompt": t.get("prompt")}
        for t in tasks
        if t.get("status") == "pending" and (not project or t.get("project") == project)
    ]
    return True, {"gate": "author", "todo": todo}


def _s3_build(period: str, project: str | None, dry_run: bool) -> tuple[bool, dict]:
    reports = _period_reports(period, project)
    if dry_run:
        return True, {"dry_run": True, "reports": reports, "skipped": ["md2html", "auto_verify"]}
    if not reports:
        return True, {"note": "无待生成报告", "reports": []}
    if _run_tool("md2html.py") != 0:
        return False, {"stage": "md2html", "reports": reports}
    failed = []
    for r in reports:
        if _run_tool("auto_verify.py", ["--report", r, "--quiet"]) != 0:
            failed.append(r)
    if failed:
        return False, {"stage": "auto_verify", "failed": failed}
    return True, {"reports": reports}


def _s4_audit(period: str, project: str | None, dry_run: bool) -> tuple[bool, dict]:
    reports = _period_reports(period, project)
    if dry_run:
        return True, {"dry_run": True, "reports": reports, "skipped": ["audit_pipeline --submit"]}
    if not reports:
        return True, {"note": "无待审计报告", "reports": []}
    failed = []
    for r in reports:
        if _run_tool("audit_pipeline.py", ["--submit", "--report", r]) != 0:
            failed.append(r)
    if failed:
        return False, {"stage": "audit_pipeline", "failed": failed}
    return True, {"reports": reports}


def _s5_monitor(period: str, project: str | None, dry_run: bool) -> tuple[bool, dict]:
    payload = pipeline_status.collect(period)
    return True, {
        "blocking": payload.get("blocking"),
        "audit_total": (payload.get("audit") or {}).get("total"),
    }


_STAGE_FUNCS = {
    "S0_detect": _s0_detect,
    "S1_plan": _s1_plan,
    "S3_build": _s3_build,
    "S4_audit": _s4_audit,
    "S5_monitor": _s5_monitor,
}


def run(
    period: str,
    project: str | None = None,
    dry_run: bool = False,
    from_stage: str | None = None,
) -> int:
    """从 `from_stage`（缺省 `S0_detect`）起顺序执行；遇 `S2_author` 停在 pending。"""
    try:
        _common.parse_period(period)
    except ValueError:
        print(f"[ERROR] 非法周期标识：{period}", file=sys.stderr)
        return 2
    start = from_stage or STAGES[0]
    if start not in STAGES:
        print(f"[ERROR] 非法起始阶段：{start}（可选 {list(STAGES)}）", file=sys.stderr)
        return 2

    try:
        state = _common.load_state(period)
    except FileNotFoundError:
        state = _common.new_state(period)  # 冷启动
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    now = _now()
    state["updated"] = now
    idx = STAGES.index(start)

    # resume 语义：start 之前的阶段视为已完成（人工已处理 S2 闸门）
    for name in STAGES[:idx]:
        st = state["stages"].setdefault(name, {})
        st["status"] = "completed"
        st.setdefault("completed", now)

    for name in STAGES[idx:]:
        if name == "S2_author":
            _ok, summary = _s2_author(period, project, dry_run)
            state["stages"][name] = {"status": "pending", "summary": summary, "started": now}
            _common.save_state(period, state)
            todo = summary.get("todo", [])
            print(f"[S2_author] 人工闸门：已产出待撰写清单（{len(todo)} 项），"
                  f"完成后 resume --from-stage S3_build")
            return 0
        ok, summary = _STAGE_FUNCS[name](period, project, dry_run)
        state["stages"][name] = {
            "status": "completed" if ok else "failed",
            "summary": summary,
            "started": now,
            "completed": now if ok else "",
        }
        _common.save_state(period, state)
        if not ok:
            print(f"[FAILED] {name}：{summary}", file=sys.stderr)
            return 1
        print(f"[OK] {name}")
    return 0


def status(period: str) -> dict:
    """只读状态视图：状态文件缺失返回冷启动空状态；损坏抛 `ValueError`。"""
    try:
        return _common.load_state(period)
    except FileNotFoundError:
        return _common.new_state(period)


def main() -> int:
    ap = argparse.ArgumentParser(description="端到端流水线编排器（六阶段状态机）")
    sub = ap.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="从 S0 起跑（遇 S2 人工闸门暂停）")
    p_run.add_argument("--period", required=True)
    p_run.add_argument("--project", default="")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.add_argument("--from-stage", default="")

    p_res = sub.add_parser("resume", help="人工完成 S2 后从指定阶段续跑")
    p_res.add_argument("--period", required=True)
    p_res.add_argument("--from-stage", default="S3_build")
    p_res.add_argument("--project", default="")
    p_res.add_argument("--dry-run", action="store_true")

    p_st = sub.add_parser("status", help="只读状态视图")
    p_st.add_argument("--period", required=True)
    p_st.add_argument("--porcelain", action="store_true")

    args = ap.parse_args()
    if args.command == "run":
        return run(args.period, args.project or None, args.dry_run, args.from_stage or None)
    if args.command == "resume":
        return run(args.period, args.project or None, args.dry_run, args.from_stage)
    payload = pipeline_status.collect(args.period)
    if args.porcelain:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(pipeline_status.render_md(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
