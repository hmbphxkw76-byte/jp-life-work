"""增量生成 POC 测试（架构优化方向 D / I-5，T2.4 / T2.5）。

- 变更筛选：仅选中变更的月度报告 md，排除非报告文件；
- 等价性：增量选择是全部报告的子集；
- 基准：``--bench`` 输出全量 vs 增量耗时对比 JSON。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import incremental_build  # noqa: E402
from _common import ROOT as CROOT  # noqa: E402


class TestIncrementalBuild(unittest.TestCase):
    def test_changed_reports_filters_non_reports(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "01-x" / "reports").mkdir(parents=True)
            (repo / "01-x" / "reports" / "2026-11-x.md").write_text("# x\n", encoding="utf-8")
            (repo / "README.md").write_text("x\n", encoding="utf-8")
            for args in (["init"], ["add", "-A"],
                         ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init"]):
                subprocess.run(["git", *args], cwd=repo, capture_output=True)
            (repo / "01-x" / "reports" / "2026-11-x.md").write_text("# y\n", encoding="utf-8")
            (repo / "README.md").write_text("y\n", encoding="utf-8")
            old = incremental_build.ROOT
            incremental_build.ROOT = repo
            try:
                self.assertEqual(
                    incremental_build.changed_reports("HEAD"),
                    ["01-x/reports/2026-11-x.md"],
                )
            finally:
                incremental_build.ROOT = old

    def test_changed_is_subset_of_all(self):
        allr = set(incremental_build.all_reports())
        changed = set(incremental_build.changed_reports("HEAD"))
        self.assertTrue(changed <= allr, f"增量选择越出全量集合：{sorted(changed - allr)}")

    def test_md2html_changed_flag(self):
        proc = subprocess.run(
            [sys.executable, "engine/tools/md2html.py", "--changed"],
            cwd=str(CROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("无变更报告", proc.stdout)

    def test_bench_output_shape(self):
        proc = subprocess.run(
            [sys.executable, "engine/tools/incremental_build.py", "--bench"],
            cwd=str(CROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        # 无变更报告时直接退出，不产生 JSON；有则须含对比字段
        if proc.returncode == 0 and proc.stdout.strip().startswith("{"):
            data = json.loads(proc.stdout.strip().splitlines()[-1])
            self.assertIn("incremental_sec", data)
            self.assertIn("full_sec", data)
        else:
            self.assertIn("无变更报告", proc.stdout)
