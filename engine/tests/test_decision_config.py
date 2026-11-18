"""``engine/config/decision-tools.json`` 配置化守卫（P1-10）。

覆盖：
- 配置 schema 与必需键；
- 决策工具从配置取值（财务模型 / 待核实闭环）；
- **硬编码漂移守卫**——工具源码中不得再出现配置项的字面量；
- ``load_decision_config`` 的缺失 / 损坏 / schema 版本不符分支。
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import _common  # noqa: E402


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


pfm = _load("personal_finance_model", "engine/tools/personal_finance_model.py")
pv = _load("pending_verification", "engine/tools/pending_verification.py")


class ConfigSchemaCase(unittest.TestCase):
    def test_schema_version(self) -> None:
        self.assertEqual(_common.load_decision_config()["schema_version"],
                         _common.DECISION_CONFIG_SCHEMA)

    def test_required_keys(self) -> None:
        cfg = _common.load_decision_config()
        self.assertIn("personal_finance_model", cfg)
        self.assertIn("pending_verification", cfg)
        fin = cfg["personal_finance_model"]
        for k in ("representative_rent_jpy", "social_insurance_rate", "sources"):
            self.assertIn(k, fin)
        for k in ("income", "living", "initial_months", "driving", "intermediary", "exam"):
            self.assertIn(k, fin["sources"])
        for k in ("default_deadline", "near_window_days"):
            self.assertIn(k, cfg["pending_verification"])


class ConsumptionCase(unittest.TestCase):
    def test_finance_model_uses_config(self) -> None:
        cfg = _common.load_decision_config()["personal_finance_model"]
        self.assertEqual(pfm.REPRESENTATIVE_RENT, cfg["representative_rent_jpy"])
        self.assertEqual(pfm.SOCIAL_INSURANCE_RATE, cfg["social_insurance_rate"])
        self.assertEqual(pfm.SOURCES["income"][0], cfg["sources"]["income"][0])

    def test_pending_verification_uses_config(self) -> None:
        cfg = _common.load_decision_config()["pending_verification"]
        self.assertEqual(pv.DEFAULT_DEADLINE, cfg["default_deadline"])
        self.assertEqual(pv.NEAR_WINDOW_DAYS, cfg["near_window_days"])


class DriftGuardCase(unittest.TestCase):
    """工具源码不得再写死配置项字面量（否则配置改动不生效）。"""

    def test_no_hardcoded_literals(self) -> None:
        targets = {
            "engine/tools/personal_finance_model.py":
                ["62_500", "62500", "0.15"],
            "engine/tools/pending_verification.py":
                ['"2026-12-31"', "<= 30"],
        }
        for rel, needles in targets.items():
            text = (ROOT / rel).read_text(encoding="utf-8")
            for n in needles:
                self.assertNotIn(n, text, f"{rel} 出现硬编码字面量 {n}，应改用 decision-tools.json")


class LoaderErrorCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _patch(self, path: Path):
        return mock.patch.object(_common, "DECISION_CONFIG_PATH", path)

    def test_missing(self) -> None:
        with self._patch(self.root / "nope.json"):
            with self.assertRaises(ValueError):
                _common.load_decision_config()

    def test_corrupt(self) -> None:
        p = self.root / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        with self._patch(p):
            with self.assertRaises(ValueError):
                _common.load_decision_config()

    def test_wrong_schema(self) -> None:
        p = self.root / "wrong.json"
        p.write_text(json.dumps({"schema_version": "9.9"}), encoding="utf-8")
        with self._patch(p):
            with self.assertRaises(ValueError):
                _common.load_decision_config()

    def test_ok(self) -> None:
        p = self.root / "ok.json"
        p.write_text(json.dumps({"schema_version": "1.0", "x": 1}), encoding="utf-8")
        with self._patch(p):
            self.assertEqual(_common.load_decision_config()["x"], 1)


if __name__ == "__main__":
    unittest.main()
