# 根目录整理设计（docs/ 与 site/ 分离）

**日期**：2026-11-12
**状态**：待批准
**范围**：仓库根目录的 .md / .html 归位；不改动 13 个主题目录内部结构

---

## 1. 意图与原因

根目录散落 9 个 .md/.html 文件：4 份规范/方案文档、`README.md`、3 个生成的阅读页面、看板源文档 `updates.md`。
目标：把「源文档」与「构建产物」分层，让根目录只保留项目入口与配置，达到常见仓库的最佳实践。

## 2. 目标 / 非目标 / 反目标

**目标**
- 根目录只保留 `README.md`、`requirements.txt`、`.gitignore`
- 规范/方案文档集中到 `docs/`
- 生成的阅读站集中到 `site/`
- 不破坏 CI、GitHub Pages（若启用）与所有内部链接

**非目标**
- 不改动 13 个主题目录内部结构（`data/prompts/reports` 保持不变）
- 不改动提示词三层继承体系
- 不重写任何报告内容

**反目标（失败信号）**
- CI workflow 路径失效
- 聚合页互链或「独立原文」链接 404
- 规范文档之间的交叉引用失效

## 3. 约束

- `build_library.py` 在根生成 index/library，页内互链为相对路径（`library.html#…`），并链接 `NN-*/reports/*.html`
- `validate.py` 第 11 项要求 index/library 在根
- `update_scheduler.py` 在根写 `updates.md`；`scheduled-update.yml` 执行 `md2html.py updates.md` 并 `git add updates.md updates.html`
- `html-sync.yml` 清理步骤白名单了根目录三个 html
- 仓库无 `_config.yml`；若启用 GitHub Pages（源=根），需把源切到 `site/`
- 已核实：13 个主题的 reports md **不**引用根页面，无需改动

## 4. 方案选择

| 方案 | 做法 | 取舍 | 结论 |
|---|---|---|---|
| A | 仅 4 份规范 md → `docs/` | 零风险，但根目录仍剩 5 个文件 | 否 |
| B | 规范 md → `docs/`；生成页 → `site/` | 根目录最干净，需改脚本/CI/链接 | **采纳** |
| C | 全部 → `docs/`，Pages 源=docs/ | docs/ 混入构建产物，与「HTML 仅 reports/ 入库」约定冲突 | 否 |

## 5. 目标结构

```text
jp-life-work/
├── README.md
├── requirements.txt
├── .gitignore
├── docs/                          # 源文档
│   ├── 内容边界规范.md
│   ├── 内容更新周期标准.md
│   ├── 自动化更新方案.md
│   ├── 基线报告管理规则.md
│   └── superpowers/               # 现有设计/计划存档
├── site/                          # 生成的阅读站（构建产物）
│   ├── index.html
│   ├── library.html
│   ├── updates.html
│   └── updates.md                 # 看板源文档（与 updates.html 同目录）
├── prompts/                       # 提示词 + tools
└── NN-*/                          # 13 个主题
```

> `site/` 为命名选择，可替换为 `public/` 等；一经确定，全库统一。

## 6. 改动清单

### 6.1 文件移动
- `内容边界规范.md`、`内容更新周期标准.md`、`自动化更新方案.md`、`基线报告管理规则.md` → `docs/`
- `index.html`、`library.html` → `site/`
- `updates.md`、`updates.html` → `site/`

### 6.2 脚本
- `build_library.py`：`build_pages()` 输出改为 `site/index.html`、`site/library.html`；「独立原文」链接加 `../` 前缀；写入前 `mkdir -p site/`
- `validate.py`：第 11 项路径改为 `site/index.html`、`site/library.html`
- `update_scheduler.py`：`DASHBOARD_PATH = ROOT / "site/updates.md"`；看板内所有根相对链接统一加 `../` 前缀；写入前 `mkdir -p site/`；同步帮助文本
- `archive_reports.py`：docstring 中 `基线报告管理规则.md` → `docs/基线报告管理规则.md`
- `test_build_library.py`：`Path("index.html")` / `Path("library.html")` → `site/…`

### 6.3 CI
- `html-sync.yml`：清理白名单改为 `site/*.html`
- `scheduled-update.yml`：`md2html.py site/updates.md`；`git add site/updates.md site/updates.html`

### 6.4 链接与文档
- `README.md`：更新顶部入口链接、目录结构图、使用约定
- 4 份规范文档：更新交叉引用（`../README.md`、`../prompts/…`）
- 13 个主题提示词 + 通用基座 + 2 个脚手架：`../../基线报告管理规则.md` → `../../docs/基线报告管理规则.md`
- `updates.md`：由 `update_scheduler.py` 生成，链接前缀随生成器统一处理（见 6.2），不手工编辑
- `.gitignore`：更新「HTML 入库」约定注释

### 6.5 明确不改动
- `docs/superpowers/` 下的历史设计/计划文档（历史记录，保持原样）
- 13 个主题目录内部结构
- 报告内容

## 7. 验收

- `python prompts/tools/validate.py` 12 项全通过
- `python prompts/tools/build_library.py --check` 通过
- `python -m unittest discover -s prompts/tools/tests -p "test_*.py"` 通过
- 全库检索无失效的根页面引用
- 聚合页互链与「独立原文」链接可解析

## 8. 留给实施者

- 批量链接替换的实现方式（脚本或手工）
- 是否同时清理 gitignored 临时目录（`_tmp_prompt-polish/`、`.trae-html-share-packages/`、`.superpowers/brainstorm/`）
