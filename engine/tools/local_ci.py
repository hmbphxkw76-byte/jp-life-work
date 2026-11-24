#!/usr/bin/env python3
"""本地等价 CI 入口（本地优先 · 远程兜底 · 结果分享）。

复刻 `.github/workflows/` 中**本地可跑、只读、确定性、不依赖外网**的检查步骤
（validate / audit-gate 的检查类步骤），一条命令跑完并汇总。

原则：
  - 本地能跑的，一律本地跑（快、可复跑、无副作用）；
  - 本地环境不具备的才远程跑（链接可达率探测 / 自动开 PR / webhook / runner 环境 / secrets）；
  - 结果落盘为确定性 JSON（无时间戳），可重复运行逐字节一致，供结果分享。

用法：
    python engine/tools/local_ci.py run [选项]
    python engine/tools/local_ci.py list

退出码：0 全部通过；1 存在失败项；2 仅警告（含参数错误）。

本工具是**编排层**，不新增门禁项：每项检查均调用既有工具，判定口径仍归各工具。
规格见 docs/toolchain/specs/local-ci-entry.md。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT  # noqa: E402

SCHEMA_VERSION = "1.0"
EMIT_DEFAULT = ROOT / "engine" / "report-audits" / "local-ci" / "local-ci-status.json"
CHECK_TIMEOUT = 900  # 单检查项超时（秒）

PY = sys.executable


@dataclass(frozen=True)
class Check:
    """一项本地等价检查。"""

    id: str
    name: str
    ci: str
    cmd: tuple[str, ...]
    note: str = ""


# ──────────────────────────────────────────────
# 默认检查集（33 项，全部只读）
# ──────────────────────────────────────────────
CHECKS: tuple[Check, ...] = (
    Check("validate", "结构与规范校验", "validate", (PY, "engine/tools/validate.py")),
    Check("classify", "报告归位检查", "validate",
          (PY, "engine/tools/classify_reports.py", "--check", "--unknown-warn")),
    Check("region", "结构补全检查", "validate",
          (PY, "engine/tools/ensure_region_topics.py", "--check")),
    Check("hub", "汇总页一致性", "validate", (PY, "engine/tools/build_hub.py", "--check")),
    Check("index", "全局索引一致性", "validate",
          (PY, "engine/tools/build_index.py", "--check")),
    Check("links", "内链存在性", "validate", (PY, "engine/tools/link_check.py")),
    Check("registry", "工具注册表一致性", "validate",
          (PY, "engine/tools/generate_registry.py", "--check")),
    Check("audit-registry", "报告登记册一致性", "validate",
          (PY, "engine/tools/audit_registry.py", "--check")),
    Check("preflight", "落盘前自检", "validate",
          (PY, "engine/tools/audit_preflight.py", "--all")),
    Check("structure", "必需要素结构校验", "validate",
          (PY, "engine/tools/structure_check.py")),
    Check("parity", "md↔HTML 一致性", "validate",
          (PY, "engine/tools/md_html_parity.py")),
    Check("prompt", "提示词结构门禁", "validate", (PY, "engine/tools/prompt_check.py")),
    Check("lang", "来源语言门禁", "validate",
          (PY, "engine/tools/source_language_gate.py", "--changed", "--base", "main")),
    Check("content", "无法核实内容门禁", "validate",
          (PY, "engine/tools/verified_content_gate.py", "--all")),
    Check("metrics", "决策度量校验", "validate",
          (PY, "engine/tools/decision_metrics.py", "--check")),
    Check("decision-log", "决策日志校验", "validate",
          (PY, "engine/tools/decision_log.py", "--check")),
    Check("source-check", "来源条目 schema 校验", "validate",
          (PY, "engine/tools/source_check.py")),
    Check("counterexample", "反例扫描", "validate",
          (PY, "engine/tools/counterexample_scan.py")),
    Check("lint", "报告内容 lint", "validate",
          (PY, "engine/tools/lint_reports.py", "--new-only")),
    Check("compliance", "模板合规校验", "validate",
          (PY, "engine/tools/compliance_check.py", "--new-only")),
    Check("stage", "阶段闸检查", "validate", (PY, "engine/tools/stage_gate_check.py")),
    Check("gen-gate", "生成前信息核验（闸0）", "validate",
          (PY, "engine/tools/generation_gate.py", "--all")),
    Check("info-quality", "信息质量检查", "validate",
          (PY, "engine/tools/info_quality_check.py", "--check")),
    Check("fact-card", "事实卡片校验", "validate",
          (PY, "engine/tools/fact_card_check.py")),
    Check("pending", "待核实闭环", "validate",
          (PY, "engine/tools/pending_verification.py", "--check")),
    Check("finance", "财务模型一致性", "validate",
          (PY, "engine/tools/personal_finance_model.py", "--check")),
    Check("vocab-topic", "词库主题校验", "validate",
          (PY, "engine/vocabulary/script/vocab_tool.py", "topic-check")),
    Check("vocab-verify", "词库校验", "validate",
          (PY, "engine/vocabulary/script/vocab_tool.py", "verify")),
    Check("vocab-sync", "词库同步校验", "validate",
          (PY, "engine/vocabulary/script/sync_vocab.py", "check")),
    Check("vocab-near", "词库近义检查", "validate",
          (PY, "engine/vocabulary/script/vocab_near_check.py")),
    Check("vocab-cross", "词库交叉校验", "validate",
          (PY, "engine/vocabulary/script/vocab_tool.py", "cross-check")),
    Check("audit-gate", "合并门禁", "audit-gate",
          (PY, "engine/tools/audit_pipeline.py", "--gate")),
    Check("l5", "L5 证据元评估", "audit-gate",
          (PY, "engine/tools/l5_meta_check.py", "--check")),
)

# 可选检查（默认不跑；--with-tests / --with-coverage 追加）
EXTRA_CHECKS: tuple[Check, ...] = (
    Check("tests", "单元测试", "validate.tests",
          (PY, "-m", "unittest", "discover", "-s", "engine/tests")),
    Check("coverage", "覆盖率门禁", "validate.coverage",
          (PY, "engine/tools/coverage_gate.py")),
)

# 本地环境不具备、只能远程跑的环节（不在本地等价集内）。
REMOTE_ONLY: tuple[tuple[str, str], ...] = (
    ("probe", "链接可达率探测（link_check --external 等，依赖外网，不稳定）"),
    ("submit-pr", "自动开 PR / 自动合并（需 GitHub token 与网络）"),
    ("webhook-alert", "外部告警通道（需 webhook 凭据）"),
    ("runner-env", "GitHub runner 环境 / secrets / 服务端分支保护"),
)

# 非只读或需额外输入而排除的步骤（记录在此，消除「应接未接」歧义）。
EXCLUDED: tuple[tuple[str, str], ...] = (
    ("audit-check", "audit_check.py --all 会写报告，非只读"),
    ("auto-verify", "auto_verify.py 写运行日志且耗时，归维护流程"),
    ("cleanup-check", "本工具运行本身产生 __pycache__，自检会自伤"),
    ("review-gate", "review_gate.py --changed 需变更清单输入"),
    ("html-sync-write", "html-sync 的 md2html / build_hub / 提交回写，非只读"),
    ("maintenance-apply", "维护流程的 --apply / --write 修复类步骤，非只读"),
)


def current_branch() -> str:
    """当前 git 分支（读不到时返回 ``unknown``）。"""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
        )
        return proc.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def status_for_exit(code: int) -> str:
    """退出码 -> 状态。0 通过 / 2 仅警告 / 其余失败。"""
    if code == 0:
        return "pass"
    if code == 2:
        return "warn"
    return "fail"


def _last_line(text: str) -> str:
    for line in reversed(text.strip().splitlines()):
        if line.strip():
            return line.strip()
    return ""


def run_check(check: Check) -> dict:
    """执行单项检查，返回结果字典（确定性：不含时间戳 / 时长）。"""
    try:
        proc = subprocess.run(
            list(check.cmd),
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CHECK_TIMEOUT,
        )
        code, output = proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        code, output = 1, f"超时（>{CHECK_TIMEOUT}s）"
    except OSError as exc:  # 命令无法启动
        code, output = 1, f"无法执行：{exc}"
    return {
        "id": check.id,
        "name": check.name,
        "ci": check.ci,
        "exit_code": code,
        "status": status_for_exit(code),
        "summary": _last_line(output),
    }


def select(checks: tuple[Check, ...], only: str = "", skip: str = "") -> tuple[Check, ...]:
    """按 id 过滤检查集；未知 id 抛 SystemExit（由 CLI 转为退出码 2）。"""
    ids = {c.id for c in checks}
    want = [s.strip() for s in only.split(",") if s.strip()]
    drop = {s.strip() for s in skip.split(",") if s.strip()}
    unknown = (set(want) | drop) - ids
    if unknown:
        raise SystemExit(f"未知检查项：{sorted(unknown)}；可用：{sorted(ids)}")
    out = [c for c in checks if c.id in set(want)] if want else list(checks)
    return tuple(c for c in out if c.id not in drop)


def overall(results: list[dict]) -> int:
    """汇总退出码：任一失败 1 / 任一警告 2 / 否则 0。"""
    if any(r["status"] == "fail" for r in results):
        return 1
    if any(r["status"] == "warn" for r in results):
        return 2
    return 0


def build_document(results: list[dict], branch: str) -> dict:
    """构造确定性结果文档（无时间戳、无耗时）。"""
    return {
        "schema_version": SCHEMA_VERSION,
        "comment": "本地等价 CI 结果（确定性，无时间戳）。由 local_ci.py run --emit 生成。",
        "branch": branch,
        "checks": results,
        "summary": {
            "total": len(results),
            "pass": sum(1 for r in results if r["status"] == "pass"),
            "warn": sum(1 for r in results if r["status"] == "warn"),
            "fail": sum(1 for r in results if r["status"] == "fail"),
        },
    }


def render_text(results: list[dict], branch: str) -> str:
    lines = [f"本地等价 CI（本地优先 · 远程兜底）· 分支 {branch}"]
    for r in results:
        mark = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[r["status"]]
        tail = f" — {r['summary']}" if r["summary"] else ""
        lines.append(f"  [{mark}] {r['id']:<14} {r['name']}（{r['ci']}）{tail}")
    s = build_document(results, branch)["summary"]
    lines.append(f"汇总：{s['total']} 项，通过 {s['pass']} / 警告 {s['warn']} / 失败 {s['fail']}")
    return "\n".join(lines)


def render_markdown(results: list[dict], branch: str) -> str:
    s = build_document(results, branch)["summary"]
    lines = [
        "## 本地等价 CI 结果",
        "",
        f"- 分支：`{branch}`",
        f"- 汇总：**{s['total']} 项，通过 {s['pass']} / 警告 {s['warn']} / 失败 {s['fail']}**",
        "",
        "| # | 检查 | 对应 CI | 状态 | 摘要 |",
        "|---|---|---|---|---|",
    ]
    for i, r in enumerate(results, 1):
        mark = {"pass": "✅ 通过", "warn": "⚠️ 警告", "fail": "❌ 失败"}[r["status"]]
        lines.append(f"| {i} | {r['name']} (`{r['id']}`) | {r['ci']} | {mark} | {r['summary']} |")
    lines += ["", "### 本地未覆盖（仅远程）", ""]
    for name, desc in REMOTE_ONLY:
        lines.append(f"- `{name}`：{desc}")
    return "\n".join(lines)


def _pool(with_tests: bool, with_coverage: bool) -> tuple[Check, ...]:
    flags = (with_tests, with_coverage)
    extra = tuple(c for c, on in zip(EXTRA_CHECKS, flags, strict=True) if on)
    return CHECKS + extra


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="本地等价 CI（本地优先 · 远程兜底）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="跑检查集")
    run.add_argument("--only", default="", help="只跑指定 id（逗号分隔）")
    run.add_argument("--skip", default="", help="跳过指定 id（逗号分隔）")
    run.add_argument("--json", action="store_true", help="JSON 输出到 stdout")
    run.add_argument("--markdown", action="store_true", help="Markdown 输出到 stdout")
    run.add_argument("--emit", default="", help="结果 JSON 落盘路径")
    run.add_argument("--with-tests", action="store_true", help="追加单元测试检查")
    run.add_argument("--with-coverage", action="store_true", help="追加覆盖率门禁检查")
    sub.add_parser("list", help="列出检查项与远程分工")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        print("本地等价检查：")
        for c in CHECKS:
            print(f"  {c.id:<14} {c.name}（{c.ci}）")
        print("可选检查（--with-* 追加）：")
        for c in EXTRA_CHECKS:
            print(f"  {c.id:<14} {c.name}（{c.ci}）")
        print("排除（非只读 / 需额外输入）：")
        for name, desc in EXCLUDED:
            print(f"  {name:<14} {desc}")
        print("仅远程：")
        for name, desc in REMOTE_ONLY:
            print(f"  {name:<14} {desc}")
        return 0

    try:
        chosen = select(_pool(args.with_tests, args.with_coverage), args.only, args.skip)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2

    branch = current_branch()
    results = [run_check(c) for c in chosen]

    if args.json:
        print(json.dumps(build_document(results, branch), ensure_ascii=False, indent=2))
    elif args.markdown:
        print(render_markdown(results, branch))
    else:
        print(render_text(results, branch))

    if args.emit:
        out = Path(args.emit)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(build_document(results, branch), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        newline="\n")
        if not args.json and not args.markdown:
            print(f"结果已落盘：{out}")

    return overall(results)


if __name__ == "__main__":
    sys.exit(main())
