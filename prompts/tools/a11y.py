# -*- coding: utf-8 -*-
"""无障碍合规检查：对比度 / 焦点环 / 结构 / 表格语义。

规范来源（已核对官方原文）：
- WebAIM《Contrast and Color Accessibility》/ WCAG 2.1 1.4.3、1.4.11、2.4.7
- GOV.UK Design System：skip link、page template、details 组件
- BBC GEL：Data tables（role=group / aria-labelledby / tabindex / caption）

本模块只做只读检查，供单元测试与 validate.py 第 13 项复用。
"""
from __future__ import annotations

import re

# ─────────────────────────────────────────────────────────────
# 颜色与对比度（WCAG 2.x 相对亮度公式）
# ─────────────────────────────────────────────────────────────

def _srgb(channel: float) -> float:
    channel /= 255.0
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _luminance(rgb) -> float:
    r, g, b = rgb
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def _hex_to_rgb(value: str):
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        return None
    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def parse_color(value: str):
    """解析 #rgb / #rrggbb / rgb() / rgba()，返回 (r, g, b, a) 或 None。"""
    if not value:
        return None
    value = value.strip()
    if value.startswith("#"):
        rgb = _hex_to_rgb(value)
        return (*rgb, 1.0) if rgb else None
    match = re.match(r"rgba?\(([^)]+)\)", value)
    if not match:
        return None
    parts = [p.strip() for p in match.group(1).split(",")]
    if len(parts) < 3:
        return None
    try:
        r, g, b = (int(float(parts[0])), int(float(parts[1])), int(float(parts[2])))
    except ValueError:
        return None
    alpha = float(parts[3]) if len(parts) > 3 else 1.0
    return (r, g, b, alpha)


def _composite(fg, bg):
    """把带透明度的前景色合成到背景色上，返回不透明 rgb。"""
    r, g, b, a = fg
    return (
        round(r * a + bg[0] * (1 - a)),
        round(g * a + bg[1] * (1 - a)),
        round(b * a + bg[2] * (1 - a)),
    )


def contrast_ratio(first, second) -> float:
    l1, l2 = _luminance(first), _luminance(second)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def parse_root_variables(css: str) -> dict:
    """提取 :root 中的 CSS 自定义属性（小写键名）。"""
    variables = {}
    match = re.search(r":root\s*\{(.*?)\}", css, re.DOTALL)
    if not match:
        return variables
    for name, value in re.findall(
        r"(--[a-z0-9-]+)\s*:\s*([^;]+);", match.group(1), re.IGNORECASE
    ):
        variables[name.lower()] = value.strip()
    return variables


def resolve_color(value: str, variables: dict):
    """解析 var(--x) 或字面值，返回 (r, g, b, a) 或 None。"""
    if not value:
        return None
    value = value.strip()
    match = re.fullmatch(r"var\(\s*(--[a-z0-9-]+)\s*\)", value, re.IGNORECASE)
    if match:
        return parse_color(variables.get(match.group(1).lower(), ""))
    return parse_color(value)


def effective_contrast(fg_value: str, bg_value: str, variables: dict) -> float:
    fg = resolve_color(fg_value, variables)
    bg = resolve_color(bg_value, variables)
    if fg is None or bg is None:
        return 0.0
    bg_rgb = (bg[0], bg[1], bg[2])
    return contrast_ratio(_composite(fg, bg_rgb), bg_rgb)


# ─────────────────────────────────────────────────────────────
# 对比度契约（取各令牌的最深/最差背景，覆盖全部用法）
# ─────────────────────────────────────────────────────────────

TEXT_PAIRS = [
    ("正文 ink / 白", "var(--ink)", "#ffffff"),
    ("正文 ink2 / 白", "var(--ink2)", "#ffffff"),
    ("次要 ink3 / 白", "var(--ink3)", "#ffffff"),
    ("次要 ink3 / 页面底", "var(--ink3)", "var(--bg)"),
    ("navy / 页面底", "var(--navy)", "var(--bg)"),
    ("navy2 / blue-l", "var(--navy2)", "var(--blue-l)"),
    ("blue / 白", "var(--blue)", "#ffffff"),
    ("amber / amber-l", "var(--amber)", "var(--amber-l)"),
    ("green / green-l", "var(--green)", "var(--green-l)"),
    ("gray / gray-l", "var(--gray)", "var(--gray-l)"),
    ("topic-body #222 / 白", "#222222", "#ffffff"),
    ("report-bar navy / 渐变底", "var(--navy)", "#edf3fa"),
    ("toc ink2 / 侧栏底", "var(--ink2)", "#fbfcfe"),
    ("hero eyebrow / 渐变最深", "rgba(255,255,255,.72)", "#2f5597"),
    ("hero sub / 渐变最深", "rgba(255,255,255,.8)", "#2f5597"),
    ("hero legend / 渐变最深", "rgba(255,255,255,.78)", "#2f5597"),
    ("hero stat / 渐变最深", "rgba(255,255,255,.85)", "#2f5597"),
    ("topbar nav / 深底", "rgba(255,255,255,.82)", "#16324f"),
    ("topbar brand-sub / 深底", "rgba(255,255,255,.72)", "#16324f"),
    ("topbar placeholder / 深底", "rgba(255,255,255,.55)", "#16324f"),
    ("白 / navy（按钮）", "#ffffff", "var(--navy)"),
    ("白 / navy2（按钮 hover）", "#ffffff", "var(--navy2)"),
]

NON_TEXT_PAIRS = [
    ("搜索框边框 / 深底", "rgba(255,255,255,.6)", "#16324f"),
    ("chip 边框 / 白", "var(--border-control)", "#ffffff"),
    ("target 高亮环 / 白", "var(--blue)", "#ffffff"),
]


def check_palette_contrast(css: str) -> list:
    """文字对比度：WCAG 2.1 AA 正文 4.5:1。"""
    variables = parse_root_variables(css)
    errors = []
    for label, fg, bg in TEXT_PAIRS:
        ratio = effective_contrast(fg, bg, variables)
        if ratio < 4.5:
            errors.append(f"对比度（文字）{label}: {ratio:.2f}:1 < 4.5:1")
    return errors


def check_non_text_contrast(css: str) -> list:
    """非文本对比度：WCAG 2.1 AA 1.4.11 要求 3:1。"""
    variables = parse_root_variables(css)
    errors = []
    for label, fg, bg in NON_TEXT_PAIRS:
        ratio = effective_contrast(fg, bg, variables)
        if ratio < 3.0:
            errors.append(f"对比度（非文本）{label}: {ratio:.2f}:1 < 3:1")
    return errors


# ─────────────────────────────────────────────────────────────
# 焦点环
# ─────────────────────────────────────────────────────────────

def _outline_color(block: str):
    match = re.search(r"outline-color\s*:\s*([^;]+);", block)
    if match:
        return match.group(1).strip()
    match = re.search(r"(?:^|;)\s*outline\s*:\s*([^;]+);", block)
    if match:
        for part in reversed(match.group(1).split()):
            if parse_color(part):
                return part
    return None


def check_focus_indicator(css: str) -> list:
    """焦点可见性：2.4.7 + 1.4.11（焦点指示物 3:1）。"""
    errors = []
    if re.search(r"outline\s*:\s*(none|0)\s*;", css):
        errors.append("焦点环：存在 outline:none/0，需移除并改用 :focus-visible")
    rules = re.findall(r"(?m)([^{}]*:focus-visible[^{]*)\{([^}]*)\}", css)
    if not rules:
        errors.append("焦点环：缺少 :focus-visible 规则")
        return errors
    variables = parse_root_variables(css)
    colors = []
    for selector, block in rules:
        color = _outline_color(block)
        if color:
            colors.append((selector.strip(), color))
    if not colors:
        errors.append("焦点环：:focus-visible 规则未指定 outline 颜色")
        return errors
    for selector, color in colors:
        if "topbar" in selector or "header" in selector:
            ratio = effective_contrast(color, "#16324f", variables)
            if ratio < 3.0:
                errors.append(f"焦点环 {selector} 颜色 {color} 在深底上 {ratio:.2f}:1 < 3:1")
        else:
            ratio = effective_contrast(color, "#ffffff", variables)
            if ratio < 3.0:
                errors.append(f"焦点环 {selector} 颜色 {color} 在白底上 {ratio:.2f}:1 < 3:1")
    return errors


# ─────────────────────────────────────────────────────────────
# 结构 / 表格语义
# ─────────────────────────────────────────────────────────────

def check_structure(html: str, require_chrome: bool = True) -> list:
    """landmark 骨架与 skip link（GOV.UK / APG）。

    require_chrome=True 用于聚合页（含 header/footer/nav/aside）；
    独立原文页只有 skip link + main（无站点 chrome），传 False。
    """
    errors = []
    body = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL)
    content = body.group(1) if body else html
    if not re.match(
        r'\s*<a [^>]*class="skip-link"[^>]*href="#main-content"', content
    ):
        errors.append("结构：body 首位缺少 skip link（href=#main-content）")
    if not re.search(r'<main[^>]*id="main-content"', html):
        errors.append("结构：缺少 main#main-content landmark")
    if require_chrome:
        if not re.search(r"<header", html):
            errors.append("结构：缺少 header landmark")
        if not re.search(r"<footer", html):
            errors.append("结构：缺少 footer landmark")
        for tag in ("nav", "aside"):
            for match in re.finditer(rf"<{tag}[^>]*>", html):
                if 'aria-label="' not in match.group(0):
                    errors.append(f"结构：<{tag}> 缺少 aria-label")
    return errors


def check_details(html: str) -> list:
    """details 结构（GOV.UK：summary > span.summary-text + div.details-text）。"""
    errors = []
    for match in re.finditer(r"<details[^>]*>(.*?)</details>", html, re.DOTALL):
        block = match.group(0)
        if not re.search(r"<summary><span class=\"summary-text\">", block):
            errors.append("结构：details 缺少 <summary><span class=summary-text> 结构")
        if not re.search(r'</summary><div class="details-text">', block):
            errors.append("结构：details 缺少 <div class=details-text> 内容包裹")
    return errors


def check_tables(html: str) -> list:
    """表格语义（BBC GEL：容器 role=group + aria-labelledby + tabindex + caption + th[scope]）。"""
    errors = []
    wrappers = re.findall(r'<div class="table-wrap"([^>]*)>', html)
    for attrs in wrappers:
        if 'role="group"' not in attrs:
            errors.append("表格容器缺少 role=group")
        if 'tabindex="0"' not in attrs:
            errors.append("表格容器缺少 tabindex=0")
        labelledby = re.search(r'aria-labelledby="([^"]+)"', attrs)
        if not labelledby:
            errors.append("表格容器缺少 aria-labelledby")
        elif f'<caption id="{labelledby.group(1)}"' not in html:
            errors.append(f"表格容器引用的 caption 不存在: #{labelledby.group(1)}")
    for table in re.findall(r"<table>.*?</table>", html, re.DOTALL):
        if "<caption" not in table:
            errors.append("表格缺少 <caption>")
        if not re.search(r'<th[^>]*scope="(col|row)"', table):
            errors.append("表格表头缺少 scope 属性")
    return errors


def check_html(html: str, page_kind: str = "aggregate") -> list:
    """对单个 HTML 页面执行结构 / 表格检查。

    page_kind="aggregate"：聚合页，校验完整 landmark / details / 表格语义；
    page_kind="source"：独立原文页，仅校验 skip link + main 骨架。
    """
    aggregate = page_kind == "aggregate"
    errors = check_structure(html, require_chrome=aggregate)
    if aggregate:
        errors += check_details(html) + check_tables(html)
    return errors
