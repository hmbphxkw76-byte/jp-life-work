#!/usr/bin/env python3
"""source_normalize.py — 来源字段归一化单一事实源（n25）。

供 ``source_check`` 与后续信源批评（n21）、证据强度（n22）复用；
其他工具不得再各写一套机构名 / URL / 日期归一化规则。

纯函数、无副作用；全部做 NFKC 归一以对齐日语全角字符。
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


def normalize_year(text: str) -> str:
    """时点年份归一：优先西历 4 位年；否则日本年号 N 年；无则空串。"""
    if not text:
        return ""
    s = unicodedata.normalize("NFKC", str(text))
    m = _WESTERN_YEAR.search(s)
    if m:
        return m.group(0)
    m = _ERA_YEAR.search(s)
    if m:
        return f"{m.group(1)}{int(m.group(2))}年"
    return ""


def extract_year(text: str) -> str:
    """兼容旧行为：返回原始时点串（西历 4 位年或「年号 + 数字」），供 ``year`` 字段。

    与 ``normalize_year`` 的区别：保留原始表记（如「令和8」），不做年号补全。
    """
    if not text:
        return ""
    s = unicodedata.normalize("NFKC", str(text))
    m = _WESTERN_YEAR.search(s)
    if m:
        return m.group(0)
    m = _ERA_YEAR.search(s)
    if m:
        return f"{m.group(1)}{m.group(2)}"
    return ""
