"""md -> HTML 同步（html-sync.yml 的 md2html 步骤）。

扫描各业务线 reports/*.md，转换为同名自包含 .html（与 monitoring-common-spec
第 1 节「双格式交付」一致）。纯图表型简报（只出 HTML 的业务线）没有 md 源，
本工具自然跳过。幂等：重复执行产生相同输出。

渲染对齐 monitoring-common-spec 第 3 / 5 节：表格加 class="fixed" 并逐列声明
百分比列宽；h2 章节重编号 id="sN" 并生成简化锚点导航 <nav aria-label="报告导航">
（置于文首 h1 与副标题之后、首个 h2 之前）。

跨主题锚点兼容（2026-11-14）：toc 扩展生成的 id 会剥离非 ASCII 字符
（如「3.3 维权与合规工具箱」→ id="33"），导致形如 #03-维权与合规工具箱 的
GitHub 风格中文锚点在 HTML 中不可达。为此在 sN 重编号之后，为每个标题（h1–h6）
内部注入 <a id="GitHub风格slug"></a> 附加锚点（保留 CJK/字母数字/连字符、
空格转连字符、小写、重复标题加 -N 后缀），sN 导航与跨主题中文锚点双通道并存。

退出码：0 = 成功（含无 md 可转换）；1 = 转换失败或依赖缺失。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import iter_business_dirs  # noqa: E402

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ max-width: 1160px; margin: 24px auto; padding: 0 16px;
      font-family: "Segoe UI", "Microsoft YaHei", sans-serif; color: #1a1a2e; line-height: 1.7; }}
h1, h2, h3 {{ color: #16213e; }}
table {{ border-collapse: collapse; width: 100%; overflow-x: auto; display: block; }}
th, td {{ border: 1px solid #cbd5e1; padding: 6px 10px; text-align: left; }}
th {{ background: #f1f5f9; }}
img {{ max-width: 100%; }}
code {{ background: #f6f8fa; padding: 2px 4px; border-radius: 3px; }}
blockquote {{ border-left: 4px solid #94a3b8; margin: 0; padding-left: 12px; color: #475569; }}
nav {{ margin: 12px 0 20px; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
nav a {{ margin-right: 14px; color: #16213e; font-size: 14px; text-decoration: none; white-space: nowrap; }}
nav a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


H2_RE = re.compile(r"<h2\b[^>]*>.*?</h2>", re.DOTALL)
HEAD_RE = re.compile(r"<h([1-6])\b[^>]*>.*?</h\1>", re.DOTALL)
TABLE_RE = re.compile(r"<table\b.*?</table>", re.DOTALL)
TH_RE = re.compile(r"<th\b[^>]*>")
# GitHub 风格 slug 的剔除字符：保留 \w（含中日韩文字、字母数字、下划线）、连字符与空格
SLUG_STRIP_RE = re.compile(r"[^\w\- ]", re.UNICODE)


def _slug(heading_html: str) -> str:
    """标题 HTML -> GitHub 风格 slug（保留 CJK：小写、去标点、空格转连字符）。"""
    s = _strip_tags(heading_html).strip()
    s = SLUG_STRIP_RE.sub("", s).replace(" ", "-").lower()
    return s


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def _with_width(th: str, width: int) -> str:
    """给单个 <th> 补百分比列宽（已含 width: 时跳过，避免重复声明）。"""
    if "width:" in th:
        return th
    if "style=" in th:
        return re.sub(r'style="([^"]*)"', lambda m: f'style="{m.group(1)}; width:{width}%"', th, count=1)
    return th.replace("<th", f'<th style="width:{width}%"', 1)


def _fix_tables(html: str) -> str:
    """表格加 class="fixed"；表头逐列声明百分比列宽（同表之和 100%）。"""

    def fix(m: re.Match) -> str:
        tbl = m.group(0)
        if 'class="fixed"' not in tbl:
            tbl = tbl.replace("<table", '<table class="fixed"', 1)
        ths = TH_RE.findall(tbl)
        if not ths:
            return tbl
        n = len(ths)
        base, rem = divmod(100, n)
        widths = [base] * n
        widths[-1] += rem
        it = iter(widths)
        return TH_RE.sub(lambda mm: _with_width(mm.group(0), next(it)), tbl)

    return TABLE_RE.sub(fix, html)


def _fix_headings(html: str) -> str:
    """h2 重编号 id="sN"，并在文首（h1 与副标题 h3 之后、首个 h2 之前）插入简化锚点导航（通用规范第 5 节）。"""
    items: list[str] = []

    def repl(m: re.Match) -> str:
        i = len(items) + 1
        items.append(f'<a href="#s{i}">{_strip_tags(m.group(0))}</a>')
        return re.sub(r'\bid="[^"]*"', f'id="s{i}"', m.group(0), count=1)

    html = H2_RE.sub(repl, html)
    if not items:
        return html
    nav = '<nav aria-label="报告导航">\n' + "\n".join(items) + "\n</nav>\n"
    # 优先插在首个 h2 之前（避开 h1 与副标题 h3 之间）；无 h2 时退化为 h1 之后
    m = re.search(r"<h2\b", html)
    if m:
        return html[: m.start()] + nav + html[m.start() :]
    m = re.search(r"<h1\b[^>]*>.*?</h1>", html, re.DOTALL)
    if m:
        return html[: m.end()] + "\n" + nav + html[m.end() :]
    return nav + html


def _fix_heading_anchors(html: str) -> str:
    """为每个标题（h1–h6）注入 GitHub 风格中文 slug 附加锚点，保证跨主题 #中文锚点 链接可达。

    与 _fix_headings 的 sN 重编号双通道并存：h2 保留 id="sN"（导航用），标题内
    额外注入 <a id="slug"></a>（跨主题链接用）；重复标题按 GitHub 惯例追加 -N。
    """
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


def convert(md_path: Path) -> str:
    """md 文本 -> 自包含 HTML 文本。依赖 markdown 包（见 requirements.txt）。"""
    try:
        import markdown
    except ImportError:
        print("[ERROR] 缺少 markdown 依赖，请先执行 pip install -r requirements.txt")
        raise SystemExit(1)
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
    return TEMPLATE.format(title=title, body=body)


def collect_md_reports():
    out = []
    for b in iter_business_dirs():
        reports = b.path / "reports"
        if reports.is_dir():
            out.extend(sorted(reports.glob("*.md")))
    return out


def main() -> int:
    targets = collect_md_reports()
    if not targets:
        print("md2html：无 md 报告源（纯图表型简报只出 HTML），跳过")
        return 0
    ok = 0
    for md in targets:
        try:
            html = convert(md)
            out = md.with_suffix(".html")
            out.write_text(html, encoding="utf-8")
            print(f"[OK] {md} -> {out.name}")
            ok += 1
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] 转换失败 {md}: {e}")
            return 1
    print(f"md2html 完成：转换 {ok} 份")
    return 0


if __name__ == "__main__":
    sys.exit(main())
