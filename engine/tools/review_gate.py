#!/usr/bin/env python3
"""工具链变更双轴评审软门禁（TOOLCHAIN-DEV-SPEC 第七节；mainline 融合 P3）。

映射 mainline `pr-push-review` 的「评审覆盖」意图到本仓库的 worktree 合并模型：
当变更涉及工具链代码（``engine/tools/``、``engine/vocabulary/script/``、
``tools/``）时，要求 ``docs/toolchain/reviews/`` 存在至少一份双轴评审报告；
否则退出码 1（软门禁，P2 观察期可由调用方决定是否阻断）。

内容层变更（``*/reports/``、``*/prompts/`` 等）不在范围内，直接放行。

用法：
    python engine/tools/review_gate.py --changed <变更清单文件>
    python engine/tools/review_gate.py --changed <清单> --reviews-dir <目录>

变更清单：每行一个仓库相对路径（``git diff --name-only`` 输出）。
退出码：0 = 通过（无工具链变更 / 已有评审）；1 = 工具链变更缺评审或参数错误。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REVIEWS_DIR = ROOT / "docs" / "toolchain" / "reviews"

# 工具链代码范围（与 TOOLCHAIN-DEV-SPEC 第二节一致）
SCOPE_DIRS = (
    "engine/tools/",
    "engine/vocabulary/script/",
    "engine/scripts/",
)


def is_toolchain_path(rel: str) -> bool:
    """路径是否落在工具链代码范围内（兼容正反斜杠）。"""
    norm = str(rel).replace("\\", "/").strip()
    return any(norm.startswith(d) for d in SCOPE_DIRS)


def read_changed(path: Path) -> list[str]:
    """读取变更清单（逐行，忽略空行与 # 注释）。"""
    text = path.read_text(encoding="utf-8")
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def has_review(reviews_dir: Path) -> bool:
    """评审目录是否存在至少一份 .md 评审报告。"""
    if not reviews_dir.is_dir():
        return False
    return any(p.suffix.lower() == ".md" for p in reviews_dir.iterdir())


def gate(changed_file: Path, reviews_dir: Path) -> int:
    """执行软门禁，返回退出码。"""
    changed = read_changed(changed_file)
    if not changed:
        print("评审软门禁：变更清单为空，跳过")
        return 0
    toolchain = [c for c in changed if is_toolchain_path(c)]
    if not toolchain:
        print(f"评审软门禁：{len(changed)} 项变更均不在工具链范围，跳过")
        return 0
    if has_review(reviews_dir):
        print(f"评审软门禁：工具链变更 {len(toolchain)} 项，已存在双轴评审报告")
        return 0
    print(f"[X] 工具链变更 {len(toolchain)} 项缺少双轴评审报告："
          f"{reviews_dir} 为空，须先产出 Standards / Spec 双轴评审")
    return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="工具链变更双轴评审软门禁")
    ap.add_argument("--changed", required=True, help="变更清单文件（每行一个相对路径）")
    ap.add_argument("--reviews-dir", default=str(DEFAULT_REVIEWS_DIR),
                    help="双轴评审报告目录（默认 docs/toolchain/reviews）")
    args = ap.parse_args(argv)

    changed_file = Path(args.changed)
    if not changed_file.is_file():
        print(f"[ERROR] 变更清单不存在：{changed_file}", file=sys.stderr)
        return 1
    return gate(changed_file, Path(args.reviews_dir))


if __name__ == "__main__":
    sys.exit(main())
