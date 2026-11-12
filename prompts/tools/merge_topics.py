# -*- coding: utf-8 -*-
"""将各编号主题（NN-*）下分散的多份章节 .md 合并为单份完整文档。

用法:
    python prompts/tools/merge_topics.py            # 生成合并文档（不删除旧文件）
    python prompts/tools/merge_topics.py --clean    # 生成后删除旧章节 md 及对应 html

合并规则：
    - 读取 reports/00-index.md 的「文件一览」表格，按编号顺序合并各章节。
    - 每个章节原有的 # 一级标题降级为 ##，## 降级为 ###，以此类推（代码块内不处理）。
    - 00-index.md 的内容作为「导航与使用约定」置于文档前部，其标题同样降级一级。
    - 输出文件：reports/日本{主题中文名}知识手册.md
"""
import argparse
import re
import sys
from pathlib import Path


def slugify(value: str, separator: str = "-") -> str:
    """与 md2html.py 一致的 slugify：保留中文，转小写，标点转 separator。"""
    value = value.strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", separator, value, flags=re.UNICODE)
    value = re.sub(rf"{re.escape(separator)}+", separator, value)
    return value.strip(separator)

# 主题目录名 -> 中文主题名
TOPIC_NAMES = {
    "05-industry-autonomous": "自动驾驶与自动化",
    "02-career-driver": "司机职业",
    "03-career-management": "管理岗过渡",
    "12-culture-life": "文化与生活",
    "07-economy-finance": "经济与财务",
    "10-education-qualification": "资格与教育投资",
    "11-language-japanese": "日语学习",
    "04-industry-logistics": "日本物流行业",
    "09-politics-law": "政治与法规",
    "13-regional-info": "地域信息",
    "06-industry-technology": "技术与数字化",
    "08-visa-immigration": "签证与在留资格",
}

# 已是单文档格式，跳过
SKIP = {"01-ssw-driver"}

MERGE_DATE = "2026-11-12"


def demote_headings(text: str) -> str:
    """将 markdown 标题整体降级一级（# -> ##），跳过代码块。"""
    lines = text.split("\n")
    in_code = False
    out = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if not in_code:
            m = re.match(r"^(#{1,5})(\s+)", line)
            if m:
                line = "#" + line
        out.append(line)
    return "\n".join(out)


def parse_index(index_md: Path):
    """解析 00-index.md 的「文件一览/阅读顺序」表格，返回 [(编号, 章节名, 相对路径)]。"""
    text = index_md.read_text(encoding="utf-8")
    lines = text.split("\n")
    # 定位「文件一览」或「阅读顺序」标题所在行
    start_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^#{1,4}\s*(文件一览|阅读顺序)", line):
            start_idx = i
            break
    if start_idx is None:
        return []
    # 从标题行向下，直到遇到下一个同级或更高级标题为止
    heading_level = len(re.match(r"^(#+)", lines[start_idx]).group(1))
    region_lines = []
    for line in lines[start_idx + 1:]:
        m = re.match(r"^(#+)", line)
        if m and len(m.group(1)) <= heading_level:
            break
        region_lines.append(line)
    region = "\n".join(region_lines)

    chapters = []
    pattern = re.compile(r"\|\s*(\d+)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|")
    for m in pattern.finditer(region):
        num, title, rel = m.group(1), m.group(2), m.group(3)
        chapters.append((num, title, rel))
    return chapters


def clean_index_links(index_text: str) -> str:
    """将 00-index.md 中指向本主题章节 .md 的链接改为纯文本，保留外部 URL 与跨主题引用。"""
    # 仅去掉以 .md 结尾的相对路径链接（本主题章节），保留 http(s) 链接
    text = re.sub(r"\[([^\]]+)\]\((?!https?://)[^)]*\.md\)", r"\1", index_text)
    return text


def fix_internal_links(text: str, anchor_map: dict) -> str:
    """将章节内容中指向本主题其他章节 .md 的相对链接替换为文档内锚点。"""
    def repl(m):
        label = m.group(1)
        target = m.group(2)
        stem = Path(target).stem
        anchor = anchor_map.get(stem)
        if anchor:
            return f"[{label}](#{anchor})"
        return m.group(0)  # 不在映射内则原样保留
    # 匹配非 http(s) 的 .md 链接
    return re.sub(r"\[([^\]]+)\]\((?!https?://)([^)]+\.md)\)", repl, text)


def build_global_map(topic_dirs: list) -> dict:
    """扫描所有主题，构建全局映射：主题名 -> {知识手册html文件名, {章节stem: 锚点}}。"""
    gmap = {}
    for d in topic_dirs:
        topic_name = d.name
        if topic_name in SKIP:
            continue
        cn_name = TOPIC_NAMES.get(topic_name)
        if not cn_name:
            continue
        index_path = d / "reports" / "00-index.md"
        if not index_path.exists():
            continue
        chapters = parse_index(index_path)
        if not chapters:
            continue
        prefix = "" if cn_name.startswith("日本") else "日本"
        handbook_html = f"{prefix}{cn_name}知识手册.html"
        anchors = {}
        for num, title, rel in chapters:
            stem = Path(rel).stem
            anchor = slugify(f"{num}-{title}")
            anchors[stem] = anchor
        gmap[topic_name] = {"handbook_html": handbook_html, "anchors": anchors}
    return gmap


def fix_cross_topic_links(text: str, current_topic: str, global_map: dict) -> str:
    """将指向其他主题章节 .md 的链接替换为对应主题知识手册 html 的锚点链接。"""
    def repl(m):
        label = m.group(1)
        target = m.group(2)
        # 从路径中提取编号主题名
        m_topic = re.search(r"(\d{2}-[\w-]+)", target)
        if not m_topic:
            return m.group(0)
        topic_name = m_topic.group(1)
        if topic_name == current_topic:
            return m.group(0)  # 本主题链接由 fix_internal_links 处理
        topic_info = global_map.get(topic_name)
        if not topic_info:
            return m.group(0)
        stem = Path(target).stem
        handbook = topic_info["handbook_html"]
        # 指向 00-index 的链接 -> 知识手册首页（无锚点）
        if stem == "00-index":
            return f"[{label}](../../{topic_name}/reports/{handbook})"
        anchor = topic_info["anchors"].get(stem)
        if not anchor:
            return m.group(0)
        # 从当前主题 reports/ 到目标主题 reports/ 的相对路径（需两级 .. 到项目根）
        return f"[{label}](../../{topic_name}/reports/{handbook}#{anchor})"
    # 匹配包含编号主题名的非 http(s) .md 链接
    return re.sub(r"\[([^\]]+)\]\((?!https?://)([^)]*\d{2}-[\w-]+[^)]*\.md)\)", repl, text)


def merge_topic(topic_dir: Path, clean: bool, global_map: dict) -> bool:
    topic_name = topic_dir.name
    if topic_name in SKIP:
        return False
    cn_name = TOPIC_NAMES.get(topic_name)
    if not cn_name:
        print(f"跳过（无中文名映射）: {topic_name}", file=sys.stderr)
        return False

    reports_dir = topic_dir / "reports"
    index_path = reports_dir / "00-index.md"
    if not index_path.exists():
        print(f"跳过（无 00-index.md）: {topic_name}", file=sys.stderr)
        return False

    chapters = parse_index(index_path)
    if not chapters:
        print(f"跳过（未解析到章节）: {topic_name}", file=sys.stderr)
        return False

    # 构建「章节文件名 stem -> 锚点」映射，用于修复跨章节链接
    # 锚点与 md2html.py 的 slugify 保持一致
    anchor_map = {}
    for num, title, rel in chapters:
        stem = Path(rel).stem
        anchor = slugify(f"{num}-{title}")
        anchor_map[stem] = anchor

    # 读取并降级 00-index 内容
    index_text = index_path.read_text(encoding="utf-8")
    index_text = clean_index_links(index_text)
    index_text = fix_cross_topic_links(index_text, topic_name, global_map)
    index_demoted = demote_headings(index_text)

    parts = []
    # 文档总标题与元信息
    parts.append(f"# 日本{cn_name}知识手册")
    parts.append("")
    parts.append(f"> **版本**：v1.0（合并整理版）　**整理日期**：{MERGE_DATE}")
    parts.append(f"> **说明**：本文档由原分散的多份章节文档合并整理而成，保留全部原内容与层级关系。后续更新请直接维护本单份文档。")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## 导航与使用约定")
    parts.append("")
    parts.append(index_demoted.strip())
    parts.append("")
    parts.append("---")
    parts.append("")

    # 按顺序合并各章节
    for num, title, rel in chapters:
        # 确定章节文件路径（相对 reports/）
        chap_path = (reports_dir / rel).resolve()
        if not chap_path.exists():
            print(f"  警告：章节文件不存在，跳过 {num} {title}: {chap_path}", file=sys.stderr)
            continue
        chap_text = chap_path.read_text(encoding="utf-8")
        # 去掉原章节首行的 # 标题（由统一的 ## 编号标题替代）
        chap_lines = chap_text.split("\n")
        if chap_lines and re.match(r"^#\s+\S", chap_lines[0]):
            chap_lines = chap_lines[1:]
            # 去掉紧随其后的空行
            while chap_lines and chap_lines[0].strip() == "":
                chap_lines = chap_lines[1:]
        chap_text = "\n".join(chap_lines)
        chap_demoted = demote_headings(chap_text)
        chap_demoted = fix_internal_links(chap_demoted, anchor_map)
        chap_demoted = fix_cross_topic_links(chap_demoted, topic_name, global_map)
        parts.append(f"## {num} {title}")
        parts.append("")
        parts.append(chap_demoted.strip())
        parts.append("")
        parts.append("---")
        parts.append("")

    merged = "\n".join(parts).rstrip() + "\n"
    prefix = "" if cn_name.startswith("日本") else "日本"
    out_name = f"{prefix}{cn_name}知识手册.md"
    out_path = reports_dir / out_name
    out_path.write_text(merged, encoding="utf-8")
    print(f"已生成: {out_path}（{len(chapters)} 个章节）")

    if clean:
        # 删除旧章节 md 及对应 html
        removed = []
        for num, title, rel in chapters:
            chap_path = (reports_dir / rel).resolve()
            if chap_path.exists():
                chap_path.unlink()
                removed.append(str(chap_path))
            html_path = chap_path.with_suffix(".html")
            if html_path.exists():
                html_path.unlink()
                removed.append(str(html_path))
        # 删除 00-index.md 及对应 html
        if index_path.exists():
            index_path.unlink()
            removed.append(str(index_path))
        index_html = index_path.with_suffix(".html")
        if index_html.exists():
            index_html.unlink()
            removed.append(str(index_html))
        for r in removed:
            print(f"  已删除: {r}")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="合并各主题分散章节为单份文档")
    parser.add_argument("--clean", action="store_true", help="合并后删除旧章节文件")
    parser.add_argument("topics", nargs="*", help="指定主题目录名；默认处理全部")
    args = parser.parse_args()

    root = Path.cwd()
    if args.topics:
        topic_dirs = [root / t for t in args.topics]
    else:
        topic_dirs = sorted(
            p for p in root.iterdir()
            if p.is_dir() and re.match(r"^\d{2}-", p.name)
        )

    global_map = build_global_map(topic_dirs)

    count = 0
    for d in topic_dirs:
        if merge_topic(d, args.clean, global_map):
            count += 1
    print(f"\n完成，共处理 {count} 个主题")
    return 0


if __name__ == "__main__":
    sys.exit(main())
