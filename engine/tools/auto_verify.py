"""报告生成后自动验证编排层（AutoVerify）。

定位：报告 md 生成 / md2html 转换完成之后，自动执行预设规则集并驱动后续流程，
      是「生成 → 验证 → 写回 → 提交审计」端到端无人值守的编排入口。

规则集（V1–V5，全部复用既有判定内核，不新造规则）：
    V1 交付物与文件可访问   md/html 存在、可读、非空；命名 slug 与目录一致；
                            html 缺失时自动调用 md2html 补齐
    V2 必填字段与要素       复用 audit_preflight.check_text（E1–E8 / 命名 / 口径 /
                            引用 / 登记册指针 / 绝对化）
    V3 格式合规             复用 compliance_check（类型骨架）+ lint_reports（HTML）
    V4 数据准确性与一致性   复用 audit_check（L3/L4 + 信息质量四维度，含 C-13
                            报告↔登记册数值一致性）
    V5 关键指标数值范围     登记册活值 ↔ 报告「数据变更摘要」数值覆盖比对

行为：
    - 通过（无 P0/P1）→ 把验证结果幂等写入报告「## 自动验证结果」章节 → 重新生成
      HTML → 复核 → 自动 audit_pipeline --submit
    - 失败（任一 P0/P1）→ 退出码 1，打印逐条定位（规则 / 位置 / 详情），不写回、不提交
    - 日志：engine/report-audits/audit/verify/<report-stem>.json

用法：
    python auto_verify.py --report <仓库相对路径> [--dry-run] [--no-submit] [--json]
    python auto_verify.py --all [--dry-run] [--no-submit]

退出码：0=通过（可含 P2）；1=存在 P0/P1 或文件不可访问；2=参数 / 环境错误。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_check  # noqa: E402
import audit_preflight  # noqa: E402
import compliance_check  # noqa: E402
import info_quality_check  # noqa: E402
import lint_reports  # noqa: E402
import md2html  # noqa: E402
from _common import ROOT, atomic_write, detect_month_report, iter_business_dirs, resolve_within  # noqa: E402
from info_quality_check import live_table, read as iq_read, report_value_rows, significant_numbers  # noqa: E402

BASE_DATE_RE = re.compile(r"数据基准日\**\s*[:：]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})")

TOOL_VERSION = "1.0"
RULES_DIR = ROOT / "engine" / "report-audits" / "audit" / "verify"

BLOCK_START = "<!-- AUTO-VERIFY:START -->"
BLOCK_END = "<!-- AUTO-VERIFY:END -->"
BLOCK_RE = re.compile(re.escape(BLOCK_START) + r".*?" + re.escape(BLOCK_END), re.DOTALL)

P_LEVELS = {"P0": 0, "P1": 1, "P2": 2}
V2_CODES = {"PF-NAME", "PF-PAIR", "PF-E1", "PF-E2", "PF-E3", "PF-E4", "PF-E5",
            "PF-E6", "PF-E7", "PF-E8", "PF-ABS", "PF-CALIBER", "PF-CITE", "PF-REG"}


@dataclass
class RuleResult:
    """单条规则的验证结果。"""

    id: str
    name: str
    status: str          # pass / warn / fail
    findings: list[dict] = field(default_factory=list)
    detail: str = ""

    def counts(self) -> dict:
        c = {"P0": 0, "P1": 0, "P2": 0}
        for f in self.findings:
            c[f.get("severity", "P2")] = c.get(f.get("severity", "P2"), 0) + 1
        return c


@dataclass
class VerifyResult:
    """单份报告的自动验证结果。"""

    report: str
    run_at: str
    base_date: str = "—"
    rules: list[RuleResult] = field(default_factory=list)
    actions: dict = field(default_factory=dict)

    def counts(self) -> dict:
        c = {"P0": 0, "P1": 0, "P2": 0}
        for r in self.rules:
            for k, v in r.counts().items():
                c[k] += v
        return c

    @property
    def passed(self) -> bool:
        c = self.counts()
        return c["P0"] == 0 and c["P1"] == 0

    @property
    def log_path(self) -> Path:
        return RULES_DIR / (Path(self.report).stem + ".json")


# ──────────────────────────────────────────────
# 工具
# ──────────────────────────────────────────────

def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _finding_dict(f) -> dict:
    """把各层 Finding（dataclass 或 dict）统一成可序列化 dict。"""
    if isinstance(f, dict):
        return {k: f.get(k, "") for k in ("code", "severity", "layer", "location", "detail", "spec")}
    return {
        "code": getattr(f, "code", ""),
        "severity": getattr(f, "severity", ""),
        "layer": getattr(f, "layer", ""),
        "location": getattr(f, "location", ""),
        "detail": getattr(f, "detail", ""),
        "spec": getattr(f, "spec", ""),
    }


def _severity_rank(sev: str) -> int:
    return P_LEVELS.get(sev, 2)


def _registry_of(md_path: Path) -> Path | None:
    data_dir = md_path.parents[1] / "data"
    if not data_dir.is_dir():
        return None
    for f in sorted(data_dir.glob("*.md")):
        if "registry" in f.name:
            return f
    return None


# ──────────────────────────────────────────────
# 规则实现
# ──────────────────────────────────────────────

def rule_v1_deliverables(rel: str, md_path: Path, html_path: Path) -> tuple[RuleResult, bool]:
    """V1 交付物与文件可访问；返回（结果, html 是否由本规则补齐）。"""
    findings: list[dict] = []
    regenerated = False
    if not md_path.is_file():
        findings.append({"code": "V1-MD", "severity": "P0", "layer": "V1",
                         "location": "交付物", "detail": f"报告源稿不存在：{rel}", "spec": "S-05"})
    elif md_path.stat().st_size == 0:
        findings.append({"code": "V1-MD", "severity": "P0", "layer": "V1",
                         "location": "交付物", "detail": "报告源稿为空文件", "spec": "S-05"})
    if not html_path.is_file():
        findings.append({"code": "V1-HTML", "severity": "P1", "layer": "V1",
                         "location": "交付物", "detail": "缺少同名 HTML，自动生成", "spec": "S-05"})
        try:
            atomic_write(html_path, md2html.convert(md_path.resolve()))
            regenerated = True
        except Exception as exc:  # noqa: BLE001
            findings.append({"code": "V1-HTML", "severity": "P0", "layer": "V1",
                             "location": "交付物", "detail": f"HTML 自动生成失败：{exc}", "spec": "S-05"})
    elif html_path.stat().st_size == 0:
        findings.append({"code": "V1-HTML", "severity": "P0", "layer": "V1",
                         "location": "交付物", "detail": "HTML 为空文件", "spec": "S-05"})

    # 命名 slug 与目录一致性（与 preflight PF-NAME 同口径，独立呈现）
    det = detect_month_report(md_path.name)
    slug_dir = re.sub(r"^\d{2}-", "", md_path.parents[1].name) if len(md_path.parents) > 1 else ""
    if not det:
        findings.append({"code": "V1-NAME", "severity": "P1", "layer": "V1",
                         "location": "文件命名", "detail": "不符合月度命名约定（YYYY-MM-<主题slug>）", "spec": "S-11"})
    elif slug_dir and det[1] != slug_dir:
        findings.append({"code": "V1-NAME", "severity": "P1", "layer": "V1",
                         "location": "文件命名",
                         "detail": f"报告 slug「{det[1]}」与目录 slug「{slug_dir}」不一致", "spec": "S-04"})

    worst = "pass"
    if any(f["severity"] == "P0" for f in findings):
        worst = "fail"
    elif any(f["severity"] == "P1" for f in findings):
        worst = "fail"
    elif findings:
        worst = "warn"
    detail = "交付物齐全且可访问" if worst == "pass" else f"{len(findings)} 项问题"
    if regenerated:
        detail += "（HTML 已自动生成）"
    return RuleResult("V1", "交付物与文件可访问", worst, findings, detail), regenerated


def rule_v2_fields(rel: str, text: str, html: str = "") -> RuleResult:
    """V2 必填字段与要素（复用 audit_preflight.check_text，不含 HTML 相关项）。

    传入真实 html 以保证 PF-PAIR 判定正确；PF-SKELETON / PF-LINT 归入 V3。
    """
    findings = [ _finding_dict(f) for f in audit_preflight.check_text(rel, text, html, "", "") ]
    findings = [f for f in findings if f["code"] in V2_CODES]
    worst = _worst(findings)
    return RuleResult("V2", "必填字段与要素", worst, findings,
                      "要素 / 命名 / 口径 / 引用 / 登记册指针校验")


def rule_v3_format(rel: str, html: str, type_id: str) -> RuleResult:
    """V3 格式合规：类型骨架 + HTML lint。"""
    findings: list[dict] = []
    if html:
        if not type_id:
            findings.append({"code": "V3-SKELETON", "severity": "P2", "layer": "V3",
                             "location": "类型骨架", "detail": "business-config 未引用类型模板", "spec": "S-05"})
        else:
            rules = compliance_check.load_rules()
            det = detect_month_report(Path(rel).name)
            cycle = "monthly"
            if det and det[0].endswith("Q4"):
                cycle = "quarterly"
            rule, _ = compliance_check.cycle_rule(rules, type_id, cycle)
            if rule is None:
                findings.append({"code": "V3-SKELETON", "severity": "P2", "layer": "V3",
                                 "location": "类型骨架", "detail": f"类型 {type_id} 未登记", "spec": "S-05"})
            else:
                for level, msg in compliance_check.check_report(html, rule, rules.get("common", {})):
                    findings.append({"code": "V3-SKELETON", "severity": "P1" if level == "E" else "P2",
                                     "layer": "V3", "location": "类型骨架",
                                     "detail": f"[{type_id}/{cycle}] {msg}", "spec": "S-11"})
        for level, msg in lint_reports.lint_html(html):
            findings.append({"code": "V3-LINT", "severity": "P1" if level == "E" else "P2",
                             "layer": "V3", "location": "HTML lint", "detail": msg, "spec": "S-11"})
    worst = _worst(findings)
    return RuleResult("V3", "格式合规", worst, findings, "类型骨架与 HTML 结构校验")


def rule_v4_consistency(rel: str, md_path: Path, html_path: Path, type_id: str,
                        iq_by_path: dict, l5_status: dict) -> RuleResult:
    """V4 数据准确性与一致性（L3/L4 + 信息质量四维度）。"""
    res = audit_check.check_report(rel, md_path, html_path, type_id, iq_by_path, l5_status)
    findings = [_finding_dict(f) for f in res.findings
                if f.layer in ("L3", "L4") or str(getattr(f, "code", "")).startswith("C-")]
    worst = _worst(findings)
    return RuleResult("V4", "数据准确性与一致性", worst, findings,
                      "来源标注 / 失效引用 / 跨文档重复 / 登记册口径 / 报告↔登记册数值一致性")


def rule_v5_ranges(rel: str, text: str, registry: Path | None) -> RuleResult:
    """V5 关键指标数值范围：登记册活值 ↔ 报告数值覆盖比对。"""
    findings: list[dict] = []
    if registry is None:
        return RuleResult("V5", "关键指标数值范围", "pass", [],
                          "无登记册，跳过（主题未建登记册）")
    lt = live_table(iq_read(registry))
    if not lt:
        return RuleResult("V5", "关键指标数值范围", "pass", [],
                          "登记册无活值表，跳过")
    hdr, rows = lt
    vi = next((i for i, h in enumerate(hdr) if "最新值" in h), None)
    if vi is None:
        return RuleResult("V5", "关键指标数值范围", "pass", [],
                          "登记册无「最新值」列，跳过")
    reg_vals = {int(c[0]): c[vi] for c in rows if len(c) > vi and c[0].isdigit()}
    rep_vals = report_value_rows(text)
    if not rep_vals:
        return RuleResult("V5", "关键指标数值范围", "pass", [],
                          f"登记册 {len(reg_vals)} 项；报告无编号活值行，跳过比对")
    missing_total = []
    for no, rv in sorted(reg_vals.items()):
        if no not in rep_vals:
            continue
        missing = significant_numbers(rv) - significant_numbers(rep_vals[no])
        if missing:
            missing_total.append(f"#{no} 缺 {', '.join(sorted(missing))}")
    if missing_total:
        findings.append({"code": "V5-RANGE", "severity": "P1", "layer": "V5",
                         "location": "数据变更摘要",
                         "detail": "登记册活值数值未在报告对应行出现：" + "；".join(missing_total),
                         "spec": "S-09"})
    worst = _worst(findings)
    covered = sum(1 for no in reg_vals if no in rep_vals)
    detail = f"登记册 {len(reg_vals)} 项，报告覆盖 {covered} 项"
    return RuleResult("V5", "关键指标数值范围", worst, findings, detail)


def _worst(findings: list[dict]) -> str:
    if any(f.get("severity") == "P0" for f in findings):
        return "fail"
    if any(f.get("severity") == "P1" for f in findings):
        return "fail"
    if findings:
        return "warn"
    return "pass"


# ──────────────────────────────────────────────
# 写回与提交
# ──────────────────────────────────────────────

def _base_date(text: str) -> str:
    """从报告文本提取数据基准日（用于写回块的稳定标识）。"""
    m = BASE_DATE_RE.search(text)
    return m.group(1) if m else "—"


def render_block(result: VerifyResult, log_rel: str) -> str:
    """渲染写回块。

    稳定性：块内只使用「数据基准日 + 规则集 + 规则结论」，不含运行时刻与内容指纹
    （避免自指漂移）；同一份报告重复验证不产生内容变化，运行时刻仅写入 JSON 日志。
    """
    c = result.counts()
    concl = "通过" if result.passed else "不通过"
    rows = "｜".join(f"{r.id} {r.name} {r.status}" for r in result.rules)
    return "\n".join([
        BLOCK_START,
        "## 自动验证结果",
        "",
        f"> 数据基准日：{result.base_date}　|　规则集：auto-verify v{TOOL_VERSION}　|　"
        f"结论：{concl}（P0 {c['P0']} / P1 {c['P1']} / P2 {c['P2']}）",
        f"> 规则明细：{rows}",
        f"> 验证日志：{log_rel}",
        BLOCK_END,
    ])


def write_back(md_path: Path, block: str) -> bool:
    """幂等写入「自动验证结果」章节（存在则替换，不存在则追加）。"""
    text = _read(md_path)
    if BLOCK_RE.search(text):
        new = BLOCK_RE.sub(lambda _m: block, text)
    else:
        new = text.rstrip("\n") + "\n\n" + block + "\n"
    if new != text:
        atomic_write(md_path, new)
        return True
    return False


def write_log(result: VerifyResult, log_rel: str) -> Path:
    RULES_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "tool": "auto_verify",
        "version": TOOL_VERSION,
        "run_at": result.run_at,
        "report": result.report,
        "passed": result.passed,
        "counts": result.counts(),
        "rules": [asdict(r) for r in result.rules],
        "actions": result.actions,
        "log": log_rel,
    }
    p = result.log_path
    atomic_write(p, json.dumps(payload, ensure_ascii=False, indent=2))
    return p


def submit_audit(rel: str) -> tuple[bool, str]:
    """自动提交审计（submit）；返回（是否成功, 输出）。

    先执行 ``--sync`` 使内容已变的报告回到 stale（未变更者不受影响），再提交；
    避免「已审计报告直接 submit」被状态机拒绝。
    """
    base = ["python", "engine/tools/audit_pipeline.py"]
    logs: list[str] = []
    # 内容已变 → 先撤销旧的「已审计」徽章（避免残留过期 audit_id / 指纹）
    badge = subprocess.run(
        ["python", "engine/tools/audit_badge.py", "--revoke", "--report", rel],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT))
    logs.append(((badge.stdout or "") + (badge.stderr or "")).strip())
    sync = subprocess.run(base + ["--sync"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=str(ROOT))
    logs.append(((sync.stdout or "") + (sync.stderr or "")).strip())
    proc = subprocess.run(base + ["--submit", "--report", rel],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=str(ROOT))
    logs.append(((proc.stdout or "") + (proc.stderr or "")).strip())
    out = "\n".join(x for x in logs if x)
    return proc.returncode == 0, out


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def verify_report(rel: str, dry_run: bool = False, do_submit: bool = True) -> VerifyResult:
    rel = rel.replace("\\", "/")
    md_path = resolve_within(ROOT, rel)
    html_path = md_path.with_suffix(".html")
    run_at = datetime.now().isoformat(timespec="seconds")
    result = VerifyResult(report=rel, run_at=run_at)

    # V1
    v1, regenerated = rule_v1_deliverables(rel, md_path, html_path)
    result.rules.append(v1)
    result.actions["html_regenerated"] = regenerated
    if not md_path.is_file():
        # 源稿缺失：无法继续，直接失败返回
        write_log(result, "")
        return result

    text = _read(md_path)
    html = _read(html_path) if html_path.is_file() else ""
    cfg = md_path.parents[1] / "prompts" / "business-config.md"
    type_id = compliance_check.detect_type(_read(cfg)) if cfg.is_file() else ""
    registry = _registry_of(md_path)

    # V2 / V3 / V4 / V5
    result.rules.append(rule_v2_fields(rel, text, html))
    result.rules.append(rule_v3_format(rel, html, type_id))
    iq = audit_check.iq_findings_by_path()
    l5 = audit_check.l5_status()
    result.rules.append(rule_v4_consistency(rel, md_path, html_path, type_id, iq, l5))
    result.rules.append(rule_v5_ranges(rel, text, registry))

    log_rel = _rel(result.log_path)
    result.actions["log"] = log_rel

    if not result.passed:
        result.actions["terminated"] = "验证未通过，终止后续流程（未写回、未提交）"
        write_log(result, log_rel)
        return result

    # 通过 → 写回
    if dry_run:
        result.actions["dry_run"] = "试运行：未写回、未重新生成、未提交"
        write_log(result, log_rel)
        return result

    result.base_date = _base_date(text)
    block = render_block(result, log_rel)
    changed = write_back(md_path, block)
    result.actions["section_written"] = changed
    # 重新生成 HTML（含验证结果章节）
    atomic_write(html_path, md2html.convert(md_path.resolve()))
    result.actions["html_regenerated"] = True
    # 写回后复核（确保未引入 P0/P1）
    recheck = verify_report(rel, dry_run=True, do_submit=False)
    if not recheck.passed:
        result.actions["recheck_failed"] = "写回后复核未通过"
        result.rules.append(RuleResult("V6", "写回复核", "fail",
                                       [f for r in recheck.rules for f in r.findings],
                                       "写回验证结果后 P0/P1 复现"))
        result.actions["terminated"] = "写回后复核未通过，终止（未提交）"
        write_log(result, log_rel)
        return result
    result.actions["recheck"] = "写回后复核通过"

    write_log(result, log_rel)

    # 自动提交审计
    if do_submit:
        ok, out = submit_audit(rel)
        result.actions["submitted"] = ok
        result.actions["submit_output"] = out
        write_log(result, log_rel)
    return result


def iter_reports() -> list[str]:
    out: list[str] = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        for md in sorted(reports.glob("*.md")):
            out.append(_rel(md))
    return out


def _print_result(result: VerifyResult, verbose: bool = True) -> None:
    c = result.counts()
    concl = "通过" if result.passed else "不通过"
    print(f"{result.report}：{concl}（P0 {c['P0']} / P1 {c['P1']} / P2 {c['P2']}）")
    if verbose:
        for r in result.rules:
            mark = {"pass": "✓", "warn": "!", "fail": "✗"}.get(r.status, "?")
            print(f"  [{mark}] {r.id} {r.name}：{r.detail}")
            for f in sorted(r.findings, key=lambda x: _severity_rank(x.get("severity", "P2"))):
                print(f"        [{f.get('severity')}] {f.get('code')} {f.get('location')}：{f.get('detail')}")
        for k, v in result.actions.items():
            print(f"  · {k}：{v}")


def main() -> int:
    ap = argparse.ArgumentParser(description="报告生成后自动验证（AutoVerify）")
    ap.add_argument("--report", help="单份报告（仓库相对路径）")
    ap.add_argument("--all", action="store_true", help="全量验证")
    ap.add_argument("--dry-run", action="store_true", help="只验证与写日志，不写回、不提交")
    ap.add_argument("--no-submit", action="store_true", help="写回但不自动提交审计")
    ap.add_argument("--json", action="store_true", help="结果输出到 stdout（JSON）")
    ap.add_argument("--quiet", action="store_true", help="不打印逐条明细")
    args = ap.parse_args()

    if not args.report and not args.all:
        ap.print_help()
        return 2

    rels = iter_reports() if args.all else [args.report.replace("\\", "/")]
    results: list[VerifyResult] = []
    for rel in rels:
        try:
            exists = resolve_within(ROOT, rel).is_file()
        except (ValueError, OSError):
            exists = False
        if not exists:
            print(f"[ERROR] 报告不存在：{rel}", file=sys.stderr)
            return 2
        results.append(verify_report(rel, dry_run=args.dry_run,
                                     do_submit=not args.no_submit and not args.dry_run))

    if args.json:
        print(json.dumps({
            "summary": {
                "reports": len(results),
                "passed": sum(1 for r in results if r.passed),
                "failed": sum(1 for r in results if not r.passed),
            },
            "results": [{"report": r.report, "passed": r.passed, "counts": r.counts(),
                         "actions": r.actions,
                         "rules": [asdict(x) for x in r.rules]} for r in results],
        }, ensure_ascii=False, indent=2))
    else:
        for r in results:
            _print_result(r, verbose=not args.quiet)

    failed = [r for r in results if not r.passed]
    if failed:
        print(f"\n[FAIL] {len(failed)} 份报告验证未通过，流程已终止："
              + "、".join(r.report for r in failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
