"""内容更新任务清单（手动 / 待建定时任务的「生成任务清单」步骤）。

按业务线与周期判断应执行的任务，输出 tasks.md（人读）与 tasks.json
（--porcelain，供创建 Issue 的脚本判断是否为空）。

报告已统一为月度命名 `YYYY-MM-<主题slug>`：一个主题每月产出一份报告，
季度节拍按季度末月归档（2026-Q4 -> 2026-12），与月度报告同一套命名 / 对比 /
展示逻辑。任务清单按目标自然月判断报告是否已产出。

用法：
    python prompts/tools/update_planner.py --porcelain --pending-only \
        [--project 01-ssw-driver] [--period 2026-11] > tasks.json
    python prompts/tools/update_planner.py --pending-only [--project ...] [--period ...] > tasks.md

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
    Business,
    iter_business_dirs,
    month_report_name,
    parse_period,
    quarter_to_month,
    topic_slug,
)


def default_period(now: datetime) -> str:
    """与定时任务的周期计算逻辑一致：季首月用季度标识。"""
    month = now.month
    year = now.year
    if month in (1, 4, 7, 10):
        return f"{year}-Q{(month - 1) // 3 + 1}"
    return f"{year}-{month:02d}"


# 月度任务选取提示词的优先级：越靠前者越贴合「月度产出」语义，
# 避免按字母序误选到年度 / 季度提示词。
PROMPT_PRIORITY = [
    "prompt-monthly-monitor.md",
    "prompt-update.md",
    "prompt-policy-review.md",
    "prompt-baseline-setup.md",
    "prompt-quarterly-analysis.md",
    "prompt-annual-review.md",
    "prompt-annual-refresh.md",
    "prompt-weekly-monitor.md",
]


def pick_prompt(prompts: list[str]) -> str:
    """从主题可用提示词中挑一个最贴合月度任务的；为空返回空串。"""
    for p in PROMPT_PRIORITY:
        if p in prompts:
            return p
    return sorted(prompts)[0] if prompts else ""


def target_month(period: str) -> str:
    """周期标识 -> 目标自然月（季度 / 年度取末月）。"""
    try:
        cycle, y, n = parse_period(period)
    except ValueError:
        raise
    if cycle == "month":
        return f"{y}-{n:02d}"
    if cycle == "quarter":
        return quarter_to_month(period) or f"{y}-{(n * 3):02d}"
    return f"{y}-12"


def build_tasks(period: str, businesses: list[Business]) -> list[dict]:
    month = target_month(period)
    tasks = []
    for b in businesses:
        # 扫描主题 prompts/ 下全部提示词（含 update / policy-review 等），
        # 只要建立了任一提示词即纳入该月任务（具体节拍由提示词优先级选取）
        prompts_dir = b.path / "prompts"
        prompts = (
            sorted(p.name for p in prompts_dir.glob("prompt-*.md"))
            if prompts_dir.is_dir()
            else []
        )
        if not prompts:
            continue
        rs = topic_slug(b.region if not b.property_type else b.property_type)
        output = month_report_name(month, rs, "html")
        status = "done" if (b.path / "reports" / output).exists() else "pending"
        tasks.append(
            {
                "project": b.rel,
                "cycle": "monthly",
                "cycle_label": "月度",
                "period": month,
                "prompt": f"{b.rel}/prompts/{pick_prompt(prompts)}",
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
    ap.add_argument("--project", default="", help="限定业务线（如 01-ssw-driver），缺省全部")
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
