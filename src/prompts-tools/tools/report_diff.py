"""跨月内容对比高亮（block 级 diff + 「已更新」标记）。

把当期报告与上一期（同主题、最近一个更早自然月）报告做全量内容比对：
- 未变更块：原样展示；
- 新增块：绿色高亮 + 「已更新 · 新增」标记；
- 修改块：黄色高亮 + 「已更新 · 修改」标记，并保留旧块为删除态（可追溯）；
- 删除块：灰色删除线 + 「已更新 · 删除」标记。

分块粒度：标题 / 段落 / 列表项 / 表格行 / 引用块 / 代码块（block 级），
基于 `difflib.SequenceMatcher` 的 LCS 比对。纯函数，供 build_hub 与测试调用。
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser

# block 级元素：作为最小比对单元
BLOCK_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "tr", "pre", "hr", "dt", "dd"}
# 容器元素：继续向下递归，不整体成块
CONTAINER_TAGS = {
    "#document", "body", "blockquote", "table", "thead", "tbody", "tfoot",
    "ul", "ol", "dl", "div", "nav", "section", "article", "aside", "header",
    "footer", "main", "figure", "figcaption", "details", "summary",
}
VOID_TAGS = {"br", "hr", "img", "meta", "link", "input", "area", "base", "col", "embed", "source", "track", "wbr"}

BADGE_TEXT = {"new": "已更新 · 新增", "mod": "已更新 · 修改", "del": "已更新 · 删除"}


@dataclass
class Block:
    tag: str
    text: str
    html: str


class _Node:
    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag: str, attrs: list | None = None):
        self.tag = tag
        self.attrs = attrs or []
        self.children: list = []


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("#document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(_Node(tag, attrs))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _serialize(node) -> str:
    if isinstance(node, str):
        return escape(node)
    if node.tag == "#document":
        return "".join(_serialize(c) for c in node.children)
    attrs = "".join(f' {k}="{escape(v, quote=True)}"' for k, v in node.attrs)
    if node.tag in VOID_TAGS:
        return f"<{node.tag}{attrs}>"
    inner = "".join(_serialize(c) for c in node.children)
    return f"<{node.tag}{attrs}>{inner}</{node.tag}>"


def _inner_text(node) -> str:
    if isinstance(node, str):
        return node
    return "".join(_inner_text(c) for c in node.children)


def _normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _extract(node: _Node, out: list[Block]) -> None:
    for child in node.children:
        if isinstance(child, str):
            if child.strip():
                out.append(Block("#text", _normalize_text(child), escape(child)))
            continue
        if child.tag in BLOCK_TAGS:
            out.append(Block(child.tag, _normalize_text(_inner_text(child)), _serialize(child)))
        elif child.tag in CONTAINER_TAGS:
            _extract(child, out)
        else:
            # 容器层出现的行内元素（如裸 <strong>）：按文本块处理
            out.append(Block(child.tag, _normalize_text(_inner_text(child)), _serialize(child)))


def extract_blocks(html: str) -> list[Block]:
    """HTML 文本 -> block 列表（保留原始 HTML 供高亮渲染）。"""
    builder = _TreeBuilder()
    builder.feed(html)
    blocks: list[Block] = []
    _extract(builder.root, blocks)
    return blocks


def _mark(html: str, tag: str, kind: str) -> str:
    """给单个 block 的 HTML 打高亮标记 + 「已更新」徽章。"""
    cls = f"diff-{kind}"
    badge = f'<span class="diff-badge">{BADGE_TEXT[kind]}</span>'
    if tag == "li":
        marked = re.sub(r"<li\b[^>]*>", lambda m: m.group(0)[:-1] + f' class="{cls}">', html, count=1)
        return re.sub(r"(<li\b[^>]*>)", r"\1" + badge, marked, count=1)
    if tag == "tr":
        marked = re.sub(r"<tr\b[^>]*>", lambda m: m.group(0)[:-1] + f' class="{cls}">', html, count=1)
        return re.sub(r"(<t[dh]\b[^>]*>)", r"\1" + badge, marked, count=1)
    if tag == "hr":
        return html
    return f'<div class="diff-block {cls}">{badge}{html}</div>'


# 配对为「修改」的最低文本相似度：低于此值按「删除 + 新增」处理，
# 避免把结构重排误判为逐块修改。
MOD_SIMILARITY = 0.35


def _similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def diff_blocks(prev_blocks: list[Block], curr_blocks: list[Block]) -> list[tuple[str, Block, Block | None]]:
    """比对两期 block 序列 -> [(op, curr_block, prev_block_or_None)]。

    op ∈ {equal, new, mod, del}。mod 同时携带旧块（用于删除态展示）。
    replace 块按位置配对，仅当文本相似度 ≥ MOD_SIMILARITY 时判为「修改」，
    否则拆分为「删除 + 新增」，保证对比结论准确。
    """
    prev_texts = [b.text for b in prev_blocks]
    curr_texts = [b.text for b in curr_blocks]
    sm = difflib.SequenceMatcher(None, prev_texts, curr_texts, autojunk=False)
    out: list[tuple[str, Block, Block | None]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for j in range(j1, j2):
                out.append(("equal", curr_blocks[j], None))
        elif tag == "insert":
            for j in range(j1, j2):
                out.append(("new", curr_blocks[j], None))
        elif tag == "delete":
            for i in range(i1, i2):
                out.append(("del", prev_blocks[i], None))
        else:  # replace
            old = prev_blocks[i1:i2]
            new = curr_blocks[j1:j2]
            paired = min(len(old), len(new))
            for k in range(paired):
                if _similarity(old[k].text, new[k].text) >= MOD_SIMILARITY:
                    out.append(("mod", new[k], old[k]))
                else:
                    out.append(("del", old[k], None))
                    out.append(("new", new[k], None))
            for k in range(paired, len(old)):
                out.append(("del", old[k], None))
            for k in range(paired, len(new)):
                out.append(("new", new[k], None))
    return out


def _group_del(blocks: list[Block]) -> str:
    """把连续删除块折叠为一组（默认收起，可展开追溯）。"""
    inner = "".join(b.html for b in blocks)
    return (
        f'<details class="diff-del-group">'
        f'<summary>已更新 · 删除 {len(blocks)} 处（点击展开）</summary>'
        f'{inner}</details>'
    )


def render_diffed_body(curr_html: str, prev_html: str | None) -> tuple[str, dict]:
    """渲染当期报告 body（含高亮标记）-> (html, 统计)。

    - 未变更：原样展示；
    - 新增 / 修改：高亮 + 「已更新」徽章；
    - 删除：折叠为可展开组（默认收起，避免干扰阅读）。
    prev_html 为 None（首期）时原样返回，统计为全 0。
    """
    curr_blocks = extract_blocks(curr_html)
    if prev_html is None:
        return curr_html, {"new": 0, "mod": 0, "del": 0, "equal": len(curr_blocks), "prev": None}

    prev_blocks = extract_blocks(prev_html)
    ops = diff_blocks(prev_blocks, curr_blocks)
    stats = {"new": 0, "mod": 0, "del": 0, "equal": 0, "prev": len(prev_blocks)}
    parts: list[str] = []
    del_buffer: list[Block] = []

    def flush() -> None:
        if del_buffer:
            parts.append(_group_del(del_buffer))
            del_buffer.clear()

    for op, block, old in ops:
        stats[op] += 1
        if op == "equal":
            flush()
            parts.append(block.html)
        elif op == "new":
            flush()
            parts.append(_mark(block.html, block.tag, "new"))
        elif op == "mod":
            # 旧块并入删除组（折叠），新块高亮为「修改」；旧块计入删除统计
            if old is not None:
                del_buffer.append(old)
                stats["del"] += 1
            flush()
            parts.append(_mark(block.html, block.tag, "mod"))
        else:  # del
            del_buffer.append(block)
    flush()
    return "".join(parts), stats


def strip_body(html: str) -> str:
    """取 HTML 的 <body> 内容；无 body 时返回原文。"""
    m = re.search(r"<body\b[^>]*>(.*)</body>", html, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else html


def diff_summary(stats: dict, period: str, prev_period: str | None) -> str:
    """生成对比摘要文案。"""
    if prev_period is None:
        return f"{period} 期为首期报告，无上期对比。"
    return (
        f"{period} 期与 {prev_period} 期对比："
        f"新增 {stats['new']} 处、修改 {stats['mod']} 处、删除 {stats['del']} 处，"
        f"未变更 {stats['equal']} 处。"
    )
