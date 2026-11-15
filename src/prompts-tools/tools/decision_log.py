"""决策日志：记录「决策状态变化」并生成时间线。

在月度更新流程中，决策状态（五问判定 / 关键决策）发生变化时追加一条记录，
形成时间线，为后续复盘提供数据支撑。

用法：
    python src/prompts-tools/tools/decision_log.py --add --question 去不去 --field 判定 \
        --old 待定 --new 是 --basis "个人参数补齐" --source 00
    python src/prompts-tools/tools/decision_log.py --list
    python src/prompts-tools/tools/decision_log.py --timeline

退出码：0 = 成功；1 = 参数错误 / 写入失败。
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT  # noqa: E402

LOG_PATH = ROOT / "00-decision-hub" / "data" / "decision_log.md"
ROW_RE = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|(.+)\|\s*$", re.M)

HEADER = ["日期", "决策问题", "字段", "变化前", "变化后", "依据", "来源"]


def _read() -> str:
    return LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.exists() else ""


def _ensure_header(text: str) -> str:
    if LOG_PATH.exists() and "# 决策日志" in text:
        return text
    return (
        "# 决策日志（状态变化时间线）\n\n"
        "> **用途**：记录五问判定与关键决策的**状态变化**，生成时间线，为后续复盘提供数据支撑。\n"
        "> **字段**：日期 / 决策问题 / 字段 / 变化前 / 变化后 / 依据 / 来源；由 `decision_log.py` 维护。\n\n"
        "| " + " | ".join(HEADER) + " |\n|" + "---|" * len(HEADER) + "\n"
    )


def add(question: str, field: str, old: str, new: str, basis: str, source: str,
        when: str = "") -> None:
    text = _ensure_header(_read())
    when = when or date.today().isoformat()
    row = f"| {when} | {question} | {field} | {old} | {new} | {basis} | {source} |"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(text.rstrip() + "\n" + row + "\n", encoding="utf-8")


def entries(limit: int = 0) -> list[dict]:
    """读取日志条目（按时间倒序，limit=0 全部）。"""
    text = _read()
    out: list[dict] = []
    for m in ROW_RE.finditer(text):
        cells = [c.strip() for c in m.group(2).split("|")]
        if len(cells) < 6:
            continue
        out.append({"日期": m.group(1), "决策问题": cells[0], "字段": cells[1],
                    "变化前": cells[2], "变化后": cells[3], "依据": cells[4], "来源": cells[5]})
    out.reverse()
    return out[:limit] if limit else out


def render_timeline(limit: int = 0) -> str:
    rows = entries(limit)
    lines = ["## 决策时间线", ""]
    if not rows:
        lines.append("（暂无记录）")
        return "\n".join(lines)
    for r in rows:
        lines.append(f"- **{r['日期']}**｜{r['决策问题']} · {r['字段']}："
                     f"{r['变化前']} → {r['变化后']}（依据：{r['依据']}；来源：{r['来源']}）")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="决策日志")
    ap.add_argument("--add", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--timeline", action="store_true")
    ap.add_argument("--question", default="")
    ap.add_argument("--field", default="")
    ap.add_argument("--old", default="")
    ap.add_argument("--new", default="")
    ap.add_argument("--basis", default="")
    ap.add_argument("--source", default="00-decision-hub")
    ap.add_argument("--date", default="")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if args.add:
        if not (args.question and args.field and args.new):
            print("[ERROR] --add 需要 --question / --field / --new")
            return 1
        add(args.question, args.field, args.old or "（初始）", args.new,
            args.basis or "—", args.source, args.date)
        print(f"已追加决策日志：{args.question} · {args.field} → {args.new}")
        return 0

    if args.timeline:
        print(render_timeline(args.limit))
        return 0

    for r in entries(args.limit):
        print(f"{r['日期']}｜{r['决策问题']}·{r['字段']}：{r['变化前']} → {r['变化后']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
