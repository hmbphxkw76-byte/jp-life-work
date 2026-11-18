#!/usr/bin/env python3
"""link_check.py — 仓库内链存在性校验（内部链接门禁）。

扫描会「活」引用仓库相对路径的载体，逐一验证目标文件是否存在：

- 主题：`*/prompts/business-config.md`、`*/operations-guide.md`、`*/data/*.md`、`*/reports/*.md`
- 汇总：`index.html`、`search-index.json`
- 搜索：`engine/search/*.json`
- 文档：`docs/*.md`

提取来源：
- Markdown 链接 `[文字](path)`（跳过 http(s) / `#anchor` / `mailto:` / 含 `{{` 模板）
- JSON 字符串值中形如仓库相对路径（以 `.md` / `.html` 结尾）
- HTML `href="..."`（跳过 http(s) / `#`）

历史迁移留痕（`engine/report-audits/report-migration-*`）不参与校验。

用法：
    python engine/tools/link_check.py            # 校验，缺失则退出码 1
    python engine/tools/link_check.py --json     # 机器可读输出
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 参与扫描的载体（相对 ROOT）
GLOBS = [
    "*/prompts/business-config.md",
    "*/operations-guide.md",
    "*/data/*.md",
    "*/reports/*.md",
    "docs/*.md",
    "engine/search/*.json",
    "index.html",
    "search-index.json",
]

SKIP_PREFIXES = ("engine/report-audits/report-migration-",)

_MD_LINK = re.compile(r"\]\(([^)\s]+)\)")
_HREF = re.compile(r'href="([^"]+)"')
_JSON_PATH = re.compile(r"^[0-9A-Za-z_\-]+/.+\.(md|html)$")


def _is_external(p: str) -> bool:
    return p.startswith(("http://", "https://", "#", "mailto:", "tel:"))


def _looks_like_path(p: str) -> bool:
    return p.endswith((".md", ".html")) or "/" in p


def _candidates(text: str, is_json: bool, is_html: bool) -> set[str]:
    out: set[str] = set()
    if is_json:
        try:
            data = json.loads(text)
        except ValueError:
            data = None
        if data is not None:
            stack = [data]
            while stack:
                cur = stack.pop()
                if isinstance(cur, str):
                    if _JSON_PATH.match(cur):
                        out.add(cur)
                elif isinstance(cur, list):
                    stack.extend(cur)
                elif isinstance(cur, dict):
                    stack.extend(cur.values())
    if is_html:
        for m in _HREF.finditer(text):
            out.add(m.group(1))
    for m in _MD_LINK.finditer(text):
        out.add(m.group(1))
    return out


def _check_audit_status(root: Path) -> list[str]:
    """audit-status.json 的键为报告路径，须指向实际存在的文件。"""
    f = root / "engine/report-audits/audit/audit-status.json"
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out: list[str] = []
    for key in (data.get("reports") or {}):
        if not (root / key).exists():
            out.append(key)
    return sorted(out)


def check(root: Path = ROOT) -> list[str]:
    """返回缺失的仓库相对路径（去重、排序）。"""
    missing: set[str] = set()
    for pattern in GLOBS:
        for f in sorted(root.glob(pattern)):
            rel = f.relative_to(root).as_posix()
            if any(rel.startswith(p) for p in SKIP_PREFIXES):
                continue
            is_json = f.suffix == ".json"
            is_html = f.suffix == ".html"
            text = f.read_text(encoding="utf-8", errors="replace")
            for cand in _candidates(text, is_json, is_html):
                cand = cand.split("#", 1)[0]
                if not cand or _is_external(cand) or "{{" in cand:
                    continue
                if not _looks_like_path(cand):
                    continue
                # JSON / HTML 内的路径为仓库根相对；Markdown 链接为文件相对
                base_dir = root if (is_json or is_html) else f.parent
                target = (base_dir / cand).resolve()
                try:
                    rel_target = target.relative_to(root).as_posix()
                except ValueError:
                    continue  # 指向仓库外，不在内链校验范围
                if not target.exists():
                    missing.add(rel_target)
    missing.update(_check_audit_status(root))
    return sorted(missing)


def main() -> int:
    ap = argparse.ArgumentParser(description="仓库内链存在性校验")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    missing = check()
    if args.json:
        print(json.dumps({"missing": missing, "count": len(missing)},
                         ensure_ascii=False, indent=2))
    elif missing:
        print(f"[ERROR] 发现 {len(missing)} 个失效内链：")
        for p in missing:
            print(f"  - {p}")
    else:
        print("内链校验通过：无失效引用")

    if missing:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
