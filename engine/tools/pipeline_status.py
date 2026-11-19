"""统一监控视图：阶段进度 / 阻塞点 / 审计分布 / 心跳（PIPELINE-ORCHESTRATOR）。

对应 `docs/端到端流水线治理标准.md`「监控」：

- 汇总编排状态机的阶段进度、当前阻塞点（首个非 completed 阶段）、
  审计状态分布与 `automation-status.json` 最近心跳；
- 输出 `status.md`（人读）+ `status.json`（机器读）到 `engine/report-audits/pipeline/`；
- 只读既有状态与台账，不修改任何规则。

`STAGES` 为六阶段 canonical 顺序，编排器 `pipeline_runner` 复用本常量，
避免出现两份阶段事实源。

用法：
    python engine/tools/pipeline_status.py [--period 2026-11] [--porcelain]

退出码：0 = 正常（含空状态）。
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402
import automation_status  # noqa: E402

# 六阶段 canonical 顺序（S2_author 为唯一人工闸门）
STAGES: tuple[str, ...] = (
    "S0_detect",
    "S1_plan",
    "S2_author",
    "S3_build",
    "S4_audit",
    "S5_monitor",
)

AUDIT_STATUS_PATH = _common.ROOT / "engine" / "report-audits" / "audit" / "audit-status.json"
STATUS_JSON = _common.PIPELINE_DIR / "status.json"
STATUS_MD = _common.PIPELINE_DIR / "status.md"


def _latest_period() -> str:
    """最新状态文件的周期标识；无状态文件返回空串。"""
    files = sorted(_common.PIPELINE_DIR.glob("state-*.json"))
    if not files:
        return ""
    name = files[-1].name
    return name[len("state-"):-len(".json")]


def _audit_distribution() -> dict:
    """审计台账状态分布（`audit-status.json` 的 reports.*.state）。"""
    try:
        data = json.loads(AUDIT_STATUS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"total": 0, "states": {}}
    reports = data.get("reports", {}) if isinstance(data, dict) else {}
    states = Counter(
        (v.get("state") or "unknown") for v in reports.values() if isinstance(v, dict)
    )
    return {"total": len(reports), "states": dict(sorted(states.items()))}


def _latest_heartbeat() -> dict | None:
    """`automation-status.json` 最近一次心跳；无记录返回 None。"""
    records = automation_status.load_status().get("records", [])
    if not records:
        return None
    latest = max(records, key=lambda r: r.get("timestamp") or "")
    return {
        "phase": latest.get("phase"),
        "result": latest.get("result"),
        "timestamp": latest.get("timestamp"),
    }


def collect(period: str | None = None) -> dict:
    """汇总监控视图。

    - 状态文件不存在 → 空阶段表（冷启动），`blocking` 为 None；
    - 状态文件损坏 / schema 不符 → `state_error` 记录原因，不静默续跑。
    """
    period = period or _latest_period()
    stages: dict = {}
    state_error: str | None = None
    if period:
        try:
            stages = _common.load_state(period).get("stages", {})
        except FileNotFoundError:
            stages = {}
        except ValueError as exc:
            stages = {}
            state_error = str(exc)
    if not stages:
        blocking = None
    else:
        blocking = next(
            (
                name
                for name in STAGES
                if (stages.get(name) or {}).get("status") != "completed"
            ),
            None,
        )
    return {
        "period": period,
        "stages": stages,
        "blocking": blocking,
        "state_error": state_error,
        "audit": _audit_distribution(),
        "heartbeat": _latest_heartbeat(),
    }


def render_md(payload: dict) -> str:
    """渲染人读 `status.md`。"""
    period = payload.get("period") or "—"
    blocking = payload.get("blocking")
    lines = [
        f"# 流水线状态 · {period}",
        "",
        f"- 周期：{period}",
        f"- 阻塞：{blocking or '无'}",
    ]
    if payload.get("state_error"):
        lines.append(f"- 状态文件异常：{payload['state_error']}")
    stages = payload.get("stages") or {}
    lines += ["", "## 阶段进度", "", "| 阶段 | 状态 | 完成时间 |", "|---|---|---|"]
    for name in STAGES:
        st = stages.get(name) or {}
        lines.append(f"| {name} | {st.get('status') or '—'} | {st.get('completed') or '—'} |")
    audit = payload.get("audit") or {}
    lines += ["", "## 审计状态分布", "", f"- 报告总数：{audit.get('total', 0)}"]
    for state, n in (audit.get("states") or {}).items():
        lines.append(f"- {state}：{n}")
    hb = payload.get("heartbeat")
    lines += ["", "## 最近心跳", ""]
    if hb:
        lines.append(f"- {hb.get('phase')} / {hb.get('result')} @ {hb.get('timestamp')}")
    else:
        lines.append("- 无记录")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="统一流水线监控视图")
    ap.add_argument("--period", default="", help="周期标识；缺省取最新状态文件")
    ap.add_argument("--porcelain", action="store_true", help="仅输出 JSON")
    args = ap.parse_args()
    payload = collect(args.period or None)
    _common.PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
    _common.atomic_write(STATUS_JSON, json.dumps(payload, ensure_ascii=False, indent=2))
    _common.atomic_write(STATUS_MD, render_md(payload))
    if args.porcelain:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_md(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
