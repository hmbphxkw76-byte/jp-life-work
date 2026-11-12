# -*- coding: utf-8 -*-
"""项目规范一致性校验脚本。

校验项：
  1. 单文档约束：知识库主题 reports/ 下仅 1 份知识手册 md，无编号开头的零散 md
  2. 目录结构：编号主题目录（NN-*）统一为 data/ + prompts/ + reports/ + reports/archives/
  3. HTML 存在性：reports/ 下每个 md 须有同名 html
  4. 无 00-index 残留
  5. 表格来源规范：表格无独立"来源"列、无 [Source:…] 原文
  6. 引用覆盖：知识手册正文存在 [Source: URL, 年份] 行内引用
  7. 活值硬编码检测：prompt 模板内禁止写入具体活值（数字+单位）
  8. 跨主题链接锚点：指向其他主题知识手册 html 的锚点须存在
  9. 提示词变量：第 3 层提示词须含 {{HANDBOOK_PATH}}、{{REGISTRY_PATH}}、{{TOPIC_DIR}}
 10. 继承声明：第 3 层提示词头部须声明三层继承
 11. 聚合页面同步：主题总览与汇总阅读双向链接完整，生成页面与主题源文件同步

用法:
    python prompts/tools/validate.py              # 全量校验
    python prompts/tools/validate.py --quiet      # 仅输出违规项
    python prompts/tools/validate.py --check 1,3  # 只跑指定校验项编号

退出码: 0 = 全部通过；1 = 存在错误；2 = 存在警告（无错误）
"""
import argparse
import re
import sys
from pathlib import Path

import build_library

ROOT = Path(__file__).resolve().parents[2]

# 监测项目（多版本单文档，不适用"仅 1 份知识手册"约束）
MONITOR_PROJECT = "01-ssw-driver"

# 知识手册文件名特征
HANDBOOK_SUFFIX = "知识手册.md"

# 活值单位模式（用于检测 prompt 硬编码活值）
VALUE_UNITS = (
    r"円|万円|円/月|円/年|人|万人|名|社|個|件|歳|才|年|ヶ月|か月|月|日|"
    r"%|倍|km|kg|t|時間|分|秒|km/h|㎡|m²|万|億|千"
)

# 活值硬编码正则：数字（含千分位）+ 可选空格 + 单位
HARDCODED_VALUE_RE = re.compile(
    r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\s*(?:" + VALUE_UNITS + r")\b"
    r"|\b\d+(?:\.\d+)?\s*(?:" + VALUE_UNITS + r")\b"
)


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

def iter_topic_dirs():
    """遍历所有编号主题目录（NN-*）。"""
    for p in sorted(ROOT.iterdir()):
        if p.is_dir() and re.match(r"^\d{2}-", p.name):
            yield p


def is_knowledge_topic(topic_name: str) -> bool:
    """是否为知识库主题（非监测项目）。"""
    return topic_name != MONITOR_PROJECT


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_code_blocks(text: str) -> str:
    """移除代码块内容（避免误判代码内的数字为活值）。"""
    return re.sub(r"```[\s\S]*?```", "", text)


# ──────────────────────────────────────────────
# 校验项
# ──────────────────────────────────────────────

def check_single_doc(errors, warnings):
    """1. 单文档约束：知识库主题 reports/ 下仅 1 份知识手册 md，无零散编号 md。"""
    for topic in iter_topic_dirs():
        if not is_knowledge_topic(topic.name):
            continue
        reports = topic / "reports"
        if not reports.is_dir():
            errors.append(f"[{topic.name}] 缺少 reports/ 目录")
            continue
        mds = [f for f in reports.iterdir() if f.is_file() and f.suffix == ".md"]
        # 编号开头的零散 md（如 01-xxx.md）
        scattered = [f for f in mds if re.match(r"^\d{2}-", f.name)]
        if scattered:
            for f in scattered:
                errors.append(
                    f"[{topic.name}] 禁止零散章节 md: {f.name}（应合并为单份知识手册）"
                )
        # 知识手册数量
        handbooks = [f for f in mds if f.name.endswith(HANDBOOK_SUFFIX)]
        if len(handbooks) != 1:
            errors.append(
                f"[{topic.name}] 知识手册 md 数量应为 1，实际 {len(handbooks)}: "
                + ", ".join(f.name for f in handbooks)
            )


def check_dir_structure(errors, warnings):
    """2. 目录结构：data/ + prompts/ + reports/ + reports/archives/。"""
    for topic in iter_topic_dirs():
        required = ["data", "prompts", "reports"]
        for sub in required:
            if not (topic / sub).is_dir():
                errors.append(f"[{topic.name}] 缺少目录: {sub}/")
        archives = topic / "reports" / "archives"
        if not archives.is_dir():
            errors.append(f"[{topic.name}] 缺少目录: reports/archives/")
        # 监测项目允许有 reviews/，其他主题不应有
        if topic.name != MONITOR_PROJECT and (topic / "reviews").is_dir():
            warnings.append(f"[{topic.name}] 存在 reviews/ 目录（仅监测项目保留）")


def check_html_exists(errors, warnings):
    """3. HTML 存在性：reports/ 下每个 md 须有同名 html。"""
    for topic in iter_topic_dirs():
        reports = topic / "reports"
        if not reports.is_dir():
            continue
        for md in reports.glob("*.md"):
            html = md.with_suffix(".html")
            if not html.exists():
                errors.append(f"[{topic.name}] 缺少同名 HTML: {md.name}")
        # archives 同理
        archives = reports / "archives"
        if archives.is_dir():
            for md in archives.glob("*.md"):
                html = md.with_suffix(".html")
                if not html.exists():
                    warnings.append(f"[{topic.name}/archives] 缺少同名 HTML: {md.name}")


def check_no_00index(errors, warnings):
    """4. 无 00-index 残留。"""
    for topic in iter_topic_dirs():
        for idx in topic.rglob("00-index.md"):
            errors.append(f"[{topic.name}] 残留 00-index.md（应并入知识手册导航区）: {idx.relative_to(ROOT)}")
        for idx in topic.rglob("00-index.html"):
            errors.append(f"[{topic.name}] 残留 00-index.html: {idx.relative_to(ROOT)}")


def check_table_sources(errors, warnings):
    """5. 表格来源规范：无独立"来源"列、无 [Source:…] 原文。"""
    for topic in iter_topic_dirs():
        reports = topic / "reports"
        if not reports.is_dir():
            continue
        for md in reports.glob("*.md"):
            text = read_text(md)
            lines = text.split("\n")
            in_table = False
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("|") and stripped.endswith("|"):
                    cells = [c.strip() for c in stripped.strip("|").split("|")]
                    if in_table:
                        # 检查是否有"来源"列
                        for cell in cells:
                            if cell == "来源" or cell == "数据来源":
                                errors.append(
                                    f"[{topic.name}/{md.name}:{i}] 表格禁止独立「来源」列"
                                )
                        # 检查单元格内是否有 [Source:…]
                        for cell in cells:
                            if "[Source:" in cell:
                                errors.append(
                                    f"[{topic.name}/{md.name}:{i}] 表格内禁止 [Source:…] 原文"
                                )
                    in_table = True
                elif in_table and not stripped.startswith("|"):
                    in_table = False


def check_source_citations(errors, warnings):
    """6. 引用覆盖：知识手册正文应存在 [Source: URL, 年份] 行内引用。"""
    for topic in iter_topic_dirs():
        if not is_knowledge_topic(topic.name):
            continue
        reports = topic / "reports"
        if not reports.is_dir():
            continue
        for md in reports.glob("*" + HANDBOOK_SUFFIX):
            text = read_text(md)
            # 去掉代码块和表格，只看正文段落
            body = strip_code_blocks(text)
            body = re.sub(r"^\|.*\|$", "", body, flags=re.MULTILINE)
            citations = re.findall(r"\[Source:\s*https?://[^\],]+,\s*\d{4}\]", body)
            if not citations:
                warnings.append(
                    f"[{topic.name}/{md.name}] 未检测到 [Source: URL, 年份] 行内引用"
                )


def check_no_hardcoded_values(errors, warnings):
    """7. 活值硬编码检测：prompt 模板内禁止写入具体活值（数字+单位）。"""
    for topic in iter_topic_dirs():
        prompt_dir = topic / "prompts"
        if not prompt_dir.is_dir():
            continue
        for pf in prompt_dir.glob("*.md"):
            text = read_text(pf)
            # 去掉代码块
            text = strip_code_blocks(text)
            # 去掉 {{ }} 变量行
            text = re.sub(r"\{\{[^}]+\}\}", "", text)
            # 去掉 [Source: URL, 年份]
            text = re.sub(r"\[Source:[^\]]+\]", "", text)
            # 去掉 URL
            text = re.sub(r"https?://\S+", "", text)
            # 去掉版本号 vYYYY.MM.DD
            text = re.sub(r"v\d{4}\.\d{2}\.\d{2}(?:_\d+)?", "", text)
            # 去掉日期 YYYY-MM-DD
            text = re.sub(r"\d{4}-\d{2}-\d{2}", "", text)
            # 去掉表格表头分隔行 |---|---|
            text = re.sub(r"^\|[-:\s|]+\|$", "", text, flags=re.MULTILINE)
            # 逐行检查（排除纯数字行、章节标题行）
            for i, line in enumerate(text.split("\n"), 1):
                stripped = line.strip()
                if not stripped:
                    continue
                # 跳过标题行
                if stripped.startswith("#"):
                    continue
                # 跳过表格分隔行
                if re.match(r"^\|[-:\s|]+\|$", stripped):
                    continue
                # 跳过纯引用标记行（如 [x]、☐）
                if re.match(r"^[-*]\s*\[?[ x☐]?\]?\s*$", stripped):
                    continue
                # 跳过明确的制度常数声明（非追踪活值）
                if re.search(r"制度常数|非追踪活值|制度性常数", stripped):
                    continue
                # 含"当前有效值/当前值"的行必须检测：仅取该标记之后的片段，
                # 避免把同一行中"旧值 24,500 → 当前 22,100"的旧值误报为活值
                current = re.search(r"当前有效|当前值|现行值", stripped)
                if current:
                    checkable = stripped[current.start():]
                elif re.search(r"旧值|旧费用|旧数据", stripped) and re.search(
                    r"不得|禁止|严禁|不可|不再|勿|❌", stripped
                ):
                    # 被显式否定的历史值，非当前活值
                    continue
                elif re.search(r"(上限|通算|制度|规则|要件|资格|号别|分野|回数)", stripped):
                    continue
                else:
                    checkable = stripped
                # 检测数字+单位
                for m in HARDCODED_VALUE_RE.finditer(checkable):
                    warnings.append(
                        f"[{topic.name}/{pf.name}:{i}] 疑似活值硬编码: \"{m.group()}\""
                        f"（活值应存于 {topic.name}/data/*-indicator-registry.md）"
                    )


def check_internal_anchor_links(errors, warnings):
    """8b. 内部锚点链接：知识手册内 #锚点 链接须存在对应标题 id。"""
    for topic in iter_topic_dirs():
        reports = topic / "reports"
        if not reports.is_dir():
            continue
        for md in reports.glob("*.md"):
            html_path = md.with_suffix(".html")
            if not html_path.exists():
                continue
            html_text = read_text(html_path)
            ids = set(re.findall(r'<h[1-6]\s+id="([^"]+)"', html_text))
            md_text = read_text(md)
            # 匹配内部锚点链接 ](#锚点) （非 http、非 ../）
            for m in re.finditer(r"\]\(#[^)]+\)", md_text):
                anchor = m.group(0)[3:-1]  # 去掉 ](# 和 )
                if anchor not in ids:
                    errors.append(
                        f"[{topic.name}/{md.name}] 内部锚点不存在: #{anchor}"
                    )


def check_cross_topic_links(errors, warnings):
    """8. 跨主题链接锚点：指向其他主题知识手册 html 的锚点须存在。"""
    # 收集所有知识手册 html 中的锚点 id
    anchors_by_html: dict[str, set[str]] = {}
    for topic in iter_topic_dirs():
        reports = topic / "reports"
        if not reports.is_dir():
            continue
        for html in reports.glob("*.html"):
            text = read_text(html)
            ids = set(re.findall(r'<h[1-6]\s+id="([^"]+)"', text))
            anchors_by_html[str(html.relative_to(ROOT)).replace("\\", "/")] = ids

    import os.path
    # 检查知识手册 md 中的跨主题链接
    link_re = re.compile(r"\]\((\.\./[^)]+\.html)#([^)]+)\)")
    for topic in iter_topic_dirs():
        reports = topic / "reports"
        if not reports.is_dir():
            continue
        for md in reports.glob("*.md"):
            text = read_text(md)
            for m in link_re.finditer(text):
                href = m.group(1)
                anchor = m.group(2)
                # 解析目标 html 的相对路径（从 reports/ 出发），用 normpath 规范化
                target_html = Path(os.path.normpath(str(reports / href)))
                try:
                    target_rel = str(target_html.relative_to(ROOT)).replace("\\", "/")
                except ValueError:
                    errors.append(
                        f"[{topic.name}/{md.name}] 跨主题链接目标越界: {href}"
                    )
                    continue
                if target_rel not in anchors_by_html:
                    errors.append(
                        f"[{topic.name}/{md.name}] 跨主题链接目标不存在: {href}"
                    )
                    continue
                if anchor not in anchors_by_html[target_rel]:
                    errors.append(
                        f"[{topic.name}/{md.name}] 跨主题链接锚点不存在: "
                        f"{href}#{anchor}"
                    )


def check_prompt_variables(errors, warnings):
    """9. 提示词变量：知识库主题提示词须含必要变量（监测项目除外）。"""
    required = ["{{HANDBOOK_PATH}}", "{{REGISTRY_PATH}}", "{{TOPIC_DIR}}"]
    for topic in iter_topic_dirs():
        if not is_knowledge_topic(topic.name):
            continue  # 监测项目使用报告类变量，不检查 HANDBOOK_PATH/TOPIC_DIR
        prompt_dir = topic / "prompts"
        if not prompt_dir.is_dir():
            continue
        for pf in prompt_dir.glob("*.md"):
            text = read_text(pf)
            for var in required:
                if var not in text:
                    errors.append(
                        f"[{topic.name}/{pf.name}] 缺少必要变量: {var}"
                    )


def check_inheritance_declaration(errors, warnings):
    """10. 继承声明：第 3 层提示词头部须声明三层继承。"""
    for topic in iter_topic_dirs():
        prompt_dir = topic / "prompts"
        if not prompt_dir.is_dir():
            continue
        for pf in prompt_dir.glob("*.md"):
            text = read_text(pf)
            head = text[:2000]  # 只看文件头部
            if "通用基座" not in head or "类型模板" not in head:
                errors.append(
                    f"[{topic.name}/{pf.name}] 头部缺少三层继承声明（须含「通用基座」与「类型模板」）"
                )


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def check_anchor_links(errors, warnings):
    """8. 锚点链接校验：内部 #锚点 与跨主题 html#锚点 均须存在。"""
    check_internal_anchor_links(errors, warnings)
    check_cross_topic_links(errors, warnings)


def check_library_pages(errors, warnings):
    """11. 聚合页面同步：双向链接完整，生成结果与主题源文件一致。"""
    try:
        topics = build_library.load_topics()
        pages = build_library.build_pages()
    except build_library.BuildError as exc:
        errors.append(f"[聚合页面] 构建失败: {exc}")
        return

    contents = {}
    for relative in pages:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"[聚合页面] 缺少生成页面: {relative.as_posix()}")
            continue
        contents[relative] = read_text(path)

    if len(contents) == len(pages):
        index = contents[Path("index.html")]
        library = contents[Path("library.html")]
        for topic in topics:
            anchor = build_library.topic_anchor(topic["id"])
            if f'id="{anchor}"' not in index:
                errors.append(f"[index.html] 缺少主题卡片锚点: #{anchor}")
            if f'href="library.html#{anchor}"' not in index:
                errors.append(
                    f"[index.html] 缺少主题汇总链接: library.html#{anchor}"
                )
            if f'id="{anchor}"' not in library:
                errors.append(f"[library.html] 缺少主题正文锚点: #{anchor}")
            if f'href="index.html#{anchor}"' not in library:
                errors.append(
                    f"[library.html] 缺少主题返回链接: index.html#{anchor}"
                )

    for relative in build_library.compare_outputs(pages, root=ROOT):
        if (ROOT / relative).is_file():
            errors.append(
                f"[{relative.as_posix()}] 聚合页面与主题源文件不同步，"
                "请运行 python prompts/tools/build_library.py"
            )


CHECKS = [
    (1, "单文档约束", check_single_doc),
    (2, "目录结构", check_dir_structure),
    (3, "HTML 存在性", check_html_exists),
    (4, "无 00-index 残留", check_no_00index),
    (5, "表格来源规范", check_table_sources),
    (6, "引用覆盖", check_source_citations),
    (7, "活值硬编码检测", check_no_hardcoded_values),
    (8, "锚点链接校验", check_anchor_links),
    (9, "提示词变量", check_prompt_variables),
    (10, "继承声明", check_inheritance_declaration),
    (11, "聚合页面同步", check_library_pages),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="项目规范一致性校验")
    parser.add_argument(
        "--check", default="",
        help="只跑指定校验项编号（逗号分隔，如 1,3,5）；默认全部",
    )
    parser.add_argument("--quiet", action="store_true", help="仅输出违规项")
    args = parser.parse_args()

    selected = set()
    if args.check:
        selected = set(int(x) for x in args.check.split(",") if x.strip().isdigit())

    all_errors: list[str] = []
    all_warnings: list[str] = []

    for num, name, fn in CHECKS:
        if selected and num not in selected:
            continue
        errors: list[str] = []
        warnings: list[str] = []
        fn(errors, warnings)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        if not args.quiet:
            status = "PASS" if not errors and not warnings else (
                "FAIL" if errors else "WARN"
            )
            print(f"[{num:>2}] {name}: {status}")
        for e in errors:
            print(f"  ✗ {e}")
        for w in warnings:
            print(f"  ⚠ {w}")

    print()
    print(f"错误: {len(all_errors)}  警告: {len(all_warnings)}")
    if all_errors:
        return 1
    if all_warnings:
        return 2
    print("全部通过 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
