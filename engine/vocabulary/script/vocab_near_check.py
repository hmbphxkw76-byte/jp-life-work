#!/usr/bin/env python3
"""vocab_near_check.py — 词库近义 / 近重复词条扫描（P2-6）。

扫描各主题 `terms.md` 的词条与别名，检出**疑似近义 / 近重复**对，产出机读清单
供人工裁定合并（合并流程见 `docs/词库近义合并规范.md`）。

判定（命中即列为疑似）：
- 包含：一条是另一条的子串（长度 ≥ 2）。

> 不采用编辑距离类规则：会把「大型 / 中型」这类反义对误报为近义，不符合「可合并」口径。

用法：
    python engine/vocabulary/script/vocab_near_check.py            # 扫描并写清单
    python engine/vocabulary/script/vocab_near_check.py --check    # 不写文件
    python engine/vocabulary/script/vocab_near_check.py --json

输出：`engine/vocabulary/data/near-dup-report.json`（不入库）。
退出码：0=无疑似；1=扫描失败；2=存在疑似对（需人工裁定）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VOCAB_DATA = ROOT / "engine" / "vocabulary" / "data"
OUT = VOCAB_DATA / "near-dup-report.json"

MIN_LEN_SUBSTR = 2


def _similar(a: str, b: str) -> str:
    """返回命中原因（空串表示不相似）。

    仅采用**包含关系**：编辑距离类规则会把「大型 / 中型」这类反义对误报为近义，
    不符合「可合并」口径；同尾前缀是包含关系的加强确认。
    """
    if not a or not b:
        return ""
    if a == b:
        return "完全相同"
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    if len(short) >= MIN_LEN_SUBSTR and short in long:
        return "包含关系"
    return ""


def _terms(path: Path) -> list[tuple[str, str]]:
    """解析 terms.md → [(词条, 别名)]（与 build_hub._load_vocab_terms 同口径）。"""
    out: list[tuple[str, str]] = []
    if not path.is_file():
        return out
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.startswith("| ") or ln.count("|") < 6:
            continue
        cells = [c.strip() for c in ln.split("|")]
        if len(cells) < 5:
            continue
        term = cells[2]
        if not term or term in ("词条", "---"):
            continue
        out.append((term, cells[3]))
    return out


def scan() -> list[dict]:
    """全主题扫描，返回疑似对列表（按主题、词条排序）。"""
    pairs: list[dict] = []
    if not VOCAB_DATA.is_dir():
        return pairs
    for f in sorted(VOCAB_DATA.glob("*/terms.md")):
        topic = f.parent.name
        entries = _terms(f)
        # 仅比较规范词条（canonical）：别名已归一到词条，别名两两比较属噪声。
        surface = [(term, "词条", term) for term, _alias in entries]
        for i in range(len(surface)):
            for j in range(i + 1, len(surface)):
                ta, ka, oa = surface[i]
                tb, kb, ob = surface[j]
                reason = _similar(ta, tb)
                if reason:
                    pairs.append({"topic": topic, "a": ta, "a_kind": ka, "a_term": oa,
                                  "b": tb, "b_kind": kb, "b_term": ob, "reason": reason})
    pairs.sort(key=lambda p: (p["topic"], p["a"], p["b"]))
    return pairs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="词库近义 / 近重复词条扫描")
    ap.add_argument("--check", action="store_true", help="不写文件")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    pairs = scan()
    if args.json:
        print(json.dumps({"count": len(pairs), "pairs": pairs}, ensure_ascii=False, indent=2))
    else:
        print(f"近义扫描：{len(pairs)} 对疑似")
        for p in pairs[:40]:
            print(f"  [{p['topic']}] {p['a']}({p['a_kind']}) ~ {p['b']}({p['b_kind']})：{p['reason']}")
        if not args.check:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps({"count": len(pairs), "pairs": pairs},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"已写入：{OUT.relative_to(ROOT)}")
    if pairs:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
