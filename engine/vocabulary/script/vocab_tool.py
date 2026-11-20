#!/usr/bin/env python3
"""vocab_tool.py — 标准化动态词汇库管理工具（主题无关核心）。

设计原则：
- 主题与实现解耦：全部主题参数读自 config/topics.json，新增任意领域词汇零代码修改。
- 单一事实源：每个主题一个 md-table 词库文件（data/<topic>/terms.md），由本脚本统一读写，
  词汇表禁止手工编辑；别名/标签分隔符为半角分号「;」。
- 退出码（对齐 engine/tools 工具链约定）：0=通过；1=错误（阻断）；2=警告（有产出但有瑕疵）。

用法示例：
  python engine/vocabulary/script/vocab_tool.py topics
  python engine/vocabulary/script/vocab_tool.py init --topic 01-ssw-driver
  python engine/vocabulary/script/vocab_tool.py import --topic 01-ssw-driver --file engine/vocabulary/data/01-ssw-driver/imports/2026-11-13_seed-01-ssw-driver.md
  python engine/vocabulary/script/vocab_tool.py check --topic 01-ssw-driver
  python engine/vocabulary/script/vocab_tool.py tag --topic 01-ssw-driver --id SSW-001 --add 运输 --remove 资格
  python engine/vocabulary/script/vocab_tool.py export --topic 01-ssw-driver --format all
  python engine/vocabulary/script/vocab_tool.py index
  python engine/vocabulary/script/vocab_tool.py verify
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent.parent  # vocabulary/
DEFAULT_CONFIG = TOOL_ROOT / "config" / "topics.json"

STORAGE_HEADER = ["ID", "词条", "别名", "分类", "标签", "定义", "来源", "首次登记", "最近更新",
                  "核验状态", "来源URL", "置信度"]
DEFAULT_VERIFICATION = "待核实"
DEFAULT_CONFIDENCE = "待评"
VERIFICATION_VALUES = ("已核验", "部分核验", "待核实")
CONFIDENCE_VALUES = ("S", "A", "B", "C", "待评")
VERSION_HEADER = ["版本", "日期", "变更", "说明"]

IMPORT_KEYS = ("id", "term", "aliases", "category", "tags", "definition", "source",
                "verification", "source_url", "confidence")
HEADER_MAP = {
    "id": "id", "ID": "id", "编号": "id",
    "词条": "term", "术语": "term", "term": "term",
    "别名": "aliases", "同义词": "aliases", "alias": "aliases", "aliases": "aliases",
    "分类": "category", "类别": "category", "category": "category",
    "标签": "tags", "tags": "tags",
    "定义": "definition", "释义": "definition", "description": "definition", "definition": "definition",
    "来源": "source", "出处": "source", "source": "source",
    "核验状态": "verification", "verification": "verification",
    "来源url": "source_url", "source_url": "source_url", "来源URL": "source_url",
    "置信度": "confidence", "confidence": "confidence",
}

SEP_RE = re.compile(r"^:?-{3,}:?$")


# ---------- 基础工具 ----------

def today() -> str:
    return date.today().isoformat()


def norm(value) -> str:
    """归一化：NFKC + 全角分号折半 + 空白折叠 + 忽略大小写（仅用于去重键）。"""
    if value is None:
        return ""
    s = unicodedata.normalize("NFKC", str(value))
    s = s.replace("；", ";").replace("，", ",")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def split_list(value) -> list:
    """按分号（半/全角）拆分为去重后的列表。"""
    if not value:
        return []
    out, seen = [], set()
    for p in re.split(r"[;；]", str(value)):
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def cell(value) -> str:
    """表格单元格消毒：竖线转全角斜杠、换行折叠为空格。"""
    s = "" if value is None else str(value)
    return s.replace("|", "／").replace("\r", " ").replace("\n", " ").strip()


def rel(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(TOOL_ROOT).as_posix()
    except ValueError:
        return str(path)


# ---------- md 表格解析与渲染 ----------

def get_section(text: str, title: str) -> list:
    """取 '## <title>' 小节下的全部行。"""
    lines, capture = [], False
    for line in text.splitlines():
        if line.strip().startswith("## "):
            capture = line.strip()[3:].strip() == title
            continue
        if capture:
            lines.append(line)
    return lines


def parse_table(lines: list) -> list:
    """解析 md 表格为二维数组，自动剔除分隔行。"""
    rows: list[list[str]] = []
    for raw in lines:
        s = raw.strip()
        if not s.startswith("|"):
            if rows:
                break
            continue
        body = s[1:]
        if body.endswith("|"):
            body = body[:-1]
        cells = [c.strip() for c in body.split("|")]
        if cells and all(SEP_RE.match(c) for c in cells):
            continue
        rows.append(cells)
    return rows


def load_storage(path: Path):
    """读取词库 → (terms, versions)。terms 字段：id/term/aliases/category/tags/definition/source/first_added/last_updated。"""
    text = path.read_text(encoding="utf-8")
    terms, versions = [], []
    trows = parse_table(get_section(text, "词汇表"))
    vrows = parse_table(get_section(text, "版本记录"))
    for r in trows[1:]:
        r = list(r) + [""] * (len(STORAGE_HEADER) - len(r))
        terms.append({
            "id": r[0], "term": r[1], "aliases": split_list(r[2]),
            "category": r[3], "tags": split_list(r[4]),
            "definition": r[5], "source": r[6],
            "first_added": r[7], "last_updated": r[8],
            "verification": r[9] or DEFAULT_VERIFICATION,
            "source_url": r[10] or "",
            "confidence": r[11] or DEFAULT_CONFIDENCE,
        })
    for r in vrows[1:]:
        r = list(r) + [""] * (len(VERSION_HEADER) - len(r))
        versions.append(r[:4])
    return terms, versions


def render_terms_md(tmeta: dict, terms: list, versions: list) -> str:
    L = [f"# {tmeta.get('name', tmeta['id'])}词汇库（{tmeta['id']}）", ""]
    L.append("> **定位**：vocabulary 子系统主题词库，由 `script/vocab_tool.py` 统一管理；词汇表请勿手工编辑，"
             "变更一律走 `import` / `tag` 命令。")
    L.append(f"> **主题配置**：`config/topics.json` → `{tmeta['id']}`（{tmeta.get('description', '')}）")
    L.append("> **去重规范**：词条与别名经归一化（NFKC + 空白折叠 + 忽略大小写）后全局唯一；别名/标签分隔符为半角 `;`。")
    L.append("")
    L.append("## 词汇表")
    L.append("")
    L.append("| " + " | ".join(STORAGE_HEADER) + " |")
    L.append("| " + " | ".join(["---"] * len(STORAGE_HEADER)) + " |")
    for t in terms:
        row = [t["id"], t["term"], ";".join(t["aliases"]), t["category"], ";".join(t["tags"]),
               t["definition"], t["source"], t["first_added"], t["last_updated"],
               t.get("verification", DEFAULT_VERIFICATION), t.get("source_url", ""),
               t.get("confidence", DEFAULT_CONFIDENCE)]
        L.append("| " + " | ".join(cell(x) for x in row) + " |")
    L += ["", "## 版本记录", ""]
    L.append("| " + " | ".join(VERSION_HEADER) + " |")
    L.append("| " + " | ".join(["---"] * len(VERSION_HEADER)) + " |")
    for v in versions:
        L.append("| " + " | ".join(cell(x) for x in v) + " |")
    L.append("")
    return "\n".join(L)


def next_version(versions: list) -> str:
    if not versions:
        return "v1.0"
    m = re.match(r"v(\d+)\.(\d+)", str(versions[-1][0]))
    return f"v{m.group(1)}.{int(m.group(2)) + 1}" if m else "v1.1"


# ---------- 配置 ----------

def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在：{path}")
    cfg = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(cfg.get("topics"), dict):
        raise ValueError("配置文件缺少 topics 对象")
    return cfg


def resolve_topic(cfg: dict, topic: str) -> dict:
    topics = cfg["topics"]
    if topic not in topics:
        raise KeyError(f"主题 '{topic}' 未在配置中注册；可用主题：{', '.join(topics)}")
    t = dict(topics[topic])
    t["id"] = topic
    for key in ("storage", "imports_dir", "exports_dir"):
        if key not in t:
            raise ValueError(f"主题 '{topic}' 配置缺少 {key}")
        t[key] = (TOOL_ROOT / t[key]) if not Path(t[key]).is_absolute() else Path(t[key])
    if not t.get("id_prefix"):
        raise ValueError(f"主题 '{topic}' 配置缺少 id_prefix")
    return t


def resolve_import_file(file_arg: str) -> Path:
    p = Path(file_arg)
    if not p.exists():
        alt = TOOL_ROOT / p  # 允许相对 vocabulary/ 根目录书写
        if alt.exists():
            return alt
    return p


def load_verify_exemptions() -> list:
    """读取 config/verify-exemptions.json（显式豁免清单）。

    文件缺失 / 损坏 / 结构不符时视为无豁免（不阻断校验），保证测试与最小部署可用。
    """
    path = TOOL_ROOT / "config" / "verify-exemptions.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return []
    items = data.get("exemptions") if isinstance(data, dict) else None
    return items if isinstance(items, list) else []


def is_exempt(topic_id: str, check_name: str) -> bool:
    """该主题的该类检查是否已列入显式豁免清单（check / verify 共用）。"""
    return any(
        isinstance(e, dict) and e.get("topic") == topic_id and e.get("check") == check_name
        for e in load_verify_exemptions()
    )


# ---------- 去重索引 ----------

def build_uniq(terms: list) -> dict:
    """词条 + 全部别名 → 归一化唯一索引（norm -> id）。"""
    idx: dict[str, str] = {}
    for t in terms:
        for v in [t["term"]] + list(t["aliases"]):
            k = norm(v)
            if k:
                idx.setdefault(k, t["id"])
    return idx


def next_serial(terms: list, prefix: str) -> int:
    pat = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    nums = [int(m.group(1)) for t in terms for m in [pat.match(t["id"])] if m]
    return (max(nums) + 1) if nums else 1


# ---------- 导入文件解析 ----------

def read_import_file(path: Path) -> list:
    """支持 .md（表格）/ .csv / .json 三种格式 → 规范化条目列表。"""
    suffix = path.suffix.lower()
    raw_rows = []
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            raw_rows = [{k: v for k, v in row.items() if k} for row in csv.DictReader(f)]
    elif suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            data = data.get("terms", [])
        if not isinstance(data, list):
            raise ValueError('JSON 导入文件须为词条对象数组或 {"terms": [...]}')
        raw_rows = data
    elif suffix in (".md", ".markdown"):
        rows = parse_table(path.read_text(encoding="utf-8-sig").splitlines())
        if not rows:
            raise ValueError("md 导入文件中未找到表格")
        keys = [HEADER_MAP.get(norm(h), norm(h)) for h in rows[0]]
        for r in rows[1:]:
            r = list(r) + [""] * (len(keys) - len(r))
            raw_rows.append(dict(zip(keys, r, strict=False)))
    else:
        raise ValueError(f"不支持的导入格式：{suffix}（支持 .md / .csv / .json）")

    entries = []
    for i, row in enumerate(raw_rows, 2):
        mapped: dict[str, object] = {"_line": i}
        for k, v in row.items():
            ck = HEADER_MAP.get(norm(k), norm(k))
            if ck in IMPORT_KEYS:
                mapped[ck] = "" if v is None else str(v).strip()
        entries.append(mapped)
    return entries


# ---------- 子命令 ----------

def auto_sync_hook(topic_id: str):
    """词汇库变更后自动触发提示词同步（config/sync.json 存在且 auto_trigger 时生效）。"""
    sync_cfg = TOOL_ROOT / "config" / "sync.json"
    if not sync_cfg.exists():
        return
    try:
        import subprocess
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "sync_vocab.py"),
             "--config", str(sync_cfg), "sync", "--topic", topic_id],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env, timeout=120)
        out = (r.stdout or "").strip()
        if out:
            print(out)
        if r.returncode != 0:
            print(f"  [warn] 自动同步未成功（exit {r.returncode}），可手动重试："
                  f"python engine/vocabulary/script/sync_vocab.py sync --topic {topic_id}")
    except Exception as exc:  # 钩子失败不阻断词汇库主流程
        print(f"  [warn] 自动同步钩子异常：{exc}；可手动重试 sync_vocab.py sync --topic {topic_id}")


def cmd_topics(cfg: dict) -> int:
    print(f"配置：{rel(Path(cfg.get('_path', DEFAULT_CONFIG)))}（{cfg.get('version', '?')}）")
    for tid, t in cfg["topics"].items():
        print(f"  {tid}  名称={t.get('name', tid)}  ID前缀={t.get('id_prefix')}  词库={t.get('storage')}")
    print(f"共 {len(cfg['topics'])} 个主题。新增主题：topic-add --topic <id> --name <名称>（自动创建目录，勿手工编辑注册表）。")
    return 0


def cmd_init(tmeta: dict) -> int:
    for d in (tmeta["imports_dir"], tmeta["exports_dir"], tmeta["storage"].parent):
        d.mkdir(parents=True, exist_ok=True)
    if tmeta["storage"].exists():
        print(f"[init] 词库已存在，跳过：{rel(tmeta['storage'])}")
    else:
        versions = [["v1.0", today(), "首建词库", "init 命令创建空词库骨架"]]
        tmeta["storage"].write_text(render_terms_md(tmeta, [], versions), encoding="utf-8")
        print(f"[init] 创建词库骨架：{rel(tmeta['storage'])}")
    print(f"[init] 主题 '{tmeta['id']}' 初始化完成（imports/ exports/ 就绪）。"
          f"下一步：import --topic {tmeta['id']} --file <导入文件>")
    return 0


def cmd_import(tmeta: dict, file_arg: str) -> int:
    storage = tmeta["storage"]
    if not storage.exists():
        print(f"[error] 词库不存在：{rel(storage)}；先运行 init --topic {tmeta['id']}")
        return 1
    file_path = resolve_import_file(file_arg)
    if not file_path.exists():
        print(f"[error] 导入文件不存在：{file_path}")
        return 1

    terms, versions = load_storage(storage)
    existing = build_uniq(terms)
    allow = tmeta.get("categories") or None
    entries = read_import_file(file_path)

    added = skipped = invalid = 0
    warns = []
    today_s = today()
    for e in entries:
        line = e.get("_line", "?")
        term = e.get("term", "")
        category = e.get("category", "")
        definition = e.get("definition", "")
        source = e.get("source", "")
        aliases = split_list(e.get("aliases", ""))
        tags = split_list(e.get("tags", ""))
        if not term or not category:
            invalid += 1
            warns.append(f"第 {line} 行：词条或分类为空，已忽略")
            continue
        if not definition:
            invalid += 1
            warns.append(f"第 {line} 行：定义缺失，已忽略")
            continue
        if not source:
            source = "需核实原文"
            warns.append(f"第 {line} 行：来源为空，自动标注「需核实原文」")
        if allow and category not in allow:
            warns.append(f"第 {line} 行：分类「{category}」不在受控词表，仍按原值收录（建议核对 config/categories）")
        keys = [norm(term)] + [norm(a) for a in aliases]
        conflict = next((existing[k] for k in keys if k and k in existing), None)
        if conflict:
            skipped += 1
            warns.append(f"「{term}」与已有条目 {conflict} 重复，已跳过")
            continue
        new_term = {
            "id": f"{tmeta['id_prefix']}-{next_serial(terms, tmeta['id_prefix']):03d}",
            "term": term, "aliases": aliases, "category": category,
            "tags": tags, "definition": definition, "source": source,
            "first_added": today_s, "last_updated": today_s,
            "verification": e.get("verification") or DEFAULT_VERIFICATION,
            "source_url": e.get("source_url", ""),
            "confidence": e.get("confidence") or DEFAULT_CONFIDENCE,
        }
        terms.append(new_term)
        for k in keys:
            if k:
                existing[k] = new_term["id"]
        added += 1

    if added:
        versions.append([next_version(versions), today_s, "批量导入",
                         f"新增 {added} 条 / 跳过重复 {skipped} 条 / 无效 {invalid} 条；文件 {file_path.name}"])
        storage.write_text(render_terms_md(tmeta, terms, versions), encoding="utf-8")
    print(f"[import] 读取 {len(entries)} 行 → 新增 {added} / 跳过重复 {skipped} / 无效 {invalid}；"
          f"词库共 {len(terms)} 条" + (f"（{rel(storage)} 已更新至 {versions[-1][0]}）" if added else "（未写盘）"))
    for w in warns[:10]:
        print(f"  [warn] {w}")
    if len(warns) > 10:
        print(f"  [warn] 其余 {len(warns) - 10} 条警告省略")
    if added:
        auto_sync_hook(tmeta["id"])
    return 2 if (skipped or invalid or warns) else 0


def check_topic(tmeta: dict) -> tuple[list, list]:
    """单主题结构校验：存在性 / 重复 / 空值 / 分类 / ID 前缀 / 条目数下限 / 序号连续性。

    返回 (errors, warns)；退出码语义由调用方映射（1=错误 / 2=警告 / 0=通过）。
    """
    storage = tmeta["storage"]
    if not storage.exists():
        return [f"词库不存在：{rel(storage)}"], []
    terms, _versions = load_storage(storage)
    allow = tmeta.get("categories") or None
    prefix = tmeta.get("id_prefix", "")
    min_terms = int(tmeta.get("min_terms", 1) or 1)
    errors, warns = [], []
    if len(terms) < min_terms:
        errors.append(f"词条数 {len(terms)} 低于下限 {min_terms}")
    seen: dict[str, tuple[str, str]] = {}
    ids: set[str] = set()
    for t in terms:
        if t["id"] in ids:
            errors.append(f"ID 重复：{t['id']}")
        ids.add(t["id"])
        if not t["term"] or not t["category"]:
            errors.append(f"{t['id']}: 词条或分类为空")
        if not t["definition"]:
            warns.append(f"{t['id']}: 定义为空")
        if allow and t["category"] not in allow:
            warns.append(f"{t['id']}: 分类「{t['category']}」不在受控词表")
        for kind, v in [("词条", t["term"])] + [("别名", a) for a in t["aliases"]]:
            k = norm(v)
            if not k:
                continue
            if k in seen:
                if seen[k][0] == t["id"]:
                    warns.append(f"{t['id']}: {kind}「{v}」与自身词条/别名重复（冗余，建议清理）")
                else:
                    errors.append(f"重复：{t['id']} 的{kind}「{v}」与 {seen[k][0]}({seen[k][1]}) 冲突")
            else:
                seen[k] = (t["id"], kind)
    pat = re.compile(rf"^{re.escape(prefix)}-(\d+)$") if prefix else None
    if pat:
        bad = [t["id"] for t in terms if not pat.match(t["id"])]
        if bad:
            errors.append(f"ID 前缀不符 {len(bad)} 条（须为 {prefix}-<数字>，如 {'、'.join(bad[:3])}）")
        nums = sorted(int(m.group(1)) for t in terms for m in [pat.match(t["id"])] if m)
        gap = bool(nums) and nums != list(range(1, len(nums) + 1))
        if gap and not is_exempt(tmeta.get("id", ""), "id_sequence_gap"):
            warns.append(f"ID 序号不连续（{nums[0]}..{nums[-1]}）；如系人工删除条目所致属正常，建议保留连续性")
    return errors, warns


def cmd_check(tmeta: dict) -> int:
    storage = tmeta["storage"]
    terms, versions = load_storage(storage) if storage.exists() else ([], [])
    errors, warns = check_topic(tmeta)
    print(f"[check] {rel(storage)}：共 {len(terms)} 条，版本 {versions[-1][0] if versions else '—'}")
    for e in errors:
        print(f"  [error] {e}")
    for w in warns[:10]:
        print(f"  [warn] {w}")
    if len(warns) > 10:
        print(f"  [warn] 其余 {len(warns) - 10} 条警告省略")
    if errors:
        print(f"[check] 结论：不通过（{len(errors)} 项错误 / {len(warns)} 项警告）")
        return 1
    print(f"[check] 结论：通过（0 项错误 / {len(warns)} 项警告）")
    return 2 if warns else 0


def cmd_verify(cfg: dict, args) -> int:
    """全主题词库校验：逐主题复用 check_topic（重复 / 空值 / 分类 / ID 前缀 / 条目数下限）。"""
    errors, warns = [], []
    for tid in cfg["topics"]:
        tmeta = resolve_topic(cfg, tid)
        e, w = check_topic(tmeta)
        errors += [f"{tid}: {x}" for x in e]
        warns += [f"{tid}: {x}" for x in w]
    print(f"[verify] 注册主题 {len(cfg['topics'])} 个：{len(errors)} 项错误 / {len(warns)} 项警告")
    for err in errors:
        print(f"  [error] {err}")
    for warn in warns[:20]:
        print(f"  [warn] {warn}")
    if len(warns) > 20:
        print(f"  [warn] 其余 {len(warns) - 20} 条警告省略")
    return 1 if errors else (2 if warns else 0)


def cmd_tag(tmeta: dict, term_id: str, add: str, remove: str) -> int:
    storage = tmeta["storage"]
    if not storage.exists():
        print(f"[error] 词库不存在：{rel(storage)}")
        return 1
    terms, versions = load_storage(storage)
    target = next((t for t in terms if t["id"].lower() == term_id.lower()), None)
    if not target:
        print(f"[error] 未找到词条 ID：{term_id}")
        return 1
    add_list, remove_list = split_list(add), split_list(remove)
    before = list(target["tags"])
    tags = [x for x in before if x not in remove_list]
    for a in add_list:
        if a not in tags:
            tags.append(a)
    if tags == before:
        print(f"[tag] {target['id']}「{target['term']}」标签无变化，未写盘")
        return 0
    target["tags"] = tags
    target["last_updated"] = today()
    detail = f"{target['id']}：增 {','.join(add_list) or '—'} / 删 {','.join(remove_list) or '—'}"
    versions.append([next_version(versions), today(), "标签调整", detail])
    storage.write_text(render_terms_md(tmeta, terms, versions), encoding="utf-8")
    print(f"[tag] {target['id']}「{target['term']}」标签 → {';'.join(tags) or '（空）'}；词库更新至 {versions[-1][0]}")
    auto_sync_hook(tmeta["id"])
    return 0


def cmd_alias(tmeta: dict, term_id: str, add: str, remove: str) -> int:
    """调整既有词条别名（增 / 删），保持词库由工具统一读写。"""
    storage = tmeta["storage"]
    if not storage.exists():
        print(f"[error] 词库不存在：{rel(storage)}")
        return 1
    terms, versions = load_storage(storage)
    target = next((t for t in terms if t["id"].lower() == term_id.lower()), None)
    if not target:
        print(f"[error] 未找到词条 ID：{term_id}")
        return 1
    add_list, remove_list = split_list(add), split_list(remove)
    before = list(target["aliases"])
    aliases = [x for x in before if x not in remove_list]
    for a in add_list:
        if a not in aliases:
            aliases.append(a)
    if aliases == before:
        print(f"[alias] {target['id']}「{target['term']}」别名无变化，未写盘")
        return 0
    target["aliases"] = aliases
    target["last_updated"] = today()
    detail = f"{target['id']}：增 {','.join(add_list) or '—'} / 删 {','.join(remove_list) or '—'}"
    versions.append([next_version(versions), today(), "别名调整", detail])
    storage.write_text(render_terms_md(tmeta, terms, versions), encoding="utf-8")
    print(f"[alias] {target['id']}「{target['term']}」别名 → {';'.join(aliases) or '（空）'}；词库更新至 {versions[-1][0]}")
    auto_sync_hook(tmeta["id"])
    return 0


def cmd_remove(tmeta: dict, term_ids: str) -> int:
    """按 ID 删除词条（可复用命令，避免手改词库）。

    term_ids 为逗号分隔的 ID 列表；未找到的 ID 记入版本行但不阻断已删除项。
    """
    storage = tmeta["storage"]
    if not storage.exists():
        print(f"[error] 词库不存在：{rel(storage)}")
        return 1
    ids = [x.strip() for x in str(term_ids).split(",") if x.strip()]
    if not ids:
        print("[error] 未指定任何词条 ID")
        return 1
    terms, versions = load_storage(storage)
    before = len(terms)
    idset = {i.lower() for i in ids}
    kept = [t for t in terms if t["id"].lower() not in idset]
    removed = [t for t in terms if t["id"].lower() in idset]
    found = {t["id"].lower() for t in removed}
    missing = [i for i in ids if i.lower() not in found]
    if not removed:
        print(f"[remove] 未找到任何指定词条：{','.join(ids)}")
        return 1
    detail = f"删除 {len(removed)} 条：{','.join(t['id'] for t in removed)}"
    if missing:
        detail += f"；未找到 {','.join(missing)}"
    versions.append([next_version(versions), today(), "词条删除", detail])
    storage.write_text(render_terms_md(tmeta, kept, versions), encoding="utf-8")
    print(f"[remove] 删除 {len(removed)} 条（{before}→{len(kept)}）；词库更新至 {versions[-1][0]}")
    auto_sync_hook(tmeta["id"])
    return 0


def cmd_verify_update(tmeta: dict, file_arg: str) -> int:
    """回填既有词条的核验字段（核验状态 / 来源URL / 置信度）。

    导入文件须含 ID（或词条）列，以及核验状态 / 来源URL / 置信度 中至少一列；
    按 ID 优先、词条归一化为辅匹配。仅更新提供且合法的值，未提供列保持不变。
    """
    storage = tmeta["storage"]
    if not storage.exists():
        print(f"[error] 词库不存在：{rel(storage)}")
        return 1
    terms, versions = load_storage(storage)
    by_id = {t["id"].lower(): t for t in terms}
    by_term = {norm(t["term"]): t for t in terms}
    entries = read_import_file(Path(file_arg))
    updated = missing = invalid = 0
    for e in entries:
        key = str(e.get("id", "")).strip()
        term_key = norm(str(e.get("term", "")))
        target = by_id.get(key.lower()) if key else by_term.get(term_key)
        if not target:
            missing += 1
            print(f"  [warn] 未匹配词条：id={key or '—'} term={e.get('term', '') or '—'}")
            continue
        changed = False
        ver = str(e.get("verification", "")).strip()
        if ver:
            if ver not in VERIFICATION_VALUES:
                invalid += 1
                print(f"  [warn] {target['id']} 核验状态非法：{ver!r}")
            elif ver != target.get("verification"):
                target["verification"] = ver
                changed = True
        conf = str(e.get("confidence", "")).strip().upper()
        if conf:
            if conf not in CONFIDENCE_VALUES:
                invalid += 1
                print(f"  [warn] {target['id']} 置信度非法：{conf!r}")
            elif conf != target.get("confidence"):
                target["confidence"] = conf
                changed = True
        url = str(e.get("source_url", "")).strip()
        if url and url != target.get("source_url"):
            target["source_url"] = url
            changed = True
        if changed:
            target["last_updated"] = today()
            updated += 1
    if updated:
        versions.append([next_version(versions), today(), "核验回填",
                         f"更新 {updated} 条核验字段；文件 {Path(file_arg).name}"])
        storage.write_text(render_terms_md(tmeta, terms, versions), encoding="utf-8")
        auto_sync_hook(tmeta["id"])
    print(f"[verify-update] 读取 {len(entries)} 行 → 更新 {updated} / 未匹配 {missing} / 非法 {invalid}；"
          f"词库共 {len(terms)} 条" + (f"（已更新至 {versions[-1][0]}）" if updated else "（未写盘）"))
    return 2 if (missing or invalid) else 0


def cmd_export(tmeta: dict, fmt: str, out: str) -> int:
    storage = tmeta["storage"]
    if not storage.exists():
        print(f"[error] 词库不存在：{rel(storage)}")
        return 1
    terms, versions = load_storage(storage)
    if not terms:
        print(f"[warn] 词库为空，导出空产物：{rel(storage)}")
    fmts = {"json", "csv", "jsonl"}
    if fmt == "all":
        selected = ["json", "csv", "jsonl"]
    elif fmt in fmts:
        selected = [fmt]
    else:
        print(f"[error] 不支持的导出格式：{fmt}（支持 json / csv / jsonl / all）")
        return 1
    version = versions[-1][0] if versions else "v1.0"
    exports_dir = tmeta["exports_dir"]
    exports_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for t in terms:
        counts[t["category"]] = counts.get(t["category"], 0) + 1

    for f in selected:
        if out and len(selected) == 1:
            target = Path(out)
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            target = exports_dir / f"{tmeta['id']}_{today()}_export.{f}"
        if f == "json":
            payload = {
                "topic": tmeta["id"], "name": tmeta.get("name", tmeta["id"]),
                "version": version, "generated_at": datetime.now().isoformat(timespec="seconds"),
                "count": len(terms), "categories": counts,
                "terms": [{**t, "aliases": t["aliases"], "tags": t["tags"]} for t in terms],
            }
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        elif f == "jsonl":
            lines = [json.dumps(t, ensure_ascii=False) for t in terms]
            target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        else:
            rows = [STORAGE_HEADER] + [
                [t["id"], t["term"], ";".join(t["aliases"]), t["category"], ";".join(t["tags"]),
                 t["definition"], t["source"], t["first_added"], t["last_updated"],
                 t.get("verification", DEFAULT_VERIFICATION), t.get("source_url", ""),
                 t.get("confidence", DEFAULT_CONFIDENCE)] for t in terms]
            with target.open("w", encoding="utf-8-sig", newline="") as fh:
                csv.writer(fh).writerows(rows)
        print(f"[export] {rel(target)}（{len(terms)} 条，{version}）")
    return 0


def cmd_index(cfg: dict) -> int:
    rows, total = [], 0
    for tid in cfg["topics"]:
        tmeta = resolve_topic(cfg, tid)
        if tmeta["storage"].exists():
            terms, versions = load_storage(tmeta["storage"])
        else:
            terms, versions = [], []
        counts: dict[str, int] = {}
        for t in terms:
            counts[t["category"]] = counts.get(t["category"], 0) + 1
        dist = " / ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
        last = max((t["last_updated"] for t in terms), default="—")
        rows.append((tid, tmeta.get("name", tid), tmeta["id_prefix"], len(terms), dist or "—",
                     versions[-1][0] if versions else "—", rel(tmeta["storage"]), last))
        total += len(terms)

    L = ["# 词汇库索引（vocabulary）", ""]
    L.append(f"> 由 `script/vocab_tool.py index` 自动生成，请勿手工编辑。生成时间：{datetime.now().isoformat(timespec='seconds')}")
    L.append("")
    L.append("## 主题总览")
    L.append("")
    L.append("| 主题 | 名称 | ID 前缀 | 词条数 | 分类分布 | 词库版本 | 存储路径 | 最近更新 |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        L.append("| " + " | ".join(cell(x) for x in r) + " |")
    L.append("")
    L.append(f"合计：{len(rows)} 个主题，{total} 条词条。")
    L.append("")
    L.append("## 上层对接")
    L.append("")
    L.append("- 结构化导出：各主题 `data/<topic>/exports/` 下的 JSON / JSONL / CSV（数据契约见 README 第六节）。")
    L.append("- 检索建议：以词条 ID 为主键，别名与标签作为索引字段，分类作为过滤面。")
    L.append("")
    index_path = TOOL_ROOT / "INDEX.md"
    index_path.write_text("\n".join(L), encoding="utf-8")
    print(f"[index] {rel(index_path)} 已生成（{len(rows)} 个主题 / {total} 条词条）")
    return 0


# ---------- 主题管理（topic-add / topic-remove / topic-check）----------

TOPIC_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def plog_ops(msg: str):
    """主题管理操作日志（追溯用），落 data/topic-ops.log。"""
    p = TOOL_ROOT / "data" / "topic-ops.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="") as f:
        f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}\n")


def backup_topics_file(cfg_path: Path) -> Path:
    bdir = TOOL_ROOT / "data" / "topic-backups"
    bdir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = bdir / f"topics.{ts}.json"
    shutil.copyfile(cfg_path, dst)
    olds = sorted(bdir.glob("topics.*.json"))
    for p in olds[:-5]:
        with contextlib.suppress(OSError):
            p.unlink()
    return dst


def bump_registry_version(cfg: dict):
    v = str(cfg.get("version", "v1.0"))
    m = re.match(r"v(\d+)\.(\d+)", v)
    cfg["version"] = f"v{m.group(1)}.{int(m.group(2)) + 1}" if m else "v1.1"
    cfg["updated"] = today()


def derive_prefix(existing: set, tid: str) -> str:
    parts = [p for p in tid.split("-") if p]
    cand = parts[0][:4].upper() if len(parts) == 1 else "".join(p[0] for p in parts).upper()[:4]
    cand = cand or "T"
    if cand not in existing and re.match(r"^[A-Z]{2,4}$", cand):
        return cand
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        c2 = (cand[:3] + ch) if len(cand) >= 4 else (cand + ch)
        if re.match(r"^[A-Z]{2,4}$", c2) and c2 not in existing:
            return c2
    raise ValueError("无法自动派生可用 ID 前缀，请用 --prefix 手动指定")


def make_skeleton(tmeta: dict) -> list:
    """创建主题目录与词库骨架（幂等），返回本次新建路径。"""
    created = []
    for d in (tmeta["imports_dir"], tmeta["exports_dir"], tmeta["storage"].parent):
        if not d.exists():
            d.mkdir(parents=True)
            created.append(str(d))
    if not tmeta["storage"].exists():
        versions = [["v1.0", today(), "首建词库", "topic-add/init 创建空词库骨架"]]
        tmeta["storage"].write_text(render_terms_md(tmeta, [], versions), encoding="utf-8")
        created.append(str(tmeta["storage"]))
    return created


def cmd_topic_add(cfg: dict, args) -> int:
    cfg_path = Path(cfg["_path"])
    tid = args.topic
    if not TOPIC_ID_RE.match(tid):
        print(f"[error] 主题 ID 须为小写 kebab-case（字母/数字/连字符）：{tid}")
        return 1
    topics = cfg["topics"]
    if tid in topics:
        print(f"[error] 主题 '{tid}' 已注册（避免重复条目）。如需重建目录结构，运行 init --topic {tid}。")
        return 1
    prefixes = {t.get("id_prefix", "") for t in topics.values()}
    try:
        prefix = (args.prefix or "").strip().upper() or derive_prefix(prefixes, tid)
    except ValueError as exc:
        print(f"[error] {exc}")
        return 1
    if not re.match(r"^[A-Z]{2,4}$", prefix):
        print(f"[error] ID 前缀须为 2–4 位大写字母：{prefix}")
        return 1
    if prefix in prefixes:
        print(f"[error] ID 前缀冲突：{prefix} 已被占用（避免无效节点）。请用 --prefix 指定其他前缀。")
        return 1
    categories = split_list(args.categories)
    entry = {
        "name": args.name or tid,
        "description": args.description or "",
        "id_prefix": prefix,
        "storage": f"data/{tid}/terms.md",
        "imports_dir": f"data/{tid}/imports",
        "exports_dir": f"data/{tid}/exports",
        "categories": categories,
    }
    data_dir = TOOL_ROOT / "data" / tid
    dir_existed = data_dir.exists()
    backup = backup_topics_file(cfg_path)
    try:
        topics[tid] = entry
        bump_registry_version(cfg)
        out = {k: v for k, v in cfg.items() if k != "_path"}
        tmp = cfg_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, cfg_path)
        tmeta = resolve_topic(cfg, tid)
        created = make_skeleton(tmeta)
        cmd_index(cfg)
        plog_ops(f"[topic-add] topic={tid} prefix={prefix} "
                 f"categories={'/'.join(categories) or '—'} dir_existed={dir_existed} "
                 f"created={';'.join(created) or '—'} backup={backup.name} result=OK")
        print(f"[topic-add] 主题 '{tid}' 注册并初始化完成（注册表 {cfg['version']}）：")
        print(f"  词库目录：data/{tid}/terms.md（{'已存在，直接纳管，未覆盖既有内容' if dir_existed else '新建'}）")
        print(f"  索引：INDEX.md 已重建；操作日志：data/topic-ops.log；注册表备份：{backup.name}")
        if not categories:
            print("  [warn] 未提供受控分类词表（--categories）；导入词条时分类不受限，建议后续补充。")
        if dir_existed:
            print("  [warn] 检测到同名数据目录已存在，已按孤儿目录纳管。")
        print(f"  下一步：python engine/vocabulary/script/vocab_tool.py import --topic {tid} --file <导入文件>")
        return 0
    except Exception as exc:
        shutil.copyfile(backup, cfg_path)
        if not dir_existed and data_dir.exists():
            shutil.rmtree(data_dir, ignore_errors=True)
        plog_ops(f"[topic-add] topic={tid} result=FAILED rollback={exc}")
        print(f"[error] 主题注册失败，已回滚注册表与本次新建目录（现有目录结构未受影响）：{exc}")
        print(f"[error] 注册表备份：{backup}；可修复后重试 topic-add")
        return 1


def cmd_topic_remove(cfg: dict, args) -> int:
    cfg_path = Path(cfg["_path"])
    tid = args.topic
    if tid not in cfg["topics"]:
        print(f"[error] 主题 '{tid}' 未注册。")
        return 1
    storage = TOOL_ROOT / cfg["topics"][tid].get("storage", f"data/{tid}/terms.md")
    count = 0
    if storage.exists():
        terms, _ = load_storage(storage)
        count = len(terms)
    if count and not args.force:
        print(f"[error] 词库含 {count} 条词条；确认移除注册请加 --force（词库数据默认保留，不删除）。")
        return 1
    bind_warn = False
    sync_cfg = TOOL_ROOT / "config" / "sync.json"
    if sync_cfg.exists():
        try:
            sc = json.loads(sync_cfg.read_text(encoding="utf-8-sig"))
            bind_warn = any(b.get("topic") == tid for b in sc.get("bindings", []))
        except Exception:
            pass
    backup = backup_topics_file(cfg_path)
    try:
        del cfg["topics"][tid]
        bump_registry_version(cfg)
        out = {k: v for k, v in cfg.items() if k != "_path"}
        tmp = cfg_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, cfg_path)
        if args.delete_data:
            shutil.rmtree(TOOL_ROOT / "data" / tid, ignore_errors=True)
        cmd_index(cfg)
        plog_ops(f"[topic-remove] topic={tid} terms={count} delete_data={bool(args.delete_data)} "
                 f"backup={backup.name} result=OK")
        print(f"[topic-remove] 主题 '{tid}' 已移出注册表（注册表 {cfg['version']}，索引已重建）；"
              f"词库数据{'已删除' if args.delete_data else '保留于 data/' + tid + '/'}。")
        if bind_warn:
            print("  [warn] sync.json 仍存在该主题的同步绑定，请同步移除该 binding，否则 sync 会报「未注册」错误。")
        return 0
    except Exception as exc:
        shutil.copyfile(backup, cfg_path)
        plog_ops(f"[topic-remove] topic={tid} result=FAILED rollback={exc}")
        print(f"[error] 移除失败，已回滚注册表（现有目录结构未受影响）：{exc}")
        return 1


def cmd_topic_check(cfg: dict, args) -> int:
    errors, warns = [], []
    prefixes: dict[str, str] = {}
    for tid, t in cfg["topics"].items():
        p = t.get("id_prefix", "")
        if not p:
            errors.append(f"{tid}: 缺少 id_prefix")
        elif p in prefixes:
            errors.append(f"{tid}: ID 前缀 {p} 与 {prefixes[p]} 冲突")
        else:
            prefixes[p] = tid
        storage = TOOL_ROOT / t.get("storage", f"data/{tid}/terms.md")
        if not storage.parent.exists():
            errors.append(f"{tid}: 数据目录缺失；运行 init --topic {tid} 修复")
        elif not storage.exists():
            warns.append(f"{tid}: 词库文件缺失；运行 init --topic {tid} 修复")
        if not t.get("categories"):
            warns.append(f"{tid}: 未配置受控分类词表（categories），导入时分类不受限")
    data_root = TOOL_ROOT / "data"
    reserved = {"sync-backups", "topic-backups"}
    if data_root.exists():
        for d in sorted(data_root.iterdir()):
            if d.is_dir() and d.name not in reserved and d.name not in cfg["topics"]:
                warns.append(f"孤儿数据目录：data/{d.name}/ 未在注册表登记（确认无用可手动删除，或用 topic-add 纳管）")
    print(f"[topic-check] 注册主题 {len(cfg['topics'])} 个：{len(errors)} 项错误 / {len(warns)} 项警告")
    for e in errors:
        print(f"  [error] {e}")
    for w in warns:
        print(f"  [warn] {w}")
    plog_ops(f"[topic-check] topics={len(cfg['topics'])} errors={len(errors)} warnings={len(warns)} result="
             + ("FAIL" if errors else "WARN" if warns else "OK"))
    return 1 if errors else (2 if warns else 0)


# ---------- 跨主题概念对齐（n23） ----------

def cross_check_gaps(cfg: dict) -> tuple[list, list, dict]:
    """跨主题同概念对齐检测（纯函数，n23）。

    返回 (errors, warnings, summary)：
    - errors：`concept_map` 引用不存在的词条；
    - warnings：同定义异名未登记 / 同名词条未登记（供人工登记）。
    """
    terms_by_topic: dict[str, list] = {}
    for tid in cfg["topics"]:
        tmeta = resolve_topic(cfg, tid)
        try:
            terms, _ = load_storage(tmeta["storage"])
        except (FileNotFoundError, ValueError):
            terms = []
        terms_by_topic[tid] = terms

    index: dict[str, list] = {}
    by_def: dict[str, list] = {}
    for tid, terms in terms_by_topic.items():
        for t in terms:
            index.setdefault(norm(t["term"]), []).append((tid, t["id"], t["term"]))
            d = norm(t["definition"])
            if d:
                by_def.setdefault(d, []).append((tid, t["id"], t["term"]))

    concept_map = cfg.get("concept_map") or {}
    registered = {(it.get("topic"), it.get("id"))
                  for entry in concept_map.values() for it in entry.get("terms", [])}

    errors = []
    for cid in sorted(concept_map):
        for it in concept_map[cid].get("terms", []):
            tid, tid_id = it.get("topic"), it.get("id")
            if tid not in terms_by_topic or not any(t["id"] == tid_id for t in terms_by_topic[tid]):
                errors.append(f"{cid} 引用不存在的词条：{tid}:{tid_id}")

    warns = []
    for _d, items in by_def.items():
        if len({x[0] for x in items}) < 2 or len({norm(x[2]) for x in items}) <= 1:
            continue
        if all((x[0], x[1]) in registered for x in items):
            continue
        warns.append("同定义异名未登记：" + " / ".join(f"{x[0]}:{x[1]}({x[2]})" for x in items))

    unregistered_same = 0
    for _k, items in index.items():
        if len({x[0] for x in items}) < 2:
            continue
        if all((x[0], x[1]) in registered for x in items):
            continue
        unregistered_same += 1
        if len(warns) < 20:
            warns.append("同名词条未登记：" + " / ".join(f"{x[0]}:{x[1]}" for x in items))

    summary = {
        "concepts": len(concept_map),
        "registered_terms": len(registered),
        "same_term_groups": sum(1 for v in index.values() if len({x[0] for x in v}) >= 2),
        "unregistered_same_term_groups": unregistered_same,
    }
    return errors, warns, summary


def cmd_cross_check(cfg: dict, args) -> int:
    """跨主题同概念对齐校验（n23，命令入口）。"""
    errors, warns, summary = cross_check_gaps(cfg)
    if getattr(args, "json", False):
        print(json.dumps({"errors": errors, "warnings": warns, **summary},
                         ensure_ascii=False, indent=2))
    else:
        print(f"[cross-check] 概念 {summary['concepts']} 条（登记词条 {summary['registered_terms']}）；"
              f"同名词条组 {summary['same_term_groups']}，未登记 {summary['unregistered_same_term_groups']}；"
              f"错误 {len(errors)} / 警告 {len(warns)}")
        for e in errors:
            print(f"  [error] {e}")
        for w in warns[:20]:
            print(f"  [warn] {w}")
    plog_ops(f"[cross-check] concepts={summary['concepts']} errors={len(errors)} warnings={len(warns)}")
    return 1 if errors else (2 if warns else 0)


# ---------- 词表变更审计指纹（n26） ----------

def vocab_hash(cfg: dict) -> tuple[str, int, int]:
    """全库词表内容指纹（n26）：词汇表小节按主题排序拼接后 SHA-256。

    仅取「词汇表」小节（版本记录为变更留痕，不计入内容指纹）；不含 mtime，确定性。
    返回 ``(hash_hex, topics, terms)``。
    """
    import hashlib
    h = hashlib.sha256()
    n = 0
    topics = 0
    for tid in sorted(cfg["topics"]):
        tmeta = resolve_topic(cfg, tid)
        try:
            text = tmeta["storage"].read_text(encoding="utf-8")
        except (FileNotFoundError, ValueError):
            continue
        topics += 1
        rows = parse_table(get_section(text, "词汇表"))[1:]
        h.update(f"{tid}\n".encode())
        for r in rows:
            h.update(("|".join(r) + "\n").encode())
        n += len(rows)
    return h.hexdigest(), topics, n


def cmd_vocab_hash(cfg: dict, args) -> int:
    """词表指纹命令（n26）：打印 / ``--check`` 对基线 / ``--write`` 刷新基线。"""
    digest, topics, terms = vocab_hash(cfg)
    base_path = TOOL_ROOT / "config" / "vocab-fingerprint.json"
    if getattr(args, "write", False):
        base_path.parent.mkdir(parents=True, exist_ok=True)
        base_path.write_text(json.dumps(
            {"vocab_hash": digest, "topics": topics, "terms": terms, "updated": today()},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[vocab-hash] 基线已写入：{rel(base_path)}（{digest[:12]}…，{topics} 主题 / {terms} 词条）")
        return 0
    if getattr(args, "check", False):
        if not base_path.exists():
            print(f"[vocab-hash] 基线缺失：{rel(base_path)}（运行 vocab-hash --write）")
            return 1
        base = json.loads(base_path.read_text(encoding="utf-8-sig")).get("vocab_hash")
        if base == digest:
            print(f"[vocab-hash] 匹配（{digest[:12]}…，{topics} 主题 / {terms} 词条）")
            return 0
        print(f"[vocab-hash] 失配：当前 {digest[:12]}… ≠ 基线 {str(base)[:12]}…"
              "（词库已变更：请 sync_vocab 同步提示词并刷新基线）")
        return 2
    print(json.dumps({"vocab_hash": digest, "topics": topics, "terms": terms}, ensure_ascii=False))
    return 0


# ---------- 入口 ----------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="标准化动态词汇库管理工具（主题无关核心，参数读自 config/topics.json）")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG), help="主题注册表路径（默认 engine/vocabulary/config/topics.json）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("topics", help="列出已注册主题")
    p = sub.add_parser("init", help="创建主题目录与词库骨架")
    p.add_argument("--topic", required=True)
    p = sub.add_parser("import", help="批量导入词条（增量，自动去重跳过）")
    p.add_argument("--topic", required=True)
    p.add_argument("--file", required=True, help="导入文件（.md 表格 / .csv / .json）")
    p = sub.add_parser("check", help="全库去重与结构校验")
    p.add_argument("--topic", required=True)
    p = sub.add_parser("tag", help="调整词条自定义标签")
    p.add_argument("--topic", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--add", default="", help="追加标签，分号分隔")
    p.add_argument("--remove", default="", help="移除标签，分号分隔")
    p = sub.add_parser("alias", help="调整既有词条别名")
    p.add_argument("--topic", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--add", default="", help="追加别名，分号分隔")
    p.add_argument("--remove", default="", help="移除别名，分号分隔")
    p = sub.add_parser("remove", help="按 ID 删除词条（逗号分隔）")
    p.add_argument("--topic", required=True)
    p.add_argument("--id", required=True, help="待删除词条 ID，逗号分隔")
    p = sub.add_parser("verify-update", help="回填既有词条核验字段（核验状态 / 来源URL / 置信度）")
    p.add_argument("--topic", required=True)
    p.add_argument("--file", required=True, help="回填文件（.md 表格 / .csv / .json，含 ID 或词条列）")
    p = sub.add_parser("export", help="一键导出结构化数据")
    p.add_argument("--topic", required=True)
    p.add_argument("--format", default="all", choices=["json", "csv", "jsonl", "all"])
    p.add_argument("--out", default="", help="自定义输出路径（仅单格式时生效）")
    sub.add_parser("index", help="生成全主题索引 INDEX.md")
    p = sub.add_parser("topic-add", help="注册新主题并自动创建目录结构（备份回滚 + 操作日志）")
    p.add_argument("--topic", required=True, help="主题 ID（小写 kebab-case）")
    p.add_argument("--name", default="", help="主题显示名（缺省用 topic ID）")
    p.add_argument("--prefix", default="", help="ID 前缀（2–4 位大写字母，缺省自动派生并查重）")
    p.add_argument("--categories", default="", help="受控分类词表，分号分隔")
    p.add_argument("--description", default="", help="主题描述")
    p = sub.add_parser("topic-remove", help="移除主题注册（词库数据默认保留）")
    p.add_argument("--topic", required=True)
    p.add_argument("--force", action="store_true", help="词库非空时确认移除注册")
    p.add_argument("--delete-data", action="store_true", help="同时删除 data/<topic>/ 数据目录")
    sub.add_parser("topic-check", help="主题注册表与目录结构一致性审计")
    p = sub.add_parser("cross-check", help="跨主题同概念对齐校验（n23）")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("vocab-hash", help="词表内容指纹（n26）：打印 / --check / --write")
    p.add_argument("--check", action="store_true", help="与基线 config/vocab-fingerprint.json 比对")
    p.add_argument("--write", action="store_true", help="刷新基线")
    sub.add_parser("verify", help="全主题词库校验（重复 / 空值 / 分类 / ID 前缀 / 条目数下限）")

    args = ap.parse_args(argv)
    try:
        cfg = load_config(Path(args.config))
        cfg["_path"] = args.config
        if args.cmd == "topics":
            return cmd_topics(cfg)
        if args.cmd == "index":
            return cmd_index(cfg)
        if args.cmd == "topic-add":
            return cmd_topic_add(cfg, args)
        if args.cmd == "topic-remove":
            return cmd_topic_remove(cfg, args)
        if args.cmd == "topic-check":
            return cmd_topic_check(cfg, args)
        if args.cmd == "cross-check":
            return cmd_cross_check(cfg, args)
        if args.cmd == "vocab-hash":
            return cmd_vocab_hash(cfg, args)
        if args.cmd == "verify":
            return cmd_verify(cfg, args)
        tmeta = resolve_topic(cfg, args.topic)
        if args.cmd == "init":
            return cmd_init(tmeta)
        if args.cmd == "import":
            return cmd_import(tmeta, args.file)
        if args.cmd == "check":
            return cmd_check(tmeta)
        if args.cmd == "tag":
            return cmd_tag(tmeta, args.id, args.add, args.remove)
        if args.cmd == "alias":
            return cmd_alias(tmeta, args.id, args.add, args.remove)
        if args.cmd == "remove":
            return cmd_remove(tmeta, args.id)
        if args.cmd == "verify-update":
            return cmd_verify_update(tmeta, args.file)
        if args.cmd == "export":
            return cmd_export(tmeta, args.format, args.out)
    except (KeyError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[error] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
