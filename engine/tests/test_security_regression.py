"""安全回归测试（架构优化方向 G / I-10，T3.4）。

覆盖三类关键安全属性：
- 内容指纹剥离「已审计」标识（防自锁）；
- ``<script>`` 嵌入前 ``<`` 转义（防 ``</script>`` 逃逸）；
- 报告路径越界防护。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import audit_badge  # noqa: E402
import audit_registry  # noqa: E402
import build_hub  # noqa: E402


class TestSecurityRegression(unittest.TestCase):
    def test_fingerprint_ignores_audit_badge(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.md"
            p.write_text("# 标题\n正文\n", encoding="utf-8")
            fp1 = audit_registry.content_fingerprint(p)
            p.write_text("# 标题\n正文\n\n> **已审计** abc\n", encoding="utf-8")
            fp2 = audit_registry.content_fingerprint(p)
            self.assertEqual(fp1, fp2, "注入已审计标识不应改变内容指纹")

    def test_embed_json_escapes_script_close(self):
        out = build_hub.embed_json({"x": "</script><script>alert(1)</script>"})
        self.assertNotIn("</script>", out)
        self.assertIn("\\u003c/script>", out)

    def test_audit_badge_rejects_outside_path(self):
        with self.assertRaises(SystemExit):
            audit_badge._targets(False, "../outside.md")
