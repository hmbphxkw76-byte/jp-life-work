#!/usr/bin/env python3
"""source_normalize.py — 来源字段归一化与分类单一事实源（n25；P0-P2 升级）。

供 ``source_check`` 与后续信源批评（n21）、证据强度（n22）复用；
其他工具不得再各写一套机构名 / URL / 日期 / 分组 / 独立性归一化规则。

纯函数、无副作用；全部做 NFKC 归一以对齐日语全角字符。

P0-1：``extract_year`` / ``normalize_year`` 先剥离 URL 再取年，
避免 URL 中的数字 ID（如 ``001471906.pdf``）被误判为年份；
``year_is_plausible`` 提供时点合理性判据（P2-6）。

P1-3 / P1-4 / P2-7：来源分组受控词表 ``GROUP_VOCAB`` + ``normalize_group``、
独立性判定 ``classify_independence``、权威等级 ``authority_grade``；
``detect_language`` 支撑 P1-5（日本官方中文页口径）。
"""
from __future__ import annotations

import re
import unicodedata

# URL 尾部常见标点（中日文），避免把句号 / 括号计入链接
_URL_TRAIL = ").,，。；;、》」』】"
# 机构名修饰分隔（「· 2026」「・令和 8 年」等）
_ORG_SEP = re.compile(r"\s*[·・]\s*")
_WS = re.compile(r"\s+")
# 西历 4 位年
_WESTERN_YEAR = re.compile(r"(?:19|20)\d{2}")
# 日本年号：令和 / 平成 / 昭和 N 年（「年」可省略，兼容「令和 8-07-13」）
_ERA_YEAR = re.compile(r"(令和|平成|昭和)\s*(\d{1,2})\s*年?")
# URL（含 markdown 链接内地址）——取年前先剥离，避免 URL 数字 ID 误判为年份。
# 停在空白 / 右括号 / 右方括号，避免把紧随的 ``）`` / ``。`` 记年一并吞掉。
_URL_RE = re.compile(r"https?://[^\s)\]]+")

# 合理时点区间（P2-6）：超出即视为疑似 URL 数字误判
YEAR_MIN = 1990
YEAR_MAX = 2030

# 来源分组受控词表（P1-4）：规范分组 → 别名 / 关键词（按序匹配，先命中先归）。
# 目的：把 21 份报告中 39 种异构来源小节标题收敛为有限枚举，供聚合审计。
GROUP_VOCAB: dict[str, tuple[str, ...]] = {
    "内部知识库": ("内部知识库", "交叉引用", "只读引用"),
    "媒体": ("媒体", "新闻报道", "政策环境信号"),
    "平台抽样": ("平台抽样", "求人门户", "薪资调查", "行情"),
    "补充来源": ("补充来源", "新增来源", "本期核验", "登记册更新台账", "补充"),
    "官方一手": ("官方一手", "日本政府官方", "政府官方", "官方", "省厅", "e-Gov",
                 "ISA", "法务省", "外务省", "使领馆", "出入国在留管理庁", "厚生",
                 "国土交通", "気象庁", "防災庁", "国交省", "総務省", "文部科学"),
    "权威机构": ("权威机构", "权威组织", "考试", "学会", "协会", "行业团体",
                 "专业机构", "研究机构", "行业机构", "大学", "学校", "法律援助",
                 "医疗", "教学资源", "学习"),
}

# 权威等级（P2-7）：规范分组 → 等级字母
_GRADE_OF: dict[str, str] = {
    "官方一手": "A",
    "权威机构": "B",
    "补充来源": "B",
    "媒体": "C",
    "平台抽样": "D",
    "内部知识库": "X",
}

# 独立性判定关键词（P1-3）：非独立（转引 / 聚合 / 平台 / 企业 / 自引）优先，
# 命中即「非独立」；否则命中官方 / 机构 / 教育 / 域名后缀即「独立」；其余「不明」。
_NONIND_RE = re.compile(
    r"门户|挂牌|中介|媒体|转载|转引|转述|聚合|求人|招聘|样本|已回溯|排名|汇总|"
    r"recruit|career|jobs|/job|/news/|/pr/|press|github|企业 ?IR"
)
_INDEP_RE = re.compile(
    r"官方|政府|省厅|庁|委员会|协会|学会|研究|机构|团体|大学|学校|基金会|基金|"
    r"教习所|driver-license|料金|学费|go\.jp|ac\.jp|or\.jp|e-Stat|JILPT"
)


def normalize_url(url: str) -> str:
    """URL 归一：NFKC、去首尾空白与尾部标点；空值返回空串。"""
    if not url:
        return ""
    u = unicodedata.normalize("NFKC", str(url)).strip()
    return u.rstrip(_URL_TRAIL)


def normalize_org(text: str) -> str:
    """机构名归一：NFKC、去 markdown 强调、去「·」后修饰、压缩空白。"""
    if not text:
        return ""
    s = unicodedata.normalize("NFKC", str(text))
    s = re.sub(r"[*_`]", "", s)
    s = _ORG_SEP.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    return s


def strip_urls(text: str) -> str:
    """剥离 URL（含 markdown 链接内地址），供日期抽取避免 URL 数字 ID 干扰。"""
    return _URL_RE.sub(" ", str(text or ""))


# 行尾年份（容忍 URL 后紧跟的 `,2026` / `，2026。` 记法）
_TAIL_YEAR_RE = re.compile(r"((?:19|20)\d{2})[\s。．.,，;；、》」』】]*$")
# URL 中的日期路径段（如 `/2026/10/`），要求年位前为分隔符，避免 `001471906.pdf` 误判
_URL_YEAR_RE = re.compile(r"(?:^|[/_.\-])((?:19|20)\d{2})(?=[/_.\-]|$)")


def _year_raw(text: str) -> str:
    """从非 URL 文本取年时点：西历 4 位年优先，其次日本年号（保留原始表记）。"""
    s = unicodedata.normalize("NFKC", strip_urls(text))
    m = _WESTERN_YEAR.search(s)
    if m:
        return m.group(0)
    m = _ERA_YEAR.search(s)
    if m:
        return f"{m.group(1)}{m.group(2)}"
    return ""


def _year_fallback(text: str) -> str:
    """文本无年时回退：行尾年 → URL 日期路径段；仍无则空串。"""
    s = unicodedata.normalize("NFKC", str(text or ""))
    m = _TAIL_YEAR_RE.search(s)
    if m:
        return m.group(1)
    for um in _URL_RE.finditer(s):
        dm = _URL_YEAR_RE.search(um.group(0))
        if dm:
            return dm.group(1)
    return ""


def extract_year(text: str) -> str:
    """兼容旧行为：返回原始时点串（西历 4 位年或「年号 + 数字」），供 ``year`` 字段。

    与 ``normalize_year`` 的区别：保留原始表记（如「令和8」），不做年号补全。
    先剥离 URL 再取年，避免 URL 数字 ID 被误判为年份（P0-1）；
    文本无年时回退行尾年 / URL 日期路径段。
    """
    if not text:
        return ""
    return _year_raw(text) or _year_fallback(text)


def normalize_year(text: str) -> str:
    """时点年份归一：优先西历 4 位年；否则日本年号 N 年；无则空串。"""
    raw = extract_year(text)
    if not raw:
        return ""
    m = re.fullmatch(r"(令和|平成|昭和)(\d{1,2})", raw)
    if m:
        return f"{m.group(1)}{int(m.group(2))}年"
    return raw


def year_is_plausible(year: str) -> bool:
    """时点合理性（P2-6）：西历 4 位年须落在 ``YEAR_MIN..YEAR_MAX``；年号视为合理；空值交由缺年告警。"""
    if not year:
        return True
    s = unicodedata.normalize("NFKC", str(year)).strip()
    m = re.fullmatch(r"((?:19|20)\d{2})", s)
    if m:
        return YEAR_MIN <= int(m.group(1)) <= YEAR_MAX
    return bool(re.fullmatch(r"(令和|平成|昭和)\d{1,2}年?", s))


def normalize_group(text: str) -> str:
    """把来源小节标题归一到受控分组（P1-4）；未命中返回空串。"""
    s = unicodedata.normalize("NFKC", str(text or ""))
    s = re.sub(r"[*_`#]", "", s).strip()
    for canon, keys in GROUP_VOCAB.items():
        if any(k in s for k in keys):
            return canon
    return ""


def classify_independence(text: str, url: str = "", group: str = "") -> str:
    """独立性判定（P1-3）：非独立 / 独立 / 不明。"""
    s = f"{group} {text} {url}"
    if _NONIND_RE.search(s):
        return "非独立"
    if _INDEP_RE.search(s):
        return "独立"
    return "不明"


def authority_grade(group_canonical: str) -> str:
    """权威等级（P2-7）：由受控分组映射 A/B/C/D/X；未知返回空串。"""
    return _GRADE_OF.get(group_canonical, "")


def detect_language(url: str) -> str:
    """来源页面语言（P1-5）：zh / en / ja（默认 ja）。

    仅识别路径 / 参数中的语言段（如 ``/cn/``、``itpr_zh``、``/english/``），
    不把地区子域（如 ``shanghai.cn.emb-japan.go.jp``）误判为中文页。
    """
    u = unicodedata.normalize("NFKC", str(url or "")).lower()
    # 中文页：``/cn/`` / ``/zh/`` / ``/zh-CHS/`` / ``itpr_zh`` / ``xxx_cn.html``
    if re.search(r"/(cn|zh)(/|$)|/zh[-_]|itpr_zh|_cn\.", u):
        return "zh"
    if re.search(r"/(en|english)(/|$)|itpr_en|/en/", u):
        return "en"
    return "ja"
