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
    python engine/tools/coverage_gate.py
    python engine/tools/coverage_gate.py --update-baseline
    python engine/tools/coverage_gate.py --porcelain
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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
    if not isinstance(data.get("per_tool_min"), int) or isinstance(data.get("per_tool_min"), bool):
        raise ValueError("coverage-config.json 缺少整型 per_tool_min")
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


def per_tool_coverage() -> dict:
    """逐工具覆盖率明细（P2-3：薄弱点可定位）。

    读取最近一次 ``.coverage`` 数据，对 ``engine/tools/*.py`` 逐文件计算
    ``(语句数 - 缺失) / 语句数``，返回 ``{文件名: 百分比}``（升序，薄弱项在前）。
    无数据时返回空字典。
    """
    import coverage

    cov = coverage.Coverage(config_file=str(RC))
    try:
        cov.load()
    except Exception:  # noqa: BLE001
        return {}
    data = cov.get_data()
    out: dict[str, float] = {}
    for f in data.measured_files():
        rel = Path(f)
        try:
            rel = rel.relative_to(ROOT)
        except ValueError:
            continue
        parts = rel.parts
        if len(parts) < 2 or parts[0] != "engine" or parts[1] != "tools":
            continue
        if rel.suffix != ".py" or rel.name == "_common.py":
            continue
        try:
            _fn, statements, _excluded, missing, _fmt = cov.analysis2(f)[:5]
        except Exception:  # noqa: BLE001
            continue
        n = len(statements or [])
        if n:
            out[rel.name] = round((n - len(missing or [])) / n * 100, 1)
    return dict(sorted(out.items(), key=lambda kv: kv[1]))


def tools_below(per_tool: dict, per_tool_min: int) -> list[str]:
    """低于单工具最低阈值的工具名（升序，薄弱项在前）。"""
    return [k for k, v in per_tool.items() if v < per_tool_min]


def evaluate(total: float, threshold: int, enforce: bool,
             per_tool_min: int | None = None, per_tool: dict | None = None) -> int:
    """按阈值与开关判定退出码（0 达标 / 1 阻断 / 2 观察）。

    总覆盖率与单工具最低阈值（``per_tool_min``）双重判定：任一不达标即不通过。
    ``per_tool_min`` 为 None 时退化为仅总覆盖率判定（兼容既有调用）。
    """
    code = 0 if total >= threshold else (1 if enforce else 2)
    if per_tool_min is not None and per_tool and tools_below(per_tool, per_tool_min):
        if enforce:
            code = 1
        elif code == 0:
            code = 2
    return code


def write_baseline(path: Path, payload: dict) -> None:
    """原子写入基线 JSON（目录不存在自动创建；失败不留半写文件）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            tmp.unlink()
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

    per_tool = per_tool_coverage()
    weakest = dict(list(per_tool.items())[:5])
    per_tool_min = config["per_tool_min"]
    below = tools_below(per_tool, per_tool_min)
    code = evaluate(total, config["threshold"], config["enforce"], per_tool_min, per_tool)
    if not ok:
        # 测试全绿是覆盖率的前提；测试失败一律阻断
        code = 1

    if args.update_baseline:
        write_baseline(ROOT / config["baseline"], {
            "threshold": config["threshold"],
            "per_tool_min": per_tool_min,
            "enforce": config["enforce"],
            "total_percent": round(total, 2),
            "tests_green": ok,
            "per_tool": per_tool,
            "weakest": weakest,
        })

    if args.porcelain:
        print(json.dumps({
            "total_percent": round(total, 2),
            "threshold": config["threshold"],
            "enforce": config["enforce"],
            "tests_green": ok,
            "per_tool": per_tool,
            "weakest": weakest,
            "per_tool_min": per_tool_min,
            "below_tools": below,
            "exit_code": code,
        }, ensure_ascii=False))
    else:
        if report.strip():
            print(report.rstrip())
        print(f"覆盖率 {total:.1f}%（阈值 {config['threshold']}%，"
              f"enforce={config['enforce']}）（测试 {'全绿' if ok else '有失败'}）")
        if weakest:
            print("薄弱工具 Top5：" + "、".join(
                f"{k} {v}%" for k, v in weakest.items()))
        if below:
            print("低于单工具阈值（{}%）的工具：{}".format(
                per_tool_min, "、".join(f"{k} {per_tool[k]}%" for k in below)))
        if code == 1:
            print("[BLOCK] 覆盖率未达阈值或测试失败，阻断合并")
        elif code == 2:
            print("[WARN] 覆盖率未达阈值（观察期，不阻断）")
        else:
            print("[OK] 覆盖率达标")
    return code


if __name__ == "__main__":
    sys.exit(main())
