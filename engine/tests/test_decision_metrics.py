"""``engine/tools/decision_metrics.py`` 单元测试（P1-6）。

覆盖：``_rows`` 表格解析、``collect``（收敛率 / 判定率 / 缺失 / 件套 / 日志）、
``append_history`` / ``trend``、``render_md``、``main`` 退出码（0/1/2）。

全部在 ``tempfile`` 临时目录内构造。
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


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


m = _load("decision_metrics", "engine/tools/decision_metrics.py")

REGISTRY_TEXT = """# 登记册

## 一、五问指标状态表

| # | 决策问题 | 指标 | 来源主题 | 引用位置 | 收敛状态 | 缺失标记 |
|---|---|---|---|---|---|---|
| 1 | 去不去 | 净收入 | 01 | x | 已收敛 | — |
| 2 | 去不去 | 缺口 | 01 | y | 部分 | 缺对比 |
| 3 | 能不能去 | 在留 | 08 | z | 已收敛 | — |

## 二、暴露的缺失清单（补缺触发器）

| 优先级 | 缺失主题 | 覆盖的决策问题 | 缺口证据 | 建议类型 | 期限 |
|---|---|---|---|---|---|
| P1 | 中国同岗到手对比 | 去不去 | 待补 | employment-research | 2026-11-01 |
| 已接入 | 在留救济 | 能不能去 | 已建 | policy-analysis | 已完成（2026-11-14） |

## 三、观察项

## 四、决策支持件套状态

### 4.1 五问判定

| # | 决策问题 | 判定 | 依据 | 置信度 |
|---|---|---|---|---|
| 1 | 去不去 | 是 | a | C1 |
| 2 | 能不能去 | 待定 | b | C2 |

### 4.2 件套清单

| 件套 | 路径 | 状态 |
|---|---|---|
| 个人参数 | x | 已建 |
| 财务模型 | y | 待建 |
"""

LOG_TEXT = ("# 决策日志\n\n| 日期 | 决策问题 | 字段 | 变化前 | 变化后 | 依据 | 来源 |\n"
            "|---|---|---|---|---|---|---|\n"
            "| 2026-11-01 | 去不去 | 判定 | 待定 | 是 | 参数齐 | 00 |\n"
            "| 2026-11-02 | 去不去 | 判定 | 是 | 否 | 复评 | 00 |\n")


class RowsCase(unittest.TestCase):
    def test_rows_skips_separator_and_non_numeric(self) -> None:
        text = ("## 一、五问指标状态表\n\n| # | a | b |\n|---|---|---|\n"
                "| 1 | x | y |\n| x | y | z |\n\n## 二、\n")
        rows = m._rows(text, __import__("re").compile(
            r"##\s*一、五问指标状态表(.*?)\n##\s*", __import__("re").DOTALL))
        self.assertEqual(rows, [["1", "x", "y"]])


class CollectCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.reg = self.root / "registry.md"
        self.reg.write_text(REGISTRY_TEXT, encoding="utf-8")
        self.log = self.root / "decision_log.md"
        self.log.write_text(LOG_TEXT, encoding="utf-8")

    def test_collect(self) -> None:
        with mock.patch.object(m, "REGISTRY", self.reg), \
                mock.patch.object(m, "LOG", self.log):
            snap = m.collect()
        self.assertEqual(snap["indicator_total"], 3)
        self.assertEqual(snap["indicator_converged"], 2)
        self.assertEqual(snap["gap_entries"], 1)
        self.assertEqual(snap["question_total"], 2)
        self.assertEqual(snap["question_decided"], 1)
        self.assertEqual(snap["kit_total"], 2)
        self.assertEqual(snap["kit_ready"], 1)
        self.assertEqual(snap["decision_log_entries"], 2)
        # n19 需求维度
        self.assertEqual(snap["requirement_total"], 3)
        self.assertEqual(snap["requirement_covered"], 2)
        self.assertEqual(snap["requirement_partial"], 1)
        self.assertEqual(snap["requirement_uncovered"], 0)
        self.assertEqual(snap["requirement_overdue"], 1)
        # n20 反馈维度
        self.assertEqual(snap["gap_total"], 2)
        self.assertEqual(snap["gap_closed"], 1)
        self.assertEqual(snap["gap_close_rate"], 0.5)

    def test_requirements_matrix(self) -> None:
        with mock.patch.object(m, "REGISTRY", self.reg):
            mx = m.requirements_matrix()
        self.assertEqual(len(mx["requirements"]), 3)
        self.assertEqual(len(mx["gaps"]), 2)
        req1 = mx["requirements"][0]
        self.assertEqual(req1["需求编号"], "REQ-01")
        self.assertEqual(req1["责任主题"], "01")
        self.assertEqual(req1["覆盖状态"], "已覆盖")
        self.assertEqual(req1["关联缺失编号"], "GAP-01")
        # 「能不能去」关联 GAP-02
        self.assertEqual(mx["requirements"][2]["关联缺失编号"], "GAP-02")

    def test_collect_missing_registry(self) -> None:
        with mock.patch.object(m, "REGISTRY", self.root / "nope.md"), \
                mock.patch.object(m, "LOG", self.log), \
                self.assertRaises(FileNotFoundError):
            m.collect()


class HistoryTrendCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.hist = self.root / "history.jsonl"

    def test_trend_no_history(self) -> None:
        with mock.patch.object(m, "HISTORY", self.hist):
            self.assertFalse(m.trend({})["available"])

    def test_trend_delta(self) -> None:
        self.hist.write_text(json.dumps(
            {"period": "2026-10", "indicator_converged": 1, "gap_entries": 2,
             "question_decided": 0, "kit_ready": 1, "decision_log_entries": 1}) + "\n",
            encoding="utf-8")
        snap = {"period": "2026-11", "indicator_converged": 2, "gap_entries": 1,
                "question_decided": 1, "kit_ready": 2, "decision_log_entries": 3}
        with mock.patch.object(m, "HISTORY", self.hist):
            tr = m.trend(snap)
        self.assertTrue(tr["available"])
        self.assertEqual(tr["prev_period"], "2026-10")
        self.assertEqual(tr["delta"]["indicator_converged"], 1)
        self.assertEqual(tr["delta"]["decision_log_entries"], 2)

    def test_append_history(self) -> None:
        with mock.patch.object(m, "HISTORY", self.hist):
            m.append_history({"period": "2026-11"})
            self.assertTrue(self.hist.is_file())
            self.assertEqual(len(self.hist.read_text(encoding="utf-8").splitlines()), 1)


class RenderMainCase(unittest.TestCase):
    def test_render_md(self) -> None:
        snap = {"indicator_convergence_rate": 0.5, "indicator_converged": 1,
                "indicator_total": 2, "question_decision_rate": 0.0,
                "question_decided": 0, "question_total": 2, "gap_entries": 1,
                "kit_readiness_rate": 1.0, "kit_ready": 1, "kit_total": 1,
                "decision_log_entries": 2,
                "requirement_coverage_rate": 0.5, "requirement_covered": 1,
                "requirement_total": 2, "requirement_partial": 1,
                "requirement_uncovered": 0, "requirement_overdue": 0,
                "gap_total": 2, "gap_closed": 1, "gap_close_rate": 0.5,
                "gap_close_avg_days": None}
        md = m.render_md(snap)
        self.assertIn("五问 / 缺失决策度量", md)
        self.assertIn("决策变化次数", md)
        self.assertIn("需求覆盖率", md)
        self.assertIn("缺失闭环率", md)

    def test_main_exit_1_on_empty(self) -> None:
        with mock.patch.object(m, "collect",
                               return_value={"indicator_total": 0, "question_total": 0,
                                             "gap_entries": 0, "question_decided": 0}), \
                mock.patch.object(sys, "argv", ["decision_metrics.py", "--json"]):
            self.assertEqual(m.main(), 1)

    def test_main_exit_2_on_pending(self) -> None:
        snap = {"indicator_total": 2, "question_total": 2, "gap_entries": 1,
                "question_decided": 1, "indicator_convergence_rate": 0.5,
                "question_decision_rate": 0.5}
        with mock.patch.object(m, "collect", return_value=snap), \
                mock.patch.object(sys, "argv", ["decision_metrics.py", "--json"]):
            self.assertEqual(m.main(), 2)

    def test_main_exit_0(self) -> None:
        snap = {"indicator_total": 2, "question_total": 2, "gap_entries": 0,
                "question_decided": 2, "indicator_convergence_rate": 1.0,
                "question_decision_rate": 1.0}
        with mock.patch.object(m, "collect", return_value=snap), \
                mock.patch.object(sys, "argv", ["decision_metrics.py", "--json"]):
            self.assertEqual(m.main(), 0)


if __name__ == "__main__":
    unittest.main()
