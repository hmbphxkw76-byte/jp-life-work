"""审计报告登记册（AuditGuard 体系）。

自动发现全部业务主题下的真实报告（reports/*.md），生成机器可读 + 人读登记册，
并校验「登记册 ↔ 实际文件」双向一致（无遗漏、无多余、指纹匹配）。

登记册字段见 docs/审计报告标准化管理体系.md 第 2.2 节。

用法：
    python audit_registry.py --init     # 扫描并（重）生成登记册（幂等）
    python audit_registry.py --check    # 校验一致性（退出码 0/1/2）

退出码：0 = 一致；1 = 不一致（缺漏 / 多余 / 指纹失配）；2 = 仅信息性差异。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    ROOT,
    TYPE_RE,
    detect_month_report,
    iter_business_dirs,
    topic_slug,
)

AUDIT_DIR = ROOT / "src" / "report-audits" / "audit"
REGISTRY_JSON = AUDIT_DIR / "report-registry.json"
REGISTRY_MD = AUDIT_DIR / "report-registry.md"
SPEC_VERSION = "v1.0"


def sha256_file(path: Path) -> str:
    """文件字节 SHA-256（小写 hex）。"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# 已审计标识块（连同其前置空行一并剥离：注入 / 撤销标识不改变内容指纹）
BADGE_RE = re.compile(r"^>\s*\*\*已审计\*\*.*$", re.MULTILINE)
BADGE_BLOCK_RE = re.compile(r"\n{1,2}^>\s*\*\*已审计\*\*[^\n]*", re.MULTILINE)
# HTML 已审计徽章（同理剥离：标识属审计状态，不计入内容指纹）
AUDIT_BADGE_HTML_RE = re.compile(r'<div class="audit-badge".*?</div>', re.DOTALL)


def content_fingerprint(path: Path) -> str:
    """内容指纹：去除「已审计」标识块（含前置空行）后的 md 文本 SHA-256。

    标识块由审计流程注入 / 撤销，属「审计状态」而非「研究内容」，
    因此不计入内容指纹——否则注入标识会使审计失效，形成自锁。
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    text = BADGE_BLOCK_RE.sub("", text)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def html_fingerprint(path: Path) -> str:
    """HTML 交付物指纹：剥离「已审计」徽章后的 SHA-256（与 md 指纹同理）。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    text = AUDIT_BADGE_HTML_RE.sub("", text)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_fingerprints(md_path: Path, html_path: Path | None) -> tuple[str, str]:
    """md + html 双指纹；html 缺失时第二项为空串（向后兼容）。"""
    md = content_fingerprint(md_path)
    html = html_fingerprint(html_path) if html_path and html_path.is_file() else ""
    return md, html


def type_id_of(topic_dir: Path) -> str:
    """从 business-config 继承声明解析报告类型 ID。"""
    cfg = topic_dir / "prompts" / "business-config.md"
    if not cfg.is_file():
        return ""
    m = TYPE_RE.search(cfg.read_text(encoding="utf-8", errors="replace"))
    return m.group(1) if m else ""


def discover() -> list[dict]:
    """扫描全部业务主题 -> 报告登记条目列表（按主题、期间、路径排序）。"""
    out: list[dict] = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if not reports.is_dir():
            continue
        tid = type_id_of(b.path)
        for md in sorted(reports.glob("*.md")):
            det = detect_month_report(md.name)
            period, slug = (det[0], det[1]) if det else ("", "")
            out.append(
                {
                    "report": md.relative_to(ROOT).as_posix(),
                    "topic": b.rel,
                    "topic_slug": topic_slug(b.region if not b.property_type else b.property_type),
                    "period": period,
                    "slug": slug,
                    "type_id": tid,
                    "md": md.relative_to(ROOT).as_posix(),
                    "html": md.with_suffix(".html").relative_to(ROOT).as_posix(),
                    "content_hash": content_fingerprint(md),
                    "audit_id": "",
                    "audit_state": "registered",
                    "finalized_at": "",
                }
            )
    out.sort(key=lambda r: (r["topic"], r["period"], r["report"]))
    return out


def _md_table(rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def render_md(entries: list[dict], run_date: str) -> str:
    rows = [["报告", "主题", "期间", "类型", "内容指纹", "审计状态", "审计编号"]]
    for e in entries:
        rows.append(
            [f"[{e['report']}](../{e['report']})", e["topic"], e["period"] or "—",
             e["type_id"] or "—", f"`sha256:{e['content_hash'][:12]}`",
             e["audit_state"], e["audit_id"] or "—"]
        )
    return "\n".join(
        [
            "# 审计报告登记册（AuditGuard）",
            "",
            f"> 生成日期：{run_date}　|　报告总数：{len(entries)}　|　"
            f"依据《审计报告标准化管理体系》{SPEC_VERSION}",
            "> 本文件由 `audit_registry.py --init` 自动生成，请勿手工编辑。",
            "",
            _md_table(rows),
            "",
        ]
    )


def _audit_state() -> dict:
    """读取审计状态（audit-status.json）-> {report: {audit_id, audit_state, finalized_at}}。"""
    p = AUDIT_DIR / "audit-status.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data.get("reports", {})


def build() -> list[dict]:
    """生成登记册（JSON + MD），并合并审计状态（状态 / 审计编号 / 终审时间）。"""
    entries = discover()
    state = _audit_state()
    for e in entries:
        st = state.get(e["report"], {})
        e["audit_id"] = st.get("audit_id", "") or ""
        e["audit_state"] = st.get("state", "registered") or "registered"
        e["finalized_at"] = st.get("finalized_at", "") or ""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": SPEC_VERSION,
        "generated": date.today().isoformat(),
        "count": len(entries),
        "reports": entries,
    }
    REGISTRY_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REGISTRY_MD.write_text(render_md(entries, date.today().isoformat()), encoding="utf-8")
    return entries


def check() -> tuple[int, list[str]]:
    """校验登记册与实际文件一致 -> (问题数, 明细)。"""
    problems: list[str] = []
    entries = discover()
    if not REGISTRY_JSON.is_file():
        return 1, [f"登记册缺失：{REGISTRY_JSON.relative_to(ROOT)}（运行 --init 生成）"]
    data = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
    reg = {e["report"]: e for e in data.get("reports", [])}
    disc = {e["report"]: e for e in entries}

    missing = sorted(set(disc) - set(reg))
    extra = sorted(set(reg) - set(disc))
    for r in missing:
        problems.append(f"登记册遗漏报告：{r}")
    for r in extra:
        problems.append(f"登记册多余报告（文件已不存在）：{r}")
    for r in sorted(set(reg) & set(disc)):
        if reg[r]["content_hash"] != disc[r]["content_hash"]:
            problems.append(f"内容指纹失配（内容已变更）：{r}")
    return len(problems), problems


def main() -> int:
    ap = argparse.ArgumentParser(description="审计报告登记册")
    ap.add_argument("--init", action="store_true", help="扫描并生成登记册")
    ap.add_argument("--check", action="store_true", help="校验登记册一致性")
    args = ap.parse_args()

    if args.init:
        entries = build()
        print(f"登记册已生成：{len(entries)} 份报告")
        print(f"  {REGISTRY_JSON.relative_to(ROOT)}")
        print(f"  {REGISTRY_MD.relative_to(ROOT)}")
        return 0

    if args.check:
        n, problems = check()
        for p in problems:
            print(f"[X] {p}")
        if n == 0:
            print(f"登记册一致：{len(discover())} 份报告全部登记、指纹匹配")
            return 0
        print(f"登记册校验失败：{n} 项不一致")
        return 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
