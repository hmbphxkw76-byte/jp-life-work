"""信息质量全量评估与闭环修复（InfoQuality-Guard 的程序化实现）。

对应 `docs/信息质量评估提示词体系.md` 的可执行子集：
- 阶段 0 扫描建档：iter_business_dirs() 遍历全部主题目录；
- 阶段 1 四维度评估：完整性 / 逻辑一致性 / 信息准确性 / 内容关联性，全部量化；
- 阶段 2 混乱识别分类：C-01~C-14（其中 C-11 / C-12 为语义类，不在程序化判定内；其余需语义判断，见报告说明）；
- 阶段 3 自动修复：S-02 去重 / S-05 缺失补全（占位）/ S-08 引用修复；
- 阶段 4 修复验证：修复后复评 + 回归校验；仍未达标的 P0/P1 回到阶段 3 返工，
  最多 MAX_REWORK_ROUNDS 轮（提示词体系模块六「流程纪律」第 4 条）；
- 阶段 5 报告交付：评估台账 / 修复台账 / 验证报告 + 机器可读 JSON。

退出码约定（与仓库既有工具一致）：
- 0 = 通过（无 P0/P1 遗留）
- 1 = 存在 P0/P1 遗留（需人工介入或下轮修复）
- 2 = 仅存在 P2 遗留（放行）

用法：
    python engine/tools/info_quality_check.py           # 全量评估（只报告）
    python engine/tools/info_quality_check.py --apply   # 评估 + 自动修复 + 复评
    python engine/tools/info_quality_check.py --check   # 仅检查（不写报告文件）

判定口径（与项目架构约定对齐，决策见 engine/report-audits/info-quality/rules-notes.md）：
- C-03 跨文档重复仅针对研究正文 reports/*.md；各主题的 prompts / operations-guide /
  handbook 是「自包含业务包」，共享模板句属设计内重复，不计为缺陷。跨文档重复按
  归一化相似度 ≥ 80% 判定（恢复《信息质量评估提示词体系》模块二 2.4 口径）。
- C-07 来源标注认可：URL、「来源」字样、登记册指针、手册指针、Markdown 链接，
  以及白名单内的交叉引用括号；纯交叉引用括号（主题目录 / 路径文件 / 纯编号）不计。
  事实单元自 2026-11-15 起纳入表格行；程序化门槛 20% 不变，报告维度「语义目标
  完成度」单独统计并公示。
- C-08 时效自 2026-11-15 起直接读取登记册「版本日期 / 核验日期」字段化值判定，
  不再使用「报告期间 + 更新标记」旧逻辑。
- C-10 登记册口径一致性按 Schema 分支：新表（含「口径」列）直接比较「口径」列；
  旧表（「优先数据源 + 最新值内嵌口径」）沿用原比较逻辑。仅解析活值表，历史
  版本快照为冻结存档，不参与判定。
- C-13 报告 ↔ 登记册数值一致性（全量覆盖全部业务主题，P1）。
- C-14 ④/⑤ 级来源必须完成核验标注（分级字段化，P1）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, detect_month_report, iter_business_dirs, md_table, topic_slug  # noqa: E402

# ──────────────────────────────────────────────
# 内置默认参数（与提示词体系模块九一致，无需人工配置）
# ──────────────────────────────────────────────
THRESH_REQUIRED_COVERAGE = 0.95      # 必需要素覆盖率门槛
THRESH_DUP_RATIO = 0.10              # 重复冗余率门槛
THRESH_SOURCE_COVERAGE = 0.20        # 事实单元来源覆盖率程序化门槛（低于此值判 C-07 提示）
THRESH_CITE_VALID = 1.00             # 交叉引用有效率门槛
STALE_MONTHS = 12                    # 报告时效窗口（月）
STALE_DAYS = STALE_MONTHS * 30       # 时效窗口（天，按 30 天/月折算）
DUP_MIN_CHARS = 40                   # 重复段落判定最小长度
SIMILARITY_DUP = 0.80                # 高相似判定阈值（跨文档，模块二 2.4）
THRESH_EMPTY_MODULE = 0.20           # 空模块占比门槛（超过提示）
THRESH_FACT_DUP = 0.10               # 跨报告事实重复率门槛
FACT_MIN_CHARS = 12                  # 事实片段判定最小长度
MAX_REWORK_ROUNDS = 2               # 修复最大返工轮次（提示词体系模块九：2 轮）

# 报告 ↔ 登记册数值一致性覆盖范围：None = 全量业务主题（2026-11-16 起）；
# 元组 = 限定主题（分期推进期使用）。00 决策层无登记册，自动跳过。
VALUE_SYNC_TOPICS = None

# ④/⑤ 级来源允许的核验标注（分级字段化）
GRADE_ANNOTATION_MARKERS = (
    "已核验", "已核实", "已回溯", "需核实原文", "待核实", "单源待证",
    "转引", "转载", "推断", "历史参考", "仅供参考", "样本", "未核实",
)

AUDIT_DIR = ROOT / "engine" / "report-audits" / "info-quality"

# 主题级必需要素（文件/目录）
REQUIRED_ITEMS = (
    ("prompts/business-config.md", "业务配置（单一事实源）", "P0"),
    ("data/（指标登记册）", "指标登记册", "P0"),
    ("reports/（月度报告 md）", "月度报告", "P1"),
    ("operations-guide.md", "操作指南", "P1"),
)

# 报告级必需要素（免责声明改为结构化校验，见 check_disclaimer）
REPORT_REQUIRED_MARKERS = (
    ("来源标注", None, "P1"),   # 以覆盖率方式判定，见 check_report
    ("执行摘要/结论", ("摘要", "结论"), "P1"),
)

# 结构化免责声明必含要素（替代原「免责 / 不构成法律意见」子串匹配）
DISCLAIMER_REQUIRED = (
    "免责声明",        # 标题标识
    "不构成法律意见",  # 法律免责
    "专业人士",        # 转介专业人士
)
DISCLAIMER_TAX_HINT = "税务"

H2_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
CN_NUM_RE = re.compile(r"^([一二三四五六七八九十]+)[、.]")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# 「已审计」标识块（审计状态，非研究内容）：相似度 / 覆盖率计算前统一剥离
BADGE_LINE_RE = re.compile(r"^>\s*\*\*已审计\*\*.*$", re.MULTILINE)
# 自动验证结果块（交付协议规定的机器生成块）：设计内重复，不计入相似度 / 重复判定
AUTO_VERIFY_BLOCK_RE = re.compile(
    r"<!-- AUTO-VERIFY:START -->.*?<!-- AUTO-VERIFY:END -->", re.DOTALL)
# 设计内重复（模板化声明 / 纯交叉引用列表，非研究正文交叉重复）：
# 与 prompts / operations-guide / handbook 的「自包含业务包」同口径，命中即不参与 C-03 跨文档判定。
BOILERPLATE_BLOCK_RE = re.compile(
    r"^\s*(?:"
    r"\*\*(?:监测节奏|登记册字段|结构变更备注|数据变更摘要)\*\*"
    r"|本主题(?:不含|不维护)"
    r"|-\s*\[\d{2}-[a-z0-9-]+[^\]]*\]\(\.\./\.\./"
    r")"
)
# 行内标签 / Markdown 链接文本（标签 2–24 字）
BRACKET_RE = re.compile(r"\[([^\]]{2,24})\](\([^)]*\))?")

# 「交叉引用」白名单：允许计为来源标注的括号标签（单独维护，初始为空）
CROSS_REF_SOURCE_WHITELIST: set[str] = set()

P_LEVELS = {"P0": 0, "P1": 1, "P2": 2}


@dataclass
class Finding:
    """一条混乱问题记录。"""

    code: str          # C-01~C-14
    level: str         # P0/P1/P2
    topic: str         # 主题目录名
    path: str          # 相对仓库根的路径
    location: str      # 文档内位置描述
    detail: str        # 判定依据描述
    spec: str = ""     # 对应修复规范（S-xx）
    status: str = "open"   # open / fixed / unfixable


@dataclass
class Repair:
    """一条修复记录。"""

    finding_code: str
    topic: str
    path: str
    spec: str
    action: str
    before: str
    after: str
    result: str = "applied"   # applied / skipped


@dataclass
class Metrics:
    """四维度量化指标（全项目聚合）。"""

    topics_total: int = 0
    topics_complete: int = 0
    required_coverage: float = 0.0
    missing_items: int = 0
    contradictions: int = 0        # C-01/C-02/C-10
    gaps: int = 0                  # C-04
    source_coverage: float = 0.0
    semantic_completion: float = 0.0   # 语义目标完成度（向 100% 溯源目标，单独公示）
    stale_reports: int = 0
    dup_ratio: float = 0.0
    fact_dup_ratio: float = 0.0      # 跨报告事实重复率
    empty_module_ratio: float = 0.0  # 空模块占比
    attribution_errors: int = 0
    cite_valid_ratio: float = 1.0
    broken_links: int = 0
    findings_by_level: dict = field(default_factory=dict)


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _norm(text: str) -> str:
    """段落归一化：去空白、去 Markdown 修饰符，用于重复判定。"""
    t = re.sub(r"`*", "", text)
    t = re.sub(r"[ \t\u3000]+", "", t)
    return t.strip()


def _similar(a: str, b: str) -> float:
    """归一化段落相似度（SequenceMatcher ratio，模块二 2.4 重复判定内核）。"""
    return SequenceMatcher(None, a, b).ratio()


def _paragraphs(text: str) -> list[str]:
    """按空行切分段落块（保留表格/代码块整体）。"""
    blocks = re.split(r"\n\s*\n", text)
    return [b.strip() for b in blocks if b.strip()]


def _substantive(block: str) -> bool:
    """是否为实质性段落（排除表格、代码块、纯标题、引用块）。"""
    if block.startswith("|") or block.startswith("```"):
        return False
    if H2_RE.match(block):
        return False
    return len(_norm(block)) >= DUP_MIN_CHARS


def _strip_badges(text: str) -> str:
    """剥离机器生成块（自动验证结果）与「已审计」标识，避免干扰相似度与覆盖率计算。"""
    text = AUTO_VERIFY_BLOCK_RE.sub("", text)
    return BADGE_LINE_RE.sub("", text)


def _has_source(block: str) -> bool:
    """来源标注判定（2026-11-15 收紧括号口径）。

    认可：① URL；② 「来源」字样；③ 登记册指针（含「登记册」）；
    ④ 手册指针（含「手册」）；⑤ Markdown 链接（`[文本](url)`）；
    ⑥ 白名单内的交叉引用括号。
    纯交叉引用括号（主题目录 / 路径文件 / 纯编号，如 `[08-visa-immigration]`、
    `[001472175.pdf]`）不计为来源标注；机构标签须同行存在 URL / 「来源」字样
    （该情形已由 ① / ② 覆盖），不再单独计入。
    """
    if "http" in block or "来源" in block or "登记册" in block or "手册" in block:
        return True
    for m in BRACKET_RE.finditer(block):
        tag, target = m.group(1), m.group(2)
        if target:                      # Markdown 链接（含 URL）
            return True
        if tag in CROSS_REF_SOURCE_WHITELIST:
            return True
    return False


def _fact_units(text: str) -> tuple[list[str], list[str]]:
    """事实单元 = 含数字的实质段落 + 含数字的表格行（2026-11-15 起表格行纳入统计）。

    返回 (段落单元, 表格行单元)；已剥离「已审计」标识块。
    """
    text = _strip_badges(text)
    paras = [b for b in _paragraphs(text) if _substantive(b) and re.search(r"\d", b)]
    rows: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if (
            s.startswith("|")
            and "---" not in s
            and not re.match(r"^\|\s*#", s)
            and re.search(r"\d", s)
        ):
            rows.append(s)
    return paras, rows


def _split_row(line: str) -> list[str]:
    """Markdown 表格行 -> 单元格列表（去首尾空管）。"""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _live_table(text: str) -> tuple[list[str], list[list[str]]] | None:
    """定位登记册「活值表」：第一个表头同时含「指标」与（「口径」或「优先数据源」）的表。

    返回 (表头, 数据行)；表头首个单元格为「#」。未找到返回 None。
    历史版本快照等其它表不参与判定。
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            hdr = _split_row(s)
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(_split_row(lines[j].strip()))
                j += 1
            if "指标" in hdr and ("口径" in hdr or "优先数据源" in hdr):
                return hdr, rows
            i = j
        else:
            i += 1
    return None


def _registry_calibers(text: str) -> dict[str, str]:
    """登记册活值表 -> {指标: 口径}（Schema 分支）。

    新表（含「口径」列）：直接取「口径」列；
    旧表（「优先数据源 + 最新值内嵌口径」）：取「优先数据源」，若「最新值」含显式
    「口径 / 定义：…」标注则并列填入。
    """
    lt = _live_table(text)
    if not lt:
        return {}
    hdr, rows = lt
    out: dict[str, str] = {}
    for cells in rows:
        if len(cells) < 2 or not cells[0].isdigit():
            continue
        name = cells[1]
        if not name:
            continue
        if "口径" in hdr:
            idx = hdr.index("口径")
            out[name] = _norm(cells[idx]) if idx < len(cells) else ""
        elif "优先数据源" in hdr:
            idx = hdr.index("优先数据源")
            base = cells[idx] if idx < len(cells) else ""
            extra = ""
            for i, h in enumerate(hdr):
                if "最新值" in h and i < len(cells):
                    m = re.search(r"(?:口径|定义)[：:]([^；;，,）)]+)", cells[i])
                    if m:
                        extra = m.group(1).strip()
                    break
            out[name] = _norm(base + (f"｜{extra}" if extra else ""))
    return out


def registry_latest_date(text: str):
    """登记册全文 -> 字段化日期最新值（C-08 判定依据；阶段闸 G2-STALE 共用）。

    新表：取「核验日期」「版本日期」列；旧表：取「基准版本」中的 vYYYY.MM.DD。
    无可用字段时返回 None（不判定，不再回退旧逻辑）。
    """
    lt = _live_table(text)
    if not lt:
        return None
    hdr, rows = lt
    dates: list[date] = []
    col_idx: list[int] = []
    for i, h in enumerate(hdr):
        if "核验日期" in h or "版本日期" in h or "基准版本" in h:
            col_idx.append(i)
    for cells in rows:
        for i in col_idx:
            if i >= len(cells):
                continue
            for y, m, d in re.findall(r"(\d{4})[.-](\d{1,2})[.-](\d{1,2})", cells[i]):
                try:
                    dates.append(date(int(y), int(m), int(d)))
                except ValueError:
                    continue
    return max(dates) if dates else None


def _significant_numbers(s: str) -> set[str]:
    """抽取「数值型」数字（排除年份、1–2 位小数前零、YYYY.M 版本串与括号内文献号）。"""
    s = re.sub(r"\[[^\]]*\]", " ", s)
    out: set[str] = set()
    for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", s):
        t = m.group(0).replace(",", "")
        if re.fullmatch(r"(?:19|20)\d{2}", t):
            continue
        if re.fullmatch(r"\d{1,2}", t):
            continue
        if re.fullmatch(r"\d{4}\.\d{1,2}", t):
            continue
        out.add(t)
    return out


def _report_value_rows(text: str) -> dict[int, str]:
    """报告「数据变更摘要」表 -> {#: 活值单元格}（用于 C-13 数值一致性）。"""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            hdr = _split_row(s)
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(_split_row(lines[j].strip()))
                j += 1
            if "指标" in hdr and any("活值" in h for h in hdr):
                vi = next(i2 for i2, h in enumerate(hdr) if "活值" in h)
                out: dict[int, str] = {}
                for cells in rows:
                    if len(cells) > vi and cells[0].isdigit():
                        out[int(cells[0])] = cells[vi]
                return out
            i = j
        else:
            i += 1
    return {}


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def check_disclaimer(text: str) -> tuple[bool, str]:
    """结构化免责声明校验（替代子串匹配）。

    必含：「免责声明」标识 + 「不构成法律意见」+ 「专业人士」转介；
    建议含：「税务」字样。缺项返回 (False, 缺项说明)。
    """
    missing = [k for k in DISCLAIMER_REQUIRED if k not in text]
    if missing:
        return False, "缺少要素：" + "、".join(missing)
    if DISCLAIMER_TAX_HINT not in text:
        return False, f"缺少要素：{DISCLAIMER_TAX_HINT}（建议含税务免责）"
    return True, ""


def empty_module_ratio(text: str) -> tuple[int, int]:
    """h2 模块「空模块」占比 -> (空模块数, 总模块数)。

    空模块 = 标题与下一标题之间无实质内容（无段落 / 表格行 / 列表）。
    """
    lines = text.splitlines()
    heads = [i for i, ln in enumerate(lines) if re.match(r"^##\s+", ln)]
    if not heads:
        return 0, 0
    empty = 0
    for idx, start in enumerate(heads):
        end = heads[idx + 1] if idx + 1 < len(heads) else len(lines)
        content = [ln.strip() for ln in lines[start + 1:end]
                   if ln.strip() and not ln.strip().startswith("#")]
        if not content:
            empty += 1
    return empty, len(heads)


def _fact_blocks(text: str) -> list[str]:
    """提取含数字的事实片段（段落或表格行），归一化后用于跨报告重复判定。"""
    out: list[str] = []
    for b in _paragraphs(text):
        if b.startswith("```"):
            continue
        for line in b.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if re.search(r"\d", s) and len(_norm(s)) >= FACT_MIN_CHARS:
                out.append(_norm(s))
    return out


def fact_duplication(units: list[dict]) -> tuple[float, list[dict]]:
    """跨报告事实重复率：同一事实片段（归一化）出现在 ≥2 份报告的比例。

    返回 (rate, details)；rate = 重复出现的事实片段字符数 / 全部事实片段字符数。
    """
    index: dict[str, list[tuple[str, str]]] = {}
    total_chars = 0
    for u in units:
        for rp in u["reports"]:
            for n in _fact_blocks(_read(rp)):
                index.setdefault(n, []).append((u["topic"], _rel(rp)))
                total_chars += len(n)
    dup_chars = 0
    details: list[dict] = []
    for n, locs in index.items():
        topics = {t for t, _ in locs}
        if len(topics) > 1:
            dup_chars += len(n) * (len(locs) - 1)
            details.append({"fact": n[:80], "topics": sorted(topics), "count": len(locs)})
    rate = (dup_chars / total_chars) if total_chars else 0.0
    return rate, details


# ──────────────────────────────────────────────
# 阶段 0：扫描建档
# ──────────────────────────────────────────────

def scan_topics() -> list[dict]:
    """遍历全部业务线主题目录，建立内容清单。"""
    units = []
    for b in iter_business_dirs():
        p = b.path
        mds = sorted(x for x in p.rglob("*.md") if x.is_file())
        reports = sorted((p / "reports").glob("*.md")) if (p / "reports").is_dir() else []
        units.append(
            {
                "topic": b.rel,
                "slug": topic_slug(b.region),
                "path": p,
                "mds": mds,
                "reports": reports,
                "has_guide": (p / "operations-guide.md").exists(),
                "has_config": (p / "prompts" / "business-config.md").exists(),
                "registry": next(
                    (x for x in sorted((p / "data").glob("*.md")) if "registry" in x.name),
                    None,
                ) if (p / "data").is_dir() else None,
            }
        )
    return units


# ──────────────────────────────────────────────
# 阶段 1：四维度评估
# ──────────────────────────────────────────────

def check_topic_completeness(u: dict, findings: list[Finding]) -> tuple[int, int]:
    """维度一：主题完整性。返回 (已具备要素数, 应备要素数)。"""
    present = 0
    total = len(REQUIRED_ITEMS)
    if u["has_config"]:
        present += 1
    else:
        findings.append(Finding("C-06", "P0", u["topic"], f"{u['topic']}/prompts/business-config.md",
                                "文件缺失", "缺少业务配置（单一事实源）", "S-05"))
    if u["registry"] is not None:
        present += 1
    else:
        findings.append(Finding("C-06", "P0", u["topic"], f"{u['topic']}/data/",
                                "目录/文件缺失", "缺少指标登记册 data/*_indicator_registry.md", "S-05"))
    if u["reports"]:
        present += 1
    else:
        findings.append(Finding("C-06", "P1", u["topic"], f"{u['topic']}/reports/",
                                "目录/文件缺失", "缺少月度报告（reports/*.md）", "S-05"))
    if u["has_guide"]:
        present += 1
    else:
        findings.append(Finding("C-06", "P1", u["topic"], f"{u['topic']}/operations-guide.md",
                                "文件缺失", "缺少操作指南 operations-guide.md", "S-05"))
    return present, total


def check_report(u: dict, rp: Path, findings: list[Finding]) -> dict:
    """单份报告 md 的检查：归属、时效、结构、来源覆盖、断层、重复标题。"""
    text = _read(rp)
    rel = _rel(rp)
    stats = {"source_cov": 1.0, "subs": 0, "sourced": 0, "empty_modules": 0, "total_modules": 0}

    # C-05 内容归属错误：报告 slug 与目录 slug 不一致
    det = detect_month_report(rp.name)
    if det and det[1] != u["slug"]:
        findings.append(Finding("C-05", "P1", u["topic"], rel, "文件命名",
                                f"报告 slug「{det[1]}」与目录 slug「{u['slug']}」不一致", "S-04"))

    # C-06 报告结构要素
    for label, markers, level in REPORT_REQUIRED_MARKERS:
        if markers is None:
            continue
        if not any(m in text for m in markers):
            findings.append(Finding("C-06", level, u["topic"], rel, "结构要素缺失",
                                    f"缺少「{label}」要素", "S-05"))

    # C-06 免责声明：结构化校验（标识 + 法律免责 + 专业人士 + 税务）
    ok, dd = check_disclaimer(text)
    if not ok:
        findings.append(Finding("C-06", "P1", u["topic"], rel, "结构要素缺失",
                                f"免责声明结构化校验未通过：{dd}", "S-05"))

    # C-06 空模块占比
    em, tm = empty_module_ratio(text)
    stats["empty_modules"] = em
    stats["total_modules"] = tm
    if tm and em / tm > THRESH_EMPTY_MODULE:
        findings.append(Finding("C-06", "P2", u["topic"], rel, "空模块占比",
                                f"空模块 {em}/{tm}（{em / tm:.0%}）超过门槛 {THRESH_EMPTY_MODULE:.0%}", "S-10"))

    # C-06 md/html 配对
    if not rp.with_suffix(".html").exists():
        findings.append(Finding("C-06", "P2", u["topic"], rel, "文件配对",
                                "缺少对应 HTML 交付物（.md2html 同步）", "S-05"))

    # 维度三：来源标注——结构性（必须有来源章节）+ 覆盖性（事实单元含来源比例）
    heads = [t for _, t in H2_RE.findall(text)]
    if not any(("来源" in h or "参考" in h or "出处" in h) for h in heads):
        findings.append(Finding("C-07", "P1", u["topic"], rel, "结构要素缺失",
                                "缺少「来源 / 参考来源」章节", "S-06"))
    paras, rows = _fact_units(text)
    fact_blocks = paras + rows
    sourced = sum(1 for b in fact_blocks if _has_source(b))
    stats["subs"] = len(fact_blocks)
    stats["sourced"] = sourced
    stats["subs_paras"] = len(paras)
    stats["subs_rows"] = len(rows)
    stats["source_cov"] = (sourced / len(fact_blocks)) if fact_blocks else 1.0
    if fact_blocks and stats["source_cov"] < THRESH_SOURCE_COVERAGE:
        findings.append(Finding("C-07", "P2", u["topic"], rel, "事实单元来源覆盖不足",
                                f"含数字事实单元（段落 + 表格行）来源覆盖率 {stats['source_cov']:.0%} "
                                f"< {THRESH_SOURCE_COVERAGE:.0%}（程序化门槛；语义目标 100%）",
                                "S-06"))

    # C-08 时效：直接读取登记册「版本日期 / 核验日期」字段化值（2026-11-15 起）
    reg_date = registry_latest_date(_read(u["registry"])) if u.get("registry") else None
    if reg_date is not None:
        age_days = (date.today() - reg_date).days
        if age_days > STALE_DAYS:
            findings.append(Finding("C-08", "P2", u["topic"], rel, "时效",
                                    f"登记册最新核验日期 {reg_date.isoformat()} 已超出 "
                                    f"{STALE_MONTHS} 个月窗口（{age_days} 天）", "S-07"))

    # C-14 分级字段化：④/⑤ 级来源条目必须带显式核验标注
    check_grade_annotations(u, rel, text, findings)

    # C-04 逻辑断层：h2 中文序号跳号
    h2s = H2_RE.findall(text)
    nums = []
    for _, title in h2s:
        m = CN_NUM_RE.match(title.strip())
        if m:
            nums.append(m.group(1))
    order = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    seq = [order.index(n) for n in nums if n in order]
    for a, b in zip(seq, seq[1:]):
        if b - a > 1:
            findings.append(Finding("C-04", "P2", u["topic"], rel, "章节序号",
                                    f"h2 中文序号由「{order[a]}」跳至「{order[b]}」，存在逻辑断层嫌疑", "S-03"))
            break

    # C-02 同文档重复标题（表述矛盾/结构冗余嫌疑）
    seen: dict[str, int] = {}
    for _, title in h2s:
        key = _norm(title)
        if key in seen:
            findings.append(Finding("C-02", "P2", u["topic"], rel, "重复标题",
                                    f"标题「{title.strip()}」在文档内出现 {seen[key] + 1} 次", "S-01"))
            seen[key] += 1
        else:
            seen[key] = 1
    return stats


def check_grade_annotations(u: dict, rel: str, text: str, findings: list[Finding]) -> None:
    """C-14：④/⑤ 级来源条目必须带显式核验标注（分级字段化）。

    仅作用于含 ④/⑤ 来源分级小节的报告；「只读引用」类 ④ 小节（跨主题引用，非来源
    清单）豁免。标注集合见 GRADE_ANNOTATION_MARKERS。
    """
    current: str | None = None
    for line in text.splitlines():
        h = re.match(r"^(#{2,4})\s*(.*)$", line.strip())
        if h:
            m = re.match(r"^([①②③④⑤])\s*(.*)$", h.group(2).strip())
            if m and m.group(1) in ("④", "⑤") and "只读引用" not in m.group(2):
                current = m.group(1)
            else:
                current = None
            continue
        if current and re.match(r"^\s*\d+\.\s+", line):
            if not any(k in line for k in GRADE_ANNOTATION_MARKERS):
                findings.append(Finding(
                    "C-14", "P1", u["topic"], rel, "来源分级",
                    f"{current} 级来源条目缺少核验标注（{'、'.join(GRADE_ANNOTATION_MARKERS)} 任一）",
                    "S-06"))


def check_value_sync(u: dict, rp: Path, text: str, findings: list[Finding]) -> None:
    """C-13：报告 ↔ 登记册数值一致性（全量覆盖 VALUE_SYNC_TOPICS，P1）。

    以登记册活值表「最新值」列为基准，抽取数值型数字；报告「数据变更摘要」对应
    编号行若缺失该数值则判不一致。仅比数值存在性，不做单位 / 口径换算。
    """
    if u.get("registry") is None:
        return
    if VALUE_SYNC_TOPICS is not None and u["topic"] not in VALUE_SYNC_TOPICS:
        return
    lt = _live_table(_read(u["registry"]))
    if not lt:
        return
    hdr, rows = lt
    vi = next((i for i, h in enumerate(hdr) if "最新值" in h), None)
    if vi is None:
        return
    reg_vals = {int(c[0]): c[vi] for c in rows if len(c) > vi and c[0].isdigit()}
    rep_vals = _report_value_rows(text)
    rel = _rel(rp)
    for no, reg_v in sorted(reg_vals.items()):
        if no not in rep_vals:
            continue
        missing = _significant_numbers(reg_v) - _significant_numbers(rep_vals[no])
        if missing:
            findings.append(Finding(
                "C-13", "P1", u["topic"], rel, "数据变更摘要",
                f"指标 #{no} 登记册活值中的数值 {', '.join(sorted(missing))} "
                f"未在报告「数据变更摘要」对应行出现", "S-09"))


def check_cross_topic(units: list[dict], findings: list[Finding]) -> dict:
    """维度二/四的跨主题检查：重复段落、失效引用、登记册口径冲突。"""
    # ── 重复段落（同文档内 + 跨文档）──
    # ── 重复段落 ──
    # 同文档内重复：全部 md（真实冗余信号，可自动去重）
    file_chars: dict[str, int] = {}
    dup_extra_chars = 0
    for u in units:
        for md in u["mds"]:
            text = _strip_badges(_read(md))
            counts: dict[str, int] = {}
            chars = 0
            for b in _paragraphs(text):
                if not _substantive(b):
                    continue
                n = _norm(b)
                if len(n) < DUP_MIN_CHARS:
                    continue
                chars += len(n)
                counts[n] = counts.get(n, 0) + 1
            rel_md = _rel(md)
            file_chars[rel_md] = chars
            for n, c in counts.items():
                if c > 1:
                    dup_extra_chars += len(n) * (c - 1)
                    findings.append(Finding(
                        "C-03", "P1", u["topic"], rel_md, "段落重复",
                        f"同一实质段落在本文件内重复 {c} 次（约 {len(n)} 字）", "S-02"))
    # 跨文档重复：仅研究正文 reports/*.md（提示级，不自动删）
    # 说明：各主题的 prompts / operations-guide / handbook 为「自包含业务包」，
    # 共享模板句属设计内重复（架构要求），不作为缺陷；研究正文才要求不交叉重复。
    # 判定：归一化后相似度 ≥ SIMILARITY_DUP（模块二 2.4；含已审计标识剥离）。
    para_index: list[tuple[str, str, str]] = []   # (topic, rel, norm)
    for u in units:
        for rp in u["reports"]:
            text = _strip_badges(_read(rp))
            for b in _paragraphs(text):
                if not _substantive(b):
                    continue
                if BOILERPLATE_BLOCK_RE.match(b):
                    continue
                n = _norm(b)
                if len(n) < DUP_MIN_CHARS:
                    continue
                para_index.append((u["topic"], _rel(rp), n))
    flagged: set[tuple[str, str]] = set()
    for i in range(len(para_index)):
        t1, r1, n1 = para_index[i]
        if len(n1) < 120:
            continue
        for j in range(i + 1, len(para_index)):
            t2, r2, n2 = para_index[j]
            if t1 == t2 or len(n2) < 120:
                continue
            if (r1, r2) in flagged:
                continue
            if _similar(n1, n2) >= SIMILARITY_DUP:
                flagged.add((r1, r2))
                findings.append(Finding(
                    "C-03", "P2", sorted((t1, t2))[0], r1, "跨文档重复",
                    f"约 {min(len(n1), len(n2))} 字的段落与 {r2} 相似度 "
                    f"≥ {SIMILARITY_DUP:.0%}，疑似研究正文交叉重复，建议确认是否需保留",
                    "S-02"))
                dup_extra_chars += min(len(n1), len(n2))
    total_chars = sum(file_chars.values())

    # ── 失效引用 ──
    total_links = 0
    broken_links = 0
    for u in units:
        for md in u["mds"]:
            text = _read(md)
            for target in MD_LINK_RE.findall(text):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                # 模板占位（{{...}} / <slug>）与全角括号收尾不是真实链接，跳过
                tok = target.split()[0] if target.split() else ""
                raw = re.split(r"[）)]", tok)[0].strip()
                if not raw or "{{" in raw or "<" in raw:
                    continue
                path_part = raw.split("#")[0]
                if not path_part:
                    continue
                total_links += 1
                resolved = (md.parent / path_part).resolve()
                if not resolved.exists():
                    broken_links += 1
                    findings.append(Finding(
                        "C-09", "P2", u["topic"], _rel(md), "交叉引用",
                        f"引用目标不存在：{raw}", "S-08"))
    cite_valid = (1 - broken_links / total_links) if total_links else 1.0

    # ── 登记册口径冲突（C-10，Schema 分支）──
    reg_defs: dict[str, dict[str, set[str]]] = {}
    for u in units:
        if u["registry"] is None:
            continue
        # 仅解析活值表（新表「口径」列 / 旧表「优先数据源 + 最新值内嵌口径」）；
        # 历史版本快照为冻结存档，不参与口径一致性判定
        for name, caliber in _registry_calibers(_read(u["registry"])).items():
            reg_defs.setdefault(name, {}).setdefault(u["topic"], set()).add(caliber)
    for name, per_topic in reg_defs.items():
        if len(per_topic) < 2:
            continue
        calibers = set().union(*per_topic.values())
        if len(calibers) > 1:
            findings.append(Finding(
                "C-10", "P2", "|".join(sorted(per_topic)), "data/（登记册）", "口径不一致",
                f"指标「{name}」在 {len(per_topic)} 个主题登记册中口径表述不一致", "S-09"))

    dup_ratio = (dup_extra_chars / total_chars) if total_chars else 0.0

    # ── 跨报告事实重复率（C-03 事实口径）──
    fact_rate, fact_details = fact_duplication(units)
    if fact_rate > THRESH_FACT_DUP:
        findings.append(Finding(
            "C-03", "P2", "全库", "reports/（跨报告）", "跨报告事实重复率",
            f"{fact_rate:.1%} 超过门槛 {THRESH_FACT_DUP:.0%}（{len(fact_details)} 组跨报告重复事实）", "S-02"))

    return {"dup_ratio": dup_ratio, "cite_valid": cite_valid, "total_links": total_links,
            "broken_links": broken_links, "fact_dup_ratio": fact_rate,
            "fact_dup_details": fact_details}


def evaluate(units: list[dict]) -> tuple[list[Finding], Metrics]:
    """阶段 1+2：执行全部检查，返回问题清单与聚合指标。"""
    findings: list[Finding] = []
    m = Metrics()
    m.topics_total = len(units)

    present_sum = 0
    total_sum = 0
    subs_all = 0
    sourced_all = 0
    empty_sum = 0
    modules_sum = 0
    for u in units:
        p, t = check_topic_completeness(u, findings)
        present_sum += p
        total_sum += t
        if p == t:
            m.topics_complete += 1
        for rp in u["reports"]:
            st = check_report(u, rp, findings)
            check_value_sync(u, rp, _read(rp), findings)
            subs_all += st["subs"]
            sourced_all += st["sourced"]
            empty_sum += st["empty_modules"]
            modules_sum += st["total_modules"]

    cross = check_cross_topic(units, findings)

    m.required_coverage = present_sum / total_sum if total_sum else 1.0
    m.missing_items = total_sum - present_sum
    m.contradictions = sum(1 for f in findings if f.code in ("C-01", "C-02", "C-10"))
    m.gaps = sum(1 for f in findings if f.code == "C-04")
    m.source_coverage = sourced_all / subs_all if subs_all else 1.0
    m.semantic_completion = m.source_coverage   # 报告维度语义目标完成度（单独公示，不入退出码）
    m.stale_reports = sum(1 for f in findings if f.code == "C-08")
    m.dup_ratio = cross["dup_ratio"]
    m.fact_dup_ratio = cross["fact_dup_ratio"]
    m.empty_module_ratio = (empty_sum / modules_sum) if modules_sum else 0.0
    m.attribution_errors = sum(1 for f in findings if f.code == "C-05")
    m.cite_valid_ratio = cross["cite_valid"]
    m.broken_links = cross["broken_links"]
    for lv in ("P0", "P1", "P2"):
        m.findings_by_level[lv] = sum(1 for f in findings if f.level == lv and f.status == "open")
    return findings, m


# ──────────────────────────────────────────────
# 阶段 3：自动修复
# ──────────────────────────────────────────────

PLACEHOLDER_CONFIG = """# {slug} · 业务配置（占位骨架，待补）

> **状态**：本文件由 `info_quality_check.py` 依据《信息质量评估提示词体系》S-05 自动补建，内容待补。
> **用途**：本主题的单一事实源（主题定位 / 适用场景 / 核心指标 / 更新规则 / 交付规则）。

## 一、主题定位

（待补）

## 二、运行变量

- 主题：{slug}
- 登记册：data/{slug}_indicator_registry.md

## 三、更新与交付规则

（待补）
"""

PLACEHOLDER_REGISTRY = """# {slug} · 指标登记册（占位骨架，待补）

> **状态**：本文件由 `info_quality_check.py` 依据《信息质量评估提示词体系》S-05 自动补建，内容待补。

## 核心指标

| # | 指标 | 口径 | 研究阶段 | 最新值 / 规则 | 来源机构 | 来源 URL | 版本日期 | 核验日期 | 核验状态 | 关联章节 | 更新时间 |
|---|---|---|---|---|---|---|---|---|---|---|---|
"""

PLACEHOLDER_GUIDE = """# {slug} · 操作指南（占位骨架，待补）

> **状态**：本文件由 `info_quality_check.py` 依据《信息质量评估提示词体系》S-05 自动补建，内容待补。

## 适用范围

（待补）

## 操作步骤

（待补）
"""

# S-05 标准化免责声明（与项目既有口径一致：17/18/19/20 报告用语）
STANDARD_DISCLAIMER = (
    "> **免责声明**：本报告为信息整理与条件化建议，不构成法律意见或税务意见；"
    "重大决策请咨询执业法律 / 税务专业人士。"
)


def _insert_disclaimer(path: Path) -> Repair | None:
    """S-05：在报告头部（首个块之后）插入标准化免责声明块引用。"""
    text = _read(path)
    ok, _ = check_disclaimer(text)
    if ok:
        return None
    m = re.search(r"\n\s*\n", text)
    first = text[: m.start()].strip() if m else text.strip()
    if m is not None and first.startswith((">", "#")):
        pos = m.end()
    else:
        nl = text.find("\n")
        pos = nl + 1 if nl != -1 else len(text)
    new_text = text[:pos] + STANDARD_DISCLAIMER + "\n\n" + text[pos:]
    path.write_text(new_text, encoding="utf-8")
    return Repair("C-06", "", _rel(path), "S-05", "插入标准化免责声明（头部块引用）",
                  "（缺失）", STANDARD_DISCLAIMER)


def _dedupe_within_file(path: Path) -> Repair | None:
    """S-02：删除同文档内重复的实质段落（保留首次出现）。"""
    text = _read(path)
    blocks = re.split(r"(\n\s*\n)", text)
    seen: dict[str, int] = {}
    out: list[str] = []
    removed = 0
    for block in blocks:
        n = _norm(block)
        if _substantive(block):
            if n in seen:
                removed += 1
                continue
            seen[n] = 1
        out.append(block)
    if not removed:
        return None
    new_text = "".join(out)
    if not path.is_absolute():
        path = ROOT / path
    path.write_text(new_text, encoding="utf-8")
    return Repair("C-03", "", _rel(path), "S-02", f"删除同文档内重复段落 {removed} 处",
                  f"重复段落 ×{removed}", "已保留首次出现并删除后续副本")


def _repoint(path: Path, old_target: str, new_target: Path) -> Repair | None:
    new_rel = os_relpath(new_target, path.parent)
    text = _read(path)
    new_text = text.replace(old_target, new_rel)
    if new_text == text:
        return None
    path.write_text(new_text, encoding="utf-8")
    return Repair("C-09", "", _rel(path), "S-08", f"失效引用重指：{old_target} → {new_rel}",
                  old_target, new_rel)


def _fix_link(path: Path, target: str) -> Repair | None:
    """S-08：失效的相对 md 链接，按唯一匹配重指。

    两级匹配：① 精确文件名全局唯一；② 归档副本 `<X>-merged-vN.N.md` 回指
    同主题 `reports/<X>.md`（唯一）。无法唯一确定时返回 None（转人工）。
    """
    path_part = target.split("#")[0]
    name = Path(path_part).name
    if not name:
        return None
    exact = [p for p in ROOT.rglob(name) if p.is_file() and ".git" not in p.parts]
    if len(exact) == 1:
        return _repoint(path, target, exact[0])
    m = re.match(r"^(?P<base>.+?)(?:-merged-v[\d.]+)?\.md$", name)
    if not m:
        return None
    base = m.group("base")
    cands = [p for p in ROOT.rglob("*.md")
             if p.is_file() and ".git" not in p.parts
             and "reports" in p.parts and p.stem == base]
    if len(cands) == 1:
        return _repoint(path, target, cands[0])
    return None


def os_relpath(target: Path, start: Path) -> str:
    import os
    return os.path.relpath(target, start).replace("\\", "/")


def repair(findings: list[Finding], units: list[dict]) -> list[Repair]:
    """按修复规范执行自动修复，返回修复记录。"""
    repairs: list[Repair] = []

    for f in findings:
        if f.status != "open":
            continue
        topic_dir = ROOT / f.topic
        if f.code == "C-06":
            if "免责声明" in f.detail:
                rp = ROOT / f.path
                if rp.exists():
                    rep = _insert_disclaimer(rp)
                    if rep:
                        rep.topic = f.topic
                        repairs.append(rep)
                        f.status = "fixed"
                    else:
                        f.status = "unfixable"
                continue
            if "business-config.md" in f.path and not (topic_dir / "prompts").exists():
                (topic_dir / "prompts").mkdir(parents=True, exist_ok=True)
            if f.path.endswith("business-config.md") and not (topic_dir / "prompts" / "business-config.md").exists():
                target = topic_dir / "prompts" / "business-config.md"
                target.write_text(PLACEHOLDER_CONFIG.format(slug=topic_slug_of(f.topic)), encoding="utf-8")
                repairs.append(Repair(f.code, f.topic, f.path, "S-05", "补建业务配置占位骨架",
                                      "（缺失）", target.read_text(encoding="utf-8")[:80] + "…"))
                f.status = "fixed"
            elif f.path.endswith("data/") or "registry" in f.detail:
                target = topic_dir / "data" / f"{topic_slug_of(f.topic)}_indicator_registry.md"
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(PLACEHOLDER_REGISTRY.format(slug=topic_slug_of(f.topic)), encoding="utf-8")
                    repairs.append(Repair(f.code, f.topic, f.path, "S-05", "补建指标登记册占位骨架",
                                          "（缺失）", target.read_text(encoding="utf-8")[:80] + "…"))
                    f.status = "fixed"
            elif f.path.endswith("reports/"):
                # 报告缺失不自动造内容，仅标注待补
                f.status = "unfixable"
                f.detail += "（报告正文需人工/研究生成，不自动补建）"
            elif f.path.endswith("operations-guide.md"):
                target = topic_dir / "operations-guide.md"
                if not target.exists():
                    target.write_text(PLACEHOLDER_GUIDE.format(slug=topic_slug_of(f.topic)), encoding="utf-8")
                    repairs.append(Repair(f.code, f.topic, f.path, "S-05", "补建操作指南占位骨架",
                                          "（缺失）", target.read_text(encoding="utf-8")[:80] + "…"))
                    f.status = "fixed"
            elif "HTML" in f.detail:
                f.status = "unfixable"
                f.detail += "（由 md2html.py 同步生成，不在此自动补建）"
            else:
                f.status = "unfixable"

        elif f.code == "C-03":
            # 仅自动修复同文档内重复（跨文档重复只报告）
            if "跨文档" in f.detail:
                continue
            rp = ROOT / f.path
            if not rp.exists():
                continue
            rep = _dedupe_within_file(rp)
            if rep:
                rep.finding_code = "C-03"
                rep.topic = f.topic
                repairs.append(rep)
                f.status = "fixed"

        elif f.code == "C-09":
            rp = ROOT / f.path
            link_target = f.detail.split("：", 1)[-1]
            rep = _fix_link(rp, link_target) if rp.exists() else None
            if rep:
                rep.finding_code = "C-09"
                rep.topic = f.topic
                repairs.append(rep)
                f.status = "fixed"
            else:
                f.status = "unfixable"

        else:
            # C-01/C-02/C-04/C-05/C-07/C-08/C-10：需语义判断或外部信息，不自动修复
            f.status = "unfixable"

    return repairs


def topic_slug_of(topic_rel: str) -> str:
    top = topic_rel.split("/")[0]
    return topic_slug(top)


# ──────────────────────────────────────────────
# 阶段 4：修复验证
# ──────────────────────────────────────────────

def verify(before: Metrics, before_findings: list[Finding], after_findings: list[Finding],
           after: Metrics, repairs: list[Repair]) -> dict:
    """复评 + 回归校验，返回验证结论。"""
    new_issues = [f for f in after_findings if f.status == "open"]
    # 回归 = 修复后新出现的失效引用（修复前不存在同位置同目标的断链）
    before_broken = {(f.path, f.detail) for f in before_findings
                     if f.code == "C-09" and f.status == "open"}
    regressed = [f for f in after_findings
                 if f.code == "C-09" and f.status == "open"
                 and (f.path, f.detail) not in before_broken]
    before_open = sum(before.findings_by_level.values())
    after_open = sum(after.findings_by_level.values())
    p0p1_contra = sum(1 for f in after_findings
                      if f.code in ("C-01", "C-02", "C-10")
                      and f.level in ("P0", "P1") and f.status == "open")
    checks = {
        "required_coverage_ok": after.required_coverage >= THRESH_REQUIRED_COVERAGE,
        "dup_ratio_ok": after.dup_ratio <= THRESH_DUP_RATIO,
        "cite_valid_not_regressed": after.broken_links <= before.broken_links,
        "p0p1_contradictions_zero": p0p1_contra == 0,
        "no_new_open_findings": after_open <= before_open,
        "no_regression": len(regressed) == 0,
        "repairs_verified": all(
            (ROOT / r.path).exists() for r in repairs if r.result == "applied"
        ),
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "before": asdict(before),
        "after": asdict(after),
        "open_after": [asdict(f) for f in new_issues],
    }


# ──────────────────────────────────────────────
# 阶段 5：报告交付
# ──────────────────────────────────────────────

def write_reports(findings: list[Finding], repairs: list[Repair],
                  before: Metrics, after: Metrics, ver: dict, run_date: str) -> list[Path]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    written = []

    # 评估台账
    rows = [["编号", "级别", "主题", "位置", "位置描述", "判定依据", "修复规范", "状态"]]
    for f in sorted(findings, key=lambda x: (P_LEVELS[x.level], x.code, x.path)):
        rows.append([f.code, f.level, f.topic, f.path, f.location, f.detail,
                     f.spec or "—", {"open": "待处理", "fixed": "已修复", "unfixable": "需人工/外部"}[f.status]])
    assessment = "\n".join([
        "# 信息质量评估台账",
        "",
        f"> 运行日期：{run_date}　|　评估范围：全项目 {before.topics_total} 个主题",
        f"> 数据来源：info_quality_check.py 程序化判定（《信息质量评估提示词体系》可执行子集）",
        "",
        "## 四维度量化指标（修复前）",
        "",
        md_table([["维度", "指标", "实测值", "门槛", "判定"],
                   ["完整性", "必需要素覆盖率", f"{before.required_coverage:.1%}",
                    f"≥ {THRESH_REQUIRED_COVERAGE:.0%}", "达标" if before.required_coverage >= THRESH_REQUIRED_COVERAGE else "不达标"],
                   ["完整性", "完整主题数", f"{before.topics_complete}/{before.topics_total}", "—", "—"],
                   ["一致性", "矛盾/口径问题数", str(before.contradictions), "= 0", "达标" if before.contradictions == 0 else "不达标"],
                   ["一致性", "逻辑断层数", str(before.gaps), "—", "—"],
                   ["准确性", "来源标注覆盖率", f"{before.source_coverage:.1%}", f"≥ {THRESH_SOURCE_COVERAGE:.0%}", "达标" if before.source_coverage >= THRESH_SOURCE_COVERAGE else "不达标"],
                   ["准确性", "语义目标完成度（向 100%，单独公示）", f"{before.semantic_completion:.1%}", "目标 100%（不阻断）", "—"],
                   ["准确性", "过期未标注报告数", str(before.stale_reports), "= 0", "达标" if before.stale_reports == 0 else "不达标"],
                   ["关联性", "重复冗余率", f"{before.dup_ratio:.1%}", f"≤ {THRESH_DUP_RATIO:.0%}", "达标" if before.dup_ratio <= THRESH_DUP_RATIO else "不达标"],
                   ["关联性", "跨报告事实重复率", f"{before.fact_dup_ratio:.1%}", f"≤ {THRESH_FACT_DUP:.0%}", "达标" if before.fact_dup_ratio <= THRESH_FACT_DUP else "不达标"],
                   ["完整性", "空模块占比", f"{before.empty_module_ratio:.1%}", f"≤ {THRESH_EMPTY_MODULE:.0%}", "达标" if before.empty_module_ratio <= THRESH_EMPTY_MODULE else "不达标"],
                   ["关联性", "归属错误数", str(before.attribution_errors), "= 0", "达标" if before.attribution_errors == 0 else "不达标"],
                   ["关联性", "交叉引用有效率", f"{before.cite_valid_ratio:.1%}", "= 100%", "达标" if before.cite_valid_ratio >= THRESH_CITE_VALID else "不达标"],
                   ["问题分布", "P0 / P1 / P2", f"{before.findings_by_level['P0']} / {before.findings_by_level['P1']} / {before.findings_by_level['P2']}", "—", "—"],
                   ]),
        "",
        "## 问题明细",
        "",
        md_table(rows),
        "",
    ])
    p = AUDIT_DIR / "assessment-ledger.md"
    p.write_text(assessment, encoding="utf-8")
    written.append(p)

    # 修复台账
    rows = [["问题编号", "主题", "位置", "修复规范", "修复动作", "修复前", "修复后", "结果"]]
    for r in repairs:
        rows.append([r.finding_code, r.topic, r.path, r.spec, r.action,
                     r.before.replace("\n", " ")[:60], r.after.replace("\n", " ")[:60], r.result])
    repair_md = "\n".join([
        "# 信息质量修复台账",
        "",
        f"> 运行日期：{run_date}　|　自动修复 {len(repairs)} 条",
        "",
        md_table(rows) if len(rows) > 1 else "（本轮无自动修复项）",
        "",
    ])
    p = AUDIT_DIR / "repair-ledger.md"
    p.write_text(repair_md, encoding="utf-8")
    written.append(p)

    # 验证报告
    chk_rows = [[k, "通过" if v else "未通过"] for k, v in ver["checks"].items()]
    report_md = "\n".join([
        "# 信息质量验证报告",
        "",
        f"> 运行日期：{run_date}",
        "",
        "## 修复后指标（复评）",
        "",
        md_table([["指标", "修复前", "修复后", "门槛"],
                   ["必需要素覆盖率", f"{before.required_coverage:.1%}", f"{after.required_coverage:.1%}", f"≥ {THRESH_REQUIRED_COVERAGE:.0%}"],
                   ["重复冗余率", f"{before.dup_ratio:.1%}", f"{after.dup_ratio:.1%}", f"≤ {THRESH_DUP_RATIO:.0%}"],
                   ["跨报告事实重复率", f"{before.fact_dup_ratio:.1%}", f"{after.fact_dup_ratio:.1%}", f"≤ {THRESH_FACT_DUP:.0%}"],
                   ["空模块占比", f"{before.empty_module_ratio:.1%}", f"{after.empty_module_ratio:.1%}", f"≤ {THRESH_EMPTY_MODULE:.0%}"],
                   ["交叉引用有效率", f"{before.cite_valid_ratio:.1%}", f"{after.cite_valid_ratio:.1%}", "= 100%"],
                   ["矛盾/口径问题数", str(before.contradictions), str(after.contradictions), "= 0"],
                   ["待处理问题数", str(sum(before.findings_by_level.values())),
                    str(sum(after.findings_by_level.values())), "—"],
                   ]),
        "",
        "## 校验项",
        "",
        md_table([["校验项", "结果"]] + chk_rows),
        "",
        "## 遗留项（需人工/外部介入）",
        "",
    ] + [
        f"- [{f.level}] {f.code} {f.topic}/{f.path}：{f.detail}"
        for f in sorted(findings, key=lambda x: P_LEVELS[x.level]) if f.status == "unfixable"
    ] + ["", f"**验证结论：{'全部通过' if ver['passed'] else '存在未通过校验项，见上表'}**", ""])
    p = AUDIT_DIR / "verification-report.md"
    p.write_text(report_md, encoding="utf-8")
    written.append(p)

    # 机器可读 JSON
    payload = {
        "run_date": run_date,
        "topics_total": after.topics_total,
        "metrics_before": asdict(before),
        "metrics_after": asdict(after),
        "findings": [asdict(f) for f in findings],
        "repairs": [asdict(r) for r in repairs],
        "verification": ver,
    }
    p = AUDIT_DIR / "info-quality.json"
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(p)

    # 累计修复历史（跨运行追加，便于周期审计）
    if repairs:
        hist = AUDIT_DIR / "repair-history.md"
        entry = f"## {run_date}：自动修复 {len(repairs)} 条\n\n" + md_table(rows) + "\n"
        if hist.exists():
            with hist.open("a", encoding="utf-8") as fh:
                fh.write(entry)
        else:
            hist.write_text("# 信息质量修复历史（累计）\n\n" + entry, encoding="utf-8")
        written.append(hist)
    return written


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def _merge_findings(base: list[Finding], latest: list[Finding]) -> list[Finding]:
    """把多轮返工的复评结果合并回首轮清单，保证评估台账 / 遗留项口径完整。

    以首轮发现为骨架：仍存在的更新级别 / 详情 / 状态；已消失的按「已修复」记；
    首轮之后新出现的追加。键 = (编号, 路径, 位置, 详情)。
    """
    def _key(f: Finding) -> tuple:
        return (f.code, f.path, f.location, f.detail)

    latest_by_key = {_key(f): f for f in latest}
    out: list[Finding] = []
    for f in base:
        nf = latest_by_key.get(_key(f))
        if nf is None:
            if f.status == "open":
                f.status = "fixed"
        else:
            f.level, f.detail, f.status = nf.level, nf.detail, nf.status
        out.append(f)
    seen = {_key(f) for f in out}
    for f in latest:
        if _key(f) not in seen:
            out.append(f)
    return out


def run(apply: bool = False, write: bool = True) -> int:
    run_date = date.today().isoformat()
    units = scan_topics()
    if not units:
        print("[ERROR] 未扫描到任何主题目录")
        return 1

    findings, before = evaluate(units)
    repairs: list[Repair] = []
    after_findings = findings
    after = before
    rounds = 0

    if apply:
        import copy
        before_findings = copy.deepcopy(findings)
        current = findings
        # 阶段 3 + 阶段 4：修复 → 复评；仍有 P0/P1 且本轮有实际修复时返工，
        # 最多 MAX_REWORK_ROUNDS 轮（仍不达标转人工裁决，由退出码 1 告警）。
        while rounds < MAX_REWORK_ROUNDS:
            rounds += 1
            made = repair(current, units)
            repairs.extend(made)
            units = scan_topics()
            current, after = evaluate(units)
            open_p0p1 = [f for f in current
                         if f.status == "open" and f.level in ("P0", "P1")]
            if not made or not open_p0p1:
                break
        after_findings = _merge_findings(findings, current)
        ver = verify(before, before_findings, after_findings, after, repairs)
    else:
        ver = {"checks": {}, "passed": False, "before": asdict(before),
               "after": asdict(before), "open_after": []}

    # 控制台摘要
    print(f"信息质量评估：{after.topics_total} 个主题")
    print(f"  必需要素覆盖率 {after.required_coverage:.1%}（门槛 {THRESH_REQUIRED_COVERAGE:.0%}）")
    print(f"  来源标注覆盖率 {after.source_coverage:.1%}（门槛 {THRESH_SOURCE_COVERAGE:.0%}）")
    print(f"  语义目标完成度 {after.semantic_completion:.1%}（向 100% 目标，单独公示；程序化门槛不变）")
    print(f"  重复冗余率 {after.dup_ratio:.1%}（门槛 {THRESH_DUP_RATIO:.0%}）")
    print(f"  跨报告事实重复率 {after.fact_dup_ratio:.1%}（门槛 {THRESH_FACT_DUP:.0%}）")
    print(f"  空模块占比 {after.empty_module_ratio:.1%}（门槛 {THRESH_EMPTY_MODULE:.0%}）")
    print(f"  交叉引用有效率 {after.cite_valid_ratio:.1%}（门槛 100%）")
    print(f"  问题：P0 {after.findings_by_level['P0']} / P1 {after.findings_by_level['P1']} / P2 {after.findings_by_level['P2']}")
    if apply:
        print(f"  自动修复 {len(repairs)} 条（返工 {rounds} 轮，上限 {MAX_REWORK_ROUNDS} 轮）；"
              f"验证{'全部通过' if ver['passed'] else '存在未通过项'}")

    if write:
        paths = write_reports(after_findings, repairs, before, after, ver, run_date)
        print("  报告已写入：" + ", ".join(_rel(p) for p in paths))

    open_p0 = sum(1 for f in after_findings if f.status == "open" and f.level == "P0")
    open_p1 = sum(1 for f in after_findings if f.status == "open" and f.level == "P1")
    open_p2 = sum(1 for f in after_findings if f.status == "open" and f.level == "P2")
    if open_p0 or open_p1:
        print(f"[ALERT] 存在 P0/P1 遗留 {open_p0 + open_p1} 项，需人工介入")
        return 1
    if open_p2:
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="信息质量全量评估与闭环修复")
    ap.add_argument("--apply", action="store_true", help="评估 + 自动修复 + 复评")
    ap.add_argument("--check", action="store_true", help="仅检查，不写报告文件")
    args = ap.parse_args()
    return run(apply=args.apply, write=not args.check)

# ── 公开接口别名（架构优化方向 F / I-6）──
# 跨模块复用统一走公开名；下划线旧名保留为别名，兼容既有内部调用。
live_table = _live_table
read = _read
report_value_rows = _report_value_rows
significant_numbers = _significant_numbers
fact_units = _fact_units
has_source = _has_source


if __name__ == "__main__":
    sys.exit(main())
