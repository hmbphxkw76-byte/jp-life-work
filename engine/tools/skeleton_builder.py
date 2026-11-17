"""报告骨架构建与空模块合并（骨架瘦身）。

能力：
1. `build_skeleton(topic, mode)`：由 business-config + 登记册生成报告骨架；
   - `mode="full"`：完整九节 / 固化锚全量，逐节「（待补）」；
   - `mode="compact"`：紧凑版，空模块合并为单一「待补模块」区块，只保留骨架与边界声明。
2. `merge_empty_modules(text)`：对**已存在报告**合并连续空 h2 模块（无实质内容），
   收敛为单个「待补模块（合并）」区块，减少骨架冗余。

所有模块边界声明集中到「零、模块边界声明」单独章节（含 / 不含 / 口径）。

用法：
    python engine/tools/skeleton_builder.py --topic 14-life-operations --mode compact
    python engine/tools/skeleton_builder.py --topic 15-health-wellbeing --mode full --out reports/2026-12-x.md
    python engine/tools/skeleton_builder.py --merge <report.md> [--apply]

退出码：0 = 成功；1 = 失败；2 = --check 不一致 / 有告警。
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import iter_business_dirs, topic_slug  # noqa: E402

DEFAULT_SECTIONS = [
    "一、核心结论（摘要）",
    "二、行业与政策发展趋势",
    "三、人才供需与薪酬（核心模块）",
    "四、雇主与企业类型细分",
    "五、岗位技能要求",
    "六、行业认可的职业资质与证书",
    "七、就业落地路径建议（结论章）",
    "八、数据可靠性与局限说明",
    "九、参考来源清单",
]

DISCLAIMER = ("> **免责声明**：本报告为信息整理与条件化建议，不构成法律意见或税务意见；"
              "重大决策请咨询执业法律 / 税务专业人士。")


def _find_topic(topic: str):
    for b in iter_business_dirs():
        if b.rel == topic or topic_slug(b.region) == topic:
            return b
    return None


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _section(text: str, keyword: str) -> str:
    """提取标题含 keyword 的小节正文（到下一同级 / 更高级标题）。"""
    m = re.search(rf"^#{{1,3}}\s+[^\n]*{keyword}[^\n]*\n(.*?)(?=^#{{1,3}}\s+|\Z)",
                  text, re.S | re.M)
    return m.group(1) if m else ""


def _extract_boundary(cfg: str) -> tuple[list[str], list[str], list[str]]:
    """从 business-config 提取「含 / 不含 / 口径」声明。"""
    inc: list[str] = []
    exc: list[str] = []
    cal: list[str] = []

    # 含：**含**： 之后的 bullet 行
    m = re.search(r"\*\*含\*\*[：:]\s*\n((?:\s*[-*]\s+.+\n)+)", cfg)
    if m:
        inc = [re.sub(r"^\s*[-*]\s+", "", ln).strip() for ln in m.group(1).splitlines() if ln.strip()]

    # 不含：**不含** 行之后的表格（允许空行）
    m = re.search(r"\*\*不含\*\*[^\n]*\n(?:\s*\n)?((?:\|.+\|\s*\n)+)", cfg)
    if m:
        for ln in m.group(1).splitlines():
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0] not in ("主题", "---", ""):
                exc.append(f"{cells[0]} → {cells[1]}")

    # 口径：取「口径清单 / 口径冲突」小节内的表格行与 bullet
    sec = _section(cfg, "口径")
    for ln in sec.splitlines():
        s = ln.strip()
        if not s.startswith(("|", "-", "*")):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")] if s.startswith("|") else [s.lstrip("-* ")]
        if s.startswith("|"):
            if len(cells) >= 2 and cells[0] not in ("口径", "指标", "---", ""):
                cal.append(" ≠ ".join(cells[:2]) if len(cells) > 2 else " | ".join(cells[:2]))
        elif cells and cells[0]:
            cal.append(cells[0])
    return inc, exc, cal


def _extract_sections(cfg: str) -> list[str]:
    """从「结构固化锚」表提取现行章节标题；缺失时回退九节骨架。"""
    secs: list[str] = []
    m = re.search(r"结构固化锚[^\n]*\n((?:\|.+\|\s*\n)+)", cfg)
    if m:
        for ln in m.group(1).splitlines():
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0] and cells[0] not in ("现行章节", "九节骨架", "---"):
                secs.append(cells[0])
    return secs or list(DEFAULT_SECTIONS)


def _extract_type(cfg: str) -> str:
    m = re.search(r"engine/report_templates/([a-z][a-z0-9-]*)/", cfg)
    return m.group(1) if m else ""


def build_skeleton(topic: str, mode: str = "full", period: str = "") -> str:
    """生成报告骨架。mode ∈ {full, compact}。"""
    b = _find_topic(topic)
    if b is None:
        raise SystemExit(f"[ERROR] 未找到主题: {topic}")
    cfg = _read(b.path / "prompts" / "business-config.md")
    name = next((ln[2:].strip() for ln in cfg.splitlines() if ln.startswith("# ")), b.rel)
    name = re.sub(r"\s*[·|].*$", "", name).strip() or b.rel
    type_id = _extract_type(cfg)
    inc, exc, cal = _extract_boundary(cfg)
    sections = _extract_sections(cfg)
    period = period or date.today().strftime("%Y-%m")

    lines: list[str] = []
    lines.append(f"# {name} · {period} 月度报告（骨架）")
    lines.append("")
    lines.append(DISCLAIMER)
    lines.append("")
    lines.append(f"> **版本**：v0.1（骨架）　**数据基准日**：{period}-14　**主题类型**：{type_id or '—'}")
    lines.append("> **模块边界声明**：见第零节（集中声明，不在各节重复）。")
    lines.append("")
    lines.append("---")
    lines.append("")
    # 零、模块边界声明
    lines.append("## 零、模块边界声明")
    lines.append("")
    lines.append("**含**：")
    for x in inc:
        lines.append(f"- {x}")
    lines.append("")
    lines.append("**不含（交叉引用）**：")
    for x in exc:
        lines.append(f"- {x}")
    lines.append("")
    if cal:
        lines.append("**口径**：")
        for x in cal[:8]:
            lines.append(f"- {x}")
        lines.append("")

    if mode == "compact":
        # 紧凑版：空模块合并为一个「待补模块」区块
        lines.append("## 一、核心结论（摘要）")
        lines.append("")
        lines.append("（待补）")
        lines.append("")
        lines.append("## 待补模块（合并）")
        lines.append("")
        lines.append("以下模块本期无实质内容，合并占位，后续周期按需展开：")
        lines.append("")
        for s in sections[1:]:
            lines.append(f"- {s}（待补）")
        lines.append("")
    else:
        for s in sections:
            lines.append(f"## {s}")
            lines.append("")
            lines.append("（待补）")
            lines.append("")
    return "\n".join(lines)


def merge_empty_modules(text: str) -> tuple[str, int]:
    """合并报告中连续空 h2 模块 -> (新文本, 合并数)。

    空模块 = 标题与下一标题之间无实质内容。连续空模块收敛为单个
    「待补模块（合并）」区块，保留首个标题作为锚。
    """
    lines = text.splitlines()
    heads = [i for i, ln in enumerate(lines) if re.match(r"^##\s+", ln)]
    if not heads:
        return text, 0
    empty_flags: list[bool] = []
    for idx, start in enumerate(heads):
        end = heads[idx + 1] if idx + 1 < len(heads) else len(lines)
        content = [ln for ln in lines[start + 1:end] if ln.strip() and not ln.strip().startswith("#")]
        empty_flags.append(not content)

    out: list[str] = []
    i = 0
    merged = 0
    while i < len(heads):
        start = heads[i]
        if not empty_flags[i]:
            end = heads[i + 1] if i + 1 < len(heads) else len(lines)
            out.extend(lines[start:end])
            i += 1
            continue
        # 连续空模块
        j = i
        while j < len(heads) and empty_flags[j]:
            j += 1
        block = lines[heads[i]:heads[j]]
        # 保留首个标题，替换为合并区块
        first_title = re.sub(r"^##\s+", "", block[0]).strip()
        out.append("## 待补模块（合并）")
        out.append("")
        out.append(f"以下模块无实质内容，合并占位：{first_title} 等 {j - i} 节。")
        out.append("")
        merged += (j - i - 1)
        i = j
    # 尾部（最后一个标题之后已在循环内处理）
    return "\n".join(out), merged


def main() -> int:
    ap = argparse.ArgumentParser(description="报告骨架构建与空模块合并")
    ap.add_argument("--topic", default="14-life-operations")
    ap.add_argument("--mode", choices=["full", "compact"], default="full")
    ap.add_argument("--period", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--merge", default="", help="对已存在报告合并空模块")
    ap.add_argument("--apply", action="store_true", help="--merge 时写回文件")
    args = ap.parse_args()

    if args.merge:
        p = Path(args.merge)
        if not p.exists():
            print(f"[ERROR] 文件不存在: {p}")
            return 1
        new, n = merge_empty_modules(_read(p))
        if args.apply:
            p.write_text(new, encoding="utf-8")
            print(f"已合并空模块 {n} 节：{p}")
            return 0
        print(f"可合并空模块 {n} 节（--apply 写回）")
        return 0

    try:
        skeleton = build_skeleton(args.topic, args.mode, args.period)
    except SystemExit as e:
        print(str(e))
        return 1
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(skeleton, encoding="utf-8")
        print(f"骨架已生成：{out}")
    else:
        print(skeleton)
    return 0


if __name__ == "__main__":
    sys.exit(main())
