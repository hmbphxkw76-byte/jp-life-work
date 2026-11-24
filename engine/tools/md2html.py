"""md -> HTML 同步（html-sync.yml 的 md2html 步骤）。

扫描各业务线 reports/*.md，转换为同名自包含 .html。报告页采用 macropulse-reports
设计范式（统一 navy 设计令牌）：

    skip-link -> header.hero（navy 标题带：eyebrow / h1 / tags；浅色 meta 面板：meta-grid / 审计徽章）
    -> nav.report-nav（sticky：报告路径 + 章节锚点 tabs + 跨月对比工具条）
    -> main.wrap（版本与运行变量卡 + h2.sec 章节）
    -> footer.footer（返回主题 / 返回首页）

**跨月对比高亮（构建期预渲染）**：每期报告自动与上一期（同主题、最近一个更早
自然月）比对，新增 / 修改片段高亮并加「已更新」徽章，删除片段折叠可追溯；
工具条提供「隐藏更新标记」对照阅读与「展开全部删除」。高亮由 report_diff.py
在构建期写入 HTML，前端 JS 仅负责开关，无 JS 时标记平铺可用。

幂等：重复执行产生相同输出。

退出码：0 = 成功（含无 md 可转换）；1 = 转换失败或依赖缺失。
"""
from __future__ import annotations

import argparse
import html as html_mod
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    HTML_TBODY_RE,
    HTML_THEAD_RE,
    HTML_TR_RE,
    ROOT,
    TYPE_LABEL_FALLBACK,
    TYPE_RE,
    is_complex_html_table,
    iter_business_dirs,
)
from report_cycles import cycle_profile_path  # noqa: E402
from report_diff import diff_summary, render_diffed_body  # noqa: E402

# ──────────────────────────────────────────────
# 设计令牌与样式（对齐 macropulse-reports 报告页）
# ──────────────────────────────────────────────

REPORT_CSS = """
:root{
  --radius-sm:8px; --radius:12px; --radius-lg:16px;
  --shadow:0 1px 3px rgba(20,40,70,.06); --shadow-md:0 4px 14px rgba(20,40,70,.09);
  --font-sans:"Microsoft YaHei","PingFang SC","Segoe UI",Arial,sans-serif;
  --font-mono:"SFMono-Regular",Consolas,"Liberation Mono",monospace;
  --focus-ring:0 0 0 3px rgba(63,111,176,.35);
  --bg:#f4f6f9; --card:#ffffff; --ink:#15202b; --ink2:#465667; --ink3:#657180;
  --line:#e1e7ee; --line2:#eef2f6;
  --navy:#16324f; --navy2:#2f5597; --blue:#3f6fb0; --blue-l:#eaf1fa;
  --red:#a83224; --red-d:#822116; --red-l:#fbece8;
  --pre:#b8541c; --pre-l:#fdf1e4;
  --green:#1c7444; --green-l:#eaf5ef;
  --amber:#956612; --amber-l:#fdf4e2;
  --gray:#646f7b; --gray-l:#eff2f4;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{font-family:var(--font-sans);background:var(--bg);color:var(--ink);line-height:1.76;font-size:14.5px}
a{color:var(--navy2);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1160px;margin:0 auto;padding:0 24px 68px}

/* ── 跳转链接 / 焦点环 ── */
.skip-link{position:absolute;left:12px;top:-48px;z-index:100;background:var(--navy);
  color:#fff;padding:8px 16px;border-radius:0 0 8px 8px;font-size:12.5px;transition:top .15s ease}
.skip-link:focus{top:0;color:#fff;text-decoration:none}
:focus-visible{outline:none;box-shadow:var(--focus-ring)}

/* ── 已审计徽章 ── */
.audit-badge{display:inline-flex;align-items:center;gap:10px;flex-wrap:wrap;
  background:var(--green-l);border:1px solid var(--green);border-radius:10px;
  padding:8px 14px;margin:0 0 14px;font-size:12.5px;color:var(--green)}
.audit-badge .audit-seal{font-weight:700;white-space:nowrap}
.audit-badge .audit-meta{color:var(--ink2)}

/* ── 题头 Hero（分层：navy 标题带 + 浅色 meta 面板） ── */
.hero{margin-bottom:20px}
.hero .wrap{padding-bottom:0}
.hero-band{background:linear-gradient(128deg,#0f2338 0%,#16324f 52%,#2f5597 100%);color:#fff;
  padding:14px 0 12px;border-radius:0 0 14px 14px}
.hero-top{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.hero-band .eyebrow{font-size:10.5px;letter-spacing:2px;color:rgba(255,255,255,.62);text-transform:uppercase}
.hero-band h1{font-size:21px;font-weight:700;letter-spacing:.3px;margin:5px 0 0;line-height:1.3}
.hero-band .tags{display:flex;flex-wrap:wrap;gap:6px}
.hero-band .tag{display:inline-block;background:rgba(255,255,255,.11);border:1px solid rgba(255,255,255,.2);
  border-radius:14px;padding:1px 10px;font-size:11px}
.hero-panel{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;
  background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:8px 12px;margin-top:8px;box-shadow:var(--shadow)}
.meta-grid{flex:1 1 0;min-width:0;column-count:2;column-gap:20px;
  font-size:11.4px;line-height:1.45;color:var(--ink2)}
.meta-grid .meta-item{break-inside:avoid;margin:0 0 2px;min-width:0;overflow-wrap:anywhere}
.meta-grid .meta-item b{color:var(--navy)}
.hero-panel .audit-badge{margin:0;flex:0 0 300px;font-size:12px;padding:6px 12px}
@media (max-width:900px){
  .hero-panel{flex-direction:column;align-items:stretch}
  .hero-panel .audit-badge{flex:1 1 auto}
  .meta-grid{column-count:1}
}

/* ── 报告导航（sticky） ── */
.report-nav{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.96);
  border-bottom:1px solid var(--line);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);
  margin-bottom:26px}
.report-nav .wrap{padding-top:10px;padding-bottom:10px}
.nav-url{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;font-size:11.5px;
  line-height:1.6;color:var(--ink3);padding-bottom:6px;margin-bottom:6px;
  border-bottom:1px dashed var(--line)}
.nav-url-label{font-weight:700;color:var(--ink2);white-space:nowrap}
.nav-url a{color:var(--blue);word-break:break-all}
.nav-tabs{display:flex;flex-wrap:wrap;gap:6px}
.nav-tabs a{color:var(--ink2);font-size:12.5px;padding:5px 10px;border-radius:6px;
  transition:background .15s ease,color .15s ease}
.nav-tabs a:hover{background:var(--blue-l);color:var(--blue)}

/* ── 跨月对比工具条 ── */
.diff-bar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;
  margin-top:8px;padding-top:8px;border-top:1px dashed var(--line);
  font-size:12px;color:var(--ink3)}
.diff-bar .diff-summary{flex:1;min-width:200px;line-height:1.6}
.diff-bar .diff-summary b{color:var(--navy)}
.diff-toggle{font-size:12px;border:1px solid var(--line);background:#fff;border-radius:7px;
  padding:4px 11px;cursor:pointer;color:var(--navy2);font-family:inherit}
.diff-toggle:hover{border-color:var(--blue)}

/* ── 正文 ── */
h2.sec{font-size:20px;color:var(--navy);margin:44px 0 4px;padding-left:12px;
  border-left:4px solid var(--navy2);font-weight:700;scroll-margin-top:110px}
h3{font-size:15.5px;color:var(--navy);margin:22px 0 8px;font-weight:700}
h4{font-size:14px;color:var(--navy);margin:16px 0 6px;font-weight:700}
p{margin:0 0 12px}
ul,ol{padding-left:22px;margin:8px 0 14px}
li{margin-bottom:6px}
hr{border:0;border-top:1px solid var(--line);margin:26px 0}
strong{color:var(--ink)}
code{background:#f6f8fa;padding:2px 5px;border-radius:4px;font-family:var(--font-mono);font-size:12.5px}
pre{background:#f6f8fa;padding:12px 14px;border-radius:8px;overflow-x:auto;margin:10px 0 16px}
pre code{background:none;padding:0;font-size:12.3px;line-height:1.65}
blockquote{border-left:4px solid var(--navy2);background:var(--blue-l);
  padding:12px 16px;border-radius:0 8px 8px 0;margin:12px 0;color:var(--ink2)}
blockquote p:last-child{margin-bottom:0}
.lead{color:var(--ink2);font-size:13.8px;margin:6px 0 14px}

/* ── 表格 ── */
table{width:100%;border-collapse:collapse;font-size:12.6px;background:var(--card);
  border-radius:8px;overflow:hidden;margin:12px 0 16px}
th{background:var(--navy);color:#fff;padding:8px 10px;text-align:left;font-weight:600;
  font-size:12px;vertical-align:bottom}
td{padding:7px 10px;border-bottom:1px solid var(--line2);vertical-align:top;line-height:1.62}
tbody tr:nth-child(even) td{background:#fafbfd}
tbody tr:hover td{background:var(--blue-l)}
td.num{font-variant-numeric:tabular-nums}

/* ── 信息卡 / 注释 ── */
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:18px 20px;margin:14px 0;box-shadow:var(--shadow)}
.card h3:first-child{margin-top:0}
.note{background:var(--amber-l);border-left:4px solid var(--amber);padding:10px 14px;
  border-radius:0 7px 7px 0;font-size:12.9px;margin:12px 0}
.note.gap{background:var(--gray-l);border-left-color:var(--gray)}
.note.check{background:var(--green-l);border-left-color:var(--green)}
.note.correct{background:var(--red-l);border-left-color:var(--red)}
.note.preline{background:var(--pre-l);border-left-color:var(--pre)}

/* ── 差异高亮（跨月对比） ── */
.diff-badge{display:inline-block;font-size:10.5px;font-weight:700;line-height:1;
  border-radius:3px;padding:2px 6px;margin-right:6px;vertical-align:middle;white-space:nowrap}
.diff-block{border-radius:6px;padding:4px 8px;margin:4px -8px}
.diff-new{background:var(--green-l);box-shadow:inset 3px 0 0 var(--green)}
.diff-new .diff-badge{background:var(--green);color:#fff}
.diff-mod{background:var(--amber-l);box-shadow:inset 3px 0 0 var(--amber)}
.diff-mod .diff-badge{background:var(--amber);color:#fff}
.diff-del-group{margin:6px 0;border:1px dashed var(--line);border-radius:6px;background:#fbfcfe}
.diff-del-group>summary{cursor:pointer;font-size:12px;color:var(--ink3);
  padding:6px 10px;user-select:none;list-style:none}
.diff-del-group>summary::-webkit-details-marker{display:none}
.diff-del-group>summary::before{content:"▸ ";color:var(--gray)}
.diff-del-group[open]>summary::before{content:"▾ "}
.diff-del-group .diff-del-body{padding:2px 8px 8px;color:var(--ink3)}
.diff-del-group .diff-del-body s,.diff-del-group .diff-del-body del{color:var(--red)}
.diff-del-group .diff-badge{background:var(--gray-l);color:var(--gray)}
/* 隐藏更新标记：对照阅读模式 */
main.hide-diff .diff-badge{display:none}
main.hide-diff .diff-block{background:none;box-shadow:none;padding:0;margin:0}
main.hide-diff .diff-del-group{display:none}

/* ── 页脚 ── */
.footer{font-size:11.4px;color:var(--ink3);text-align:center;margin-top:22px;line-height:1.9}
.footer .backlinks{margin-top:8px}
.footer .backlinks a{margin:0 8px}

/* ── 响应式 ── */
@media(max-width:760px){
  .hero{padding:30px 20px;border-radius:0 0 14px 14px}
  .hero h1{font-size:21px}
  .wrap{padding:0 14px 46px}
  td,th{padding:6px 7px;font-size:11.7px}
  h2.sec{font-size:17.5px}
}
"""

DIFF_JS = """
(function () {
  'use strict';
  var main = document.getElementById('main-content');
  var tgDiff = document.getElementById('tg-diff');
  var tgDel = document.getElementById('tg-del');
  if (main && tgDiff) {
    tgDiff.addEventListener('click', function () {
      var hide = main.classList.toggle('hide-diff');
      tgDiff.textContent = hide ? '显示更新标记' : '隐藏更新标记';
    });
  }
  if (tgDel) {
    tgDel.addEventListener('click', function () {
      var open = tgDel.getAttribute('data-open') === '1';
      var groups = document.querySelectorAll('details.diff-del-group');
      for (var i = 0; i < groups.length; i++) groups[i].open = !open;
      tgDel.setAttribute('data-open', open ? '0' : '1');
      tgDel.textContent = open ? '展开全部删除' : '收起全部删除';
    });
  }
})();
"""


# ──────────────────────────────────────────────
# 基础工具（表格 / 标题 / 锚点）
# ──────────────────────────────────────────────

H2_RE = re.compile(r"<h2\b[^>]*>.*?</h2>", re.DOTALL)
HEAD_RE = re.compile(r"<h([1-6])\b[^>]*>.*?</h\1>", re.DOTALL)
TABLE_RE = re.compile(r"<table\b.*?</table>", re.DOTALL)
TH_RE = re.compile(r"<th\b[^>]*>")
NAV_RE = re.compile(r'<nav aria-label="报告导航">.*?</nav>', re.DOTALL)
HR_RE = re.compile(r"<hr\s*/?>")
# GitHub 风格 slug 的剔除字符：保留 \w（含中日韩文字、字母数字、下划线）、连字符与空格
SLUG_STRIP_RE = re.compile(r"[^\w\- ]", re.UNICODE)
MD_NAME_RE = re.compile(r"^(\d{4})-(\d{2})-(.+)\.md$")

def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def _slug(heading_html: str) -> str:
    """标题 HTML -> GitHub 风格 slug（保留 CJK：小写、去标点、空格转连字符）。"""
    s = _strip_tags(heading_html).strip()
    s = SLUG_STRIP_RE.sub("", s).replace(" ", "-").lower()
    return s


def _with_width(th: str, width: int) -> str:
    """给单个 <th> 补百分比列宽（已含 width: 时跳过，避免重复声明）。"""
    if "width:" in th:
        return th
    if "style=" in th:
        return re.sub(r'style="([^"]*)"', lambda m: f'style="{m.group(1)}; width:{width}%"', th, count=1)
    return th.replace("<th", f'<th style="width:{width}%"', 1)


def _with_scope(th: str, scope: str) -> str:
    """给单个 <th> 补 scope（已含 scope= 时跳过，保证幂等）。"""
    if "scope=" in th:
        return th
    return th.replace("<th", f'<th scope="{scope}"', 1)


def _caption_html(prefix: str, tbl: str, idx: int) -> str:
    """复杂表 <caption>：优先取表前最近标题（h1–h6）纯文本，缺则取表头首行文本。"""
    text = ""
    heads = [mm.group(0) for mm in HEAD_RE.finditer(prefix)]
    if heads:
        text = _strip_tags(heads[-1])
    if not text:
        thead = HTML_THEAD_RE.search(tbl)
        if thead:
            first = HTML_TR_RE.search(thead.group(0))
            if first:
                cells = re.findall(r"<th\b[^>]*>(.*?)</th>", first.group(0), re.DOTALL)
                vals = [t for t in (_strip_tags(c) for c in cells) if t]
                text = " / ".join(vals)
    label = f"表 {idx}"
    return f"<caption>{label}：{text}</caption>" if text else f"<caption>{label}</caption>"


def _fix_tables(html: str) -> str:
    """表格加 class="fixed"；表头补 scope="col" 与百分比列宽；复杂表补 <caption>。

    复杂 / 多层表判定（表头行数 >1、列结构分层、首列为行标题）见
    `_common.is_complex_html_table`，与 lint_reports 共用同一口径。
    """
    idx = 0

    def fix(m: re.Match) -> str:
        nonlocal idx
        idx += 1
        tbl = m.group(0)
        if 'class="fixed"' not in tbl:
            tbl = tbl.replace("<table", '<table class="fixed"', 1)
        # 表头：逐列补百分比列宽 + scope="col"
        thead = HTML_THEAD_RE.search(tbl)
        if thead:
            head = thead.group(0)
            ths = TH_RE.findall(head)
            if ths:
                n = len(ths)
                base, rem = divmod(100, n)
                widths = [base] * n
                widths[-1] += rem
                it = iter(widths)
                new_head = TH_RE.sub(
                    lambda mm: _with_scope(_with_width(mm.group(0), next(it)), "col"), head
                )
                tbl = tbl.replace(head, new_head, 1)
        # 行标题：tbody 行首 <th> 补 scope="row"
        tbody = HTML_TBODY_RE.search(tbl)
        if tbody:
            body = tbody.group(0)

            def fix_row(rm: re.Match) -> str:
                row = rm.group(0)
                if not re.search(r"<tr\b[^>]*>\s*<th\b", row):
                    return row
                return re.sub(r"<th\b[^>]*>", lambda mm: _with_scope(mm.group(0), "row"), row, count=1)

            tbl = tbl.replace(body, HTML_TR_RE.sub(fix_row, body), 1)
        # 复杂表：补 <caption>（幂等）
        if "<caption" not in tbl and is_complex_html_table(m.group(0)):
            open_m = re.match(r"<table\b[^>]*>", tbl)
            if open_m:
                cap = _caption_html(html[: m.start()], m.group(0), idx)
                tbl = tbl[: open_m.end()] + cap + tbl[open_m.end():]
        return tbl

    return TABLE_RE.sub(fix, html)


def _fix_headings(html: str) -> str:
    """h2 重编号 id="sN"，并在文首（h1 与副标题 h3 之后、首个 h2 之前）插入简化锚点导航。"""
    items: list[str] = []

    def repl(m: re.Match) -> str:
        i = len(items) + 1
        items.append(f'<a href="#s{i}">{_strip_tags(m.group(0))}</a>')
        return re.sub(r'\bid="[^"]*"', f'id="s{i}"', m.group(0), count=1)

    html = H2_RE.sub(repl, html)
    if not items:
        return html
    nav = '<nav aria-label="报告导航">\n' + "\n".join(items) + "\n</nav>\n"
    m = re.search(r"<h2\b", html)
    if m:
        return html[: m.start()] + nav + html[m.start():]
    m = re.search(r"<h1\b[^>]*>.*?</h1>", html, re.DOTALL)
    if m:
        return html[: m.end()] + "\n" + nav + html[m.end():]
    return nav + html


def _fix_heading_anchors(html: str) -> str:
    """为每个标题（h1–h6）注入 GitHub 风格中文 slug 附加锚点，保证跨主题 #中文锚点 链接可达。"""
    used: set[str] = set()

    def repl(m: re.Match) -> str:
        tag = m.group(0)
        slug = _slug(tag)
        if not slug:
            return tag
        base, n = slug, 1
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        anchor = f'<a id="{slug}" aria-hidden="true"></a>'
        return re.sub(r"(<h[1-6]\b[^>]*>)", lambda mm: mm.group(1) + anchor, tag, count=1)

    return HEAD_RE.sub(repl, html)


# ──────────────────────────────────────────────
# 报告页拆分与渲染
# ──────────────────────────────────────────────

def _parse_meta(blockquote_html: str) -> list[str]:
    """blockquote -> meta 行列表（label：value 切分，label 加粗；超长截断）。"""
    text = re.sub(r"<br\s*/?>", "　", blockquote_html)
    text = re.sub(r"<[^>]+>", "", text)
    parts = re.split(r"　+|\n+", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        m = re.match(r"(.+?)[：:]\s*(.+)", p, re.S)
        if m:
            label, value = m.group(1).strip(), m.group(2).strip()
            if len(value) > 120:
                value = value[:120] + "…"
            out.append(f"<b>{html_mod.escape(label)}</b>：{html_mod.escape(value)}")
        else:
            out.append(html_mod.escape(p))
    return out


def _split_body(body: str) -> tuple[str, str, str, list[str]]:
    """md2html 产物 body -> (h1 HTML, blockquote HTML, 版本卡内容, 章节 HTML 列表)。

    章节以 h2 为界切分；h1 / blockquote / md2html 锚点 nav / hr 均从正文剥离
    （h1 + blockquote 进 hero，nav 由 report-nav 取代，hr 由章节间距取代）。
    """
    body = NAV_RE.sub("", body)
    body = HR_RE.sub("", body)

    h1_m = re.search(r"<h1\b[^>]*>.*?</h1>", body, re.DOTALL)
    h1 = h1_m.group(0) if h1_m else ""
    body_no_h1 = body[h1_m.end():] if h1_m else body

    bq_m = re.search(r"<blockquote\b[^>]*>.*?</blockquote>", body_no_h1, re.DOTALL)
    blockquote = bq_m.group(0) if bq_m else ""
    rest = body_no_h1[bq_m.end():] if bq_m else body_no_h1

    h2_iter = list(re.finditer(r"<h2\b[^>]*>.*?</h2>", rest, re.DOTALL))
    if not h2_iter:
        return h1, blockquote, rest.strip(), []

    preamble = rest[: h2_iter[0].start()].strip()
    sections = []
    for i, m in enumerate(h2_iter):
        start = m.start()
        end = h2_iter[i + 1].start() if i + 1 < len(h2_iter) else len(rest)
        chunk = rest[start:end].strip()
        # h2 重写为 <h2 class="sec" id="sN">（替换 md2html 生成的 id）
        tag_m = re.match(r"<h2\b[^>]*>", chunk)
        if tag_m:
            tag = tag_m.group(0)
            tag = re.sub(r'\bid="[^"]*"', f'id="s{i + 1}"', tag)
            tag = re.sub(r'\bclass="[^"]*"', "", tag)
            tag = tag[:-1].rstrip() + ' class="sec">'
            chunk = tag + chunk[tag_m.end():]
        chunk = re.sub(r'<a id="[^"]*" aria-hidden="true"></a>', "", chunk)
        sections.append(chunk)
    return h1, blockquote, preamble, sections


# 已审计标识块（md 文首 `> **已审计** ...`）。markdown 会把相邻 `>` 行合并为
# 同一 blockquote，故按「p 元素」提取，而非要求独立 blockquote。
AUDIT_BQ_RE = re.compile(r"<p><strong>已审计</strong>(.*?)</p>", re.DOTALL)


def _extract_audit_badge(body: str) -> tuple[str, str]:
    """从 body 提取「已审计」标识块 -> (去除标识后的 body, 标识纯文本)。

    标识由 audit_badge.py 注入，属审计状态而非研究内容；提取后由 hero 区
    绿色徽章渲染，不进入正文章节。
    """
    m = AUDIT_BQ_RE.search(body)
    if not m:
        return body, ""
    inner = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    inner = inner.lstrip("✅").strip()
    return body[: m.start()] + body[m.end():], inner


def _topic_meta(business_dir: Path) -> tuple[str, str]:
    """业务目录 -> (主题显示名, 类型名)。

    主题名取 business-config 首个一级标题（截去「· 业务专属配置」后缀）；
    类型取 business-config 的类型模板引用，映射 template-registry 类型名。
    """
    cfg = business_dir / "prompts" / "business-config.md"
    name, type_id = "", ""
    try:
        text = cfg.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    if text:
        m = re.search(r"^# (.+)$", text, re.M)
        if m:
            name = re.sub(r"\s*[·|].*$", "", m.group(1).strip()).strip()
        tm = TYPE_RE.search(text)
        if tm:
            type_id = tm.group(1)
    if not name:
        name = business_dir.name
    return name, TYPE_LABEL_FALLBACK.get(type_id, type_id)


def _prev_md(md_path: Path) -> Path | None:
    """同主题、最近一个更早自然月的报告 md；不存在返回 None。"""
    m = MD_NAME_RE.match(md_path.name)
    if not m:
        return None
    slug = m.group(3)
    cur_period = f"{m.group(1)}-{m.group(2)}"
    best: tuple[str, Path] | None = None
    for f in md_path.parent.glob("*.md"):
        mm = MD_NAME_RE.match(f.name)
        if not mm or mm.group(3) != slug:
            continue
        p = f"{mm.group(1)}-{mm.group(2)}"
        if p < cur_period and (best is None or p > best[0]):
            best = (p, f)
    return best[1] if best else None


def _back_url(md_path: Path, topic_slug: str) -> str:
    """报告页 -> 首页主题详情的相对链接（../../index.html#topic-<dir>）。"""
    rel = md_path.relative_to(ROOT)
    depth = len(rel.parts) - 1
    return f"{'../' * depth}index.html#topic-{topic_slug}"


def render_page(
    *, title: str, topic_name: str, type_label: str, period: str,
    rel_path: str, blockquote: str, sections: list[str], back_url: str,
    diff: tuple[str, dict, str] | None = None, audit: str = "",
    cycle_label: str = "",
) -> str:
    """渲染独立报告页。

    diff = (diffed_sections, stats, prev_period)；为 None 时无对比工具条。
    """
    esc = html_mod.escape
    meta_lines = _parse_meta(blockquote)
    meta_html = "".join(f'<div class="meta-item">{ln}</div>' for ln in meta_lines)
    tags = f'<span class="tag">{esc(period)}</span>'
    if type_label:
        tags += f'<span class="tag">{esc(type_label)}</span>'

    def _sec_title(s: str) -> str:
        """章节块 -> h2 标题纯文本（供 report-nav tabs 使用）。"""
        m = re.search(r"<h2\b[^>]*>(.*?)</h2>", s, re.DOTALL)
        raw = m.group(1) if m else s
        return _strip_tags(re.sub(r'<a id="[^"]*" aria-hidden="true"></a>', "", raw))

    tabs = "".join(
        f'<a href="#s{i}">{esc(_sec_title(s))}</a>'
        for i, s in enumerate(sections, 1)
    )

    # SEO 元数据：description 取主题 + 类型 + 期间 + 前四个章节标题；
    # keywords 取主题 / 类型 / 期间 / 常驻检索词 + 章节标题（去重、限量）。
    subject = "｜".join(x for x in (topic_name, type_label) if x)
    titles = [_sec_title(s) for s in sections]
    desc = f"{subject} {period} 报告：" + "、".join(titles[:4])
    desc = desc[:160]
    kw_seen: set[str] = set()
    kws: list[str] = []
    for k in [topic_name, type_label, period, "日本", "在留", "特定技能"] + titles:
        k = (k or "").strip()
        if k and k not in kw_seen:
            kw_seen.add(k)
            kws.append(k)
    meta_desc = esc(desc, quote=True)
    meta_kw = esc(",".join(kws[:12]), quote=True)

    audit_html = (
        f'<div class="audit-badge" role="status" aria-label="已审计报告">'
        f'<span class="audit-seal">✓ 已审计</span>'
        f'<span class="audit-meta">{esc(audit)}</span></div>'
        if audit else ""
    )

    diff_bar = ""
    body_sections = "\n".join(sections)
    if diff is not None:
        body_sections, stats, prev_period = diff
        summary = diff_summary(stats, period, prev_period)
        diff_bar = (
            '<div class="diff-bar">'
            f'<span class="diff-summary">{esc(summary)}</span>'
            '<button class="diff-toggle" id="tg-diff">隐藏更新标记</button>'
            '<button class="diff-toggle" id="tg-del">展开全部删除</button>'
            '</div>'
        )
        diff_content = (f"prev={prev_period or 'none'};new={stats['new']};"
                        f"mod={stats['mod']};del={stats['del']}")
    else:
        diff_content = "prev=none;new=0;mod=0;del=0"

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{meta_desc}">
<meta name="keywords" content="{meta_kw}">
<meta name="report-period" content="{esc(period)}">
<meta name="report-cycle" content="{esc(cycle_label)}">
<meta name="report-diff" content="{esc(diff_content)}">
<title>{esc(title)}</title>
<style>{REPORT_CSS}</style>
</head>
<body>
<a class="skip-link" href="#main-content">跳转到主要内容</a>
<header class="hero" role="banner" aria-label="报告题头">
  <div class="hero-band">
    <div class="wrap">
      <div class="hero-top">
        <div class="eyebrow">{esc(topic_name)} · {esc(type_label)}</div>
        <div class="tags">{tags}</div>
      </div>
      <h1>{esc(title)}</h1>
    </div>
  </div>
  <div class="wrap">
    <div class="hero-panel">
      <div class="meta-grid">{meta_html}</div>
      {audit_html}
    </div>
  </div>
</header>
<nav class="report-nav" aria-label="报告导航">
  <div class="wrap">
    <div class="nav-url">
      <span class="nav-url-label">报告路径</span>
      <a href="{esc(Path(rel_path).name)}">{esc(rel_path)}</a>
    </div>
    <div class="nav-tabs">{tabs}</div>
    {diff_bar}
  </div>
</nav>
<main class="wrap" id="main-content" role="main" aria-label="报告正文">
{body_sections}
</main>
<footer class="footer" role="contentinfo" aria-label="页脚">
  <p>{esc(topic_name)} · {esc(title)}｜{esc(period)}<br>
  报告路径：{esc(rel_path)}</p>
  <p class="backlinks">
    <a href="{esc(back_url)}">← 返回主题</a>
    <a href="{esc(back_url.split("#")[0])}">返回首页</a>
  </p>
</footer>
<script>{DIFF_JS}</script>
</body>
</html>
'''


def convert(md_path: Path) -> str:
    """md 文本 -> 独立报告页 HTML（含构建期跨月对比高亮）。"""
    try:
        import markdown
    except ImportError:
        print("[ERROR] 缺少 markdown 依赖，请先执行 pip install -r requirements.txt")
        raise SystemExit(1) from None
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "toc"])
    title = md_path.stem
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    body = _fix_tables(body)
    body = _fix_headings(body)
    body = _fix_heading_anchors(body)
    body, audit_text = _extract_audit_badge(body)

    h1, blockquote, _preamble, sections = _split_body(body)
    if h1 and not title:
        title = _strip_tags(re.sub(r'<a id="[^"]*" aria-hidden="true"></a>', "", h1))

    m = MD_NAME_RE.match(md_path.name)
    period = f"{m.group(1)}-{m.group(2)}" if m else ""
    business_dir = md_path.parents[1]
    topic_name, type_label = _topic_meta(business_dir)
    # 报告路径须用 POSIX 分隔符：HTML 交付物与 CI（ubuntu）/ 本地（Windows）
    # 必须逐字节一致，否则同一份 md 在不同平台渲染出不同产物（非确定性）。
    rel_path = md_path.relative_to(ROOT).with_suffix(".html").as_posix()
    back_url = _back_url(md_path, business_dir.name)

    # 构建期跨月对比：与上一期（同主题、最近一个更早自然月）比对章节内容
    diff = None
    prev = _prev_md(md_path)
    if prev is not None:
        prev_text = prev.read_text(encoding="utf-8")
        prev_body = markdown.markdown(prev_text, extensions=["tables", "fenced_code", "toc"])
        prev_body = _fix_tables(prev_body)
        _p_h1, _p_bq, _p_pre, prev_sections = _split_body(prev_body)
        diffed, stats = render_diffed_body("\n".join(sections), "\n".join(prev_sections))
        pm = MD_NAME_RE.match(prev.name)
        prev_period = f"{pm.group(1)}-{pm.group(2)}" if pm else ""
        diff = (diffed, stats, prev_period)

    cycle_label = cycle_profile_path(business_dir, business_dir.name)["label"]
    return render_page(
        title=title, topic_name=topic_name, type_label=type_label, period=period,
        rel_path=rel_path, blockquote=blockquote, sections=sections,
        back_url=back_url, diff=diff, audit=audit_text, cycle_label=cycle_label,
    )


def collect_md_reports():
    out = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if reports.is_dir():
            out.extend(sorted(reports.glob("*.md")))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="md -> HTML 同步")
    ap.add_argument("--changed", action="store_true", help="仅转换 git diff 变更的报告（增量）")
    ap.add_argument("--base", default="main...HEAD", help="增量模式的 git diff 基点")
    args = ap.parse_args()
    targets = collect_md_reports()
    if args.changed:
        from incremental_build import changed_reports
        changed = set(changed_reports(args.base))
        targets = [m for m in targets if m.relative_to(ROOT).as_posix() in changed]
        if not targets:
            print("md2html --changed：无变更报告，跳过")
            return 0
    if not targets:
        print("md2html：无 md 报告源（纯图表型简报只出 HTML），跳过")
        return 0
    ok = 0
    for md in targets:
        try:
            html = convert(md)
            out = md.with_suffix(".html")
            # newline="\n"：Windows 下默认 newline=None 会写 CRLF，使重新生成的报告 HTML
            # 在仓库里变成假 dirty（与 generate_registry / sync_vocab 同一根因）。
            out.write_text(html, encoding="utf-8", newline="\n")
            print(f"[OK] {md} -> {out.name}")
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] 转换失败 {md}: {e}")
            return 1
    print(f"md2html 完成：转换 {ok} 份")
    return 0


if __name__ == "__main__":
    sys.exit(main())
