#!/usr/bin/env python3
"""verified_content_gate.py — 无法核实内容硬门禁（默认全层零容忍）。

把「无法核实的内容一律删除」的做法固化为可机读门禁：**任何层级**出现
无法核实标记即阻断——正文、置信度表、信息差与未核验清单、待复核清单、
登记册核验状态列、`source-backlog.md`、词库版本记录等一并覆盖。
`--content-only` 可回退到「仅内容层」（豁免记录层章节 / 状态列 / 清单 / 行级豁免）。

单一事实源：``engine/config/verified-content-policy.json``
（markers / record_sections / status_columns / excluded_files / excluded_lines）。

判定单元：内容层的行（正文 / bullet / 表格行非状态列）。
退出码：0=通过；1=存在命中（阻断）；2=仅告警（``--warn``）。

用法：
    python engine/tools/verified_content_gate.py --all
    python engine/tools/verified_content_gate.py --changed --base origin/main
    python engine/tools/verified_content_gate.py --report 01-ssw-driver/reports/2026-11-ssw-driver.md
    python engine/tools/verified_content_gate.py --all --json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, iter_business_dirs  # noqa: E402

POLICY_PATH = ROOT / "engine" / "config" / "verified-content-policy.json"
POLICY_SCHEMA = "1.0"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}[\s|:-]*$")


class PolicyError(ValueError):
    pass


def load_policy() -> dict:
    """读取门禁策略（缺失 / 损坏 / schema 不符即抛 PolicyError）。"""
    try:
        data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PolicyError(f"门禁策略缺失：{POLICY_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyError(f"门禁策略损坏（非合法 JSON）：{POLICY_PATH}") from exc
    if data.get("schema") != POLICY_SCHEMA:
        raise PolicyError(f"门禁策略 schema 不符：{data.get('schema')!r}（应为 {POLICY_SCHEMA}）")
    for key in ("markers", "record_sections", "status_columns", "excluded_files", "excluded_lines"):
        if key not in data:
            raise PolicyError(f"门禁策略缺字段：{key}")
    return data


def kind_of(rel: str) -> str:
    """按相对路径判定文件类型（决定记录层规则集）。"""
    if "/reports/" in rel:
        return "report"
    if "/handbook/" in rel:
        return "handbook"
    if rel.startswith("engine/vocabulary/data/") and rel.endswith("terms.md"):
        return "vocab"
    if "/data/" in rel:
        return "registry"
    return "other"


def iter_targets() -> list[tuple[str, str]]:
    """全部受检文件：(相对路径, 类型)。"""
    out: list[tuple[str, str]] = []
    for b in iter_business_dirs():
        for sub, kind in (("reports", "report"), ("handbook", "handbook"), ("data", "registry")):
            d = b.path / sub
            if not d.is_dir():
                continue
            for md in sorted(d.glob("*.md")):
                out.append((md.relative_to(ROOT).as_posix(), kind))
    vd = ROOT / "engine" / "vocabulary" / "data"
    if vd.is_dir():
        for md in sorted(vd.glob("*/terms.md")):
            out.append((md.relative_to(ROOT).as_posix(), "vocab"))
    return out


def split_row(line: str) -> list[str]:
    """表格行 → 单元格列表（去首尾空单元格）。"""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def compute_status_columns(lines: list[str], status_cols: set[str]) -> dict[int, set[int]]:
    """行号（1 基）→ 该表的状态列下标集合。

    识别表头行（下一行为分隔行），把表头名命中 ``status_cols`` 的列记为状态列，
    应用到该表后续数据行。
    """
    out: dict[int, set[int]] = {}
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.lstrip().startswith("|") and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
            header = split_row(line)
            cols = {j for j, name in enumerate(header) if name in status_cols}
            j = i + 2
            while j < n and lines[j].lstrip().startswith("|"):
                out[j + 1] = cols  # 行号 1 基
                j += 1
            i = j
        else:
            i += 1
    return out


def scan_text(text: str, kind: str, policy: dict) -> list[dict]:
    """扫描文本 → 命中列表（行号 / 行文本 / 命中标记）。

    标记 / 记录层 / 行级豁免均为**字面量子串**匹配（策略文件不写正则，避免转义歧义）。
    """
    markers = list(policy["markers"])
    rec_pats = list(policy["record_sections"].get(kind, []))
    ex_pats = list(policy["excluded_lines"])
    status_cols = set(policy["status_columns"])
    lines = text.splitlines()
    status_map = compute_status_columns(lines, status_cols)

    hits: list[dict] = []
    stack: list[tuple[int, str]] = []  # (level, title)
    for idx, line in enumerate(lines, start=1):
        m = HEADING_RE.match(line)
        if m:
            lvl = len(m.group(1))
            title = m.group(2)
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            stack.append((lvl, title))
            continue
        if any(p in line for p in ex_pats):
            continue
        if any(p in title for _, title in stack for p in rec_pats):
            continue
        matched = [mk for mk in markers if mk in line]
        if not matched:
            continue
        # 表格行：若命中仅落在状态列，则放行
        cols = status_map.get(idx)
        if cols:
            cells = split_row(line)
            in_content = any(
                mk in cells[j]
                for mk in markers
                for j in range(len(cells))
                if j not in cols
            )
            if not in_content:
                continue
        hits.append({"line": idx, "text": line.strip()[:200], "markers": matched})
    return hits


def collect_targets(args, policy: dict) -> list[tuple[str, str]]:
    """按参数确定受检范围。"""
    excluded = set(policy["excluded_files"])
    all_targets = iter_targets()
    if args.report:
        rel = args.report.replace("\\", "/")
        kind = kind_of(rel)
        return [(rel, kind)]
    if args.changed:
        base = args.base or "origin/main"
        try:
            names = subprocess.run(
                ["git", "diff", "--name-only", f"{base}...HEAD"],
                cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout.splitlines()
        except subprocess.CalledProcessError as exc:
            raise PolicyError(f"git diff 失败：{exc.stderr.strip()}") from exc
        want = {n.replace("\\", "/") for n in names if n.endswith(".md")}
        return [(rel, kind) for rel, kind in all_targets if rel in want]
    return [(rel, kind) for rel, kind in all_targets if Path(rel).name not in excluded]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="无法核实内容硬门禁（内容层零容忍）")
    ap.add_argument("--all", action="store_true", help="全量扫描")
    ap.add_argument("--changed", action="store_true", help="仅扫相对 --base 的变更报告")
    ap.add_argument("--base", help="增量基点（默认 origin/main）")
    ap.add_argument("--report", help="单份报告（仓库相对路径）")
    ap.add_argument("--json", action="store_true", help="结果输出为 JSON")
    ap.add_argument("--warn", action="store_true", help="命中仅告警（退出码 2）")
    ap.add_argument("--content-only", action="store_true",
                    help="仅内容层：豁免记录层章节 / 状态列 / 清单 / 行级豁免（默认全层零容忍）")
    args = ap.parse_args(argv)

    try:
        policy = load_policy()
    except PolicyError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if not args.content_only:
        # 默认全层零容忍：记录层（置信度表 / 信息差与未核验清单 / 核验状态列 /
        # source-backlog / 版本记录等）亦不得出现未核实标记。
        policy = {
            **policy,
            "record_sections": {k: [] for k in policy["record_sections"]},
            "status_columns": [],
            "excluded_files": [],
            "excluded_lines": [],
        }

    targets = collect_targets(args, policy)
    results: list[dict] = []
    for rel, kind in targets:
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = scan_text(text, kind, policy)
        if hits:
            results.append({"report": rel, "kind": kind, "hits": hits})

    total = sum(len(r["hits"]) for r in results)
    if args.json:
        print(json.dumps({"total": total, "files": results}, ensure_ascii=False, indent=2))
    else:
        mode = "内容层零容忍" if args.content_only else "全层零容忍"
        print(f"无法核实内容门禁：受检 {len(targets)} 份，命中 {total} 处（{mode}）")
        for r in results:
            print(f"  [{r['kind']}] {r['report']}：{len(r['hits'])} 处")
            for h in r["hits"]:
                print(f"    L{h['line']}: {h['text']}")

    if not results:
        return 0
    return 2 if args.warn else 1


if __name__ == "__main__":
    sys.exit(main())
