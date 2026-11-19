"""归档保留期边界测试（优化方案 W1 / A2）。

单一事实源：``engine/tools/report_cycles.py`` 的 ``CYCLE_WINDOWS``（月 18 / 季 24 / 年 60）。
``archive_reports.py`` 不硬编码保留期，经 ``cycle_profile`` 取窗口。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

from archive_reports import select_archives  # noqa: E402
from report_cycles import CYCLE_WINDOWS, keep_periods  # noqa: E402

NOW = "2026-11"


def _months(start: str, n: int) -> list[str]:
    """从 start（YYYY-MM）起连续 n 个月。"""
    y, m = int(start[:4]), int(start[5:7])
    out = []
    for i in range(n):
        yy, mm = divmod(y * 12 + (m - 1) + i, 12)
        out.append(f"{yy:04d}-{mm + 1:02d}")
    return out


class TestCycleWindowsSingleSource(unittest.TestCase):
    """保留期只在一处定义。"""

    def test_windows_match_spec(self):
        self.assertEqual(CYCLE_WINDOWS["monthly"]["keep_months"], 18)
        self.assertEqual(CYCLE_WINDOWS["quarterly"]["keep_months"], 24)
        self.assertEqual(CYCLE_WINDOWS["annual"]["keep_months"], 60)

    def test_archive_reports_delegates_to_cycle_profile(self):
        src = (ROOT / "engine" / "tools" / "archive_reports.py").read_text(encoding="utf-8")
        self.assertIn("cycle_profile", src)
        self.assertNotIn("KEEP", src)  # 不再有硬编码保留期常量


class TestKeepPeriodsBoundaries(unittest.TestCase):
    """18 / 24 / 60 边界：窗口内含首月，窗口外一律归档。"""

    def test_monthly_keeps_18(self):
        periods = _months("2025-06", 18)  # 2025-06 .. 2026-11
        keep, archive = keep_periods(periods, CYCLE_WINDOWS["monthly"]["keep_months"], now=NOW)
        self.assertEqual(len(keep), 18)
        self.assertEqual(archive, [])
        # 多一个月即归档最早一期
        keep2, archive2 = keep_periods(
            _months("2025-05", 19), CYCLE_WINDOWS["monthly"]["keep_months"], now=NOW
        )
        self.assertEqual(len(keep2), 18)
        self.assertEqual(archive2, ["2025-05"])

    def test_quarterly_keeps_24(self):
        periods = _months("2024-12", 24)  # 2024-12 .. 2026-11
        keep, archive = keep_periods(periods, CYCLE_WINDOWS["quarterly"]["keep_months"], now=NOW)
        self.assertEqual(len(keep), 24)
        self.assertEqual(archive, [])
        keep2, archive2 = keep_periods(
            _months("2024-11", 25), CYCLE_WINDOWS["quarterly"]["keep_months"], now=NOW
        )
        self.assertEqual(len(keep2), 24)
        self.assertEqual(archive2, ["2024-11"])

    def test_annual_keeps_60(self):
        periods = _months("2021-12", 60)  # 2021-12 .. 2026-11
        keep, archive = keep_periods(periods, CYCLE_WINDOWS["annual"]["keep_months"], now=NOW)
        self.assertEqual(len(keep), 60)
        self.assertEqual(archive, [])
        keep2, archive2 = keep_periods(
            _months("2021-11", 61), CYCLE_WINDOWS["annual"]["keep_months"], now=NOW
        )
        self.assertEqual(len(keep2), 60)
        self.assertEqual(archive2, ["2021-11"])

    def test_select_archives_uses_window(self):
        items = [(p, Path(f"{p}.html")) for p in _months("2025-05", 19)]
        archived = select_archives(items, CYCLE_WINDOWS["monthly"]["keep_months"], now=NOW)
        self.assertEqual([p.name for p in archived], ["2025-05.html"])


if __name__ == "__main__":
    unittest.main()
