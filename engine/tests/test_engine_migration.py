"""引擎层迁移守卫（SRC→ENGINE，方案 §5 / §9）。

迁移（2026-11-17）把 `src/` 整体迁至 `engine/`、根 `tools/` 迁至 `engine/scripts/`。
本守卫固化「纯路径迁移」的终态，防止回潮：

1. 目录终态：`engine/` 存在；`src/` 与根 `tools/` 不存在；
2. 引擎识别：`_common.SKIP_TOP` 含 `engine` 且不含 `src`；`TYPE_RE` 匹配 `engine/report_templates/`；
3. 主题数：`iter_business_dirs()` 恒为 21（防 `engine/vocabulary` 误判为业务线）；
4. 深度推导：各模块 `parents[N]` 推导出的 `ROOT` 必须等于仓库根（防漏改）；
5. 活引用：`git grep "src/"` 在代码 / CI / 配置 / 文档中清零
   （仅白名单：本迁移规格书、比对脚本自身及其映射测试、脚本 README 的映射说明）。

运行：python -m unittest discover -s engine/tests
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

from _common import ROOT as CROOT, SKIP_TOP, TYPE_RE, iter_business_dirs  # noqa: E402

# `git grep "src/"` 的合法残留白名单（历史规格 / 映射表本身），见方案 §3.5 与附录 B。
SRC_WHITELIST = {
    "docs/引擎层迁移方案-2026-11-17.md",     # 本迁移唯一事实源（含旧→新映射表）
    "engine/scripts/verify_report_parity.py",  # 归一化比对脚本（含映射表）
    "engine/tests/test_verify_report_parity.py",  # 映射表的单元测试
    "engine/scripts/README.md",               # 比对工具说明（描述旧→新映射）
}


def _git_grep(pattern: str) -> list[str]:
    """返回命中 `pattern` 的跟踪文件相对路径（core.quotepath=false）。"""
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "grep", "-l", "-e", pattern],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode not in (0, 1):  # 1 = 无命中
        raise RuntimeError(f"git grep 失败：{out.stderr}")
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


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
        hits = set(_git_grep("src/"))
        hits = {h for h in hits if "/reports/" not in h}  # §3.5 报告正文留痕
        leftover = hits - SRC_WHITELIST
        self.assertEqual(
            leftover, set(),
            "存在非白名单的 src/ 活引用：" + ", ".join(sorted(leftover)),
        )

    def test_no_src_string_constant(self) -> None:
        leftover = set(_git_grep('"src"')) - SRC_WHITELIST
        self.assertEqual(leftover, set(), "存在 \"src\" 代码常量：" + ", ".join(sorted(leftover)))


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
