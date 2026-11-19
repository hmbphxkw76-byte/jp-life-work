"""跨平台差异守卫测试（I-11 / 组 D / N13）。

CI 在 ubuntu runner 上用 **bash** 执行 ``run:``；本地维护者用 **PowerShell**。
两类环境在以下三点存在实质差异，本文件把「关键不变量」固化为可执行断言：

1. **路径分隔**：Windows 用 ``\\``、POSIX 用 ``/``。工具代码不得硬编码 Windows
   路径字面量；工作流中的 ``python engine/...`` 调用必须用正斜杠（bash 与
   PowerShell 均能识别正斜杠路径）。
2. **换行**：Windows 文本模式会把 ``\\n`` 转成 ``\\r\\n``。工作流文件必须为
   LF；``atomic_write`` 必须原样保留 LF（写作口径统一，避免平台间产物漂移）。
3. **命令可用性**：工具不得依赖 shell（``shell=True`` 在两端行为不同）；工作流
   不得使用 PowerShell 专属语法或把 PowerShell 指定为 shell；工作流引用的工具
   路径必须真实存在（防止一端能跑、另一端 file-not-found）。

本文件只新增断言，不改变运行时行为；在本地（Windows / PowerShell + bash 语义）
与 CI（ubuntu / bash）均应通过。
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLCHAIN_DIRS = (
    ROOT / "engine" / "tools",
    ROOT / "engine" / "scripts",
    ROOT / "engine" / "vocabulary" / "script",
)
WORKFLOWS_DIR = ROOT / ".github" / "workflows"

# 形如 "engine\\tools" / "C:\\repo" 的 Windows 路径字面量（不含 "\\n" 之类转义）。
WIN_PATH_RE = re.compile(r"[\"'][A-Za-z0-9_./-]+\\\\[A-Za-z0-9_./-]+[\"']|[A-Za-z]:\\\\\\\\")
# 工作流中的 python 工具调用：python[.x] engine/<path>.py
PY_INVOKE_RE = re.compile(r"python[0-9.]*\s+(engine/[A-Za-z0-9_./-]+\.py)")
POWERSHELL_ONLY_RE = re.compile(r"\$env:|Write-Host|Select-String|%ERRORLEVEL%|\bpwsh\b")


def _toolchain_sources() -> list[Path]:
    """工具链三目录下的 .py 源文件（排除字节码缓存）。"""
    out: list[Path] = []
    for d in TOOLCHAIN_DIRS:
        out.extend(p for p in d.glob("*.py") if p.is_file())
    return sorted(out)


class TestPathSeparatorInvariant(unittest.TestCase):
    """路径分隔：不得硬编码 Windows 路径，工作流调用走正斜杠。"""

    def test_no_windows_path_literals_in_toolchain(self):
        offenders: list[str] = []
        for p in _toolchain_sources():
            text = p.read_text(encoding="utf-8")
            for m in WIN_PATH_RE.finditer(text):
                offenders.append(f"{p.relative_to(ROOT).as_posix()}: {m.group(0)}")
        self.assertEqual(offenders, [], "工具链代码出现 Windows 路径字面量：" + "; ".join(offenders))

    def test_workflow_python_invocations_use_forward_slashes(self):
        checked = 0
        for wf in sorted(WORKFLOWS_DIR.glob("*.yml")):
            text = wf.read_text(encoding="utf-8")
            for m in PY_INVOKE_RE.finditer(text):
                checked += 1
                self.assertNotIn("\\", m.group(1), f"{wf.name} 的工具路径含反斜杠：{m.group(1)}")
        self.assertGreater(checked, 0, "工作流中未发现 python engine/... 调用，守卫失效")


def _repo_blob(rel: Path) -> bytes:
    """读取文件在 git 仓库中的 blob 字节（而非工作树检出）。

    Windows 本地 ``core.autocrlf=true`` 会把 LF 检出为 CRLF；CI（ubuntu）为 LF。
    平台不变量应校验**仓库事实源**（blob），否则守卫在本地必然误报。
    """
    proc = subprocess.run(
        ["git", "show", f"HEAD:{rel.as_posix()}"], cwd=str(ROOT),
        capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"无法读取仓库 blob：{rel.as_posix()}")
    return proc.stdout


class TestNewlineInvariant(unittest.TestCase):
    """换行：仓库内工作流文件 LF；atomic_write 原样保留 LF。"""

    def test_workflow_blobs_use_lf_only(self):
        for wf in sorted(WORKFLOWS_DIR.glob("*.yml")):
            raw = _repo_blob(wf.relative_to(ROOT))
            self.assertNotIn(b"\r\n", raw, f"{wf.name} 的仓库 blob 含 CRLF，平台间会漂移")

    def test_gitattributes_pins_lf(self):
        """存在 .gitattributes 且把文本文件换行钉为 LF（否则 Windows 检出会漂移）。"""
        attrs = ROOT / ".gitattributes"
        self.assertTrue(attrs.is_file(), "缺少 .gitattributes，无法固化换行口径")
        text = attrs.read_text(encoding="utf-8")
        self.assertIn("* text=auto eol=lf", text, ".gitattributes 未声明 * text=auto eol=lf")

    def test_atomic_write_preserves_lf(self):
        sys.path.insert(0, str(ROOT / "engine" / "tools"))
        from _common import atomic_write  # noqa: E402

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "sample.txt"
            atomic_write(p, "第一行\n第二行\n")
            self.assertEqual(p.read_bytes(), "第一行\n第二行\n".encode(),
                             "atomic_write 改变了换行风格（Windows 下不得转成 CRLF）")


class TestCommandAvailabilityInvariant(unittest.TestCase):
    """命令可用性：不依赖 shell / 不用 PowerShell 专属语法 / 工具路径存在。"""

    def test_no_shell_true_in_toolchain(self):
        offenders: list[str] = []
        for p in _toolchain_sources():
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                if name not in {"run", "Popen", "call", "check_call", "check_output"}:
                    continue
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        offenders.append(f"{p.relative_to(ROOT).as_posix()}:{node.lineno}")
        self.assertEqual(offenders, [], "工具链代码使用 shell=True（跨平台行为不一致）：" + "; ".join(offenders))

    def test_workflows_have_no_powershell_syntax(self):
        for wf in sorted(WORKFLOWS_DIR.glob("*.yml")):
            text = wf.read_text(encoding="utf-8")
            m = POWERSHELL_ONLY_RE.search(text)
            self.assertIsNone(m, f"{wf.name} 含 PowerShell 专属语法：{m.group(0) if m else ''}")

    def test_workflows_do_not_select_powershell_shell(self):
        for wf in sorted(WORKFLOWS_DIR.glob("*.yml")):
            text = wf.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"shell:\s*(powershell|pwsh)\b",
                                 f"{wf.name} 显式选择 PowerShell 作为 runner shell")

    def test_workflow_tool_paths_exist(self):
        missing: list[str] = []
        for wf in sorted(WORKFLOWS_DIR.glob("*.yml")):
            text = wf.read_text(encoding="utf-8")
            for m in PY_INVOKE_RE.finditer(text):
                rel = m.group(1)
                if not (ROOT / rel).is_file():
                    missing.append(f"{wf.name}: {rel}")
        self.assertEqual(missing, [], "工作流引用的工具路径不存在：" + "; ".join(missing))


if __name__ == "__main__":
    unittest.main()
