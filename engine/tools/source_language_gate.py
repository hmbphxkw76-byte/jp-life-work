#!/usr/bin/env python3
"""source_language_gate.py — 来源语言与机构白名单门禁（W5）。

把「来源语言规则」从语义约束升级为**可机读硬门禁**，单一事实源为
``engine/config/source-policy.json``：

- **提示词层（全量、始终检查）**：每个业务主题 ``prompts/business-config.md`` 的
  ``{{SOURCE_LANGUAGE_RULE}}`` 必须与政策文件的 ``source_language_rule`` 逐字一致；
  任何提示词 / 模板文本不得出现「允许中文来源」的表述（``forbidden_permission_patterns``）。
- **报告层（按变更 / 指定范围）**：来源 URL 不得命中中文来源域名黑名单
  （``blocked_domains``）。默认不扫报告；``--changed`` 只扫相对 ``--base`` 的变更报告，
  ``--all`` 扫全量，``--report`` 扫指定报告。存量报告为后续清理对象，故不默认全量阻断。

退出码：0=通过；1=违规（阻断）；2=仅告警（``--warn``）。

用法：
    python engine/tools/source_language_gate.py                 # 提示词层
    python engine/tools/source_language_gate.py --changed --base origin/main
    python engine/tools/source_language_gate.py --all
    python engine/tools/source_language_gate.py --report 01-ssw-driver/reports/2026-11-ssw-driver.md
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, iter_business_dirs  # noqa: E402

POLICY_PATH = ROOT / "engine" / "config" / "source-policy.json"
POLICY_SCHEMA = "1.0"

RULE_RE = re.compile(r"\{\{SOURCE_LANGUAGE_RULE\}\}\s*=\s*(.+?)\s*$", re.M)
URL_RE = re.compile(r"https?://[^\s)\]]+")


def load_policy() -> dict:
    """读取来源政策（缺失 / 损坏 / schema 不符即抛 ValueError）。"""
    try:
        data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"来源政策缺失：{POLICY_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"来源政策损坏（非合法 JSON）：{POLICY_PATH}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != POLICY_SCHEMA:
        actual = data.get("schema_version") if isinstance(data, dict) else type(data).__name__
        raise ValueError(
            f"来源政策 schema 版本不符：{POLICY_PATH}"
            f"（期望 {POLICY_SCHEMA}，实际 {actual}）"
        )
    for key in ("source_language_rule", "forbidden_permission_patterns", "blocked_domains"):
        if key not in data:
            raise ValueError(f"来源政策缺字段 {key}：{POLICY_PATH}")
    return data


def _norm(s: str) -> str:
    """归一化空白，供规则逐字比对。"""
    return re.sub(r"\s+", " ", (s or "").strip())


def _rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def business_prompt_files() -> list[Path]:
    """全部业务主题 prompts/*.md。"""
    out: list[Path] = []
    for b in iter_business_dirs():
        pdir = b.path / "prompts"
        if pdir.is_dir():
            out.extend(sorted(pdir.glob("*.md")))
    return out


def template_files() -> list[Path]:
    """通用层全部提示词 / 模板 md（含根部规范与类型模板）。"""
    tdir = ROOT / "engine" / "report_templates"
    if not tdir.is_dir():
        return []
    return sorted(tdir.rglob("*.md"))


def check_prompts(policy: dict) -> list[str]:
    """提示词层校验：规则逐字一致 + 许可模式扫描。"""
    out: list[str] = []
    rule = _norm(policy["source_language_rule"])
    patterns = policy["forbidden_permission_patterns"]

    # 变量逐字一致：仅 business-config.md 承载该变量
    for b in iter_business_dirs():
        f = b.path / "prompts" / "business-config.md"
        if not f.is_file():
            out.append(f"{b.rel}/prompts/business-config.md: 缺文件")
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        m = RULE_RE.search(text)
        if not m:
            out.append(f"{_rel(f)}: 缺 {{{{SOURCE_LANGUAGE_RULE}}}} 变量")
            continue
        if _norm(m.group(1)) != rule:
            out.append(f"{_rel(f)}: {{{{SOURCE_LANGUAGE_RULE}}}} 与 source-policy.json 不一致")

    for f in business_prompt_files() + template_files():
        text = f.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            for pat in patterns:
                if pat in line:
                    out.append(f"{_rel(f)}:{i}: 含中文来源许可表述「{pat}」")
                    break
    return out


def _host(url: str) -> str:
    try:
        host = urlsplit(url).netloc.lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def is_blocked(url: str, domains: list[str]) -> str | None:
    """URL 命中中文来源域名黑名单则返回该域名，否则 None。"""
    host = _host(url)
    if not host:
        return None
    for d in domains:
        if host == d or host.endswith("." + d):
            return d
    return None


def check_reports(policy: dict, files: list[Path]) -> list[str]:
    """报告层校验：来源 URL 不得命中黑名单。"""
    out: list[str] = []
    for f in files:
        if not f.is_file():
            out.append(f"{_rel(f)}: 报告不存在")
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            for url in URL_RE.findall(line):
                hit = is_blocked(url, policy["blocked_domains"])
                if hit:
                    out.append(f"{_rel(f)}:{i}: 中文来源域名 {hit}（{url}）")
    return out


def changed_report_files(base: str) -> list[Path]:
    """相对 base 的变更报告 md（git diff --name-only base...HEAD）。"""
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"],
            cwd=str(ROOT), capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return []
    if res.returncode != 0:
        return []
    out: list[Path] = []
    for line in res.stdout.splitlines():
        p = Path(line.strip())
        if len(p.parts) >= 3 and p.parts[1] == "reports" and p.suffix == ".md":
            out.append(ROOT / p)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="来源语言与机构白名单门禁")
    ap.add_argument("--changed", action="store_true", help="扫相对 --base 的变更报告")
    ap.add_argument("--base", default="main", help="--changed 的基址（默认 main）")
    ap.add_argument("--all", action="store_true", dest="all_reports", help="扫全量报告")
    ap.add_argument("--report", action="append", default=[], help="指定报告（可重复）")
    ap.add_argument("--warn", action="store_true", help="仅告警（退出码 2）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        policy = load_policy()
    except ValueError as exc:
        print(f"[错误] {exc}")
        return 1

    problems = check_prompts(policy)

    report_files: list[Path] = []
    if args.all_reports:
        for b in iter_business_dirs():
            rdir = b.path / "reports"
            if rdir.is_dir():
                report_files.extend(sorted(rdir.glob("*.md")))
    elif args.changed:
        report_files = changed_report_files(args.base)
    for r in args.report:
        report_files.append(ROOT / r)
    report_files = sorted(set(report_files))
    if report_files:
        problems += check_reports(policy, report_files)

    if args.json:
        print(json.dumps({"violations": len(problems), "problems": problems},
                         ensure_ascii=False, indent=2))
    else:
        scope = f"提示词 {len(business_prompt_files())} 份"
        if report_files:
            scope += f" + 报告 {len(report_files)} 份"
        print(f"来源语言门禁：{scope}；违规 {len(problems)} 项")
        for p in problems:
            print(f"  - {p}")

    if problems:
        return 2 if args.warn else 1
    print("来源语言门禁通过：规则一致、无中文来源许可表述"
          + ("、报告来源域名合规" if report_files else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
