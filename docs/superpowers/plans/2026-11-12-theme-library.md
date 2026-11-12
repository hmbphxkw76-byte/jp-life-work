# 主题集中展示与汇总阅读 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从现有 13 个主题主文档自动生成集中导航页 `index.html` 和连续阅读页 `library.html`，提供主题详情、双向锚点、搜索、响应式导航和 CI 同步。

**Architecture:** `prompts/schedule.json` 登记主题与展示元数据，`build_library.py` 复用现有 Markdown 渲染和最新监测报告选择逻辑，输出两个自包含静态 HTML。原文保持唯一内容源；构建器为标题与链接添加主题命名空间，`validate.py` 检查生成结果是否同步。

**Tech Stack:** Python 3、Markdown for Python、标准库 unittest、原生 HTML/CSS/JavaScript、GitHub Actions。

**提交约定:** 用户未要求 Git commit，本计划只修改和验证文件，不执行提交或推送。

---

### Task 1: 主题展示元数据与公共基础样式

**Files:**
- Modify: `prompts/schedule.json`
- Modify: `prompts/tools/md2html.py:28-63`
- Create: `prompts/tools/test_build_library.py`
- Create: `prompts/tools/build_library.py`

- [ ] **Step 1: 写配置校验失败测试**

```python
import unittest
from pathlib import Path
from unittest.mock import patch
import build_library as library

ROOT = Path(__file__).resolve().parents[2]

class DisplayConfigTests(unittest.TestCase):
    def test_display_metadata_is_required(self):
        with self.assertRaises(library.BuildError):
            library.require_display_metadata({"id": "02-career-driver", "name": "司机"})

    def test_project_topics_have_display_metadata(self):
        topics = library.load_topics()
        self.assertEqual(13, len(topics))
        self.assertTrue(all(t["category"] and t["description"] for t in topics))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python prompts/tools/test_build_library.py -v`
Expected: 首次因 `build_library` 不存在而失败；创建空构建模块后，因缺少 `BuildError`、`require_display_metadata` 或元数据而失败。

- [ ] **Step 3: 实现元数据校验并登记 13 个主题**

在 `build_library.py` 定义：

```python
import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

import markdown
import md2html
import update_scheduler

ROOT = Path(__file__).resolve().parents[2]

class BuildError(RuntimeError):
    pass

def require_display_metadata(topic):
    for key in ("id", "name", "kind", "target", "category", "description"):
        if not topic.get(key):
            raise BuildError(f"[{topic.get('id', '未知主题')}] 缺少展示字段: {key}")

def load_topics():
    config = update_scheduler.load_config()
    errors = update_scheduler.validate_config(config)
    if errors:
        raise BuildError("主题配置错误：\n" + "\n".join(errors))
    topics = config["topics"]
    for topic in topics:
        require_display_metadata(topic)
    return topics
```

为 `schedule.json` 每个主题增加 `category` 与 `description`。分类严格使用“监测动态、职业就业、行业技术、经济环境、制度政策、学习成长、生活地域”；摘要使用 README 主题目录中对应用途的精简文本，不写动态指标值。

在 `md2html.py` 将现有 `<style>` 内的基础规则原样提取为 `BASE_CSS`，令 `TEMPLATE` 使用 `{base_css}`；`convert()` 同时传入 `base_css=BASE_CSS`，保持现有报告 HTML 输出不变。

- [ ] **Step 4: 运行测试并确认通过**

Run: `python prompts/tools/test_build_library.py -v`
Expected: `DisplayConfigTests` 两项 PASS。

- [ ] **Step 5: 检查本任务差异**

Run: `git diff -- prompts/schedule.json prompts/tools/md2html.py prompts/tools/build_library.py prompts/tools/test_build_library.py`
Expected: 仅包含展示字段、公共 CSS 提取、构建模块和测试；不包含用户已有的看板或自动化方案改动。

### Task 2: 正文渲染、主题命名空间与链接重写

**Files:**
- Modify: `prompts/tools/build_library.py`
- Modify: `prompts/tools/test_build_library.py`

- [ ] **Step 1: 写链接与源文件解析失败测试**

```python
class RenderingTests(unittest.TestCase):
    def test_heading_and_internal_anchor_are_namespaced(self):
        html = '<h2 id="薪资">薪资</h2><p><a href="#薪资">直达</a></p>'
        result = library.namespace_html(html, "02-career-driver", ROOT / "02-career-driver/reports", {})
        self.assertIn('id="topic-02-career-driver--薪资"', result)
        self.assertIn('href="#topic-02-career-driver--薪资"', result)

    def test_cross_topic_html_link_targets_library_anchor(self):
        source = ROOT / "02-career-driver/reports"
        target = ROOT / "08-visa-immigration/reports/日本签证与在留资格知识手册.html"
        result = library.rewrite_href(
            "../../08-visa-immigration/reports/日本签证与在留资格知识手册.html#永住",
            "02-career-driver", source, {target.resolve(): "08-visa-immigration"},
        )
        self.assertEqual("#topic-08-visa-immigration--永住", result)

    def test_missing_source_fails(self):
        config = {"id": "99-missing", "name": "缺失", "kind": "knowledge",
                  "target": "99-missing/reports/缺失.md", "category": "测试", "description": "测试"}
        with self.assertRaises(library.BuildError):
            library.resolve_topic_source(config)

    def test_monitor_source_uses_scheduler_latest_report(self):
        config = library.load_topics()[0]
        expected = ROOT / "01-ssw-driver/reports/日本特定技能司机物流监测报告_v2026.11.12_5.md"
        with patch("build_library.update_scheduler.latest_report", return_value=expected) as latest:
            source, _ = library.resolve_topic_source(config)
        latest.assert_called_once_with(config)
        self.assertEqual(expected, source)
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python prompts/tools/test_build_library.py RenderingTests -v`
Expected: 因 `namespace_html`、`rewrite_href`、`resolve_topic_source` 尚未实现而 FAIL。

- [ ] **Step 3: 实现源文件解析与 HTML 重写**

实现以下确定接口：

```python
def topic_anchor(topic_id):
    return f"topic-{topic_id}"

def heading_anchor(topic_id, original_id):
    return f"{topic_anchor(topic_id)}--{original_id}"

def resolve_topic_source(config):
    require_display_metadata(config)
    source = update_scheduler.latest_report(config) if config["kind"] == "monitor" else ROOT / config["target"]
    if source is None or not source.is_file() or not source.read_text(encoding="utf-8").strip():
        raise BuildError(f"[{config['id']}] 主文档不存在或为空: {source}")
    html = source.with_suffix(".html")
    if not html.is_file():
        raise BuildError(f"[{config['id']}] 独立 HTML 不存在: {html}")
    return source, html
```

`rewrite_href()` 依次处理：内部 `#` 锚点；外部 scheme 和 `//`；已登记主题 HTML；其他相对路径。普通相对路径用 `(source_dir / unquote(parsed.path)).resolve()` 定位，再以 `relative_to(ROOT)` 和 `quote(relative_path.as_posix(), safe='/')` 转为根目录 URL，保留 query、fragment 与末尾 `/`。

`namespace_html()` 用正则只处理 Markdown 生成结构：给 `<h1>`–`<h6>` id 加 `heading_anchor()`，重写 `<a href>`，并将 `<table>` 包入 `<div class="table-wrap">`。另提供 `extract_chapters(body, topic_id)`，返回 `{title, id, level}` 字典列表；二级标题过滤“导航与使用约定”和以“索引”结尾的元标题。

- [ ] **Step 4: 运行测试并确认通过**

Run: `python prompts/tools/test_build_library.py -v`
Expected: 配置与渲染测试全部 PASS。

- [ ] **Step 5: 检查本任务差异**

Run: `git diff -- prompts/tools/build_library.py prompts/tools/test_build_library.py`
Expected: 只包含生成与测试所需代码。

### Task 3: 两个静态页面、搜索与响应式交互

**Files:**
- Modify: `prompts/tools/build_library.py`
- Modify: `prompts/tools/test_build_library.py`
- Generate: `index.html`
- Generate: `library.html`

- [ ] **Step 1: 写页面覆盖与确定性失败测试**

```python
class PageBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first = library.build_pages()
        cls.second = library.build_pages()

    def test_output_is_deterministic(self):
        self.assertEqual(self.first, self.second)

    def test_all_topics_have_two_way_links(self):
        index = self.first[Path("index.html")]
        library_html = self.first[Path("library.html")]
        for topic in library.load_topics():
            anchor = library.topic_anchor(topic["id"])
            self.assertIn(f'id="{anchor}"', index)
            self.assertIn(f'id="{anchor}"', library_html)
            self.assertIn(f'href="library.html#{anchor}"', index)
            self.assertIn(f'href="index.html#{anchor}"', library_html)

    def test_library_retains_source_content(self):
        output = self.first[Path("library.html")]
        self.assertIn("日本司机职业知识手册", output)
        self.assertIn("02 薪资结构与工时合规", output)
        self.assertIn("日本签证与在留资格知识手册", output)
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python prompts/tools/test_build_library.py PageBuildTests -v`
Expected: 因 `build_pages` 尚未实现而 FAIL。

- [ ] **Step 3: 实现两阶段构建与 HTML 模板**

`build_pages()` 先解析所有主题源文件并建立 `source_html.resolve() -> topic_id` 映射，再逐主题调用 `markdown.markdown()`、`namespace_html()`、`extract_chapters()`，最后返回 `{Path('index.html'): str, Path('library.html'): str}`。版本通过 `update_scheduler.topic_version()` 获取。

总览模板必须输出：顶部三入口、搜索框、分类锚点、按分类排列的 13 张卡片、版本/类型/章节数、`<details>` 章节列表、汇总与独立原文链接。

汇总模板必须输出：返回总览与更新看板、全文搜索框、折叠主题导航、13 个 `<section class="topic-document">`、每主题本地目录、返回卡片与独立原文链接、完整正文和 `<noscript>` 搜索降级说明。

CSS 使用 `BASE_CSS`，补充 `.topic-card`、`.category-nav`、`.library-layout`、`.topic-navigation`、`.search-results`、`.table-wrap`、`:target`、`@media (max-width: 760px)`。桌面为侧栏加正文，窄屏卡片单列、导航折叠、表格横向滚动。

- [ ] **Step 4: 实现原生 JavaScript 搜索与快捷键**

总览脚本从卡片和章节链接生成搜索记录，支持空白分词、150ms 防抖、30 条结果、分类筛选、无结果提示；章节结果使用真实 `library.html#{主题命名空间锚点}` 链接。

汇总脚本遍历每主题标题、段落、列表项和表格行，记录最近标题作为跳转目标；生成含主题名、章节名和短摘要的结果。`/` 聚焦搜索，`Esc` 清空；结果使用 `textContent` 创建，点击后隐藏结果面板并保留浏览器原生锚点跳转。

- [ ] **Step 5: 运行测试、构建并确认通过**

Run: `python prompts/tools/test_build_library.py -v; python prompts/tools/build_library.py`
Expected: 全部单元测试 PASS；生成根目录 `index.html` 与 `library.html`，包含 13 个主题。

- [ ] **Step 6: 检查构建确定性**

Run: `git diff --stat; python prompts/tools/build_library.py; git diff --stat`
Expected: 第二次构建前后差异统计不变，无时间戳或随机输出。

### Task 4: 规范校验、CI 同步与项目入口

**Files:**
- Modify: `prompts/tools/validate.py`
- Modify: `.github/workflows/html-sync.yml`
- Modify: `README.md`
- Modify: `prompts/tools/test_build_library.py`

- [ ] **Step 1: 写生成文件同步失败测试**

```python
class GeneratedOutputTests(unittest.TestCase):
    def test_committed_pages_are_current(self):
        for relative, expected in library.build_pages().items():
            actual = ROOT / relative
            self.assertTrue(actual.is_file(), f"缺少生成页面: {relative}")
            self.assertEqual(expected, actual.read_text(encoding="utf-8"), f"页面需要重新生成: {relative}")
```

- [ ] **Step 2: 运行测试并确认当前行为**

Run: `python prompts/tools/test_build_library.py GeneratedOutputTests -v`
Expected: 构建后 PASS；临时修改任一生成页面时 FAIL，恢复后 PASS。

- [ ] **Step 3: 实现构建器检查模式与第 11 项校验**

`build_library.py` 增加 `--check`：调用 `build_pages()` 比较现有文件，缺失或内容不同则输出路径并返回 1，全部一致返回 0；默认模式在所有主题成功解析和渲染后才写入两个页面。

`validate.py` 增加 `check_library_pages(errors, warnings)`，检查两个根页面存在、每个 `topic-{id}` 在两侧存在、卡片和返回链接存在，并调用构建器检查逻辑判断陈旧输出。将 `(11, "聚合页面同步", check_library_pages)` 注册到 `CHECKS`，更新模块顶部说明。

- [ ] **Step 4: 接入 CI 与 README**

`html-sync.yml` 的触发路径增加 `prompts/schedule.json`、`prompts/tools/build_library.py`；在 `md2html.py` 后执行 `python prompts/tools/build_library.py`；清理步骤额外排除 `./index.html` 和 `./library.html`。

README 顶部增加 `[主题总览](index.html)` 与 `[汇总阅读](library.html)`；目录结构列出两个生成页面及 `build_library.py`；使用约定增加生成命令，规范校验数量改为 11 项。

- [ ] **Step 5: 运行测试与全量规范校验**

Run: `python prompts/tools/test_build_library.py -v; python prompts/tools/build_library.py --check; python prompts/tools/validate.py`
Expected: 单元测试 PASS，`--check` 返回 0，规范校验无新增错误或警告。

### Task 5: 浏览器端到端验收

**Files:**
- Verify: `index.html`
- Verify: `library.html`
- Verify: `01-ssw-driver/reports/日本特定技能司机物流监测报告_v2026.11.12_5.html`

- [ ] **Step 1: 启动静态预览并检查初始页面**

Run: `python -m http.server 8000 --bind 127.0.0.1`
Expected: 浏览器打开 `http://localhost:8000/index.html`，显示 13 张主题卡片和 7 个分类；`library.html` 显示 13 个连续主题。

- [ ] **Step 2: 验证总览搜索、详情与锚点**

在总览搜索“司机 薪资”，确认出现 02 主题及“02 薪资结构与工时合规”等章节结果。展开主题详情，点击章节，确认进入 `library.html#topic-02-career-driver--02-薪资结构与工时合规` 且目标高亮。

- [ ] **Step 3: 验证返回闭环与独立原文**

点击汇总主题“返回主题总览”，确认进入 `index.html#topic-02-career-driver` 并定位原卡片。分别点击两页“独立原文”，确认打开 `02-career-driver/reports/日本司机职业知识手册.html`，正文和来源链接可用。

- [ ] **Step 4: 验证全文检索和监测版本**

在汇总页搜索“永住”，确认结果含主题与章节摘要，点击后精确定位。返回总览打开 01 监测主题，确认其独立原文指向当前最新 `_v2026.11.12_5.html`，不是 baseline 或历史归档。

- [ ] **Step 5: 验证响应式与浏览器健康状态**

在桌面和约 390px 宽度检查：卡片单列、目录可展开、表格仅在容器内横向滚动、`document.documentElement.scrollWidth <= window.innerWidth`、控制台无 JavaScript 错误。禁用 JavaScript 后确认正文、目录和双向链接仍可使用。

- [ ] **Step 6: 最终回归与差异检查**

Run: `python prompts/tools/test_build_library.py -v; python prompts/tools/build_library.py --check; python prompts/tools/validate.py; git status --short`
Expected: 测试和规范校验通过，两个生成页面为最新；`updates.md`、`updates.html`、`自动化更新方案.md` 保留用户原改动，本任务不提交、不推送。
