"""汇总页 + 报告阅读器生成（CI: validate.yml --check 校验 / html-sync 重新生成）。

生成两个自包含静态页（无外部依赖，可直接 file:// 打开）：

**index.html**（主题报告索引）
- 主题与报告由构建时扫描发现（iter_business_dirs + reports/*.html）；
- 报告统一按自然月份聚合，命名 `YYYY-MM-<主题slug>`，不再区分基线 / 初析 /
  季度等类型；季度报告按季度末月归档（2026-Q4 -> 2026-12）；
- 主题详情页默认展示最近 12 个月报告，按时间倒序（最新在顶端），可展开更早；
- 报告链接跳转 reader.html 阅读器（带跨月对比高亮）。

**reader.html**（报告阅读器）
- 内嵌全部主题的月度报告（构建期预渲染），版本切换为纯前端 show/hide，
  响应 < 1s；
- 每期报告自动与上一期（同主题、最近一个更早自然月）做全量内容比对，
  新增 / 修改片段高亮并加「已更新」标记，删除片段折叠可追溯；
- 支持「隐藏更新标记」对照阅读与「展开全部删除」。

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
    detect_month_report,
    iter_business_dirs,
    month_to_date,
    report_title,
    topic_slug,
)
from report_diff import diff_summary, render_diffed_body, strip_body  # noqa: E402

# 主题目录名：两位编号 + 短横线 + 短 slug（与 topics.json 的键对应）
NUM_RE = re.compile(r"^(\d{2})-(.+)$")

# business-config 中的类型模板引用（如 ../../src/report_templates/employment-research/）
TYPE_RE = re.compile(r"src/report_templates/([a-z][a-z0-9-]*)/")

# 类型名回退表（template-registry.md 解析失败时启用；与注册表第二节一致）
TYPE_LABEL_FALLBACK = {
    "market-monitoring": "市场指标监测型",
    "trend-weekly": "行业趋势周报型",
    "employment-research": "职业就业调研型",
    "competitive-intelligence": "竞争情报监测型",
    "sentiment-monitoring": "舆情传播监测型",
    "consumer-research": "消费者·用户调研型",
    "industry-research": "行业深度研究型",
    "market-sizing": "市场规模测算与预测型",
    "investment-research": "投资分析与尽调型",
    "policy-analysis": "政策法规解读型",
    "feasibility-study": "可行性与市场进入型",
    "flash-commentary": "快评·事件点评型",
    "whitepaper": "白皮书·专题深度型",
}

TOPIC_REGISTRY = ROOT / "src" / "vocabulary" / "config" / "topics.json"

# 阅读器默认展示窗口：最近 12 个自然月
RECENT_MONTHS = 12


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
    meta = registry.get(name_key) or {}
    type_id = _topic_type(b)

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
            title = report_title(f.read_text(encoding="utf-8", errors="replace")) or f.stem
            reports.append({
                "title": title, "period": period, "date": date,
                "path": f"{b.rel}/reports/{f.name}",
            })
    reports.sort(key=lambda r: (r["date"], r["period"], r["title"]), reverse=True)

    return {
        "slug": b.rel, "rs": rs, "num": num,
        "name": meta.get("name") or _fallback_name(b),
        "desc": meta.get("description") or "",
        "type": type_id, "type_label": type_labels.get(type_id, type_id),
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
# 阅读器数据（构建期预渲染跨月对比）
# ──────────────────────────────────────────────

def build_reader_data(topics: list[dict]) -> dict:
    """-> {report_slug: {name, dir, months: {period: {title, body, stats, summary, path}}}}。

    每期报告与上一期（同主题、最近一个更早自然月）比对，body 为含高亮标记的
    HTML 片段；首期报告无上期对比，body 原样。
    """
    data: dict[str, dict] = {}
    for t in topics:
        months: dict[str, dict] = {}
        prev_body: str | None = None
        prev_period: str | None = None
        for r in sorted(t["reports"], key=lambda x: x["period"]):
            html = (ROOT / r["path"]).read_text(encoding="utf-8", errors="replace")
            body = strip_body(html)
            diffed, stats = render_diffed_body(body, prev_body)
            months[r["period"]] = {
                "title": r["title"],
                "body": diffed,
                "stats": stats,
                "summary": diff_summary(stats, r["period"], prev_period),
                "path": r["path"],
            }
            prev_body, prev_period = body, r["period"]
        data[t["rs"]] = {"name": t["name"], "dir": t["slug"], "months": months}
    return data


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
.tcard.is-empty{border-style:dashed;background:#fbfcfe}
.tcard.is-empty h4{color:var(--ink2)}
.tcard.is-empty .desc,.tcard.is-empty .reports{display:none}
.noresult{padding:44px 20px;text-align:center;color:var(--ink3);font-size:13.5px;
  grid-column:1/-1}

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

  /* ---------- 近 12 个月报告过滤（按查看日期动态计算） ---------- */
  var details = document.querySelectorAll('.topic-detail');
  for (var k = 0; k < details.length; k++) {
    (function (sec) {
      var rows = sec.querySelectorAll('.report-row');
      var total = rows.length;
      var older = 0;
      // 最近 12 个自然月窗口：[当前月 - 11, 当前月]
      var now = new Date();
      var start = new Date(now.getFullYear(), now.getMonth() - (RECENT_MONTHS - 1), 1);
      var startPeriod = start.getFullYear() + '-' + pad(start.getMonth() + 1);
      for (var i = 0; i < total; i++) {
        if (rows[i].getAttribute('data-period') < startPeriod) {
          rows[i].style.display = 'none';
          older++;
        }
      }
      var recent = total - older;
      var note = sec.querySelector('.rf-note');
      var toggle = sec.querySelector('.rf-toggle');
      function renderNote() {
        if (!note) return;
        note.textContent = (recent === total)
          ? '近 12 个月 · 共 ' + total + ' 份'
          : '近 12 个月 · 显示 ' + recent + ' / ' + total + ' 份';
      }
      renderNote();
      if (toggle && older > 0) {
        toggle.hidden = false;
        toggle.textContent = '显示更早报告（' + older + '）';
        toggle.addEventListener('click', function () {
          var expanded = toggle.getAttribute('data-expanded') === '1';
          for (var i = 0; i < total; i++) {
            var isOld = rows[i].getAttribute('data-period') < startPeriod;
            rows[i].style.display = (expanded && isOld) ? 'none' : '';
          }
          if (expanded) {
            toggle.setAttribute('data-expanded', '0');
            toggle.textContent = '显示更早报告（' + older + '）';
            renderNote();
          } else {
            toggle.setAttribute('data-expanded', '1');
            toggle.textContent = '只看近 12 个月';
            if (note) {
              note.textContent = '已显示全部 ' + total + ' 份报告（含 ' + older + ' 份更早报告）';
            }
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
  if (qInput) {
    var timer;
    qInput.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        state.q = qInput.value.trim().toLowerCase();
        applyFilter();
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
        f'<a href="reader.html#topic={esc(t["rs"])}&month={esc(r["period"])}" '
        f'title="{esc(r["title"])}">{esc(r["period"])}</a>'
        for r in reports[:4]
    )
    latest_btn = (
        f'<a class="btn" href="reader.html#topic={esc(t["rs"])}&month={esc(reports[0]["period"])}">'
        f'最新报告 ↗</a>'
        if reports else ""
    )
    empty = " is-empty" if not reports else ""
    count = f'{len(reports)} 份报告' if reports else "暂无报告"
    latest_note = f' · 最新 {latest}' if latest else ""
    return (
        f'<article class="tcard{empty}" data-type="{esc(t["type"])}" data-search="{search}">\n'
        f'  <div class="row1"><span class="badge">{_badge_text(t)}</span>'
        f'<span class="count">{count}{esc(latest_note)}</span></div>\n'
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
    rows = "".join(
        f'<div class="report-row" data-period="{esc(r["period"])}">\n'
        f'  <span class="rdate">{esc(r["period"])}</span>\n'
        f'  <span class="rbadge">月度</span>\n'
        f'  <a class="rt" href="reader.html#topic={esc(t["rs"])}&month={esc(r["period"])}">'
        f'{esc(r["title"])}</a>\n'
        f'  <span class="rperiod">{esc(r["period"])}</span>\n'
        f'</div>'
        for r in reports
    ) or '<p class="empty-note">该主题暂无已产出报告。</p>'
    crumb = f'主题 {t["num"]} · {t["type_label"]}' if t["type_label"] else f'主题 {t["num"]}'
    latest = f' · 最新 {reports[0]["period"]}' if reports else ''
    return (
        f'<section class="topic-detail" id="topic-{esc(t["slug"])}" data-topic="{esc(t["slug"])}">\n'
        f'  <div class="topic-head">\n'
        f'    <div class="crumb">{esc(crumb)}</div>\n'
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


def render_hub(topics: list[dict]) -> str:
    esc = html_mod.escape
    total_reports = sum(len(t["reports"]) for t in topics)
    cards = "".join(render_topic_card(t) for t in topics)
    details = "".join(render_topic_detail(t) for t in topics)
    sidebar = render_sidebar(topics)
    chips = render_type_chips(topics)
    return f'''<!DOCTYPE html>
<html lang="zh-CN" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>jp-life-work · 报告索引</title>
<style>{HUB_CSS}</style>
<script>document.documentElement.classList.remove('no-js');document.documentElement.classList.add('js');</script>
<script>var RECENT_MONTHS = {RECENT_MONTHS};</script>
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

  <div class="filterbar">
    <input id="hub-search" type="search" placeholder="搜索主题 / 报告标题…">
    <div class="chips" id="chips-type">{chips}</div>
    <span class="count" id="hub-count"></span>
  </div>

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
  <p>由 <code>src/prompts-tools/tools/build_hub.py</code> 自动生成 · 主题与报告按目录自动发现，
  新增主题重新生成即扩展 · 报告源文件见各主题 <code>reports/</code> 目录</p>
</footer>
<button class="totop" id="totop" title="回到顶部">↑</button>
<script>{HUB_JS}</script>
</body>
</html>
'''


# ──────────────────────────────────────────────
# reader.html 渲染（报告阅读器：版本切换 + 跨月对比高亮）
# ──────────────────────────────────────────────

READER_CSS = """
:root{
  --bg:#f4f6f9; --card:#ffffff; --ink:#15202b; --ink2:#465667; --ink3:#6d7c8c;
  --line:#e1e7ee; --line2:#eef2f6;
  --navy:#16324f; --navy2:#2f5597; --blue:#3f6fb0; --blue-l:#eaf1fa;
  --green:#1c7444; --green-l:#eaf5ef;
  --amber:#9a6a12; --amber-l:#fdf4e2;
  --red:#a33a3a; --red-l:#fbecec;
  --radius:12px; --shadow:0 1px 3px rgba(20,40,70,.06);
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Microsoft YaHei","PingFang SC","Segoe UI",Arial,sans-serif;
  background:var(--bg);color:var(--ink);line-height:1.7;font-size:14.5px}
a{color:var(--navy2);text-decoration:none}
a:hover{text-decoration:underline}
[hidden]{display:none!important}

/* ── 布局 ── */
.reader{display:flex;min-height:100vh;align-items:flex-start}
.rd-sidebar{width:280px;flex:none;position:sticky;top:0;height:100vh;overflow-y:auto;
  border-right:1px solid var(--line);background:#fbfcfe;padding:14px 10px 40px}
.rd-sidebar::-webkit-scrollbar{width:6px}
.rd-sidebar::-webkit-scrollbar-thumb{background:#d3dce6;border-radius:3px}
.rd-brand{display:flex;align-items:center;gap:8px;padding:4px 8px 12px;
  border-bottom:1px solid var(--line);margin-bottom:10px}
.rd-brand .logo{width:26px;height:26px;border-radius:7px;flex:none;
  background:linear-gradient(128deg,#0f2338,#2f5597);color:#fff;display:flex;
  align-items:center;justify-content:center;font-size:13px;font-weight:700}
.rd-brand .name{font-size:13px;font-weight:700;color:var(--navy);line-height:1.35}
.rd-brand .sub{font-size:10.5px;color:var(--ink3);font-weight:400}
.rd-toc{display:flex;flex-direction:column;gap:2px}
.rd-toc a{display:flex;align-items:baseline;gap:7px;font-size:12.5px;color:var(--ink2);
  padding:5px 8px;border-radius:6px;line-height:1.4}
.rd-toc a:hover{background:var(--blue-l);text-decoration:none}
.rd-toc a.active{background:var(--blue-l);color:var(--navy);font-weight:700}
.rd-toc .num{font-size:10.5px;color:var(--ink3);flex:none}
.rd-toc .cnt{margin-left:auto;font-size:10.5px;color:var(--ink3);flex:none}

.rd-main{flex:1;min-width:0;padding:18px 26px 70px;max-width:1180px}

/* ── 报告头 ── */
.rd-head{position:sticky;top:0;z-index:30;background:rgba(244,246,249,.95);
  backdrop-filter:blur(6px);border-bottom:1px solid var(--line);
  margin:-18px -26px 16px;padding:14px 26px 10px}
.rd-head .crumb{font-size:11.5px;color:var(--ink3)}
.rd-head h1{font-size:21px;color:var(--navy);margin:2px 0 6px;line-height:1.4}
.rd-head .sum{font-size:12.5px;color:var(--ink2);margin-bottom:8px}
.rd-head .sum b{color:var(--navy)}
.rd-toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.rd-months{display:flex;flex-wrap:wrap;gap:6px}
.rd-month{font-size:12px;border:1px solid var(--line);background:#fff;border-radius:14px;
  padding:3px 11px;cursor:pointer;color:var(--ink2);font-family:inherit}
.rd-month:hover{border-color:var(--blue)}
.rd-month.on{background:var(--navy);border-color:var(--navy);color:#fff;font-weight:700}
.rd-month.old{opacity:.55}
.rd-toggle{font-size:12px;border:1px solid var(--line);background:#fff;border-radius:7px;
  padding:4px 11px;cursor:pointer;color:var(--navy2);font-family:inherit}
.rd-toggle:hover{border-color:var(--blue)}

/* ── 图例 ── */
.rd-legend{display:flex;flex-wrap:wrap;gap:12px;font-size:11.5px;color:var(--ink3);
  margin:0 0 12px}
.rd-legend .k{display:inline-flex;align-items:center;gap:5px}
.rd-legend .sw{width:12px;height:12px;border-radius:3px;display:inline-block}

/* ── 报告正文（沿用 md2html 通用模板风格） ── */
.rd-body{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
  padding:22px 26px 30px;box-shadow:var(--shadow);max-width:1160px}
.rd-body h1,.rd-body h2,.rd-body h3{color:#16213e}
.rd-body table{border-collapse:collapse;width:100%;overflow-x:auto;display:block;
  margin:10px 0;font-size:13px}
.rd-body th,.rd-body td{border:1px solid #cbd5e1;padding:6px 10px;text-align:left}
.rd-body th{background:#f1f5f9}
.rd-body img{max-width:100%}
.rd-body code{background:#f6f8fa;padding:2px 4px;border-radius:3px}
.rd-body blockquote{border-left:4px solid #94a3b8;margin:8px 0;
  padding-left:12px;color:#475569}
.rd-body pre{background:#f6f8fa;padding:10px;border-radius:6px;overflow-x:auto}
.rd-body pre code{background:none;padding:0}

/* ── 差异高亮 ── */
.diff-badge{display:inline-block;font-size:10.5px;font-weight:700;line-height:1;
  border-radius:3px;padding:2px 6px;margin-right:6px;vertical-align:middle;
  white-space:nowrap}
.diff-block{border-radius:6px;padding:4px 8px;margin:4px -8px}
.diff-new{background:var(--green-l);box-shadow:inset 3px 0 0 var(--green)}
.diff-new .diff-badge{background:var(--green);color:#fff}
.diff-mod{background:var(--amber-l);box-shadow:inset 3px 0 0 var(--amber)}
.diff-mod .diff-badge{background:var(--amber);color:#fff}
.diff-del-group{margin:6px 0;border:1px dashed var(--line);border-radius:6px;
  background:#fbfcfe}
.diff-del-group>summary{cursor:pointer;font-size:12px;color:var(--ink3);
  padding:6px 10px;user-select:none;list-style:none}
.diff-del-group>summary::-webkit-details-marker{display:none}
.diff-del-group>summary::before{content:"▸ ";color:var(--gray)}
.diff-del-group[open]>summary::before{content:"▾ "}
.diff-del-group .diff-del-body{padding:2px 8px 8px;color:var(--ink3)}
.diff-del-group .diff-del-body s,.diff-del-group .diff-del-body del{color:var(--red)}
.diff-del-group .diff-badge{background:var(--gray-l);color:var(--gray)}
/* 隐藏更新标记：对照阅读模式 */
.rd-body.hide-diff .diff-badge{display:none}
.rd-body.hide-diff .diff-block{background:none;box-shadow:none;padding:0;margin:0}
.rd-body.hide-diff .diff-del-group{display:none}

/* ── 空态 ── */
.rd-empty{padding:50px 20px;text-align:center;color:var(--ink3);font-size:13.5px}

/* ── 响应式 ── */
@media (max-width: 960px){
  .reader{flex-direction:column}
  .rd-sidebar{position:static;width:100%;height:auto;max-height:240px;border-right:0;
    border-bottom:1px solid var(--line)}
  .rd-main{padding:14px 14px 50px}
  .rd-head{margin:-14px -14px 14px;padding:12px 14px 8px}
  .rd-body{padding:16px}
}
"""

READER_JS = """
(function () {
  'use strict';
  var DATA = JSON.parse(document.getElementById('report-data').textContent);
  var RECENT_MONTHS = 12;

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  /* ---------- 侧栏主题列表 ---------- */
  function renderSidebar() {
    var box = $('#rd-toc');
    if (!box) return;
    var html = '';
    Object.keys(DATA).sort().forEach(function (rs) {
      var t = DATA[rs];
      var months = Object.keys(t.months).sort().reverse();
      html += '<a href="#topic=' + rs + '&month=' + months[0] + '" data-rs="' + rs + '">'
        + '<span class="num">' + (t.dir || '').replace(/^\\d+-/, '') + '</span>'
        + '<span>' + escapeHtml(t.name) + '</span>'
        + '<span class="cnt">' + months.length + ' 期</span></a>';
    });
    box.innerHTML = html;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  /* ---------- 路由 ---------- */
  function parseHash() {
    var h = location.hash || '';
    var m = /^#topic=([^&]+)(?:&month=(\\d{4}-\\d{2}))?/.exec(h);
    if (!m) return null;
    return { rs: decodeURIComponent(m[1]), month: m[2] || null };
  }

  function currentPeriods(rs) {
    return Object.keys(DATA[rs].months).sort();  // 升序（时间正序）
  }

  function render() {
    var route = parseHash();
    var sidebar = $('#rd-toc');
    if (!route || !DATA[route.rs]) {
      // 默认落到第一个主题的最新一期
      var first = Object.keys(DATA).sort()[0];
      if (first) {
        var months = currentPeriods(first);
        location.replace('#topic=' + first + '&month=' + months[months.length - 1]);
        return;
      }
      $('#rd-main').innerHTML = '<p class="rd-empty">暂无已产出报告。</p>';
      return;
    }
    var t = DATA[route.rs];
    var periods = currentPeriods(route.rs);
    var month = route.month && t.months[route.month] ? route.month : periods[periods.length - 1];
    var rec = t.months[month];

    // 侧栏高亮
    $all('a[data-rs]', sidebar).forEach(function (a) {
      a.classList.toggle('active', a.getAttribute('data-rs') === route.rs);
    });

    // 头部
    var now = new Date();
    var start = new Date(now.getFullYear(), now.getMonth() - (RECENT_MONTHS - 1), 1);
    var startPeriod = start.getFullYear() + '-' + pad(start.getMonth() + 1);
    var monthsHtml = periods.map(function (p) {
      var cls = 'rd-month' + (p === month ? ' on' : '') + (p < startPeriod ? ' old' : '');
      return '<button class="' + cls + '" data-month="' + p + '">' + p + '</button>';
    }).join('');
    var stats = rec.stats || {};
    $('#rd-head').innerHTML =
      '<div class="crumb">' + escapeHtml(t.dir) + ' · ' + escapeHtml(t.name) + '</div>'
      + '<h1>' + escapeHtml(rec.title || (month + ' 期报告')) + '</h1>'
      + '<div class="sum">' + escapeHtml(rec.summary || '') + '</div>'
      + '<div class="rd-toolbar">'
      +   '<div class="rd-months">' + monthsHtml + '</div>'
      +   '<button class="rd-toggle" id="tg-diff">隐藏更新标记</button>'
      +   '<button class="rd-toggle" id="tg-del">展开全部删除</button>'
      + '</div>';

    // 正文
    var body = $('#rd-body');
    body.innerHTML = rec.body || '<p class="rd-empty">本期报告无内容。</p>';

    // 月份切换
    $all('.rd-month', $('#rd-head')).forEach(function (btn) {
      btn.addEventListener('click', function () {
        var p = btn.getAttribute('data-month');
        if (p === month) return;
        location.hash = '#topic=' + route.rs + '&month=' + p;  // 触发 hashchange -> render
      });
    });

    // 对照阅读开关
    var tgDiff = $('#tg-diff');
    tgDiff.addEventListener('click', function () {
      var hide = body.classList.toggle('hide-diff');
      tgDiff.textContent = hide ? '显示更新标记' : '隐藏更新标记';
    });

    // 展开全部删除
    var tgDel = $('#tg-del');
    tgDel.addEventListener('click', function () {
      var open = tgDel.getAttribute('data-open') === '1';
      $all('details.diff-del-group', body).forEach(function (d) { d.open = !open; });
      tgDel.setAttribute('data-open', open ? '0' : '1');
      tgDel.textContent = open ? '展开全部删除' : '收起全部删除';
    });

    window.scrollTo(0, 0);
  }

  window.addEventListener('hashchange', render);
  renderSidebar();
  render();
})();
"""


def render_reader(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>jp-life-work · 报告阅读器</title>
<style>{READER_CSS}</style>
</head>
<body>
<div class="reader">
  <aside class="rd-sidebar">
    <div class="rd-brand">
      <div class="logo">报</div>
      <div class="name">日本生活与工作 · 报告阅读器</div>
      <div class="sub">月度报告 · 跨月对比高亮</div>
    </div>
    <nav class="rd-toc" id="rd-toc"></nav>
  </aside>
  <main class="rd-main">
    <div class="rd-head" id="rd-head"></div>
    <div class="rd-legend">
      <span class="k"><span class="sw" style="background:var(--green-l);box-shadow:inset 3px 0 0 var(--green)"></span>已更新 · 新增</span>
      <span class="k"><span class="sw" style="background:var(--amber-l);box-shadow:inset 3px 0 0 var(--amber)"></span>已更新 · 修改</span>
      <span class="k"><span class="sw" style="background:var(--gray-l)"></span>已更新 · 删除（折叠，可展开）</span>
      <span class="k">未变更内容保持原样</span>
    </div>
    <div class="rd-body" id="rd-body"></div>
  </main>
</div>
<script id="report-data" type="application/json">{payload}</script>
<script>{READER_JS}</script>
</body>
</html>
'''


# ──────────────────────────────────────────────
# 构建 / 校验
# ──────────────────────────────────────────────

def build_outputs() -> dict[str, str]:
    topics = collect_topics()
    reader_data = build_reader_data(topics)
    return {
        "index.html": render_hub(topics),
        "reader.html": render_reader(reader_data),
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
    ap = argparse.ArgumentParser(description="生成汇总页 index.html / reader.html")
    ap.add_argument("--check", action="store_true", help="校验现有汇总页是否为最新")
    args = ap.parse_args()

    outputs = build_outputs()
    if args.check:
        stale, missing = compare_outputs(outputs)
        if stale:
            print(f"[ERROR] 汇总页已过期：{', '.join(stale)}（运行 python src/prompts-tools/tools/build_hub.py 重新生成）")
            return 1
        if missing:
            print(f"[WARN] 汇总页尚未生成：{', '.join(missing)}（由定时维护首建，不阻断）")
            return 0
        print("汇总页校验通过：index.html / reader.html 均为最新")
        return 0

    try:
        for name, content in outputs.items():
            (ROOT / name).write_text(content, encoding="utf-8")
    except OSError as e:
        print(f"[ERROR] 写入汇总页失败: {e}")
        return 1
    print("汇总页已生成：index.html / reader.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
