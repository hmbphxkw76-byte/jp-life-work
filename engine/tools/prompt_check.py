#!/usr/bin/env python3
"""prompt_check.py — 提示词命名 / 继承 / 结构 / 槽位门禁（P1-11）。

校验提示词体系的结构性约定（命名漂移即阻断）：

1. **命名**：业务提示词 `NN-<slug>/prompts/prompt-<kebab>.md`；
   类型模板 `engine/report_templates/<类型>/prompt-<kebab>-template.md`；
   泛用版 `engine/report_templates/<类型>/prompts/prompt-<kebab>.md`。
2. **继承声明**：业务提示词的基线 / 周期提示词（非 p1–p5 阶段提示词）必须引用
   `../../engine/report_templates/`（四层继承体系）。
3. **结构**：`prompt-p3/p4/p5-*.md` 必须含 `## 信息缺口` 节（固定七节骨架之一）。
4. **槽位**：`business-config.md` 必须含 `{{REGION}}` / `{{TOPIC}}` / `{{REGISTRY_PATH}}`，
   且含继承优先级口径（「冲突时」或「优先级」）。

用法：
    python engine/tools/prompt_check.py            # 全量校验，违规退出码 1
    python engine/tools/prompt_check.py --json
    python engine/tools/prompt_check.py --warn     # 仅告警（退出码 2）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, Business, iter_business_dirs  # noqa: E402

PROMPT_NAME_RE = re.compile(r"^prompt-[a-z0-9]+(-[a-z0-9]+)*\.md$")
TEMPLATE_NAME_RE = re.compile(r"^prompt-[a-z0-9]+(-[a-z0-9]+)*-template\.md$")
P_STAGE_RE = re.compile(r"^prompt-p[1-5]-[a-z0-9-]+\.md$")
INHERIT_LINK_RE = re.compile(r"\.\./\.\./engine/report_templates/")
REQUIRED_CONFIG_VARS = ("{{REGION}}", "{{TOPIC}}", "{{REGISTRY_PATH}}")
PRIORITY_RE = re.compile(r"冲突时|优先级")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def check_business(b: Business) -> list[str]:
    """校验单个业务主题 prompts/，返回问题列表。"""
    out: list[str] = []
    rel = b.rel
    prompts = b.path / "prompts"
    if not prompts.is_dir():
        return [f"{rel}: 缺 prompts/ 目录"]

    config = prompts / "business-config.md"
    if not config.is_file():
        out.append(f"{rel}: 缺 prompts/business-config.md")
    else:
        text = _read(config)
        for var in REQUIRED_CONFIG_VARS:
            if var not in text:
                out.append(f"{rel}: business-config.md 缺槽位 {var}")
        if not PRIORITY_RE.search(text):
            out.append(f"{rel}: business-config.md 缺继承优先级口径（冲突时/优先级）")

    for f in sorted(prompts.glob("*.md")):
        if f.name == "business-config.md" or f.name == "confidence-grade-standard.md":
            continue
        if not PROMPT_NAME_RE.match(f.name):
            out.append(f"{rel}/prompts/{f.name}: 命名不符 prompt-<kebab>.md")
            continue
        text = _read(f)
        if P_STAGE_RE.match(f.name):
            if "## 信息缺口" not in text:
                out.append(f"{rel}/prompts/{f.name}: 缺「## 信息缺口」节")
        else:
            if not INHERIT_LINK_RE.search(text):
                out.append(f"{rel}/prompts/{f.name}: 缺 ../../engine/report_templates/ 继承声明")
    return out


def check_templates(root: Path = ROOT) -> list[str]:
    """校验类型模板与泛用版命名。"""
    out: list[str] = []
    tdir = root / "engine" / "report_templates"
    files = sorted(set(tdir.glob("*/prompt*.md")) | set(tdir.glob("*/prompts/*.md")))
    for f in files:
        if f.parent.name == "prompts":
            if not PROMPT_NAME_RE.match(f.name):
                out.append(f"engine/report_templates/{f.parent.parent.name}/prompts/"
                           f"{f.name}: 命名不符 prompt-<kebab>.md")
        elif not TEMPLATE_NAME_RE.match(f.name):
            out.append(f"engine/report_templates/{f.parent.name}/{f.name}: "
                       f"命名不符 prompt-<kebab>-template.md")
    return out


def check(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    for b in iter_business_dirs():
        problems += check_business(b)
    problems += check_templates(root)
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="提示词命名/继承/结构/槽位门禁")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--warn", action="store_true", help="仅告警（退出码 2）")
    args = ap.parse_args(argv)

    problems = check()
    if args.json:
        print(json.dumps({"violations": len(problems), "problems": problems},
                         ensure_ascii=False, indent=2))
    else:
        print(f"提示词门禁：{len(problems)} 项违规")
        for p in problems:
            print(f"  - {p}")
    if problems:
        return 2 if args.warn else 1
    print("提示词门禁通过：命名/继承/结构/槽位一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
