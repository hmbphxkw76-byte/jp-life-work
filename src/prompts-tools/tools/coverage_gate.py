#!/usr/bin/env python3
"""工具链覆盖率门禁（TOOLCHAIN-DEV-SPEC 第六节；mainline 融合 P1 / P3）。

读取单一事实源 ``coverage-config.json`` 的 ``threshold`` / ``enforce``，
在工具链代码范围（左 ``.coveragerc`` 的 ``source`` / ``omit``）内运行契约测试并采集覆盖率：

  - ``total >= threshold``      → 退出码 0（达标）
  - ``total < threshold`` 且 ``enforce=true``  → 退出码 1（阻断）
  - ``total < threshold`` 且 ``enforce=false`` → 退出码 2（观察，不阻断）
  - 测试未全绿                       → 退出码 1（覆盖率以测试全绿为前提）

``--update-baseline`` 额外把总覆盖率写入 ``coverage-config.json`` 指定的基线文件；
``--porcelain`` 仅输出 JSON（供程序消费）。

用法：
    python src/prompts-tools/tools/coverage_gate.py
    python src/prompts-tools/tools/coverage_gate.py --update-baseline
    python src/prompts-tools/tools/coverage_gate.py --porcelain
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RC = ROOT / ".coveragerc"
CONFIG = Path(__file__).resolve().parent / "coverage-config.json"


def load_config(path: Path = CONFIG) -> dict:
    """读取覆盖率单一事实源配置。

    缺失 / 非对象 / 字段类型不符即抛错（不静默用默认值），保证门禁口径唯一。
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("coverage-config.json 顶层须为对象")
    if not isinstance(data.get("threshold"), int) or isinstance(data.get("threshold"), bool):
        raise ValueError("coverage-config.json 缺少整型 threshold")
    if not isinstance(data.get("enforce"), bool):
        raise ValueError("coverage-config.json 缺少布尔 enforce")
    if not isinstance(data.get("test_discovery"), str) or not data["test_discovery"]:
        raise ValueError("coverage-config.json 缺少 test_discovery")
    if not isinstance(data.get("baseline"), str) or not data["baseline"]:
        raise ValueError("coverage-config.json 缺少 baseline")
    return data


def run_tests(discovery: str) -> bool:
    """发现并运行契约测试，返回是否全绿。"""
    suite = unittest.defaultTestLoader.discover(str(ROOT / discovery))
    stream = io.StringIO()
    result = unittest.TextTestRunner(verbosity=0, stream=stream).run(suite)
    return result.wasSuccessful()


def measure(config: dict) -> tuple[float, str, bool]:
    """在 coverage 下运行测试，返回 ``(总覆盖率百分比, 报告文本, 测试是否全绿)``。"""
    import coverage

    cov = coverage.Coverage(config_file=str(RC))
    cov.start()
    try:
        ok = run_tests(config["test_discovery"])
    finally:
        cov.stop()
        cov.save()
    buf = io.StringIO()
    total = cov.report(file=buf)
    return float(total), buf.getvalue(), ok


def evaluate(total: float, threshold: int, enforce: bool) -> int:
    """按阈值与开关判定退出码（0 达标 / 1 阻断 / 2 观察）。"""
    if total >= threshold:
        return 0
    return 1 if enforce else 2


def write_baseline(path: Path, payload: dict) -> None:
    """原子写入基线 JSON（目录不存在自动创建；失败不留半写文件）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="工具链覆盖率门禁")
    ap.add_argument("--update-baseline", action="store_true", help="刷新基线文件")
    ap.add_argument("--porcelain", action="store_true", help="仅输出 JSON")
    args = ap.parse_args(argv)

    try:
        config = load_config()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[ERROR] 覆盖率配置无效：{exc}", file=sys.stderr)
        return 1

    total, report, ok = measure(config)
    code = evaluate(total, config["threshold"], config["enforce"])
    if not ok:
        # 测试全绿是覆盖率的前提；测试失败一律阻断
        code = 1

    if args.update_baseline:
        write_baseline(ROOT / config["baseline"], {
            "threshold": config["threshold"],
            "enforce": config["enforce"],
            "total_percent": round(total, 2),
            "tests_green": ok,
        })

    if args.porcelain:
        print(json.dumps({
            "total_percent": round(total, 2),
            "threshold": config["threshold"],
            "enforce": config["enforce"],
            "tests_green": ok,
            "exit_code": code,
        }, ensure_ascii=False))
    else:
        if report.strip():
            print(report.rstrip())
        print(f"覆盖率 {total:.1f}%（阈值 {config['threshold']}%，"
              f"enforce={config['enforce']}）（测试 {'全绿' if ok else '有失败'}）")
        if code == 1:
            print("[BLOCK] 覆盖率未达阈值或测试失败，阻断合并")
        elif code == 2:
            print("[WARN] 覆盖率未达阈值（观察期，不阻断）")
        else:
            print("[OK] 覆盖率达标")
    return code


if __name__ == "__main__":
    sys.exit(main())
