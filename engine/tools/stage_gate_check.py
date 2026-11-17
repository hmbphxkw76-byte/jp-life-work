"""阶段闸检查（信息生产全链路左移：采集 / 筛选 / 分类）。

定位：把「信息采集 → 筛选 → 分类」三阶段的质量门禁从报告交付层（F）左移到阶段出口，
在资产层（business-config / 指标登记册 / 类型引用）做形态与结构类检查。复用
`info_quality_check` 的登记册解析（单一判定内核），不新写判定规则。

覆盖（形态 / 结构类，秒级、无网络）：
- 闸1 采集：四层继承声明、运行变量、{{REGISTRY_PATH}} 指向存在、指标登记册存在；
- 闸2 筛选：登记册活值表 Schema（v1 / v2）、核验日期时效（与 C-08 同口径）；
- 闸3 分类：business-config 引用的类型 ID 已在 template-registry 注册。

语义类（来源语言规则、六族十三类选型判别、口径冲突裁决）不在本层——由提示词自检、
L5 语义复核与季度跨领域角色（R2 / R5）承载。详见 docs/信息生产全链路执行规范.md 第三节。

用法：
    python stage_gate_check.py                 # 全量
    python stage_gate_check.py --topic 01-ssw-driver
    python stage_gate_check.py --json

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
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    TEMPLATE_TYPE_DIRS,
    TYPE_RE,
    iter_business_dirs,
)
from info_quality_check import (  # noqa: E402
    STALE_DAYS,
    STALE_MONTHS,
    live_table,
    registry_latest_date,
)

REGISTRY_GLOB = "*_indicator_registry.md"
REGISTRY_PATH_RE = re.compile(r"\{\{REGISTRY_PATH\}\}\s*=\s*(\S+)")
P_LEVELS = {"P0": 0, "P1": 1, "P2": 2}


@dataclass
class Finding:
    """一条阶段闸发现。"""

    code: str       # G1-* / G2-* / G3-*
    severity: str   # P0/P1/P2
    location: str
    detail: str
    gate: str = ""


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def severity_counts(findings: list[Finding]) -> dict:
    c = {"P0": 0, "P1": 0, "P2": 0}
    for f in findings:
        c[f.severity] = c.get(f.severity, 0) + 1
    return c


# ──────────────────────────────────────────────
# 纯函数：对给定文本执行检查（可测试，不读文件）
# ──────────────────────────────────────────────

def gate1_collect(text: str) -> list[Finding]:
    """闸1 采集：business-config 的继承声明与运行变量。"""
    out: list[Finding] = []
    missing: list[str] = []
    if "prompt-generic-base.md" not in text:
        missing.append("通用基座 prompt-generic-base.md")
    if not TYPE_RE.search(text):
        missing.append("类型模板 report_templates/<类型ID>/")
    if missing:
        out.append(Finding("G1-INHERIT", "P1", "四层继承声明",
                           "business-config 未声明继承：" + "、".join(missing), "闸1"))
    vars_missing = [v for v in ("{{REGION}}", "{{TOPIC}}") if v not in text]
    if vars_missing:
        out.append(Finding("G1-VARS", "P2", "运行变量",
                           "business-config 缺少运行变量 " + "、".join(vars_missing), "闸1"))
    return out


def gate2_filter(registry_text: str) -> list[Finding]:
    """闸2 筛选：登记册活值表 Schema 与核验日期时效（C-08 同口径）。"""
    out: list[Finding] = []
    if live_table(registry_text) is None:
        out.append(Finding("G2-SCHEMA", "P1", "登记册活值表",
                           "未找到活值表（表头须含「指标」+「口径」或「优先数据源」）", "闸2"))
        return out
    d = registry_latest_date(registry_text)
    if d is not None and (date.today() - d).days > STALE_DAYS:
        out.append(Finding("G2-STALE", "P2", "登记册时效",
                           f"登记册最新核验日期 {d.isoformat()} 已超出 "
                           f"{STALE_MONTHS} 个月窗口（与 C-08 同口径）", "闸2"))
    return out


def gate3_classify(text: str) -> list[Finding]:
    """闸3 分类：business-config 引用的类型 ID 须已在 template-registry 注册。"""
    out: list[Finding] = []
    for t in sorted(set(TYPE_RE.findall(text))):
        if t not in TEMPLATE_TYPE_DIRS:
            out.append(Finding("G3-TYPE", "P1", "类型注册",
                               f"business-config 引用的类型 ID「{t}」未注册"
                               f"（template-registry / _common.TEMPLATE_TYPE_DIRS）", "闸3"))
    return out


# ──────────────────────────────────────────────
# 文件级：单主题与全量
# ──────────────────────────────────────────────

def check_topic(b) -> list[Finding]:
    """单主题阶段闸检查（读取其 business-config 与指标登记册）。"""
    out: list[Finding] = []
    cfg = b.path / "prompts" / "business-config.md"
    if not cfg.is_file():
        out.append(Finding("G1-CONFIG", "P2", "业务配置",
                           "缺少 prompts/business-config.md（骨架主题待建）", "闸1"))
        return out
    text = _read(cfg)
    out += gate1_collect(text)
    out += gate3_classify(text)

    declared = REGISTRY_PATH_RE.search(text)
    if declared and not (b.path / declared.group(1).strip()).is_file():
        out.append(Finding("G1-REGPATH", "P1", "登记册路径",
                           f"{{{{REGISTRY_PATH}}}} 声明的 {declared.group(1).strip()} 不存在", "闸1"))

    data_dir = b.path / "data"
    regs = sorted(data_dir.glob(REGISTRY_GLOB)) if data_dir.is_dir() else []
    if not regs:
        out.append(Finding("G1-REGISTRY", "P2", "指标登记册",
                           f"缺少 data/{REGISTRY_GLOB}（决策层 / 骨架主题可豁免）", "闸1"))
    else:
        out += gate2_filter(_read(regs[0]))
    return out


def run_all() -> tuple[list[dict], dict]:
    """全量检查全部业务主题。"""
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
    summary: dict[str, Any] = {
        "topics": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "by_severity": {"P0": 0, "P1": 0, "P2": 0},
    }
    for r in results:
        for k, v in r["severity"].items():
            summary["by_severity"][k] += v
    return results, summary


def main() -> int:
    ap = argparse.ArgumentParser(description="阶段闸检查（采集 / 筛选 / 分类左移）")
    ap.add_argument("--topic", help="单个主题目录名（如 01-ssw-driver）")
    ap.add_argument("--json", action="store_true", help="结果输出到 stdout（JSON）")
    args = ap.parse_args()

    if args.topic:
        matches = [b for b in iter_business_dirs() if b.rel == args.topic or b.region == args.topic]
        if not matches:
            print(f"[ERROR] 未找到主题：{args.topic}", file=sys.stderr)
            return 1
        findings = check_topic(matches[0])
        c = severity_counts(findings)
        if args.json:
            print(json.dumps({"topic": matches[0].rel, "severity": c,
                              "findings": [asdict(f) for f in findings]},
                             ensure_ascii=False, indent=2))
        else:
            print(f"{matches[0].rel}：{'通过' if not any(f.severity in ('P0','P1') for f in findings) else '不通过'}"
                  f"（P0 {c['P0']} / P1 {c['P1']} / P2 {c['P2']}）")
            for f in sorted(findings, key=lambda x: (P_LEVELS.get(x.severity, 9), x.code)):
                print(f"  [{f.severity}] {f.code} {f.location}：{f.detail}")
        if c["P0"] or c["P1"]:
            return 1
        return 2 if c["P2"] else 0

    results, summary = run_all()
    if args.json:
        print(json.dumps({
            "summary": summary,
            "results": [{"topic": r["topic"], "passed": r["passed"],
                         "severity": r["severity"],
                         "findings": [asdict(f) for f in r["findings"]]} for r in results],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"阶段闸检查：{summary['topics']} 个主题，"
              f"通过 {summary['passed']} / 不通过 {summary['failed']}")
        print(f"  P0 {summary['by_severity']['P0']} / "
              f"P1 {summary['by_severity']['P1']} / P2 {summary['by_severity']['P2']}")
        for r in results:
            if not r["passed"]:
                print(f"  [FAIL] {r['topic']}："
                      + "; ".join(f"{f.code}({f.severity})" for f in r["findings"]
                                  if f.severity in ("P0", "P1")))
    if summary["by_severity"]["P0"] or summary["by_severity"]["P1"]:
        return 1
    return 2 if summary["by_severity"]["P2"] else 0


if __name__ == "__main__":
    sys.exit(main())
