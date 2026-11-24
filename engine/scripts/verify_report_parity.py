#!/usr/bin/env python3
"""报告生成一致性校验（迁移前后归一化比对）。

为「src/ → engine/ 引擎层迁移」提供客观的「报告生成零差异」判据：
  1) 字节完全相同 → OK；
  2) 允许差异仅限：① 旧路径 → 新路径的文本替换（src/→engine/、tools/→engine/scripts/）；
     ② INDEX.md 的「最近生成（构建心跳）」时间戳行；③ JSON 易变键（generated_at 等）；
  3) 归一化后仍不同 → MISMATCH（回归）。

退出码：0 全部一致；1 存在 MISMATCH / MISSING；2 用法或基线错误。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ---- 仓库根推导（兼容迁移前 tools/ 与迁移后 engine/scripts/ 两种布局）----
_HERE = Path(__file__).resolve()


def _repo_root() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(_HERE.parent), capture_output=True, text=True,
            timeout=15, check=True,
        )
        return Path(out.stdout.strip())
    except Exception:
        if _HERE.parent.name == "scripts" and _HERE.parent.parent.name == "engine":
            return _HERE.parents[2]
        if _HERE.parent.name == "tools":
            return _HERE.parents[1]
        return _HERE.parents[2]


ROOT = _repo_root()

# 参与比对的文件集（相对仓库根）；报告取各主题 reports/ 下的 md/html
PARITY_GLOBS = [
    "index.html",
    "INDEX.md",
    "search-index.json",
    "automation-status.json",
    "*/reports/*.html",
    "*/reports/*.md",
]
EXCLUDE_GLOBS = ["**/legacy/**", "**/.migration-baseline/**"]

# 旧 → 新 路径重写（长 → 短，与方案 §3.2 同序）
PATH_REWRITES = [
    ("src/prompts-tools/tools/", "engine/tools/"),
    ("src/report_templates/", "engine/report_templates/"),
    ("src/report-audits/", "engine/report-audits/"),
    ("src/vocabulary/", "engine/vocabulary/"),
    ("src/search/", "engine/search/"),
    ("src/tests/", "engine/tests/"),
    ("tools/workflow_guard.py", "engine/scripts/workflow_guard.py"),
    ("tools/git_push.py", "engine/scripts/git_push.py"),
    ("tools/cleanup_workspace.py", "engine/scripts/cleanup_workspace.py"),
    ("tools/run_tests_parallel.py", "engine/scripts/run_tests_parallel.py"),
    ("tools/branch_naming.py", "engine/scripts/branch_naming.py"),
    ("tools/git-hooks/", "engine/scripts/git-hooks/"),
    ("tools/README.md", "engine/scripts/README.md"),
    # 新布局路径恒等映射：须在 `tools/` 兜底项之前，否则 `engine/tools/` 会被
    # 兜底项二次命中成 `engine/engine/scripts/`（单遍交替无法识别「已是新路径」）。
    ("engine/tools/", "engine/tools/"),
    ("engine/scripts/", "engine/scripts/"),
    ("src/", "engine/"),
    ("tools/", "engine/scripts/"),
]

# 时间戳：① 旧「构建心跳」整行；② INDEX.md 头部「最近生成：... UTC（由 ...）」。
TIMESTAMP_LINE_RE = re.compile(
    r"最近生成（构建心跳）：[^\n]*"
    r"|最近生成：[^\n]*UTC[^\n]*"
)
# INDEX.md 报告行的构建时间列 `| YYYY-MM-DD HH:MM |`。
INDEX_TS_RE = re.compile(r"\| \d{4}-\d{2}-\d{2} \d{2}:\d{2} \|")
VOLATILE_JSON_KEYS = {"generated_at", "generated", "timestamp", "build_time", "built_at"}

# 单遍替换：按长 → 短编排替代项，替换结果不再回扫，
# 避免 `src/prompts-tools/tools/` → `engine/tools/` 后又被 `tools/` 规则二次命中。
_PATH_REWRITE_RE = re.compile("|".join(re.escape(old) for old, _ in PATH_REWRITES))


def _rewrite(match: re.Match) -> str:
    token = match.group(0)
    for old, new in PATH_REWRITES:
        if token == old:
            return new
    return token


def _drop_volatile(obj):
    """递归剔除 JSON 中的易变键，返回可稳定比较的对象。"""
    if isinstance(obj, dict):
        return {k: _drop_volatile(v) for k, v in obj.items()
                if k not in VOLATILE_JSON_KEYS}
    if isinstance(obj, list):
        return [_drop_volatile(v) for v in obj]
    return obj


def normalize(rel: str, text: str) -> str:
    """归一化：统一换行 → 路径重写（旧→新）→ 抹时间戳；JSON 另做易变键剔除。"""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    if rel.endswith(".json"):
        try:
            return json.dumps(_drop_volatile(json.loads(t)),
                              ensure_ascii=False, sort_keys=True)
        except json.JSONDecodeError:
            pass
    t = _PATH_REWRITE_RE.sub(_rewrite, t)
    t = TIMESTAMP_LINE_RE.sub(
        lambda m: ("最近生成（构建心跳）：<TIMESTAMP>" if "构建心跳" in m.group(0)
                   else "最近生成：<TIMESTAMP>"), t)
    t = INDEX_TS_RE.sub("| <TIMESTAMP> |", t)
    return t


def discover(root: Path) -> list[str]:
    """发现参与比对的文件（相对路径，排序去重）。"""
    rels: set[str] = set()
    for pat in PARITY_GLOBS:
        for p in root.glob(pat):
            if p.is_file():
                rels.add(p.relative_to(root).as_posix())
    for pat in EXCLUDE_GLOBS:
        for p in root.glob(pat):
            if p.is_file():
                rels.discard(p.relative_to(root).as_posix())
    return sorted(rels)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_baseline(baseline_dir: Path) -> int:
    baseline_dir.mkdir(parents=True, exist_ok=True)
    for child in baseline_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    rels = discover(ROOT)
    files: dict[str, dict] = {}
    for rel in rels:
        src = ROOT / rel
        dst = baseline_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        files[rel] = {"sha256": sha256(src), "size": src.stat().st_size}
    manifest = {"created": datetime.now().isoformat(timespec="seconds"),
                "root": str(ROOT), "files": files}
    (baseline_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"[parity] 基线已写入 {baseline_dir}（{len(rels)} 个文件）")
    return 0


def compare(baseline_dir: Path) -> int:
    manifest_path = baseline_dir / "manifest.json"
    if not manifest_path.is_file():
        print(f"[parity] 基线缺失：{manifest_path}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_files: dict = manifest.get("files", {})
    cur_rels = set(discover(ROOT))
    base_rels = set(base_files)

    ok = changed = mismatch = missing = new = 0
    problems: list[str] = []
    for rel in sorted(base_rels | cur_rels):
        base_meta = base_files.get(rel)
        cur_path = ROOT / rel
        if base_meta is None:
            new += 1
            problems.append(f"NEW      {rel}")
            continue
        if not cur_path.is_file():
            missing += 1
            problems.append(f"MISSING  {rel}")
            continue
        base_bytes = (baseline_dir / rel).read_bytes()
        cur_bytes = cur_path.read_bytes()
        if base_bytes == cur_bytes:
            ok += 1
            continue
        try:
            if normalize(rel, base_bytes.decode("utf-8")) == normalize(rel, cur_bytes.decode("utf-8")):
                changed += 1
            else:
                mismatch += 1
                problems.append(f"MISMATCH {rel}（归一化后仍不同）")
        except UnicodeDecodeError:
            mismatch += 1
            problems.append(f"MISMATCH {rel}（二进制/非 UTF-8 差异）")

    print(f"[parity] 一致={ok} 仅路径/时间戳={changed} 不匹配={mismatch} "
          f"缺失={missing} 新增={new}")
    for line in problems:
        print("  " + line)
    return 1 if (mismatch or missing) else 0


def main(argv: list[str] | None = None) -> int:
    global ROOT
    ap = argparse.ArgumentParser(description="报告生成一致性校验（迁移前后归一化比对）")
    ap.add_argument("--write-baseline", metavar="DIR", help="生成基线快照（迁移前）")
    ap.add_argument("--compare", metavar="DIR", help="与基线比对（迁移后）")
    ap.add_argument("--root", default=None, help="仓库根（默认自动推导）")
    args = ap.parse_args(argv)
    if args.root:
        ROOT = Path(args.root).resolve()
    if args.write_baseline:
        return write_baseline(Path(args.write_baseline))
    if args.compare:
        return compare(Path(args.compare))
    ap.error("必须指定 --write-baseline 或 --compare 之一")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
