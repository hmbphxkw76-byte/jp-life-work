"""工作区标准化清理（engine/scripts/cleanup_workspace.py）测试。

hermetic：全部在临时目录构造残留，不触碰真实仓库工作区；
唯一例外是「已跟踪文件保护」用例，在临时目录里搭最小 git 仓库。
"""
from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "engine" / "scripts" / "cleanup_workspace.py"

spec = importlib.util.spec_from_file_location("cleanup_workspace", TOOL)
assert spec and spec.loader
cw = importlib.util.module_from_spec(spec)
sys.modules["cleanup_workspace"] = cw
spec.loader.exec_module(cw)


class TempCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _mk(self, rel: str, content: bytes = b"x") -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return p

    def _run(self, *args: str):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cw.main([*args, "--root", str(self.root)])
        return code, out.getvalue(), err.getvalue()


class TestCollectAndClean(TempCase):
    def test_collects_all_kinds(self):
        self._mk("__pycache__/mod.cpython-312.pyc")
        self._mk("engine/tests/__pycache__/x.pyc")
        self._mk(".pytest_cache/CACHEDIR.TAG")
        self._mk("tools/probe.tmp")
        self._mk("tools/.DS_Store")
        self._mk("engine/vocabulary/data/sync-backups/business-config.md.bak")
        self._mk("engine/vocabulary/data/sync.log", b"[info] x\n")

        items = cw.collect_residue(self.root)
        rels = {i.path.relative_to(self.root).as_posix() for i in items}
        self.assertIn("__pycache__", rels)
        self.assertIn("engine/tests/__pycache__", rels)
        self.assertIn(".pytest_cache", rels)
        self.assertIn("tools/probe.tmp", rels)
        self.assertIn("tools/.DS_Store", rels)
        self.assertIn("engine/vocabulary/data/sync-backups", rels)
        self.assertIn("engine/vocabulary/data/sync.log", rels)
        # 缓存目录整体回收，不逐文件列出
        self.assertNotIn("__pycache__/mod.cpython-312.pyc", rels)

    def test_clean_removes_residue_and_reports(self):
        self._mk("__pycache__/m.pyc")
        self._mk("engine/vocabulary/data/sync.log", b"log")

        code, out, _ = self._run()
        self.assertEqual(code, 0)
        self.assertIn("已清理", out)
        self.assertFalse((self.root / "__pycache__").exists())
        self.assertFalse((self.root / "engine/vocabulary/data/sync.log").exists())

    def test_generated_dirs_removed_even_when_empty(self):
        (self.root / "engine/vocabulary/data/topic-backups").mkdir(parents=True)
        code, out, _ = self._run()
        self.assertEqual(code, 0)
        self.assertIn("generated-dir 1", out)
        self.assertFalse((self.root / "engine/vocabulary/data/topic-backups").exists())

    def test_source_and_reports_untouched(self):
        self._mk("engine/tools/validate.py")
        self._mk("docs/CI.md")
        self._mk("reports/2026-11-x.md")
        self._mk("AGENTS.md")
        code, _, _ = self._run()
        self.assertEqual(code, 0)
        for rel in (
            "engine/tools/validate.py",
            "docs/CI.md",
            "reports/2026-11-x.md",
            "AGENTS.md",
        ):
            self.assertTrue((self.root / rel).exists(), rel)

    def test_log_rule_scoped_to_vocab_data(self):
        """日志清理只针对 engine/vocabulary/data，不误删其他目录的同名文件。"""
        self._mk("docs/notes.log")
        self._mk("engine/report-audits/run.log")
        items = cw.collect_residue(self.root)
        rels = {i.path.relative_to(self.root).as_posix() for i in items}
        self.assertNotIn("docs/notes.log", rels)
        self.assertNotIn("engine/report-audits/run.log", rels)

    def test_coverage_artifacts_scoped_without_hitting_coveragerc(self):
        """覆盖率数据纳入清理，但不得误删配置文件 .coveragerc。"""
        self._mk(".coverage", b"data")
        self._mk(".coverage.12345", b"data")
        coveragerc = self._mk(".coveragerc", b"[run]\n")
        items = cw.collect_residue(self.root)
        rels = {i.path.relative_to(self.root).as_posix() for i in items}
        self.assertIn(".coverage", rels)
        self.assertIn(".coverage.12345", rels)
        self.assertNotIn(".coveragerc", rels)
        self.assertTrue(coveragerc.exists())


class TestCheckAndDryRun(TempCase):
    def test_check_flags_residue_with_exit_1(self):
        self._mk("__pycache__/m.pyc")
        code, out, _ = self._run("--check")
        self.assertEqual(code, 1)
        self.assertIn("发现残留", out)
        self.assertIn("__pycache__", out)
        self.assertTrue((self.root / "__pycache__").exists(), "check 模式不得删除")

    def test_check_clean_returns_0(self):
        code, out, _ = self._run("--check")
        self.assertEqual(code, 0)
        self.assertIn("干净", out)

    def test_dry_run_does_not_delete(self):
        self._mk("__pycache__/m.pyc")
        code, out, _ = self._run("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("dry-run", out)
        self.assertTrue((self.root / "__pycache__").exists())

    def test_dry_run_clean_is_noop(self):
        code, out, _ = self._run("--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("无待清理项", out)


class TestTrackedProtection(TempCase):
    """已入库文件 / 目录不得被清理脚本删除。"""

    def _git(self, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=True,
            capture_output=True,
            env={
                "PATH": __import__("os").environ.get("PATH", ""),
                "GIT_CONFIG_NOSYSTEM": "1",
                "HOME": str(self.root),
            },
        )

    def test_tracked_file_skipped(self):
        self._git("init", "-q")
        keep = self._mk("engine/vocabulary/data/sync.log", b"tracked\n")
        self._git("add", "-A")
        self._git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x")

        items = cw.collect_residue(self.root)
        rels = {i.path.relative_to(self.root).as_posix() for i in items}
        self.assertNotIn("engine/vocabulary/data/sync.log", rels)
        self.assertTrue(keep.exists())

    def test_untracked_file_still_collected(self):
        self._git("init", "-q")
        self._mk("engine/vocabulary/data/sync.log", b"untracked\n")
        items = cw.collect_residue(self.root)
        rels = {i.path.relative_to(self.root).as_posix() for i in items}
        self.assertIn("engine/vocabulary/data/sync.log", rels)

    def test_tracked_dir_skipped(self):
        self._git("init", "-q")
        self._mk(".pytest_cache/keep.txt")
        self._git("add", "-A")
        self._git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x")
        items = cw.collect_residue(self.root)
        rels = {i.path.relative_to(self.root).as_posix() for i in items}
        self.assertNotIn(".pytest_cache", rels)


class TestCliContract(TempCase):
    def test_missing_root_errors(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cw.main(["--root", str(self.root / "nope")])
        self.assertEqual(code, 1)
        self.assertIn("根目录不存在", err.getvalue())

    def test_quiet_single_line(self):
        self._mk("__pycache__/m.pyc")
        code, out, _ = self._run("--quiet")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 1)


class TestCiWiring(unittest.TestCase):
    """CI 契约：每条工作流必须接入「前置 + 收尾（always）」清理，防止漏接。"""

    WF = ROOT / ".github" / "workflows"
    PRE = "- uses: ./.github/actions/workspace-cleanup\n        with:\n          mode: ci"
    POST = "- uses: ./.github/actions/workspace-cleanup\n        if: always()\n        with:\n          mode: ci"

    def test_every_workflow_wired_pre_and_post(self):
        files = sorted(self.WF.glob("*.yml"))
        self.assertTrue(files, "未找到任何工作流")
        for f in files:
            text = f.read_text(encoding="utf-8")
            self.assertIn(self.PRE, text, f"{f.name} 缺前置清理")
            self.assertIn(self.POST, text, f"{f.name} 缺收尾（always）清理")

    def test_composite_action_present(self):
        self.assertTrue(
            (ROOT / ".github" / "actions" / "workspace-cleanup" / "action.yml").is_file()
        )

    def test_validate_has_hygiene_job(self):
        text = (self.WF / "validate.yml").read_text(encoding="utf-8")
        self.assertIn("workspace-hygiene:", text)
        self.assertIn("check-only: 'true'", text)

    def test_logs_are_ignored(self):
        """运行日志不入库：.gitignore 必须覆盖 vocab data 下的 *.log。"""
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("engine/vocabulary/data/*.log", text)


if __name__ == "__main__":
    unittest.main()
