"""触发检测：watchlist 派生 + freshness 扫描 + 候选线索（PIPELINE-ORCHESTRATOR）。

对应 `docs/端到端流水线治理标准.md`「触发检测」：

- **W1 窗口到期**：复用 `update_planner.build_tasks` 的待办判定（节拍窗口已到且期望输出缺失）。
- **W2 核验超期**：登记册核验日期早于 `info_quality_check` 的 freshness 阈值（`STALE_DAYS`）。
- **W3 候选命中**：登记册「观察项与触发器状态」中带待办标记的线索（**仅提示，不核实**）。

纪律：
- watchlist **派生**自各主题 `business-config.md` §7 触发器与 `data/*_indicator_registry.md`，
  不新增手工配置；
- 默认**只读**（`--report` / 无参只写 stdout）；`--apply` 才写快照；
- 命中 ≠ 核实，语义确认由 Agent 完成；无触发不虚构。

用法：
    python engine/tools/trigger_watch.py --report [--period 2026-11]
    python engine/tools/trigger_watch.py --apply  [--period 2026-11]

退出码：0 = 正常（含空清单）；2 = 参数错误。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import update_planner  # noqa: E402
from _common import ROOT, atomic_write, iter_business_dirs  # noqa: E402

# freshness 阈值复用 info_quality_check（单一事实源，不另立口径）
from info_quality_check import STALE_DAYS, STALE_MONTHS  # noqa: E402

# 触发检测快照（设计文档 §3.4：engine/report-audits/pipeline/trigger-watch.json）
SNAPSHOT = ROOT / "engine" / "report-audits" / "pipeline" / "trigger-watch.json"

SEC7_RE = re.compile(r"^##\s*七、")
NEXT_SEC_RE = re.compile(r"^##\s")
DATE_RE = re.compile(r"(\d{4})[-.](\d{2})[-.](\d{2})")
VERSION_RE = re.compile(r"v(\d{4})\.(\d{2})\.(\d{2})")
OBSERVATION_SEC_RE = re.compile(
    r"^##\s*观察项与触发器状态.*?$(.*?)(?=^##\s|\Z)", re.M | re.S
)

# 候选线索关键词：仅匹配登记册「观察项与触发器状态」中明示的待办 / 未落地标记。
# 命中只作为本地线索提示，不代表来源已核实（纪律：命中 ≠ 核实）。
CANDIDATE_KEYWORDS = (
    "未发布",
    "待核实",
    "待核",
    "倒计时",
    "预计",
    "将于",
    "未同步",
    "未取得",
)


def _parse_triggers(config_text: str) -> list[str]:
    """从 business-config 文本解析 §7 触发器条目（每行 `- ...` 一条）。"""
    triggers: list[str] = []
    in_sec = False
    in_code = False
    for ln in config_text.splitlines():
        if SEC7_RE.match(ln):
            in_sec = True
            continue
        if in_sec and NEXT_SEC_RE.match(ln):
            break
        if not in_sec:
            continue
        stripped = ln.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code and stripped.startswith("- "):
            triggers.append(stripped[2:].strip())
    return triggers


def _max_column_date(text: str, col: str) -> str | None:
    """读取 Markdown 表格中指定列的最大日期（`YYYY-MM-DD`）；无则 None。"""
    idx: int | None = None
    dates: list[str] = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if col in cells:
                idx = cells.index(col)
                continue
            if idx is None:
                continue
            if all(set(c) <= set("-: ") for c in cells):
                continue  # 分隔行
            if len(cells) > idx:
                m = DATE_RE.search(cells[idx])
                if m:
                    dates.append("-".join(m.groups()))
        elif idx is not None:
            break  # 表格结束
    return max(dates) if dates else None


def _registry_last_verified(text: str) -> str | None:
    """登记册 -> 最近核验日期。

    新格式登记册读「核验日期」列；旧格式回退「基准版本」`vYYYY.MM.DD_N`。
    """
    d = _max_column_date(text, "核验日期")
    if d:
        return d
    versions = VERSION_RE.findall(text)
    if versions:
        return max(f"{y}-{m}-{d}" for y, m, d in versions)
    return None


def _find_registry(b) -> Path | None:
    """定位主题的指标登记册（`data/*_indicator_registry.md`）。"""
    data_dir = b.path / "data"
    if not data_dir.is_dir():
        return None
    regs = sorted(data_dir.glob("*_indicator_registry.md"))
    return regs[0] if regs else None


def build_watchlist() -> list[dict]:
    """派生触发 watchlist：每项含 `topic` / `trigger` / `source` / `last_verified`。

    - `topic`：业务目录名（如 `01-ssw-driver`）。
    - `trigger`：§7 触发器原文一行。
    - `source`：触发器出处（business-config 相对路径）。
    - `last_verified`：登记册最近核验日期（`YYYY-MM-DD` / `None`）。
    """
    out: list[dict] = []
    for b in iter_business_dirs():
        config = b.path / "prompts" / "business-config.md"
        if not config.is_file():
            continue
        reg = _find_registry(b)
        last_verified = None
        if reg is not None:
            last_verified = _registry_last_verified(reg.read_text(encoding="utf-8"))
        for trigger in _parse_triggers(config.read_text(encoding="utf-8")):
            out.append(
                {
                    "topic": b.region,
                    "trigger": trigger,
                    "source": f"{b.rel}/prompts/business-config.md",
                    "last_verified": last_verified,
                }
            )
    return out


def _registry_candidates(b) -> list[dict]:
    """从登记册「观察项与触发器状态」提取带待办标记的候选线索（仅提示）。"""
    out: list[dict] = []
    reg = _find_registry(b)
    if reg is None:
        return out
    text = reg.read_text(encoding="utf-8")
    m = OBSERVATION_SEC_RE.search(text)
    if not m:
        return out
    for ln in m.group(1).splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2 or not cells[0] or cells[0] == "状态项":
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        content = cells[1]
        hits = [k for k in CANDIDATE_KEYWORDS if k in content]
        if hits:
            out.append(
                {
                    "topic": b.region,
                    "trigger": f"{cells[0]}：{content}",
                    "source": f"{b.rel}/data/{reg.name}",
                    "keywords": hits,
                }
            )
    return out


def scan(period: str, now: datetime | None = None) -> dict:
    """触发检测扫描（确定性：不含当前时间戳，可重复执行零差异）。

    返回 `{"period", "window_due", "stale", "candidates"}`：
    - `window_due`：`update_planner` 判定为 pending 的节拍任务（窗口到期且输出缺失）。
    - `stale`：登记册核验日期早于 `STALE_DAYS` 的主题（附超期天数）。
    - `candidates`：登记册待办线索（仅提示，不核实；无命中为空）。
    """
    now = now or datetime.now(UTC)
    window_due = [
        t for t in update_planner.build_tasks(period, iter_business_dirs())
        if t.get("status") == "pending"
    ]
    stale: list[dict] = []
    for w in build_watchlist():
        lv = w.get("last_verified")
        if not lv:
            continue
        try:
            d = datetime.strptime(lv, "%Y-%m-%d").date()
        except ValueError:
            continue
        age = (now.date() - d).days
        if age > STALE_DAYS:
            stale.append(
                {
                    "topic": w["topic"],
                    "last_verified": lv,
                    "age_days": age,
                    "threshold_days": STALE_DAYS,
                    "threshold_months": STALE_MONTHS,
                }
            )
    candidates: list[dict] = []
    for b in iter_business_dirs():
        candidates.extend(_registry_candidates(b))
    return {
        "period": period,
        "window_due": window_due,
        "stale": stale,
        "candidates": candidates,
    }


def main_argv(argv: list[str] | None = None) -> int:
    """CLI 入口（便于测试注入 argv）。

    `--report` / 无参：只读，JSON 写 stdout；`--apply`：额外写 `SNAPSHOT`。
    """
    ap = argparse.ArgumentParser(description="触发检测：watchlist + freshness + 候选线索")
    ap.add_argument("--period", default="", help="周期标识（YYYY-MM / YYYY-Qn / YYYY），缺省按当前日期")
    ap.add_argument("--report", action="store_true", help="只读输出 JSON（默认行为，显式声明）")
    ap.add_argument("--apply", action="store_true", help="写快照 trigger-watch.json")
    args = ap.parse_args(argv)
    period = args.period or update_planner.default_period(datetime.now(UTC))
    payload = scan(period)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.apply:
        # engine/report-audits/pipeline/ 可能未被 git 跟踪（新克隆 / 清理后不存在），写前显式创建。
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(SNAPSHOT, text)
        print(f"已写入快照：{SNAPSHOT}")
    else:
        print(text)
    return 0


def main() -> int:
    return main_argv(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
