"""汇总页生成（CI: validate.yml --check 校验 / html-sync 重新生成）。

生成一个自包含静态页（无外部依赖，可直接 file:// 打开）：

**index.html**（主题报告索引）
- 主题与报告由构建时扫描发现（iter_business_dirs + reports/*.html）；
- 报告统一按自然月份聚合，命名 `YYYY-MM-<主题slug>`，不再区分基线 / 初析 /
  季度等类型；季度报告按季度末月归档（2026-Q4 -> 2026-12）；
- 展示窗口按周期类型（月 / 季 / 年，由 report_cycles.py 自动识别）：
  月度保留 18 个月、默认展示近 6 个月（「更多」展开至 18）；季度保留并展示
  近 24 个月（8 期）；年度保留并展示近 60 个月（5 份）；
- 环比更新提示：报告页 meta 携带跨期 diff 统计，汇总页据此高亮「已更新」
  并给出新增 / 修改 / 删除计数；无更新显示「无更新」，内容保持不变；
- 最新报告提示：每个主题的最新一期报告在主题卡片与详情页列表中高亮「新」标识
  （构建期确定性写入，取该主题 period 最大者）；
- 报告链接直达各主题 `reports/*.html` 独立报告页（新标签页打开），报告页内含
  构建期预渲染的跨月对比高亮（见 md2html.py / report_diff.py）；
- 搜索层：构建期生成 `search-index.json`（报告标题 / 关键词 / 命中问题，关键词
  由报告标题 + 章节 + 词库词条命中合成），并嵌入 index.html 供站内搜索使用。

--check 模式（validate.yml 使用）：重新计算内容与现有文件比对；
- 文件存在且一致 -> 退出码 0
- 文件存在但过期 -> 退出码 1（阻断合并）
- 文件不存在    -> 退出码 0 并提示（全新克隆尚未生成，由定时维护首建）

页脚不嵌入生成时间戳（避免 html-sync 每次产生仅时间戳变更的空提交）；
normalize_for_check 保留一个归一化函数，用于抹平历史版本页脚残留的时间戳行，
保证与旧提交内容可比。

退出码（生成模式）：0 = 成功；1 = 写入失败。
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    ROOT,
    TEMPLATE_ROOT,
    TYPE_LABEL_FALLBACK,
    TYPE_RE,
    atomic_write,
    detect_month_report,
    iter_business_dirs,
    month_to_date,
    report_title,
    topic_slug,
)
from report_cycles import cycle_profile  # noqa: E402

# 主题目录名：两位编号 + 短横线 + 短 slug（与 topics.json 的键对应）
NUM_RE = re.compile(r"^(\d{2})-(.+)$")

TOPIC_REGISTRY = ROOT / "engine" / "vocabulary" / "config" / "topics.json"

# 首页详情页展示窗口按周期类型动态计算（月 6 / 季 24 / 年 60），
# 由 report_cycles.py 依据主题 business-config / prompts 自动识别。
# 报告页 meta（md2html 写入）供汇总页判定环比更新状态。
REPORT_PERIOD_RE = re.compile(r'<meta name="report-period" content="([^"]*)">')
REPORT_CYCLE_RE = re.compile(r'<meta name="report-cycle" content="([^"]*)">')
REPORT_DIFF_RE = re.compile(r'<meta name="report-diff" content="([^"]*)">')


def parse_report_meta(text: str) -> dict:
    """解析报告页 meta -> {period, cycle_label, prev, new, mod, del}。"""
    def g(rx) -> str:
        m = rx.search(text)
        return html_mod.unescape(m.group(1)) if m else ""
    diff: dict[str, str] = {}
    for part in g(REPORT_DIFF_RE).split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            diff[k] = v
    return {
        "period": g(REPORT_PERIOD_RE),
        "cycle_label": g(REPORT_CYCLE_RE),
        "prev": diff.get("prev", "none"),
        "new": int(diff.get("new", 0) or 0),
        "mod": int(diff.get("mod", 0) or 0),
        "del": int(diff.get("del", 0) or 0),
    }


# ──────────────────────────────────────────────
# 纯函数：报告分类
# ──────────────────────────────────────────────

def classify_month_report(name: str):
    """报告文件名 -> (period, slug, date)；非月度报告返回 None。

    '2026-11-ssw-driver.html' -> ('2026-11', 'ssw-driver', '2026-11-30')
    """
    det = detect_month_report(name)
    if not det:
        return None
    period, slug, _ext = det
    date = month_to_date(period)
    if not date:
        return None
    return period, slug, date


# ──────────────────────────────────────────────
# 元数据加载
# ──────────────────────────────────────────────

def load_topic_registry() -> dict[str, dict]:
    """读取主题注册表（topics.json）-> {slug: meta}；缺失 / 损坏时返回空字典。"""
    try:
        data = json.loads(TOPIC_REGISTRY.read_text(encoding="utf-8"))
        topics = data.get("topics")
        return topics if isinstance(topics, dict) else {}
    except (OSError, ValueError):
        return {}


def load_type_labels() -> dict[str, str]:
    """类型 ID -> 类型名：优先解析 template-registry.md 第二节清单，失败回退内置表。"""
    labels = dict(TYPE_LABEL_FALLBACK)
    try:
        text = (TEMPLATE_ROOT / "template-registry.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return labels
    m = re.search(r"##\s*二、已注册类型清单(.*?)\n##\s", text, re.DOTALL)
    if not m:
        return labels
    for row in re.finditer(r"^\|\s*([a-z][a-z0-9-]*)\s*\|\s*([^|]+?)\s*\|", m.group(1), re.M):
        labels[row.group(1)] = row.group(2).strip()
    return labels


def _fallback_name(b) -> str:
    """主题显示名回退：business-config 首个一级标题（截去「· 业务专属配置」后缀）。"""
    cfg = b.path / "prompts" / "business-config.md"
    try:
        first = next(
            (ln[2:].strip() for ln in cfg.read_text(encoding="utf-8", errors="replace").splitlines()
             if ln.startswith("# ")),
            "",
        )
    except OSError:
        first = ""
    if first:
        return re.sub(r"\s*[·|].*$", "", first).strip() or first
    return b.rel


def _topic_type(b) -> str:
    """从 business-config 的类型模板引用提取类型 ID；缺失返回空串。"""
    cfg = b.path / "prompts" / "business-config.md"
    try:
        text = cfg.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    m = TYPE_RE.search(text)
    return m.group(1) if m else ""


# ──────────────────────────────────────────────
# 数据采集
# ──────────────────────────────────────────────

def collect_topic(b, registry: dict[str, dict], type_labels: dict[str, str]) -> dict:
    """单条业务线 -> {slug, rs, num, name, desc, type, type_label, reports[]}。

    reports 按代表日期降序（同期按 period、标题降序）。
    rs = 报告 slug（主题目录名去编号前缀）。
    """
    m = NUM_RE.match(b.rel)
    num, name_key = (m.group(1), m.group(2)) if m else ("", b.rel)
    rs = topic_slug(b.region if not b.property_type else b.property_type)
    # topics.json 键与主题目录名一致（NN-slug）；兼容旧 slug 键
    meta = registry.get(b.rel) or registry.get(name_key) or {}
    type_id = _topic_type(b)

    profile = cycle_profile(b)
    reports = []
    reports_dir = b.path / "reports"
    if reports_dir.is_dir():
        for f in sorted(reports_dir.glob("*.html")):
            cls = classify_month_report(f.name)
            if not cls:
                continue
            period, rslug, date = cls
            if rslug != rs:
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            title = report_title(text) or f.stem
            dm = parse_report_meta(text)
            changed = dm["new"] + dm["mod"] + dm["del"]
            updated = bool(dm["prev"] and dm["prev"] != "none" and changed > 0)
            delta = (f"较上期 {dm['prev']}：新增 {dm['new']} / 修改 {dm['mod']} / 删除 {dm['del']}"
                     if updated else "")
            reports.append({
                "title": title, "period": period, "date": date,
                "path": f"{b.rel}/reports/{f.name}", "is_latest": False,
                "cycle_label": dm["cycle_label"] or profile["label"],
                "updated": updated, "delta": delta, "prev_period": dm["prev"],
            })
    reports.sort(key=lambda r: (r["date"], r["period"], r["title"]), reverse=True)
    if reports:
        # 最新报告提示：仅标记该主题 period 最大者（构建期确定性，不依赖当前日期）
        reports[0]["is_latest"] = True

    return {
        "slug": b.rel, "rs": rs, "num": num,
        "name": meta.get("name") or _fallback_name(b),
        "desc": meta.get("description") or "",
        "type": type_id, "type_label": type_labels.get(type_id, type_id),
        "cycle": profile["primary"], "cycle_label": profile["label"],
        "keep_months": profile["keep_months"], "default_months": profile["default_months"],
        "cycle_source": profile["source"],
        "reports": reports,
    }


def collect_topics() -> list[dict]:
    """扫描全部业务线 -> 主题列表（按目录名升序，即编号顺序）。

    跳过完全空白的骨架目录（既无报告也无 business-config）。
    """
    registry = load_topic_registry()
    type_labels = load_type_labels()
    topics = []
    for b in iter_business_dirs():
        t = collect_topic(b, registry, type_labels)
        configured = (b.path / "prompts" / "business-config.md").exists()
        if not t["reports"] and not configured:
            continue
        topics.append(t)
    topics.sort(key=lambda t: t["slug"])
    return topics


# ──────────────────────────────────────────────
# 搜索索引（报告关键词 + 问题索引 + 词库打通）
# ──────────────────────────────────────────────

SEARCH_DIR = ROOT / "engine" / "search"
VOCAB_DATA = ROOT / "engine" / "vocabulary" / "data"
KEYWORDS_PATH = SEARCH_DIR / "keywords.json"
FIVEQ_PATH = SEARCH_DIR / "five-questions.json"


def _md_text(rel_path: str) -> str:
    p = ROOT / rel_path
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def _md_headings(text: str) -> list[str]:
    out = []
    for m in re.finditer(r"^##\s+(.+?)\s*$", text, re.M):
        t = re.sub(r"[`*_#]", "", m.group(1)).strip()
        if t:
            out.append(t)
    return out


def _load_vocab_terms() -> list[tuple[str, str, str]]:
    """(词条, 主题, 别名) 列表，来自各主题 terms.md（词库 → 搜索打通）。"""
    rows: list[tuple[str, str, str]] = []
    if not VOCAB_DATA.is_dir():
        return rows
    for f in sorted(VOCAB_DATA.glob("*/terms.md")):
        topic = f.parent.name
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for ln in lines:
            if not ln.startswith("| ") or ln.count("|") < 6:
                continue
            cells = [c.strip() for c in ln.split("|")]
            if len(cells) < 5:
                continue
            term = cells[2]
            if not term or term in ("词条", "---"):
                continue
            rows.append((term, topic, cells[3]))
    return rows


def load_keywords() -> dict[str, list[str]]:
    """读取主题级关键词表（engine/search/keywords.json）。"""
    try:
        data = json.loads(KEYWORDS_PATH.read_text(encoding="utf-8"))
        topics = data.get("topics")
        return topics if isinstance(topics, dict) else {}
    except (OSError, ValueError):
        return {}


def load_five_questions() -> list[dict]:
    """读取五问聚合视图数据（engine/search/five-questions.json）。"""
    try:
        data = json.loads(FIVEQ_PATH.read_text(encoding="utf-8"))
        qs = data.get("questions")
        return qs if isinstance(qs, list) else []
    except (OSError, ValueError):
        return []


def _report_keywords(rel_path: str, topic_name: str, type_label: str,
                     period: str, vocab: list[tuple[str, str, str]],
                     extra: list[str] | None = None) -> list[str]:
    text = _md_text(rel_path)
    kws: list[str] = []

    def add(k: str) -> None:
        k = (k or "").strip()
        if k and k not in kws:
            kws.append(k)

    add(topic_name)
    add(type_label)
    add(period)
    for k in (extra or [])[:12]:
        add(k)
    for h in _md_headings(text)[:6]:
        add(h)
    m = re.search(r"关[键鍵]词[：:]\s*(.+)", text)
    if m:
        for k in re.split(r"[,，、;；\s]+", m.group(1)):
            add(k)
    hits = 0
    for term, _t, aliases in vocab:
        if hits >= 20:
            break
        if term and term in text:
            add(term)
            hits += 1
            continue
        for a in aliases.split(";"):
            a = a.strip()
            if a and len(a) >= 2 and a in text:
                add(a)
                hits += 1
                break
    return kws[:24]


def collect_search_index(topics: list[dict]) -> dict:
    """构建标准化搜索索引：报告（标题 / 关键词 / 命中问题）+ 问题清单 + 五问视图。"""
    vocab = _load_vocab_terms()
    keywords = load_keywords()
    five = load_five_questions()
    reports: list[dict] = []
    for t in topics:
        for r in t["reports"]:
            md_rel = r["path"][:-5] + ".md" if r["path"].endswith(".html") else r["path"]
            reports.append({
                "topic": t["slug"], "topic_name": t["name"], "type": t["type"],
                "title": r["title"], "period": r["period"], "path": r["path"],
                "keywords": _report_keywords(md_rel, t["name"], t["type_label"],
                                             r["period"], vocab,
                                             extra=keywords.get(t["rs"])),
                "questions": [],
            })
    questions: list[dict] = []
    qf = SEARCH_DIR / "question-index.json"
    if qf.exists():
        try:
            data = json.loads(qf.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        for item in data.get("questions", []):
            q = (item.get("q") or "").strip()
            path = item.get("path") or ""
            if not q or not path:
                continue
            questions.append({"q": q, "path": path, "anchor": item.get("anchor", ""),
                              "group": item.get("group", "")})
            for rep in reports:
                if rep["path"] == path:
                    rep["questions"].append(q)
                    break
    return {"version": 2, "reports": reports, "questions": questions,
            "five_questions": five}


# ──────────────────────────────────────────────
# index.html 渲染
# ──────────────────────────────────────────────

HUB_CSS = """
:root{
  --bg:#f4f6f9; --card:#ffffff; --ink:#15202b; --ink2:#465667; --ink3:#6d7c8c;
  --line:#e1e7ee; --line2:#eef2f6;
  --navy:#16324f; --navy2:#2f5597; --blue:#3f6fb0; --blue-l:#eaf1fa;
  --green:#1c7444; --green-l:#eaf5ef;
  --amber:#9a6a12; --amber-l:#fdf4e2;
  --purple:#5b4b8a; --purple-l:#f0edf7;
  --gray:#74828f; --gray-l:#eff2f4;
  --radius:12px; --shadow:0 1px 3px rgba(20,40,70,.06);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{font-family:"Microsoft YaHei","PingFang SC","Segoe UI",Arial,sans-serif;
  background:var(--bg);color:var(--ink);line-height:1.7;font-size:14.5px}
a{color:var(--navy2);text-decoration:none}
a:hover{text-decoration:underline}
code{background:var(--gray-l);padding:1px 5px;border-radius:4px;font-size:12px}
[hidden]{display:none!important}

/* ── Hero ── */
.hero{background:linear-gradient(128deg,#0f2338 0%,#16324f 52%,#2f5597 100%);
  color:#fff;padding:48px 40px 42px;text-align:center}
.hero h1{font-size:27px;font-weight:700;letter-spacing:.4px;margin:0 0 4px}
.hero .stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px;justify-content:center}
.hero .stat{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);
  border-radius:10px;padding:8px 16px;font-size:12px;color:rgba(255,255,255,.85)}
.hero .stat b{font-size:20px;display:block;color:#fff;letter-spacing:.5px;line-height:1.3}

/* ── 筛选栏 ── */
.filterbar{position:sticky;top:0;z-index:40;
  background:rgba(244,246,249,.95);backdrop-filter:blur(6px);
  border-bottom:1px solid var(--line);padding:12px 24px;
  display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.filterbar>input{flex:1;min-width:220px;max-width:400px;padding:8px 14px;
  border:1px solid var(--line);border-radius:18px;font-size:13.5px;background:#fff;
  outline:none;font-family:inherit;color:var(--ink)}
.filterbar>input:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(63,111,176,.12)}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{border:1px solid var(--line);background:#fff;border-radius:14px;padding:4px 12px;
  font-size:12.5px;color:var(--ink2);cursor:pointer;user-select:none;font-family:inherit}
.chip:hover{border-color:var(--blue)}
.chip.on{background:var(--navy);border-color:var(--navy);color:#fff}
.filterbar .count{font-size:12px;color:var(--ink3);margin-left:auto;white-space:nowrap}
.search-results{max-width:1160px;margin:0 auto;padding:0 24px}
.search-results[hidden]{display:none}
.sr-head{font-size:12.5px;color:var(--ink3);padding:10px 4px 4px}
.sr-item{display:flex;gap:10px;align-items:baseline;padding:7px 10px;border:1px solid var(--line);
  border-radius:8px;margin-bottom:6px;background:#fff;flex-wrap:wrap}
.sr-item:hover{border-color:var(--blue);text-decoration:none}
.sr-period{font-size:12px;color:var(--ink3);white-space:nowrap}
.sr-title{font-size:13.5px;color:var(--navy);font-weight:600}
.sr-topic{font-size:12px;color:var(--ink2);margin-left:auto}

/* ── 主题卡片 ── */
.main{max-width:1240px;margin:0 auto;padding:8px 24px 50px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));
  gap:14px;margin:12px 0 6px}
.tcard{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  padding:16px 18px;display:flex;flex-direction:column;gap:8px;box-shadow:var(--shadow);
  transition:border-color .15s,box-shadow .15s}
.tcard:hover{border-color:#c9d6e6;box-shadow:0 4px 14px rgba(20,40,70,.09)}
.tcard .row1{display:flex;justify-content:space-between;align-items:center;gap:8px}
.badge{font-size:11px;border-radius:3px;padding:1px 7px;background:var(--blue-l);
  color:var(--navy2);white-space:nowrap;font-weight:600}
.tcard[data-type="industry-research"] .badge{background:var(--green-l);color:var(--green)}
.tcard[data-type="policy-analysis"] .badge{background:var(--amber-l);color:var(--amber)}
.tcard[data-type="market-monitoring"] .badge{background:var(--purple-l);color:var(--purple)}
.count{font-size:11.5px;color:var(--ink3);white-space:nowrap}
.tcard h4{font-size:16.5px;color:var(--navy);letter-spacing:.2px}
.tcard .desc{font-size:12.8px;color:var(--ink2);line-height:1.65;flex:1}
.tcard .reports{font-size:12px;color:var(--ink3);border-top:1px dashed var(--line);
  padding-top:8px;line-height:2}
.tcard .reports a{margin-right:12px;white-space:nowrap;font-size:12px}
.tcard .actions{display:flex;gap:8px;margin-top:2px;flex-wrap:wrap}
.btn{display:inline-block;font-size:12.5px;border-radius:7px;padding:6px 13px;
  border:1px solid var(--line);background:#fff;color:var(--navy2);cursor:pointer;
  font-family:inherit;line-height:1.5}
.btn:hover{text-decoration:none;border-color:var(--blue)}
.btn.primary{background:var(--navy);border-color:var(--navy);color:#fff}
.btn.primary:hover{background:var(--navy2);border-color:var(--navy2)}
/* ── 最新报告提示（构建期确定性高亮） ── */
.rnew{display:inline-block;font-size:10.5px;line-height:1.2;border-radius:3px;
  padding:1px 5px;background:var(--green);color:#fff;font-weight:700;
  vertical-align:1px;margin:0 2px;white-space:nowrap}
/* ── 环比更新标记 ── */
.upd{display:inline-block;font-size:10.5px;line-height:1.2;border-radius:3px;
  padding:1px 5px;font-weight:700;white-space:nowrap}
.upd.y{background:var(--green-l);color:var(--green)}
.upd.n{background:var(--gray-l);color:var(--gray)}
.delta{font-size:11.5px;color:var(--ink3);white-space:nowrap}
.tcard.is-empty{border-style:dashed;background:#fbfcfe}
.tcard.is-empty h4{color:var(--ink2)}
.tcard.is-empty .desc,.tcard.is-empty .reports{display:none}
.noresult{padding:44px 20px;text-align:center;color:var(--ink3);font-size:13.5px;
  grid-column:1/-1}

/* ── 决策者五问视图 ── */
.fq{max-width:1160px;margin:0 auto;padding:18px 24px 4px}
.fq h2{font-size:18px;color:var(--navy);margin:0 0 2px}
.fq-sub{font-size:12.5px;color:var(--ink3);margin:0 0 12px}
.fq-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}
.fq-card{display:block;background:#fff;border:1px solid var(--line);border-radius:10px;
  padding:12px 14px;box-shadow:var(--shadow)}
.fq-card:hover{border-color:var(--blue);text-decoration:none}
.fq-num{font-size:11px;color:var(--ink3)}
.fq-label{display:block;font-size:14px;font-weight:700;color:var(--navy);margin:2px 0 6px}
.fq-judgment{display:inline-block;font-size:12px;border-radius:4px;padding:1px 8px;
  background:var(--amber-l);color:var(--amber);font-weight:600}
.fq-basis{display:block;font-size:12px;color:var(--ink2);margin-top:6px;line-height:1.55}
.fq-conf{font-size:11px;color:var(--ink3)}

/* ── 主题详情页 ── */
#view-detail{display:none}
html.no-js #view-detail{display:block}
html.js.detail-mode #view-detail{display:block}
html.js.detail-mode #view-overview{display:none}
.detail-layout{display:flex;max-width:1440px;margin:0 auto;align-items:flex-start}
.sidebar{width:266px;flex:none;position:sticky;top:0;
  height:100vh;overflow-y:auto;padding:16px 10px 50px;
  border-right:1px solid var(--line);background:#fbfcfe}
.sidebar::-webkit-scrollbar{width:6px}
.sidebar::-webkit-scrollbar-thumb{background:#d3dce6;border-radius:3px}
.back-link{display:block;font-size:13px;color:var(--navy2);padding:6px 9px;
  border-radius:6px;margin:0 0 10px}
.back-link:hover{background:var(--blue-l);text-decoration:none}
.toc-topic{display:flex;align-items:baseline;gap:7px;font-size:13px;color:var(--ink2);
  padding:5px 9px;border-radius:6px;margin:2px 0;line-height:1.45}
.toc-topic:hover{background:var(--blue-l);text-decoration:none}
.toc-topic.active{background:var(--blue-l);color:var(--navy);font-weight:700}
.toc-topic .num{font-size:11px;color:var(--ink3);flex:none}
.detail-main{flex:1;min-width:0;padding:18px 26px 60px}
.topic-detail{display:block;scroll-margin-top:14px}
html.js .topic-detail{display:none}
html.js .topic-detail.active{display:block}
.topic-detail:target .topic-head{border-left-color:var(--amber);
  background:#fffdf6;border-radius:0 8px 8px 0}
.topic-head{border-left:4px solid var(--navy2);padding:2px 0 2px 12px;margin:6px 0 14px}
.topic-head .crumb{font-size:11.5px;color:var(--ink3);letter-spacing:.4px}
.topic-head h2{font-size:22px;color:var(--navy);margin:2px 0 6px}
.topic-head .desc{font-size:13px;color:var(--ink2);max-width:820px}
.topic-head .meta{font-size:12.5px;color:var(--ink3);margin-top:6px}
.report-filter{display:flex;align-items:center;gap:12px;flex-wrap:wrap;
  margin:2px 0 12px;font-size:12.5px;color:var(--ink3)}
.report-filter .rf-toggle{padding:4px 11px;font-size:12px}
.report-list{margin:6px 0 10px}
.report-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;
  padding:10px 16px;background:var(--card);border:1px solid var(--line);
  border-radius:10px;margin:8px 0;box-shadow:var(--shadow)}
.report-row:hover{border-color:#c9d6e6}
.report-row .rdate{font-size:12px;color:var(--ink3);
  font-variant-numeric:tabular-nums;white-space:nowrap;flex:none}
.report-row .rbadge{font-size:11px;border-radius:3px;padding:1px 7px;
  background:var(--blue-l);color:var(--navy2);white-space:nowrap;font-weight:600;flex:none}
.report-row .rt{font-size:14px;font-weight:700;color:var(--navy);
  flex:1;min-width:220px;line-height:1.5}
.report-row .rperiod{font-size:12px;color:var(--ink3);white-space:nowrap;flex:none}
.empty-note{border:1px dashed var(--line);border-radius:var(--radius);
  background:#fbfcfe;color:var(--ink3);font-size:13px;padding:26px;
  text-align:center;margin:14px 0}

/* ── 页脚 / 回到顶部 ── */
.footer{text-align:center;color:var(--ink3);font-size:11.5px;padding:26px 20px 36px;
  line-height:1.9;border-top:1px solid var(--line)}
.footer .muted{margin:0 0 4px}
.totop{position:fixed;right:22px;bottom:22px;width:40px;height:40px;border-radius:50%;
  background:var(--navy);color:#fff;border:0;font-size:17px;cursor:pointer;
  box-shadow:0 4px 14px rgba(15,35,56,.3);opacity:0;pointer-events:none;
  transition:opacity .2s;z-index:70;font-family:inherit}
.totop.show{opacity:1;pointer-events:auto}

/* ── 响应式 ── */
@media (max-width: 960px){
  .detail-layout{flex-direction:column}
  .sidebar{position:static;width:100%;height:auto;max-height:280px;border-right:0;
    border-bottom:1px solid var(--line)}
  .detail-main{padding:14px 14px 50px}
  .hero{padding:32px 22px 28px}
  .hero h1{font-size:22px}
  .filterbar{padding:10px 14px}
  .main{padding:6px 14px 40px}
  .cards{grid-template-columns:1fr}
  .totop{right:14px;bottom:14px}
}
"""

HUB_JS = """
(function () {
  'use strict';
  var root = document.documentElement;
  root.classList.remove('no-js');
  root.classList.add('js');

  function pad(n) { return (n < 10 ? '0' : '') + n; }

  /* ---------- 视图路由（hash：#topic-<目录名>） ---------- */
  function slugFromHash() {
    var m = /^#topic-(.+)$/.exec(location.hash || '');
    if (!m) return null;
    var slug = m[1];
    var sec = document.querySelector('.topic-detail[data-topic="' + slug + '"]');
    return sec ? slug : null;
  }
  function renderView() {
    var slug = slugFromHash();
    var secs = document.querySelectorAll('.topic-detail');
    for (var i = 0; i < secs.length; i++) {
      secs[i].classList.toggle('active', secs[i].getAttribute('data-topic') === slug);
    }
    root.classList.toggle('detail-mode', !!slug);
    var tocs = document.querySelectorAll('.toc-topic');
    for (var j = 0; j < tocs.length; j++) {
      tocs[j].classList.toggle('active',
        !!slug && tocs[j].getAttribute('href') === '#topic-' + slug);
    }
    if (slug) window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', renderView);

  /* ---------- 报告窗口过滤（月 / 季 / 年周期，按查看日期动态计算） ---------- */
  var details = document.querySelectorAll('.topic-detail');
  for (var k = 0; k < details.length; k++) {
    (function (sec) {
      var rows = sec.querySelectorAll('.report-row');
      var total = rows.length;
      var defaultMonths = parseInt(sec.getAttribute('data-default-months') || '6', 10);
      var keepMonths = parseInt(sec.getAttribute('data-keep-months') || '18', 10);
      var cycle = sec.getAttribute('data-cycle') || 'monthly';
      function startPeriod(months) {
        var now = new Date();
        var d = new Date(now.getFullYear(), now.getMonth() - (months - 1), 1);
        return d.getFullYear() + '-' + pad(d.getMonth() + 1);
      }
      var defaultStart = startPeriod(defaultMonths);
      var keepStart = startPeriod(keepMonths);
      var older = 0, beyond = 0;
      for (var i = 0; i < total; i++) {
        var p = rows[i].getAttribute('data-period');
        if (p < keepStart) {
          rows[i].style.display = 'none';
          rows[i].setAttribute('data-beyond', '1');
          beyond++;
        } else if (p < defaultStart) {
          rows[i].style.display = 'none';
          rows[i].setAttribute('data-old', '1');
          older++;
        }
      }
      var shown = total - older - beyond;
      var note = sec.querySelector('.rf-note');
      var toggle = sec.querySelector('.rf-toggle');
      function renderNote() {
        if (!note) return;
        note.textContent = '近 ' + defaultMonths + ' 个月 · 显示 ' + shown + ' / ' + total + ' 份'
          + (beyond ? '（另有 ' + beyond + ' 份已归档）' : '');
      }
      renderNote();
      if (toggle && older > 0) {
        toggle.hidden = false;
        toggle.textContent = '更多（' + older + '）';
        toggle.addEventListener('click', function () {
          var expanded = toggle.getAttribute('data-expanded') === '1';
          for (var i = 0; i < total; i++) {
            if (rows[i].getAttribute('data-beyond') === '1') continue;
            var isOld = rows[i].getAttribute('data-old') === '1';
            rows[i].style.display = (expanded && isOld) ? 'none' : '';
          }
          if (expanded) {
            toggle.setAttribute('data-expanded', '0');
            toggle.textContent = '更多（' + older + '）';
            renderNote();
          } else {
            toggle.setAttribute('data-expanded', '1');
            toggle.textContent = '收起';
            if (note) note.textContent = '已显示全部 ' + (total - beyond) + ' 份（含 ' + older + ' 份更早报告）';
          }
        });
      }
    })(details[k]);
  }

  /* ---------- 主题搜索 + 类型筛选 ---------- */
  var qInput = document.getElementById('hub-search');
  var countEl = document.getElementById('hub-count');
  var noResult = document.createElement('div');
  noResult.className = 'noresult';
  noResult.textContent = '未找到匹配的主题，请调整关键词或筛选条件。';
  var cardsBox = document.querySelector('.cards');
  if (cardsBox) cardsBox.appendChild(noResult);
  var state = { q: '', type: 'all' };
  function applyFilter() {
    var visible = 0;
    var cards = document.querySelectorAll('.tcard');
    for (var i = 0; i < cards.length; i++) {
      var card = cards[i];
      var okQ = !state.q ||
        card.getAttribute('data-search').toLowerCase().indexOf(state.q) >= 0;
      var okT = state.type === 'all' || card.getAttribute('data-type') === state.type;
      var show = okQ && okT;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    }
    noResult.style.display = visible ? 'none' : '';
    if (countEl) countEl.textContent = '共 ' + visible + ' 个主题';
  }

  /* ---------- 报告级命中（关键词 / 问题索引） ---------- */
  var resultsBox = document.getElementById('search-results');
  var SINDEX = window.SEARCH_INDEX || { reports: [], questions: [] };
  function _esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function renderReportHits() {
    if (!resultsBox) return;
    var q = state.q.trim().toLowerCase();
    if (q.length < 2) {
      resultsBox.hidden = true;
      resultsBox.innerHTML = '';
      return;
    }
    var hits = [];
    var reps = SINDEX.reports || [];
    for (var i = 0; i < reps.length; i++) {
      var r = reps[i];
      var hay = (r.topic_name + ' ' + r.title + ' ' + r.period + ' '
        + (r.keywords || []).join(' ') + ' ' + (r.questions || []).join(' ')).toLowerCase();
      if (hay.indexOf(q) >= 0) hits.push(r);
      if (hits.length >= 20) break;
    }
    if (!hits.length) {
      resultsBox.hidden = true;
      resultsBox.innerHTML = '';
      return;
    }
    var html = '<div class="sr-head">报告命中 ' + hits.length + ' 份</div>';
    for (var j = 0; j < hits.length; j++) {
      var h = hits[j];
      html += '<a class="sr-item" href="' + _esc(h.path) + '" target="_blank" rel="noopener">'
        + '<span class="sr-period">' + _esc(h.period) + '</span>'
        + '<span class="sr-title">' + _esc(h.title) + '</span>'
        + '<span class="sr-topic">' + _esc(h.topic_name) + '</span></a>';
    }
    resultsBox.innerHTML = html;
    resultsBox.hidden = false;
  }

  if (qInput) {
    var timer;
    qInput.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        state.q = qInput.value.trim().toLowerCase();
        applyFilter();
        renderReportHits();
      }, 120);
    });
  }
  var chips = document.getElementById('chips-type');
  if (chips) {
    chips.addEventListener('click', function (e) {
      var btn = e.target.closest('.chip');
      if (!btn) return;
      var all = chips.querySelectorAll('.chip');
      for (var i = 0; i < all.length; i++) all[i].classList.remove('on');
      btn.classList.add('on');
      state.type = btn.getAttribute('data-type');
      applyFilter();
    });
  }
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== qInput) {
      e.preventDefault();
      qInput.focus();
    }
  });
  applyFilter();

  /* ---------- 回到顶部 ---------- */
  var totop = document.getElementById('totop');
  window.addEventListener('scroll', function () {
    totop.classList.toggle('show', window.scrollY > 400);
  }, { passive: true });
  totop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  renderView();
})();
"""


def _badge_text(t: dict) -> str:
    return f'{t["num"]} · {t["type_label"]}' if t["type_label"] else (t["num"] or t["slug"])


def render_topic_card(t: dict) -> str:
    esc = html_mod.escape
    reports = t["reports"]
    latest = reports[0]["period"] if reports else ""
    parts = [t["name"], t["slug"], t["type_label"], t["desc"]] + [r["title"] for r in reports]
    search = esc(" ".join(p for p in parts if p))
    links = "".join(
        f'<a href="{esc(r["path"])}" target="_blank" rel="noopener" '
        f'title="{esc(r["title"])}">{esc(r["period"])}</a>'
        for r in reports[:4]
    )
    latest_btn = (
        f'<a class="btn" href="{esc(reports[0]["path"])}" target="_blank" rel="noopener">'
        f'最新报告 <span class="rnew">新</span> ↗</a>'
        if reports else ""
    )
    empty = " is-empty" if not reports else ""
    cycle_label = t.get("cycle_label", "月度")
    count = f'{len(reports)} 份报告 · {cycle_label}' if reports else "暂无报告"
    latest_note = f' · <span class="rnew">新</span> {esc(latest)}' if latest else ""
    return (
        f'<article class="tcard{empty}" data-type="{esc(t["type"])}" data-search="{search}">\n'
        f'  <div class="row1"><span class="badge">{_badge_text(t)}</span>'
        f'<span class="count">{count}{latest_note}</span></div>\n'
        f'  <h4>{esc(t["name"])}</h4>\n'
        f'  <p class="desc">{esc(t["desc"])}</p>\n'
        f'  <div class="reports">{links}</div>\n'
        f'  <div class="actions"><a class="btn primary" href="#topic-{esc(t["slug"])}">进入主题 →</a>'
        f'{latest_btn}</div>\n'
        f'</article>'
    )


def render_topic_detail(t: dict) -> str:
    esc = html_mod.escape
    reports = t["reports"]
    cycle = t.get("cycle", "monthly")
    cycle_label = t.get("cycle_label", "月度")
    default_months = int(t.get("default_months", 6))
    keep_months = int(t.get("keep_months", 18))
    rows = "".join(
        f'<div class="report-row" data-period="{esc(r["period"])}">\n'
        f'  <span class="rdate">{esc(r["period"])}</span>\n'
        + ('  <span class="rnew" title="本主题最新一期报告">新</span>\n'
           if r.get("is_latest") else "")
        + f'  <span class="rbadge">{esc(r.get("cycle_label") or cycle_label)}</span>\n'
        + (f'  <span class="upd y" title="{esc(r.get("delta", ""))}">已更新</span>\n'
           if r.get("updated") else '  <span class="upd n">无更新</span>\n')
        + f'  <a class="rt" href="{esc(r["path"])}" target="_blank" rel="noopener">'
        f'{esc(r["title"])}</a>\n'
        + (f'  <span class="delta">{esc(r["delta"])}</span>\n' if r.get("delta") else "")
        + f'  <span class="rperiod">{esc(r["period"])}</span>\n'
        f'</div>'
        for r in reports
    ) or '<p class="empty-note">该主题暂无已产出报告。</p>'
    crumb = f'主题 {t["num"]} · {t["type_label"]}' if t["type_label"] else f'主题 {t["num"]}'
    latest = (f' · 最新 <span class="rnew">新</span> {reports[0]["period"]}'
              if reports else '')
    return (
        f'<section class="topic-detail" id="topic-{esc(t["slug"])}" data-topic="{esc(t["slug"])}"'
        f' data-cycle="{esc(cycle)}" data-default-months="{default_months}"'
        f' data-keep-months="{keep_months}">\n'
        f'  <div class="topic-head">\n'
        f'    <div class="crumb">{esc(crumb)} · {esc(cycle_label)}</div>\n'
        f'    <h2>{esc(t["name"])}</h2>\n'
        f'    <p class="desc">{esc(t["desc"])}</p>\n'
        f'    <div class="meta">共 {len(reports)} 份报告{latest}</div>\n'
        f'  </div>\n'
        f'  <div class="report-filter">\n'
        f'    <span class="rf-note"></span>\n'
        f'    <button class="btn rf-toggle" hidden></button>\n'
        f'  </div>\n'
        f'  <div class="report-list">{rows}</div>\n'
        f'</section>'
    )


def render_sidebar(topics: list[dict]) -> str:
    esc = html_mod.escape
    items = "".join(
        f'<a class="toc-topic" href="#topic-{esc(t["slug"])}">'
        f'<span class="num">{esc(t["num"])}</span>{esc(t["name"])}</a>'
        for t in topics
    )
    return f'<a class="back-link" href="#/">← 返回主题总览</a>\n{items}'


def render_five_questions(five: list[dict]) -> str:
    """决策者五问视图：五张卡片（判定 / 依据 / 置信度 / 来源链接）。"""
    esc = html_mod.escape
    cards = []
    for i, q in enumerate(five, 1):
        href = esc(q["links"][0]) if q.get("links") else "#"
        cards.append(
            f'<a class="fq-card" href="{href}" target="_blank" rel="noopener">'
            f'<span class="fq-num">{i:02d}</span>'
            f'<span class="fq-label">{esc(q.get("label", ""))}</span>'
            f'<span class="fq-judgment">{esc(q.get("judgment", "待定"))}</span>'
            f'<span class="fq-basis">{esc(q.get("basis", ""))}</span>'
            f'<span class="fq-conf">置信度 {esc(q.get("confidence", ""))} · 待办 {esc(q.get("todo", ""))}</span>'
            f'</a>'
        )
    if not cards:
        return ""
    return (
        '<section class="fq">\n'
        '  <h2>决策者五问视图</h2>\n'
        '  <p class="fq-sub">去不去 · 能不能去 · 怎么去 · 去哪 · 最坏怎么办 —— 判定 / 依据 / 置信度 / 待办</p>\n'
        f'  <div class="fq-grid">{"".join(cards)}</div>\n'
        '</section>'
    )


def render_type_chips(topics: list[dict]) -> str:
    """类型筛选 chips：按主题编号顺序去重收集类型。"""
    esc = html_mod.escape
    seen: dict[str, str] = {}
    for t in topics:
        if t["type"] and t["type"] not in seen:
            seen[t["type"]] = t["type_label"]
    btns = ['<button class="chip on" data-type="all">全部类型</button>']
    for tid, label in seen.items():
        btns.append(f'<button class="chip" data-type="{esc(tid)}">{esc(label)}</button>')
    return "".join(btns)


def embed_json(obj) -> str:
    """嵌入 <script> 前转义 ``<``，防止 ``</script>`` 逃逸。"""
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")


def render_hub(topics: list[dict]) -> str:
    total_reports = sum(len(t["reports"]) for t in topics)
    cards = "".join(render_topic_card(t) for t in topics)
    details = "".join(render_topic_detail(t) for t in topics)
    sidebar = render_sidebar(topics)
    chips = render_type_chips(topics)
    search_index = collect_search_index(topics)
    search_json = embed_json(search_index)
    five_json = embed_json(search_index.get("five_questions", []))
    five_section = render_five_questions(search_index.get("five_questions", []))
    return f'''<!DOCTYPE html>
<html lang="zh-CN" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="日本生活与工作知识库报告索引：赴日决策五问、特定技能·签证·就业·生活·退出·家庭·防灾·中国侧衔接。">
<meta name="keywords" content="日本,在留,特定技能,签证,司机,生活,退出,家族,防灾,中介合规,赴日决策,五问,定居地,搜索">
<title>jp-life-work · 报告索引</title>
<style>{HUB_CSS}</style>
<script>document.documentElement.classList.remove('no-js');document.documentElement.classList.add('js');</script>
<script>var SEARCH_INDEX = {search_json};</script>
<script>var FIVE_QUESTIONS = {five_json};</script>
</head>
<body>
<div id="view-overview">
  <section class="hero">
    <h1>日本生活与工作 · 报告索引</h1>
    <div class="stats">
      <div class="stat"><b>{len(topics)}</b>主题</div>
      <div class="stat"><b>{total_reports}</b>报告总数</div>
    </div>
  </section>

  {five_section}

  <div class="filterbar">
    <input id="hub-search" type="search" placeholder="搜索主题 / 报告 / 关键词 / 五问…">
    <div class="chips" id="chips-type">{chips}</div>
    <span class="count" id="hub-count"></span>
  </div>

  <div class="search-results" id="search-results" hidden></div>

  <main class="main">
    <div class="cards">{cards}</div>
  </main>
</div>

<div id="view-detail">
  <div class="detail-layout">
    <aside class="sidebar">
      <nav>
        {sidebar}
      </nav>
    </aside>
    <main class="detail-main" id="detail-main">
      {details}
    </main>
  </div>
</div>

<footer class="footer">
  <p>由 <code>engine/tools/build_hub.py</code> 自动生成 · 主题与报告按目录自动发现，
  新增主题重新生成即扩展 · 报告源文件见各主题 <code>reports/</code> 目录</p>
</footer>
<button class="totop" id="totop" title="回到顶部">↑</button>
<script>{HUB_JS}</script>
</body>
</html>
'''


def build_outputs() -> dict[str, str]:
    topics = collect_topics()
    search_index = collect_search_index(topics)
    return {
        "index.html": render_hub(topics),
        "search-index.json": json.dumps(search_index, ensure_ascii=False, indent=2) + "\n",
    }


# 历史版本页脚曾含「最近生成」时间戳（分钟级心跳，随定时维护提交）；
# 现页脚已移除时间戳，此正则仅用于与旧提交内容比对时抹平该行的残留差异。
GENERATED_TS_RE = re.compile(r'\s*<p class="muted">最近生成：[^<]*</p>')


def normalize_for_check(text: str) -> str:
    """--check 比对专用归一化：移除历史版本页脚的「最近生成」时间戳行。

    纯函数，供 tests/ 直接调用。
    """
    return GENERATED_TS_RE.sub("", text)


def compare_outputs(outputs: dict[str, str]) -> tuple[list[str], list[str]]:
    """现有汇总页与重算内容比对 -> (stale, missing)。"""
    stale: list[str] = []
    missing: list[str] = []
    for name, content in outputs.items():
        f = ROOT / name
        if not f.exists():
            missing.append(name)
        elif normalize_for_check(f.read_text(encoding="utf-8", errors="replace")) != normalize_for_check(content):
            stale.append(name)
    return stale, missing


def main() -> int:
    ap = argparse.ArgumentParser(description="生成汇总页 index.html")
    ap.add_argument("--check", action="store_true", help="校验现有汇总页是否为最新")
    args = ap.parse_args()

    outputs = build_outputs()
    if args.check:
        stale, missing = compare_outputs(outputs)
        if stale:
            print(f"[ERROR] 汇总页已过期：{', '.join(stale)}（运行 python engine/tools/build_hub.py 重新生成）")
            return 1
        if missing:
            print(f"[WARN] 汇总页尚未生成：{', '.join(missing)}（由定时维护首建，不阻断）")
            return 0
        print("汇总页校验通过：index.html 为最新")
        return 0

    try:
        for name, content in outputs.items():
            atomic_write(ROOT / name, content)
    except OSError as e:
        print(f"[ERROR] 写入汇总页失败: {e}")
        return 1
    print("汇总页已生成：index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
