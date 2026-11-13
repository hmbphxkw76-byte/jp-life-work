# 月度滚动报告机制改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 13 个主题的 `reports/` 从「单份/多版本文件」改造为「每月一份滚动报告」：月内更新追加并标记，跨月以上月最终内容全量同步为基线，保留全部 Web 发布链路。

**Architecture:** 新增 `prompts/tools/monthly_docs.py` 统一月份命名解析与当月文档定位；`archive_reports.py` 新增 `rollover` 子命令负责跨月滚动；`update_scheduler` / `build_library` / `validate` 改用统一解析；`schedule.json` 的 `target` 统一为 `reports/` 目录；随后迁移现有文件并同步提示词与规范文档。

**Tech Stack:** Python 3.12、markdown、unittest、Git。

**Spec:** `docs/superpowers/specs/2026-11-12-monthly-report-restructure-design.md`

## Global Constraints

- 文件命名：`<base>_YYYY-MM.md`，`base` 为文档基名（如 `日本司机职业知识手册`、`日本特定技能司机物流监测报告`）；HTML 由 `md2html.py` 生成同名 `.html`。
- 增量标记（两条紧邻，缺一不可）：
  ```
  <!-- updated: YYYY-MM-DD | 变更摘要 -->
  > 🆕 **YYYY-MM-DD 更新**：变更摘要
  ```
- 三个 GitHub Actions workflow（`html-sync` / `scheduled-update` / `validate`）逻辑不动。
- 13 个主题目录、`prompts/`、`docs/` 结构不变。
- `validate.py` 退出码：0 通过 / 1 错误 / 2 警告。
- 所有命令从仓库根目录运行。
- **提交**：除非用户明确要求，不执行 `git commit`；每个任务完成后由用户决定提交时机。

## Review Focus

1. **跨月边界**：11 月最后一天 → 12 月第一天，`rollover` 必须以上月最终内容为基线，不得丢失内容与标记。
2. **同月多次更新**：同一月内两次更新必须追加到同一文件，标记时间戳可区分。
3. **旧文件残留**：迁移后 `reports/` 顶层不得残留 `*_vYYYY.MM.DD_N.md` / `*_baseline.md`。
4. **HTML 同步**：每个 md 必须有同名 html，聚合页链接到当月文件。
5. **标记配对**：每个 `<!-- updated -->` 必须有配对的可见标记，且日期一致。

---

### Task 1: 月份文档解析模块

**Files:**
- Create: `prompts/tools/monthly_docs.py`
- Test: `prompts/tools/tests/test_monthly_docs.py`

**Interfaces:**
- Produces:
  - `MONTH_SUFFIX_RE: re.Pattern` — 匹配 `_YYYY-MM` 结尾（`re.compile(r"_(\d{4})-(\d{2})$")`）
  - `month_key(stem: str) -> tuple[int, int] | None`
  - `current_document(topic: dict, root: Path | None = None) -> Path | None` — `topic["target"]` 为目录时 glob `*_YYYY-MM.md` 取最大月份；为文件时直接返回该文件；无匹配返回 `None`
  - `VISIBLE_MARKER_RE: re.Pattern` — 匹配 `^>\s*🆕\s*\*\*(?P<date>\d{4}-\d{2}-\d{2})\s*更新\*\*[：:]\s*(?P<summary>.+?)\s*$`
  - `visible_markers(text: str) -> list[dict]` — 每项含 `date`、`summary`、`lineno`

- [ ] **Step 1: 写失败测试**

`prompts/tools/tests/test_monthly_docs.py`：

```python
import tempfile
import unittest
from pathlib import Path

import monthly_docs


class MonthKeyTests(unittest.TestCase):
    def test_parses_month_suffix(self):
        self.assertEqual((2026, 11), monthly_docs.month_key("日本司机职业知识手册_2026-11"))

    def test_rejects_versioned_and_baseline(self):
        self.assertIsNone(monthly_docs.month_key("报告_v2026.11.12_5"))
        self.assertIsNone(monthly_docs.month_key("报告_baseline_2026.11"))


class CurrentDocumentTests(unittest.TestCase):
    def test_picks_latest_month(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            for name in ("手册_2026-10.md", "手册_2026-11.md", "手册_2026-12.md"):
                (reports / name).write_text("# x", encoding="utf-8")
            found = monthly_docs.current_document({"target": "reports"}, root=root)
            self.assertEqual("手册_2026-12.md", found.name)

    def test_falls_back_to_file_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "reports" / "手册.md"
            target.parent.mkdir()
            target.write_text("# x", encoding="utf-8")
            found = monthly_docs.current_document({"target": "reports/手册.md"}, root=root)
            self.assertEqual(target, found)


class VisibleMarkerTests(unittest.TestCase):
    def test_parses_marker(self):
        hits = monthly_docs.visible_markers("> 🆕 **2026-11-12 更新**：制度修正")
        self.assertEqual(1, len(hits))
        self.assertEqual("2026-11-12", hits[0]["date"])
        self.assertEqual("制度修正", hits[0]["summary"])
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s prompts/tools/tests -p "test_monthly_docs.py" -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'monthly_docs'`）

- [ ] **Step 3: 实现 `prompts/tools/monthly_docs.py`**

- `MONTH_SUFFIX_RE`、`VISIBLE_MARKER_RE` 用上面给出的正则。
- `month_key(stem)`：`MONTH_SUFFIX_RE.search(stem)` 命中则返回 `(int(year), int(month))`，否则 `None`。
- `current_document(topic, root=None)`：`base = root or ROOT`；`target = base / topic["target"]`；`target.is_file()` 时返回 `target`；否则 glob `*_YYYY-MM.md`（用 `MONTH_SUFFIX_RE` 过滤），取 `month_key` 最大者；无则 `None`。
- `visible_markers(text)`：逐行 `VISIBLE_MARKER_RE.match`，收集 `date`/`summary`/`lineno`。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s prompts/tools/tests -p "test_monthly_docs.py" -v`
Expected: PASS（3 个测试类全绿）

---

### Task 2: 可见标记校验

**Files:**
- Modify: `prompts/tools/validate.py`（`check_update_markers`，新增 `check_document_markers`）
- Test: `prompts/tools/tests/test_validate_markers.py`

**Interfaces:**
- Consumes: `monthly_docs.VISIBLE_MARKER_RE`、`build_library.UPDATE_MARKER_RE`
- Produces: `validate.check_document_markers(text: str) -> list[tuple[int, str, str]]` — 每项 `(lineno, level, message)`，`level ∈ {"error", "warning"}`

- [ ] **Step 1: 写失败测试**

`prompts/tools/tests/test_validate_markers.py`：

```python
import unittest

import validate


class MarkerPairTests(unittest.TestCase):
    def test_comment_without_visible_marker_is_error(self):
        text = "### 章节\n<!-- updated: 2026-11-12 -->\n\n内容\n"
        levels = [level for _, level, _ in validate.check_document_markers(text)]
        self.assertIn("error", levels)

    def test_malformed_visible_marker_is_error(self):
        text = "<!-- updated: 2026-11-12 | 摘要 -->\n> 🆕 2026-11-12 更新：摘要\n"
        levels = [level for _, level, _ in validate.check_document_markers(text)]
        self.assertIn("error", levels)

    def test_date_mismatch_is_error(self):
        text = "<!-- updated: 2026-11-12 | 摘要 -->\n> 🆕 **2026-11-13 更新**：摘要\n"
        levels = [level for _, level, _ in validate.check_document_markers(text)]
        self.assertIn("error", levels)

    def test_matched_pair_passes(self):
        text = "<!-- updated: 2026-11-12 | 摘要 -->\n> 🆕 **2026-11-12 更新**：摘要\n"
        self.assertEqual([], validate.check_document_markers(text))
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s prompts/tools/tests -p "test_validate_markers.py" -v`
Expected: FAIL（`AttributeError: module 'validate' has no attribute 'check_document_markers'`）

- [ ] **Step 3: 实现 `check_document_markers` 并接入 `check_update_markers`**

- 遍历文本行：
  - 命中 `build_library.UPDATE_MARKER_RE.fullmatch(stripped)` 的注释行：语法 OK；记录日期，检查**下一个非空行**是否为同日期的可见标记，不是则记 `error`（`更新标记缺少配对的可见标记` 或 `可见标记日期不一致`）。
  - 命中 `build_library.UPDATE_MARKER_RE.search` 但不 `fullmatch`：记 `error`（沿用现有「单独成行」规则）。
  - 以 `> 🆕` 开头但不匹配 `monthly_docs.VISIBLE_MARKER_RE`：记 `error`（`可见标记语法错误`）。
- `check_update_markers` 改为对每个文件调用 `check_document_markers`，把结果写入 `errors`/`warnings`（沿用现有编号 12 的输出格式）。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s prompts/tools/tests -p "test_validate_markers.py" -v`
Expected: PASS

---

### Task 3: 跨月 rollover 命令

**Files:**
- Modify: `prompts/tools/archive_reports.py`（新增 `rollover` 子命令与 `rollover_topic` 函数）
- Test: `prompts/tools/tests/test_archive_rollover.py`

**Interfaces:**
- Consumes: `monthly_docs.current_document`、`monthly_docs.month_key`
- Produces: `archive_reports.rollover_topic(topic: dict, root: Path | None = None, today: date | None = None, dry_run: bool = False) -> list[str]` — 返回操作日志；CLI `python prompts/tools/archive_reports.py rollover [--topic NN-xxx] [--dry-run]`

- [ ] **Step 1: 写失败测试**

`prompts/tools/tests/test_archive_rollover.py`：

```python
import tempfile
import unittest
from datetime import date
from pathlib import Path

import archive_reports


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class RolloverTests(unittest.TestCase):
    def test_creates_new_month_from_previous(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "reports/手册_2026-11.md", "# 手册\n")
            log = archive_reports.rollover_topic(
                {"target": "reports"}, root=root, today=date(2026, 12, 1)
            )
            self.assertTrue((root / "reports/手册_2026-12.md").is_file())
            self.assertTrue((root / "reports/archives/手册_2026-11.md").is_file())
            self.assertFalse((root / "reports/手册_2026-11.md").exists())

    def test_noop_when_same_month(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "reports/手册_2026-11.md", "# 手册\n")
            archive_reports.rollover_topic(
                {"target": "reports"}, root=root, today=date(2026, 11, 15)
            )
            self.assertFalse((root / "reports/手册_2026-12.md").exists())

    def test_updates_header_version_and_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "reports/手册_2026-11.md",
                  "> **版本**：v2026.11.12_5（第五期）　**数据基准日**：2026-11-12\n")
            archive_reports.rollover_topic(
                {"target": "reports"}, root=root, today=date(2026, 12, 1)
            )
            text = (root / "reports/手册_2026-12.md").read_text(encoding="utf-8")
            self.assertIn("2026-12", text)
            self.assertIn("2026-12-01", text)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s prompts/tools/tests -p "test_archive_rollover.py" -v`
Expected: FAIL（`AttributeError: module 'archive_reports' has no attribute 'rollover_topic'`）

- [ ] **Step 3: 实现 `rollover_topic` 与 CLI**

- `rollover_topic(topic, root=None, today=None, dry_run=False)`：
  - `base = root or ROOT`；`target = base / topic["target"]`；`current = monthly_docs.current_document(topic, root=base)`；无则返回 `["跳过：无当月文件"]`。
  - `key = monthly_docs.month_key(current.stem)`；无则返回 `["跳过：文件名无月份"]`。
  - `today = today or datetime.now(JST).date()`；`current_month = (today.year, today.month)`。
  - `key >= current_month` → 返回 `["跳过：已是当月"]`。
  - `base_name = current.stem[: MONTH_SUFFIX_RE.search(current.stem).start()]`；`new_stem = f"{base_name}_{today.year:04d}-{today.month:02d}"`。
  - 读取内容，更新头部：`(?m)^(\s*>\s*\*\*版本\*\*[：:]\s*)v\d{4}\.\d{2}\.\d{2}(?:_\d+)?` → `\1{YYYY-MM}`；`(?m)^(\s*>\s*\*\*(?:数据基准日|整理日期)\*\*[：:]\s*)\d{4}-\d{2}-\d{2}` → `\1{today.isoformat()}`。
  - `dry_run` 时只返回日志不落盘；否则写 `target/{new_stem}.md`，把 `current` 移动到 `target/archives/current.name`。
  - 返回日志（含新旧路径）。
- CLI：`rollover` 子命令，`--topic` 可选（默认遍历 `schedule.json` 全部主题），`--dry-run` 透传。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest discover -s prompts/tools/tests -p "test_archive_rollover.py" -v`
Expected: PASS

---

### Task 4: 工具链与配置适配

**Files:**
- Modify: `prompts/schedule.json`
- Modify: `prompts/tools/update_scheduler.py`
- Modify: `prompts/tools/build_library.py`
- Modify: `prompts/tools/validate.py`（`check_single_doc`）
- Test: `prompts/tools/tests/test_tool_integration.py`

**Interfaces:**
- Consumes: `monthly_docs.current_document`
- Produces: 无新增公共接口（内部改用解析器）

- [ ] **Step 1: 写失败测试**

`prompts/tools/tests/test_tool_integration.py`：

```python
import json
import unittest
from pathlib import Path

import monthly_docs

ROOT = Path(__file__).resolve().parents[3]


class ToolIntegrationTests(unittest.TestCase):
    def test_schedule_targets_are_directories(self):
        config = json.loads((ROOT / "prompts/schedule.json").read_text(encoding="utf-8"))
        for topic in config["topics"]:
            self.assertTrue(
                (ROOT / topic["target"]).is_dir(),
                f"[{topic['id']}] target 应为目录: {topic['target']}",
            )

    def test_every_topic_resolves_to_month_document(self):
        config = json.loads((ROOT / "prompts/schedule.json").read_text(encoding="utf-8"))
        for topic in config["topics"]:
            found = monthly_docs.current_document(topic, root=ROOT)
            self.assertIsNotNone(found, f"[{topic['id']}] 未解析到当月文档")
            self.assertRegex(found.stem, r"_\d{4}-\d{2}$")
```

> 注：本测试在迁移（Task 5）前会失败，属预期；Task 5 完成后复跑。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest discover -s prompts/tools/tests -p "test_tool_integration.py" -v`
Expected: FAIL（`test_schedule_targets_are_directories` 或 `test_every_topic_resolves_to_month_document` 失败）

- [ ] **Step 3: 改 `prompts/schedule.json`**

- 把 02–13 号主题的 `target` 由 `NN-xxx/reports/<手册名>.md` 改为 `NN-xxx/reports`；01 保持不变。

- [ ] **Step 4: 改 `update_scheduler.py`**

- `latest_report(topic)`：改为 `monthly_docs.current_document(topic)`（保留 `topic_version` 对 `VERSION_RE` 的兼容分支，月份文件返回 `YYYY-MM`）。
- `topic_version(topic)`：知识类改用 `monthly_docs.current_document(topic)` 读头部；监测类沿用。
- 看板 / 工单模板中的 `handbook_name` / `handbook_url`：改用 `monthly_docs.current_document(topic)` 解析出的文件（`target` 为目录时）。

- [ ] **Step 5: 改 `build_library.py`**

- `resolve_topic_source(config)`：统一改用 `monthly_docs.current_document(config)`；`target` 为目录时不再直接拼路径。
- `collect_report_editions(topic)`：新增对 `_YYYY-MM` 结尾文件的解析，`date = f"{year}-{month}-01"`、`version = f"{year}-{month}"`。
- `build_month_reports(topic)`：按 `_YYYY-MM` 直接归位（每月一份）。

- [ ] **Step 6: 改 `validate.py` 的 `check_single_doc`**

- 改为「月度单份约束」：每个主题 `reports/` 顶层恰好 1 份 `*_YYYY-MM.md`；知识类额外校验文件名含 `知识手册`；监测类不含。编号 1 的输出文案相应更新。

- [ ] **Step 7: 运行测试与校验**

Run: `python -m unittest discover -s prompts/tools/tests -p "test_tool_integration.py" -v && python prompts/tools/validate.py`
Expected: 集成测试仍有一项失败（迁移未完成），`validate.py` 报错误（旧文件名不符合新月命名）——记录现状，Task 5 修复。

---

### Task 5: 现有文件迁移

**Files:**
- Rename: `01-ssw-driver/reports/日本特定技能司机物流监测报告_v2026.11.12_5.md` → `..._2026-11.md`
- Rename: 02–13 号主题 `reports/日本XX知识手册.md` → `reports/日本XX知识手册_2026-11.md`
- Archive: `01-ssw-driver/reports/日本特定技能司机物流监测报告_baseline.md` → `archives/日本特定技能司机物流监测报告_baseline_2026.11.md`
- Modify: 上述 md 的头部与标记
- Regenerate: 全部 HTML

**Interfaces:**
- Consumes: Task 1–4 的解析器与工具

- [ ] **Step 1: 迁移 01 监测报告**

- `git mv 01-ssw-driver/reports/日本特定技能司机物流监测报告_v2026.11.12_5.md 01-ssw-driver/reports/日本特定技能司机物流监测报告_2026-11.md`
- 头部：`**版本**：2026-11（月度滚动报告）　**数据基准日**：2026-11-12`；删除 `{{...}}` 运行变量块（已执行完毕）。
- 为文件内全部 10 处 `<!-- updated: 2026-11-12 -->` 补配对可见标记：`> 🆕 **2026-11-12 更新**：<该节变更摘要>`；摘要取自该节标题或「本次更新重点」。
- 在头部下方新增「本月更新记录」表：`2026-11-11`（首期基线建立）、`2026-11-12`（制度修正：分野日语要件分区分化、JLPT 满员）。

- [ ] **Step 2: 迁移 02–13 知识手册**

对每个主题执行：`git mv reports/日本XX知识手册.md reports/日本XX知识手册_2026-11.md`，头部 `**版本**：2026-11（月度滚动报告）　**整理日期**：2026-11-12`，并在「导航与使用约定」后新增一条可见标记：`> 🆕 **2026-11-12 更新**：合并整理为单份手册`。

- [ ] **Step 3: 归档基线**

`git mv 01-ssw-driver/reports/日本特定技能司机物流监测报告_baseline.md 01-ssw-driver/reports/archives/日本特定技能司机物流监测报告_baseline_2026.11.md`

- [ ] **Step 4: 重新生成 HTML 与聚合页**

Run: `python prompts/tools/md2html.py && python prompts/tools/build_library.py`
Expected: 无输出错误；`index.html` / `library.html` 链接到 `_2026-11` 文件。

- [ ] **Step 5: 校验**

Run: `python prompts/tools/validate.py && python prompts/tools/build_library.py --check && python -m unittest discover -s prompts/tools/tests -p "test_*.py"`
Expected: 全部通过（`validate.py` 0 错误 0 警告；聚合页最新；测试全绿）

---

### Task 6: 提示词与规范文档适配

**Files:**
- Modify: `prompts/通用基座/prompt-generic-base.md`
- Modify: `prompts/知识库主题更新/prompt-knowledge-topic-update-template.md`
- Modify: `prompts/职业就业调研/prompt-employment-research-template.md`
- Modify: `prompts/市场指标监测/prompt-monthly-monitor-template.md`
- Modify: 13 个主题 prompt（路径与约定）
- Modify: `prompts/tools/merge_topics.py`（输出名改为当月）
- Modify: 根目录 `内容边界规范.md`、`内容更新周期标准.md`、`自动化更新方案.md`、`基线报告管理规则.md`、`README.md`
- Modify: `prompts/tools/tests/test_prompt_contracts.py`（同步契约）

**Interfaces:**
- Consumes: Task 1–4 的命名与标记约定

- [ ] **Step 1: 更新通用基座与模板**

- 输出路径：`reports/<base>_YYYY-MM.md`；跨月先 `archive_reports.py rollover`。
- 标记：`<!-- updated -->` + `> 🆕 **... 更新**：...` 双标记。
- 知识库模板：「单份手册」→「单月单份」。
- 删除 `{{BASELINE_PATH}}` / `{{PREVIOUS_REPORT_PATH}}` 基线相关变量，改为 `{{CURRENT_MONTH}}`、`{{PREVIOUS_MONTH_DOC}}`。

- [ ] **Step 2: 更新 13 个主题 prompt**

- 路径变量 `{{HANDBOOK_PATH}}` 指向当月文件；删除基线轮换表述；头部版本写 `YYYY-MM`。

- [ ] **Step 3: 更新 `merge_topics.py`**

- 输出文件名改为 `reports/日本{主题中文名}知识手册_{YYYY-MM}.md`（`YYYY-MM` 取当前月）。

- [ ] **Step 4: 更新规范文档与 README**

- `基线报告管理规则.md` → 改写为「月度报告管理规范」（每月一份、月内追加、跨月全量同步、`rollover` 命令）。
- `内容边界规范.md` / `内容更新周期标准.md` / `自动化更新方案.md`：更新命名与标记约定。
- `README.md`：报告机制、文件命名、标记说明。

- [ ] **Step 5: 运行契约测试**

Run: `python -m unittest discover -s prompts/tools/tests -p "test_*.py"`
Expected: PASS（契约测试与提示词一致）

---

### Task 7: 全量验证

**Files:** 无新增

- [ ] **Step 1: 结构完整性**

Run: `python prompts/tools/validate.py`
Expected: 13 项全 PASS，0 错误 0 警告

- [ ] **Step 2: 月度归档逻辑**

Run: `python prompts/tools/archive_reports.py rollover --dry-run`
Expected: 输出「跳过：已是当月」（当前 2026-11）

- [ ] **Step 3: 12 月基线推演**

在临时目录用 Task 3 的测试模拟 12-01 rollover，确认生成 `_2026-12.md` 且内容与 11 月最终文件一致。

Run: `python -m unittest prompts/tools/tests/test_archive_rollover.py -v`
Expected: PASS

- [ ] **Step 4: 标记可追溯**

人工抽查 01 报告：11 月内两处更新时间戳（11-11、11-12）可区分；每个 `<!-- updated -->` 有配对可见标记。

- [ ] **Step 5: HTML 与聚合页**

Run: `python prompts/tools/build_library.py --check`
Expected: 「聚合页面均为最新」

- [ ] **Step 6: 核心目录完整性**

确认 13 个主题目录、`prompts/`、`docs/` 均未删除或合并；每个主题 `reports/` 当月仅一份 md + 同名 html。
