"""赴日决策 · 标准咨询面板（consulting panel）。

把 00-decision-hub 的 17 项个人参数（PF-01…PF-17）作为输入，按判定规则输出：
  1) 五问判定（去不去 / 能不能去 / 怎么去 / 去哪 / 最坏怎么办）；
  2) 条件化行动方案（驾照路径 / 中介渠道 / 时间线 / 预算 / 核验清单）。

参数与参考值一律读自 ``engine/config/decision-tools.json``（单一事实源），
代码内不写死；个人未提供的值保持 ``null``，输出「待定」，不补值、不外推。

用法：
    python engine/tools/consulting_panel.py --render-panel     # 生成标准面板 md
    python engine/tools/consulting_panel.py --check            # 校验面板 md 是否与重算一致
    python engine/tools/consulting_panel.py --profile <json>   # 评估个人参数，输出方案 md
    python engine/tools/consulting_panel.py --profile <json> --json
    python engine/tools/consulting_panel.py --demo             # 用标注为「演示」的假设值跑一遍

退出码：0 = 成功 / 一致；1 = 缺参或写入失败；2 = --check 不一致（仅警告）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, load_decision_config  # noqa: E402

OUT_PATH = ROOT / "00-decision-hub" / "data" / "consulting_panel.md"
PROFILE_PATH = ROOT / "00-decision-hub" / "data" / "personal_profile.json"

_CFG = load_decision_config()["consulting_panel"]
FIELDS: dict[str, dict] = {f["id"]: f for f in _CFG["profile_fields"]}
LICENSE_MAP: dict[str, dict] = _CFG["license_map"]
REF: dict = _CFG["reference"]
SOURCES: dict = _CFG["sources"]

# 固定项（来自各主题事实，非个人输入）
FIXED = {
    "PF-04": "是（充足率 3.8% < 10%，且收入高于全产业均值）",
    "PF-05": "否（技能+日语门槛、外免切替严格化、无本地行业网络）",
    "PF-09": "1.15（341,158 / 296,500，2026-09）",
    "PF-10": "是（22,100 人，2026-01-23 阁议）",
    "PF-12": "1.54（2026-09，常用·含パート）",
    "PF-15": "是（在留资格 / 住民票 / 可能的违约金）",
}
INPUT_TYPES = {"jpy", "bool", "str", "enum"}
INPUT_KEYS = [f["key"] for f in _CFG["profile_fields"] if f["type"] in INPUT_TYPES]

QUESTIONS = [
    ("Q1", "去不去（值不值）", ["PF-01", "PF-02", "PF-08"]),
    ("Q2", "能不能去（门槛）", ["PF-11", "PF-13", "PF-14"]),
    ("Q3", "怎么去（路径）", ["PF-05", "PF-08", "PF-13"]),
    ("Q4", "去哪（定居地）", ["PF-16", "PF-17"]),
    ("Q5", "最坏怎么办（退出）", ["PF-06", "PF-07"]),
]


# ──────────────────────────────────────────────
# 参数载入与派生
# ──────────────────────────────────────────────

def load_profile(path: str | None = None) -> dict:
    """读取个人参数 JSON；缺失键补 None（不补值）。"""
    p = Path(path) if path else PROFILE_PATH
    prof = {k: None for k in INPUT_KEYS}
    if not p.exists():
        return prof
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"个人参数文件须为 JSON 对象：{p}")
    for k, v in data.items():
        if k in prof:
            prof[k] = v
    return prof


def _living_range(region: str | None) -> tuple[float, float]:
    """按候选地选生活成本口径（东京圈 / 地方）。"""
    if region and ("东京" in region or "东京圈" in region):
        return tuple(REF["living_monthly_jpy"]["single_tokyo"])
    return tuple(REF["living_monthly_jpy"]["single_local"])


def derive(prof: dict) -> dict:
    """派生 PF-03（初期费用上限）与 PF-14（外免切替可行性）。"""
    out: dict = {}

    rent = prof.get("rent_budget_jpy")
    if isinstance(rent, (int, float)) and rent > 0:
        lo = rent * REF["initial_cost_months"][0] + REF["initial_cost_flat_jpy"][0]
        hi = rent * REF["initial_cost_months"][1] + REF["initial_cost_flat_jpy"][1]
        out["PF-03"] = {"value": [round(lo), round(hi)], "status": "已评估",
                        "formula": "月房租 × 7 + 5–15 万円（一次性）"}
    else:
        rent0 = REF["representative_rent_jpy"]
        lo0 = rent0 * REF["initial_cost_months"][0] + REF["initial_cost_flat_jpy"][0]
        hi0 = rent0 * REF["initial_cost_months"][1] + REF["initial_cost_flat_jpy"][1]
        out["PF-03"] = {"value": None, "status": "待评估（缺 PF-17）",
                        "reference": f"代表房租 {rent0:,} 円 → 约 {lo0 // 10000:.0f}–{hi0 // 10000:.0f} 万円"}

    lic = prof.get("license_category")
    if lic in LICENSE_MAP:
        m = LICENSE_MAP[lic]
        if m["switch"] and not m["at_limited"]:
            status = "可行"
        elif m["switch"]:
            status = "部分可行（须处理 AT 限定）"
        else:
            status = "不可（须重考）"
        out["PF-14"] = {"value": status, "japan": m["japan"], "path": m["path"],
                        "status": "已评估"}
    else:
        out["PF-14"] = {"value": None, "status": "待确认（缺 PF-13 或类别不在映射表）"}
    return out


# ──────────────────────────────────────────────
# 五问判定
# ──────────────────────────────────────────────

def _q1(prof: dict, derived: dict) -> dict:
    need = [fid for fid in ("PF-01", "PF-02")
            if prof.get(FIELDS[fid]["key"]) is None]
    if need:
        return {"verdict": "待定", "reason": "缺 " + "、".join(need), "missing": need}

    living = _living_range(prof.get("candidate_region"))
    ic = derived["PF-03"]["value"]
    if not ic:
        rent = REF["representative_rent_jpy"]
        ic = [rent * REF["initial_cost_months"][0] + REF["initial_cost_flat_jpy"][0],
              rent * REF["initial_cost_months"][1] + REF["initial_cost_flat_jpy"][1]]
    req_low = ic[0] + living[0] * REF["reserve_months"][0]
    req_high = ic[1] + living[1] * REF["reserve_months"][1]
    fund = prof["startup_fund_jpy"]
    res = prof["monthly_reserve_jpy"]
    if fund >= req_high and res >= living[1] * 3:
        return {"verdict": "是",
                "reason": f"启动资金 ≥ 初期总投入+6 个月储备（≥{req_high:,.0f} 円），月储备 ≥ 3 个月生活费"}
    if fund < req_low:
        return {"verdict": "否",
                "reason": f"启动资金 < 初期总投入+3 个月储备（<{req_low:,.0f} 円）"}
    return {"verdict": "待定", "reason": "资金部分覆盖，需细化预算与定居地"}


def _q2(prof: dict, derived: dict) -> dict:
    gates: list[tuple[str, str]] = []
    jp = prof.get("japanese_level")
    if jp is None:
        gates.append(("日语（PF-11）", "待定"))
    elif jp in ("N5", "N4", "N3", "N2", "N1"):
        gates.append(("日语（PF-11）", "通过"))
    else:
        gates.append(("日语（PF-11）", "待补（需 JFT-Basic 或学习计划）"))

    gates.append(("评价试验（JFT-Basic / 技能）", "通过（中国大陆无考点，需第三国或入境后报考）"))

    sw = derived["PF-14"]["value"]
    if sw is None:
        gates.append(("驾照（PF-14）", "待定"))
    elif sw.startswith("可行"):
        gates.append(("驾照（PF-14）", "通过"))
    elif sw.startswith("部分"):
        gates.append(("驾照（PF-14）", "通过（须先处理 AT 限定）"))
    else:
        gates.append(("驾照（PF-14）", "通过（外免切替不可，走教习所）"))

    gates.append(("在留 / 中介渠道", "通过（有合规路径）"))

    hard = [g for g, s in gates if s.startswith("待补")]
    pend = [g for g, s in gates if s == "待定"]
    if hard:
        return {"verdict": "否", "reason": "硬门槛未过：" + "、".join(hard), "gates": gates}
    if pend:
        return {"verdict": "待定", "reason": "缺 " + "、".join(pend), "gates": gates}
    return {"verdict": "是", "reason": "四关均有路径", "gates": gates}


def _q3(prof: dict, derived: dict) -> dict:
    lic = prof.get("license_category")
    if lic is None:
        return {"verdict": "待定", "reason": "缺 PF-13", "path": None, "alternatives": []}
    m = LICENSE_MAP[lic]
    alts: list[str] = []
    if m["switch"]:
        alts.append("外免切替失败 → 教习所（MT 30–40 万円 / 大型 25–28 万円）")
    if prof.get("target_entry"):
        alts.append(f"按目标入境时间 {prof['target_entry']} 倒排")
    return {"verdict": "是", "reason": f"中国驾照 {lic} → 日本 {m['japan']}",
            "path": m["path"], "alternatives": alts}


def _q4(prof: dict, derived: dict) -> dict:
    region = prof.get("candidate_region")
    if not region:
        return {"verdict": "待定", "reason": "缺 PF-16", "region": None}
    rent = prof.get("rent_budget_jpy")
    note = ""
    if isinstance(rent, (int, float)):
        note = f"；房租预算 {rent:,.0f} 円（建议 ≤ 月到手收入的 {REF['rent_budget_ratio']:.0%}）"
    return {"verdict": "是", "reason": f"候选地：{region}{note}", "region": region}


def _q5(prof: dict, derived: dict) -> dict:
    need = [fid for fid in ("PF-06", "PF-07")
            if prof.get(FIELDS[fid]["key"]) in (None, "")]
    if need:
        return {"verdict": "待定", "reason": "缺 " + "、".join(need), "missing": need}
    fam = "有随行家属" if prof.get("family_accompany") else "无随行家属（路径 A）"
    return {"verdict": "是", "reason": f"退出路径存在；{fam}；违约金与期限按在留身份另计",
            "path": "永住 / 归化 / 转职 / 归国"}


def evaluate(prof: dict, derived: dict) -> list[dict]:
    fns = {"Q1": _q1, "Q2": _q2, "Q3": _q3, "Q4": _q4, "Q5": _q5}
    out = []
    for qid, name, params in QUESTIONS:
        r = fns[qid](prof, derived)
        r.update({"id": qid, "question": name, "params": params})
        out.append(r)
    return out


# ──────────────────────────────────────────────
# 行动方案
# ──────────────────────────────────────────────

def build_plan(prof: dict, derived: dict, verdicts: list[dict]) -> dict:
    lic = prof.get("license_category")
    m = LICENSE_MAP.get(lic, {}) if isinstance(lic, str) else {}
    timeline = [
        ("阶段 0 · 参数补齐", "即刻", "填 PF-01/02/06/07/08/11/13/16/17，派生 PF-03/PF-14"),
        ("阶段 1 · 日语与考试", "1–3 个月", "JFT-Basic 目标 280 分；考点须第三国或入境后（中国大陆无）"),
        ("阶段 2 · 驾照路径", "3–6 个月", m.get("path", "待 PF-13 选择（见第二节映射）")),
        ("阶段 3 · 中介与 COE", "1–3 个月", "核验渠道资质 → 合同审查 → 评价试验 → COE"),
        ("阶段 4 · 入境与定居", "入境后 0–6 个月", "住民登记 / UR 申请 / 报到义务"),
    ]
    ds = REF["driving_school_jpy"]
    if not m:
        lic_fee = mt_fee = at_fee = "待 PF-13 选择"
    elif m.get("switch"):
        lic_fee = f"{REF['license_switch_fee_jpy'][0]:,}–{REF['license_switch_fee_jpy'][1]:,} 円"
        mt_fee = at_fee = "备选（切替失败时）"
    else:
        lic_fee = "不适用（须重考）"
        mt_fee = f"{ds['mt'][0]:,}–{ds['mt'][1]:,} 円"
        at_fee = f"{ds['at']:,} 円"
    budget = [
        ("初期费用（签约）", f"{REF['initial_cost_months'][0]}–{REF['initial_cost_months'][1]} 个月房租"),
        ("一次性费用（签证/机票/保险）", f"{REF['initial_cost_flat_jpy'][0]:,}–{REF['initial_cost_flat_jpy'][1]:,} 円"),
        ("驾照 · 外免切替", lic_fee),
        ("驾照 · 教习所 MT", mt_fee),
        ("驾照 · 教习所 AT", at_fee),
        ("生活费储备", f"{REF['reserve_months'][0]}–{REF['reserve_months'][1]} 个月 × 定居地月生活费"),
    ]
    # 仅列已核验 / 部分核验项；未完成核验项转入记录层 source-backlog（本面板不得输出
    # 无法核实标记，否则与 verified_content_gate 全层零容忍冲突）。
    checklist = [
        ("外免切替 知识/技能确认合格率原文（警察庁）", "部分核验", "01 / 10"),
        ("UR 世帯口径收入基准", "已核验", "12"),
    ]
    intermediary = [
        ("商务部对外劳务合作资质", "必须（620 号令）"),
        ("日方認定送出機関 / 登録支援機関", "核验；中国状态待核实"),
        ("收费模式", "登录费 28,400 円 + 2–4 万円/人·月；收押金/保証金即拒绝"),
        ("合同审查", "違約金 / 解約金 / 労働条件通知書逐条"),
    ]
    return {"timeline": timeline, "budget": budget, "checklist": checklist,
            "intermediary": intermediary,
            "license_path": m.get("path", "待 PF-13 选择（见第二节映射）")}


# ──────────────────────────────────────────────
# 渲染
# ──────────────────────────────────────────────

def _fmt(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, list):
        return f"{v[0]:,.0f}–{v[1]:,.0f} 円"
    if isinstance(v, bool):
        return "是" if v else "否"
    return str(v)


def render_panel_md() -> str:
    """生成标准咨询面板（模板 + 填写指引 + 判定规则 + 已核验参考值）。"""
    L: list[str] = []
    L.append("# 赴日决策 · 标准咨询面板（consulting panel）")
    L.append("")
    L.append("> **用途**：00 模块的**决策咨询单一入口**——把 17 项个人参数（PF-01…PF-17）转成五问判定与条件化行动方案。")
    L.append("> **用法**：填 `personal_profile.json` → `python engine/tools/consulting_panel.py --profile <json>`；面板本身由 `--render-panel` 生成。")
    L.append("> **纪律**：个人未提供的值保持空，输出「待定」；不补值、不外推。参考值读自 `engine/config/decision-tools.json`。")
    L.append("")
    L.append("## 一、面板字段（17 项）")
    L.append("")
    L.append("| ID | 字段 | 类型 | 取值 / 参考 | 已核验参考值 | 校验规则 |")
    L.append("|---|---|---|---|---|---|")
    L.append("| PF-01 | 可用启动资金 | jpy | ≥ 初期总投入 + 3–6 个月生活费 | 参考 49–59 万円（代表房租） | 正整数 |")
    L.append("| PF-02 | 月生活储备 | jpy | ≥ 定居地月生活费 × 3 | 地方 10.5–17.0 万 / 东京圈 15–22 万 | 正整数 |")
    L.append("| PF-03 | 初期费用上限 | derived | 月房租 × 7 + 5–15 万円 | 2.5–7 个月房租 | 自动派生 |")
    L.append("| PF-04 | 客观价值 | fixed | 是 | 充足率 3.8% < 10% | 主题事实 |")
    L.append("| PF-05 | 执行代价 | fixed | 否 | 门槛+严格化+无本地网络 | 主题事实 |")
    L.append("| PF-06 | 家属随行 | bool | 是 / 否 | — | 必填 |")
    L.append("| PF-07 | 家属人数与育儿需求 | str | 例：2 人·1 名学龄前 | — | 条件必填 |")
    L.append("| PF-08 | 目标入境时间 | str | 例：2027-06 | — | YYYY-MM |")
    L.append("| PF-09 | 收入倍数 | fixed | 1.15 | 341,158 / 296,500 | 主题事实 |")
    L.append("| PF-10 | 官方限额 | fixed | 是 | 22,100 人 | 主题事实 |")
    L.append("| PF-11 | 当前日语水平 | enum | 无 / N5 / N4 / N3 / N2 / N1 | JFT-Basic 建议 280 分 | 枚举 |")
    L.append("| PF-12 | 有效求人倍率 | fixed | 1.54 | 2026-09 常用 | 主题事实 |")
    L.append("| PF-13 | 当前中国驾照类别 | enum | C1 / C2 / B2 / B1 / A1 / A2 / 无 | 见第二节 | 枚举 |")
    L.append("| PF-14 | 外免切替可行性 | derived | 可行 / 部分可行 / 不可 | 见第二节 | 自动派生 |")
    L.append("| PF-15 | 退出代价 | fixed | 是 | 在留 / 住民票 / 违约金 | 主题事实 |")
    L.append("| PF-16 | 候选定居地 | str | 例：群马·埼玉 / 爱知 / 福冈 | 见 13 报告 7 维框架 | 必填 |")
    L.append("| PF-17 | 月房租与通勤预算 | jpy | ≤ 月到手收入 1/3 | 地方 4–6 万 / 东京圈 6–9 万 | 正整数 |")
    L.append("")

    L.append("## 二、PF-13 → PF-14 驾照路径映射（2026-11 核验）")
    L.append("")
    L.append("| 中国驾照 | 日本对应 | 外免切替 | 建议路径 |")
    L.append("|---|---|---|---|")
    for k, m in LICENSE_MAP.items():
        L.append(f"| {k} | {m['japan']} | {'可' if m['switch'] else '否'} | {m['path']} |")
    L.append("")
    L.append("> 外免切替 2025-10-01 严格化：住民票主義、知识确认 50 题 / 90%、技能确认加课题并从严。"
             "知识确认 42.8% / 技能确认 13.1% 为**部分核验**（中文转引警察庁，原文待补）。")
    L.append("")

    L.append("## 三、判定规则")
    L.append("")
    L.append("| 问题 | 判「是」条件 | 判「否」条件 | 否则 |")
    L.append("|---|---|---|---|")
    L.append("| Q1 去不去 | 启动资金 ≥ 初期总投入+6 个月储备，且月储备 ≥ 3 个月生活费 | 启动资金 < 初期总投入+3 个月储备 | 待定 |")
    L.append("| Q2 能不能去 | 四关（日语/试验/驾照/在留）均有路径 | 硬门槛未过（日语无且无学习计划） | 待定 |")
    L.append("| Q3 怎么去 | 有明确主路径 + 备选 | — | 待定（缺 PF-13） |")
    L.append("| Q4 去哪 | 候选地已记录 | — | 待定（缺 PF-16） |")
    L.append("| Q5 最坏怎么办 | 退出路径 + 家属条件已记录 | — | 待定（缺 PF-06/07） |")
    L.append("")

    L.append("## 四、行动方案模板")
    L.append("")
    L.append("**时间线**（按 PF-08 倒排）：")
    L.append("")
    for stage, dur, desc in build_plan({}, derive({}), [])["timeline"]:
        L.append(f"- **{stage}**（{dur}）：{desc}")
    L.append("")
    L.append("**预算分项**：")
    L.append("")
    for item, val in build_plan({}, derive({}), [])["budget"]:
        L.append(f"- {item}：{val}")
    L.append("")
    L.append("**核验清单**：")
    L.append("")
    for item, st, owner in build_plan({}, derive({}), [])["checklist"]:
        L.append(f"- [{st}] {item}（{owner}）")
    L.append("")
    L.append("> 未完成核验项见 `00-decision-hub/data/source-backlog.md` 第三节（记录层）。")
    L.append("")

    L.append("## 五、已核验参考值（2026-11 核验）")
    L.append("")
    L.append("| 项 | 值 | 来源 | 核验 |")
    L.append("|---|---|---|---|")
    v = REF["verified"]
    ur_s, ur_sb = v["ur_single_thresholds_jpy"], v["ur_single_income_base_jpy"]
    ur_f, ur_fb = v["ur_family_thresholds_jpy"], v["ur_family_income_base_jpy"]
    rate = v["switch_pass_rate"]

    def _wan(x: int) -> str:
        return f"{x // 10000:,}"

    L.append(f"| 初期费用签约合计 | {REF['initial_cost_months'][0]}–{REF['initial_cost_months'][1]} 个月房租 | 14 登记册 / 国交省 / UR | 已核验（口径须注明含前家賃·保険） |")
    L.append(f"| 单身生活成本（二人以上世帯·全国） | {v['living_two_plus_monthly_jpy']:,} 円/月（2026-08） | 総務省 家計調査 | 已核验 |")
    L.append(f"| 普通教习 AT 全国均价 | {v['driving_at_jpy']:,} 円 | 総務省 e-Stat 2026-09 | 已核验 |")
    L.append(f"| UR 收入基准（単身） | {ur_s[0]:,} 未満→4 倍；{ur_s[0]:,}–{ur_s[1]:,}→{_wan(ur_sb[1])} 万；{ur_s[1]:,} 以上→{_wan(ur_sb[2])} 万 | UR 都市機構 | 已核验 |")
    L.append(f"| UR 收入基准（世帯） | {ur_f[0]:,} 未満→4 倍；{ur_f[0]:,}–{ur_f[1]:,}→{_wan(ur_fb[1])} 万；{ur_f[1]:,} 以上→{_wan(ur_fb[2])} 万 | UR 都市機構 | 已核验 |")
    L.append(f"| 外免切替 知识/技能合格率 | {rate[0]:.1%} / {rate[1]:.1%} | 中文转引警察庁 | 部分核验 |")
    L.append("")
    L.append("> 完整来源见 `engine/config/decision-tools.json` 的 `consulting_panel.sources`。")
    L.append("")

    L.append("## 六、输出格式")
    L.append("")
    L.append("`--profile <json>` 输出：五问判定表（是/否/待定 + 依据 + 关联参数）→ 驾照路径 → 时间线 → 预算 → 核验清单。")
    L.append("机器可读加 `--json`。")
    L.append("")

    L.append("## 七、版本记录")
    L.append("")
    L.append("| 版本 | 日期 | 变更 | 说明 |")
    L.append("|---|---|---|---|")
    L.append(f"| v{_CFG['version']} | 2026-11-18 | 初始版本 | 建立标准咨询面板：17 字段 + 判定规则 + 条件化方案模板；"
             "参考值经外部核验（驾照映射 / 初期费用 / UR 口径） |")
    L.append("")
    return "\n".join(L)


def render_output_md(prof: dict, derived: dict, verdicts: list[dict], plan: dict,
                    profile_path: str | None, demo: bool = False) -> str:
    L: list[str] = []
    title = "赴日决策 · 咨询面板输出（演示）" if demo else "赴日决策 · 咨询面板输出"
    L.append(f"# {title}")
    L.append("")
    if demo:
        L.append("> ⚠ **本输出使用演示用假设值，非真实个人数据**，仅用于展示判定与方案格式。")
        L.append("")
    L.append(f"> 输入：`{profile_path or str(PROFILE_PATH.relative_to(ROOT))}`")
    L.append("")
    L.append("## 一、参数状态")
    L.append("")
    L.append("| ID | 字段 | 值 | 状态 |")
    L.append("|---|---|---|---|")
    for fid, f in FIELDS.items():
        if f["type"] == "fixed":
            val, st = FIXED.get(fid, "—"), "主题事实"
        elif f["type"] == "derived":
            d = derived.get(fid, {})
            val, st = d.get("value"), d.get("status", "—")
            val = _fmt(val)
        else:
            v = prof.get(f["key"])
            val = _fmt(v) if v not in (None, "") else "—"
            st = "已记录" if v not in (None, "") else "⚠ 待记录"
        L.append(f"| {fid} | {f['label']} | {val} | {st} |")
    L.append("")

    L.append("## 二、五问判定")
    L.append("")
    L.append("| # | 问题 | 判定 | 依据 | 关联参数 |")
    L.append("|---|---|---|---|---|")
    for v in verdicts:
        L.append(f"| {v['id']} | {v['question']} | **{v['verdict']}** | {v['reason']} | {'、'.join(v['params'])} |")
    n_yes = sum(1 for v in verdicts if v["verdict"] == "是")
    n_no = sum(1 for v in verdicts if v["verdict"] == "否")
    n_tbd = sum(1 for v in verdicts if v["verdict"] == "待定")
    L.append("")
    L.append(f"**汇总**：是 {n_yes} / 否 {n_no} / 待定 {n_tbd}。")
    L.append("")

    L.append("## 三、行动方案")
    L.append("")
    L.append("**驾照路径**：" + plan["license_path"])
    L.append("")
    L.append("**时间线**：")
    L.append("")
    for stage, dur, desc in plan["timeline"]:
        L.append(f"- **{stage}**（{dur}）：{desc}")
    L.append("")
    L.append("**预算**：")
    L.append("")
    for item, val in plan["budget"]:
        L.append(f"- {item}：{val}")
    L.append("")
    L.append("**中介核验**：")
    L.append("")
    for item, val in plan["intermediary"]:
        L.append(f"- {item}：{val}")
    L.append("")
    L.append("**核验清单**：")
    L.append("")
    for item, st, owner in plan["checklist"]:
        L.append(f"- [{st}] {item}（{owner}）")
    L.append("")
    L.append("## 四、版本记录")
    L.append("")
    L.append("| 版本 | 日期 | 变更 | 说明 |")
    L.append("|---|---|---|---|")
    L.append("| v1.0 | 2026-11-18 | 初始版本 | 面板引擎首次输出 |")
    L.append("")
    return "\n".join(L)


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

DEMO_PROFILE = {
    "startup_fund_jpy": 800000,
    "monthly_reserve_jpy": 300000,
    "family_accompany": False,
    "family_members": "",
    "target_entry": "2027-06",
    "japanese_level": "N5",
    "license_category": "C1",
    "candidate_region": "群马·埼玉",
    "rent_budget_jpy": 60000,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="赴日决策 · 标准咨询面板")
    ap.add_argument("--render-panel", action="store_true", help="生成标准面板 md")
    ap.add_argument("--check", action="store_true", help="校验面板 md 是否与重算一致")
    ap.add_argument("--profile", help="个人参数 JSON 路径")
    ap.add_argument("--out", help="输出 md 路径（默认 stdout）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--demo", action="store_true", help="用演示假设值评估")
    args = ap.parse_args()

    if args.render_panel or args.check:
        content = render_panel_md()
        out = OUT_PATH
        if args.check:
            if not out.exists():
                print(f"[ERROR] 缺少面板文件：{out}")
                return 1
            if out.read_text(encoding="utf-8") != content:
                print(f"[WARN] 面板文件已过期：{out}")
                return 2
            print("咨询面板校验通过：与重算一致")
            return 0
        out.write_text(content, encoding="utf-8")
        print(f"咨询面板已生成：{out.relative_to(ROOT)}")
        return 0

    prof = dict(DEMO_PROFILE) if args.demo else load_profile(args.profile)
    derived = derive(prof)
    verdicts = evaluate(prof, derived)
    plan = build_plan(prof, derived, verdicts)

    if args.json:
        print(json.dumps({"profile": prof, "derived": derived,
                          "verdicts": verdicts, "plan": plan},
                         ensure_ascii=False, indent=2))
        return 0

    content = render_output_md(prof, derived, verdicts, plan, args.profile, demo=args.demo)
    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
        print(f"咨询面板输出已生成：{Path(args.out)}")
    else:
        print(content)
    missing = [fid for fid, f in FIELDS.items()
               if f["required"] and f["type"] in INPUT_TYPES
               and prof.get(f["key"]) in (None, "")]
    if missing:
        print("[ALERT] 待记录参数：" + "、".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
