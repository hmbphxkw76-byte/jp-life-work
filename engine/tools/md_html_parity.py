#!/usr/bin/env python3
"""md_html_parity.py — md 源稿 ↔ 同名 HTML 交付物一致性门禁（P1-3）。

HTML 是 md 的确定性派生物（md2html.py 幂等）。本工具重新渲染每份 md 源稿，
与仓库中已提交的 HTML 逐字节比对，用于阻断「改了 md 未同步 HTML」或
「HTML 被手工改动」造成的漂移。

判定：
  - OK       渲染结果与提交 HTML 一致；
  - MISSING  存在 md 源稿但缺同名 HTML（漏生成）；
  - MISMATCH 渲染结果与提交 HTML 不一致（漂移，阻断）。

归一化：仅统一换行（CRLF/CR → LF）；其余差异一律视为漂移——报告 HTML 必须
与 md 渲染结果逐字节一致（CI 在 ubuntu、本地在 Windows 均如此）。

用法：
    python engine/tools/md_html_parity.py            # 全量校验，漂移则退出码 1
    python engine/tools/md_html_parity.py --report <路径>   # 单份校验
    python engine/tools/md_html_parity.py --json
    python engine/tools/md_html_parity.py --warn     # 仅告警（退出码 2）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT  # noqa: E402
from md2html import collect_md_reports, convert  # noqa: E402


def _normalize(text: str) -> str:
    """统一换行；其余保持原样（报告 HTML 必须逐字节可复现）。"""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def check_report(md_path: Path) -> dict:
    """校验单份 md 与其 HTML 交付物。"""
    rel = md_path.relative_to(ROOT).as_posix()
    html_path = md_path.with_suffix(".html")
    if not html_path.is_file():
        return {"path": rel, "status": "MISSING", "detail": "缺同名 HTML"}
    try:
        rendered = _normalize(convert(md_path))
    except Exception as e:  # noqa: BLE001
        return {"path": rel, "status": "ERROR", "detail": f"渲染失败：{e}"}
    committed = _normalize(html_path.read_text(encoding="utf-8", errors="replace"))
    if rendered == committed:
        return {"path": rel, "status": "OK", "detail": ""}
    # 给出首个差异位置，便于定位。
    idx = next((i for i, (a, b) in enumerate(zip(rendered, committed, strict=False)) if a != b),
               min(len(rendered), len(committed)))
    snippet = rendered[idx:idx + 60].replace("\n", "\\n")
    return {"path": rel, "status": "MISMATCH",
            "detail": f"首处差异 @{idx}：渲染={snippet!r}…"}


def check(root: Path = ROOT) -> list[dict]:
    return [check_report(md) for md in collect_md_reports()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="md ↔ HTML 一致性门禁")
    ap.add_argument("--report", help="单份 md 路径（仓库相对或绝对）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--warn", action="store_true", help="仅告警（退出码 2）")
    args = ap.parse_args(argv)

    if args.report:
        p = Path(args.report)
        if not p.is_absolute():
            p = ROOT / p
        if p.suffix != ".md":
            p = p.with_suffix(".md")
        results = [check_report(p)]
    else:
        results = check()

    bad = [r for r in results if r["status"] != "OK"]
    counts = {s: sum(1 for r in results if r["status"] == s)
              for s in ("OK", "MISSING", "MISMATCH", "ERROR")}
    if args.json:
        print(json.dumps({"reports": results, "counts": counts,
                          "violations": len(bad)}, ensure_ascii=False, indent=2))
    else:
        scope = "单份" if args.report else f"{len(results)} 份"
        print(f"md↔html 一致性：{scope}报告，OK={counts['OK']} "
              f"MISSING={counts['MISSING']} MISMATCH={counts['MISMATCH']} "
              f"ERROR={counts['ERROR']}")
        for r in bad:
            print(f"  - {r['path']}: {r['status']} {r['detail']}")
    if bad:
        return 2 if args.warn else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
