#!/usr/bin/env python3
"""precommit_content_gate.py — 提交前内容硬门禁。

定位：在 ``git commit`` 之前，对**暂存区**内的报告 / 资产文件执行内容核验，
未核验信息一律不得进入仓库。与 ``engine/tools/generation_gate.py``（闸0，生成前）
和 CI 交付门禁（推送后）共同构成三道卡点。

复用既有判定内核，不新写规则：
- 无法核实内容：``verified_content_gate.scan_text``（全层零容忍）；
- 来源语言：``source_language_gate``（报告层中文域名黑名单 + 提示词层许可表述）；
- 来源 schema：``source_check.extract_report``（缺来源章节阻断）。

退出码：0=通过；1=命中（阻断提交）。

用法（由 pre-commit 钩子调用）：
    python engine/scripts/precommit_content_gate.py
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import source_check  # noqa: E402
import source_language_gate  # noqa: E402
import verified_content_gate  # noqa: E402


@dataclass
class Finding:
    """一条提交前内容核验发现。"""

    code: str       # PC-CONTENT / PC-LANG / PC-SOURCE / PC-POLICY
    severity: str   # P1
    location: str
    detail: str


def staged_entries() -> list[tuple[str, str, str]]:
    """暂存区条目：(相对路径, 类型, 文本)。仅 .md。"""
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=str(ROOT), capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    out: list[tuple[str, str, str]] = []
    for line in res.stdout.splitlines():
        rel = line.strip().replace("\\", "/")
        if not rel.endswith(".md"):
            continue
        p = ROOT / rel
        if not p.is_file():
            continue
        out.append((rel, verified_content_gate.kind_of(rel), p.read_text(encoding="utf-8", errors="replace")))
    return out


def _full_layer_policy(policy: dict) -> dict:
    """全层零容忍（与 CI 默认口径一致）。"""
    return {
        **policy,
        "record_sections": {k: [] for k in policy["record_sections"]},
        "status_columns": [],
        "excluded_files": [],
        "excluded_lines": [],
    }


def gate_entries(entries: list[tuple[str, str, str]]) -> list[Finding]:
    """对 (相对路径, 类型, 文本) 列表执行内容核验。"""
    try:
        vc_policy = _full_layer_policy(verified_content_gate.load_policy())
    except Exception as exc:  # noqa: BLE001
        return [Finding("PC-POLICY", "P1", "repo", f"无法核实内容政策加载失败：{exc}")]
    try:
        lang_policy = source_language_gate.load_policy()
    except Exception as exc:  # noqa: BLE001
        return [Finding("PC-POLICY", "P1", "repo", f"来源语言政策加载失败：{exc}")]

    out: list[Finding] = []
    blocked = lang_policy["blocked_domains"]
    forbidden = lang_policy["forbidden_permission_patterns"]

    for rel, kind, text in entries:
        # 内容层扫描：报告 / 手册 / 登记册 / 词库（与 verified_content_gate.iter_targets 同口径）。
        # prompts 为指令文本，合法含标记词，只做来源语言层检查。
        if kind in ("report", "handbook", "registry", "vocab"):
            for h in verified_content_gate.scan_text(text, kind, vc_policy):
                out.append(Finding(
                    "PC-CONTENT", "P1", f"{rel}:{h['line']}",
                    f"无法核实标记 {h['markers']}：{h['text']}",
                ))

        if kind == "report":
            for i, line in enumerate(text.splitlines(), 1):
                for url in source_language_gate.URL_RE.findall(line):
                    hit = source_language_gate.is_blocked(url, blocked)
                    if hit:
                        out.append(Finding(
                            "PC-LANG", "P1", f"{rel}:{i}",
                            f"中文来源域名 {hit}（{url}）",
                        ))
            rec = source_check.extract_report(rel, text)
            if "缺来源章节" in rec["problems"]:
                out.append(Finding("PC-SOURCE", "P1", rel, "缺来源章节"))
        elif _is_prompt_like(rel):
            # 仅提示词 / 模板层扫描中文来源许可表述（与 source_language_gate.check_prompts 同口径）；
            # 其他文档（如工具 README / CI 文档）讨论政策本身不视为违规。
            for pat in forbidden:
                if pat in text:
                    out.append(Finding(
                        "PC-LANG", "P1", rel, f"含中文来源许可表述「{pat}」"))
                    break
    return out


def _is_prompt_like(rel: str) -> bool:
    """是否为提示词 / 模板层文件（与 source_language_gate 的扫描范围一致）。"""
    return "/prompts/" in rel or rel.startswith("engine/report_templates/")


def main() -> int:
    entries = staged_entries()
    findings = gate_entries(entries)
    if findings:
        print(f"提交前内容硬门禁：命中 {len(findings)} 项（阻断提交）")
        for f in findings:
            print(f"  [{f.severity}] {f.code} {f.location}：{f.detail}")
        return 1
    if entries:
        print(f"提交前内容硬门禁通过：受检 {len(entries)} 份暂存文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
