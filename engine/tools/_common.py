"""公共模块：仓库结构识别、报告命名解析、周期计算。

所有 engine/tools/*.py 共享；纯函数部分供 tests/ 直接调用。
"""
from __future__ import annotations

import contextlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

# 仓库根目录：engine/tools/_common.py -> parents[2]
ROOT = Path(__file__).resolve().parents[2]

# 引擎层根目录（engine/report_templates）
ENGINE = ROOT / "engine"
TEMPLATE_ROOT = ENGINE / "report_templates"

# 新报告认定期间：>= 该期间视为新报告，纳入阻断级校验；历史报告由豁免清单管理。
NEW_FROM = "2026-11"

# 顶层目录中不属于「地区 / 业务主题」的目录
SKIP_TOP = {".git", ".github", "engine", "report_templates", "prompts", "tests", "docs"}

# ──────────────────────────────────────────────
# 现行命名规范：YYYY-MM-<主题slug>.md / .html（月度报告系列）
# ──────────────────────────────────────────────
# 2026-11-13 体系重构：取消基线 / 初析 / 季度等报告类型标签，全部报告按自然
# 月份聚合，统一命名「YYYY-MM-主题名称」。主题名称取目录 slug（去 NN- 编号
# 前缀，如 01-ssw-driver -> ssw-driver）。季度报告按季度末月归档（2026-Q4 ->
# 2026-12），与月度报告同一套命名 / 对比 / 展示逻辑。
MONTH_REPORT_RE = re.compile(r"^(\d{4}-(?:0[1-9]|1[0-2]))-([a-z][a-z0-9-]*)\.(html|md)$")

# 目录名 -> 主题 slug（去掉两位编号前缀）
DIR_SLUG_RE = re.compile(r"^\d{2}-(.+)$")


def topic_slug(dir_name: str) -> str:
    """业务目录名 -> 主题 slug（`01-ssw-driver` -> `ssw-driver`）。"""
    m = DIR_SLUG_RE.match(dir_name)
    return m.group(1) if m else dir_name


def detect_month_report(name: str):
    """按新命名规范识别月度报告 -> (period, slug, ext)；不匹配返回 None。

    例：'2026-11-ssw-driver.html' -> ('2026-11', 'ssw-driver', 'html')
    旧命名（baseline / initial_analysis / quarterly 等）不匹配，由
    detect_legacy_report 单独识别（仅迁移期使用）。
    """
    m = MONTH_REPORT_RE.match(name)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return None


def month_report_name(period: str, slug: str, ext: str = "md") -> str:
    """构造月度报告文件名（`2026-11` + `ssw-driver` -> `2026-11-ssw-driver.md`）。"""
    return f"{period}-{slug}.{ext}"


def quarter_to_month(period: str):
    """季度标识 -> 季度末月标识（`2026-Q4` -> `2026-12`）；非季度返回 None。"""
    m = re.fullmatch(r"(\d{4})-Q([1-4])", period or "")
    if not m:
        return None
    return f"{m.group(1)}-{(int(m.group(2)) * 3):02d}"


# ──────────────────────────────────────────────
# 历史命名（仅迁移脚本与归档读取使用；新产出不得再使用）
# ──────────────────────────────────────────────
MONTHLY_RE = re.compile(r"^(\d{4}-(?:0[1-9]|1[0-2]))_monthly\.(html|md)$")
QUARTERLY_RE = re.compile(r"^(\d{4}-Q[1-4])_quarterly\.(html|md)$")
ANNUAL_RE = re.compile(r"^(\d{4})_annual\.(html|md)$")
BASELINE_RE = re.compile(r"^(\d{4}-(?:0[1-9]|1[0-2]))_baseline(?:_report)?\.(html|md)$")
# 事件触发插刷件（日期前缀 + 自由主题名）
LEGACY_SPECIAL_RE = re.compile(
    r"^(\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]))[-_].+\.(html|md)$"
)

REPORT_RES = (
    ("monthly", MONTHLY_RE),
    ("quarterly", QUARTERLY_RE),
    ("annual", ANNUAL_RE),
    ("baseline", BASELINE_RE),
)

# 通用层根部必备文件（validate.py 使用；类型中立共享文件）
REQUIRED_TEMPLATE_FILES = (
    "prompt-generic-base.md",
    "monitoring-common-spec.md",
    "template-registry.md",
    "report-classification.md",
    "registry-schema.md",
    "compliance-rules.json",
)

# 类型模板目录：类型 ID -> 该类型必备模板（相对 report_templates/<类型ID>/）
# 与 report_templates/template-registry.md 第二节登记一致；新增类型时同步两处。
TEMPLATE_TYPE_DIRS = {
    "market-monitoring": (
        "prompt-baseline-setup-template.md",
        "prompt-monthly-monitor-template.md",
        "prompt-quarterly-analysis-template.md",
        "prompt-annual-review-template.md",
    ),
    "employment-research": (
        "prompt-baseline-setup-template.md",
        "prompt-update-template.md",
    ),
    "competitive-intelligence": (
        "prompt-baseline-setup-template.md",
        "prompt-monthly-update-template.md",
    ),
    "sentiment-monitoring": (
        "prompt-baseline-setup-template.md",
        "prompt-monthly-update-template.md",
    ),
    "consumer-research": (
        "prompt-baseline-setup-template.md",
        "prompt-study-template.md",
    ),
    "industry-research": (
        "prompt-baseline-setup-template.md",
        "prompt-annual-refresh-template.md",
    ),
    "market-sizing": (
        "prompt-baseline-setup-template.md",
        "prompt-annual-refresh-template.md",
    ),
    "investment-research": (
        "prompt-baseline-setup-template.md",
        "prompt-target-update-template.md",
    ),
    "policy-analysis": (
        "prompt-baseline-setup-template.md",
        "prompt-policy-review-template.md",
    ),
    "feasibility-study": (
        "prompt-baseline-setup-template.md",
        "prompt-study-template.md",
    ),
    "flash-commentary": (
        "prompt-baseline-setup-template.md",
        "prompt-flash-note-template.md",
    ),
    "whitepaper": (
        "prompt-baseline-setup-template.md",
        "prompt-topic-study-template.md",
    ),
}

# business-config 中的类型模板引用（如 ../../engine/report_templates/employment-research/）
TYPE_RE = re.compile(r"engine/report_templates/([a-z][a-z0-9-]*)/")

# 类型 ID -> 类型名回退表（与 template-registry.md 第二节一致；构建时解析失败启用）
TYPE_LABEL_FALLBACK = {
    "market-monitoring": "市场指标监测型",
    "employment-research": "职业就业调研型",
    "competitive-intelligence": "竞争情报监测型",
    "sentiment-monitoring": "舆情传播监测型",
    "consumer-research": "消费者·用户调研型",
    "industry-research": "行业深度研究型",
    "market-sizing": "市场规模测算与预测型",
    "investment-research": "投资分析与尽调型",
    "policy-analysis": "政策法规解读型",
    "feasibility-study": "可行性与市场进入型",
    "flash-commentary": "快评·事件点评型",
    "whitepaper": "白皮书·专题深度型",
}

# 通用层禁现的业务关键词（与 2026-11-13 重构验证口径一致）
BUSINESS_KEYWORDS = (
    "迪拜", "公寓", "Dubai", "UAE", "阿联酋", "DLD", "CBUAE", "EIBOR",
    "AED", "Bayut", "Knight Frank", "CBRE", "JLL", "Savills", "Ejari",
    "Peak Trust", "ValuStrat", "DXBinteract", "PropertyIndex",
)

# 业务主题词标记（仅扫描 report_templates/<类型ID>/**，不含根部规范）：
# 类型层出现任一即视为业务污染（如某条业务线的行业词被带入通用模板）。
BUSINESS_TOPIC_MARKERS = (
    "SSW", "司机", "卡车", "物流", "日语", "JLPT", "在留", "住民票",
    "国民健康保険", "介护", "介護", "民宿", "厂房", "网络安全", "特定技能",
)


@dataclass(frozen=True)
class Business:
    """一条业务线目录：支持单层（`NN-主题/`）与旧两层（`{地区}/{业务类型}/`）。

    单层目录时 property_type 为空串，region 即目录名。
    """

    region: str
    property_type: str = ""

    @property
    def path(self) -> Path:
        return ROOT / self.rel

    @property
    def rel(self) -> str:
        return f"{self.region}/{self.property_type}" if self.property_type else self.region


def _is_business_dir(p: Path) -> bool:
    """目录本身是否构成一条业务线（含 prompts/、reports/ 或 data/）。"""
    if not p.is_dir() or p.name.startswith("."):
        return False
    if any((p / s).is_dir() for s in ("prompts", "reports", "data")):
        return True
    return (p / "prompts" / "business-config.md").exists()


def iter_business_dirs() -> list[Business]:
    """识别所有业务线目录：单层主题目录或旧两层 `{地区}/{业务类型}`。"""
    out: list[Business] = []
    if not ROOT.exists():
        return out
    for top in sorted(ROOT.iterdir()):
        if not top.is_dir() or top.name.startswith(".") or top.name in SKIP_TOP:
            continue
        if _is_business_dir(top):
            out.append(Business(top.name))
            continue
        for prop in sorted(top.iterdir()):
            if _is_business_dir(prop):
                out.append(Business(top.name, prop.name))
    return out


def detect_report(name: str):
    """按文件名识别报告 -> (cycle, period, ext)；不匹配返回 None。

    例：'2026-11_monthly.html' -> ('monthly', '2026-11', 'html')
    仅识别历史命名（迁移期使用）；新命名请用 detect_month_report。
    """
    for cycle, rx in REPORT_RES:
        m = rx.match(name)
        if m:
            return cycle, m.group(1), m.group(2)
    return None


def detect_legacy_report(name: str):
    """识别历史命名报告 -> (kind, period, ext)；不匹配返回 None。

    kind ∈ {baseline, initial, quarterly, annual, monthly, special}。
    仅迁移脚本使用：把存量报告归入自然月并合并重命名。
    """
    det = detect_report(name)
    if det:
        return det
    m = LEGACY_SPECIAL_RE.match(name)
    if m:
        kind = "initial" if "initial_analysis" in name else "special"
        return kind, m.group(1), m.group(2)
    return None


def month_to_date(period: str) -> str:
    """月度标识 -> 代表日期（ISO，取月末）；非法返回空串。"""
    m = re.fullmatch(r"(\d{4})-(\d{2})", period or "")
    if not m:
        return ""
    y, mo = int(m.group(1)), int(m.group(2))
    if not 1 <= mo <= 12:
        return ""
    from calendar import monthrange

    return f"{y:04d}-{mo:02d}-{monthrange(y, mo)[1]:02d}"


def parse_period(s: str):
    """解析周期标识 -> (cycle, y, n)。cycle in {'month','quarter','year'}。

    '2026-11' -> ('month', 2026, 11)；'2026-Q3' -> ('quarter', 2026, 3)；
    '2026' -> ('year', 2026, None)。非法输入抛 ValueError。
    """
    m = re.fullmatch(r"(\d{4})-(\d{2})", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return "month", y, mo
    m = re.fullmatch(r"(\d{4})-Q([1-4])", s)
    if m:
        return "quarter", int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r"(\d{4})", s)
    if m:
        return "year", int(m.group(1)), None
    raise ValueError(f"无法识别的周期: {s}")


def tasks_for_period(cycle: str, y: int, n):
    """给定周期应执行的任务清单 -> [(report_cycle, y, n), ...]。

    月度期：月度任务；季首月追加该季度任务；1 月追加上一自然年年度任务。
    季度期：仅该季度。年度期：仅该年度。
    """
    if cycle == "month":
        tasks = [("monthly", y, n)]
        if n in (1, 4, 7, 10):
            tasks.append(("quarterly", y, (n - 1) // 3 + 1))
        if n == 1:
            tasks.append(("annual", y - 1, None))
        return tasks
    if cycle == "quarter":
        return [("quarterly", y, n)]
    return [("annual", y, None)]


def report_title(html_text: str) -> str:
    """从 HTML 文本提取 <title>；缺失时返回空串。"""
    m = re.search(r"<title>(.*?)</title>", html_text, re.DOTALL)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()


# ──────────────────────────────────────────────
# 原子写与路径安全（架构优化方向 B / C）
# ──────────────────────────────────────────────

def atomic_write(path, text: str, encoding: str = "utf-8") -> None:
    """原子写入：临时文件 + ``os.replace``。

    失败时清理临时文件、原文件保持不变（天然回滚），不产生半写状态。
    ``newline=""`` 保留 ``text`` 中的换行风格（CRLF / LF 不转换）。
    """
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "w", encoding=encoding, newline="") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            tmp.unlink()
        raise


def resolve_within(base, rel: str) -> Path:
    """把 ``base`` 下的相对路径解析为绝对路径，并校验其位于 ``base`` 内。

    越界抛出 :class:`ValueError`；调用方负责转换为友好错误。
    """
    base = Path(base).resolve()
    target = (base / str(rel).replace("\\", "/")).resolve()
    target.relative_to(base)
    return target


# ──────────────────────────────────────────────
# 审计产物渲染共用（去重：原 5 处 _md_table / 4 处 _link_prefix 逐字重复）
# ──────────────────────────────────────────────

def md_table(rows: list[list[str]]) -> str:
    """把二维行数据渲染为 Markdown 表格（审计类工具共用单一事实源）。"""
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def link_prefix(out_file: Path) -> str:
    """从产物文件回到仓库根的相对前缀（保证 Markdown 链接可用）。"""
    return "../" * (len(out_file.relative_to(ROOT).parts) - 1)


# ──────────────────────────────────────────────
# 端到端流水线编排：状态层（2026-11-17 任务 1）
# ──────────────────────────────────────────────
# 状态文件只存路径 / 状态 / 时间戳 / 摘要，不存正文、不存凭据。
import json  # noqa: E402

# 编排状态与快照目录（设计文档 §3.4：engine/report-audits/pipeline/）
PIPELINE_DIR = ENGINE / "report-audits" / "pipeline"

# 状态文件 schema 版本；缺失或不符即视为损坏，拒绝静默续跑（可重建）
STATE_SCHEMA_VERSION = "1.0"


def pipeline_state_path(period: str) -> Path:
    """周期 -> 状态文件路径（`state-<period>.json`）。"""
    return PIPELINE_DIR / f"state-{period}.json"


def new_state(period: str) -> dict:
    """新建空状态：仅 schema 版本、周期与空阶段表。"""
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "period": period,
        "stages": {},
        "updated": "",
    }


def load_state(period: str) -> dict:
    """读取周期状态。

    文件缺失抛 :class:`FileNotFoundError`（调用方决定冷启动 / 报错）；
    内容非合法 JSON、非对象或 ``schema_version`` 不符抛 :class:`ValueError`。
    """
    path = pipeline_state_path(period)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"状态文件损坏（非合法 JSON）：{path}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != STATE_SCHEMA_VERSION:
        actual = data.get("schema_version") if isinstance(data, dict) else type(data).__name__
        raise ValueError(
            f"状态文件 schema 版本不符：{path}（期望 {STATE_SCHEMA_VERSION}，实际 {actual}）"
        )
    return data


def save_state(period: str, state: dict) -> None:
    """原子写入周期状态（目录不存在时自动创建）。"""
    PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write(pipeline_state_path(period), json.dumps(state, ensure_ascii=False, indent=2))


# ──────────────────────────────────────────────
# 决策工具配置（硬编码外置的单一事实源）
# ──────────────────────────────────────────────

DECISION_CONFIG_PATH = ENGINE / "config" / "decision-tools.json"
DECISION_CONFIG_SCHEMA = "1.0"


def load_decision_config() -> dict:
    """读取决策工具配置（``engine/config/decision-tools.json``）。

    配置缺失 / 非合法 JSON / schema 版本不符抛 :class:`ValueError`。
    决策类工具（财务模型、待核实闭环等）的阈值与定位常量一律以此为准，
    代码内不得再写死；漂移由 ``test_decision_config`` 守卫。
    """
    try:
        data = json.loads(DECISION_CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"决策工具配置缺失：{DECISION_CONFIG_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"决策工具配置损坏（非合法 JSON）：{DECISION_CONFIG_PATH}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != DECISION_CONFIG_SCHEMA:
        actual = data.get("schema_version") if isinstance(data, dict) else type(data).__name__
        raise ValueError(
            f"决策工具配置 schema 版本不符：{DECISION_CONFIG_PATH}"
            f"（期望 {DECISION_CONFIG_SCHEMA}，实际 {actual}）"
        )
    return data

