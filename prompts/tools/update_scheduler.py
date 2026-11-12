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
    python prompts/tools/update_scheduler.py alert --kind run_failure --reason "定时调度失败"
    python prompts/tools/update_scheduler.py alert --recovered
    python prompts/tools/update_scheduler.py heartbeat --max-gap-days 10
    python prompts/tools/update_scheduler.py backlog

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

# 告警分级与固定标题（标题是去重键，不可随运行变化）
ALERT_KINDS = {
    "run_failure": ("[告警][P0] 周期更新调度失败", "p0"),
    "heartbeat": ("[告警][P0] 周期调度停摆", "p0"),
    "backlog": ("[告警][P1] 更新任务积压", "p1"),
    "overdue": ("[告警][P2] 更新任务逾期", "p2"),
    "finalize": ("[告警][P1] 内容收口失败", "p1"),
}
SEVERITY_COLORS = {"p0": "B60205", "p1": "D93F0B", "p2": "FBCA04"}
SEVERITY_DESC = {
    "p0": "阻断：调度失败或停摆，需当日处理",
    "p1": "重要：积压或内容收口失败，需 3 日内处理",
    "p2": "提示：逾期预警，下次周检处理",
}

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

| 项 | 内容 |
|---|---|
| 级别 | **$severity_label**（$severity_desc） |
| 工作流 | $workflow |
| 运行 | $run_url |
| 分支 | $ref |
| 提交 | $sha |
| 时间 | $created_at |
| 最近连续失败 | $recent_failures 次（不含本次） |

$detail

### 处理建议

$suggestions

> 去重规则：同一标题同时只保留一个未关闭 Issue；冷却期内重复失败只记录日志，不重复评论。
> 恢复后由成功运行自动追加「已恢复」回执，请确认后关闭本 Issue。

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
        "(issues?q=is%3Aissue+label%3Aops-alert) | 分级 P0/P1/P2；"
        "失败、停摆、积压、收口失败自动创建/追加 |",
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
        lookahead = int(cfg.get("dispatch", {}).get("lookahead_days", 3))

        def dispatchable(row: dict) -> bool:
            status = row["status"]
            if status["due"]:
                return True
            # 短周期主题给提前量，避免"周巡检 + 7 天节奏"被拖成 13 天
            return (
                status["cadence"] <= 7
                and status["last"] is not None
                and status["days_left"] <= lookahead
            )

        selected = [r for r in rows if dispatchable(r)]
        selected.sort(key=lambda r: (
            r["topic"].get("priority", 99), r["status"]["days_left"],
        ))
        limit = int(cfg.get("dispatch", {}).get("max_issues_per_run", 4))
        selected = selected[:limit]
        early = [r for r in selected if not r["status"]["due"]]
        if early:
            log(
                "短周期提前派发: "
                + ", ".join(
                    f"{r['topic']['id']}（{r['status']['text']}）" for r in early
                )
            )

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
# alert（分级、冷却、恢复回执）
# ──────────────────────────────────────────────

ALERT_SUGGESTIONS = {
    "run_failure": (
        "1. 打开运行日志定位失败步骤。\n"
        "2. 修复后手动重跑：`gh workflow run scheduled-update.yml`。\n"
        "3. 若为权限问题，检查 Settings → Actions → General → "
        "Workflow permissions 是否为 **Read and write**。\n"
        "4. 若为网络/配额问题，确认 Actions 分钟数未耗尽。"
    ),
    "heartbeat": (
        "1. 检查工作流是否被禁用：`gh workflow view scheduled-update.yml`。\n"
        "2. 手动启用：`gh workflow enable scheduled-update.yml`。\n"
        "3. 确认默认分支仍有 `schedule` 触发配置。\n"
        "4. 若仓库长期无活动，先手动触发一次恢复计时。"
    ),
    "backlog": (
        "1. 打开 `update-task` 工单列表，优先处理逾期最久的主题。\n"
        "2. 已完成的工单及时关闭，避免占用积压阈值。\n"
        "3. 若某主题长期无法更新，调大 `prompts/schedule.json` 的 "
        "`cadence_days` 或降级优先级。"
    ),
    "overdue": (
        "1. 下次周检时优先处理到期主题。\n"
        "2. 若属于预期内延迟（如出差），可暂不处理，逾期超过 30 天会升级为 P1。\n"
        "3. 关闭已完成工单可避免误判积压。"
    ),
    "finalize": (
        "1. 查看告警下方 `validate.py` 输出，修复规范错误。\n"
        "2. 本地复跑：`python prompts/tools/validate.py`。\n"
        "3. 修复后推送，或对失败运行执行 `gh run rerun <run-id>`。\n"
        "4. 确认 HTML 与归档已随提交入库。"
    ),
}


def open_issue_index(label: str) -> dict[str, int]:
    out = run_gh([
        "issue", "list", "--label", label, "--state", "open",
        "--limit", "100", "--json", "number,title",
    ])
    return {
        item.get("title", ""): int(item["number"])
        for item in json.loads(out.stdout or "[]")
    }


def issue_age_hours(number: int) -> float:
    """Issue 距最近一次更新的小时数，用于告警冷却。"""
    out = run_gh([
        "api", f"repos/{detect_repo()}/issues/{number}", "--jq", ".updated_at",
    ])
    stamp = out.stdout.strip().replace("Z", "+00:00")
    updated = datetime.fromisoformat(stamp)
    return (datetime.now(timezone.utc) - updated).total_seconds() / 3600


def recent_failure_count() -> int:
    """统计最近一次成功之前的连续失败次数。"""
    try:
        out = run_gh([
            "run", "list", "--workflow=scheduled-update.yml",
            "--limit", "10", "--json", "conclusion",
        ])
    except RuntimeError:
        return 0
    count = 0
    for row in json.loads(out.stdout or "[]"):
        conclusion = row.get("conclusion")
        if conclusion == "success":
            break
        if conclusion in ("failure", "timed_out", "startup_failure", "cancelled"):
            count += 1
    return count


def detail_block(path: str) -> str:
    if not path:
        return "无附加日志。"
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return f"日志文件不可读：`{path}`"
    lines = text.splitlines()
    total = len(lines)
    if total > 40:
        lines = lines[:40] + [f"...（已截断，共 {total} 行，完整日志见运行页面）"]
    return "### 失败详情\n\n```text\n" + "\n".join(lines) + "\n```"


def run_context() -> dict:
    now = datetime.now(JST)
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = detect_repo()
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    return {
        "now": now,
        "run_url": (
            f"{server}/{repo}/actions/runs/{run_id}"
            if run_id else "（本地运行，无 URL）"
        ),
        "workflow": os.environ.get("GITHUB_WORKFLOW", "scheduled-update"),
        "ref": detect_branch(),
        "sha": os.environ.get("GITHUB_SHA", git("rev-parse", "--short", "HEAD"))[:7],
        "owner": os.environ.get("GITHUB_REPOSITORY_OWNER", ""),
    }


def post_or_update_alert(
    title: str, body: str, severity: str, cooldown_hours: float,
) -> int:
    """同一标题只保留一个未关闭 Issue；冷却期内只记日志，不重复评论。"""
    ensure_label(LABEL_ALERT, "B60205", "自动化调度异常告警")
    ensure_label(
        f"severity:{severity}", SEVERITY_COLORS.get(severity, "B60205"),
        SEVERITY_DESC.get(severity, "自动化告警"),
    )
    existing = open_issue_index(LABEL_ALERT)
    if title in existing:
        number = existing[title]
        age = issue_age_hours(number)
        if age < cooldown_hours:
            log(f"告警 #{number} 仍在冷却期（{age:.1f}h < {cooldown_hours}h），跳过评论")
            return 0
        run_gh(["issue", "comment", str(number), "--body", body])
        log(f"已追加告警评论到 #{number}（级别 {severity.upper()}）")
        return 0

    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".md", delete=False, newline="\n"
    ) as fh:
        fh.write(body)
        body_path = fh.name
    try:
        created = run_gh([
            "issue", "create", "--title", title,
            "--body-file", body_path,
            "--label", LABEL_ALERT,
            "--label", f"severity:{severity}",
        ])
        log(f"已创建告警 Issue（{severity.upper()}）: "
            f"{created.stdout.strip().splitlines()[-1]}")
    finally:
        Path(body_path).unlink(missing_ok=True)
    return 0


def build_alert_body(args: argparse.Namespace, title: str, severity: str) -> str:
    ctx = run_context()
    mention = (
        f"@{ctx['owner']}" if ctx["owner"] and severity in ("p0", "p1") else ""
    )
    return ALERT_TEMPLATE.substitute(
        reason=args.reason,
        severity_label=severity.upper(),
        severity_desc=SEVERITY_DESC.get(severity, "自动化告警"),
        workflow=ctx["workflow"],
        run_url=ctx["run_url"],
        ref=ctx["ref"],
        sha=ctx["sha"],
        created_at=f"{ctx['now']:%Y-%m-%d %H:%M} JST",
        recent_failures=recent_failure_count(),
        detail=detail_block(getattr(args, "detail_file", "") or ""),
        suggestions=ALERT_SUGGESTIONS.get(
            getattr(args, "kind", "run_failure"), ALERT_SUGGESTIONS["run_failure"]
        ),
        mention=mention,
    )


def cmd_recovered(args: argparse.Namespace) -> int:
    """在未关闭的 P0 告警下追加恢复回执（不自动关闭）。"""
    titles = (
        [args.title] if args.title
        else [ALERT_KINDS["run_failure"][0], ALERT_KINDS["heartbeat"][0]]
    )
    existing = open_issue_index(LABEL_ALERT)
    ctx = run_context()
    note = (
        f"已恢复：{ctx['now']:%Y-%m-%d %H:%M} JST 的成功运行已完成。\n\n"
        f"运行：{ctx['run_url']}\n\n请确认结果后关闭本 Issue。"
    )
    for title in titles:
        number = existing.get(title)
        if not number:
            continue
        comments = json.loads(
            run_gh([
                "issue", "view", str(number), "--json", "comments",
            ]).stdout or "{}"
        ).get("comments", [])
        if comments and "已恢复" in comments[-1].get("body", ""):
            log(f"告警 #{number} 已有恢复回执，跳过")
            continue
        run_gh(["issue", "comment", str(number), "--body", note])
        log(f"已追加恢复回执到 #{number}")
    return 0


def cmd_alert(args: argparse.Namespace) -> int:
    if args.recovered:
        if not require_gh():
            return fail("未找到 gh CLI，无法写入恢复回执。")
        return cmd_recovered(args)

    if not require_gh():
        return fail("未找到 gh CLI，无法创建告警 Issue。")
    default_title, default_severity = ALERT_KINDS.get(
        args.kind, ALERT_KINDS["run_failure"]
    )
    title = args.title or default_title
    severity = (args.severity or default_severity).lower()
    if severity not in SEVERITY_COLORS:
        return fail(f"未知告警级别: {severity}")
    body = build_alert_body(args, title, severity)
    return post_or_update_alert(
        title, body, severity, cooldown_hours=args.cooldown_hours,
    )


# ──────────────────────────────────────────────
# heartbeat / backlog（自动巡检类告警）
# ──────────────────────────────────────────────

def cmd_heartbeat(args: argparse.Namespace) -> int:
    """检测调度停摆：上次成功运行距现在超过阈值时告警。"""
    if os.environ.get("GITHUB_EVENT_NAME") != "schedule" and not args.force:
        log("非 schedule 触发，跳过停摆检测（可用 --force 强制执行）")
        return 0
    if not require_gh():
        log("未找到 gh CLI，跳过停摆检测")
        return 0
    try:
        out = run_gh([
            "run", "list", "--workflow=scheduled-update.yml",
            "--status", "success", "--limit", "10",
            "--json", "createdAt,url,event",
        ])
    except RuntimeError as exc:
        log(f"读取运行历史失败，跳过停摆检测: {exc}")
        return 0
    # 只看 schedule 触发的成功运行，避免手动 dry-run 掩盖定时停摆
    rows = [
        row for row in json.loads(out.stdout or "[]")
        if row.get("event") == "schedule"
    ]
    if not rows:
        log("暂无 schedule 成功记录（首次部署或定时从未成功），跳过停摆检测")
        return 0

    last = datetime.fromisoformat(
        rows[0]["createdAt"].replace("Z", "+00:00")
    )
    gap_days = (datetime.now(timezone.utc) - last).total_seconds() / 86400
    if gap_days <= args.max_gap_days:
        log(f"停摆检测正常：距上次成功 {gap_days:.1f} 天")
        return 0

    args.kind = "heartbeat"
    args.reason = (
        f"调度已 {gap_days:.1f} 天未成功运行（阈值 {args.max_gap_days} 天），"
        "可能存在 cron 丢弃、工作流被禁用或权限失效"
    )
    args.detail_file = ""
    title, severity = ALERT_KINDS["heartbeat"]
    body = build_alert_body(args, title, severity) + (
        f"\n\n上次成功运行：{rows[0].get('url', '—')}"
    )
    return post_or_update_alert(
        title, body, severity, cooldown_hours=args.cooldown_hours,
    )


def cmd_backlog(args: argparse.Namespace) -> int:
    """积压/逾期巡检：逾期超阈值或未关闭工单过多时告警。"""
    cfg = load_config()
    errors = validate_config(cfg)
    if errors:
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    if not require_gh():
        log("未找到 gh CLI，跳过积压巡检")
        return 0

    rows = gather(cfg)
    overdue: list[tuple[int, dict]] = []
    for row in rows:
        status = row["status"]
        if status["key"] != "overdue":
            continue
        days = 0 if status["last"] is None else -status["days_left"]
        overdue.append((days, row))

    try:
        task_count = len(open_task_issues())
    except RuntimeError as exc:
        log(f"读取工单失败，按 0 计: {exc}")
        task_count = 0

    critical = [x for x in overdue if x[0] > args.critical_days]
    warn = [x for x in overdue if args.warn_days < x[0] <= args.critical_days]

    if critical or task_count > args.max_open:
        title, severity = ALERT_KINDS["backlog"]
        args.kind = "backlog"
        reasons = []
        if critical:
            reasons.append(f"{len(critical)} 个主题逾期超过 {args.critical_days} 天")
        if task_count > args.max_open:
            reasons.append(f"未关闭工单 {task_count} 个，超过阈值 {args.max_open}")
        args.reason = "；".join(reasons)
        args.detail_file = ""
        body = build_alert_body(args, title, severity) + _backlog_detail(
            critical, warn, task_count
        )
        return post_or_update_alert(
            title, body, severity, cooldown_hours=args.cooldown_hours,
        )

    if warn:
        title, severity = ALERT_KINDS["overdue"]
        args.kind = "overdue"
        args.reason = f"{len(warn)} 个主题逾期超过 {args.warn_days} 天（未达 P1 阈值）"
        args.detail_file = ""
        body = build_alert_body(args, title, severity) + _backlog_detail(
            [], warn, task_count
        )
        return post_or_update_alert(
            title, body, severity, cooldown_hours=args.cooldown_hours,
        )

    log(
        f"积压巡检正常：逾期 {len(overdue)} 个，未关闭工单 {task_count} 个"
    )
    return 0


def _backlog_detail(
    critical: list[tuple[int, dict]],
    warn: list[tuple[int, dict]],
    task_count: int,
) -> str:
    lines = ["", "### 积压明细", "", f"- 未关闭 `update-task` 工单：{task_count} 个"]
    for days, row in critical + warn:
        topic = row["topic"]
        lines.append(
            f"- {topic['id']} {topic['name']}：逾期 {days} 天，"
            f"到期 {row['status']['next_due']}，"
            f"工单入口 `{topic['prompt']}`"
        )
    if not critical and not warn:
        lines.append("- 无逾期主题，仅工单数量超阈值。")
    return "\n".join(lines) + "\n"


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

    p_alert = sub.add_parser("alert", help="创建/追加分级告警 Issue，或写入恢复回执")
    p_alert.add_argument(
        "--kind", default="run_failure", choices=sorted(ALERT_KINDS),
        help="告警类型，决定默认标题、级别与处理建议",
    )
    p_alert.add_argument("--reason", default="周期更新调度工作流运行失败")
    p_alert.add_argument("--severity", default="", choices=["", "p0", "p1", "p2"])
    p_alert.add_argument("--title", default="", help="覆盖默认标题（去重键）")
    p_alert.add_argument("--detail-file", default="", help="附带的失败日志文件")
    p_alert.add_argument(
        "--cooldown-hours", type=float, default=6.0,
        help="同一告警的评论冷却小时数（默认 6）",
    )
    p_alert.add_argument(
        "--recovered", action="store_true",
        help="在未关闭告警下追加恢复回执；配合 --title 可指定单个告警",
    )
    p_alert.set_defaults(func=cmd_alert)

    p_heartbeat = sub.add_parser("heartbeat", help="检测调度停摆并告警")
    p_heartbeat.add_argument(
        "--max-gap-days", type=int, default=10,
        help="距上次成功运行超过该天数即告警（默认 10）",
    )
    p_heartbeat.add_argument(
        "--force", action="store_true", help="非 schedule 触发时也执行检测",
    )
    p_heartbeat.add_argument("--cooldown-hours", type=float, default=24.0)
    p_heartbeat.set_defaults(func=cmd_heartbeat)

    p_backlog = sub.add_parser("backlog", help="检测逾期与工单积压并分级告警")
    p_backlog.add_argument("--warn-days", type=int, default=14)
    p_backlog.add_argument("--critical-days", type=int, default=30)
    p_backlog.add_argument("--max-open", type=int, default=6)
    p_backlog.add_argument("--cooldown-hours", type=float, default=24.0)
    p_backlog.set_defaults(func=cmd_backlog)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
