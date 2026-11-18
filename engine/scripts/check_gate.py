#!/usr/bin/env python3
"""输入润色与确认门禁 · 可移植性自检。

校验「跨 IDE / 跨模型 / 跨机器」所需载体是否齐备。只读，不修改任何文件。

用法：
    python engine/scripts/check_gate.py
    python engine/scripts/check_gate.py --root <仓库根>

退出码：0 = 必备项全部通过（可选项目缺失仅告警）；1 = 有必备项缺失。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

GATE_SECTION = "输入润色与确认门禁"
GATE_HINT = "机械判定"
REQUIRED_SKILL = "prompt-polish-confirm"
DOC_NAME = "输入润色与确认门禁.md"


def find_repo_root(start: Path) -> Path:
    """从 start 向上找同时含 AGENTS.md 与 .git 的目录。"""
    cur = start.resolve()
    for cand in (cur, *cur.parents):
        if (cand / "AGENTS.md").exists() and (cand / ".git").exists():
            return cand
    return cur


def check(root: Path) -> list[tuple[str, bool, str]]:
    """返回 [(检查项, 是否通过, 详情)]。"""
    results: list[tuple[str, bool, str]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, bool(ok), detail))

    agents = root / "AGENTS.md"
    add("AGENTS.md 存在（单一事实源）", agents.exists(), str(agents))
    if agents.exists():
        text = agents.read_text(encoding="utf-8")
        add("AGENTS.md 含门禁节", GATE_SECTION in text)
        add("AGENTS.md 含机械判定口径", GATE_HINT in text)

    claude = root / "CLAUDE.md"
    add("CLAUDE.md 存在", claude.exists(), str(claude))
    if claude.exists():
        add("CLAUDE.md 导入 AGENTS.md", "@AGENTS.md" in claude.read_text(encoding="utf-8"))

    cursor = root / ".cursorrules"
    add(".cursorrules 指针（可选）", cursor.exists(), str(cursor))

    meta = root / ".meituan-catpaw"
    skill_dirs = sorted(meta.glob("*/skills")) if meta.exists() else []
    skill_ok = any((d / REQUIRED_SKILL / "SKILL.md").exists() for d in skill_dirs)
    add(
        "工作区 skill 就位",
        skill_ok,
        "; ".join(str(d / REQUIRED_SKILL) for d in skill_dirs) or "未找到 .meituan-catpaw/*/skills",
    )

    doc = root / "docs" / DOC_NAME
    add("设计文档存在", doc.exists(), str(doc))

    return results


def _is_optional(name: str) -> bool:
    return "可选" in name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="输入门禁可移植性自检")
    parser.add_argument("--root", default=None, help="仓库根目录（默认自动探测）")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else find_repo_root(Path(__file__).resolve().parents[2])
    results = check(root)

    width = max(len(name) for name, _, _ in results)
    failed = 0
    for name, ok, detail in results:
        mark = "PASS" if ok else ("WARN" if _is_optional(name) else "FAIL")
        if not ok and not _is_optional(name):
            failed += 1
        line = f"[{mark}] {name.ljust(width)}"
        if detail:
            line += f"  {detail}"
        print(line)

    print(f"\n仓库根：{root}")
    if failed:
        print(f"结果：{failed} 项必备检查未通过 —— 请运行 `python engine/scripts/bootstrap_gate.py --install`")
        return 1
    print("结果：门禁载体齐备，跨 IDE / 跨模型 / 跨机器可用。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
