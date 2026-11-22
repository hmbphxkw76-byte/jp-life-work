#!/usr/bin/env python3
"""generation_gate.py — 生成前信息核验（闸0）。

定位：把「信息输入是否满足可生成条件」前置到报告生成之前，与「提交前内容硬门禁」
（``engine/scripts/precommit_content_gate.py``）和 CI 交付门禁共同构成三道卡点。

复用既有判定内核，不新写规则：
- 闸1-3：``stage_gate_check.check_topic``（继承 / 变量 / 登记册 / 类型注册）；
- 来源语言：``source_language_gate.check_prompts``（过滤本主题）；
- 无法核实内容：``verified_content_gate.scan_text``（全层零容忍）；
- 来源 schema：``source_check.extract_report``（缺来源章节阻断）。

退出码：0=可生成；1=存在 P0/P1（阻断）；2=仅 P2（告警放行）。

用法：
    python engine/tools/generation_gate.py --topic 01-ssw-driver
    python engine/tools/generation_gate.py --all
    python engine/tools/generation_gate.py --all --json
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import source_check  # noqa: E402
import source_language_gate  # noqa: E402
import stage_gate_check  # noqa: E402
import verified_content_gate  # noqa: E402
from _common import iter_business_dirs  # noqa: E402

P_LEVELS = {"P0": 0, "P1": 1, "P2": 2}


@dataclass
class Finding:
    """一条生成前核验发现。"""

    code: str       # G0-STRUCT / G0-LANG / G0-CONTENT / G0-SOURCE
    severity: str   # P0 / P1 / P2
    location: str
    detail: str


def severity_counts(findings: list[Finding]) -> dict:
    c = {"P0": 0, "P1": 0, "P2": 0}
    for f in findings:
        c[f.severity] = c.get(f.severity, 0) + 1
    return c


def _full_layer_policy(policy: dict) -> dict:
    """全层零容忍：清空记录层 / 状态列 / 文件与行级豁免（与 CI 默认口径一致）。"""
    return {
        **policy,
        "record_sections": {k: [] for k in policy["record_sections"]},
        "status_columns": [],
        "excluded_files": [],
        "excluded_lines": [],
    }


def _topic_files(b) -> list[tuple[str, str, Path]]:
    """本主题受检文件：(相对路径, 类型, 路径)。

    与 ``verified_content_gate.iter_targets`` 同口径：报告 / 手册 / 登记册
    纳入内容层扫描；``prompts/`` 为指令文本（合法含标记词），只做来源语言层检查。
    """
    out: list[tuple[str, str, Path]] = []
    for sub in ("data", "handbook", "reports"):
        d = b.path / sub
        if not d.is_dir():
            continue
        for md in sorted(d.glob("*.md")):
            rel = f"{b.rel}/{sub}/{md.name}"
            out.append((rel, verified_content_gate.kind_of(rel), md))
    return out


def check_topic(b) -> list[Finding]:
    """单主题生成前核验（读取其资产与既有报告）。

    ``b`` 需含 ``path``（主题目录）与 ``rel``（仓库相对目录名）。
    """
    out: list[Finding] = []

    # G0-STRUCT：闸1-3
    for f in stage_gate_check.check_topic(b):
        out.append(Finding(f.code, f.severity, f"{b.rel}/{f.location}", f.detail))

    # G0-LANG：提示词层来源语言（过滤本主题）
    try:
        lang_policy = source_language_gate.load_policy()
    except Exception as exc:  # noqa: BLE001
        out.append(Finding("G0-LANG", "P1", b.rel, f"来源语言政策加载失败：{exc}"))
    else:
        for msg in source_language_gate.check_prompts(lang_policy):
            if msg.startswith(b.rel + "/"):
                out.append(Finding("G0-LANG", "P1", msg.split(":", 1)[0], msg))

    # G0-CONTENT / G0-SOURCE
    try:
        vc_policy = _full_layer_policy(verified_content_gate.load_policy())
    except Exception as exc:  # noqa: BLE001
        out.append(Finding("G0-CONTENT", "P1", b.rel, f"无法核实内容政策加载失败：{exc}"))
        return out

    for rel, kind, path in _topic_files(b):
        text = path.read_text(encoding="utf-8", errors="replace")
        for h in verified_content_gate.scan_text(text, kind, vc_policy):
            out.append(Finding(
                "G0-CONTENT", "P1", f"{rel}:{h['line']}",
                f"无法核实标记 {h['markers']}：{h['text']}",
            ))
        if kind == "report":
            rec = source_check.extract_report(rel, text)
            if "缺来源章节" in rec["problems"]:
                out.append(Finding("G0-SOURCE", "P1", rel, "缺来源章节"))
    return out


def run_all() -> tuple[list[dict], dict]:
    """全量核验全部业务主题。"""
    results: list[dict] = []
    for b in iter_business_dirs():
        findings = check_topic(b)
        results.append({
            "topic": b.rel,
            "findings": findings,
            "severity": severity_counts(findings),
            "passed": not any(f.severity in ("P0", "P1") for f in findings),
        })
    results.sort(key=lambda r: r["topic"])
    summary: dict = {
        "topics": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "by_severity": {"P0": 0, "P1": 0, "P2": 0},
    }
    for r in results:
        for k, v in r["severity"].items():
            summary["by_severity"][k] += v
    return results, summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="生成前信息核验（闸0）")
    ap.add_argument("--topic", help="单个主题目录名（如 01-ssw-driver）")
    ap.add_argument("--all", action="store_true", help="全量核验")
    ap.add_argument("--json", action="store_true", help="结果输出到 stdout（JSON）")
    args = ap.parse_args(argv)

    if args.topic:
        matches = [b for b in iter_business_dirs()
                   if b.rel == args.topic or b.region == args.topic]
        if not matches:
            print(f"[ERROR] 未找到主题：{args.topic}", file=sys.stderr)
            return 1
        findings = check_topic(matches[0])
        c = severity_counts(findings)
        passed = not any(f.severity in ("P0", "P1") for f in findings)
        if args.json:
            print(json.dumps({
                "topic": matches[0].rel, "passed": passed, "severity": c,
                "findings": [asdict(f) for f in findings],
            }, ensure_ascii=False, indent=2))
        else:
            print(f"{matches[0].rel}：{'可生成' if passed else '阻断'}"
                  f"（P0 {c['P0']} / P1 {c['P1']} / P2 {c['P2']}）")
            for f in sorted(findings, key=lambda x: (P_LEVELS.get(x.severity, 9), x.code)):
                print(f"  [{f.severity}] {f.code} {f.location}：{f.detail}")
        return 1 if (c["P0"] or c["P1"]) else (2 if c["P2"] else 0)

    if not args.all:
        ap.print_help()
        return 2

    results, summary = run_all()
    if args.json:
        print(json.dumps({
            "summary": summary,
            "results": [{"topic": r["topic"], "passed": r["passed"],
                         "severity": r["severity"],
                         "findings": [asdict(f) for f in r["findings"]]}
                        for r in results],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"生成前信息核验（闸0）：{summary['topics']} 个主题，"
              f"可生成 {summary['passed']} / 阻断 {summary['failed']}")
        print(f"  P0 {summary['by_severity']['P0']} / "
              f"P1 {summary['by_severity']['P1']} / P2 {summary['by_severity']['P2']}")
        for r in results:
            if not r["passed"]:
                print(f"  [BLOCK] {r['topic']}："
                      + "; ".join(f"{f.code}({f.severity})" for f in r["findings"]
                                  if f.severity in ("P0", "P1")))
    if summary["by_severity"]["P0"] or summary["by_severity"]["P1"]:
        return 1
    return 2 if summary["by_severity"]["P2"] else 0


if __name__ == "__main__":
    sys.exit(main())
