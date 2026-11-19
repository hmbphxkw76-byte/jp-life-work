"""个人财务模型：整合 01 收入 / 07 生活成本 / 14 初期费用 / 10 教习费 / 17 中介费，
自动计算「净储蓄率」与「回本周期」两个核心指标。

数据来源：各主题登记册活值（`data/*_indicator_registry.md`），本工具只读、不回写；
数值一律可追溯至「主题 + 登记册指标号 + 版本」，缺失值标「⚠ 待补」且不参与计算。

用法：
    python engine/tools/personal_finance_model.py            # 生成 md（默认写 00 data/）
    python engine/tools/personal_finance_model.py --json     # 输出机器可读 JSON
    python engine/tools/personal_finance_model.py --check    # 校验已生成 md 是否与重算一致

退出码：0 = 成功 / 一致；1 = 计算缺项或写入失败；2 = --check 不一致（仅警告）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, iter_business_dirs, load_decision_config  # noqa: E402

OUT_PATH = ROOT / "00-decision-hub" / "data" / "personal_finance_model.md"

# 参数外置：代表房租 / 社保负担率 / 登记册定位均读自 engine/config/decision-tools.json
# （单一事实源；硬编码漂移由 test_decision_config 守卫）。
_FINANCE_CFG = load_decision_config()["personal_finance_model"]
# 代表房租：UR 賃貸住宅收入基准阈值（12-culture-life 登记册 / 00 报告 5.2），
# 作为初期费用「4–7 个月房租」的折算基准；非个人记录。
REPRESENTATIVE_RENT = _FINANCE_CFG["representative_rent_jpy"]
# 社保负担率：07 报告「年金·社保约工资的 14–15% 负担」，取上限 15%（保守）。
SOCIAL_INSURANCE_RATE = _FINANCE_CFG["social_insurance_rate"]

# 登记册定位：(主题目录, 指标号, 值所在列索引)
# 01/07/10/14 为 5 列（值在第 4 列，索引 3）；17 为 12 列（值在第 5 列，索引 4）。
SOURCES = {k: tuple(v) for k, v in _FINANCE_CFG["sources"].items()}


# ──────────────────────────────────────────────
# 登记册读取
# ──────────────────────────────────────────────

def _registry_path(topic_dir: str) -> Path:
    for b in iter_business_dirs():
        if b.rel == topic_dir:
            for p in sorted((b.path / "data").glob("*_indicator_registry.md")):
                return p
    return ROOT / topic_dir / "data" / "_missing_registry.md"


def _read_rows(path: Path) -> dict[int, list[str]]:
    """解析登记册核心指标表 -> {指标号: [单元格...]}。"""
    rows: dict[int, list[str]] = {}
    if not path.exists():
        return rows
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or not re.fullmatch(r"\d+", cells[0]):
            continue
        rows[int(cells[0])] = cells
    return rows


def _cell(rows: dict[int, list[str]], num: int, idx: int = 3) -> str:
    """取某指标行的第 idx 个单元格（默认第 4 列 = 最新值）。"""
    cells = rows.get(num, [])
    return cells[idx] if idx < len(cells) else ""


# ──────────────────────────────────────────────
# 数值提取
# ──────────────────────────────────────────────

def _yen(text: str) -> float | None:
    """从文本提取「円」金额（含千分位）。"""
    m = re.search(r"([\d,]+(?:\.\d+)?)\s*円", text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _yen_range(text: str) -> tuple[float, float] | None:
    """提取「X–Y 万円」或「X–Y 円」区间。"""
    m = re.search(r"([\d.]+)\s*[–\-—]\s*([\d.]+)\s*万円", text)
    if m:
        return float(m.group(1)) * 10_000, float(m.group(2)) * 10_000
    m = re.search(r"([\d,]+)\s*[–\-—]\s*([\d,]+)\s*円", text)
    if m:
        return (float(m.group(1).replace(",", "")), float(m.group(2).replace(",", "")))
    return None


def _months(text: str) -> tuple[float, float] | None:
    """提取「合计可达 X–Y 个月」区间；找不到时回退到最后一个「X–Y 个月」。

    14 登记册原文含多项「0–2 个月 / 0.5–1 个月」等分项口径，
    必须优先取「合计可达 4–7 个月」这一总计口径，避免误取分项。
    """
    m = re.search(r"合计(?:可达)?\s*\**\s*(\d+)\s*[–\-—]\s*(\d+)\s*个?月", text)
    if m:
        return float(m.group(1)), float(m.group(2))
    hits = re.findall(r"(\d+)\s*[–\-—]\s*(\d+)\s*个?月", text)
    if hits:
        return float(hits[-1][0]), float(hits[-1][1])
    return None


def _sum_yen(text: str) -> float | None:
    """把文本中所有「円」金额相加（用于试验费等多项合计）。"""
    vals = [float(x.replace(",", "")) for x in re.findall(r"([\d,]+)\s*円", text)]
    return sum(vals) if vals else None


# ──────────────────────────────────────────────
# 模型计算
# ──────────────────────────────────────────────

def build_model() -> dict:
    """读取活值并计算，返回结构化结果（含缺失标记）。"""
    inputs: dict[str, dict] = {}
    missing: list[str] = []

    def reg(topic: str) -> tuple[Path, dict[int, list[str]]]:
        p = _registry_path(topic)
        return p, _read_rows(p)

    # 收入
    p, rows = reg(SOURCES["income"][0])
    income = _yen(_cell(rows, SOURCES["income"][1], SOURCES["income"][2]))
    inputs["income"] = {"topic": SOURCES["income"][0], "item": SOURCES["income"][1],
                        "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                        "raw": _cell(rows, SOURCES["income"][1], SOURCES["income"][2]), "value": income}
    if income is None:
        missing.append("01 收入（#5）")

    # 生活成本
    p, rows = reg(SOURCES["living"][0])
    living = _yen_range(_cell(rows, SOURCES["living"][1], SOURCES["living"][2]))
    inputs["living"] = {"topic": SOURCES["living"][0], "item": SOURCES["living"][1],
                        "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                        "raw": _cell(rows, SOURCES["living"][1], SOURCES["living"][2]), "value": list(living) if living else None}
    if not living:
        missing.append("07 生活成本（#7）")

    # 初期费用（月数 × 代表房租）
    p, rows = reg(SOURCES["initial_months"][0])
    months = _months(_cell(rows, SOURCES["initial_months"][1], SOURCES["initial_months"][2]))
    initial = (months[0] * REPRESENTATIVE_RENT, months[1] * REPRESENTATIVE_RENT) if months else None
    inputs["initial"] = {"topic": SOURCES["initial_months"][0], "item": SOURCES["initial_months"][1],
                         "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                         "raw": _cell(rows, SOURCES["initial_months"][1], SOURCES["initial_months"][2]),
                         "value": list(initial) if initial else None,
                         "rent": REPRESENTATIVE_RENT}
    if not initial:
        missing.append("14 初期费用（#4）")

    # 教习费
    p, rows = reg(SOURCES["driving"][0])
    driving = _yen(_cell(rows, SOURCES["driving"][1], SOURCES["driving"][2]))
    inputs["driving"] = {"topic": SOURCES["driving"][0], "item": SOURCES["driving"][1],
                         "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                         "raw": _cell(rows, SOURCES["driving"][1], SOURCES["driving"][2]), "value": driving}
    if driving is None:
        missing.append("10 教习费（#10）")

    # 中介费（登录费 + 行情中值 3 万円/月）
    p, rows = reg(SOURCES["intermediary"][0])
    inter_raw = _cell(rows, SOURCES["intermediary"][1], SOURCES["intermediary"][2])
    login = _yen(inter_raw)
    per_month = _yen_range(inter_raw)
    intermediary = login + (per_month[0] + per_month[1]) / 2 if login is not None and per_month else None
    inputs["intermediary"] = {"topic": SOURCES["intermediary"][0], "item": SOURCES["intermediary"][1],
                              "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                              "raw": inter_raw, "value": intermediary}
    if intermediary is None:
        missing.append("17 中介费（#12）")

    # 考试费
    p, rows = reg(SOURCES["exam"][0])
    exam_raw = _cell(rows, SOURCES["exam"][1], SOURCES["exam"][2])
    exam = _sum_yen(exam_raw)
    inputs["exam"] = {"topic": SOURCES["exam"][0], "item": SOURCES["exam"][1],
                      "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                      "raw": exam_raw, "value": exam}
    if exam is None:
        missing.append("01 考试费（#3）")

    result: dict = {"inputs": inputs, "missing": missing, "assumptions": {
        "representative_rent": REPRESENTATIVE_RENT,
        "social_insurance_rate": SOCIAL_INSURANCE_RATE,
    }}

    if missing:
        result["metrics"] = None
        return result

    living_low, living_high = living  # type: ignore[misc]
    take_home = income * (1 - SOCIAL_INSURANCE_RATE)
    save_high = take_home - living_low   # 生活成本低 → 储蓄高
    save_low = take_home - living_high   # 生活成本高 → 储蓄低
    initial_low, initial_high = initial  # type: ignore[misc]
    upfront_low = initial_low + driving + intermediary + exam
    upfront_high = initial_high + driving + intermediary + exam

    result["metrics"] = {
        "take_home_monthly": round(take_home, 2),
        "saving_monthly_low": round(save_low, 2),
        "saving_monthly_high": round(save_high, 2),
        "saving_rate_low": round(save_low / take_home, 4),
        "saving_rate_high": round(save_high / take_home, 4),
        "upfront_low": round(upfront_low, 2),
        "upfront_high": round(upfront_high, 2),
        "payback_months_low": round(upfront_low / save_high, 2),
        "payback_months_high": round(upfront_high / save_low, 2),
        "payback_months_mid": round(((upfront_low + upfront_high) / 2) / ((save_low + save_high) / 2), 2),
    }
    return result


# ──────────────────────────────────────────────
# 渲染
# ──────────────────────────────────────────────

def _fmt_yen(v: float) -> str:
    return f"{v:,.0f} 円"


def render_md(model: dict) -> str:
    lines: list[str] = []
    lines.append("# 赴日决策 · 个人财务模型（净储蓄率 / 回本周期）")
    lines.append("")
    lines.append("> **用途**：00 模块的**财务测算单一事实源**。整合 01 收入、07 生活成本、14 初期费用、10 教习费、17 中介费五大模块登记册活值，自动计算「净储蓄率」与「回本周期」。")
    lines.append("> **纪律**：只读引用各主题登记册活值，不独立改值；每个输入可追溯到「主题 + 指标号 + 版本」；缺失标「⚠ 待补」，不补值、不外推。")
    lines.append("> **生成**：`engine/tools/personal_finance_model.py`（确定性，无 mtime）。")
    lines.append("")
    lines.append("## 一、输入活值（五大模块）")
    lines.append("")
    lines.append("| 模块 | 来源主题 | 指标# | 原始值 | 采用值 |")
    lines.append("|---|---|---|---|---|")
    label = {"income": "收入", "living": "生活成本", "initial": "初期费用",
             "driving": "教习费", "intermediary": "中介费", "exam": "考试费"}
    for key, name in label.items():
        i = model["inputs"][key]
        val = i["value"]
        if isinstance(val, list):
            shown = f"{val[0]:,.0f} – {val[1]:,.0f} 円"
        elif val is None:
            shown = "⚠ 待补"
        else:
            shown = _fmt_yen(val)
        lines.append(f"| {name} | {i['topic']} | #{i['item']} | {i['raw']} | {shown} |")
    lines.append("")
    lines.append("**假设**：代表房租 " + _fmt_yen(REPRESENTATIVE_RENT) + "（UR 基準阈值，12-culture-life）；社保负担率 "
                 + f"{SOCIAL_INSURANCE_RATE:.0%}（07 报告 14–15% 取上限）；中介费按「登录费 + 行情中值 3 万円/月」计。")
    lines.append("")
    m = model.get("metrics")
    if not m:
        lines.append("## 二、计算结果")
        lines.append("")
        lines.append("⚠ **存在缺失输入，暂无法计算**：" + "、".join(model["missing"]) + "。补齐后重新运行工具。")
        lines.append("")
    else:
        lines.append("## 二、核心指标")
        lines.append("")
        lines.append("| 指标 | 区间 | 中值 | 口径 |")
        lines.append("|---|---|---|---|")
        lines.append(f"| 净储蓄率 | {m['saving_rate_low']:.1%} – {m['saving_rate_high']:.1%} | {(m['saving_rate_low']+m['saving_rate_high'])/2:.1%} | 月净储蓄 / 到手月收 |")
        lines.append(f"| 回本周期 | {m['payback_months_low']:.1f} – {m['payback_months_high']:.1f} 个月 | {m['payback_months_mid']:.1f} 个月 | 初期总投入 / 月净储蓄 |")
        lines.append("")
        lines.append("## 三、计算明细")
        lines.append("")
        lines.append("| 项 | 值 |")
        lines.append("|---|---|")
        lines.append(f"| 到手月收 | {_fmt_yen(m['take_home_monthly'])} |")
        lines.append(f"| 月净储蓄（低 / 高） | {_fmt_yen(m['saving_monthly_low'])} / {_fmt_yen(m['saving_monthly_high'])} |")
        lines.append(f"| 初期总投入（低 / 高） | {_fmt_yen(m['upfront_low'])} / {_fmt_yen(m['upfront_high'])} |")
        lines.append(f"| └ 初期费用（4–7 个月房租） | {_fmt_yen(model['inputs']['initial']['value'][0])} – {_fmt_yen(model['inputs']['initial']['value'][1])} |")
        lines.append(f"| └ 教习费 | {_fmt_yen(model['inputs']['driving']['value'])} |")
        lines.append(f"| └ 中介费 | {_fmt_yen(model['inputs']['intermediary']['value'])} |")
        lines.append(f"| └ 考试费 | {_fmt_yen(model['inputs']['exam']['value'])} |")
        lines.append("")
        lines.append("**敏感性**：回本周期对「生活成本」与「初期费用」最敏感；若实际房租高于代表值 62,500 円，初期费用与回本周期同步上升。")
        lines.append("")
    lines.append("## 四、局限")
    lines.append("")
    lines.append("1. 收入采用行业月均现金给与（含加班、全职务），**非个人 Offer 值**；实际以个人确定收入为准。")
    lines.append("2. 生活成本为手册估算（07 / 手册 02），**待个人收支结算记录后校准**。")
    lines.append("3. 初期费用未含机票、签证费、生活用品与储备金；中介费未含中国侧服务费（⚠ 待核实）。")
    lines.append("4. 本模型为规划估算，不构成投资 / 税务建议。")
    lines.append("")
    lines.append("## 五、版本记录")
    lines.append("")
    lines.append("| 版本 | 日期 | 变更 | 说明 |")
    lines.append("|---|---|---|---|")
    lines.append("| v1.0 | 2026-11-15 | 初始版本 | 建立五大模块整合模型；输出净储蓄率与回本周期 |")
    lines.append("")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="个人财务模型（净储蓄率 / 回本周期）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--check", action="store_true", help="校验已生成 md 是否与重算一致")
    ap.add_argument("--out", default=str(OUT_PATH), help="输出 md 路径")
    args = ap.parse_args()

    model = build_model()
    if args.json:
        print(json.dumps(model, ensure_ascii=False, indent=2))
        return 0 if not model["missing"] else 1

    content = render_md(model)
    out = Path(args.out)
    if args.check:
        if not out.exists():
            print(f"[ERROR] 缺少模型文件：{out}")
            return 1
        if out.read_text(encoding="utf-8") != content:
            print(f"[WARN] 模型文件已过期：{out}（运行工具重新生成）")
            return 2
        print("个人财务模型校验通过：与重算一致")
        return 0

    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
    except OSError as e:
        print(f"[ERROR] 写入失败：{e}")
        return 1
    print(f"个人财务模型已生成：{out.relative_to(ROOT)}")
    if model["missing"]:
        print("[ALERT] 缺失输入：" + "、".join(model["missing"]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
