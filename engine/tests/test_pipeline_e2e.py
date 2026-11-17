"""E2E 流水线骨架（架构优化方向 E / I-8）。

以真实报告为载体，串起「生成 → 门禁 → 审计校验」：

    auto_verify --dry-run --no-submit --json
    → V1 交付物 / V2 要素 / V3 格式 / V4 一致性 / V5 数值范围

合并环节的 E2E 由 ``test_workflow_guard.py`` 覆盖；本模块附带合并层冒烟。
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = "01-ssw-driver/reports/2026-11-ssw-driver.md"


class TestPipelineE2E(unittest.TestCase):
    def test_generate_gate_audit_chain(self):
        if not (ROOT / REPORT).is_file():
            self.skipTest("报告夹具不存在")
        proc = subprocess.run(
            [sys.executable, "engine/tools/auto_verify.py",
             "--report", REPORT, "--dry-run", "--no-submit", "--json"],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        data = json.loads(proc.stdout)
        self.assertIn("results", data)
        rules = data["results"][0]["rules"]
        ids = {r["id"] for r in rules}
        self.assertTrue({"V1", "V2", "V3", "V4", "V5"} <= ids, f"规则集不完整：{sorted(ids)}")

    def test_merge_layer_smoke(self):
        proc = subprocess.run(
            [sys.executable, "engine/scripts/workflow_guard.py", "status"],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])
