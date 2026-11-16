#!/usr/bin/env python3
"""架构注册表生成器（架构优化方向 A / I-9，T3.2 / T3.3）。

- 扫描工具脚本 / 报告类型 / 主题 / 工作流，生成 ``registry.json``（机器可读事实源）；
- 用注册表渲染 ``README.md`` 标记区间内的快照行（自动生成文档）；
- ``--check``：校验注册表与 README 快照是否与代码一致（不一致退出码 1）。

用法：
    python src/prompts-tools/tools/generate_registry.py --write
    python src/prompts-tools/tools/generate_registry.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = ROOT / "src" / "prompts-tools" / "tools"
REGISTRY_JSON = TOOLS_DIR / "registry.json"
README = TOOLS_DIR / "README.md"
BEGIN = "<!-- REGISTRY:BEGIN -->"
END = "<!-- REGISTRY:END -->"


def scan() -> dict:
    """扫描代码，产出注册表内容（唯一事实源）。"""
    tools = sorted(p.name for p in TOOLS_DIR.glob("*.py") if p.name != "_common.py")
    rules = json.loads(
        (ROOT / "src" / "report_templates" / "compliance-rules.json").read_text(encoding="utf-8")
    )
    types = sorted(rules.get("types", {}))
    topics = sorted(p.name for p in ROOT.iterdir()
                    if p.is_dir() and re.match(r"^\d{2}-", p.name))
    workflows = sorted(p.name for p in (ROOT / ".github" / "workflows").glob("*.yml"))
    return {"version": 1, "tools": tools, "types": types, "topics": topics, "workflows": workflows}


def counts(reg: dict) -> str:
    return (f"工具 {len(reg['tools'])} · 类型 {len(reg['types'])} · "
            f"主题 {len(reg['topics'])} · 工作流 {len(reg['workflows'])}")


def render_snapshot(reg: dict) -> str:
    return (f"{BEGIN}\n> 注册表快照：{counts(reg)}"
            f"（由 `generate_registry.py` 生成，勿手工编辑）\n{END}")


def write() -> int:
    reg = scan()
    REGISTRY_JSON.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text = README.read_text(encoding="utf-8")
    if BEGIN in text and END in text:
        text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END),
                      render_snapshot(reg), text, flags=re.DOTALL)
    else:
        text = text.rstrip("\n") + "\n\n" + render_snapshot(reg) + "\n"
    README.write_text(text, encoding="utf-8")
    print(f"注册表已生成：{REGISTRY_JSON.relative_to(ROOT)}（{counts(reg)}）")
    return 0


def check() -> int:
    reg = scan()
    problems: list[str] = []
    if not REGISTRY_JSON.is_file():
        problems.append("缺少 registry.json")
    else:
        disk = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
        for key in ("tools", "types", "topics", "workflows"):
            if sorted(disk.get(key, [])) != reg[key]:
                problems.append(f"{key} 不一致：注册表 {sorted(disk.get(key, []))} vs 实测 {reg[key]}")
    text = README.read_text(encoding="utf-8") if README.is_file() else ""
    if BEGIN not in text or END not in text:
        problems.append("README 缺少注册表标记区间")
    elif counts(reg) not in text:
        problems.append(f"README 快照行过期（应为 {counts(reg)}）")
    if problems:
        for p in problems:
            print(f"[ERROR] {p}")
        return 1
    print(f"注册表一致：{counts(reg)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="架构注册表生成器")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="生成 registry.json 并更新 README 快照")
    mode.add_argument("--check", action="store_true", help="校验一致性")
    args = ap.parse_args()
    if args.write:
        return write()
    return check()


if __name__ == "__main__":
    sys.exit(main())
