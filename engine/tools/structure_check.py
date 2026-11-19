#!/usr/bin/env python3
"""structure_check.py — 报告必需要素结构门禁（信息差 / 质量可靠 / 决策支撑）。

两部分：
1. 报告必需要素：每份报告（md 源稿）是否具备四大必需要素（h2 级）；
2. 主题骨架完备性：已配 `prompts/business-config.md` 的主题须有 `handbook/`，
   或在 `engine/vocabulary/config/skeleton-exemptions.json` 显式豁免；空骨架不占位。

1. 数据可靠性与局限说明（允许变体：数据治理与局限 / 数据缺口与未核验 / 风险、局限）
2. 置信度标注（分级码说明或置信度表）
3. 信息差与未核验清单（允许变体：缺失清单 / 信息差）
4. 决策建议（允许变体：建议章 / 结论章 / 观察清单 / 决策框架）

分级口径见 ``engine/report_templates/confidence-grade-standard.md``（来源 S/A/B/C ×
时效 新/中/旧 × 核验 已核验/部分核验/待核实 → 两位分级码）。

用法：
    python engine/tools/structure_check.py            # 全量校验，缺失则退出码 1
    python engine/tools/structure_check.py --report <路径>   # 单份校验
    python engine/tools/structure_check.py --json
    python engine/tools/structure_check.py --warn     # 仅告警（退出码 2）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 必需要素：key -> (展示名, 命中任一关键词即视为具备；匹配范围为报告全部 h2 标题)
REQUIRED: dict[str, tuple[str, tuple[str, ...]]] = {
    "reliability": ("数据可靠性与局限说明", ("数据可靠性与局限",)),
    "confidence": ("置信度标注", ("置信度", "置信")),
    "gap": ("信息差与未核验清单", ("信息差", "缺失清单", "未核验清单")),
    "decision": ("决策建议", ("建议", "结论章", "观察清单", "决策框架", "结论")),
}

_H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# 骨架豁免清单（W1 / A5）：已配 business-config 但无 handbook 的主题须显式声明。
SKELETON_EXEMPT_CONFIG = ROOT / "engine" / "vocabulary" / "config" / "skeleton-exemptions.json"


def _titles(text: str) -> list[str]:
    return [m.group(1).strip() for m in _H2.finditer(text)]


def missing_elements(text: str) -> list[str]:
    """返回缺失要素的 key 列表（按 REQUIRED 顺序）。"""
    joined = "\n".join(_titles(text))
    return [k for k, (_, kws) in REQUIRED.items() if not any(kw in joined for kw in kws)]


def check_report(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    missing = missing_elements(text)
    return {"path": path.relative_to(ROOT).as_posix(), "missing": missing}


def check(root: Path = ROOT) -> list[dict]:
    out = []
    for f in sorted(root.glob("*/reports/*.md")):
        out.append(check_report(f))
    return out


def skeleton_exemptions() -> dict[str, str]:
    """读取骨架豁免清单 -> {topic: reason}；缺失 / 损坏时为空（不抛错）。"""
    try:
        data = json.loads(SKELETON_EXEMPT_CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {
        e.get("topic"): e.get("reason", "")
        for e in data.get("exemptions", [])
        if e.get("topic")
    }


def check_skeleton(root: Path = ROOT) -> list[dict]:
    """主题骨架完备性：已配 business-config 的主题须有 handbook/ 或显式豁免。

    返回违规项 [{"topic", "missing": "handbook/"}]；空骨架（无 business-config）不占位。
    """
    from _common import iter_business_dirs

    exempt = skeleton_exemptions()
    issues = []
    for b in iter_business_dirs():
        cfg = b.path / "prompts" / "business-config.md"
        if not cfg.exists():
            continue
        if (b.path / "handbook").is_dir():
            continue
        if b.rel in exempt:
            continue
        issues.append({"topic": b.rel, "missing": "handbook/"})
    return issues


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="报告必需要素结构校验")
    ap.add_argument("--report", help="单份报告路径（仓库相对或绝对）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--warn", action="store_true", help="仅告警（退出码 2）")
    args = ap.parse_args(argv)

    if args.report:
        p = Path(args.report)
        if not p.is_absolute():
            p = ROOT / p
        results = [check_report(p)]
    else:
        results = check()

    bad = [r for r in results if r["missing"]]
    skeleton = check_skeleton()
    if args.json:
        print(json.dumps({"reports": results, "violations": len(bad),
                          "skeleton": skeleton, "skeleton_violations": len(skeleton)},
                         ensure_ascii=False, indent=2))
    else:
        scope = "单份" if args.report else f"{len(results)} 份"
        print(f"结构校验：{scope}报告，{len(bad)} 份缺必需要素；"
              f"骨架 {len(skeleton)} 个主题缺 handbook")
        for r in bad:
            labels = [REQUIRED[k][0] for k in r["missing"]]
            print(f"  - {r['path']}: 缺 {', '.join(labels)}")
        for r in skeleton:
            print(f"  - {r['topic']}: 缺 {r['missing']}")
    if bad or skeleton:
        return 2 if args.warn else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
