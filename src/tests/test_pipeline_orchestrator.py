"""端到端流水线编排系统测试（任务 1：状态层基础设施）。

覆盖 `_common` 状态层：状态 shape、save / load 往返、损坏 / 版本不符报错。
后续任务（触发检测 / 编排器 / 监控 / CI 接线）在同一文件追加用例。

运行：python -m unittest discover -s src/tests -v
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "prompts-tools" / "tools"))

import _common  # noqa: E402


class TestPipelineStateLayer(unittest.TestCase):
    """任务 1：状态层基础设施（schema 校验用例 ≥ 3）。"""

    def test_new_state_shape(self):
        s = _common.new_state("2026-11")
        self.assertEqual(s["schema_version"], "1.0")
        self.assertEqual(s["period"], "2026-11")
        self.assertEqual(s["stages"], {})
        self.assertEqual(s["updated"], "")

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
                _common.save_state("2026-11", _common.new_state("2026-11"))
                self.assertTrue((Path(d) / "state-2026-11.json").is_file())
                loaded = _common.load_state("2026-11")
                self.assertEqual(loaded["period"], "2026-11")
                self.assertEqual(loaded["schema_version"], "1.0")

    def test_load_corrupt_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
                (Path(d) / "state-2026-11.json").write_text("{not json", encoding="utf-8")
                with self.assertRaises(ValueError):
                    _common.load_state("2026-11")

    def test_load_version_mismatch_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with unittest.mock.patch.object(_common, "PIPELINE_DIR", Path(d)):
                p = Path(d) / "state-2026-11.json"
                bad_payloads = [
                    {"schema_version": "0.9", "period": "2026-11", "stages": {}},
                    {"period": "2026-11", "stages": {}},
                ]
                for bad in bad_payloads:
                    p.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        _common.load_state("2026-11")


if __name__ == "__main__":
    unittest.main()
