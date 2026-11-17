"""存量报告迁移到月度命名规范（2026-11 体系重构）。

背景：取消基线 / 初析 / 季度等报告类型标签，全部报告按自然月份聚合，统一命名
「YYYY-MM-<主题slug>」。同一主题同一自然月的多份存量报告合并为一份月度报告：
以「初析报告」为主体，其余（基线等）作为附录保留，**不删改任何原文内容**。

归属规则：
- 基线　`2026-11_baseline_report.md`　　　-> 2026-11，附录
- 初析　`2026-11-13_initial_analysis_report.md` -> 2026-11，主体
- 季度　`2026-Q4_quarterly.md`　　　　　　-> 2026-12（季度末月），主体
- 专题　`2026-11-13_landing_checklist.md`　-> 2026-11，主体（清单类）
- 专题　`2026-11-13_settlement_profile.md` -> 2026-11，附录（档案类）
- 其余历史命名（monthly / annual / weekly / special）按同类规则归入自然月

产物：
- `<主题>/reports/YYYY-MM-<slug>.md` + 同名 `.html`（md2html 重新生成）
- `engine/report-audits/report-migration-2026-11.json`（机器可读迁移清单）
- `engine/report-audits/report-migration-2026-11.md`（人读迁移报告）

用法：
    python engine/tools/migrate_monthly_reports.py --check   # 试跑
    python engine/tools/migrate_monthly_reports.py --apply   # 执行

退出码：0 = 成功；1 = 存在无法归类的报告或写入失败；2 = --check 发现待迁移项。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    detect_legacy_report,
    iter_business_dirs,
    month_report_name,
    quarter_to_month,
    topic_slug,
)

AUDIT_DIR = Path(__file__).resolve().parents[1] / "report-audits"
MANIFEST_JSON = AUDIT_DIR / "report-migration-2026-11.json"
MANIFEST_MD = AUDIT_DIR / "report-migration-2026-11.md"

# 角色：main = 月度报告主体；appendix = 附录（原文保留）
MAIN_KINDS = {"initial", "monthly", "quarterly", "annual"}


def role_of(kind: str, name: str) -> str:
    """判定存量报告在合并中的角色。"""
    if kind == "special":
        # 清单 / 执行类作主体，档案 / 模板类作附录
        return "main" if any(w in name for w in ("checklist", "清单")) else "appendix"
    if kind in MAIN_KINDS:
        return "main"
    return "appendix"


def month_of(kind: str, period: str) -> str:
    """历史报告周期 -> 自然月标识（季度 / 年度取末月）。"""
    if kind in ("quarterly",):
        return quarter_to_month(period) or period
    if kind == "annual":
        return f"{period}-12"
    if kind in ("monthly", "baseline"):
        return period
    # initial / weekly / special：period 为 ISO 日期，取月前
    return period[:7]


def demote_headings(text: str, levels: int = 1) -> str:
    """把 markdown 标题降 N 级（跳过围栏代码块），用于附录融入主报告。"""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence:
            m = re.match(r"^(#{1,6})(\s.*)$", line)
            if m:
                hashes = "#" * min(len(m.group(1)) + levels, 6)
                line = hashes + m.group(2)
        out.append(line)
    return "\n".join(out)


def first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def normalize(text: str) -> str:
    """归一化文本（去空白 / 换行差异 / markdown 标题标记），用于内容留存校验。

    附录融入时标题会降级（新增 `#`），故标题标记不参与留存判定；其余文字
    （含表格 / 列表 / 代码）必须逐字保留。
    """
    text = re.sub(r"(?m)^\s{0,3}#+\s?", "", text)
    return re.sub(r"\s+", "", text)


def build_merge(sources: list[dict]) -> tuple[str, list[dict]]:
    """把同一月的多份报告合并为一份月度报告 -> (markdown, 附录记录)。

    sources: [{name, kind, period, text, role}]，至少一份。
    """
    mains = [s for s in sources if s["role"] == "main"]
    appendices = [s for s in sources if s["role"] == "appendix"]
    if not mains:
        # 无主体时按文件名升序把第一份提升为主体
        sources = sorted(sources, key=lambda s: s["name"])
        mains = [sources[0]]
        appendices = sources[1:]

    body = mains[0]["text"].rstrip()
    notes = []
    for s in appendices:
        title = first_heading(s["text"]) or s["name"]
        note = "以下为原报告《{}》（{}）全文，作为附录保留，内容未删改。".format(title, s["name"])
        notes.append({"source": s["name"], "kind": s["kind"], "title": title})
        body += "\n\n---\n\n> **附录说明**：" + note + "\n\n" + demote_headings(s["text"].strip(), 1)
    return body.strip() + "\n", notes


def collect_topic_sources(b) -> list[dict]:
    """扫描一条业务线的 reports/*.md，返回待迁移来源列表。"""
    reports = b.path / "reports"
    if not reports.is_dir():
        return []
    slug = topic_slug(b.region if not b.property_type else b.property_type)
    out = []
    for f in sorted(reports.glob("*.md")):
        det = detect_legacy_report(f.name)
        if not det:
            continue
        kind, period, _ = det
        out.append(
            {
                "name": f.name,
                "path": f,
                "kind": kind,
                "period": period,
                "month": month_of(kind, period),
                "role": role_of(kind, f.name),
                "slug": slug,
                "text": f.read_text(encoding="utf-8"),
            }
        )
    return out


def plan() -> tuple[dict, list[str]]:
    """全仓扫描 -> {slug: {month: {target, sources:[...], target_rel}}}。"""
    plan_map: dict[str, dict[str, dict]] = {}
    unknown: list[str] = []
    for b in iter_business_dirs():
        sources = collect_topic_sources(b)
        for s in sources:
            if not re.fullmatch(r"\d{4}-\d{2}", s["month"]):
                unknown.append(f"{b.rel}/reports/{s['name']}")
                continue
            slug = s["slug"]
            slot = plan_map.setdefault(slug, {}).setdefault(
                s["month"],
                {"target": month_report_name(s["month"], slug), "sources": []},
            )
            slot["sources"].append(s)
    return plan_map, unknown


def render_manifest(plan_map: dict, results: list[dict]) -> str:
    lines = [
        "# 存量报告迁移清单（2026-11 月度体系重构）",
        "",
        "> 自动生成，请勿手工编辑。由 `engine/tools/migrate_monthly_reports.py` 产出。",
        "",
        "## 一、迁移规则",
        "",
        "- 全部报告按自然月份聚合，统一命名 `YYYY-MM-<主题slug>.md` + 同名 `.html`。",
        "- 取消基线 / 初析 / 季度等类型标签；季度报告按季度末月归档（如 2026-Q4 → 2026-12）。",
        "- 同月多份报告合并为一份：初析为主体，基线等作为附录，原文内容未删改。",
        "- HTML 由 `md2html.py` 依据合并后 md 重新生成，与 md 源一致。",
        "",
        "## 二、迁移明细",
        "",
        "| 主题 | 目标月 | 目标文件 | 来源文件 | 角色 | 内容校验 |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        mark = "✅ 原文已收录" if r["content_preserved"] else "❌ 内容缺失"
        lines.append(
            f"| {r['slug']} | {r['month']} | `{r['target']}` | `{r['source']}` | {r['role']} | {mark} |"
        )
    lines += [
        "",
        "## 三、内容留存校验",
        "",
        "每份存量报告的归一化全文（去空白）均作为子串出现在目标文件中，"
        "脚本在 --apply 时逐份校验，任一缺失即报错退出。",
        "",
        f"- 迁移报告总数：{len(results)}",
        f"- 全部通过内容留存校验：{'是' if all(r['content_preserved'] for r in results) else '否'}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="存量报告迁移到月度命名规范")
    ap.add_argument("--check", action="store_true", help="试跑：只报告待迁移项")
    ap.add_argument("--apply", action="store_true", help="执行迁移")
    args = ap.parse_args()

    plan_map, unknown = plan()
    if unknown:
        for u in unknown:
            print(f"[UNKNOWN] {u}: 无法归入自然月，需人工处理")
        if not args.apply:
            return 1

    total = sum(len(slot["sources"]) for months in plan_map.values() for slot in months.values())
    print(f"待迁移报告：{total} 份，覆盖 {len(plan_map)} 个主题")

    if args.check:
        for slug in sorted(plan_map):
            for month in sorted(plan_map[slug], reverse=True):
                slot = plan_map[slug][month]
                srcs = ", ".join(s["name"] for s in slot["sources"])
                print(f"[PLAN] {slug} {month} -> {slot['target']}  <- {srcs}")
        print("（--check 试跑，未写入任何文件）")
        return 2 if total else 0

    if not args.apply:
        print("请指定 --check 或 --apply")
        return 2

    # 延迟导入 md2html，避免其依赖在 --check 时也强制加载
    import md2html

    results: list[dict] = []
    for slug in sorted(plan_map):
        brel = slug_to_rel(slug)
        for month in sorted(plan_map[slug], reverse=True):
            slot = plan_map[slug][month]
            target_name = slot["target"]
            sources = slot["sources"]
            merged, _notes = build_merge(sources)

            # 内容留存校验：每份来源的归一化全文必须出现在合并结果中
            norm_merged = normalize(merged)
            preserved = True
            for s in sources:
                ok = normalize(s["text"]) in norm_merged
                results.append(
                    {
                        "slug": slug,
                        "month": month,
                        "target": f"{brel}/reports/{target_name}",
                        "source": s["name"],
                        "role": s["role"],
                        "kind": s["kind"],
                        "content_preserved": ok,
                    }
                )
                preserved = preserved and ok
            if not preserved:
                print(f"[ERROR] {target_name}: 内容留存校验失败，中止迁移")
                return 1

            out_md = Path(brel) / "reports" / target_name
            out_html = out_md.with_suffix(".html")
            try:
                out_md.write_text(merged, encoding="utf-8")
                out_html.write_text(md2html.convert(out_md), encoding="utf-8")
            except OSError as e:
                print(f"[ERROR] 写入失败 {out_md}: {e}")
                return 1

            # 删除存量 md + html
            for s in sources:
                for ext in ("md", "html"):
                    old = s["path"].with_suffix(f".{ext}")
                    if old.exists():
                        old.unlink()
                        print(f"[MOVED] {old} -> {out_md.name}")

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_JSON.write_text(
        json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    MANIFEST_MD.write_text(render_manifest(plan_map, results), encoding="utf-8")
    print(f"迁移完成：{len(results)} 份来源已并入 {total and sum(len(m) for m in plan_map.values())} 份月度报告")
    print(f"迁移清单：{MANIFEST_MD}")
    return 0


def slug_to_rel(slug: str) -> str:
    """主题 slug -> 业务目录相对路径（遍历业务线反查）。"""
    for b in iter_business_dirs():
        if topic_slug(b.region if not b.property_type else b.property_type) == slug:
            return b.rel
    return ""


if __name__ == "__main__":
    sys.exit(main())
