"""``engine/tools/l5_meta_check.py`` 单元测试（P1-4）。

覆盖：``_latest_evidence`` 取值、``evaluate``（覆盖缺口 / 无效证据 / basis 缺失 /
依据偏简告警 / 无报告）、``render_md``、``main`` 退出码（0/1/2）。

台账与状态以 mock 注入，不读写真实台账。
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

from audit_check import L5_CHECKLIST  # noqa: E402


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


m = _load("l5_meta_check", "engine/tools/l5_meta_check.py")


def _evidence(result: str = "yes", basis: str = "", verdict: str | None = None) -> str:
    items = []
    for label in L5_CHECKLIST:
        it = {"item": label[0], "result": result}
        if basis:
            it["basis"] = basis
        items.append(it)
    data = {"version": "2.0", "items": items}
    if verdict:
        data["verdict"] = verdict
    return json.dumps(data, ensure_ascii=False)


def _ledger(ev: str) -> list[dict]:
    return [{"report": "01-x/reports/2026-11-x.md", "role": "reviewer_l2",
             "event": "stage_pass", "evidence": ev}]


class LatestEvidenceCase(unittest.TestCase):
    def test_takes_last_stage_pass(self) -> None:
        led = [
            {"report": "r", "role": "reviewer_l2", "event": "stage_pass", "evidence": "A"},
            {"report": "r", "role": "reviewer_l2", "event": "stage_pass", "evidence": "B"},
        ]
        self.assertEqual(m._latest_evidence(led, "r"), "B")

    def test_stage_fail_resets(self) -> None:
        led = [
            {"report": "r", "role": "reviewer_l2", "event": "stage_pass", "evidence": "A"},
            {"report": "r", "role": "reviewer_l2", "event": "stage_fail", "evidence": ""},
        ]
        self.assertEqual(m._latest_evidence(led, "r"), "")


class EvaluateCase(unittest.TestCase):
    def _run(self, ledger, state, l5):
        with mock.patch.object(m, "load_ledger", return_value=ledger), \
                mock.patch.object(m, "rebuild_status", return_value=state), \
                mock.patch.object(m, "l5_status_from_ledger", return_value=l5):
            return m.evaluate()

    def test_all_valid(self) -> None:
        rep = "01-x/reports/2026-11-x.md"
        out = self._run(_ledger(_evidence("no", "依据充足且具体")),
                        {rep: {"state": "audited"}}, {rep: True})
        self.assertEqual(out["audited"], 1)
        self.assertEqual(out["coverage"], 1.0)
        self.assertEqual(out["basis_missing"], 0)
        self.assertEqual(out["problems"], [])

    def test_missing_evidence_blocks(self) -> None:
        rep = "01-x/reports/2026-11-x.md"
        out = self._run([], {rep: {"state": "audited"}}, {rep: False})
        self.assertLess(out["coverage"], 1.0)
        self.assertTrue(any("覆盖率" in p for p in out["problems"]))

    def test_basis_missing_blocks(self) -> None:
        rep = "01-x/reports/2026-11-x.md"
        # no 结论无 basis → validate 失败，且 basis_missing 计数
        out = self._run(_ledger(_evidence("no", "")),
                        {rep: {"state": "audited"}}, {rep: False})
        self.assertGreaterEqual(out["basis_missing"], 1)

    def test_short_basis_warns(self) -> None:
        rep = "01-x/reports/2026-11-x.md"
        out = self._run(_ledger(_evidence("uncertain", "短")),
                        {rep: {"state": "audited"}}, {rep: True})
        self.assertTrue(out["warnings"])

    def test_no_audited(self) -> None:
        out = self._run([], {}, {})
        self.assertEqual(out["audited"], 0)
        self.assertTrue(out["problems"])

    def test_verdict_fail_counted(self) -> None:
        rep = "01-x/reports/2026-11-x.md"
        out = self._run(_ledger(_evidence("yes", "x", verdict="fail")),
                        {rep: {"state": "audited"}}, {rep: True})
        self.assertEqual(out["verdict_fail"], 1)


class RenderAndMainCase(unittest.TestCase):
    def test_render_md_has_rows(self) -> None:
        rep = {"updated": "t", "audited": 1, "with_valid_evidence": 1, "coverage": 1.0,
               "evidence_valid_rate": 1.0, "basis_missing": 0, "avg_basis_chars": 5.0,
               "verdict_fail": 0, "problems": [], "warnings": [],
               "reports": [{"report": "r", "valid": True, "l5_status": True, "problems": []}]}
        md = m.render_md(rep)
        self.assertIn("L5 语义复核证据元评估", md)
        self.assertIn("| r |", md)

    def test_main_exit_1(self) -> None:
        with mock.patch.object(m, "evaluate", return_value={"problems": ["x"], "warnings": []}), \
                mock.patch.object(sys, "argv", ["l5_meta_check.py", "--json"]):
            self.assertEqual(m.main(), 1)

    def test_main_exit_2(self) -> None:
        with mock.patch.object(m, "evaluate", return_value={"problems": [], "warnings": ["w"]}), \
                mock.patch.object(sys, "argv", ["l5_meta_check.py", "--json"]):
            self.assertEqual(m.main(), 2)

    def test_main_exit_0(self) -> None:
        with mock.patch.object(m, "evaluate", return_value={"problems": [], "warnings": []}), \
                mock.patch.object(sys, "argv", ["l5_meta_check.py", "--json"]):
            self.assertEqual(m.main(), 0)


if __name__ == "__main__":
    unittest.main()
