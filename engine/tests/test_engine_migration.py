"""引擎层迁移守卫（SRC→ENGINE，方案 §5 / §9）。

迁移（2026-11-17）把 `src/` 整体迁至 `engine/`、根 `tools/` 迁至 `engine/scripts/`。
本守卫固化「纯路径迁移」的终态，防止回潮：

1. 目录终态：`engine/` 存在；`src/` 与根 `tools/` 不存在；
2. 引擎识别：`_common.SKIP_TOP` 含 `engine` 且不含 `src`；`TYPE_RE` 匹配 `engine/report_templates/`；
3. 主题数：`iter_business_dirs()` 恒为 21（防 `engine/vocabulary` 误判为业务线）；
4. 深度推导：各模块 `parents[N]` 推导出的 `ROOT` 必须等于仓库根（防漏改）；
5. 活引用：`git grep "src/"` 在代码 / CI / 配置 / 文档中清零
   （仅白名单：本迁移规格书、比对脚本自身及其映射测试、脚本 README 的映射说明）；
   并扩展扫描「裸 `tools/` 路径」与「旧模块路径 `src.xxx`」，防无斜杠旧路径形态回潮。

运行：python -m unittest discover -s engine/tests
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

from _common import ROOT as CROOT, SKIP_TOP, TYPE_RE, iter_business_dirs  # noqa: E402

# 旧路径活引用的合法残留白名单（映射表本身 / 比对脚本说明 / 本守卫自身）。
# 迁移方案与历史评审为一次性文档，已清理；如再出现引用按残留处理。
SRC_WHITELIST = {
    "engine/scripts/verify_report_parity.py",  # 归一化比对脚本（含映射表）
    "engine/tests/test_verify_report_parity.py",  # 映射表的单元测试
    "engine/scripts/README.md",               # 比对工具说明（描述旧→新映射）
    "engine/tests/test_engine_migration.py",  # 本守卫自身（含待检字面量）
}

# 裸 `tools/` 扫描的结构性豁免：以下文件中的 `tools/` **不是**「旧根 tools/ 目录」引用，
# 而是 engine/ 子树示意图 / 合成 fixture，不属迁移残留（不得据此放宽其它文件）。
TOOLS_TOKEN_EXCLUDE = {
    "engine/report_templates/prompt-generic-base.md",  # engine/ 目录树中的 engine/tools 子节点
    "engine/tests/test_cleanup.py",                    # 合成 fixture 路径（自测清理器行为）
}

# 旧路径的两种「无斜杠前缀」形态：裸 `tools/` 目录引用、旧模块路径 `src.<包>`。
BARE_TOOLS_RE = re.compile(r"(?<![\w/])tools/")
LEGACY_MODULE_RE = re.compile(r"src\.(?:tests|prompts|report|search|vocabulary|tools)\b")

# 扫描时跳过的目录（版本库 / 任务工作树 / 运行期产物）
SCAN_EXCLUDE_DIRS = {
    ".git", ".worktrees", ".migration-baseline", ".catpaw", ".catpaw-",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "htmlcov",
}


def _iter_text_files():
    """产出 (rel, text)：全量文件（含未跟踪），排除版本库 / 工作树 / 运行期产物 / 报告正文。"""
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        parts = p.relative_to(ROOT).parts
        if any(part in SCAN_EXCLUDE_DIRS or part.startswith(".catpaw-")
               for part in parts):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if "/reports/" in rel:  # §3.5 报告正文留痕
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        yield rel, text


def _scan(pattern: str) -> list[str]:
    """全量扫描（含未跟踪文件）中含 `pattern` 的文本文件相对路径。

    不用 `git grep`：后者只搜已跟踪文件，会漏掉尚未 add 的新文件（本守卫自身
    即属此类），造成「本地绿 / CI 红」的假阴性。
    """
    return [rel for rel, text in _iter_text_files() if pattern in text]


def _scan_re(pattern: re.Pattern[str]) -> list[str]:
    """同 `_scan` 口径，但按正则匹配（用于裸 `tools/` 路径、旧模块路径 `src.xxx` 等形态）。"""
    return [rel for rel, text in _iter_text_files() if pattern.search(text)]


class TestLayoutTerminalState(unittest.TestCase):
    """目录终态。"""

    def test_engine_dir_exists(self) -> None:
        self.assertTrue((ROOT / "engine").is_dir(), "缺少 engine/ 引擎层目录")
        for sub in ("tools", "scripts", "report_templates", "report-audits",
                    "search", "vocabulary", "tests"):
            self.assertTrue((ROOT / "engine" / sub).is_dir(), f"缺少 engine/{sub}/")

    def test_src_and_tools_absent(self) -> None:
        self.assertFalse((ROOT / "src").exists(), "旧 src/ 尚存（应已整体迁至 engine/）")
        self.assertFalse((ROOT / "tools").exists(), "旧根 tools/ 尚存（应已迁至 engine/scripts/）")


class TestEngineRecognition(unittest.TestCase):
    """引擎识别常量（防漏改导致误判）。"""

    def test_skip_top_contains_engine_not_src(self) -> None:
        self.assertIn("engine", SKIP_TOP)
        self.assertNotIn("src", SKIP_TOP)

    def test_type_re_matches_engine_templates(self) -> None:
        self.assertIsNotNone(TYPE_RE.search("engine/report_templates/employment-research/"))
        self.assertIsNone(TYPE_RE.search("src/report_templates/employment-research/"))

    def test_business_dir_count_is_21(self) -> None:
        dirs = iter_business_dirs()
        self.assertEqual(len(dirs), 21, f"业务主题数应为 21，实际 {len(dirs)}")
        names = {b.region for b in dirs}
        self.assertNotIn("engine", names, "engine/ 被误判为业务线（SKIP_TOP 漏加 engine？）")
        self.assertNotIn("vocabulary", names)


class TestDepthDerivation(unittest.TestCase):
    """`parents[N]` 深度推导必须解析到仓库根（方案 §3.3）。"""

    def _import(self, name: str):
        import importlib
        return importlib.import_module(name)

    def test_common_root(self) -> None:
        self.assertEqual(CROOT.resolve(), ROOT.resolve())

    def test_tool_roots(self) -> None:
        for mod in ("coverage_gate", "generate_registry", "review_gate"):
            self.assertEqual(self._import(mod).ROOT.resolve(), ROOT.resolve(), mod)

    def test_migrate_audit_dir(self) -> None:
        mod = self._import("migrate_monthly_reports")
        self.assertEqual(mod.AUDIT_DIR.resolve(), (ROOT / "engine" / "report-audits").resolve())

    def test_script_roots(self) -> None:
        sys.path.insert(0, str(ROOT / "engine" / "scripts"))
        try:
            for mod in ("cleanup_workspace", "run_tests_parallel"):
                self.assertEqual(self._import(mod).ROOT.resolve(), ROOT.resolve(), mod)
        finally:
            sys.path.pop(0)


class TestNoLiveSrcReferences(unittest.TestCase):
    """`git grep "src/"` 与 `git grep '"src"'` 活引用清零（白名单除外）。"""

    def test_no_src_path_references(self) -> None:
        leftover = set(_scan("src/")) - SRC_WHITELIST
        self.assertEqual(
            leftover, set(),
            "存在非白名单的 src/ 活引用：" + ", ".join(sorted(leftover)),
        )

    def test_no_src_string_constant(self) -> None:
        leftover = set(_scan('"src"')) - SRC_WHITELIST
        self.assertEqual(leftover, set(), "存在 \"src\" 代码常量：" + ", ".join(sorted(leftover)))

    def test_no_bare_tools_dir_references(self) -> None:
        """裸 `tools/` 目录引用清零（防「根 tools/ → engine/scripts/」漏改回潮）。"""
        leftover = set(_scan_re(BARE_TOOLS_RE)) - SRC_WHITELIST - TOOLS_TOKEN_EXCLUDE
        self.assertEqual(
            leftover, set(),
            "存在非白名单的裸 tools/ 路径引用：" + ", ".join(sorted(leftover)),
        )

    def test_no_legacy_module_path_references(self) -> None:
        """旧模块路径 `src.<包>` 清零（防 `src.tests` 之类漏改）。"""
        leftover = set(_scan_re(LEGACY_MODULE_RE)) - SRC_WHITELIST
        self.assertEqual(
            leftover, set(),
            "存在旧模块路径（src.xxx）：" + ", ".join(sorted(leftover)),
        )

    def test_scan_sees_untracked_files(self) -> None:
        # 回归：扫描必须覆盖未跟踪文件（否则新文件中的旧路径引用会漏检）
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "engine").mkdir()
            (root / "engine" / "tools").mkdir()
            (root / "engine" / "scripts").mkdir()
            (root / "engine" / "report_templates").mkdir()
            (root / "engine" / "report-audits").mkdir()
            (root / "engine" / "search").mkdir()
            (root / "engine" / "vocabulary").mkdir()
            (root / "engine" / "tests").mkdir()
            (root / "leak.md").write_text("见 src/report_templates/x.md", encoding="utf-8")
            with unittest.mock.patch.object(sys.modules[__name__], "ROOT", root):
                self.assertIn("leak.md", _scan("src/"))


class TestParityScriptPresent(unittest.TestCase):
    """附录 B 比对脚本就位（阶段 7 客观判据）。"""

    def test_parity_script_exists(self) -> None:
        self.assertTrue((ROOT / "engine" / "scripts" / "verify_report_parity.py").is_file())

    def test_parity_rewrite_map_order(self) -> None:
        """映射表须长 → 短，且含 src/ 与 tools/ 兜底项。"""
        text = (ROOT / "engine" / "scripts" / "verify_report_parity.py").read_text(encoding="utf-8")
        src_idx = text.find('("src/", "engine/")')
        tools_idx = text.find('("tools/", "engine/scripts/")')
        self.assertGreater(src_idx, 0)
        self.assertGreater(tools_idx, src_idx, "tools/ 兜底项须排在 src/ 之后（防二次命中）")


if __name__ == "__main__":
    unittest.main()
