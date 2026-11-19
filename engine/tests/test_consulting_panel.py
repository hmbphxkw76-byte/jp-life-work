"""``engine/tools/consulting_panel.py`` 测试（标准咨询面板）。

覆盖：
- 配置 schema 与单一事实源消费；
- PF-03 / PF-14 派生规则；
- 五问判定（空白 / 已填 / 边界）；
- 面板渲染确定性与 ``--check`` 一致性；
- 演示值必须显式标注（防止把假设值当真实个人数据）。
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

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


cp = _load("consulting_panel", "engine/tools/consulting_panel.py")


class ConfigCase(unittest.TestCase):
    def test_schema(self) -> None:
        cfg = _common.load_decision_config()["consulting_panel"]
        self.assertEqual(cfg["version"], "1.0")
        self.assertEqual(len(cfg["profile_fields"]), 17)
        for k in ("license_map", "reference", "sources"):
            self.assertIn(k, cfg)
        for k in ("initial_cost_months", "living_monthly_jpy", "driving_school_jpy",
                  "license_switch_fee_jpy", "rent_budget_ratio"):
            self.assertIn(k, cfg["reference"])

    def test_single_source_consumption(self) -> None:
        cfg = _common.load_decision_config()["consulting_panel"]
        self.assertEqual(cp.LICENSE_MAP, cfg["license_map"])
        self.assertEqual(cp.REF, cfg["reference"])
        self.assertEqual(len(cp.FIELDS), 17)


class DeriveCase(unittest.TestCase):
    def test_pf03_with_rent(self) -> None:
        d = cp.derive({"rent_budget_jpy": 60000})
        lo = 60000 * cp.REF["initial_cost_months"][0] + cp.REF["initial_cost_flat_jpy"][0]
        hi = 60000 * cp.REF["initial_cost_months"][1] + cp.REF["initial_cost_flat_jpy"][1]
        self.assertEqual(d["PF-03"]["value"], [round(lo), round(hi)])
        self.assertEqual(d["PF-03"]["status"], "已评估")

    def test_pf03_without_rent(self) -> None:
        d = cp.derive({})
        self.assertIsNone(d["PF-03"]["value"])
        self.assertIn("缺 PF-17", d["PF-03"]["status"])

    def test_pf14_map(self) -> None:
        self.assertTrue(cp.derive({"license_category": "C1"})["PF-14"]["value"].startswith("可行"))
        self.assertIn("部分", cp.derive({"license_category": "C2"})["PF-14"]["value"])
        self.assertIn("不可", cp.derive({"license_category": "B2"})["PF-14"]["value"])
        self.assertIsNone(cp.derive({})["PF-14"]["value"])


class EvaluateCase(unittest.TestCase):
    def test_blank_all_pending(self) -> None:
        prof = {k: None for k in cp.INPUT_KEYS}
        verdicts = cp.evaluate(prof, cp.derive(prof))
        self.assertEqual({v["verdict"] for v in verdicts}, {"待定"})

    def test_demo_profile(self) -> None:
        prof = dict(cp.DEMO_PROFILE)
        verdicts = cp.evaluate(prof, cp.derive(prof))
        by_id = {v["id"]: v["verdict"] for v in verdicts}
        self.assertEqual(by_id["Q2"], "是")
        self.assertEqual(by_id["Q3"], "是")
        self.assertEqual(by_id["Q4"], "是")

    def test_q1_yes_and_no(self) -> None:
        base = dict(cp.DEMO_PROFILE)
        yes = dict(base, startup_fund_jpy=2_000_000, monthly_reserve_jpy=600_000)
        self.assertEqual(cp._q1(yes, cp.derive(yes))["verdict"], "是")
        no = dict(base, startup_fund_jpy=10_000, monthly_reserve_jpy=10_000)
        self.assertEqual(cp._q1(no, cp.derive(no))["verdict"], "否")

    def test_q2_hard_fail(self) -> None:
        prof = dict(cp.DEMO_PROFILE, japanese_level="无")
        self.assertEqual(cp._q2(prof, cp.derive(prof))["verdict"], "否")


class RenderCase(unittest.TestCase):
    def test_panel_deterministic(self) -> None:
        self.assertEqual(cp.render_panel_md(), cp.render_panel_md())

    def test_panel_roundtrip(self) -> None:
        cp.OUT_PATH.write_text(cp.render_panel_md(), encoding="utf-8")
        self.assertEqual(cp.render_panel_md(), cp.OUT_PATH.read_text(encoding="utf-8"))

    def test_demo_labeled(self) -> None:
        prof = dict(cp.DEMO_PROFILE)
        out = cp.render_output_md(prof, cp.derive(prof), cp.evaluate(prof, cp.derive(prof)),
                                  cp.build_plan(prof, cp.derive(prof), []), None, demo=True)
        self.assertIn("演示", out)
        self.assertIn("非真实个人数据", out)

    def test_output_marks_missing(self) -> None:
        prof = {k: None for k in cp.INPUT_KEYS}
        out = cp.render_output_md(prof, cp.derive(prof), cp.evaluate(prof, cp.derive(prof)),
                                  cp.build_plan(prof, cp.derive(prof), []), None)
        self.assertIn("⚠ 待记录", out)


class LoadProfileCase(unittest.TestCase):
    def test_missing_file_all_none(self) -> None:
        prof = cp.load_profile(str(ROOT / "no-such-file.json"))
        self.assertTrue(all(v is None for v in prof.values()))

    def test_partial(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.json"
            p.write_text(json.dumps({"license_category": "C1", "bogus": 1}), encoding="utf-8")
            prof = cp.load_profile(str(p))
            self.assertEqual(prof["license_category"], "C1")
            self.assertIsNone(prof["startup_fund_jpy"])
            self.assertNotIn("bogus", prof)


if __name__ == "__main__":
    unittest.main()
