"""待核实项闭环管理：登记 / 追踪各主题登记册的首轮核验截止期限。

- 主题范围由 `iter_business_dirs()` 动态派生（凡存在 `data/*_indicator_registry.md` 的主题）；
- 扫描登记册的「核验闭环」段，读取 `首轮核验截止` 与待核实项（含 ⚠ 的行）；
- 状态：未登记 / 进行中 / 临近（≤30 天）/ 已逾期；
- 输出 JSON 到 `engine/report-audits/audit/pending-verification.json`（机器可读），
  并在控制台给出人读汇总。

用法：
    python engine/tools/pending_verification.py            # 汇总 + 写 JSON
    python engine/tools/pending_verification.py --check    # 仅检查，不写文件

退出码：0 = 全部在窗口内；1 = 存在逾期或未登记；2 = 仅临近。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, iter_business_dirs, load_decision_config  # noqa: E402


def _topics() -> tuple[str, ...]:
    """纳入有跟踪需求的主题：登记册含「首轮核验截止」或 ⚠ 待核实项。"""
    out = []
    for b in iter_business_dirs():
        hits = sorted((b.path / "data").glob("*_indicator_registry.md"))
        if not hits:
            continue
        text = hits[0].read_text(encoding="utf-8", errors="replace")
        if "首轮核验截止" in text or "⚠" in text:
            out.append(b.rel)
    return tuple(sorted(out))


# 文档口径的默认截止日：历史校验报告已归档（git 历史），程序不消费（实际截止日解析自登记册文本）。
# 阈值与默认值外置到 engine/config/decision-tools.json（单一事实源）。
_PENDING_CFG = load_decision_config()["pending_verification"]
DEFAULT_DEADLINE = _PENDING_CFG["default_deadline"]
NEAR_WINDOW_DAYS = _PENDING_CFG["near_window_days"]
OUT_PATH = ROOT / "engine" / "report-audits" / "audit" / "pending-verification.json"


def _registry(topic: str) -> Path | None:
    for b in iter_business_dirs():
        if b.rel == topic:
            hits = sorted((b.path / "data").glob("*_indicator_registry.md"))
            return hits[0] if hits else None
    return None


def _parse(topic: str) -> dict:
    p = _registry(topic)
    if p is None:
        return {"topic": topic, "registry": None, "deadline": None, "status": "未登记",
                "pending": [], "entries": 0}
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"首轮核验截止[：:]\s*(\d{4}-\d{2}-\d{2})", text)
    deadline = m.group(1) if m else None
    # 待核实项：含 ⚠ 的行（去重后按出现顺序）
    pending = []
    for ln in text.splitlines():
        if "⚠" in ln:
            s = ln.strip()
            if s and s not in pending:
                pending.append(s[:120])
    status = "未登记"
    if deadline:
        d = date.fromisoformat(deadline)
        today = date.today()
        if d < today:
            status = "已逾期"
        elif (d - today).days <= NEAR_WINDOW_DAYS:
            status = "临近"
        else:
            status = "进行中"
    return {"topic": topic, "registry": str(p.relative_to(ROOT)).replace("\\", "/"),
            "deadline": deadline, "status": status, "pending": pending,
            "entries": len(pending)}


def run() -> tuple[list[dict], dict]:
    rows = [_parse(t) for t in _topics()]
    summary = {
        "updated": date.today().isoformat(),
        "topics": len(rows),
        "registered": sum(1 for r in rows if r["deadline"]),
        "overdue": sum(1 for r in rows if r["status"] == "已逾期"),
        "due_soon": sum(1 for r in rows if r["status"] == "临近"),
        "unregistered": sum(1 for r in rows if r["status"] == "未登记"),
        "pending_items": sum(len(r["pending"]) for r in rows),
    }
    return rows, summary


def main() -> int:
    ap = argparse.ArgumentParser(description="待核实项闭环管理")
    ap.add_argument("--check", action="store_true", help="仅检查，不写 JSON")
    args = ap.parse_args()

    rows, summary = run()
    print(f"待核实项闭环：{summary['topics']} 个模块")
    print(f"  已登记截止 {summary['registered']} / 未登记 {summary['unregistered']} / "
          f"临近 {summary['due_soon']} / 已逾期 {summary['overdue']}；待核实条目 {summary['pending_items']} 条")
    for r in rows:
        print(f"  [{r['status']}] {r['topic']} 截止 {r['deadline'] or '—'} · 待核实 {len(r['pending'])} 条")

    if not args.check:
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps({"summary": summary, "items": rows},
                                       ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已写入：{OUT_PATH.relative_to(ROOT)}")

    if summary["overdue"] or summary["unregistered"]:
        return 1
    if summary["due_soon"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
