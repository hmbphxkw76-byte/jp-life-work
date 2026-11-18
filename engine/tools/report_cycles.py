"""报告周期策略（月 / 季 / 年三档保留与展示窗口）。

规则（2026-11 体系）：
- 月度报告：保留近 18 个月，默认展示近 6 个月，超 6 个月折叠进「更多」，
  点击后完整展开至 18 个月；超 18 个月移入 archives/ 归档。
- 季度报告：保留并展示近 24 个月（8 个季度），按季度末月归档。
- 年度报告：保留并展示近 60 个月（5 份），按自然年归档。
- 更新一律在上一期（环比）基础上进行；无更新保持不变。
- 基准月 2026-11；2027-01 起以 2026-12 为环比基准。

周期归属按主题 business-config / prompts 自动识别（`detect_cycle`），
可用 engine/vocabulary/config/report-cycles.json 的 overrides 覆盖（可扩展）。

本模块为纯函数 + 配置读取，供 build_hub / build_index / archive_reports 消费。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, Business  # noqa: E402

# 周期窗口（保留 / 默认展示），单位：月。default == keep 时完整展示，不折叠。
CYCLE_WINDOWS: dict[str, dict] = {
    "monthly": {"keep_months": 18, "default_months": 6, "label": "月度", "cycle": "month"},
    "quarterly": {"keep_months": 24, "default_months": 24, "label": "季度", "cycle": "quarter"},
    "annual": {"keep_months": 60, "default_months": 60, "label": "年度", "cycle": "year"},
}

# 当前基准月：所有月报以此为基础做环比；下一期 2027-01 起切换为 2026-12。
BASELINE_PERIOD = "2026-11"

CONFIG_PATH = ROOT / "engine" / "vocabulary" / "config" / "report-cycles.json"

# 主题 prompts 文件 -> 周期线索
_ANNUAL_PROMPTS = ("prompt-annual-refresh.md", "prompt-annual-review.md")
_QUARTERLY_PROMPTS = ("prompt-quarterly-analysis.md",)
_MONTHLY_PROMPTS = ("prompt-monthly-monitor.md", "prompt-update.md")
_POLICY_PROMPTS = ("prompt-policy-review.md",)  # 事件触发 + 年度台账


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def load_config() -> dict:
    """读取 report-cycles.json；缺失 / 损坏时回退内置策略（不抛错）。"""
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"policy": CYCLE_WINDOWS, "baseline_period": BASELINE_PERIOD, "overrides": {}}
    policy = data.get("policy") or CYCLE_WINDOWS
    # 合并内置默认，缺项自动补齐（可扩展：新增周期只需在配置中追加）
    merged = {k: {**CYCLE_WINDOWS.get(k, {}), **v} for k, v in policy.items()}
    for k, v in CYCLE_WINDOWS.items():
        merged.setdefault(k, v)
    return {
        "policy": merged,
        "baseline_period": data.get("baseline_period", BASELINE_PERIOD),
        "overrides": data.get("overrides") or {},
    }


def _prompt_names(path: Path) -> set[str]:
    d = path / "prompts"
    if not d.is_dir():
        return set()
    return {f.name for f in d.glob("prompt-*.md")}


def detect_cycle_in(path: Path) -> dict:
    """按主题目录自动识别周期归属 -> {"primary", "cycles", "source"}。

    识别优先级（不改 business-config 结构，仅读既有内容）：
      1. prompt-annual-refresh / prompt-annual-review → annual
      2. prompt-quarterly-analysis                    → quarterly
      3. prompt-policy-review（事件 + 年度台账）      → annual
      4. prompt-monthly-monitor / prompt-update       → monthly
      5. business-config 文本含「季度」/「年度」        → quarterly / annual
      6. 兜底 monthly
    """
    names = _prompt_names(path)
    cfg = _read_text(path / "prompts" / "business-config.md")

    cycles: list[str] = []
    if names & set(_MONTHLY_PROMPTS):
        cycles.append("monthly")
    if names & set(_QUARTERLY_PROMPTS):
        cycles.append("quarterly")
    if names & set(_ANNUAL_PROMPTS) or names & set(_POLICY_PROMPTS):
        cycles.append("annual")

    if "prompt-annual-refresh.md" in names:
        primary, source = "annual", "prompt-annual-refresh"
    elif "prompt-quarterly-analysis.md" in names:
        primary, source = "quarterly", "prompt-quarterly-analysis"
    elif "prompt-annual-review.md" in names:
        primary, source = "annual", "prompt-annual-review"
    elif "prompt-policy-review.md" in names:
        primary, source = "annual", "prompt-policy-review"
    elif "prompt-monthly-monitor.md" in names:
        primary, source = "monthly", "prompt-monthly-monitor"
    elif "prompt-update.md" in names:
        primary, source = "monthly", "prompt-update"
    elif "季度" in cfg:
        primary, source = "quarterly", "business-config:季度"
    elif "年度" in cfg:
        primary, source = "annual", "business-config:年度"
    else:
        primary, source = "monthly", "fallback"

    if primary not in cycles:
        cycles.insert(0, primary)
    return {"primary": primary, "cycles": cycles, "source": source}


def cycle_profile_path(path: Path, rel: str = "") -> dict:
    """按主题目录路径生成周期画像（含窗口）。

    rel 用于 overrides 匹配（主题目录名，如 13-regional-info）；缺省取 path.name。
    """
    cfg = load_config()
    det = detect_cycle_in(Path(path))
    rel = rel or Path(path).name
    override = cfg["overrides"].get(rel)
    if override:
        primary = override.get("primary", det["primary"])
        source = "override"
    else:
        primary = det["primary"]
        source = det["source"]
    win = cfg["policy"].get(primary) or CYCLE_WINDOWS["monthly"]
    return {
        "primary": primary,
        "label": win["label"],
        "keep_months": int(win["keep_months"]),
        "default_months": int(win["default_months"]),
        "cycles": det["cycles"],
        "source": source,
        "override": bool(override),
    }


def cycle_profile(b: Business) -> dict:
    """主题周期画像（含窗口）-> {primary, label, keep_months, default_months, cycles, source, override}。

    先取自动识别结果，再应用 report-cycles.json 的 overrides（可扩展）。
    """
    return cycle_profile_path(b.path, b.rel)


def window_for(primary: str) -> dict:
    """按周期 ID 取窗口（供 build_index / archive_reports 使用）。"""
    cfg = load_config()
    win = cfg["policy"].get(primary) or CYCLE_WINDOWS.get(primary) or CYCLE_WINDOWS["monthly"]
    return {
        "label": win["label"],
        "keep_months": int(win["keep_months"]),
        "default_months": int(win["default_months"]),
    }


def period_month_index(period: str) -> int | None:
    """YYYY-MM -> 月序号（年*12+月-1），用于窗口比较；非法返回 None。"""
    m = re.fullmatch(r"(\d{4})-(\d{2})", period or "")
    if not m:
        return None
    y, mo = int(m.group(1)), int(m.group(2))
    if not 1 <= mo <= 12:
        return None
    return y * 12 + (mo - 1)


def month_index_period(idx: int) -> str:
    """月序号 -> YYYY-MM。"""
    y, mo = divmod(idx, 12)
    return f"{y:04d}-{mo + 1:02d}"


def start_period(months: int, now: str | None = None) -> str:
    """当前月（或指定月）往前推 months-1 个月的起始 YYYY-MM。"""
    from datetime import datetime
    if now is None:
        now = datetime.now().strftime("%Y-%m")
    base = period_month_index(now)
    if base is None:
        base = period_month_index(BASELINE_PERIOD) or 0
    return month_index_period(base - (months - 1))


def keep_periods(periods: list[str], keep_months: int, now: str | None = None) -> tuple[list[str], list[str]]:
    """按保留窗口切分 -> (保留期列表, 应归档期列表)。periods 需可解析为 YYYY-MM。"""
    start = start_period(keep_months, now)
    keep: list[str] = []
    archive: list[str] = []
    for p in periods:
        (keep if p >= start else archive).append(p)
    return keep, archive
