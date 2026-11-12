# -*- coding: utf-8 -*-
"""从主题主文档生成集中展示页与汇总阅读页。"""

import argparse
import html
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


def namespace_html(body, topic_id, source_dir, html_to_topic):
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
    return re.sub(
        r"<table>.*?</table>",
        lambda match: f'<div class="table-wrap">{match.group(0)}</div>',
        body,
        flags=re.DOTALL,
    )


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


CATEGORIES = ("监测动态", "职业就业", "行业技术", "经济环境", "制度政策", "学习成长", "生活地域")

LIBRARY_CSS = """
:root { --accent: #1a5f5a; --ink: #222; --muted: #66736f; --line: #d9e2df; --paper: #fff; --wash: #f4f7f6; }
html { scroll-behavior: smooth; scroll-padding-top: 88px; }
body.index-page, body.library-page { max-width: none; margin: 0; padding: 0; background: var(--wash); color: var(--ink); }
.site-header { position: sticky; top: 0; z-index: 30; background: rgba(255,255,255,.97); border-bottom: 1px solid var(--line); }
.topbar { max-width: 1200px; margin: 0 auto; padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.brand { color: var(--accent); font-size: 18px; font-weight: 700; white-space: nowrap; }
.topnav { display: flex; flex-wrap: wrap; gap: 16px; font-size: 14px; }
.topnav a[aria-current="page"] { font-weight: 700; border-bottom: 2px solid var(--accent); }
.page-main { max-width: 1200px; margin: 0 auto; padding: 28px 24px 48px; }
.hero { margin-bottom: 22px; }
.hero h1 { margin: 0 0 8px; padding: 0; border: 0; font-size: 28px; }
.hero p { margin: 0; color: var(--muted); }
.search-shell { position: relative; max-width: 820px; margin: 18px 0; }
.search-input { width: 100%; padding: 12px 16px; border: 1px solid #b9c9c4; border-radius: 8px; font: inherit; background: #fff; }
.search-input:focus { outline: 3px solid rgba(26,95,90,.18); border-color: var(--accent); }
.search-hint { margin: 6px 0 0; color: var(--muted); font-size: 12px; }
.search-results { display: none; position: absolute; z-index: 40; top: calc(100% - 24px); left: 0; right: 0; max-height: 420px; overflow-y: auto; padding: 8px; background: #fff; border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 10px 30px rgba(20,50,45,.14); }
.search-results.is-visible { display: block; }
.search-result { display: block; padding: 10px 12px; border-radius: 5px; color: var(--ink); }
.search-result:hover, .search-result:focus { background: #edf5f3; text-decoration: none; }
.search-result strong, .search-result span { display: block; }
.search-result span { color: var(--muted); font-size: 12px; line-height: 1.55; }
.search-empty { padding: 14px; margin: 0; color: var(--muted); }
.category-nav { display: flex; flex-wrap: wrap; gap: 8px; margin: 22px 0; }
.category-nav a { padding: 6px 12px; border: 1px solid var(--line); border-radius: 999px; background: #fff; font-size: 13px; }
.category-nav a.is-active { color: #fff; background: var(--accent); border-color: var(--accent); }
.category-section { margin: 30px 0; scroll-margin-top: 82px; }
.category-heading { margin: 0 0 14px; padding-left: 10px; border-left: 4px solid var(--accent); font-size: 20px; }
.topic-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
.topic-card { min-width: 0; padding: 20px; background: var(--paper); border: 1px solid var(--line); border-radius: 10px; scroll-margin-top: 88px; }
.topic-card:target { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(26,95,90,.18); }
.topic-card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.topic-title { margin: 0; font-size: 18px; line-height: 1.5; }
.topic-number { color: var(--accent); margin-right: 6px; }
.topic-category { flex: none; padding: 2px 8px; border-radius: 4px; background: #edf5f3; color: var(--accent); font-size: 12px; }
.topic-description { min-height: 3.4em; margin: 12px 0; color: #4d5955; }
.topic-meta { color: var(--muted); font-size: 12px; }
.card-actions { display: flex; flex-wrap: wrap; gap: 10px; margin: 16px 0 12px; }
.button { display: inline-block; padding: 7px 12px; border: 1px solid var(--accent); border-radius: 6px; font-size: 13px; }
.button-primary { color: #fff; background: var(--accent); }
.button-secondary { color: var(--accent); background: #fff; }
.topic-details { border-top: 1px solid #edf1ef; padding-top: 10px; }
.topic-details summary, .topic-local-toc summary { cursor: pointer; color: var(--accent); font-weight: 700; }
.chapter-list { margin: 8px 0 0; padding-left: 0; list-style: none; }
.chapter-list li { margin: 0; }
.chapter-list a { display: block; padding: 5px 8px; border-radius: 4px; font-size: 13px; }
.chapter-list a:hover { background: #edf5f3; }
.library-layout { display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 24px; align-items: start; }
.library-sidebar { position: sticky; top: 84px; max-height: calc(100vh - 104px); overflow-y: auto; }
.topic-navigation { padding: 14px; background: #fff; border: 1px solid var(--line); border-radius: 8px; }
.topic-navigation summary { cursor: pointer; color: var(--accent); font-weight: 700; }
.topic-navigation ul { margin: 10px 0 0; padding-left: 0; list-style: none; }
.topic-navigation li { margin: 0; }
.topic-navigation a { display: block; padding: 5px 7px; border-radius: 4px; font-size: 13px; line-height: 1.5; }
.topic-navigation a:hover { background: #edf5f3; }
.library-content { min-width: 0; }
.topic-document { min-width: 0; margin-bottom: 28px; padding: 28px; background: #fff; border: 1px solid var(--line); border-radius: 10px; scroll-margin-top: 82px; }
.topic-document:target { border-color: var(--accent); }
.topic-toolbar { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px; padding-bottom: 12px; border-bottom: 1px solid var(--line); color: var(--muted); font-size: 12px; }
.topic-toolbar-links { display: flex; flex-wrap: wrap; gap: 12px; }
.topic-local-toc { margin: 18px 0; padding: 12px 16px; background: #f4f7f6; border-radius: 6px; }
.topic-local-toc .chapter-list { columns: 2; column-gap: 24px; }
.topic-body { min-width: 0; }
.topic-body p, .topic-body li { overflow-wrap: anywhere; }
.topic-body h1:first-child { margin-top: 18px; }
.topic-body h1, .topic-body h2, .topic-body h3, .topic-body h4, .topic-body h5, .topic-body h6 { scroll-margin-top: 86px; }
.topic-body h1:target, .topic-body h2:target, .topic-body h3:target, .topic-body h4:target, .topic-body h5:target, .topic-body h6:target { background: #fff3bf; outline: 3px solid #fff3bf; }
.table-wrap { max-width: 100%; overflow-x: auto; }
.table-wrap table { min-width: 480px; width: 100%; }
.topic-body img { height: auto; }
.update-badge { display: inline-block; margin: 0 0 0 6px; padding: 1px 8px; border: 1px solid #e5d272; border-radius: 999px; background: #fff3bf; color: #7a5c00; font-size: 12px; font-weight: 400; line-height: 1.6; vertical-align: middle; white-space: nowrap; }
.update-note { margin-left: 4px; color: #9a7b1e; font-size: 12px; font-weight: 400; }
.update-block { position: relative; margin: 1.2em 0; padding: 14px 16px; background: #fffdf6; border: 1px solid #f0dfa8; border-left: 4px solid #e8b93c; border-radius: 6px; }
.update-block > .update-badge { position: absolute; top: -11px; left: 12px; margin: 0; box-shadow: 0 1px 2px rgba(120,90,10,.12); }
.update-section { margin: 1.4em 0; padding: 2px 0 2px 16px; border-left: 4px solid #e8b93c; background: rgba(232,185,60,.05); }
.topic-update-flag { display: inline-block; margin-left: 6px; padding: 0 6px; border: 1px solid #e5d272; border-radius: 999px; background: #fff3bf; color: #7a5c00; font-size: 11px; line-height: 1.6; white-space: nowrap; }
.noscript-note { padding: 10px 14px; background: #fff3bf; border: 1px solid #e5d272; }
[hidden] { display: none !important; }
@media (min-width: 761px) {
  .topic-navigation > .navigation-content { display: block; }
  .topic-navigation > summary { pointer-events: none; list-style: none; }
}
@media (max-width: 760px) {
  html { scroll-padding-top: 18px; }
  .site-header { position: static; }
  .topbar { padding: 12px 16px; align-items: flex-start; flex-direction: column; gap: 8px; }
  .page-main { padding: 20px 14px 36px; }
  .hero h1 { font-size: 24px; }
  .topic-grid { grid-template-columns: minmax(0, 1fr); }
  .topic-description { min-height: 0; }
  .library-layout { display: block; }
  .library-sidebar { position: static; max-height: none; margin-bottom: 18px; }
  .topic-document { padding: 18px 15px; }
  .topic-local-toc .chapter-list { columns: 1; }
  .search-results { position: static; margin-top: 6px; max-height: 360px; }
}
@media print {
  .site-header, .search-shell, .category-nav, .library-sidebar, .card-actions, .topic-toolbar { display: none !important; }
  body.index-page, body.library-page { background: #fff; }
  .library-layout { display: block; }
  .topic-document { border: 0; padding: 0; break-before: page; }
}
"""

INDEX_JS = r"""
(() => {
  const input = document.getElementById('site-search');
  const resultBox = document.getElementById('search-results');
  const cards = Array.from(document.querySelectorAll('.topic-card'));
  const sections = Array.from(document.querySelectorAll('.category-section'));
  const chapters = Array.from(document.querySelectorAll('.chapter-link'));
  const filters = Array.from(document.querySelectorAll('[data-filter]'));
  let activeCategory = '';
  let timer;

  const termsOf = value => value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const matches = (text, terms) => terms.every(term => text.toLowerCase().includes(term));

  function renderResults(items, query) {
    resultBox.replaceChildren();
    if (!query) {
      resultBox.classList.remove('is-visible');
      return;
    }
    resultBox.classList.add('is-visible');
    if (!items.length) {
      const empty = document.createElement('p');
      empty.className = 'search-empty';
      empty.textContent = '未找到匹配主题或章节。';
      resultBox.appendChild(empty);
      return;
    }
    items.slice(0, 30).forEach(item => {
      const link = document.createElement('a');
      link.className = 'search-result';
      link.href = item.href;
      const title = document.createElement('strong');
      title.textContent = item.title;
      const meta = document.createElement('span');
      meta.textContent = item.meta;
      link.append(title, meta);
      resultBox.appendChild(link);
    });
  }

  function applyFilters() {
    const query = input.value.trim();
    const terms = termsOf(query);
    const results = [];
    cards.forEach(card => {
      const categoryOk = !activeCategory || card.dataset.category === activeCategory;
      const textOk = !terms.length || matches(card.textContent, terms);
      card.hidden = !(categoryOk && textOk);
      if (categoryOk && terms.length && textOk) {
        results.push({
          href: 'index.html#' + card.id,
          title: card.querySelector('.topic-title').textContent.trim(),
          meta: card.dataset.category + ' · 匹配主题'
        });
      }
    });
    chapters.forEach(link => {
      const card = link.closest('.topic-card');
      const categoryOk = !activeCategory || card.dataset.category === activeCategory;
      if (categoryOk && terms.length && matches(link.dataset.search, terms)) {
        card.hidden = false;
        results.push({
          href: link.href,
          title: link.textContent.trim(),
          meta: card.querySelector('.topic-title').textContent.trim() + ' · 章节直达'
        });
      }
    });
    sections.forEach(section => {
      section.hidden = !Array.from(section.querySelectorAll('.topic-card')).some(card => !card.hidden);
    });
    renderResults(results, query);
  }

  filters.forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    activeCategory = link.dataset.filter;
    filters.forEach(item => item.classList.toggle('is-active', item === link));
    applyFilters();
  }));
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(applyFilters, 150);
  });
  resultBox.addEventListener('click', () => resultBox.classList.remove('is-visible'));
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      event.preventDefault();
      input.focus();
    }
    if (event.key === 'Escape' && document.activeElement === input) {
      input.value = '';
      applyFilters();
    }
  });
})();
"""

LIBRARY_JS = r"""
(() => {
  const input = document.getElementById('site-search');
  const resultBox = document.getElementById('search-results');
  const records = [];
  let timer;

  document.querySelectorAll('.topic-document').forEach(topic => {
    let currentId = topic.id;
    let currentTitle = topic.dataset.name;
    const blocks = topic.querySelectorAll('.topic-body h1, .topic-body h2, .topic-body h3, .topic-body h4, .topic-body h5, .topic-body h6, .topic-body p, .topic-body li, .topic-body tr');
    blocks.forEach(block => {
      if (/^H[1-6]$/.test(block.tagName)) {
        currentId = block.id;
        currentTitle = block.textContent.trim();
      }
      const text = block.textContent.trim();
      if (text) {
        records.push({ text, topic: topic.dataset.name, title: currentTitle, target: currentId });
      }
    });
  });

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
      resultBox.classList.remove('is-visible');
      return;
    }
    resultBox.classList.add('is-visible');
    const found = records.filter(record => matches(record.text, terms)).slice(0, 30);
    if (!found.length) {
      const empty = document.createElement('p');
      empty.className = 'search-empty';
      empty.textContent = '未找到匹配内容，原正文仍可继续阅读。';
      resultBox.appendChild(empty);
      return;
    }
    found.forEach(record => {
      const link = document.createElement('a');
      link.className = 'search-result';
      link.href = '#' + record.target;
      const title = document.createElement('strong');
      title.textContent = record.topic + ' · ' + record.title;
      const meta = document.createElement('span');
      meta.textContent = snippet(record.text, terms);
      link.append(title, meta);
      resultBox.appendChild(link);
    });
  }

  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(renderResults, 150);
  });
  resultBox.addEventListener('click', () => resultBox.classList.remove('is-visible'));
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
{md2html.BASE_CSS}
{LIBRARY_CSS}
</style>
</head>
<body class="{body_class}">
{content}
<script>{script}</script>
</body>
</html>
"""


def render_index(topics):
    sections = []
    for category_index, category in enumerate(CATEGORIES, 1):
        category_topics = [topic for topic in topics if topic["category"] == category]
        cards = []
        for topic in category_topics:
            topic_id = topic["id"]
            anchor = topic_anchor(topic_id)
            original_url = quote(topic["html"].relative_to(ROOT).as_posix(), safe="/")
            chapter_items = "".join(
                f'<li><a class="chapter-link" data-search="{html.escape(topic["name"] + " " + chapter["title"], quote=True)}" href="library.html#{chapter["id"]}">{html.escape(chapter["title"])}</a></li>'
                for chapter in topic["chapters"]
            )
            updates = topic.get("updates") or []
            update_flag = ""
            if updates:
                latest = max(update["date"] for update in updates)
                update_flag = (
                    f'<span class="topic-update-flag" title="最近更新 {html.escape(latest)}">'
                    f"已更新 {len(updates)} 处</span>"
                )
            cards.append(f"""
<article class="topic-card" id="{anchor}" data-category="{html.escape(topic['category'], quote=True)}">
  <div class="topic-card-header">
    <h3 class="topic-title"><span class="topic-number">{html.escape(topic_id[:2])}</span>{html.escape(topic['name'])}</h3>
    <span class="topic-category">{html.escape(topic['category'])}</span>
  </div>
  <p class="topic-description">{html.escape(topic['description'])}</p>
  <div class="topic-meta">{html.escape(topic['version'])} · {'周期监测' if topic['kind'] == 'monitor' else '知识手册'} · {len(topic['chapters'])} 个主要章节{update_flag}</div>
  <div class="card-actions">
    <a class="button button-primary" href="library.html#{anchor}">在汇总页阅读 →</a>
    <a class="button button-secondary" href="{original_url}">查看独立原文</a>
  </div>
  <details class="topic-details">
    <summary>主题详情与章节直达</summary>
    <ul class="chapter-list">{chapter_items}</ul>
  </details>
</article>""")
        sections.append(f"""
<section class="category-section" id="category-{category_index}">
  <h2 class="category-heading">{html.escape(category)} <small>{len(category_topics)} 个主题</small></h2>
  <div class="topic-grid">{''.join(cards)}</div>
</section>""")

    category_links = '<a href="#topics" data-filter="" class="is-active">全部</a>' + "".join(
        f'<a href="#category-{index}" data-filter="{category}">{category}</a>'
        for index, category in enumerate(CATEGORIES, 1)
    )
    content = f"""
<header class="site-header">
  <div class="topbar">
    <a class="brand" href="index.html">日本生活与工作知识库</a>
    <nav class="topnav" aria-label="主导航"><a href="index.html" aria-current="page">主题总览</a><a href="library.html">汇总阅读</a><a href="updates.html">周期更新看板</a></nav>
  </div>
</header>
<main class="page-main" id="topics">
  <div class="hero"><h1>主题总览</h1><p>集中浏览 13 个当前主题，展开章节详情，或进入连续汇总阅读。历史归档不在此重复收录。</p></div>
  <div class="search-shell">
    <input class="search-input" id="site-search" type="search" placeholder="搜索主题、分类或章节，例如：司机 薪资" autocomplete="off">
    <p class="search-hint">按 / 快速聚焦，按 Esc 清空；最多展示 30 条结果。</p>
    <div class="search-results" id="search-results" role="region" aria-label="搜索结果" aria-live="polite"></div>
  </div>
  <nav class="category-nav" aria-label="主题分类">{category_links}</nav>
  {''.join(sections)}
</main>"""
    return page_shell("主题总览｜日本生活与工作知识库", "index-page", content, INDEX_JS)


def render_library(topics):
    navigation = "".join(
        f'<li><a href="#{topic_anchor(topic["id"])}"><span class="topic-number">{topic["id"][:2]}</span>{html.escape(topic["name"])}</a></li>'
        for topic in topics
    )
    documents = []
    for topic in topics:
        anchor = topic_anchor(topic["id"])
        original_url = quote(topic["html"].relative_to(ROOT).as_posix(), safe="/")
        chapter_items = "".join(
            f'<li><a href="#{chapter["id"]}">{html.escape(chapter["title"])}</a></li>'
            for chapter in topic["chapters"]
        )
        updates = topic.get("updates") or []
        update_flag = ""
        if updates:
            latest = max(update["date"] for update in updates)
            update_flag = (
                f'　<span class="topic-update-flag" title="最近更新 {html.escape(latest)}">'
                f"已更新 {len(updates)} 处</span>"
            )
        documents.append(f"""
<section class="topic-document" id="{anchor}" data-name="{html.escape(topic['name'], quote=True)}">
  <header class="topic-toolbar">
    <span>{html.escape(topic['category'])} · {html.escape(topic['version'])}{update_flag}</span>
    <div class="topic-toolbar-links"><a href="index.html#{anchor}">返回主题总览</a><a href="{original_url}">独立原文</a></div>
  </header>
  <details class="topic-local-toc"><summary>本主题目录（{len(topic['chapters'])} 个主要章节）</summary><ul class="chapter-list">{chapter_items}</ul></details>
  <div class="topic-body">{topic['body']}</div>
</section>""")
    content = f"""
<header class="site-header">
  <div class="topbar">
    <a class="brand" href="index.html">日本生活与工作知识库</a>
    <nav class="topnav" aria-label="主导航"><a href="index.html">主题总览</a><a href="library.html" aria-current="page">汇总阅读</a><a href="updates.html">周期更新看板</a></nav>
  </div>
</header>
<main class="page-main">
  <div class="hero"><h1>汇总阅读</h1><p>按主题编号连续阅读全部当前主文档。原标题层级、表格与来源链接均保留，并统一添加主题命名空间。</p></div>
  <div class="search-shell">
    <input class="search-input" id="site-search" type="search" placeholder="搜索全部主题正文，例如：永住" autocomplete="off">
    <p class="search-hint">按 / 快速聚焦，按 Esc 清空；点击结果定位到最近章节，正文不会被隐藏。</p>
    <div class="search-results" id="search-results" role="region" aria-label="全文搜索结果" aria-live="polite"></div>
    <noscript><p class="noscript-note">JavaScript 不可用，搜索已停用；完整正文、目录和双向链接仍可使用。</p></noscript>
  </div>
  <div class="library-layout">
    <aside class="library-sidebar"><details class="topic-navigation"><summary>全部主题导航</summary><div class="navigation-content"><ul>{navigation}</ul></div></details></aside>
    <div class="library-content">{''.join(documents)}</div>
  </div>
</main>"""
    return page_shell("汇总阅读｜日本生活与工作知识库", "library-page", content, LIBRARY_JS)


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
        topic["body"] = namespace_html(body, topic["id"], topic["source"].parent, html_to_topic)
        topic["chapters"] = extract_chapters(topic["body"], topic["id"])
        topic["body"], topic["updates"] = apply_update_markers(topic["body"], topic["id"])

    heading_ids = re.findall(r'<h[1-6] id="([^"]+)"', "".join(topic["body"] for topic in topics))
    duplicates = sorted({anchor for anchor in heading_ids if heading_ids.count(anchor) > 1})
    if duplicates:
        raise BuildError("汇总页标题锚点冲突：" + "、".join(duplicates))

    return {
        Path("index.html"): render_index(topics),
        Path("library.html"): render_library(topics),
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
