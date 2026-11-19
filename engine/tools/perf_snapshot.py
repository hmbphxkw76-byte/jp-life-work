#!/usr/bin/env python3
"""性能趋势快照（架构优化方向 D / I-13，组 D / N14）。

采集两类指标并追加到 ``engine/report-audits/toolchain/perf-trend.json``：

- **规模快照**：仓库体积 / 文件数、报告 md / html 数与 html 体积、
  ``index.html`` / ``search-index.json`` 体积、工具数、契约测试数；
- **耗时快照**：``validate`` / ``build_hub --check`` / ``build_index --check`` /
  ``md2html``，以及可选 ``unittest``（``--with-tests``，默认关闭，避免维护流程翻倍耗时）。

基线语义：输出文件缺失时，首条快照即为基线；``--set-baseline`` 用当前快照覆盖基线。
历史保留最近 36 条（月度约 3 年）。``--porcelain`` 只输出 JSON（供程序消费）。

用法：
    python engine/tools/perf_snapshot.py
    python engine/tools/perf_snapshot.py --with-tests
    python engine/tools/perf_snapshot.py --set-baseline
    python engine/tools/perf_snapshot.py --porcelain

退出码：0 成功；1 失败（输出不可写 / 快照无法生成）。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import ROOT, SKIP_TOP, atomic_write  # noqa: E402

OUTPUT = ROOT / "engine" / "report-audits" / "toolchain" / "perf-trend.json"
HISTORY_LIMIT = 36

# 默认耗时采集命令（相对仓库根，正斜杠路径，跨平台一致）。
FAST_COMMANDS: dict[str, list[str]] = {
    "validate": ["engine/tools/validate.py"],
    "build_hub_check": ["engine/tools/build_hub.py", "--check"],
    "build_index_check": ["engine/tools/build_index.py", "--check"],
    "md2html": ["engine/tools/md2html.py"],
}
TEST_COMMAND: dict[str, list[str]] = {
    "unittest": ["-m", "unittest", "discover", "-s", "engine/tests", "-q"],
}

# 统计仓库体积时跳过的生成 / 缓存目录。
SKIP_DIRS = {".git", ".worktrees", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}


def _iter_report_dirs(root: Path):
    """产出业务线下的 ``reports`` 目录（与 _common.iter_business_dirs 同口径）。"""
    for top in sorted(root.iterdir()):
        if not top.is_dir() or top.name.startswith(".") or top.name in SKIP_TOP:
            continue
        if (top / "reports").is_dir():
            yield top / "reports"
            continue
        for prop in sorted(top.iterdir()):
            if prop.is_dir() and not prop.name.startswith(".") and (prop / "reports").is_dir():
                yield prop / "reports"


def collect_scale(root: Path) -> dict:
    """采集规模快照（纯读取，不写盘）。"""
    repo_files = 0
    repo_bytes = 0
    for p in root.rglob("*"):
        # 按相对路径判断，避免仓库所在上级目录（如 .worktrees/）被误判为跳过项。
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if p.is_file():
            repo_files += 1
            try:
                repo_bytes += p.stat().st_size
            except OSError:
                continue

    md_count = html_count = html_bytes = 0
    for reports in _iter_report_dirs(root):
        md_count += sum(1 for _ in reports.glob("*.md"))
        for html in reports.glob("*.html"):
            html_count += 1
            try:
                html_bytes += html.stat().st_size
            except OSError:
                continue

    index_html = root / "index.html"
    search_index = root / "search-index.json"
    tool_count = len([p for p in (root / "engine" / "tools").glob("*.py")
                      if p.name != "_common.py"])
    test_count = unittest.defaultTestLoader.discover(
        str(root / "engine" / "tests")).countTestCases()

    return {
        "repo_files": repo_files,
        "repo_bytes": repo_bytes,
        "report_md": md_count,
        "report_html": html_count,
        "report_html_bytes": html_bytes,
        "index_html_bytes": index_html.stat().st_size if index_html.is_file() else 0,
        "search_index_bytes": search_index.stat().st_size if search_index.is_file() else 0,
        "tool_count": tool_count,
        "test_count": test_count,
    }


def run_timed(commands: dict[str, list[str]], root: Path) -> dict[str, dict]:
    """依次运行命令并记录耗时（秒）与退出码；不因非零退出码抛错。"""
    result: dict[str, dict] = {}
    for name, args in commands.items():
        argv = [sys.executable, *args]
        t0 = time.perf_counter()
        proc = subprocess.run(argv, cwd=str(root), capture_output=True, check=False)
        result[name] = {
            "sec": round(time.perf_counter() - t0, 3),
            "returncode": proc.returncode,
        }
    return result


def _delta(baseline: dict, current: dict) -> dict:
    """基线与当前的差值（耗时 / 规模），同键相减。"""
    out: dict = {"timings": {}, "scale": {}}
    for key, val in current["timings"].items():
        base = baseline.get("timings", {}).get(key)
        out["timings"][key] = None if base is None else round(val["sec"] - base["sec"], 3)
    for key, val in current["scale"].items():
        base = baseline.get("scale", {}).get(key)
        out["scale"][key] = None if base is None else val - base
    return out


def snapshot(output: Path, root: Path, with_tests: bool = False,
             set_baseline: bool = False) -> dict:
    """生成一条快照并落盘，返回 ``{baseline, current, delta}``。"""
    commands = dict(FAST_COMMANDS)
    if with_tests:
        commands.update(TEST_COMMAND)

    current = {
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "scale": collect_scale(root),
        "timings": run_timed(commands, root),
    }

    data: dict[str, Any] = {"schema": 1, "baseline": None, "history": []}
    if output.is_file():
        try:
            loaded = json.loads(output.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("history"), list):
                data = {"schema": 1, "baseline": loaded.get("baseline"),
                        "history": loaded["history"]}
        except (OSError, json.JSONDecodeError):
            pass

    baseline = data.get("baseline")
    if baseline is None or set_baseline:
        baseline = current
    history = data.setdefault("history", [])
    history.append(current)
    data["history"] = history[-HISTORY_LIMIT:]
    baseline = baseline or data["history"][0]
    data["baseline"] = baseline

    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(output, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return {"baseline": baseline, "current": current,
            "delta": _delta(baseline, current)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="性能趋势快照")
    ap.add_argument("--output", default=str(OUTPUT), help="快照文件路径")
    ap.add_argument("--with-tests", action="store_true", help="额外采集 unittest 耗时")
    ap.add_argument("--set-baseline", action="store_true", help="用当前快照覆盖基线")
    ap.add_argument("--porcelain", action="store_true", help="只输出 JSON")
    args = ap.parse_args(argv)

    output = Path(args.output)
    try:
        result = snapshot(output, ROOT, with_tests=args.with_tests,
                          set_baseline=args.set_baseline)
    except OSError as e:
        print(f"[ERROR] 快照写入失败：{e}")
        return 1

    if args.porcelain:
        print(json.dumps(result, ensure_ascii=False))
        return 0

    cur = result["current"]
    print(f"性能趋势快照：{cur['timestamp']}")
    print(f"  规模：仓库 {cur['scale']['repo_files']} 文件 / "
          f"{cur['scale']['repo_bytes']} bytes；报告 md {cur['scale']['report_md']} / "
          f"html {cur['scale']['report_html']}；测试 {cur['scale']['test_count']} 项")
    for name, entry in cur["timings"].items():
        print(f"  耗时：{name} {entry['sec']}s（退出码 {entry['returncode']}）")
    print(f"  快照文件：{output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
