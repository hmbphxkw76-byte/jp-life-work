"""注册表生成器测试（架构优化方向 A / I-9，T3.2 / T3.3）。"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import generate_registry  # noqa: E402


class TestRegistryGenerator(unittest.TestCase):
    def test_scan_nonempty(self):
        reg = generate_registry.scan()
        self.assertGreater(len(reg["tools"]), 0)
        self.assertGreater(len(reg["types"]), 0)
        self.assertGreater(len(reg["topics"]), 0)
        self.assertGreater(len(reg["workflows"]), 0)

    def test_check_passes(self):
        proc = subprocess.run(
            [sys.executable, "engine/tools/generate_registry.py", "--check"],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_write_is_idempotent(self):
        before = generate_registry.REGISTRY_JSON.read_text(encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "engine/tools/generate_registry.py", "--write"],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        after = generate_registry.REGISTRY_JSON.read_text(encoding="utf-8")
        self.assertEqual(before, after, "重复生成 registry.json 应无变化")
