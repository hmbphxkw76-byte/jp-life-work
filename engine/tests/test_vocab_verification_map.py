"""``verification-retention-map.json`` 守卫（B3 / 核验闭环第一批）。

锁定两条不变量：
1. 全库每条「部分核验」词条的**分类**都必须落在保留口径映射内（无未映射 = 无需临时裁定）；
2. 映射的 ``coverage`` 计数与实测一致（防止基线数字漂移）。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "vocabulary" / "script"))

import vocab_tool  # noqa: E402

CONFIG = ROOT / "engine" / "vocabulary" / "config"


def _all_terms():
    cfg = vocab_tool.load_config(CONFIG / "topics.json")
    for tid in cfg["topics"]:
        tmeta = vocab_tool.resolve_topic(cfg, tid)
        terms, _ = vocab_tool.load_storage(tmeta["storage"])
        yield from terms


class VerificationRetentionMapCase(unittest.TestCase):
    def setUp(self) -> None:
        self.map = json.loads((CONFIG / "verification-retention-map.json").read_text(encoding="utf-8"))
        self.mapped = set(self.map["categories"])

    def test_every_partial_category_is_mapped(self) -> None:
        cats = {t.get("category", "") for t in _all_terms()
                if t.get("verification") == "部分核验"}
        self.assertTrue(cats, "应存在部分核验条目")
        self.assertEqual(sorted(cats - self.mapped), [], "存在未映射的部分核验分类")

    def test_coverage_matches_measured(self) -> None:
        cov = self.map["coverage"]
        counted: dict[str, int] = {}
        for t in _all_terms():
            counted[t.get("verification", "?")] = counted.get(t.get("verification", "?"), 0) + 1
        self.assertEqual(cov["terms_total"], sum(counted.values()))
        self.assertEqual(cov["verified_terms"], counted.get("已核验", 0))
        self.assertEqual(cov["partial_terms"], counted.get("部分核验", 0))
        self.assertEqual(cov["pending_terms"], counted.get("待核实", 0))


if __name__ == "__main__":
    unittest.main()
