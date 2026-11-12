# -*- coding: utf-8 -*-
"""Markdown 转 HTML 批量转换脚本（全库共用）。

用法:
    python prompts/tools/md2html.py              # 转换根目录下所有编号主题目录（NN-*）
    python prompts/tools/md2html.py path/to/file.md    # 转换单个文件
    python prompts/tools/md2html.py path/to/dir        # 转换目录下所有 .md

HTML 与源 md 写入同一目录（reports/ 下的 md 生成同名 .html），
使用 UTF-8 编码，支持表格、代码块、目录锚点。
"""
import argparse
import re
import sys
from pathlib import Path

import markdown


def slugify(value, separator):
    """保留中文、字母、数字的 slugify；空格与标点转为 separator。"""
    value = value.strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", separator, value, flags=re.UNICODE)
    value = re.sub(rf"{re.escape(separator)}+", separator, value)
    return value.strip(separator)


EXTENSIONS = ["tables", "fenced_code", "toc", "nl2br"]
EXTENSION_CONFIGS = {"toc": {"permalink": False, "slugify": slugify}}

BASE_CSS = """  body { max-width: 860px; margin: 2rem auto; padding: 0 1rem;
         font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
         line-height: 1.7; color: #222; }
  pre { background: #f5f5f5; padding: 0.8rem; overflow-x: auto; border-radius: 4px; }
  code { background: #f5f5f5; padding: 0.1em 0.3em; border-radius: 3px; }
  pre code { padding: 0; background: none; }
  table { border-collapse: collapse; }
  th, td { border: 1px solid #ccc; padding: 0.4em 0.7em; }
  table a[title^="来源"] { color: inherit; text-decoration: none;
    word-break: normal; overflow-wrap: anywhere;
    border-bottom: 1px dotted #b8b0a0; }
  table a[title^="来源"] strong, table a[title^="来源"] em,
  table a[title^="来源"] code { color: inherit; background: none; }
  table a[title^="来源"]:hover { color: #1a5f5a; background: rgba(26,95,90,.09);
    border-bottom: 1px solid currentColor; }
  table a[title^="来源"]::after { content: "↗"; margin-left: 3px;
    font-size: .76em; opacity: 0; }
  table a[title^="来源"]:hover::after { opacity: .85; }
  blockquote { border-left: 4px solid #ccc; margin-left: 0; padding-left: 1em; color: #555; }"""

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{base_css}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def convert(md_path: Path) -> Path:
    """转换单个 md 文件，HTML 写入同目录，返回生成的 HTML 路径。"""
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(
        text, extensions=EXTENSIONS, extension_configs=EXTENSION_CONFIGS
    )
    title = md_path.stem
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    html = TEMPLATE.format(title=title, body=body, base_css=BASE_CSS)

    # 与源文件同目录：08-visa-immigration/reports/a.md -> .../reports/a.html
    out_path = md_path.with_suffix(".html")
    out_path.write_text(html, encoding="utf-8")
    return out_path


def collect_md_files(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in inputs:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.is_file() and p.suffix.lower() == ".md":
            files.append(p)
        else:
            print(f"跳过（不存在或不是 .md）: {p}", file=sys.stderr)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="将 Markdown 转换为 HTML")
    parser.add_argument(
        "inputs", nargs="*",
        help="md 文件或目录；默认转换根目录下所有编号主题目录（NN-*）",
    )
    args = parser.parse_args()

    root = Path.cwd()
    inputs = [Path(p) for p in args.inputs] or sorted(
        p for p in root.iterdir() if p.is_dir() and re.match(r"^\d{2}-", p.name)
    )

    files = collect_md_files(inputs)
    if not files:
        print("未找到需要转换的 .md 文件", file=sys.stderr)
        return 1

    for md_path in files:
        out_path = convert(md_path)
        print(f"{md_path} -> {out_path}")

    print(f"完成，共转换 {len(files)} 个文件（HTML 与 md 同目录）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
