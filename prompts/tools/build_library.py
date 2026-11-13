# -*- coding: utf-8 -*-
"""从主题主文档生成集中展示页与汇总阅读页。"""

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

import markdown
import md2html
import update_scheduler

ROOT = Path(__file__).resolve().parents[2]


class BuildError(RuntimeError):
    """主题聚合页面构建失败。"""


def require_display_metadata(topic):
    for key in ("id", "name", "kind", "target", "category", "description"):
        if not topic.get(key):
            raise BuildError(f"[{topic.get('id', '未知主题')}] 缺少展示字段: {key}")


def load_topics():
    config = update_scheduler.load_config()
    errors = update_scheduler.validate_config(config)
    if errors:
        raise BuildError("主题配置错误：\n" + "\n".join(errors))
    topics = config["topics"]
    for topic in topics:
        require_display_metadata(topic)
    return topics


def topic_anchor(topic_id):
    return f"topic-{topic_id}"


def heading_anchor(topic_id, original_id):
    return f"{topic_anchor(topic_id)}--{original_id}"


def resolve_topic_source(config):
    require_display_metadata(config)
    source = update_scheduler.latest_report(config) if config["kind"] == "monitor" else ROOT / config["target"]
    if source is None or not source.is_file() or not source.read_text(encoding="utf-8").strip():
        raise BuildError(f"[{config['id']}] 主文档不存在或为空: {source}")
    html_path = source.with_suffix(".html")
    if not html_path.is_file():
        raise BuildError(f"[{config['id']}] 独立 HTML 不存在: {html_path}")
    return source, html_path


def rewrite_href(href, topic_id, source_dir, html_to_topic):
    if href.startswith("#"):
        return "#" + heading_anchor(topic_id, unquote(href[1:]))
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith("/") or not parsed.path:
        return href
    target = (source_dir / unquote(parsed.path)).resolve()
    if target in html_to_topic:
        target_id = html_to_topic[target]
        if parsed.fragment:
            return "#" + heading_anchor(target_id, unquote(parsed.fragment))
        return "#" + topic_anchor(target_id)
    try:
        relative = target.relative_to(ROOT)
    except ValueError:
        return href
    path = quote(relative.as_posix(), safe="/")
    if parsed.path.endswith("/"):
        path += "/"
    return urlunsplit(("", "", path, parsed.query, parsed.fragment))


def _add_col_scope(match):
    """给表头 <th> 补 scope="col"（BBC GEL 表格语义）。"""
    attrs = match.group(1) or ""
    if "scope=" in attrs:
        return match.group(0)
    return f'<th{attrs} scope="col">'


def _wrap_table(match, topic_id, topic_name, counter):
    """表格包裹：容器 role=group + aria-labelledby + tabindex + caption（BBC GEL）。"""
    table = match.group(0)
    caption_id = f"table-caption-{topic_id}-{counter}"
    label = f"{topic_name} · 数据表 {counter}" if topic_name else f"数据表 {counter}"
    table = re.sub(
        r"<table[^>]*>",
        lambda m: f'{m.group(0)}<caption id="{caption_id}">{html.escape(label)}</caption>',
        table,
        count=1,
    )
    table = re.sub(r"<th(\s[^>]*)?>", _add_col_scope, table)
    return (
        f'<div class="table-wrap" role="group" aria-labelledby="{caption_id}" tabindex="0">'
        f"{table}</div>"
    )


def namespace_html(body, topic_id, source_dir, html_to_topic, topic_name=""):
    body = re.sub(
        r'<h([1-6]) id="([^"]+)">',
        lambda match: f'<h{match.group(1)} id="{heading_anchor(topic_id, match.group(2))}">',
        body,
    )

    def replace_href(match):
        original = html.unescape(match.group(2))
        rewritten = rewrite_href(original, topic_id, source_dir, html_to_topic)
        return f'{match.group(1)}{html.escape(rewritten, quote=True)}{match.group(3)}'

    body = re.sub(r'(<a\b[^>]*?\bhref=")([^"]*)(")', replace_href, body)

    counter = 0

    def wrap(match):
        nonlocal counter
        counter += 1
        return _wrap_table(match, topic_id, topic_name, counter)

    return re.sub(r"<table>.*?</table>", wrap, body, flags=re.DOTALL)


def extract_chapters(body, topic_id):
    chapters = []
    prefix = heading_anchor(topic_id, "")
    for match in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', body, flags=re.DOTALL):
        anchor, raw_title = match.groups()
        title = html.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()
        if not anchor.startswith(prefix) or title == "导航与使用约定" or title.endswith("索引"):
            continue
        chapters.append({"title": title, "id": anchor, "level": 2})
    return chapters


# ─────────────────────────────────────────────────────────────
# 更新标记（已更新 标注 / 高亮）
#
# 约定写法（写在源文档 markdown 中，单独成行）：
#   <!-- updated: 2026-11-12 -->
#   <!-- updated: 2026-11-12 | 本次更新摘要 -->
#
# 两种生效方式：
#   章节级：标记紧跟在章节标题（## NN …）之后 → 标题加「已更新」徽标，整节内容高亮；
#   块级：  标记位于段落 / 表格 / 列表 / 引用 / 代码块之前 → 该块加徽标并高亮。
# 未标记的内容在构建后保持逐字节不变。
# ─────────────────────────────────────────────────────────────

UPDATE_MARKER_RE = re.compile(
    r"<!--\s*updated:\s*(?P<date>\d{4}-\d{2}-\d{2})(?:\s*\|\s*(?P<note>[^>]*?))?\s*-->"
)

_VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class _TopLevelBlockSplitter(HTMLParser):
    """把 HTML 拆成顶层块序列，保留原始文本以便无损重组。"""

    def __init__(self, html_text):
        super().__init__(convert_charrefs=False)
        self._html = html_text
        self._line_starts = [0]
        for match in re.finditer("\n", html_text):
            self._line_starts.append(match.end())
        self.blocks = []
        self._depth = 0
        self._start = None
        self.feed(html_text)
        self.close()

    def _offset(self):
        line, column = self.getpos()
        return self._line_starts[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if tag in _VOID_ELEMENTS:
            if self._depth == 0:
                start = self._offset()
                self.blocks.append(self._html[start:start + len(self.get_starttag_text())])
            return
        if self._depth == 0:
            self._start = self._offset()
        self._depth += 1

    def handle_startendtag(self, tag, attrs):
        if self._depth == 0:
            start = self._offset()
            self.blocks.append(self._html[start:start + len(self.get_starttag_text())])

    def handle_endtag(self, tag):
        if self._depth == 0:
            start = self._offset()
            self.blocks.append(self._html[start:start + len(tag) + 3])
            return
        self._depth -= 1
        if self._depth == 0 and self._start is not None:
            end = self._offset() + len(tag) + 3
            self.blocks.append(self._html[self._start:end])
            self._start = None

    def handle_data(self, data):
        if self._depth == 0:
            start = self._offset()
            self.blocks.append(self._html[start:start + len(data)])

    def handle_comment(self, data):
        if self._depth == 0:
            start = self._offset()
            self.blocks.append(self._html[start:start + len(data) + 7])

    def handle_entityref(self, name):
        if self._depth == 0:
            start = self._offset()
            self.blocks.append(self._html[start:start + len(name) + 2])

    def handle_charref(self, name):
        if self._depth == 0:
            start = self._offset()
            self.blocks.append(self._html[start:start + len(name) + 3])


def _is_heading(block):
    match = re.match(r"<h([1-6])\b", block.strip())
    return int(match.group(1)) if match else None


def _badge_html(date, note):
    title = f"已更新 {date}" + (f"：{note}" if note else "")
    note_html = f'<span class="update-note">{html.escape(note)}</span>' if note else ""
    return (
        f'<span class="update-badge" title="{html.escape(title, quote=True)}">'
        f"已更新 {html.escape(date)}</span>{note_html}"
    )


def _inject_heading_badge(heading_html, date, note):
    badge = _badge_html(date, note)
    match = re.search(r"</h[1-6]>", heading_html)
    if not match:
        return heading_html + badge
    position = match.start()
    return f"{heading_html[:position]} {badge}{heading_html[position:]}"


def _process_blocks(blocks):
    result = []
    updates = []
    index = 0
    total = len(blocks)
    while index < total:
        block = blocks[index]
        stripped = block.strip()
        marker = UPDATE_MARKER_RE.fullmatch(stripped) if stripped else None
        if marker is None:
            result.append(block)
            index += 1
            continue

        date = marker.group("date")
        note = (marker.group("note") or "").strip()
        updates.append({"date": date, "note": note})

        previous = None
        for position in range(len(result) - 1, -1, -1):
            if result[position].strip():
                previous = position
                break

        next_index = index + 1
        while next_index < total and not blocks[next_index].strip():
            next_index += 1

        previous_level = _is_heading(result[previous]) if previous is not None else None
        next_level = _is_heading(blocks[next_index]) if next_index < total else None

        if previous_level:
            # 章节级：标记紧跟标题之后
            result[previous] = _inject_heading_badge(result[previous], date, note)
            end = index + 1
            while end < total:
                level = _is_heading(blocks[end])
                if level is not None and level <= previous_level:
                    break
                end += 1
            inner_html, inner_updates = _process_blocks(blocks[index + 1:end])
            updates.extend(inner_updates)
            if inner_html.strip():
                result.append(
                    f'<div class="update-section" data-updated="{html.escape(date, quote=True)}">'
                    f"{inner_html}</div>"
                )
            index = end
            continue

        if next_level:
            # 章节级：标记位于标题之前
            end = next_index + 1
            while end < total:
                level = _is_heading(blocks[end])
                if level is not None and level <= next_level:
                    break
                end += 1
            heading_html = _inject_heading_badge(blocks[next_index], date, note)
            inner_html, inner_updates = _process_blocks(blocks[next_index + 1:end])
            updates.extend(inner_updates)
            result.append(heading_html)
            if inner_html.strip():
                result.append(
                    f'<div class="update-section" data-updated="{html.escape(date, quote=True)}">'
                    f"{inner_html}</div>"
                )
            index = end
            continue

        # 块级：标记位于段落 / 表格 / 列表 / 引用 / 代码块之前
        if next_index < total:
            result.append(
                f'<div class="update-block" data-updated="{html.escape(date, quote=True)}">'
                f"{_badge_html(date, note)}{blocks[next_index]}</div>"
            )
            index = next_index + 1
        else:
            index += 1
    return "".join(result), updates


def apply_update_markers(body, topic_id=None):
    """把更新标记转换为可见徽标与高亮包装，返回 (html, 更新记录)。

    没有标记时原样返回，保证未更新内容逐字节不变。
    """
    if not UPDATE_MARKER_RE.search(body):
        return body, []
    blocks = _TopLevelBlockSplitter(body).blocks
    if "".join(blocks) != body:
        return body, []
    return _process_blocks(blocks)


def collect_updates(body):
    """统计源文档中的更新标记，供总览页与工具条展示。"""
    return [
        {"date": match.group("date"), "note": (match.group("note") or "").strip()}
        for match in UPDATE_MARKER_RE.finditer(body)
    ]


def topic_modified(topic):
    """主题最近更新日期：优先取更新标记最新日期，回退 git 最后提交日。"""
    updates = topic.get("updates") or []
    if updates:
        return max(update["date"] for update in updates)
    if not topic.get("target"):
        return "—"
    last, _ = update_scheduler.topic_last_update(topic)
    return last or "—"


# ─────────────────────────────────────────────────────────────
# 月度报告版本发现（总览页操作列月份标签）
# ─────────────────────────────────────────────────────────────

VERSIONED_STEM_RE = re.compile(r"_v(\d{4})\.(\d{2})\.(\d{2})(?:_(\d+))?$")
BASELINE_PERIOD_RE = re.compile(
    r"_baseline_(\d{4})(?:\.(\d{2})|Q([1-4])|H([1-2]))?$", re.IGNORECASE)
DATE_META_RE = re.compile(r"\*\*(?:整理日期|数据基准日)\*\*[：:]\s*(\d{4})-(\d{2})-(\d{2})")
VERSION_META_RE = re.compile(r"\*\*版本\*\*[：:]\s*v(\d{4})\.(\d{2})\.(\d{2})")
UPDATED_MARK_RE = re.compile(r"<!--\s*updated:\s*(\d{4})-(\d{2})-(\d{2})")


def _period_date(year, month, quarter, half):
    """历史基线周期 → 该周期首月首日（用于月份归位）。"""
    y = int(year)
    if month:
        return f"{y:04d}-{int(month):02d}-01"
    if quarter:
        return f"{y:04d}-{3 * int(quarter) - 2:02d}-01"
    if half:
        return f"{y:04d}-{6 * int(half) - 5:02d}-01"
    return f"{y:04d}-01-01"


def _content_dates(text, stem):
    """从报告正文/元数据收集候选日期（整理日期、版本行、更新标记、基线周期）。"""
    dates = []
    for pattern in (DATE_META_RE, VERSION_META_RE):
        match = pattern.search(text)
        if match:
            dates.append(f"{match.group(1)}-{match.group(2)}-{match.group(3)}")
    dates.extend(f"{y}-{m}-{d}" for y, m, d in UPDATED_MARK_RE.findall(text))
    period = BASELINE_PERIOD_RE.search(stem)
    if period:
        dates.append(_period_date(*period.groups()))
    return dates


def _topic_reports_dir(topic):
    """定位主题的 reports/ 目录（监测类 target 为目录，知识类 target 为文件）。"""
    target = topic.get("target")
    if target:
        path = ROOT / target
        return path if path.is_dir() else path.parent
    html_path = topic.get("html")
    return html_path.parent if html_path else None


def collect_report_editions(topic):
    """收集主题的报告版本（当前 + 归档），返回 [{date, seq, version, html}]。

    日期优先级：文件名版本号 > 正文元数据（整理日期 / 数据基准日 / 版本行）>
    更新标记 > 基线周期。仅保留存在同名 HTML 的条目，避免生成死链。
    """
    reports_dir = _topic_reports_dir(topic)
    if reports_dir is None or not reports_dir.is_dir():
        return []
    directories = [reports_dir]
    archives = reports_dir / "archives"
    if archives.is_dir():
        directories.append(archives)

    editions = []
    seen = set()
    for directory in directories:
        for md in sorted(directory.glob("*.md")):
            if md.stem in seen:
                continue
            seen.add(md.stem)
            html = md.with_suffix(".html")
            if not html.is_file():
                continue
            version_match = VERSIONED_STEM_RE.search(md.stem)
            if version_match:
                year, month, day, seq = version_match.groups()
                editions.append({
                    "date": f"{year}-{month}-{day}",
                    "seq": int(seq or 0),
                    "version": f"v{year}.{month}.{day}" + (f"_{seq}" if seq else ""),
                    "html": html,
                })
                continue
            text = md.read_text(encoding="utf-8", errors="replace")
            dates = _content_dates(text, md.stem)
            if not dates:
                continue
            meta_match = VERSION_META_RE.search(text)
            version = (
                "v{}.{}.{}".format(*meta_match.groups())
                if meta_match else "baseline"
            )
            editions.append({
                "date": max(dates), "seq": 0, "version": version, "html": html,
            })
    return editions


def build_month_reports(topic):
    """按月份归位报告版本：每月取跨年份最新一份，返回 {month: edition}。"""
    by_month = {}
    for edition in collect_report_editions(topic):
        month = int(edition["date"][5:7])
        current = by_month.get(month)
        if current is None or (edition["date"], edition["seq"]) > (
            current["date"], current["seq"]
        ):
            by_month[month] = edition
    return by_month


CATEGORIES = ("监测动态", "职业就业", "行业技术", "经济环境", "制度政策", "学习成长", "生活地域")
CATEGORY_EN = {
    "监测动态": "MONITORING",
    "职业就业": "CAREER",
    "行业技术": "INDUSTRY & TECH",
    "经济环境": "ECONOMY",
    "制度政策": "POLICY",
    "学习成长": "LEARNING",
    "生活地域": "LIFE & REGION",
}

LIBRARY_CSS = """
:root {
  /* 颜色令牌 */
  --bg: #f4f6f9; --card: #ffffff; --ink: #15202b; --ink2: #465667; --ink3: #5f6e7d;
  --line: #e1e7ee; --line2: #eef2f6; --border-control: #76828f;
  --navy: #16324f; --navy2: #2f5597; --blue: #3f6fb0; --blue-l: #eaf1fa;
  --green: #1c7444; --green-l: #eaf5ef;
  --amber: #8a5f0e; --amber-l: #fdf4e2; --amber-line: #f0dcb0;
  --gray: #5f6b76; --gray-l: #eff2f4;
  /* 间距档位（4px 基准，USWDS 式有限档位） */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-7: 40px; --space-8: 56px;
  /* 圆角档位 */
  --radius-xs: 4px; --radius-sm: 6px; --radius-md: 10px; --radius-lg: 12px;
  --radius-pill: 999px;
  /* 行宽 / 容器宽度 */
  --measure-body: 860px; --measure-main: 1240px; --measure-layout: 1440px;
  --measure-sidebar: 266px; --measure-search: 240px; --measure-results: 340px;
  --measure-table: 480px; --measure-card-min: 320px; --measure-note-min: 200px;
  --measure-search-min: 180px; --measure-results-max: 360px;
  --measure-sidebar-max: 280px;
  --topbar-h: 56px; --shadow: 0 1px 3px rgba(20,40,70,.06);
}
html { scroll-behavior: smooth; scroll-padding-top: calc(var(--topbar-h) + 14px); }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
body.index-page, body.library-page, body.changelog-page {
  max-width: none; margin: 0; padding: 0; background: var(--bg); color: var(--ink);
  font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", Arial, sans-serif;
  line-height: 1.7; font-size: 14.5px;
}
[hidden] { display: none !important; }
/* 仅页面框架组件使用 border-box；.topic-body 内的源文档元素保持原始盒模型 */
.topbar, .hero, .filterbar, .main, .layout, .sidebar, .reader-main, .cards, .topic-card,
.report-block, .report-bar, .topic-local-toc, .topic-head, .searchbox, .footer, .totop,
.topic-table, .month-tags, .month-tag,
.topbar *, .hero *, .filterbar *, .sidebar *, .topic-card *, .report-block .report-bar *,
.topic-local-toc *, .searchbox *, .footer *, .topic-table *, .month-tags * { box-sizing: border-box; }

/* ── 顶栏 ── */
.topbar { position: sticky; top: 0; z-index: 50; background: rgba(22,50,79,.97); color: #fff;
  display: flex; align-items: center; gap: var(--space-4); padding: 0 var(--space-5); height: var(--topbar-h);
  box-shadow: 0 2px 10px rgba(15,35,56,.25); }
.topbar .brand { font-weight: 700; font-size: 15px; letter-spacing: .4px; white-space: nowrap; }
.topbar .brand a { color: #fff; }
.topbar .brand a:hover { text-decoration: none; }
.topbar .brand-sub { font-size: 12.5px; color: rgba(255,255,255,.72); letter-spacing: .6px; white-space: nowrap; }
.topbar nav { display: flex; gap: 4px; }
.topbar nav a { color: rgba(255,255,255,.82); font-size: 13px; padding: 5px 12px; border-radius: var(--radius-pill); }
.topbar nav a:hover { background: rgba(255,255,255,.14); color: #fff; text-decoration: none; }
.topbar nav a.active { background: rgba(255,255,255,.18); color: #fff; font-weight: 600; }
.topbar .spacer { flex: 1; }

/* ── 搜索框 ── */
.searchbox { position: relative; }
.searchbox > input { width: var(--measure-search); max-width: 42vw; padding: 6px 13px; border-radius: var(--radius-pill);
  border: 1px solid rgba(255,255,255,.6); background: rgba(255,255,255,.1); color: #fff;
  font-size: 13px; font-family: inherit; }
.searchbox > input::placeholder { color: rgba(255,255,255,.55); }
.searchbox > input:focus { background: rgba(255,255,255,.18); border-color: rgba(255,255,255,.85); }
.topbar :focus-visible { outline-color: #ffffff; }
.searchbox .results { position: absolute; top: calc(100% + 6px); right: 0; width: var(--measure-results); max-width: 86vw;
  background: #fff; border: 1px solid var(--line); border-radius: var(--radius-md);
  box-shadow: 0 10px 30px rgba(15,35,56,.2); max-height: var(--measure-results-max); overflow-y: auto;
  z-index: 60; display: none; color: var(--ink); }
.searchbox .results.show { display: block; }
.sr-item { display: block; padding: 9px 13px; border-bottom: 1px solid var(--line2); }
.sr-item:last-child { border-bottom: 0; }
.sr-item:hover { background: var(--blue-l); text-decoration: none; }
.sr-item .t { font-size: 13px; color: var(--navy); font-weight: 700; line-height: 1.4; }
.sr-item .path { font-size: 11px; color: var(--ink3); margin-top: 1px; }
.sr-item .s { font-size: 12px; color: var(--ink2); line-height: 1.55; margin-top: 3px;
  max-height: 3.2em; overflow: hidden; }
.sr-none { padding: 16px; text-align: center; color: var(--ink3); font-size: 12.5px; }

/* ── Hero（总览页） ── */
.hero { background: linear-gradient(128deg,#0f2338 0%,#16324f 52%,#2f5597 100%);
  color: #fff; padding: var(--space-7) var(--space-7) var(--space-7); }
.hero .eyebrow { font-size: 11.5px; letter-spacing: 2.4px; color: rgba(255,255,255,.72); }
.hero h1 { font-size: 27px; font-weight: 700; letter-spacing: .4px; margin: 8px 0; padding: 0; border: 0; }
.hero .sub { font-size: 13.5px; color: rgba(255,255,255,.8); max-width: var(--measure-body); margin: 0; }
.hero .stats { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
.hero .stat { background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.2);
  border-radius: var(--radius-md); padding: var(--space-2) var(--space-4); font-size: 12px; color: rgba(255,255,255,.85); }
.hero .stat b { font-size: 20px; display: block; color: #fff; letter-spacing: .5px; line-height: 1.3; }
.hero .legend { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 18px;
  font-size: 12px; color: rgba(255,255,255,.78); }
.hero .legend .legend-text { color: rgba(255,255,255,.72); }

/* ── 筛选栏（总览页） ── */
.filterbar { position: sticky; top: var(--topbar-h); z-index: 40;
  background: rgba(244,246,249,.95); backdrop-filter: blur(6px);
  border-bottom: 1px solid var(--line); padding: var(--space-3) var(--space-5);
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip { border: 1px solid var(--border-control); background: #fff; border-radius: var(--radius-pill); padding: var(--space-1) var(--space-3);
  font-size: 12.5px; color: var(--ink2); cursor: pointer; user-select: none; font-family: inherit; }
.chip:hover { border-color: var(--blue); }
.chip.on { background: var(--navy); border-color: var(--navy); color: #fff; }
.filterbar .count { font-size: 12px; color: var(--ink3); margin-left: auto; white-space: nowrap; }

/* ── 主题卡片（总览页） ── */
.main { max-width: var(--measure-main); margin: 0 auto; padding: var(--space-2) var(--space-5) 50px; }
.category-section { margin-bottom: 12px; scroll-margin-top: calc(var(--topbar-h) + 14px); }
.region-head { display: flex; align-items: baseline; gap: 10px; margin: 24px 0 2px; flex-wrap: wrap; }
.region-head h2 { font-size: 20px; color: var(--navy); margin: 0; padding: 0; border: 0; }
.region-head .en { font-size: 11px; color: var(--ink3); letter-spacing: 1.6px; text-transform: uppercase; }
.region-head .count { font-size: 11.5px; color: var(--ink3); }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(var(--measure-card-min), 1fr));
  gap: 14px; margin: 12px 0 6px; }
.topic-card { min-width: 0; background: var(--card); border: 1px solid var(--line); border-radius: var(--radius-lg);
  padding: var(--space-4) 18px; display: flex; flex-direction: column; gap: var(--space-2); box-shadow: var(--shadow);
  transition: border-color .15s, box-shadow .15s; scroll-margin-top: calc(var(--topbar-h) + 14px); }
.topic-card:hover { border-color: #c9d6e6; box-shadow: 0 4px 14px rgba(20,40,70,.09); }
.topic-card:target { border-color: var(--blue); box-shadow: 0 0 0 3px var(--blue); }
.topic-card .row1 { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.badge { font-size: 11px; border-radius: var(--radius-xs); padding: 1px 7px; background: var(--blue-l);
  color: var(--navy2); white-space: nowrap; font-weight: 600; }
.badge.std { background: var(--gray-l); color: var(--gray); }
.badge.warn { background: var(--amber-l); color: var(--amber); }
.badge.baseline { background: var(--green-l); color: var(--green); }
.badge.updated { background: var(--amber-l); color: var(--amber); }
.count { font-size: 11.5px; color: var(--ink3); white-space: nowrap; }
.topic-card h4 { font-size: 16.5px; color: var(--navy); letter-spacing: .2px; margin: 0; padding: 0; border: 0; line-height: 1.5; }
.topic-number { color: var(--blue); font-weight: 700; margin-right: 6px; }
.topic-card .desc { font-size: 12.8px; color: var(--ink2); line-height: 1.65; flex: 1; margin: 0; }
.status-row { display: flex; gap: 6px; flex-wrap: wrap; }
.status-badge { font-size: 11px; border-radius: var(--radius-xs); padding: 2px var(--space-2); font-weight: 600; white-space: nowrap; }
.sb-base { background: var(--green-l); color: var(--green); }
.sb-upd { background: var(--amber-l); color: var(--amber); }
.sb-none { background: var(--gray-l); color: var(--gray); font-weight: 500; }
.topic-update-flag { font-size: 11px; border-radius: var(--radius-xs); padding: 2px var(--space-2); font-weight: 600;
  white-space: nowrap; background: var(--amber-l); color: var(--amber); }
.topic-card .actions { display: flex; gap: 8px; margin-top: 2px; flex-wrap: wrap; }
.btn { display: inline-block; font-size: 12.5px; border-radius: var(--radius-sm); padding: 6px 13px;
  border: 1px solid var(--border-control); background: #fff; color: var(--navy2); cursor: pointer;
  font-family: inherit; line-height: 1.5; }
.btn:hover { text-decoration: none; border-color: var(--blue); }
.btn.primary { background: var(--navy); border-color: var(--navy); color: #fff; }
.btn.primary:hover { background: var(--navy2); border-color: var(--navy2); }
.topic-details { border-top: 1px dashed var(--line); padding-top: 8px; }
.topic-details summary, .topic-local-toc summary { cursor: pointer; color: var(--navy2); font-weight: 700; font-size: 12.5px; }
.topic-details .summary-text, .topic-local-toc .summary-text { font: inherit; }
.topic-details .details-text, .topic-local-toc .details-text { margin-top: 2px; }
.chapter-list { margin: 8px 0 0; padding-left: 0; list-style: none; }
.chapter-list li { margin: 0; }
.chapter-list a { display: block; padding: 5px 9px; border-radius: var(--radius-sm); font-size: 12.5px; line-height: 1.5; }
.chapter-list a:hover { background: var(--blue-l); text-decoration: none; }
.noresult { padding: 44px 20px; text-align: center; color: var(--ink3); font-size: 13.5px; }

/* ── 主题总览表（总览页） ── */
.topic-table { width: 100%; min-width: 760px; border-collapse: separate; border-spacing: 0;
  background: var(--card); border: 1px solid var(--line); border-radius: var(--radius-lg);
  overflow: hidden; box-shadow: var(--shadow); }
.topic-table th, .topic-table td { padding: 9px 14px; border-bottom: 1px solid var(--line2);
  text-align: left; vertical-align: middle; font-size: 13.5px; }
.topic-table thead th { background: var(--gray-l); color: var(--navy); font-size: 12.5px;
  letter-spacing: .4px; border-bottom: 1px solid var(--line); white-space: nowrap; }
.topic-table tbody tr:last-child td { border-bottom: 0; }
.topic-table tbody tr:hover { background: #f8fafd; }
.topic-row { scroll-margin-top: calc(var(--topbar-h) + 14px); }
.topic-row:target td { background: #fff8e6; }
.topic-row:target td:first-child { box-shadow: inset 3px 0 0 var(--blue); }
.col-num { width: 52px; color: var(--blue); font-weight: 700; white-space: nowrap; }
.col-topic { min-width: 230px; }
.topic-link { color: var(--navy); font-weight: 700; font-size: 14.5px; }
.topic-link:hover { text-decoration: underline; }
.topic-meta { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-top: 3px; }
.col-topic .topic-details { border-top: 1px dashed var(--line); padding-top: 6px; margin-top: 6px; }
.col-topic .chapter-list { margin-top: 4px; }
.col-topic .chapter-list a { padding: 3px 7px; font-size: 12px; }
.col-cat { width: 110px; white-space: nowrap; }
.col-ops { min-width: 500px; }
.month-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.month-tag { display: inline-block; min-width: 34px; text-align: center; padding: 2px 7px;
  border-radius: var(--radius-pill); font-size: 11.5px; line-height: 1.6;
  background: var(--navy); color: #fff; white-space: nowrap; }
.month-tag:hover { background: var(--navy2); text-decoration: none; }
.month-tag.off { background: var(--gray-l); color: var(--ink3); cursor: default; }

/* ── 更新记录页 ── */
.cl-group { margin: 18px 0; }
.cl-date { font-size: 16px; color: var(--navy); margin: 0 0 8px; padding: 0; border: 0; }
.cl-list { list-style: none; margin: 0; padding: 0; }
.cl-list li { display: flex; gap: var(--space-3); align-items: baseline; flex-wrap: wrap;
  background: var(--card); border: 1px solid var(--line); border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-4); margin-bottom: var(--space-2); }
.cl-topic { font-weight: 700; color: var(--navy); }
.cl-note { flex: 1; min-width: var(--measure-note-min); font-size: 13px; color: var(--ink2); }
.topic-modified { font-size: 11px; color: var(--ink3); white-space: nowrap; }

/* ── 阅读页布局 ── */
.layout { display: flex; max-width: var(--measure-layout); margin: 0 auto; align-items: flex-start; }
.sidebar { width: var(--measure-sidebar); flex: none; position: sticky; top: var(--topbar-h);
  height: calc(100vh - var(--topbar-h)); overflow-y: auto; padding: var(--space-4) 10px 50px;
  border-right: 1px solid var(--line); background: #fbfcfe; }
.sidebar::-webkit-scrollbar { width: 6px; }
.sidebar::-webkit-scrollbar-thumb { background: #d3dce6; border-radius: var(--radius-xs); }
.toc-region { font-size: 13px; font-weight: 700; color: var(--navy); margin: 14px 0 5px;
  letter-spacing: .4px; padding: 0 8px; }
.toc-topic { display: block; font-size: 13px; color: var(--ink2); padding: 5px 9px;
  border-radius: var(--radius-sm); margin: 2px 0; line-height: 1.4; }
.toc-topic:hover { background: var(--blue-l); text-decoration: none; }
.toc-topic.active { background: var(--blue-l); color: var(--navy); font-weight: 700; }
.reader-main { flex: 1; min-width: 0; padding: 18px 26px 60px; }
.topic-section { margin-bottom: 10px; scroll-margin-top: calc(var(--topbar-h) + 14px); }
.topic-head { border-left: 4px solid var(--navy2); padding: 2px 0 2px 12px; margin: 28px 0 12px; }
.topic-head .crumb { font-size: 11.5px; color: var(--ink3); letter-spacing: .4px; }
.topic-head h2 { font-size: 21px; color: var(--navy); margin: 2px 0; padding: 0; border: 0; }
.topic-head .meta { font-size: 12.3px; color: var(--ink2); }
.report-block { background: var(--card); border: 1px solid var(--line);
  border-radius: var(--radius-lg); margin: var(--space-4) 0; overflow: hidden; box-shadow: var(--shadow);
  scroll-margin-top: calc(var(--topbar-h) + 14px); }
.report-bar { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; padding: var(--space-3) var(--space-4);
  background: linear-gradient(125deg,#f5f9fd,#edf3fa); border-bottom: 1px solid var(--line); }
.report-bar .rt { font-size: 14px; font-weight: 700; color: var(--navy); flex: 1; min-width: var(--measure-note-min);
  line-height: 1.5; }
.report-bar .ra { font-size: 12px; display: flex; gap: 10px; align-items: center; white-space: nowrap; }
.topic-local-toc { padding: var(--space-3) var(--space-4); background: #f8fafc; border-bottom: 1px solid var(--line); }
.topic-local-toc .chapter-list { columns: 2; column-gap: 24px; }

/* ── 主题正文（保持源文档原始排版） ── */
.topic-body { min-width: 0; padding: 18px 22px 26px; font-size: 16px; line-height: 1.7; color: #222; }
.topic-body p, .topic-body li { overflow-wrap: anywhere; }
.topic-body h1:first-child { margin-top: 18px; }
.topic-body h1, .topic-body h2, .topic-body h3, .topic-body h4, .topic-body h5, .topic-body h6 { scroll-margin-top: calc(var(--topbar-h) + 14px); }
.topic-body h1:target, .topic-body h2:target, .topic-body h3:target, .topic-body h4:target, .topic-body h5:target, .topic-body h6:target { background: #fff3bf; outline: 3px solid #fff3bf; }
.table-wrap { max-width: 100%; overflow-x: auto; }
.table-wrap table { min-width: var(--measure-table); width: 100%; }
.table-wrap caption { caption-side: top; text-align: left; font-size: 12.5px;
  color: var(--ink3); padding: 0 0 6px; }
.topic-body img { height: auto; }

/* ── 更新标注（amber 家族） ── */
.update-badge { display: inline-block; margin: 0 0 0 6px; padding: 1px 8px;
  border: 1px solid var(--amber-line); border-radius: var(--radius-pill); background: var(--amber-l);
  color: var(--amber); font-size: 12px; font-weight: 600; line-height: 1.6;
  vertical-align: middle; white-space: nowrap; }
.update-note { margin-left: 4px; color: var(--amber); font-size: 12px; font-weight: 400; }
.update-block { position: relative; margin: 1.2em 0; padding: 14px 16px; background: #fffdf7;
  border: 1px solid var(--amber-line); border-left: 4px solid var(--amber); border-radius: var(--radius-sm); }
.update-block > .update-badge { position: absolute; top: -11px; left: 12px; margin: 0;
  box-shadow: 0 1px 2px rgba(120,90,10,.12); }
.update-section { margin: 1.4em 0; padding: 2px 0 2px 16px; border-left: 4px solid var(--amber);
  background: rgba(154,106,18,.05); }
.noscript-note { padding: 10px 14px; background: var(--amber-l); border: 1px solid var(--amber-line); }

/* ── 页脚 / 回到顶部 ── */
.footer { text-align: center; color: var(--ink3); font-size: 11.5px; padding: 26px 20px 36px;
  line-height: 1.9; border-top: 1px solid var(--line); }
.footer code { background: var(--gray-l); padding: 0.1em 0.3em; border-radius: var(--radius-xs); }
.totop { position: fixed; right: 22px; bottom: 22px; width: 40px; height: 40px; border-radius: 50%;
  background: var(--navy); color: #fff; border: 0; font-size: 17px; cursor: pointer;
  box-shadow: 0 4px 14px rgba(15,35,56,.3); opacity: 0; pointer-events: none;
  transition: opacity .2s; z-index: 70; font-family: inherit; }
.totop.show { opacity: 1; pointer-events: auto; }

/* ── 响应式 ── */
@media (max-width: 960px) {
  html { scroll-padding-top: 18px; }
  .topbar { position: static; height: auto; padding: 8px 14px; flex-wrap: wrap; row-gap: 8px; }
  .topbar .brand-sub { display: none; }
  .searchbox { flex: 1; min-width: var(--measure-search-min); }
  .searchbox > input { width: 100%; max-width: none; }
  .searchbox .results { left: 0; right: auto; width: min(var(--measure-results), 86vw); }
  .filterbar { position: static; padding: 10px 14px; }
  .hero { padding: 32px 22px 28px; }
  .hero h1 { font-size: 22px; }
  .main { padding: 6px 14px 40px; }
  .cards { grid-template-columns: 1fr; }
  .layout { flex-direction: column; align-items: stretch; }
  .sidebar { position: static; width: 100%; height: auto; max-height: var(--measure-sidebar-max);
    border-right: 0; border-bottom: 1px solid var(--line); }
  .reader-main { padding: 14px 14px 50px; }
  .topic-local-toc .chapter-list { columns: 1; }
  .report-bar .ra { width: 100%; }
  .totop { right: 14px; bottom: 14px; }
}
@media print {
  .topbar, .filterbar, .sidebar, .searchbox, .topic-card .actions, .topic-details,
  .report-bar, .topic-local-toc, .totop { display: none !important; }
  body.index-page, body.library-page, body.changelog-page { background: #fff; }
  .layout { display: block; }
  .report-block { border: 0; box-shadow: none; }
  .topic-section { break-before: page; }
}
"""

INDEX_JS = r"""
(() => {
  const input = document.getElementById('site-search');
  const resultBox = document.getElementById('search-results');
  const countEl = document.getElementById('hub-count');
  const totop = document.getElementById('totop');
  const rows = Array.from(document.querySelectorAll('.topic-row'));
  const noResult = document.createElement('div');
  noResult.className = 'noresult';
  noResult.textContent = '未找到匹配的主题，请调整关键词或筛选条件。';
  document.querySelector('.main').appendChild(noResult);

  const state = { q: '', category: 'all', status: 'all' };
  let timer;

  const termsOf = value => value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const matches = (text, terms) => terms.every(term => text.toLowerCase().includes(term));

  function renderResults(items) {
    resultBox.replaceChildren();
    if (!state.q) {
      resultBox.classList.remove('show');
      return;
    }
    resultBox.classList.add('show');
    if (!items.length) {
      const empty = document.createElement('div');
      empty.className = 'sr-none';
      empty.textContent = '未找到匹配的主题或章节。';
      resultBox.appendChild(empty);
      return;
    }
    items.slice(0, 30).forEach(item => {
      const link = document.createElement('a');
      link.className = 'sr-item';
      link.href = item.href;
      const title = document.createElement('div');
      title.className = 't';
      title.textContent = item.title;
      const meta = document.createElement('div');
      meta.className = 'path';
      meta.textContent = item.meta;
      link.append(title, meta);
      resultBox.appendChild(link);
    });
  }

  function applyFilters() {
    const terms = termsOf(state.q);
    const results = [];
    let visible = 0;
    rows.forEach(row => {
      const categoryOk = state.category === 'all' || row.dataset.category === state.category;
      const statusOk = state.status === 'all' || row.dataset.status === state.status;
      const textOk = !terms.length || matches(row.dataset.search, terms);
      const show = categoryOk && statusOk && textOk;
      row.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    if (terms.length) {
      TOPIC_INDEX.forEach(record => {
        const categoryOk = state.category === 'all' || record.category === state.category;
        const statusOk = state.status === 'all' || record.status === state.status;
        if (categoryOk && statusOk && matches(record.text, terms)) {
          results.push({ href: record.href, title: record.title, meta: record.meta });
        }
      });
    }
    noResult.style.display = visible ? 'none' : '';
    countEl.textContent = '共 ' + visible + ' 个主题';
    renderResults(results);
  }

  function bindChips(id, key) {
    const wrap = document.getElementById(id);
    wrap.addEventListener('click', event => {
      const btn = event.target.closest('.chip');
      if (!btn) return;
      wrap.querySelectorAll('.chip').forEach(chip => chip.classList.remove('on'));
      btn.classList.add('on');
      state[key] = btn.dataset[key];
      applyFilters();
    });
  }
  bindChips('chips-category', 'category');
  bindChips('chips-status', 'status');

  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      state.q = input.value.trim();
      applyFilters();
    }, 150);
  });
  resultBox.addEventListener('click', () => resultBox.classList.remove('show'));
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      event.preventDefault();
      input.focus();
    }
    if (event.key === 'Escape' && document.activeElement === input) {
      input.value = '';
      state.q = '';
      applyFilters();
    }
  });

  window.addEventListener('scroll', () => {
    totop.classList.toggle('show', window.scrollY > 600);
  }, { passive: true });
  totop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  applyFilters();
})();
"""

LIBRARY_JS = r"""
(() => {
  const input = document.getElementById('site-search');
  const resultBox = document.getElementById('search-results');
  const totop = document.getElementById('totop');
  const tocLinks = Array.from(document.querySelectorAll('.toc-topic'));
  const sections = Array.from(document.querySelectorAll('.topic-section'));
  const records = SEARCH_INDEX;
  let timer;

  const termsOf = value => value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const matches = (text, terms) => terms.every(term => text.toLowerCase().includes(term));

  function snippet(text, terms) {
    const lower = text.toLowerCase();
    const positions = terms.map(term => lower.indexOf(term)).filter(index => index >= 0);
    const start = Math.max(0, Math.min(...positions) - 42);
    return (start ? '…' : '') + text.slice(start, start + 150) + (start + 150 < text.length ? '…' : '');
  }

  function renderResults() {
    const query = input.value.trim();
    const terms = termsOf(query);
    resultBox.replaceChildren();
    if (!terms.length) {
      resultBox.classList.remove('show');
      return;
    }
    resultBox.classList.add('show');
    const found = records.filter(record => matches(record.text, terms)).slice(0, 30);
    if (!found.length) {
      const empty = document.createElement('div');
      empty.className = 'sr-none';
      empty.textContent = '未找到匹配内容，原正文仍可继续阅读。';
      resultBox.appendChild(empty);
      return;
    }
    found.forEach(record => {
      const link = document.createElement('a');
      link.className = 'sr-item';
      link.href = '#' + record.target;
      const title = document.createElement('div');
      title.className = 't';
      title.textContent = record.topic + ' · ' + record.title;
      const meta = document.createElement('div');
      meta.className = 's';
      meta.textContent = snippet(record.text, terms);
      link.append(title, meta);
      resultBox.appendChild(link);
    });
  }

  function highlightToc() {
    let current = sections[0];
    sections.forEach(section => {
      if (section.getBoundingClientRect().top <= 120) current = section;
    });
    tocLinks.forEach(link => {
      link.classList.toggle('active', !!current && link.getAttribute('href') === '#' + current.id);
    });
  }

  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(renderResults, 150);
  });
  resultBox.addEventListener('click', () => resultBox.classList.remove('show'));
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      event.preventDefault();
      input.focus();
    }
    if (event.key === 'Escape' && document.activeElement === input) {
      input.value = '';
      renderResults();
    }
  });

  window.addEventListener('scroll', () => {
    totop.classList.toggle('show', window.scrollY > 600);
    highlightToc();
  }, { passive: true });
  totop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  highlightToc();
})();
"""

CHANGELOG_JS = r"""
(() => {
  const totop = document.getElementById('totop');
  window.addEventListener('scroll', () => {
    totop.classList.toggle('show', window.scrollY > 600);
  }, { passive: true });
  totop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
})();
"""


def page_shell(title, body_class, content, script):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
{md2html.SHELL_CSS}
{md2html.BASE_CSS}
{LIBRARY_CSS}
</style>
</head>
<body class="{body_class}">
<a class="skip-link" href="#main-content">跳到主要内容</a>
{content}
{md2html.SKIP_LINK_JS}
<script>{script}</script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────
# 页面骨架层：共享组件（顶栏 / 搜索框 / Hero / 页脚 / 回顶）
# ─────────────────────────────────────────────────────────────

NAV_ITEMS = (
    ("index", "index.html", "主题总览"),
    ("library", "library.html", "汇总阅读"),
    ("changelog", "changelog.html", "更新记录"),
    ("updates", "updates.html", "周期更新看板"),
)


def render_searchbox(placeholder, label="搜索结果"):
    return (
        '<div class="searchbox">\n'
        f'    <input id="site-search" type="search" placeholder="{html.escape(placeholder, quote=True)}" autocomplete="off">\n'
        f'    <div class="results" id="search-results" role="region" aria-label="{html.escape(label)}" aria-live="polite"></div>\n'
        "  </div>"
    )


def render_topbar(active, brand_sub="", search_placeholder=None):
    brand_sub_html = (
        f'<div class="brand-sub">{html.escape(brand_sub)}</div>' if brand_sub else ""
    )
    nav_links = "".join(
        f'<a href="{url}"' + (' class="active"' if key == active else "") + f'>{label}</a>'
        for key, url, label in NAV_ITEMS
    )
    search_html = render_searchbox(search_placeholder) if search_placeholder else ""
    spacer = '<div class="spacer"></div>' if search_html else ""
    return (
        '<header class="topbar">\n'
        '  <div class="brand"><a href="index.html">日本生活与工作知识库</a></div>\n'
        f"  {brand_sub_html}\n"
        f'  <nav aria-label="主导航">{nav_links}</nav>\n'
        f"  {spacer}\n"
        f"  {search_html}\n"
        "</header>"
    )


def render_hero(eyebrow, title, sub, stats, legend="", noscript=""):
    stats_html = "".join(
        f'<div class="stat"><b>{value}</b>{label}</div>' for value, label in stats
    )
    legend_html = f'<div class="legend">{legend}</div>' if legend else ""
    noscript_html = f"<noscript>{noscript}</noscript>" if noscript else ""
    return (
        '<section class="hero">\n'
        f'  <div class="eyebrow">{html.escape(eyebrow)}</div>\n'
        f"  <h1>{html.escape(title)}</h1>\n"
        f'  <p class="sub">{html.escape(sub)}</p>\n'
        f'  <div class="stats">{stats_html}</div>\n'
        f"  {legend_html}\n"
        f"  {noscript_html}\n"
        "</section>"
    )


def render_footer(text):
    return f'<footer class="footer">{text}</footer>'


def render_totop():
    return '<button class="totop" id="totop" aria-label="回到顶部">↑</button>'


# ── 内容块层：总览页表格行与月份标签 ──

def render_month_tags(month_reports):
    """内容块：操作列的 12 个月份标签（有报告可点击，无报告置灰）。"""
    tags = []
    for month in range(1, 13):
        edition = month_reports.get(month)
        label = f"{month}月"
        if edition:
            url = quote(edition["html"].relative_to(ROOT).as_posix(), safe="/")
            title = html.escape(f"{edition['date']} · {edition['version']}", quote=True)
            tags.append(f'<a class="month-tag" href="{url}" title="{title}">{label}</a>')
        else:
            tags.append(
                f'<span class="month-tag off" title="该月暂无报告" aria-disabled="true">'
                f"{label}</span>"
            )
    return '<div class="month-tags">' + "".join(tags) + "</div>"


def render_topic_row(topic):
    """内容块：总览页主题行（编号 / 主题 / 分类 / 操作）。"""
    topic_id = topic["id"]
    anchor = topic_anchor(topic_id)
    name = topic["name"]
    updates = topic.get("updates") or []
    if updates:
        latest = max(update["date"] for update in updates)
        status = "updated"
        flag = (
            f'<span class="topic-update-flag" title="最近更新 {html.escape(latest)}">'
            f"已更新 {len(updates)} 处</span>"
        )
    else:
        status = "baseline"
        flag = '<span class="status-badge sb-none">暂无更新</span>'
    modified = topic.get("modified") or topic_modified(topic)
    modified_html = (
        f'<span class="topic-modified">最近更新 {html.escape(modified)}</span>'
        if modified != "—" else ""
    )
    chapter_items = "".join(
        f'<li><a class="chapter-link" data-search="{html.escape(topic["name"] + " " + chapter["title"], quote=True)}" href="library.html#{chapter["id"]}">{html.escape(chapter["title"])}</a></li>'
        for chapter in topic["chapters"]
    )
    details = (
        f'<details class="topic-details"><summary><span class="summary-text">'
        f"章节直达（{len(topic['chapters'])}）</span></summary>"
        f'<div class="details-text"><ul class="chapter-list">{chapter_items}</ul></div></details>'
    )
    search_text = " ".join(
        [name, topic["description"], topic["category"]]
        + [chapter["title"] for chapter in topic["chapters"]]
    )
    return f"""<tr class="topic-row" id="{anchor}" data-category="{html.escape(topic['category'], quote=True)}" data-status="{status}" data-search="{html.escape(search_text, quote=True)}">
  <td class="col-num">{html.escape(topic_id[:2])}</td>
  <td class="col-topic"><a class="topic-link" href="library.html#{anchor}">{html.escape(name)}</a><div class="topic-meta"><span class="status-badge sb-base">基准框架 · {html.escape(topic['version'])}</span>{flag}{modified_html}</div>{details}</td>
  <td class="col-cat"><span class="badge">{html.escape(topic['category'])}</span></td>
  <td class="col-ops">{render_month_tags(build_month_reports(topic))}</td>
</tr>"""


def render_topic_table(topics):
    """内容块：总览页主题表格（编号 / 主题 / 分类 / 操作）。"""
    rows = "".join(render_topic_row(topic) for topic in topics)
    return (
        '<div class="table-wrap" role="group" aria-labelledby="topic-table-caption" tabindex="0">\n'
        '<table class="topic-table">\n'
        f'<caption id="topic-table-caption">共 {len(topics)} 个主题 · '
        "操作列月份标签对应该主题当月发布的报告</caption>\n"
        "<thead><tr><th scope=\"col\">编号</th><th scope=\"col\">主题</th>"
        '<th scope="col">分类</th><th scope="col">操作</th></tr></thead>\n'
        f"<tbody>{rows}</tbody>\n"
        "</table>\n"
        "</div>"
    )


# ── 页面装配层：主题总览 ──

def render_index(topics):
    total_updates = sum(len(topic.get("updates") or []) for topic in topics)
    updated_topics = sum(1 for topic in topics if topic.get("updates"))
    category_chips = '<button class="chip on" data-category="all">全部</button>' + "".join(
        f'<button class="chip" data-category="{html.escape(category, quote=True)}">{html.escape(category)}</button>'
        for category in CATEGORIES
    )
    status_chips = (
        '<button class="chip on" data-status="all">全部状态</button>'
        '<button class="chip" data-status="updated">有更新</button>'
        '<button class="chip" data-status="baseline">仅基准框架</button>'
    )
    legend = (
        '<span class="status-badge sb-base">基准框架</span>'
        '<span class="legend-text">原始基准信息，完整保留</span>\n'
        '    <span class="status-badge sb-upd">已更新</span>'
        '<span class="legend-text">基准后的更新内容，突出标注</span>'
    )
    content = (
        render_topbar(
            "index",
            "JAPAN LIFE & WORK KNOWLEDGE BASE",
            "搜索主题 / 分类 / 章节…（按 / 聚焦）",
        )
        + "\n"
        + render_hero(
            "JAPAN LIFE & WORK KNOWLEDGE BASE",
            "主题总览",
            f"集中浏览 {len(topics)} 个当前主题：操作列的月份标签按年滚动，"
            "直达该主题当月发布的报告；也可进入连续汇总阅读。"
            "基准框架完整保留原始信息，更新内容以「已更新」标注突出展示，互不覆盖。",
            [
                (len(topics), "主题"),
                (len(CATEGORIES), "分类"),
                (updated_topics, "份文档有更新"),
                (total_updates, "处更新标注"),
            ],
            legend=legend,
            noscript='<p class="noscript-note">JavaScript 不可用，搜索与筛选已停用；'
            "全部主题行与月份报告链接仍可使用。</p>",
        )
        + "\n"
        + '<div class="filterbar">\n'
        + f'  <div class="chips" id="chips-category">{category_chips}</div>\n'
        + f'  <div class="chips" id="chips-status">{status_chips}</div>\n'
        + '  <span class="count" id="hub-count"></span>\n'
        + "</div>\n"
        + f'<main class="main" id="main-content">{render_topic_table(topics)}</main>\n'
        + render_footer(
            "由 <code>prompts/tools/build_library.py</code> 自动生成 · "
            "主题源文件见各主题 <code>reports/</code> 目录"
        )
        + "\n"
        + render_totop()
    )
    script = (
        "const TOPIC_INDEX = "
        + json.dumps(
            build_topic_search_index(topics),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + ";\n"
        + INDEX_JS
    )
    return page_shell("主题总览｜日本生活与工作知识库", "index-page", content, script)


# ── 导航配置层：侧栏主题导航 ──

def build_navigation(topics):
    """导航配置层：按分类构建侧栏主题导航。"""
    parts = []
    for category in CATEGORIES:
        items = "".join(
            f'<a class="toc-topic" href="#{topic_anchor(topic["id"])}">'
            f'<span class="topic-number">{topic["id"][:2]}</span>'
            f'{html.escape(topic["name"])}</a>'
            for topic in topics if topic["category"] == category
        )
        if items:
            parts.append(
                f'<div class="toc-region">{html.escape(category)}</div>{items}'
            )
    return "".join(parts)


# ── 导航配置层：搜索索引 ──

_SEARCH_BLOCK_RE = re.compile(
    r'<h[1-6] id="([^"]+)">(.*?)</h[1-6]>'
    r"|<p>(.*?)</p>"
    r"|<li>(.*?)</li>"
    r"|<tr[^>]*>(.*?)</tr>",
    re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _iter_search_blocks(body):
    """从主题正文提取检索块（标题 / 段落 / 列表项 / 表格行）。"""
    for match in _SEARCH_BLOCK_RE.finditer(body):
        heading_id, heading_html, p_html, li_html, tr_html = match.groups()
        if heading_id:
            text = html.unescape(_TAG_RE.sub("", heading_html)).strip()
            yield {"kind": "heading", "id": heading_id, "title": text, "text": text}
        elif p_html is not None:
            text = html.unescape(_TAG_RE.sub("", p_html)).strip()
            if text:
                yield {"kind": "block", "text": text}
        elif li_html is not None:
            text = html.unescape(_TAG_RE.sub("", li_html)).strip()
            if text:
                yield {"kind": "block", "text": text}
        elif tr_html is not None:
            text = html.unescape(_TAG_RE.sub("", tr_html)).strip()
            if text:
                yield {"kind": "block", "text": text}


def build_library_search_index(topics):
    """导航配置层：为汇总阅读页构建全文检索索引。"""
    records = []
    for topic in topics:
        current_id = topic_anchor(topic["id"])
        current_title = topic["name"]
        for block in _iter_search_blocks(topic["body"]):
            if block["kind"] == "heading":
                current_id = block["id"]
                current_title = block["title"]
            records.append({
                "text": block["text"],
                "topic": topic["name"],
                "title": current_title,
                "target": current_id,
            })
    return records


def build_topic_search_index(topics):
    """导航配置层：为主题总览页构建主题 + 章节检索索引。"""
    records = []
    for topic in topics:
        status = "updated" if topic.get("updates") else "baseline"
        records.append({
            "title": topic["name"],
            "meta": topic["category"] + " · 匹配主题",
            "href": "index.html#" + topic_anchor(topic["id"]),
            "text": f"{topic['name']} {topic['description']} {topic['category']}",
            "category": topic["category"],
            "status": status,
        })
        for chapter in topic["chapters"]:
            records.append({
                "title": chapter["title"],
                "meta": topic["name"] + " · 章节直达",
                "href": "library.html#" + chapter["id"],
                "text": f"{topic['name']} {chapter['title']}",
                "category": topic["category"],
                "status": status,
            })
    return records


# ── 内容块层：主题章节 ──

def render_topic_section(topic):
    """内容块：主题章节（汇总阅读页）。"""
    anchor = topic_anchor(topic["id"])
    original_url = quote(topic["html"].relative_to(ROOT).as_posix(), safe="/")
    chapter_items = "".join(
        f'<li><a href="#{chapter["id"]}">{html.escape(chapter["title"])}</a></li>'
        for chapter in topic["chapters"]
    )
    updates = topic.get("updates") or []
    if updates:
        latest = max(update["date"] for update in updates)
        update_flag = (
            f'<span class="topic-update-flag" title="最近更新 {html.escape(latest)}">'
            f"已更新 {len(updates)} 处</span>"
        )
    else:
        update_flag = '<span class="status-badge sb-none">暂无更新</span>'
    kind = "周期监测" if topic["kind"] == "monitor" else "知识手册"
    modified = topic.get("modified") or topic_modified(topic)
    modified_text = f"最近更新 {modified}"
    return f"""
<section class="topic-section" id="{anchor}" data-name="{html.escape(topic['name'], quote=True)}">
  <header class="topic-head">
    <div class="crumb">{html.escape(topic['category'])} · {kind}</div>
    <h2><span class="topic-number">{html.escape(topic['id'][:2])}</span>{html.escape(topic['name'])}</h2>
    <div class="meta">{html.escape(topic['version'])} · {len(topic['chapters'])} 个主要章节 · {modified_text} · {update_flag}</div>
  </header>
  <article class="report-block">
    <header class="report-bar">
      <div class="rt">{html.escape(topic['name'])}</div>
      <span class="badge baseline">基准框架</span>
      <div class="ra"><a href="index.html#{anchor}">返回主题总览</a><a href="{original_url}">独立原文 ↗</a></div>
    </header>
    <details class="topic-local-toc"><summary><span class="summary-text">本主题目录（{len(topic['chapters'])} 个主要章节）</span></summary><div class="details-text"><ul class="chapter-list">{chapter_items}</ul></div></details>
    <div class="topic-body">{topic['body']}</div>
  </article>
</section>"""


# ── 页面装配层：汇总阅读 ──

def render_library(topics):
    total_updates = sum(len(topic.get("updates") or []) for topic in topics)
    documents = "".join(render_topic_section(topic) for topic in topics)
    content = (
        render_topbar("library", "汇总阅读", "全文检索主题正文…（按 / 聚焦）")
        + "\n"
        + render_hero(
            "JAPAN LIFE & WORK KNOWLEDGE BASE",
            "汇总阅读",
            "按主题编号连续阅读全部当前主文档。原标题层级、表格与来源链接均保留并统一添加主题命名空间；"
            "更新内容以「已更新」标注突出展示，未更新内容保持原样。",
            [
                (len(topics), "主题"),
                (total_updates, "处更新标注"),
                (len(CATEGORIES), "分类"),
            ],
            noscript='<p class="noscript-note">JavaScript 不可用，搜索已停用；'
            "完整正文、目录和双向链接仍可使用。</p>",
        )
        + "\n"
        + '<div class="layout">\n'
        + '  <aside class="sidebar" aria-label="主题导航">'
        f'<nav id="toc" aria-label="主题目录">{build_navigation(topics)}</nav></aside>\n'
        + f'  <main class="reader-main" id="main-content">{documents}</main>\n'
        + "</div>\n"
        + render_footer(
            "由 <code>prompts/tools/build_library.py</code> 自动生成 · "
            f"共 {len(topics)} 个主题 · {total_updates} 处更新标注"
        )
        + "\n"
        + render_totop()
    )
    script = (
        "const SEARCH_INDEX = "
        + json.dumps(
            build_library_search_index(topics),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + ";\n"
        + LIBRARY_JS
    )
    return page_shell("汇总阅读｜日本生活与工作知识库", "library-page", content, script)


# ── 导航配置层：Changelog 数据 ──

def build_changelog_entries(topics):
    """把各主题的更新标记展开为倒序 Changelog 条目。"""
    entries = []
    for topic in topics:
        for update in topic.get("updates") or []:
            entries.append({
                "date": update["date"],
                "note": (update.get("note") or "").strip(),
                "topic_name": topic["name"],
                "anchor": topic_anchor(topic["id"]),
            })
    entries.sort(key=lambda item: (item["date"], item["topic_name"]), reverse=True)
    return entries


# ── 内容块层：更新记录分组 ──

def render_changelog_group(group):
    """内容块：单个更新日期的更新列表。"""
    items = "".join(
        '<li>'
        f'<span class="cl-topic">{html.escape(item["topic_name"])}</span>'
        f'<span class="cl-note">{html.escape(item["note"]) if item["note"] else "已更新（无摘要）"}</span>'
        f'<a href="library.html#{item["anchor"]}">查看主题 →</a>'
        '</li>'
        for item in group["items"]
    )
    return (
        f'<section class="cl-group" id="changelog-{group["date"]}">'
        f'<h2 class="cl-date">{group["date"]}</h2>'
        f'<ul class="cl-list">{items}</ul></section>'
    )


# ── 页面装配层：更新记录 ──

def render_changelog(topics):
    """更新记录页：按日期倒序列出全部「已更新」标注。"""
    entries = build_changelog_entries(topics)
    groups = []
    for entry in entries:
        if not groups or groups[-1]["date"] != entry["date"]:
            groups.append({"date": entry["date"], "items": []})
        groups[-1]["items"].append(entry)
    blocks = (
        "".join(render_changelog_group(group) for group in groups)
        or '<p class="noresult">暂无更新记录。</p>'
    )
    content = (
        render_topbar("changelog", "更新记录")
        + "\n"
        + render_hero(
            "JAPAN LIFE & WORK KNOWLEDGE BASE",
            "更新记录",
            "按日期倒序列出全部「已更新」标注。基准框架完整保留，更新内容以日期 + 摘要追踪，"
            "可跳转到汇总阅读对应主题。",
            [
                (len(entries), "条更新"),
                (len(groups), "个更新日期"),
                (len(topics), "个主题"),
            ],
            noscript='<p class="noscript-note">JavaScript 不可用不影响更新记录阅读。</p>',
        )
        + "\n"
        + f'<main class="main" id="main-content">{blocks}</main>\n'
        + render_footer(
            "由 <code>prompts/tools/build_library.py</code> 自动生成 · "
            f"共 {len(entries)} 条更新记录"
        )
        + "\n"
        + render_totop()
    )
    return page_shell("更新记录｜日本生活与工作知识库", "changelog-page", content, CHANGELOG_JS)


def build_pages():
    topics = []
    for config in load_topics():
        source, html_path = resolve_topic_source(config)
        topic = dict(config)
        topic.update({"source": source, "html": html_path, "version": update_scheduler.topic_version(config)})
        topics.append(topic)

    html_to_topic = {topic["html"].resolve(): topic["id"] for topic in topics}
    for topic in topics:
        body = markdown.markdown(
            topic["source"].read_text(encoding="utf-8"),
            extensions=md2html.EXTENSIONS,
            extension_configs=md2html.EXTENSION_CONFIGS,
        )
        topic["body"] = namespace_html(
            body, topic["id"], topic["source"].parent, html_to_topic, topic["name"]
        )
        topic["chapters"] = extract_chapters(topic["body"], topic["id"])
        topic["body"], topic["updates"] = apply_update_markers(topic["body"], topic["id"])
        topic["modified"] = topic_modified(topic)

    heading_ids = re.findall(r'<h[1-6] id="([^"]+)"', "".join(topic["body"] for topic in topics))
    duplicates = sorted({anchor for anchor in heading_ids if heading_ids.count(anchor) > 1})
    if duplicates:
        raise BuildError("汇总页标题锚点冲突：" + "、".join(duplicates))

    return {
        Path("index.html"): render_index(topics),
        Path("library.html"): render_library(topics),
        Path("changelog.html"): render_changelog(topics),
    }


def compare_outputs(pages, root=ROOT):
    stale = []
    for relative_path, expected in pages.items():
        destination = root / relative_path
        if not destination.is_file() or destination.read_text(encoding="utf-8") != expected:
            stale.append(relative_path)
    return stale


def main(argv=None):
    parser = argparse.ArgumentParser(description="生成主题集中展示页与汇总阅读页")
    parser.add_argument("--check", action="store_true", help="仅检查生成页面是否与主题源同步")
    args = parser.parse_args(argv)
    try:
        pages = build_pages()
        if args.check:
            stale = compare_outputs(pages)
            for relative_path in stale:
                print(f"页面需要重新生成: {relative_path}")
            if stale:
                return 1
            print("聚合页面均为最新")
            return 0
        for relative_path, output in pages.items():
            destination = ROOT / relative_path
            destination.write_text(output, encoding="utf-8")
            print(f"生成: {relative_path}")
        return 0
    except BuildError as error:
        print(f"构建失败: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
