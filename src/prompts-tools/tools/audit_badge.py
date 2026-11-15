"""已审计标识注入 / 撤销 / 校验（AuditGuard 体系）。

依据 docs/审计报告标准化管理体系.md 第六节：仅 `audited` 且内容指纹匹配的报告
允许携带「已审计」标识。标识写入 md 文首（免责声明块之后），由 md2html 渲染为
HTML hero 区绿色徽章。

**指纹口径**：内容指纹基于「去除已审计标识块」的 md 文本计算，因此注入 / 撤销
标识不会改变指纹、不会使审计失效。

用法：
    python audit_badge.py --apply --all          # 为全部已审计报告注入标识
    python audit_badge.py --apply --report <路径>
    python audit_badge.py --revoke --all         # 撤销全部标识
    python audit_badge.py --check                # 校验标识 ⟺ 状态一致
    python audit_badge.py --sync                 # 有效者注入、失效者撤销

退出码：0 = 一致 / 操作成功；1 = 不一致（check 发现 P0）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT  # noqa: E402
from audit_registry import (  # noqa: E402
    AUDIT_DIR,
    REGISTRY_JSON,
    SPEC_VERSION,
    content_fingerprint,
    discover,
)

STATUS = AUDIT_DIR / "audit-status.json"
BADGE_RE = re.compile(r"^>\s*\*\*已审计\*\*.*$", re.MULTILINE)
DISCLAIMER_RE = re.compile(r"免责|不构成法律意见")


def _load_status() -> dict:
    """审计状态优先由台账派生（防信任分裂），文件仅作回退。"""
    try:
        from audit_pipeline import load_ledger, rebuild_status
        return rebuild_status(load_ledger())
    except Exception:  # noqa: BLE001
        pass
    if not STATUS.is_file():
        return {}
    try:
        return json.loads(STATUS.read_text(encoding="utf-8")).get("reports", {})
    except json.JSONDecodeError:
        return {}


def badge_text(audit_id: str, finalized_at: str, fp: str) -> str:
    day = (finalized_at or "")[:10] or "—"
    return (
        f"> **已审计** ✅ 审计编号 `{audit_id}`｜终审通过：{day}｜"
        f"内容指纹 `{fp[:19]}`｜依据《审计报告标准化管理体系》{SPEC_VERSION}"
    )


def _insert_after_disclaimer(text: str, badge: str) -> str:
    """把标识块插入到免责声明块引用之后（找不到则放到文首标题之后）。"""
    lines = text.splitlines()
    # 定位免责声明块引用组的末行
    i = 0
    disc_end = -1
    while i < len(lines):
        if lines[i].startswith(">"):
            j = i
            while j < len(lines) and (lines[j].startswith(">") or not lines[j].strip()):
                if lines[j].startswith(">") and DISCLAIMER_RE.search(lines[j]):
                    disc_end = j
                j += 1
            i = j
        else:
            i += 1
    if disc_end >= 0:
        lines.insert(disc_end + 1, "")
        lines.insert(disc_end + 2, badge)
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    # 回落：文首标题之后
    for k, line in enumerate(lines):
        if line.startswith("# "):
            lines.insert(k + 1, "")
            lines.insert(k + 2, badge)
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return badge + "\n\n" + text


def _strip_badge(text: str) -> tuple[str, bool]:
    """移除已审计标识块（连同其前置空行）-> (新文本, 是否移除)。"""
    lines = text.splitlines()
    out = []
    removed = False
    for line in lines:
        if BADGE_RE.match(line):
            removed = True
            # 去掉紧邻的前置空行
            if out and not out[-1].strip():
                out.pop()
            continue
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), removed


def _regenerate_html(md: Path) -> None:
    """重新生成同名 HTML（md2html）。"""
    try:
        import md2html
    except ImportError:
        return
    html = md2html.convert(md)
    md.with_suffix(".html").write_text(html, encoding="utf-8")


def _targets(all_: bool, rel: str | None) -> list[str]:
    if all_:
        return [e["report"] for e in discover()]
    if not rel:
        raise SystemExit("[ERROR] 需要 --report <路径> 或 --all")
    rel = rel.replace("\\", "/")
    try:
        resolved = (ROOT / rel).resolve()
        resolved.relative_to(ROOT.resolve())
    except (ValueError, OSError):
        raise SystemExit(f"[ERROR] 路径越出仓库根：{rel}")
    if not resolved.is_file():
        raise SystemExit(f"[ERROR] 报告不存在：{rel}")
    return [resolved.relative_to(ROOT.resolve()).as_posix()]


def cmd_apply(all_: bool, rel: str | None) -> int:
    status = _load_status()
    n = 0
    for rep in _targets(all_, rel):
        v = status.get(rep, {})
        if v.get("state") != "audited":
            print(f"[SKIP] {rep}：状态 {v.get('state') or '未登记'}，不注入标识")
            continue
        md = ROOT / rep
        fp = content_fingerprint(md).removeprefix("sha256:")
        if f"sha256:{fp}" != v.get("content_hash"):
            print(f"[SKIP] {rep}：指纹失配，审计失效")
            continue
        text = md.read_text(encoding="utf-8")
        text, _ = _strip_badge(text)
        text = _insert_after_disclaimer(text, badge_text(v["audit_id"], v.get("finalized_at", ""), fp))
        md.write_text(text, encoding="utf-8")
        _regenerate_html(md)
        n += 1
    print(f"已注入标识：{n} 份")
    return 0


def cmd_revoke(all_: bool, rel: str | None) -> int:
    n = 0
    for rep in _targets(all_, rel):
        md = ROOT / rep
        text = md.read_text(encoding="utf-8")
        new_text, removed = _strip_badge(text)
        if removed:
            md.write_text(new_text, encoding="utf-8")
            _regenerate_html(md)
            n += 1
    print(f"已撤销标识：{n} 份")
    return 0


def cmd_sync() -> int:
    status = _load_status()
    applied = revoked = 0
    for e in discover():
        rep = e["report"]
        md = ROOT / rep
        text = md.read_text(encoding="utf-8")
        has = bool(BADGE_RE.search(text))
        v = status.get(rep, {})
        valid = v.get("state") == "audited" and content_fingerprint(md) == v.get("content_hash")
        if valid and not has:
            fp = content_fingerprint(md).removeprefix("sha256:")
            text = _insert_after_disclaimer(text, badge_text(v["audit_id"], v.get("finalized_at", ""), fp))
            md.write_text(text, encoding="utf-8")
            _regenerate_html(md)
            applied += 1
        elif not valid and has:
            text, _ = _strip_badge(text)
            md.write_text(text, encoding="utf-8")
            _regenerate_html(md)
            revoked += 1
    print(f"标识同步：注入 {applied} 份，撤销 {revoked} 份")
    return 0


def cmd_check() -> int:
    status = _load_status()
    problems: list[str] = []
    for e in discover():
        rep = e["report"]
        md = ROOT / rep
        text = md.read_text(encoding="utf-8")
        has = bool(BADGE_RE.search(text))
        v = status.get(rep, {})
        valid = v.get("state") == "audited" and content_fingerprint(md) == v.get("content_hash")
        if has and not valid:
            problems.append(f"{rep}：携带已审计标识但状态为 {v.get('state') or '未登记'} 或指纹失配")
        if valid and not has:
            problems.append(f"{rep}：状态 audited 但缺少已审计标识")
        # HTML 侧
        html = md.with_suffix(".html")
        if html.is_file():
            htext = html.read_text(encoding="utf-8", errors="replace")
            h_has = 'class="audit-badge"' in htext
            if h_has != has:
                problems.append(f"{rep}：HTML 标识与 md 标识不一致")
    if problems:
        for p in problems:
            print(f"[X] {p}")
        print(f"标识校验失败：{len(problems)} 项不一致")
        return 1
    print(f"标识校验通过：{len(discover())} 份报告标识与审计状态一致")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="已审计标识管理")
    ap.add_argument("--apply", action="store_true", help="注入标识")
    ap.add_argument("--revoke", action="store_true", help="撤销标识")
    ap.add_argument("--check", action="store_true", help="校验标识与状态一致")
    ap.add_argument("--sync", action="store_true", help="同步标识（有效注入、失效撤销）")
    ap.add_argument("--report", help="报告相对路径")
    ap.add_argument("--all", action="store_true", help="作用于全部报告")
    args = ap.parse_args()

    if args.check:
        return cmd_check()
    if args.sync:
        return cmd_sync()
    if args.apply:
        return cmd_apply(args.all, args.report)
    if args.revoke:
        return cmd_revoke(args.all, args.report)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
