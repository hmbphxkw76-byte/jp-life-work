"""内容更新任务清单（CI: content-update 的「生成任务清单」步骤）。

按业务线与周期判断应执行的任务，输出 tasks.md（人读）与 tasks.json
（--porcelain，供创建 Issue 的脚本判断是否为空）。

用法（与 content-update.yml 一致）：
    python prompts/tools/update_planner.py --porcelain --pending-only \
        [--project dubai/apartment] [--period 2026-11] > tasks.json
    python prompts/tools/update_planner.py --pending-only [--project ...] [--period ...] > tasks.md

周期规则（与 _common.tasks_for_period 一致）：
    月度期 YYYY-MM  -> 月度任务；季首月追加季度任务；1 月追加上一自然年年度任务
    季度期 YYYY-Qn  -> 季度任务
    年度期 YYYY     -> 年度任务
任务状态：输出文件已存在于业务 reports/ 则为 done，否则 pending。

退出码：0 = 正常（含空清单）；2 = 参数错误（项目 / 周期无法识别）。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    PROMPT_FILES,
    Business,
    expected_output,
    iter_business_dirs,
    parse_period,
    tasks_for_period,
)

CYCLE_LABEL = {"monthly": "月度", "quarterly": "季度", "annual": "年度", "baseline": "基线"}


def default_period(now: datetime) -> str:
    """与 content-update.yml 的「计算周期标识」逻辑一致：季首月用季度标识。"""
    month = now.month
    year = now.year
    if month in (1, 4, 7, 10):
        return f"{year}-Q{(month - 1) // 3 + 1}"
    return f"{year}-{month:02d}"


def build_tasks(period: str, businesses: list[Business]) -> list[dict]:
    try:
        cycle, y, n = parse_period(period)
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        raise SystemExit(2)
    tasks = []
    for b in businesses:
        for rc, ry, rn in tasks_for_period(cycle, y, n):
            # 业务线只为已建立周期提示词的周期生成任务（节拍设计由业务 prompts/ 实际内容决定），
            # 避免「周报型 / 事件触发型」业务线被硬派月度 / 季度 / 年度任务。
            if not (b.path / "prompts" / PROMPT_FILES[rc]).exists():
                continue
            output = expected_output(rc, ry, rn)
            prompt_rel = f"{b.rel}/prompts/{PROMPT_FILES[rc]}"
            status = "done" if (b.path / "reports" / output).exists() else "pending"
            tasks.append(
                {
                    "project": b.rel,
                    "cycle": rc,
                    "cycle_label": CYCLE_LABEL[rc],
                    "period": f"{ry}" + (f"-Q{rn}" if rc == "quarterly" else (f"-{rn:02d}" if rc == "monthly" else "")),
                    "prompt": prompt_rel,
                    "output": f"{b.rel}/reports/{output}",
                    "status": status,
                }
            )
    return tasks


def render_md(tasks: list[dict], period: str) -> str:
    lines = [f"## 内容更新任务清单（{period}）", ""]
    for t in tasks:
        mark = "x" if t["status"] == "done" else " "
        state = "已产出" if t["status"] == "done" else "待产出"
        lines.append(
            f"- [{mark}] {t['project']} · {t['cycle_label']} {t['period']}"
            f" — 提示词 `{t['prompt']}` · 输出 `{t['output']}`（{state}）"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="内容更新任务清单生成")
    ap.add_argument("--project", default="", help="限定业务线（如 dubai/apartment），缺省全部")
    ap.add_argument("--period", default="", help="周期标识（YYYY-MM / YYYY-Qn / YYYY），缺省按当前 UTC 日期")
    ap.add_argument("--pending-only", action="store_true", help="仅输出未完成任务")
    ap.add_argument("--porcelain", action="store_true", help="输出 JSON 数组")
    args = ap.parse_args()

    businesses = iter_business_dirs()
    if args.project:
        target = args.project.strip("/")
        businesses = [b for b in businesses if b.rel == target]
        if not businesses:
            print(f"[ERROR] 未找到业务线目录: {target}", file=sys.stderr)
            return 2

    period = args.period or default_period(datetime.now(tz=timezone.utc))
    try:
        parse_period(period)
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2

    tasks = build_tasks(period, businesses)
    if args.pending_only:
        tasks = [t for t in tasks if t["status"] == "pending"]

    if args.porcelain:
        print(json.dumps(tasks, ensure_ascii=False))
    else:
        print(render_md(tasks, period), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
