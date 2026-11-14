"""结构与规范校验（validate.yml 的「结构与规范校验」步骤）。

退出码：0 = 通过；1 = 存在错误项；2 = 仅存在警告项。

校验项：
- 通用层根部必备文件齐全（report_templates/ 3 份共享文件）
- 类型模板目录齐全（report_templates/<类型ID>/，清单见 _common.TEMPLATE_TYPE_DIRS）
- 通用层（含全部类型子目录）无业务关键词（地区 / 业务类型 / 专属机构等）
- 业务线目录结构（prompts/business-config.md、reports/、data/）
- 业务配置含运行变量区
- 报告文件命名符合通用规范
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    BUSINESS_KEYWORDS,
    REQUIRED_TEMPLATE_FILES,
    TEMPLATE_ROOT,
    TEMPLATE_TYPE_DIRS,
    detect_month_report,
    iter_business_dirs,
    month_report_name,
    ROOT,
    topic_slug,
)

ERRORS: list[str] = []
WARNINGS: list[str] = []


def err(msg: str) -> None:
    ERRORS.append(msg)


def warn(msg: str) -> None:
    WARNINGS.append(msg)


def check_templates() -> None:
    tpl_dir = TEMPLATE_ROOT
    if not tpl_dir.is_dir():
        err("缺少通用模板目录 src/report_templates/")
        return
    for name in REQUIRED_TEMPLATE_FILES:
        if not (tpl_dir / name).exists():
            err(f"通用层缺少必备文件: report_templates/{name}")
    for type_id, files in TEMPLATE_TYPE_DIRS.items():
        type_dir = tpl_dir / type_id
        if not type_dir.is_dir():
            err(f"缺少类型模板目录: report_templates/{type_id}/")
            continue
        for name in files:
            if not (type_dir / name).exists():
                err(f"类型 {type_id} 缺少必备模板: report_templates/{type_id}/{name}")
    for md in tpl_dir.rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        for kw in BUSINESS_KEYWORDS:
            if kw in text:
                err(f"通用层出现业务关键词「{kw}」: {md.relative_to(ROOT)}")


def check_business_dirs() -> None:
    businesses = iter_business_dirs()
    if not businesses:
        warn("未识别到任何业务线目录（{地区}/{物业类型}）")
        return
    for b in businesses:
        config = b.path / "prompts" / "business-config.md"
        if not config.exists():
            warn(f"{b.rel}: 缺少业务配置 prompts/business-config.md")
        else:
            text = config.read_text(encoding="utf-8", errors="replace")
            for var in ("{{REGION}}", "{{TOPIC}}", "{{REGISTRY_PATH}}"):
                if var not in text:
                    warn(f"{b.rel}: business-config.md 缺少变量 {var}")
        for sub in ("reports", "data"):
            if not (b.path / sub).is_dir():
                warn(f"{b.rel}: 缺少 {sub}/ 目录（空目录不入 git，首次产出后自动补齐）")
        reports = b.path / "reports"
        if reports.is_dir():
            rs = topic_slug(b.region if not b.property_type else b.property_type)
            for f in sorted(reports.iterdir()):
                if not f.is_file() or f.suffix not in (".md", ".html"):
                    continue
                det = detect_month_report(f.name)
                if det is None:
                    warn(f"{b.rel}/reports/{f.name}: 文件名不符合月度报告命名约定（YYYY-MM-<主题slug>）")
                elif det[1] != rs:
                    warn(f"{b.rel}/reports/{f.name}: 主题 slug「{det[1]}」与目录「{rs}」不一致")
                elif f.suffix == ".html" and not (reports / month_report_name(det[0], rs, "md")).exists():
                    warn(f"{b.rel}/reports/{f.name}: 缺少对应 md 源稿")


def main() -> int:
    check_templates()
    check_business_dirs()
    for e in ERRORS:
        print(f"[ERROR] {e}")
    for w in WARNINGS:
        print(f"[WARN] {w}")
    if not ERRORS and not WARNINGS:
        print("结构与规范校验通过：通用层完整、业务线结构齐全、命名合规")
    if ERRORS:
        print(f"校验失败：{len(ERRORS)} 项错误，{len(WARNINGS)} 项警告")
        return 1
    if WARNINGS:
        print(f"校验存在 {len(WARNINGS)} 项警告（无错误）")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
