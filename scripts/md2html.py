# -*- coding: utf-8 -*-
"""Markdown 转 HTML 批量转换脚本。

用法:
    python scripts/md2html.py                    # 转换 docs/ 下所有 .md
    python scripts/md2html.py path/to/file.md    # 转换单个文件
    python scripts/md2html.py path/to/dir        # 转换目录下所有 .md
    python scripts/md2html.py -o out-dir ...     # 指定输出目录（默认 output/）

输出保持相对目录结构，HTML 使用 UTF-8 编码，支持表格、代码块、目录锚点。
"""
import argparse
import sys
from pathlib import Path

import markdown

EXTENSIONS = ["tables", "fenced_code", "toc", "nl2br"]
EXTENSION_CONFIGS = {"toc": {"permalink": False}}

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ max-width: 860px; margin: 2rem auto; padding: 0 1rem;
         font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
         line-height: 1.7; color: #222; }}
  pre {{ background: #f5f5f5; padding: 0.8rem; overflow-x: auto; border-radius: 4px; }}
  code {{ background: #f5f5f5; padding: 0.1em 0.3em; border-radius: 3px; }}
  pre code {{ padding: 0; background: none; }}
  table {{ border-collapse: collapse; }}
  th, td {{ border: 1px solid #ccc; padding: 0.4em 0.7em; }}
  blockquote {{ border-left: 4px solid #ccc; margin-left: 0; padding-left: 1em; color: #555; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def convert(md_path: Path, out_dir: Path, root: Path) -> Path:
    """转换单个 md 文件，返回生成的 HTML 路径。"""
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(
        text, extensions=EXTENSIONS, extension_configs=EXTENSION_CONFIGS
    )
    title = md_path.stem
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    html = TEMPLATE.format(title=title, body=body)

    # 保持相对目录结构：docs/01-visa-immigration/a.md -> output/docs/01-visa-immigration/a.html
    try:
        rel = md_path.resolve().relative_to(Path(root).resolve())
    except ValueError:
        rel = Path(md_path.name)
    out_path = out_dir / rel.with_suffix(".html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
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
        help="md 文件或目录；默认转换 docs/ 目录",
    )
    parser.add_argument("-o", "--out", default="output", help="输出目录（默认 output/）")
    args = parser.parse_args()

    root = Path.cwd()
    inputs = [Path(p) for p in args.inputs] or [root / "docs"]
    out_dir = Path(args.out)

    files = collect_md_files(inputs)
    if not files:
        print("未找到需要转换的 .md 文件", file=sys.stderr)
        return 1

    for md_path in files:
        out_path = convert(md_path, out_dir, root)
        print(f"{md_path} -> {out_path}")

    print(f"完成，共转换 {len(files)} 个文件，输出目录: {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
