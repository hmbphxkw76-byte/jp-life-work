#!/usr/bin/env python3
"""输入润色与确认门禁 · 新机器部署脚本。

git clone 后运行一条命令完成部署与自检：
    python engine/scripts/bootstrap_gate.py            # 校验模式（只读）
    python engine/scripts/bootstrap_gate.py --install  # 部署模式（补齐缺失载体）
    python engine/scripts/bootstrap_gate.py --install --personal  # 额外部署到个人 skills 目录

部署内容（项目级，jp-life-work）：
- 校验单一事实源 AGENTS.md 的「输入润色与确认门禁」节；
- 补齐 CLAUDE.md（@AGENTS.md 导入）与 .cursorrules（指针）；
- 确保工作区 skill prompt-polish-confirm 就位；
- 运行 check_gate 自检并输出报告。

默认不修改个人级（跨项目）工件；--personal 才会写入 ~/.meituan-catpaw/<uid>/skills/。
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_gate import check, find_repo_root  # noqa: E402

CLAUDE_MD = """# CLAUDE.md

本仓库会话硬性规约以 `AGENTS.md` 为唯一事实源（含「输入润色与确认门禁」），任何 IDE / 模型均须遵守。

@AGENTS.md
"""

CURSORRULES = """# Cursor 规则
# 本仓库会话硬性规约以 AGENTS.md 为唯一事实源（含「输入润色与确认门禁」），请严格遵守。
@AGENTS.md
"""


def install(root: Path) -> list[str]:
    """补齐缺失的项目级载体，返回动作列表。"""
    actions: list[str] = []

    claude = root / "CLAUDE.md"
    if not claude.exists():
        claude.write_text(CLAUDE_MD, encoding="utf-8", newline="\n")
        actions.append(f"创建 {claude}")

    cursor = root / ".cursorrules"
    if not cursor.exists():
        cursor.write_text(CURSORRULES, encoding="utf-8", newline="\n")
        actions.append(f"创建 {cursor}")

    return actions


def install_personal(root: Path) -> list[str]:
    """把工作区 skill 部署到 ~/.meituan-catpaw/<uid>/skills/（跨项目可用）。"""
    actions: list[str] = []
    home = Path(os.path.expanduser("~")) / ".meituan-catpaw"
    if not home.exists():
        actions.append(f"跳过：未找到 {home}")
        return actions

    src_dirs = sorted((root / ".meituan-catpaw").glob("*/skills"))
    for src in src_dirs:
        uid = src.parent.parent.name
        dst = home / uid / "skills"
        dst.mkdir(parents=True, exist_ok=True)
        for skill_dir in src.iterdir():
            if not skill_dir.is_dir():
                continue
            target = dst / skill_dir.name
            if target.exists():
                actions.append(f"已存在 {target}")
                continue
            try:
                os.symlink(skill_dir.resolve(), target, target_is_directory=True)
                actions.append(f"链接 {skill_dir} -> {target}")
            except (OSError, NotImplementedError):
                shutil.copytree(skill_dir, target)
                actions.append(f"复制 {skill_dir} -> {target}")
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="输入门禁新机器部署")
    parser.add_argument("--root", default=None, help="仓库根目录（默认自动探测）")
    parser.add_argument("--install", action="store_true", help="补齐缺失载体（默认只校验）")
    parser.add_argument("--personal", action="store_true", help="额外部署到个人 skills 目录")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else find_repo_root(Path(__file__).resolve().parents[2])
    if not (root / "AGENTS.md").exists():
        print(f"错误：{root} 不是 jp-life-work 仓库根（缺 AGENTS.md）", file=sys.stderr)
        return 2

    print(f"[bootstrap] 仓库根：{root}")
    if args.install:
        for a in install(root):
            print(f"[bootstrap] {a}")
        if args.personal:
            for a in install_personal(root):
                print(f"[bootstrap] {a}")
    else:
        print("[bootstrap] 校验模式（只读）；加 --install 补齐缺失载体")

    print("[bootstrap] 运行自检：")
    results = check(root)
    width = max(len(n) for n, _, _ in results)
    failed = 0
    for name, ok, detail in results:
        mark = "PASS" if ok else ("WARN" if "可选" in name else "FAIL")
        if not ok and "可选" not in name:
            failed += 1
        line = f"[{mark}] {name.ljust(width)}"
        if detail:
            line += f"  {detail}"
        print(line)
    if failed:
        print(f"\n结果：{failed} 项必备检查未通过。")
        return 1
    print("\n结果：门禁已就绪 —— 跨 IDE / 跨模型 / 跨机器可用。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
