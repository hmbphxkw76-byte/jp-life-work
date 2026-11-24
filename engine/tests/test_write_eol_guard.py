"""写回换行口径静态守卫（CRLF 假 dirty 根因闭环）。

背景：Windows 下 ``Path.write_text()`` / ``open(..., "w")`` 默认 ``newline=None``，
会把 ``\\n`` 翻译成 ``os.linesep``（CRLF），使**跟踪文件**在仓库里变成假 dirty，
阻塞 ``workflow_guard sync``。``hardening-write-lf`` / ``fix-md2html-eol`` 已修三处，
本守卫把「工具源码不得出现未受控的文本写回」固化为可执行契约。

扫描范围：``engine/tools`` / ``engine/scripts`` / ``engine/vocabulary/script`` 的 ``*.py``
（测试代码写入的是临时目录、不入库，不产生假 dirty，故不纳入）。
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = ("engine/tools", "engine/scripts", "engine/vocabulary/script")

# 文件级豁免：仅在「该写点确实不需要 LF 控制」时登记，必须写明理由与复核日期。
EXEMPTIONS: dict[str, str] = {}


def _writing_mode(call: ast.Call) -> str | None:
    """返回写模式（含 w/a/x/+）或 None。"""
    mode = None
    if call.args:
        first = call.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            mode = first.value
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant) \
                and isinstance(kw.value.value, str):
            mode = kw.value.value
    if mode is None:
        return None
    return mode if any(c in mode for c in "wax+") else None


def _targets(call: ast.Call) -> list[str]:
    """该调用涉及的写回类别：['text'] / ['open'] / ['fdopen']。"""
    fn = call.func
    if isinstance(fn, ast.Attribute):
        if fn.attr == "write_text":
            return ["text"]
        if fn.attr in ("open", "fdopen"):
            return ["open"] if _writing_mode(call) else []
    if isinstance(fn, ast.Name) and fn.id == "open":
        return ["open"] if _writing_mode(call) else []
    return []


def _has_newline(call: ast.Call) -> bool:
    return any(kw.arg == "newline" for kw in call.keywords)


def scan(root: Path = ROOT) -> list[tuple[str, int, str]]:
    """返回未受控写点：(相对路径, 行号, 说明)。"""
    bad: list[tuple[str, int, str]] = []
    for d in SCAN_DIRS:
        for f in sorted((root / d).glob("*.py")):
            rel = f.relative_to(root).as_posix()
            if rel in EXEMPTIONS:
                continue
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            lines = f.read_text(encoding="utf-8").splitlines()
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                kinds = _targets(node)
                if not kinds or _has_newline(node):
                    continue
                label = "+".join(kinds)
                bad.append((rel, node.lineno,
                            f"{label} 缺 newline= （{lines[node.lineno - 1].strip()[:60]}）"))
    return bad


class WriteEolGuardCase(unittest.TestCase):
    def test_no_uncontrolled_text_writes(self) -> None:
        bad = scan()
        self.assertEqual(bad, [], "存在未受控的文本写回（会产生 CRLF 假 dirty）：\n"
                                 + "\n".join(f"{p}:{ln} {d}" for p, ln, d in bad))

    def test_exemptions_are_documented(self) -> None:
        for rel, reason in EXEMPTIONS.items():
            self.assertTrue((ROOT / rel).is_file(), f"豁免文件不存在：{rel}")
            self.assertTrue(reason.strip(), f"豁免须写明理由：{rel}")


if __name__ == "__main__":
    unittest.main()
