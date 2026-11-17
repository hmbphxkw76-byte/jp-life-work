"""报告多层级信息校验（AuditGuard 体系）。

对每份真实报告执行 L1–L5 五层校验（见 docs/审计报告标准化管理体系.md 第四节）：
- L1 结构层：命名合规、md/html 配对、HTML 骨架（h2 节数 / 编号 / 锚点）、HTML lint；
- L2 要素层：报告必需要素 E1–E8 齐全；
- L3 溯源层：来源章节、事实段落来源标注覆盖率、失效引用；
- L4 一致性层：跨文档重复、登记册口径冲突、绝对化表述扫描；
- L5 语义层：人工 / LLM 复核清单（结论-依据匹配、表述一致、时效、以偏概全）。

**内嵌信息质量四维度**：L2–L4 直接调用 `info_quality_check.evaluate()`，把 C-01～C-14
发现按性质映射到审计层级，不重复实现判定逻辑。

用法：
    python audit_check.py --all           # 全量校验并写报告（audit-check-report.md/.json）
    python audit_check.py --report <path> # 单份校验（仓库相对路径）
    python audit_check.py --all --json    # 仅输出 JSON 到 stdout

退出码：0 = 全部 pass；1 = 存在 P0/P1；2 = 仅 P2。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    ROOT,
    detect_month_report,
    iter_business_dirs,
    link_prefix,
    md_table,
)
import compliance_check  # noqa: E402
import info_quality_check  # noqa: E402
from audit_registry import content_fingerprint  # noqa: E402
from info_quality_check import (  # noqa: E402
    THRESH_SOURCE_COVERAGE,
    fact_units,
    has_source,
)
from lint_reports import lint_html  # noqa: E402

AUDIT_DIR = ROOT / "engine" / "report-audits" / "audit"
CHECK_REPORT_MD = AUDIT_DIR / "audit-check-report.md"
CHECK_REPORT_JSON = AUDIT_DIR / "audit-check-report.json"
PENDING_P2 = AUDIT_DIR / "pending-p2.json"
P2_REVIEW_DAYS = 30
IQ_CACHE = ROOT / "engine" / "report-audits" / "info-quality" / "findings-by-path.json"
CACHE_VERSION = "1.1"   # IQ 缓存版本：读 / 写 / 键三者共用同一常量（配置唯一事实源）

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.DOTALL)
H2_RE = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.DOTALL)
# 绝对化措辞（语义确认后定级；此处仅提示）。排除否定语境与引述语境，避免误报。
ABSOLUTE_RE = re.compile(r"必过|包过|稳过|保证通过|一定通过|100%|绝对(?!值|收入|水平|优势)|必然会上涨|必定")
_ABS_NEG_CHARS = "不未无勿禁止不得拒绝非没有"
_ABS_QUOTE_CHARS = "「『“‘\"'"


def _absolute_hits(text: str) -> list[str]:
    """绝对化命中（排除否定 / 引述语境）。"""
    hits: list[str] = []
    for m in ABSOLUTE_RE.finditer(text):
        ctx = text[max(0, m.start() - 12):m.start()]
        if any(c in ctx for c in _ABS_NEG_CHARS):
            continue
        if any(c in ctx[-6:] for c in _ABS_QUOTE_CHARS):
            continue
        hits.append(m.group(0))
    return hits

# 信息质量 C-xx → 审计层级映射
C_TO_LAYER = {
    "C-01": "L5", "C-02": "L4", "C-03": "L4", "C-04": "L5",
    "C-05": "L2", "C-06": "L2", "C-07": "L3", "C-08": "L3",
    "C-09": "L3", "C-10": "L4", "C-11": "L5", "C-12": "L5",
    "C-13": "L4", "C-14": "L3",
}

L5_CHECKLIST = (
    "结论与依据是否匹配（关键结论有「事实→推理→结论」链）",
    "表述是否与来源原文含义一致（无夸大 / 曲解）",
    "关键信息是否在时效内、未被更新版本取代",
    "是否存在以偏概全 / 过度推断 / 绝对化表述",
    "口径并列是否清晰、未合并未取均值",
    "跨主题引用是否准确、无归属错误",
)


@dataclass
class AuditFinding:
    layer: str      # L1..L5
    code: str       # L1-NAME / E3 / C-06 / ABS-01
    severity: str   # P0/P1/P2
    report: str
    location: str
    detail: str
    spec: str = ""


@dataclass
class ReportResult:
    report: str
    topic: str
    period: str
    type_id: str
    layers: dict = field(default_factory=dict)   # layer -> pass/fail
    findings: list = field(default_factory=list) # AuditFinding
    l5_checklist: list = field(default_factory=list)

    @property
    def severity_counts(self) -> dict:
        c = {"P0": 0, "P1": 0, "P2": 0}
        for f in self.findings:
            c[f.severity] = c.get(f.severity, 0) + 1
        return c

    @property
    def passed(self) -> bool:
        return not any(f.severity in ("P0", "P1") for f in self.findings)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


# ──────────────────────────────────────────────
# L1 结构层
# ──────────────────────────────────────────────

def check_structure(rel: str, md_path: Path, html_path: Path, type_id: str) -> list[AuditFinding]:
    out: list[AuditFinding] = []

    # 命名合规
    det = detect_month_report(md_path.name)
    if not det:
        out.append(AuditFinding("L1", "L1-NAME", "P1", rel, "文件命名",
                                "不符合月度报告命名约定（YYYY-MM-<主题slug>）", "S-11"))
    else:
        topic_slug = md_path.parents[1].name
        slug = re.sub(r"^\d{2}-", "", topic_slug)
        if det[1] != slug:
            out.append(AuditFinding("L1", "L1-SLUG", "P1", rel, "文件命名",
                                    f"报告 slug「{det[1]}」与目录 slug「{slug}」不一致", "S-04"))

    # md/html 配对
    if not html_path.is_file():
        out.append(AuditFinding("L1", "L1-PAIR", "P1", rel, "文件配对",
                                "缺少同名 HTML 交付物", "S-05"))

    if not html_path.is_file():
        return out

    html = _read(html_path)
    # HTML lint
    for level, msg in lint_html(html):
        out.append(AuditFinding("L1", "L1-LINT", "P1" if level == "E" else "P2", rel,
                                "HTML lint", msg, "S-11"))
    # 标题
    t = TITLE_RE.search(html)
    if not t or not re.sub(r"<[^>]+>", "", t.group(1)).strip():
        out.append(AuditFinding("L1", "L1-TITLE", "P1", rel, "必填字段",
                                "缺少非空 <title>", "S-05"))
    # 顶部导航
    if not re.search(r'<nav\b[^>]*aria-label="报告导航"', html):
        out.append(AuditFinding("L1", "L1-NAV", "P1", rel, "必填字段",
                                "缺少顶部导航 <nav aria-label=\"报告导航\">", "S-05"))

    # 类型骨架
    if not type_id:
        out.append(AuditFinding("L1", "L1-TYPE", "P2", rel, "报告类型",
                                "business-config 未引用 report_templates/<类型ID>/，无法校验骨架", "S-05"))
        return out
    rules = compliance_check.load_rules()
    rule, _ = compliance_check.cycle_rule(rules, type_id, "monthly")
    if rule is None:
        out.append(AuditFinding("L1", "L1-TYPE", "P2", rel, "报告类型",
                                f"类型 {type_id} 未在 compliance-rules.json 登记", "S-05"))
        return out
    for level, msg in compliance_check.check_report(html, rule, rules.get("common", {})):
        out.append(AuditFinding("L1", "L1-SKELETON", "P1" if level == "E" else "P2", rel,
                                "类型骨架", f"[{type_id}/monthly] {msg}", "S-11"))
    return out


# ──────────────────────────────────────────────
# L2 要素层
# ──────────────────────────────────────────────

def check_elements(rel: str, md_path: Path, html_path: Path) -> list[AuditFinding]:
    out: list[AuditFinding] = []
    text = _read(md_path)
    html = _read(html_path) if html_path.is_file() else ""

    def add(code: str, sev: str, detail: str, spec: str = "S-05"):
        out.append(AuditFinding("L2", code, sev, rel, "必需要素", detail, spec))

    if not re.search(r"^#\s+\S", text, re.MULTILINE):
        add("E1", "P1", "缺少一级标题（含期间）")
    if not ("版本" in text and ("基准日" in text or "基准" in text)):
        add("E2", "P2", "缺少版本号 / 数据基准日标注")
    if not ("免责" in text or "不构成法律意见" in text):
        add("E3", "P1", "缺少免责声明")
    if not any(k in text for k in ("摘要", "核心结论", "结论先行", "执行摘要")):
        add("E4", "P1", "缺少结论摘要")
    if len(H2_RE.findall(html)) < 1:
        add("E5", "P1", "HTML 正文无 h2 章节（正文缺失或骨架不完整）")
    heads = re.findall(r"^#{1,6}\s+(.*)$", text, re.MULTILINE)
    if not any(("来源" in h or "参考" in h or "出处" in h) for h in heads):
        add("E6", "P1", "缺少「来源 / 参考来源」章节")
    if not any(k in text for k in ("观察", "触发", "后续", "待办", "下期")):
        add("E8", "P2", "缺少后续动作 / 观察清单")

    # E7 来源标注覆盖率（事实单元 = 段落 + 表格行）
    paras, rows = fact_units(text)
    fact_blocks = paras + rows
    if fact_blocks:
        cov = sum(1 for b in fact_blocks if has_source(b)) / len(fact_blocks)
        if cov < THRESH_SOURCE_COVERAGE:
            add("E7", "P2", f"事实单元来源标注覆盖率 {cov:.0%} < {THRESH_SOURCE_COVERAGE:.0%}", "S-06")
    return out


# ──────────────────────────────────────────────
# L4 一致性层（本地部分）
# ──────────────────────────────────────────────

def check_local_consistency(rel: str, md_path: Path) -> list[AuditFinding]:
    out: list[AuditFinding] = []
    text = _read(md_path)
    hits = _absolute_hits(text)
    if hits:
        out.append(AuditFinding("L4", "ABS-01", "P2", rel, "绝对化表述",
                                f"命中绝对化措辞 {len(hits)} 处（{', '.join(sorted(set(hits))[:5])}），"
                                "语义确认后定级", "S-10"))
    return out


# ──────────────────────────────────────────────
# 汇总：单份报告
# ──────────────────────────────────────────────

def check_report(rel: str, md_path: Path, html_path: Path, type_id: str,
                 iq_by_path: dict[str, list[AuditFinding]],
                 l5_status: dict[str, bool] | None = None) -> ReportResult:
    topic_dir = md_path.parents[1]
    det = detect_month_report(md_path.name)
    res = ReportResult(
        report=rel,
        topic=topic_dir.name,
        period=det[0] if det else "",
        type_id=type_id,
        l5_checklist=list(L5_CHECKLIST),
    )
    res.findings.extend(check_structure(rel, md_path, html_path, type_id))
    res.findings.extend(check_elements(rel, md_path, html_path))
    res.findings.extend(check_local_consistency(rel, md_path))
    res.findings.extend(iq_by_path.get(rel, []))
    for layer in ("L1", "L2", "L3", "L4", "L5"):
        ls = [f for f in res.findings if f.layer == layer]
        res.layers[layer] = "pass" if not any(f.severity in ("P0", "P1") for f in ls) else "fail"
    # L5 不由本地规则判定，而是从审计台账的复核证据派生（未填证据 = pending，非 pass）
    if l5_status is not None:
        if l5_status.get(rel, False):
            res.layers["L5"] = "pass"
        else:
            res.layers["L5"] = "pending"
            res.findings.append(AuditFinding(
                "L5", "L5-EVIDENCE", "P1", rel, "语义复核",
                "缺少有效 L5 语义复核证据（re_review --evidence / --backfill-l5，见 l5-semantic-review.md）", ""))
    return res


def _iq_findings_by_path() -> dict[str, list[AuditFinding]]:
    """运行信息质量四维度评估，把发现映射到审计层级并按报告路径归组。

    带内容哈希缓存：业务包全部 md 未变时直接复用，避免每次全量重算（去冗余）。
    """
    key = _iq_cache_key()
    if IQ_CACHE.is_file():
        try:
            data = json.loads(IQ_CACHE.read_text(encoding="utf-8"))
            if data.get("version") == CACHE_VERSION and data.get("key") == key:
                return {p: [AuditFinding(**d) for d in items]
                        for p, items in data.get("findings", {}).items()}
        except (json.JSONDecodeError, TypeError):
            pass

    units = info_quality_check.scan_topics()
    findings, _metrics = info_quality_check.evaluate(units)
    mapped: dict[str, list[dict]] = {}
    for f in findings:
        layer = C_TO_LAYER.get(f.code, "L5")
        mapped.setdefault(f.path, []).append({
            "layer": layer, "code": f.code, "severity": f.level,
            "report": f.path, "location": f.location,
            "detail": f"{f.detail}（信息质量四维度）", "spec": f.spec,
        })
    IQ_CACHE.parent.mkdir(parents=True, exist_ok=True)
    IQ_CACHE.write_text(json.dumps({"version": CACHE_VERSION, "key": key, "findings": mapped},
                                ensure_ascii=False, indent=2), encoding="utf-8")
    return {p: [AuditFinding(**d) for d in items] for p, items in mapped.items()}


def _hash_bytes(h: "hashlib._Hash", data: bytes) -> None:
    """写入哈希前统一换行符：检出配置差异（core.autocrlf）会让同一提交在
    不同工作区呈现 CRLF / LF 两种字节，若按原始字节哈希，缓存键会随检出
    环境漂移（同一份内容算出两个键），既让缓存永不命中、又使生成物反复变脏。"""
    h.update(data.replace(b"\r\n", b"\n"))


def _iq_cache_key() -> str:
    """全库内容哈希（业务主题下全部 md 的路径 + 内容指纹）+ 判定内核版本。"""
    h = hashlib.sha256()
    _hash_bytes(h, CACHE_VERSION.encode("utf-8"))
    try:
        _hash_bytes(h, Path(info_quality_check.__file__).read_bytes())
    except OSError:
        pass
    for b in iter_business_dirs():
        for md in sorted(b.path.rglob("*.md")):
            h.update(md.relative_to(ROOT).as_posix().encode("utf-8"))
            h.update(content_fingerprint(md).encode("utf-8"))
    return h.hexdigest()


def _l5_status() -> dict[str, bool]:
    """从审计台账派生 L5 状态（懒加载，避免与 audit_pipeline 循环依赖）。"""
    try:
        from audit_pipeline import l5_status_from_ledger
        return l5_status_from_ledger()
    except Exception:  # noqa: BLE001
        return {}


def run_all() -> tuple[list[ReportResult], dict]:
    """全量校验 -> (逐报告结果, 汇总)。"""
    iq = _iq_findings_by_path()
    l5 = _l5_status()
    results: list[ReportResult] = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        type_id = compliance_check.detect_type(
            _read(b.path / "prompts" / "business-config.md")
        ) if (b.path / "prompts" / "business-config.md").is_file() else ""
        for md in sorted(reports.glob("*.md")):
            rel = _rel(md)
            results.append(check_report(rel, md, md.with_suffix(".html"), type_id, iq, l5))
    results.sort(key=lambda r: r.report)

    summary: dict[str, Any] = {
        "reports": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "by_severity": {"P0": 0, "P1": 0, "P2": 0},
        "by_layer": {f"L{i}": {"pass": 0, "fail": 0, "pending": 0, "P0": 0, "P1": 0, "P2": 0}
                      for i in range(1, 6)},
    }
    for r in results:
        for k, v in r.severity_counts.items():
            summary["by_severity"][k] += v
        for layer, st in r.layers.items():
            summary["by_layer"][layer][st] += 1
        for f in r.findings:
            summary["by_layer"][f.layer][f.severity] += 1
    return results, summary


def write_pending_p2(results: list[ReportResult], run_date: str) -> list[dict]:
    """汇总 P2 发现到闭环台账（保留首次发现日期，更新最近发现与复核期限）。"""
    existing: dict = {}
    if PENDING_P2.is_file():
        try:
            old = json.loads(PENDING_P2.read_text(encoding="utf-8")).get("items", [])
            for e in old:
                existing[(e.get("report", ""), e.get("code", ""), e.get("location", ""))] = e
        except json.JSONDecodeError:
            existing = {}
    items: list[dict] = []
    for r in results:
        for f in r.findings:
            if f.severity != "P2":
                continue
            key = (r.report, f.code, f.location)
            prev = existing.get(key, {})
            first = prev.get("first_seen", run_date)
            items.append({
                "report": r.report, "code": f.code, "location": f.location,
                "detail": f.detail, "spec": f.spec,
                "first_seen": first, "last_seen": run_date,
                "review_by": (date.fromisoformat(first) + timedelta(days=P2_REVIEW_DAYS)).isoformat(),
            })
    payload = {"version": "1.0", "updated": run_date, "count": len(items), "items": items}
    PENDING_P2.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return items


def write_report(results: list[ReportResult], summary: dict, run_date: str) -> list[Path]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [["报告", "层级结论", "P0", "P1", "P2", "结论"]]
    prefix = link_prefix(CHECK_REPORT_MD)
    for r in results:
        c = r.severity_counts
        layers = " ".join(f"{k}{'✓' if v == 'pass' else ('?' if v == 'pending' else '✗')}"
                          for k, v in sorted(r.layers.items()))
        rows.append([f"[{r.report}]({prefix}{r.report})", layers, str(c["P0"]), str(c["P1"]),
                     str(c["P2"]), "通过" if r.passed else "不通过"])
    detail_rows = [["层级", "编号", "级别", "报告", "位置", "判定依据"]]
    for r in results:
        for f in sorted(r.findings, key=lambda x: (x.layer, x.severity, x.code)):
            detail_rows.append([f.layer, f.code, f.severity, r.report, f.location, f.detail])
    layer_rows = [[k, str(v["pass"]), str(v["fail"]), str(v.get("pending", 0)),
                   str(v["P0"]), str(v["P1"]), str(v["P2"])]
                  for k, v in sorted(summary["by_layer"].items())]
    if summary["failed"] == 0:
        conclusion = "全部通过"
    else:
        conclusion = f"{summary['failed']} 份报告存在 P0/P1，需修复后复评"

    md = "\n".join(
        [
            "# 报告多层级校验报告（AuditGuard）",
            "",
            f"> 校验日期：{run_date}　|　报告总数：{summary['reports']}　|　"
            f"通过 {summary['passed']} / 不通过 {summary['failed']}",
            "> 层级：L1 结构 / L2 要素 / L3 溯源 / L4 一致性 / L5 语义（清单）；"
            "判定内核内嵌信息质量四维度。",
            "",
            "## 逐报告结论",
            "",
            md_table(rows),
            "",
            "## 分层汇总",
            "",
            md_table([["层级", "pass", "fail", "pending", "P0", "P1", "P2"]] + layer_rows),
            "",
            "## 发现明细",
            "",
            md_table(detail_rows) if len(detail_rows) > 1 else "（无发现项）",
            "",
            "## L5 语义复核清单（人工 / LLM 逐项确认）",
            "",
        ]
        + [f"- [ ] {item}" for item in L5_CHECKLIST]
        + ["", f"**总体结论：{conclusion}**", ""]
    )
    p = CHECK_REPORT_MD
    p.write_text(md, encoding="utf-8")

    payload = {
        "run_date": run_date,
        "summary": summary,
        "results": [
            {
                "report": r.report, "topic": r.topic, "period": r.period,
                "type_id": r.type_id, "layers": r.layers,
                "severity": r.severity_counts, "passed": r.passed,
                "findings": [asdict(f) for f in r.findings],
                "l5_checklist": r.l5_checklist,
            }
            for r in results
        ],
    }
    pj = CHECK_REPORT_JSON
    pj.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return [p, pj]


def main() -> int:
    ap = argparse.ArgumentParser(description="报告多层级信息校验")
    ap.add_argument("--all", action="store_true", help="全量校验并写报告")
    ap.add_argument("--report", help="单份校验（仓库相对路径）")
    ap.add_argument("--json", action="store_true", help="结果输出到 stdout（JSON）")
    args = ap.parse_args()

    if args.report:
        rel = args.report.replace("\\", "/")
        md = ROOT / rel
        if not md.is_file():
            print(f"[ERROR] 报告不存在：{rel}")
            return 1
        html = md.with_suffix(".html")
        type_id = ""
        cfg = md.parents[1] / "prompts" / "business-config.md"
        if cfg.is_file():
            type_id = compliance_check.detect_type(_read(cfg)) or ""
        iq = _iq_findings_by_path()
        res = check_report(rel, md, html, type_id, iq, _l5_status())
        if args.json:
            print(json.dumps({"result": asdict(res)}, ensure_ascii=False, indent=2))
        else:
            c = res.severity_counts
            print(f"{rel}：{'通过' if res.passed else '不通过'}"
                  f"（P0 {c['P0']} / P1 {c['P1']} / P2 {c['P2']}）")
            for f in sorted(res.findings, key=lambda x: (x.layer, x.severity)):
                print(f"  [{f.layer}/{f.severity}] {f.code} {f.location}：{f.detail}")
        sc = res.severity_counts
        if sc["P0"] or sc["P1"]:
            return 1
        return 2 if sc["P2"] else 0

    if args.all:
        results, summary = run_all()
        if args.json:
            print(json.dumps({
                "summary": summary,
                "results": [{"report": r.report, "passed": r.passed,
                             "severity": r.severity_counts,
                             "findings": [asdict(f) for f in r.findings]} for r in results],
            }, ensure_ascii=False, indent=2))
        else:
            paths = write_report(results, summary, date.today().isoformat())
            p2 = write_pending_p2(results, date.today().isoformat())
            print(f"  P2 闭环台账：{len(p2)} 项 → {PENDING_P2.relative_to(ROOT)}")
            print(f"多层级校验：{summary['reports']} 份报告，"
                  f"通过 {summary['passed']} / 不通过 {summary['failed']}")
            print(f"  P0 {summary['by_severity']['P0']} / "
                  f"P1 {summary['by_severity']['P1']} / P2 {summary['by_severity']['P2']}")
            for r in results:
                if not r.passed:
                    print(f"  [FAIL] {r.report}："
                          + "; ".join(f"{f.layer}/{f.code}" for f in r.findings
                                      if f.severity in ("P0", "P1")))
            print("  报告已写入：" + ", ".join(_rel(p) for p in paths))
        if summary["by_severity"]["P0"] or summary["by_severity"]["P1"]:
            return 1
        if summary["by_severity"]["P2"]:
            return 2
        return 0

    ap.print_help()
    return 0

# ── 公开接口别名（架构优化方向 F / I-6）──
absolute_hits = _absolute_hits
iq_findings_by_path = _iq_findings_by_path
l5_status = _l5_status
rel = _rel


if __name__ == "__main__":
    sys.exit(main())
