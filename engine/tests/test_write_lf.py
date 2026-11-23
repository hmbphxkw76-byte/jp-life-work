#!/usr/bin/env python3
"""test_write_lf.py — 工具写回换行口径守卫（LF）。

背景：Windows 下 ``Path.write_text()`` / ``open(..., "w")`` 默认 ``newline=None``，
会把 ``\\n`` 翻译成 ``os.linesep``（CRLF），使跟踪文件在仓库里变成假 dirty，
并阻塞 ``workflow_guard.py sync``。仓库换行口径的单一事实源是
``.gitattributes`` 的 ``* text=auto eol=lf``。

本测试锁定两个已确认的写回点产出字节级 LF：
- ``engine/tools/generate_registry.py``（registry.json + ``engine/tools/README.md``）
- ``engine/vocabulary/script/sync_vocab.py``（sync-state.json）
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_DIR / "tools"))
sys.path.insert(0, str(ENGINE_DIR / "vocabulary" / "script"))

import generate_registry  # noqa: E402
import sync_vocab  # noqa: E402

# 合法的占位表格行：满足 write() 内 verify() 的表头格式校验（≥5 列）。
_PLACEHOLDER_ROW = "| TOOL | 名称 | 说明 | 状态 | engine/tools/tool.py |\n"


class TestWriteLf(unittest.TestCase):
    def test_generate_registry_write_emits_lf(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            # scan() 会读取 ROOT/engine/report_templates/compliance-rules.json；重定向 ROOT 时
            # 提供最小可用副本，其余扫描面（工具 / 主题 / 工作流）为空即可。
            rules_dir = tmp / "engine" / "report_templates"
            rules_dir.mkdir(parents=True)
            (rules_dir / "compliance-rules.json").write_text(
                '{"types": {}}', encoding="utf-8", newline=""
            )
            registry = tmp / "registry.json"
            readme = tmp / "README.md"
            readme.write_text(
                "<!-- REGISTRY:BEGIN -->" + _PLACEHOLDER_ROW + "<!-- REGISTRY:END -->\n",
                encoding="utf-8",
                newline="",
            )
            orig_registry, orig_readme, orig_root = (
                generate_registry.REGISTRY_JSON,
                generate_registry.README,
                generate_registry.ROOT,
            )
            generate_registry.REGISTRY_JSON = registry
            generate_registry.README = readme
            generate_registry.ROOT = tmp
            try:
                generate_registry.write()
            finally:
                generate_registry.REGISTRY_JSON = orig_registry
                generate_registry.README = orig_readme
                generate_registry.ROOT = orig_root

            self.assertNotIn(b"\r", registry.read_bytes(), "registry.json 含 CR（应为 LF）")
            self.assertNotIn(b"\r", readme.read_bytes(), "engine/tools/README.md 含 CR（应为 LF）")

    def test_sync_vocab_dump_json_emits_lf(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "sync-state.json"
            sync_vocab.dump_json(target, {"topic": "demo", "entries": {}})
            self.assertNotIn(b"\r", target.read_bytes(), "sync-state.json 含 CR（应为 LF）")


if __name__ == "__main__":
    unittest.main()
