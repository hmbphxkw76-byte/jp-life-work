# 工单 B9：共享检出工作区卫生（P2，一次性）

> **来源**：2026-11-19 工程收尾审计（U9）
> **状态**：待实施
> **优先级**：P2

---

## 背景

`cleanup_workspace.py --check` 实测 rc=1，8 项残留（cache-dir 6 / temp-file 1 / log 1，约 7.9 MB）：

- `.mypy_cache` / `.ruff_cache` / `engine/*/__pycache__` / `.coverage` / `engine/vocabulary/data/sync.log`

## 目标

清理共享检出残留，使 `cleanup_workspace.py --check` rc=0。

## 范围

- 做：清理未跟踪缓存/临时文件/日志。
- 不做：不删跟踪文件；不碰并行会话占用中的产物。

## 关联

- 源审计：本轮审计 §九。

## 约束

- 必须在无并行会话占用时执行（当前存在 active 任务 `consulting-panel`）。
- 逐个文件删除，禁递归删除。

## 验收判据

`cleanup_workspace.py --check` rc=0。

## 步骤

1. 确认无并行会话占用。
2. 跑 `cleanup_workspace.py`。
3. 复核。

## 证据

- 清理前后 `cleanup_workspace.py --check` 输出（完成后回填）。

## 状态

待实施（受并行会话门控）。
