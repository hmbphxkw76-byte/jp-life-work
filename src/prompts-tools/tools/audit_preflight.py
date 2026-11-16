"""落盘前快速自检（AuditGuard 左移预防层）。

定位：报告落盘后、提交审计前的快速本地检查。复用 `audit_check` / `info_quality_check`
的判定函数与常量，不新写判定规则；覆盖单份可判定的结构 / 要素 / 溯源 / 一致性项，
并追加前置增强项（口径标注、登记册指针）。跨主题判定（C-01 冲突、C-03 跨文档重复、
C-10 口径冲突）不在本层——由 `audit_check` 与周度 `info_quality_check` 承载。

本层无网络依赖、不读跨主题全库，单份检查为毫秒级，可嵌入生成提示词由生成者自助执行。

用法：
    python audit_preflight.py --report <相对路径>   # 单份
    python audit_preflight.py --all                 # 全量并写报告
    python audit_preflight.py --all --json          # 结果输出到 stdout

退出码：0=通过；1=存在 P0/P1；2=仅 P2。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, detect_month_report, iter_business_dirs  # noqa: E402
import compliance_check  # noqa: E402
import info_quality_check  # noqa: E402
from info_quality_check import (  # noqa: E402
    MD_LINK_RE,
    THRESH_SOURCE_COVERAGE,
    fact_units,
    has_source,
)
from audit_check import ABSOLUTE_RE, H2_RE, absolute_hits  # noqa: E402
from lint_reports import lint_html  # noqa: E402

AUDIT_DIR = ROOT / "src" / "report-audits" / "audit"
REPORT_MD = AUDIT_DIR / "preflight-report.md"
REPORT_JSON = AUDIT_DIR / "preflight-report.json"

P_LEVELS = {"P0": 0, "P1": 1, "P2": 2}
MD_HEAD_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
MD_H2_RE = re.compile(r"^##\s+", re.MULTILINE)
REG_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|", re.MULTILINE)
REG_PTR_RE = re.compile(r"(?:([0-9]{2}-[a-z][a-z0-9-]*)\s+)?登记册\s*((?:#\d+\s*[、/,，–\-]?\s*)+)")
REG_NUM_RE = re.compile(r"#(\d+)")


@dataclass
class Finding:
    """一条落盘前检查发现。"""

    code: str       # PF-NAME / PF-E3 / PF-ABS / PF-CITE / PF-REG ...
    severity: str   # P0/P1/P2
    location: str
    detail: str
    spec: str = ""


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def severity_counts(findings: list[Finding]) -> dict:
    c = {"P0": 0, "P1": 0, "P2": 0}
    for f in findings:
        c[f.severity] = c.get(f.severity, 0) + 1
    return c


def _add(out: list[Finding], code: str, sev: str, loc: str, detail: str, spec: str = "") -> None:
    out.append(Finding(code, sev, loc, detail, spec))


# ──────────────────────────────────────────────
# 纯函数：对给定文本执行检查（可测试，不读文件）
# ──────────────────────────────────────────────

def check_text(rel: str, text: str, html: str = "", type_id: str = "",
               registry_text: str = "") -> list[Finding]:
    """对单份报告文本执行落盘前检查。

    rel          仓库相对路径（用于命名/slug 与相对链接解析）
    text         md 源稿全文
    html         同名 HTML 全文（缺失时跳过 HTML 相关检查）
    type_id      报告类型（解析自 business-config；空则跳过骨架校验）
    registry_text 主题登记册全文（空则跳过登记册指针校验）
    """
    out: list[Finding] = []
    md_path = ROOT / rel
    slug_dir = re.sub(r"^\d{2}-", "", md_path.parents[1].name) if len(md_path.parents) > 1 else ""

    # ── 结构：命名与 slug ──
    det = detect_month_report(md_path.name)
    if not det:
        _add(out, "PF-NAME", "P1", "文件命名",
             "不符合月度命名约定（YYYY-MM-<主题slug>）", "S-11")
    elif slug_dir and det[1] != slug_dir:
        _add(out, "PF-NAME", "P1", "文件命名",
             f"报告 slug「{det[1]}」与目录 slug「{slug_dir}」不一致", "S-04")

    # ── 文件配对 ──
    if not html:
        _add(out, "PF-PAIR", "P2", "文件配对",
             "缺少同名 HTML 交付物（落盘后运行 md2html.py 同步）", "S-05")

    # ── 必需要素 E1–E8 ──
    if not re.search(r"^#\s+\S", text, re.MULTILINE):
        _add(out, "PF-E1", "P1", "必需要素", "缺少一级标题（含期间）", "S-05")
    if not ("版本" in text and ("基准日" in text or "基准" in text)):
        _add(out, "PF-E2", "P2", "必需要素", "缺少版本号 / 数据基准日标注", "S-05")
    if not ("免责" in text or "不构成法律意见" in text):
        _add(out, "PF-E3", "P1", "必需要素", "缺少免责声明", "S-05")
    if not any(k in text for k in ("摘要", "核心结论", "结论先行", "执行摘要")):
        _add(out, "PF-E4", "P1", "必需要素", "缺少结论摘要", "S-05")

    heads = MD_HEAD_RE.findall(text)
    if not any(("来源" in h or "参考" in h or "出处" in h) for h in heads):
        _add(out, "PF-E6", "P1", "必需要素", "缺少「来源 / 参考来源」章节", "S-06")

    h2_html = len(H2_RE.findall(html)) if html else 0
    h2_md = len(MD_H2_RE.findall(text))
    if h2_html < 1 and h2_md < 1:
        _add(out, "PF-E5", "P1", "必需要素", "正文无章节（h2 缺失）", "S-05")

    paras, rows = fact_units(text)
    fact_blocks = paras + rows
    if fact_blocks:
        cov = sum(1 for b in fact_blocks if has_source(b)) / len(fact_blocks)
        if cov < THRESH_SOURCE_COVERAGE:
            _add(out, "PF-E7", "P2", "事实单元来源覆盖不足",
                 f"含数字事实单元（段落 + 表格行）来源覆盖率 {cov:.0%} < {THRESH_SOURCE_COVERAGE:.0%}", "S-06")

    if not any(k in text for k in ("观察", "触发", "后续", "待办", "下期")):
        _add(out, "PF-E8", "P2", "必需要素", "缺少后续动作 / 观察清单", "S-05")

    # ── 一致性：绝对化表述 ──
    hits = absolute_hits(text)
    if hits:
        _add(out, "PF-ABS", "P2", "绝对化表述",
             f"命中绝对化措辞 {len(hits)} 处（{', '.join(sorted(set(hits))[:5])}），语义确认后定级", "S-10")

    # ── 前置增强：口径标注 ──
    if not ("口径" in text or "基准" in text):
        _add(out, "PF-CALIBER", "P2", "口径标注", "缺少口径说明 / 数据基准标注", "S-09")

    # ── 一致性：失效相对引用（C-09 子集） ──
    for target in MD_LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        tok = target.split()[0] if target.split() else ""
        raw = re.split(r"[）)]", tok)[0].strip()
        if not raw or "{{" in raw or "<" in raw:
            continue
        path_part = raw.split("#")[0]
        if not path_part:
            continue
        if not (md_path.parent / path_part).resolve().exists():
            _add(out, "PF-CITE", "P2", "交叉引用", f"引用目标不存在：{raw}", "S-08")

    # ── 前置增强：登记册指针 ──
    if registry_text:
        nums: set[int] = set()
        for m in REG_PTR_RE.finditer(text):
            ls = text.rfind("\n", 0, m.start()) + 1
            le = text.find("\n", m.end())
            line = text[ls: le if le != -1 else len(text)]
            # 同行出现其它主题目录 token → 跨主题只读锚，不在本主题登记册校验
            cross = [t for t in re.findall(r"\b(\d{2}-[a-z][a-z0-9-]*)\b", line)
                     if slug_dir and t != slug_dir]
            if cross:
                continue
            nums.update(int(x) for x in REG_NUM_RE.findall(m.group(2)))
        if nums:
            valid = {int(x) for x in REG_ROW_RE.findall(registry_text)}
            missing = sorted(nums - valid)
            if missing:
                _add(out, "PF-REG", "P2", "登记册指针",
                     f"引用登记册 {', '.join('#' + str(n) for n in missing)} 在登记册中不存在", "S-08")

    # ── 结构：类型骨架与 HTML lint（仅有 HTML 时） ──
    if html:
        if not type_id:
            _add(out, "PF-SKELETON", "P2", "类型骨架",
                 "business-config 未引用 report_templates/<类型ID>/，无法校验骨架", "S-05")
        else:
            rules = compliance_check.load_rules()
            rule, _ = compliance_check.cycle_rule(rules, type_id, "monthly")
            if rule is None:
                _add(out, "PF-SKELETON", "P2", "类型骨架",
                     f"类型 {type_id} 未在 compliance-rules.json 登记", "S-05")
            else:
                for level, msg in compliance_check.check_report(html, rule, rules.get("common", {})):
                    _add(out, "PF-SKELETON", "P1" if level == "E" else "P2",
                         "类型骨架", f"[{type_id}/monthly] {msg}", "S-11")
        for level, msg in lint_html(html):
            _add(out, "PF-LINT", "P1" if level == "E" else "P2", "HTML lint", msg, "S-11")

    return out


# ──────────────────────────────────────────────
# 文件读取封装
# ──────────────────────────────────────────────

def check_report(rel: str) -> list[Finding]:
    """读取仓库内单份报告及其 HTML / 业务配置 / 登记册，执行检查。"""
    md = ROOT / rel
    text = _read(md)
    html_path = md.with_suffix(".html")
    html = _read(html_path) if html_path.is_file() else ""

    cfg = md.parents[1] / "prompts" / "business-config.md"
    type_id = compliance_check.detect_type(_read(cfg)) if cfg.is_file() else ""

    registry_text = ""
    data_dir = md.parents[1] / "data"
    if data_dir.is_dir():
        for f in sorted(data_dir.glob("*.md")):
            if "registry" in f.name:
                registry_text = _read(f)
                break

    return check_text(rel, text, html, type_id or "", registry_text)


def run_all() -> tuple[list[dict], dict]:
    """全量检查全部业务主题下的 reports/*.md。"""
    results: list[dict] = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        for md in sorted(reports.glob("*.md")):
            rel = _rel(md)
            findings = check_report(rel)
            results.append({
                "report": rel,
                "topic": b.rel,
                "findings": findings,
                "severity": severity_counts(findings),
                "passed": not any(f.severity in ("P0", "P1") for f in findings),
            })
    results.sort(key=lambda r: r["report"])
    summary = {
        "reports": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "by_severity": {"P0": 0, "P1": 0, "P2": 0},
    }
    for r in results:
        for k, v in r["severity"].items():
            summary["by_severity"][k] += v
    return results, summary


def _md_table(rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def _link_prefix(out_file: Path) -> str:
    """从产物文件回到仓库根的相对前缀。"""
    return "../" * (len(out_file.relative_to(ROOT).parts) - 1)


def write_report(results: list[dict], summary: dict, run_date: str) -> list[Path]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [["报告", "P0", "P1", "P2", "结论"]]
    prefix = _link_prefix(REPORT_MD)
    for r in results:
        c = r["severity"]
        rows.append([f"[{r['report']}]({prefix}{r['report']})",
                     str(c["P0"]), str(c["P1"]), str(c["P2"]),
                     "通过" if r["passed"] else "不通过"])
    detail = [["编号", "级别", "报告", "位置", "判定依据"]]
    for r in results:
        for f in sorted(r["findings"], key=lambda x: (P_LEVELS.get(x.severity, 9), x.code)):
            detail.append([f.code, f.severity, r["report"], f.location, f.detail])
    conclusion = "全部通过" if summary["failed"] == 0 else f"{summary['failed']} 份报告存在 P0/P1，需修正后复检"

    md = "\n".join([
        "# 落盘前自检报告（AuditGuard Preflight）",
        "",
        f"> 检查日期：{run_date}　|　报告总数：{summary['reports']}　|　"
        f"通过 {summary['passed']} / 不通过 {summary['failed']}",
        "> 定位：提交审计前的快速本地检查；判定复用信息质量四维度与 audit_check。",
        "",
        "## 逐报告结论",
        "",
        _md_table(rows),
        "",
        "## 发现明细",
        "",
        _md_table(detail) if len(detail) > 1 else "（无发现项）",
        "",
        f"**总体结论：{conclusion}**",
        "",
    ])
    p = REPORT_MD
    p.write_text(md, encoding="utf-8")

    payload = {
        "run_date": run_date,
        "summary": summary,
        "results": [
            {
                "report": r["report"], "topic": r["topic"],
                "severity": r["severity"], "passed": r["passed"],
                "findings": [asdict(f) for f in r["findings"]],
            }
            for r in results
        ],
    }
    pj = REPORT_JSON
    pj.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return [p, pj]


def main() -> int:
    ap = argparse.ArgumentParser(description="落盘前快速自检（左移预防层）")
    ap.add_argument("--report", help="单份报告（仓库相对路径）")
    ap.add_argument("--all", action="store_true", help="全量检查并写报告")
    ap.add_argument("--json", action="store_true", help="结果输出到 stdout（JSON）")
    args = ap.parse_args()

    if args.report:
        rel = args.report.replace("\\", "/")
        if not (ROOT / rel).is_file():
            print(f"[ERROR] 报告不存在：{rel}", file=sys.stderr)
            return 1
        findings = check_report(rel)
        c = severity_counts(findings)
        if args.json:
            print(json.dumps({"report": rel, "severity": c,
                              "findings": [asdict(f) for f in findings]},
                             ensure_ascii=False, indent=2))
        else:
            print(f"{rel}：{'通过' if not any(f.severity in ('P0','P1') for f in findings) else '不通过'}"
                  f"（P0 {c['P0']} / P1 {c['P1']} / P2 {c['P2']}）")
            for f in sorted(findings, key=lambda x: (P_LEVELS.get(x.severity, 9), x.code)):
                print(f"  [{f.severity}] {f.code} {f.location}：{f.detail}")
        if c["P0"] or c["P1"]:
            return 1
        return 2 if c["P2"] else 0

    if args.all:
        results, summary = run_all()
        if args.json:
            print(json.dumps({
                "summary": summary,
                "results": [{"report": r["report"], "passed": r["passed"],
                             "severity": r["severity"],
                             "findings": [asdict(f) for f in r["findings"]]} for r in results],
            }, ensure_ascii=False, indent=2))
        else:
            paths = write_report(results, summary, date.today().isoformat())
            print(f"落盘前自检：{summary['reports']} 份报告，"
                  f"通过 {summary['passed']} / 不通过 {summary['failed']}")
            print(f"  P0 {summary['by_severity']['P0']} / "
                  f"P1 {summary['by_severity']['P1']} / P2 {summary['by_severity']['P2']}")
            for r in results:
                if not r["passed"]:
                    print(f"  [FAIL] {r['report']}："
                          + "; ".join(f.code for f in r["findings"]
                                      if f.severity in ("P0", "P1")))
            print("  报告已写入：" + ", ".join(_rel(p) for p in paths))
        if summary["by_severity"]["P0"] or summary["by_severity"]["P1"]:
            return 1
        return 2 if summary["by_severity"]["P2"] else 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
