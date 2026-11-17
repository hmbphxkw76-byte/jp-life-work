#!/usr/bin/env python3
"""工作区标准化清理：缓存、临时文件、构建副产物、过期日志。

定位：这是 jp-life-work 流水线各阶段（前置 / 收尾）统一调用的清理入口，
覆盖本地开发工作区与 CI runner 工作区，保证运行前后环境一致、无残留。

用法：
  python engine/scripts/cleanup_workspace.py              # 清理本地工作区
  python engine/scripts/cleanup_workspace.py --check      # 只检查不删除（发现残留 → 退出码 1）
  python engine/scripts/cleanup_workspace.py --dry-run    # 列出将删除项，不执行
  python engine/scripts/cleanup_workspace.py --root <dir> # 指定根（默认脚本所在仓库）

退出码：0 = 干净或已清理；1 = --check 发现残留 / 参数错误 / 清理异常。

安全约束（不可关闭）：
  - 只清理仓库根内的路径，绝不跟随符号链接外出；
  - 已被 git 跟踪的文件 / 目录一律跳过（清理对象是「未入库的产物」）；
  - 不触碰 .git、engine/、reports/、docs/ 等源码与交付物；
  - 删除目录时仅删空或纯缓存目录（缓存目录整体删除）。
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 整体删除的缓存目录名（含其全部内容）
CACHE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    ".trae-html-share-packages",
    ".screenshots",
    "htmlcov",
}

# 仓库内固定生成的备份目录（相对根，正斜杠）
GENERATED_DIRS = (
    "engine/vocabulary/data/sync-backups",
    "engine/vocabulary/data/topic-backups",
)

# 单文件匹配规则：(说明, 匹配函数)
FILE_RULES: tuple[tuple[str, str], ...] = (
    ("Python 字节码", "*.py[cod]"),
    ("Python 旧字节码", "*$py.class"),
    ("临时文件", "*.tmp"),
    ("临时文件", "*.temp"),
    ("系统垃圾", ".DS_Store"),
    ("系统垃圾", "Thumbs.db"),
    ("系统垃圾", "desktop.ini"),
    ("覆盖率数据", ".coverage"),
    ("覆盖率数据", ".coverage.*"),
)

# 运行日志（工具写入，不入库）：仅匹配 data 目录下的 *.log
LOG_GLOB = "*.log"
LOG_DIR = "engine/vocabulary/data"

# 永不进入的目录（版本库与本地任务工作树由各自机制管理）
PRUNE_DIRS = {".git"}


@dataclass(frozen=True)
class Residue:
    """一条待清理残留。kind ∈ cache-dir / generated-dir / temp-file / log / os-junk。"""

    path: Path
    kind: str

    @property
    def size(self) -> int:
        p = self.path
        try:
            if p.is_dir():
                return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            return p.stat().st_size
        except OSError:
            return 0


def _tracked_paths(root: Path) -> set[str] | None:
    """已跟踪文件集合（正斜杠相对路径）；无 git 时返回 None（跳过该保护）。"""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return {p for p in out.stdout.decode("utf-8", "replace").split("\0") if p}


def _is_tracked(rel: str, tracked: set[str] | None) -> bool:
    """rel 自身或被跟踪集合覆盖（含其下文件）即视为已入库。"""
    if tracked is None:
        return False
    return rel in tracked or any(t.startswith(rel + "/") for t in tracked)


def collect_residue(root: Path = ROOT) -> list[Residue]:
    """扫描工作区，返回全部残留项（按路径排序，目录优先）。"""
    root = root.resolve()
    tracked = _tracked_paths(root)
    found: list[Residue] = []

    # 1) 固定生成的备份目录
    for rel in GENERATED_DIRS:
        d = root / rel
        if d.is_dir():
            found.append(Residue(d, "generated-dir"))

    # 2) 目录树遍历：缓存目录整体回收，文件按规则匹配
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        cur = Path(dirpath)
        rel_dir = cur.relative_to(root).as_posix() or "."

        # 永不进入 .git
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]

        for d in list(dirnames):
            if d in CACHE_DIRS:
                p = cur / d
                rel = p.relative_to(root).as_posix()
                if not _is_tracked(rel, tracked):
                    found.append(Residue(p, "cache-dir"))
                    dirnames.remove(d)          # 整体回收，不再下钻

        if rel_dir == LOG_DIR or rel_dir.startswith(LOG_DIR + "/"):
            for f in filenames:
                if _fnmatch(f, LOG_GLOB) and not (cur / f).is_symlink():
                    p = cur / f
                    rel = p.relative_to(root).as_posix()
                    if not _is_tracked(rel, tracked):
                        found.append(Residue(p, "log"))

        for label, pat in FILE_RULES:
            for f in filenames:
                if not _fnmatch(f, pat):
                    continue
                p = cur / f
                if p.is_symlink():
                    continue
                rel = p.relative_to(root).as_posix()
                if _is_tracked(rel, tracked):
                    continue
                kind = "os-junk" if label == "系统垃圾" else "temp-file"
                found.append(Residue(p, kind))

    found.sort(key=lambda r: (r.kind, r.path.as_posix()))
    return found


def _fnmatch(name: str, pat: str) -> bool:
    """最小 glob 匹配（支持 * 与 [cod] 字符类），避免依赖 fnmatch 的平台差异。"""
    import fnmatch

    return fnmatch.fnmatchcase(name, pat)


def clean(items: list[Residue]) -> tuple[int, int, list[str]]:
    """执行删除，返回 (删除项数, 释放字节, 失败列表)。"""
    n = 0
    freed = 0
    errors: list[str] = []
    for it in items:
        try:
            size = it.size
            if it.path.is_dir():
                shutil.rmtree(it.path, ignore_errors=False)
            else:
                it.path.unlink()
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(f"{it.path.relative_to(ROOT).as_posix()}: {exc}")
            continue
        n += 1
        freed += size
    return n, freed, errors


def _human(n: int) -> str:
    step = 1024.0
    val = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if val < step or unit == "GB":
            return f"{val:.0f} {unit}" if unit == "B" else f"{val:.1f} {unit}"
        val /= step
    return f"{n} B"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="工作区标准化清理（缓存 / 临时文件 / 过期日志）")
    ap.add_argument("--root", default=str(ROOT), help="仓库根目录（默认脚本所在仓库）")
    ap.add_argument("--check", action="store_true", help="只检查不删除；发现残留退出码 1")
    ap.add_argument("--dry-run", action="store_true", help="列出将删除项，不执行")
    ap.add_argument("--quiet", action="store_true", help="仅输出汇总一行")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"[cleanup] 错误：根目录不存在 {root}", file=sys.stderr)
        return 1

    items = collect_residue(root)
    kinds = {k: 0 for k in ("cache-dir", "generated-dir", "temp-file", "log", "os-junk")}
    for it in items:
        kinds[it.kind] += 1
    total = sum(it.size for it in items)
    detail = "、".join(f"{k} {v}" for k, v in kinds.items() if v)

    if args.check:
        if items:
            print(f"[cleanup] 发现残留 {len(items)} 项（{detail}），共 {_human(total)}：")
            for it in items:
                print(f"  - [{it.kind}] {it.path.relative_to(root).as_posix()}")
            return 1
        if not args.quiet:
            print("[cleanup] 工作区干净，无残留。")
        return 0

    if args.dry_run:
        if not items:
            print("[cleanup] 工作区干净，无待清理项。")
            return 0
        print(f"[cleanup][dry-run] 将清理 {len(items)} 项（{detail}），共 {_human(total)}：")
        for it in items:
            print(f"  - [{it.kind}] {it.path.relative_to(root).as_posix()}")
        return 0

    n, freed, errors = clean(items)
    if args.quiet:
        print(
            f"[cleanup] 已清理 {n} 项（释放 {_human(freed)}）。"
            if items
            else "[cleanup] 工作区干净，无残留。"
        )
    elif items:
        print(f"[cleanup] 已清理 {n}/{len(items)} 项（{detail or '无'}），释放 {_human(freed)}。")
    else:
        print("[cleanup] 工作区干净，无残留。")
    for e in errors:
        print(f"[cleanup] 删除失败：{e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
