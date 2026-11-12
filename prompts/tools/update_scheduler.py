# -*- coding: utf-8 -*-
"""周期更新调度器（全库共用）。

职责：
  1. 读取 prompts/schedule.json，按主题节奏计算到期状态；
  2. dispatch：为到期主题创建幂等的 GitHub Issue 工单（同一主题同时只保留一个未关闭工单）；
  3. dashboard：生成根目录 updates.md 更新看板（提交入库，供个人定期查阅与回溯）；
  4. alert：调度失败时创建/追加 ops-alert Issue；
  5. status：本地查看当前排期状态。

设计约束：
  - 不联网、不调用 LLM，内容更新由 AI IDE / 本人按工单执行；
  - 只读 git 历史判断"上次更新"，不维护易漂移的状态文件；
  - Issue 创建与告警均幂等，重复运行不会刷屏。

用法:
    python prompts/tools/update_scheduler.py status
    python prompts/tools/update_scheduler.py status --json
    python prompts/tools/update_scheduler.py dispatch --dry-run
    python prompts/tools/update_scheduler.py dispatch
    python prompts/tools/update_scheduler.py dispatch --force 08-visa-immigration
    python prompts/tools/update_scheduler.py dashboard
    python prompts/tools/update_scheduler.py alert --reason "定时调度失败"

退出码: 0 = 正常；1 = 配置/命令失败。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from string import Template
from urllib.parse import quote

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "prompts" / "schedule.json"
DASHBOARD_PATH = ROOT / "updates.md"
JST = timezone(timedelta(hours=9))

LABEL_TASK = "update-task"
LABEL_ALERT = "ops-alert"

ISSUE_TEMPLATE = Template("""## 周期更新任务：$topic_id $topic_name

> 本工单由 `.github/workflows/scheduled-update.yml` 在 $created_at 自动创建。
> 同一主题同时只保留一个未关闭工单；完成后请回复版本号与提交 SHA 再关闭。

| 项 | 内容 |
|---|---|
| 主题目录 | `$topic_id` |
| 更新节奏 | 每 $cadence 天 |
| 上次更新 | $last_update |
| 本次到期 | $next_due（$status_text） |
| 主文档 | [$handbook_name]($handbook_url) |
| 更新提示词 | [prompt]($prompt_url) |
| 指标登记册 | [registry]($registry_url) |

## 执行步骤

1. 在 Trae / AI IDE 中打开更新提示词，按文件头部说明填写 `$current_date_var` 等运行变量。
2. 先读主文档与指标登记册，继承「已修正事实清单」，禁止回退已修正结论。
3. 仅增量回写主文档受影响章节；新知识在手册内顺延新建 `## NN 章节名`，禁止新建零散 `.md`。
4. 回写手册内「更新日志」与 `data/` 指标登记册。
5. 本地执行以下命令，确认 HTML 已生成、归档已整理、规范校验无错误：

```bash
python prompts/tools/md2html.py $topic_id/reports
python prompts/tools/archive_reports.py
python prompts/tools/validate.py
```

6. 提交后在本 Issue 回复「版本号 + 提交 SHA」，然后关闭本 Issue。

## 验收清单

- [ ] 每个新增数据点均附可访问来源；冲突数据并列双报
- [ ] 已修正事实无回退；空窗期未虚构变化
- [ ] 单文档约束满足（1 份主文档 + 同名 HTML）
- [ ] 更新日志与指标登记册已同步
- [ ] `validate.py` 退出码为 0 或 2（无错误）
""")

ALERT_TEMPLATE = Template("""## 告警：$reason

- 工作流：$workflow
- 运行：$run_url
- 分支：$ref
- 提交：$sha
- 时间：$created_at

### 处理建议

1. 打开运行日志定位失败步骤：$run_url
2. 修复后手动重跑：`gh workflow run scheduled-update.yml`
3. 若为权限问题，检查仓库 Settings → Actions → General → Workflow permissions 是否为 **Read and write**。
4. 恢复后关闭本 Issue；再次失败会以评论形式追加到本 Issue，不重复新建。

$mention
""")


# ──────────────────────────────────────────────
# 基础工具
# ──────────────────────────────────────────────

def git(*args: str) -> str:
    """执行 git 命令并返回 stdout（失败返回空字符串）。"""
    try:
        proc = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def detect_repo() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if repo:
        return repo
    remote = git("remote", "get-url", "origin")
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", remote)
    return m.group(1) if m else ""


def detect_branch() -> str:
    return (
        os.environ.get("GITHUB_REF_NAME", "").strip()
        or git("rev-parse", "--abbrev-ref", "HEAD")
        or "main"
    )


def repo_url(rel_path: str, is_dir: bool = False) -> str:
    """仓库相对路径 → GitHub 可访问 URL；无仓库信息时退回相对路径。"""
    repo = detect_repo()
    if not repo:
        return rel_path
    kind = "tree" if is_dir else "blob"
    return (
        f"https://github.com/{repo}/{kind}/{detect_branch()}/"
        f"{quote(rel_path.replace(os.sep, '/'), safe='/')}"
    )


def log(msg: str) -> None:
    print(msg)


def fail(msg: str) -> int:
    print(f"错误: {msg}", file=sys.stderr)
    return 1


def require_gh() -> bool:
    try:
        proc = subprocess.run(
            ["gh", "--version"], capture_output=True, text=True, timeout=30
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def run_gh(args: list[str], attempts: int = 3, base_delay: float = 2.0):
    """调用 gh，失败按指数退避重试。返回 CompletedProcess。"""
    last: subprocess.CompletedProcess | None = None
    for attempt in range(1, attempts + 1):
        last = subprocess.run(
            ["gh", *args], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
        if last.returncode == 0:
            return last
        if attempt < attempts:
            time.sleep(base_delay ** attempt)
    raise RuntimeError(
        f"gh 命令失败（已重试 {attempts} 次）: gh {' '.join(args)}\n"
        f"stdout: {last.stdout if last else ''}\nstderr: {last.stderr if last else ''}"
    )


# ──────────────────────────────────────────────
# 配置与排期计算
# ──────────────────────────────────────────────

def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_config(cfg: dict) -> list[str]:
    """配置与目录一致性校验：路径存在、主题全覆盖、无重复。"""
    errors: list[str] = []
    topics = cfg.get("topics") or []
    if not topics:
        return ["schedule.json 未配置任何主题"]

    seen: set[str] = set()
    for topic in topics:
        tid = topic.get("id", "")
        if not tid or not re.match(r"^\d{2}-", tid):
            errors.append(f"主题 id 非法: {tid!r}（须为 NN-* 形式）")
            continue
        if tid in seen:
            errors.append(f"主题 id 重复: {tid}")
        seen.add(tid)
        for key in ("name", "target", "prompt", "registry"):
            if not topic.get(key):
                errors.append(f"[{tid}] 缺少字段: {key}")
        for key in ("target", "prompt", "registry"):
            rel = topic.get(key)
            if rel and not (ROOT / rel).exists():
                errors.append(f"[{tid}] {key} 路径不存在: {rel}")

    dirs = {
        p.name for p in ROOT.iterdir()
        if p.is_dir() and re.match(r"^\d{2}-", p.name)
    }
    missing = sorted(dirs - seen)
    extra = sorted(seen - dirs)
    if missing:
        errors.append(
            "以下主题目录未登记到 schedule.json: " + ", ".join(missing)
        )
    if extra:
        errors.append(
            "schedule.json 含不存在的主题目录: " + ", ".join(extra)
        )
    return errors


def topic_last_update(topic: dict) -> tuple[str | None, str]:
    """返回 (最后提交日期 YYYY-MM-DD, 短 SHA)；无历史时为 (None, "")。"""
    target = topic["target"]
    date_str = git("log", "-1", "--format=%cs", "--", target)
    sha = git("log", "-1", "--format=%h", "--", target)
    return (date_str or None, sha)


def topic_recent_commits(topic: dict, limit: int = 3) -> list[tuple[str, str]]:
    out = git(
        "log", f"-{limit}", "--format=%cs%x09%h", "--", topic["target"]
    )
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            rows.append((parts[0], parts[1]))
    return rows


VERSION_RE = re.compile(r"_v(\d{4})\.(\d{2})\.(\d{2})(?:_(\d+))?$")


def latest_report(topic: dict) -> Path | None:
    """监测类：返回最新一期报告 md（按日期+序号，基线仅作兜底）。"""
    reports = ROOT / topic["target"]
    if not reports.is_dir():
        return None
    candidates = [f for f in reports.glob("*.md") if VERSION_RE.search(f.stem)]
    if candidates:
        return max(
            candidates,
            key=lambda f: tuple(
                int(x or 0) for x in VERSION_RE.search(f.stem).groups()
            ),
        )
    baseline = sorted(reports.glob("*_baseline.md"))
    return baseline[-1] if baseline else None


def topic_version(topic: dict) -> str:
    if topic.get("kind") == "monitor":
        latest = latest_report(topic)
        if not latest:
            return "—"
        m = VERSION_RE.search(latest.stem)
        if m:
            seq = f"_{m.group(4)}" if m.group(4) else ""
            return f"v{m.group(1)}.{m.group(2)}.{m.group(3)}{seq}"
        return "baseline"
    handbook = ROOT / topic["target"]
    if handbook.is_file():
        head = "\n".join(handbook.read_text(encoding="utf-8").splitlines()[:30])
        m = re.search(r"\*\*版本\*\*[：:]\s*(v[\d.]+)", head)
        if m:
            return m.group(1)
    return "—"


def compute_status(topic: dict, today: date, due_soon_days: int) -> dict:
    last_date, sha = topic_last_update(topic)
    cadence = int(topic.get("cadence_days", 90))
    if not last_date:
        return {
            "last": None, "sha": "", "next_due": None,
            "days_left": -10**6, "key": "no_history", "text": "无更新记录",
            "cadence": cadence, "due": True,
        }
    last = date.fromisoformat(last_date)
    next_due = last + timedelta(days=cadence)
    days_left = (next_due - today).days
    if days_left < 0:
        key, text = "overdue", f"已逾期 {abs(days_left)} 天"
    elif days_left == 0:
        key, text = "overdue", "今日到期"
    elif days_left <= due_soon_days:
        key, text = "due_soon", f"{days_left} 天后到期"
    else:
        key, text = "ok", "正常"
    return {
        "last": last_date, "sha": sha, "next_due": next_due.isoformat(),
        "days_left": days_left, "key": key, "text": text,
        "cadence": cadence, "due": key in ("overdue", "no_history"),
    }


def gather(cfg: dict) -> list[dict]:
    today = datetime.now(JST).date()
    due_soon = int(cfg.get("dispatch", {}).get("due_soon_days", 7))
    rows = []
    for topic in cfg["topics"]:
        rows.append({
            "topic": topic,
            "status": compute_status(topic, today, due_soon),
            "version": topic_version(topic),
        })
    return rows


# ──────────────────────────────────────────────
# status
# ──────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> int:
    cfg = load_config()
    errors = validate_config(cfg)
    if errors:
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    rows = gather(cfg)
    if args.json:
        print(json.dumps(
            [
                {
                    "id": r["topic"]["id"],
                    "name": r["topic"]["name"],
                    "cadence_days": r["status"]["cadence"],
                    "last_update": r["status"]["last"],
                    "last_sha": r["status"]["sha"],
                    "next_due": r["status"]["next_due"],
                    "days_left": r["status"]["days_left"],
                    "status": r["status"]["key"],
                    "version": r["version"],
                }
                for r in rows
            ],
            ensure_ascii=False, indent=2,
        ))
        return 0

    print(f"{'主题':<28}{'节奏':<8}{'上次更新':<14}{'下次到期':<14}{'状态'}")
    print("-" * 84)
    for r in rows:
        t, s = r["topic"], r["status"]
        print(
            f"{t['id']:<28}{s['cadence']:>3} 天   "
            f"{s['last'] or '—':<14}{s['next_due'] or '—':<14}{s['text']}"
        )
    due = [r for r in rows if r["status"]["due"]]
    print(f"\n已到期: {len(due)} / {len(rows)}")
    return 0


# ──────────────────────────────────────────────
# dashboard
# ──────────────────────────────────────────────

def md_link(text: str, rel_path: str) -> str:
    return f"[{text}]({rel_path.replace(os.sep, '/')})"


def cmd_dashboard(args: argparse.Namespace) -> int:
    cfg = load_config()
    errors = validate_config(cfg)
    if errors:
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    rows = gather(cfg)
    now = datetime.now(JST)
    due = [r for r in rows if r["status"]["due"]]
    soon = [r for r in rows if r["status"]["key"] == "due_soon"]
    ok = [r for r in rows if r["status"]["key"] == "ok"]

    lines: list[str] = [
        "# 周期更新看板",
        "",
        "> **自动生成**：由 `prompts/tools/update_scheduler.py` 生成，请勿手工编辑"
        "（手工改动会在下次调度时被覆盖）。",
        f"> **生成时间**：{now:%Y-%m-%d %H:%M} JST　"
        "**排期配置**：[schedule.json](prompts/schedule.json)　"
        "**调度工作流**：[scheduled-update.yml](.github/workflows/scheduled-update.yml)",
        "",
        "## 总览",
        "",
        f"- 主题总数：**{len(rows)}**　已到期：**{len(due)}**　"
        f"7 天内到期：**{len(soon)}**　正常：**{len(ok)}**",
        "- 调度节奏：每周一 09:15 JST 自动巡检；各主题节奏见下表（由 schedule.json 驱动）。",
        "- 到期后自动创建 GitHub Issue 工单（标签 `update-task`），由 AI IDE 或本人执行内容更新。",
        "",
        "## 主题状态",
        "",
        "| 主题 | 类型 | 节奏 | 上次更新 | 下次到期 | 状态 | 当前版本 | 入口 |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for r in rows:
        t, s = r["topic"], r["status"]
        kind = "监测" if t.get("kind") == "monitor" else "知识"
        last = f"{s['last']}（{s['sha']}）" if s["last"] else "—"
        nxt = s["next_due"] or "—"
        status = s["text"]
        version = r["version"]

        if t.get("kind") == "monitor":
            latest = latest_report(t)
            reports_dir = t["target"].rstrip("/")
            links = []
            if latest:
                rel = str(latest.relative_to(ROOT))
                hm = latest.with_suffix(".html")
                links.append(md_link("报告", rel))
                if hm.exists():
                    links.append(md_link("HTML", str(hm.relative_to(ROOT))))
            links.append(md_link("历史", reports_dir + "/archives/"))
            links.append(md_link("提示词", t["prompt"]))
        else:
            handbook = t["target"]
            hm = str(Path(handbook).with_suffix(".html"))
            links = [md_link("手册", handbook)]
            if (ROOT / hm).exists():
                links.append(md_link("HTML", hm))
            links.append(md_link("历史", str(Path(handbook).parent / "archives") + "/"))
            links.append(md_link("提示词", t["prompt"]))
        lines.append(
            f"| {t['id']} {t['name']} | {kind} | {s['cadence']} 天 | {last} | "
            f"{nxt} | {status} | {version} | {' · '.join(links)} |"
        )

    lines += [
        "",
        "## 到期队列",
        "",
    ]
    if not due:
        lines.append("当前无到期主题。")
    else:
        ordered = sorted(
            due,
            key=lambda r: (r["topic"].get("priority", 99), r["status"]["days_left"]),
        )
        for i, r in enumerate(ordered, 1):
            t, s = r["topic"], r["status"]
            lines.append(
                f"{i}. **{t['id']} {t['name']}** — {s['text']}；"
                f"更新入口：{md_link('提示词', t['prompt'])} · "
                f"{md_link('主文档', t['target'])}"
            )

    lines += [
        "",
        "## 查阅与追溯",
        "",
        "| 追溯对象 | 入口 | 说明 |",
        "|---|---|---|",
        "| 监测报告版本链 | [01-ssw-driver/reports](01-ssw-driver/reports/) · "
        "[archives](01-ssw-driver/reports/archives/) | 文件名含版本号，基线常驻顶层 |",
        "| 知识手册历次版本 | 各主题 `reports/` 下的手册 → GitHub 文件 History | "
        "单文档增量回写；变更摘要记入手册「更新日志」 |",
        "| 更新工单 | [update-task]"
        "(issues?q=is%3Aissue+label%3Aupdate-task) | 每个到期主题一个工单，关闭即完成 |",
        "| 调度异常 | [ops-alert]"
        "(issues?q=is%3Aissue+label%3Aops-alert) | 由失败的工作流自动创建 |",
        "| 规范校验 | [validate.py](prompts/tools/validate.py) | 提交前与 CI 双重执行 |",
        "",
        "## 使用说明",
        "",
        "1. **定期查阅**：打开本页 → 看「到期队列」→ 进入对应提示词执行更新。",
        "2. **手机查阅**：在 GitHub 仓库首页点 `updates.md` 即可阅读；"
        "HTML 版适合本地双击打开。",
        "3. **回溯历史**：监测报告直接打开 `archives/`；知识手册用 GitHub History "
        "对比任意两次提交。",
        "4. **调整节奏**：编辑 `prompts/schedule.json` 中对应主题的 `cadence_days`，"
        "下次调度自动生效。",
        "",
    ]

    out = Path(args.output) if args.output else DASHBOARD_PATH
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    log(f"看板已生成: {out.relative_to(ROOT)}（已到期 {len(due)} 个主题）")
    return 0


# ──────────────────────────────────────────────
# dispatch
# ──────────────────────────────────────────────

def ensure_label(name: str, color: str, description: str) -> None:
    try:
        run_gh([
            "label", "create", name, "--force",
            "--color", color, "--description", description,
        ], attempts=2, base_delay=1.0)
    except RuntimeError as exc:
        print(f"警告: 标签 {name} 创建/更新失败（若已存在可忽略）: {exc}",
              file=sys.stderr)


def open_task_issues() -> dict[str, int]:
    """已存在的未关闭更新工单：{topic_id: issue_number}。"""
    out = run_gh([
        "issue", "list", "--label", LABEL_TASK, "--state", "open",
        "--limit", "100", "--json", "number,title",
    ])
    mapping: dict[str, int] = {}
    for item in json.loads(out.stdout or "[]"):
        m = re.match(r"^\[更新任务\]\s+(\d{2}-[^\s]+)", item.get("title", ""))
        if m:
            mapping[m.group(1)] = int(item["number"])
    return mapping


def build_issue_body(topic: dict, status: dict, now: datetime) -> str:
    target = topic["target"]
    handbook_name = Path(target).name if Path(target).is_file() else "reports/"
    return ISSUE_TEMPLATE.substitute(
        topic_id=topic["id"],
        topic_name=topic["name"],
        created_at=f"{now:%Y-%m-%d %H:%M} JST",
        cadence=status["cadence"],
        last_update=(f"{status['last']}（{status['sha']}）"
                     if status["last"] else "无记录（首期）"),
        next_due=status["next_due"] or "现在",
        status_text=status["text"],
        handbook_name=handbook_name,
        handbook_url=repo_url(target, is_dir=not Path(target).is_file()),
        prompt_url=repo_url(topic["prompt"]),
        registry_url=repo_url(topic["registry"]),
        current_date_var="{{CURRENT_DATE}}",
    )


def cmd_dispatch(args: argparse.Namespace) -> int:
    cfg = load_config()
    errors = validate_config(cfg)
    if errors:
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1

    rows = gather(cfg)
    force = (args.force or "").strip()
    if force and force != "all":
        matched = [r for r in rows if r["topic"]["id"] == force]
        if not matched:
            return fail(f"--force 指定的主题不存在: {force}")
        selected = matched
    elif force == "all":
        selected = rows
    else:
        selected = [r for r in rows if r["status"]["due"]]
        selected.sort(key=lambda r: (
            r["topic"].get("priority", 99), r["status"]["days_left"],
        ))
        limit = int(cfg.get("dispatch", {}).get("max_issues_per_run", 4))
        selected = selected[:limit]

    if not selected:
        log("没有到期主题，无需创建工单。")
        return 0

    if not args.dry_run and not require_gh():
        return fail("未找到 gh CLI，无法创建 Issue；可用 --dry-run 预览。")

    existing: dict[str, int] = {}
    if not args.dry_run:
        ensure_label(LABEL_TASK, "0E8A16", "周期更新任务工单")
        existing = open_task_issues()

    now = datetime.now(JST)
    created = skipped = 0
    for r in selected:
        topic, status = r["topic"], r["status"]
        tid = topic["id"]
        if tid in existing:
            log(f"跳过 {tid}: 已存在未关闭工单 #{existing[tid]}")
            skipped += 1
            continue

        title = f"[更新任务] {tid} {topic['name']}（到期 {status['next_due'] or '现在'}）"
        body = build_issue_body(topic, status, now)
        if args.dry_run:
            print("=" * 72)
            print(f"标题: {title}")
            print(body)
            print()
            created += 1
            continue

        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".md", delete=False, newline="\n"
        ) as fh:
            fh.write(body)
            body_path = fh.name
        try:
            out = run_gh([
                "issue", "create",
                "--title", title,
                "--body-file", body_path,
                "--label", LABEL_TASK,
            ])
            log(f"已创建工单 {tid}: {out.stdout.strip().splitlines()[-1]}")
            created += 1
        finally:
            Path(body_path).unlink(missing_ok=True)

    log(f"完成：新建 {created}，跳过 {skipped}，候选 {len(selected)}")
    return 0


# ──────────────────────────────────────────────
# alert
# ──────────────────────────────────────────────

def cmd_alert(args: argparse.Namespace) -> int:
    if not require_gh():
        return fail("未找到 gh CLI，无法创建告警 Issue。")
    ensure_label(LABEL_ALERT, "B60205", "自动化调度异常告警")

    now = datetime.now(JST)
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = detect_repo()
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    run_url = f"{server}/{repo}/actions/runs/{run_id}" if run_id else "（本地运行，无 URL）"
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    body = ALERT_TEMPLATE.substitute(
        reason=args.reason,
        workflow=os.environ.get("GITHUB_WORKFLOW", "scheduled-update"),
        run_url=run_url,
        ref=detect_branch(),
        sha=os.environ.get("GITHUB_SHA", git("rev-parse", "--short", "HEAD"))[:7],
        created_at=f"{now:%Y-%m-%d %H:%M} JST",
        mention=f"@{owner}" if owner else "",
    )

    out = run_gh([
        "issue", "list", "--label", LABEL_ALERT, "--state", "open",
        "--limit", "100", "--json", "number,title",
    ])
    title = "[告警] 周期更新调度失败"
    for item in json.loads(out.stdout or "[]"):
        if item.get("title") == title:
            run_gh([
                "issue", "comment", str(item["number"]),
                "--body", f"再次失败：{run_url}（{now:%Y-%m-%d %H:%M} JST）",
            ])
            log(f"已追加告警评论到 #{item['number']}")
            return 0

    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".md", delete=False, newline="\n"
    ) as fh:
        fh.write(body)
        body_path = fh.name
    try:
        created = run_gh([
            "issue", "create", "--title", title,
            "--body-file", body_path, "--label", LABEL_ALERT,
        ])
        log(f"已创建告警 Issue: {created.stdout.strip().splitlines()[-1]}")
    finally:
        Path(body_path).unlink(missing_ok=True)
    return 0


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="周期更新调度器")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="查看各主题到期状态")
    p_status.add_argument("--json", action="store_true", help="输出 JSON")
    p_status.set_defaults(func=cmd_status)

    p_dispatch = sub.add_parser("dispatch", help="为到期主题创建工单")
    p_dispatch.add_argument("--dry-run", action="store_true", help="只预览，不调用 gh")
    p_dispatch.add_argument(
        "--force", default="",
        help="强制指定主题 id（如 08-visa-immigration）或 all",
    )
    p_dispatch.set_defaults(func=cmd_dispatch)

    p_dash = sub.add_parser("dashboard", help="生成 updates.md 看板")
    p_dash.add_argument("--output", default="", help="输出路径（默认根目录 updates.md）")
    p_dash.set_defaults(func=cmd_dashboard)

    p_alert = sub.add_parser("alert", help="创建或追加调度告警 Issue")
    p_alert.add_argument("--reason", default="周期更新调度工作流运行失败")
    p_alert.set_defaults(func=cmd_alert)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
