"""审计家族补测（audit_pipeline / audit_check / audit_badge / audit_preflight /
audit_sampling / audit_registry / auto_verify）。

与 test_tools.py、test_pipeline_e2e.py 互补：只补未覆盖的纯函数与可用 mock 驱动的
CLI 分支。全部 hermetic：tempfile 临时目录 + unittest.mock，不改真实仓库、不联网。
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import _common  # noqa: E402
import audit_badge  # noqa: E402
import audit_check  # noqa: E402
import audit_pipeline  # noqa: E402
import audit_preflight  # noqa: E402
import audit_registry  # noqa: E402
import audit_sampling  # noqa: E402
import auto_verify  # noqa: E402
import compliance_check  # noqa: E402
import info_quality_check  # noqa: E402
import md2html  # noqa: E402


# ---------------------------------------------------------------- 公共夹具

GOOD_TEXT = """# 示例 · 2026-11 月度报告

> **版本**：v1.0　|　**数据基准日**：2026-11-01

> **免责声明**：本报告不构成法律意见。

## 一、核心结论

结论：123 条，来源：[官方](https://example.com)。

## 二、正文

实质段落含数字 456，来源：[机构](https://example.com)。口径：测试口径。

## 三、后续观察

- 观察项：无。

## 四、数据可靠性与局限

本期数据缺口：无。

## 五、置信度标注

| 关键结论/数字 | 来源 | 时效 | 核验状态 | 分级码 |
|---|---|---|---|---|
| 123 条 | 官方 | 新 | 已核验 | S1 |

## 六、信息差与未核验清单

本期无显式缺口。

## 七、决策建议

1. 按既有节奏执行。

## 八、参考来源清单

- [来源](https://example.com)
"""


def _good_html(sections: int = 9) -> str:
    body = "".join(f'<h2 id="s{i}">第{i}节</h2>' for i in range(1, sections + 1))
    return (
        '<html><head><title>示例</title></head><body>'
        '<nav aria-label="报告导航"></nav>' + body + "</body></html>"
    )


def _l5(result: str = "yes", basis: str = "") -> str:
    return json.dumps(
        {
            "items": [
                {"item": audit_check.L5_CHECKLIST[i][0], "result": result, "basis": basis}
                for i in range(len(audit_check.L5_CHECKLIST))
            ]
        },
        ensure_ascii=False,
    )


def _make_topic(root, name="01-demo", period="2026-11", text=None, html=None,
                config=True, registry=None):
    slug = name.split("-", 1)[-1]
    base = root / name
    (base / "prompts").mkdir(parents=True, exist_ok=True)
    (base / "reports").mkdir(parents=True, exist_ok=True)
    if config:
        (base / "prompts" / "business-config.md").write_text(
            "继承：[职业就业调研型](../../engine/report_templates/employment-research/)\n",
            encoding="utf-8",
        )
    md = base / "reports" / f"{period}-{slug}.md"
    md.write_text(text if text is not None else "# 标题\n", encoding="utf-8")
    if html is not None:
        md.with_suffix(".html").write_text(html, encoding="utf-8")
    if registry is not None:
        (base / "data").mkdir(parents=True, exist_ok=True)
        (base / "data" / "x_indicator_registry.md").write_text(registry, encoding="utf-8")
    return md


def _rel(md: Path, root: Path) -> str:
    return md.relative_to(root).as_posix()


@contextlib.contextmanager
def audit_env(root: Path, audit_dir: Path | None = None):
    """把审计家族各模块的 ROOT / AUDIT_DIR / 台账路径重定向到临时目录。

    真实 iter_business_dirs / link_prefix 走 _common.ROOT，故一并重定向，
    使扫描与链接生成完全落在临时树内（hermetic）。
    """
    audit_dir = audit_dir or root / "engine" / "report-audits" / "audit"
    real_root = Path(_common.__file__).resolve().parents[2]
    targets = [
        (_common, "ROOT", root),
        (info_quality_check, "ROOT", root),
        (compliance_check, "ROOT", root),
        (compliance_check, "RULES_PATH",
         real_root / "engine" / "report_templates" / "compliance-rules.json"),
        (audit_registry, "ROOT", root),
        (audit_registry, "AUDIT_DIR", audit_dir),
        (audit_registry, "REGISTRY_JSON", audit_dir / "report-registry.json"),
        (audit_registry, "REGISTRY_MD", audit_dir / "report-registry.md"),
        (audit_pipeline, "ROOT", root),
        (audit_pipeline, "AUDIT_DIR", audit_dir),
        (audit_pipeline, "LEDGER", audit_dir / "audit-ledger.jsonl"),
        (audit_pipeline, "STATUS", audit_dir / "audit-status.json"),
        (audit_check, "ROOT", root),
        (audit_check, "AUDIT_DIR", audit_dir),
        (audit_check, "CHECK_REPORT_MD", audit_dir / "audit-check-report.md"),
        (audit_check, "CHECK_REPORT_JSON", audit_dir / "audit-check-report.json"),
        (audit_check, "PENDING_P2", audit_dir / "pending-p2.json"),
        (audit_check, "IQ_CACHE", audit_dir / "findings-by-path.json"),
        (audit_preflight, "ROOT", root),
        (audit_preflight, "AUDIT_DIR", audit_dir),
        (audit_preflight, "REPORT_MD", audit_dir / "preflight-report.md"),
        (audit_preflight, "REPORT_JSON", audit_dir / "preflight-report.json"),
        (audit_sampling, "ROOT", root),
        (audit_sampling, "SAMPLING_DIR", audit_dir / "sampling"),
        (audit_sampling, "PENDING_P2", audit_dir / "pending-p2.json"),
        (audit_badge, "ROOT", root),
        (audit_badge, "AUDIT_DIR", audit_dir),
        (audit_badge, "STATUS", audit_dir / "audit-status.json"),
        (auto_verify, "ROOT", root),
        (auto_verify, "RULES_DIR", audit_dir / "verify"),
    ]
    saved = [(m, n, getattr(m, n)) for m, n, _ in targets]
    for m, n, v in targets:
        setattr(m, n, v)
    try:
        yield audit_dir
    finally:
        for m, n, v in reversed(saved):
            setattr(m, n, v)


def _capture(func, *args, **kwargs):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = func(*args, **kwargs)
    return rc, buf.getvalue()


def _drive_audited(root: Path, rep: str) -> None:
    audit_pipeline.cmd_init()
    audit_pipeline.cmd_submit(rep, False, "generator")
    audit_pipeline.cmd_review("initial", rep, False, "pass", "", "", None)
    audit_pipeline.cmd_review("re_review", rep, False, "pass", "", "", _l5())
    audit_pipeline.cmd_review("final", rep, False, "pass", "", "", None)


# ---------------------------------------------------------------- audit_registry

class TestCovAuditRegistry(unittest.TestCase):
    def test_content_fingerprint_strips_badge(self):
        with tempfile.TemporaryDirectory() as d:
            md = Path(d) / "r.md"
            md.write_text("# 标题\n\n正文\n", encoding="utf-8")
            before = audit_registry.content_fingerprint(md)
            md.write_text("# 标题\n\n正文\n\n" + audit_badge.badge_text(
                "AUD-X", "2026-11-01T00:00:00", "sha256:abc") + "\n", encoding="utf-8")
            self.assertEqual(before, audit_registry.content_fingerprint(md))

    def test_html_fingerprint_strips_badge(self):
        with tempfile.TemporaryDirectory() as d:
            html = Path(d) / "r.html"
            html.write_text('<html><body>报告</body></html>', encoding="utf-8")
            before = audit_registry.html_fingerprint(html)
            html.write_text('<html><body>报告<div class="audit-badge">x</div></body></html>',
                            encoding="utf-8")
            self.assertEqual(before, audit_registry.html_fingerprint(html))

    def test_content_fingerprints_html_missing(self):
        with tempfile.TemporaryDirectory() as d:
            md = Path(d) / "r.md"
            md.write_text("# 标题\n", encoding="utf-8")
            md_h, html_h = audit_registry.content_fingerprints(md, Path(d) / "none.html")
            self.assertTrue(md_h.startswith("sha256:"))
            self.assertEqual(html_h, "")

    def test_type_id_of_config(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                topic = root / "01-demo"
                (topic / "prompts").mkdir(parents=True)
                (topic / "prompts" / "business-config.md").write_text(
                    "继承：[职业就业调研型](../../engine/report_templates/employment-research/)\n",
                    encoding="utf-8")
                self.assertEqual(audit_registry.type_id_of(topic), "employment-research")
                self.assertEqual(audit_registry.type_id_of(root / "none"), "")

    def test_discover_fields_and_sort(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                _make_topic(root, "02-b", period="2026-10")
                _make_topic(root, "01-a", period="2026-11")
                _make_topic(root, "01-a", period="2026-10")
                entries = audit_registry.discover()
                self.assertEqual(len(entries), 3)
                self.assertEqual(
                    [(e["topic"], e["period"]) for e in entries],
                    [("01-a", "2026-10"), ("01-a", "2026-11"), ("02-b", "2026-10")],
                )
                self.assertEqual(
                    set(entries[0]),
                    {"report", "topic", "topic_slug", "period", "slug", "type_id",
                     "md", "html", "content_hash", "html_hash", "audit_id",
                     "audit_state", "finalized_at"},
                )
                self.assertEqual(entries[0]["type_id"], "employment-research")

    def test_render_md_content(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                _make_topic(root, "01-demo")
                md = audit_registry.render_md(audit_registry.discover(), "2026-11-01")
                self.assertIn("报告登记册", md)
                self.assertIn(audit_registry.SPEC_VERSION, md)
                self.assertIn("01-demo", md)
                self.assertIn("../", md)

    def test_build_writes_json_and_md_with_audit_state(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", html=_good_html())
                rep = _rel(md, root)
                _drive_audited(root, rep)
                entries = audit_registry.build()
                self.assertTrue(audit_registry.REGISTRY_JSON.is_file())
                self.assertTrue(audit_registry.REGISTRY_MD.is_file())
                payload = json.loads(audit_registry.REGISTRY_JSON.read_text(encoding="utf-8"))
                self.assertEqual(payload["count"], 1)
                self.assertEqual(entries[0]["audit_state"], "audited")

    def test_check_missing_registry(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                n, problems = audit_registry.check()
                self.assertEqual(n, 1)
                self.assertTrue(any("登记册缺失" in p for p in problems))

    def test_check_extra_report_and_html_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", html=_good_html())
                audit_registry.build()
                md.unlink()
                n, problems = audit_registry.check()
                self.assertEqual(n, 1)
                self.assertTrue(any("登记册多余报告" in p for p in problems))

                _make_topic(root, "01-demo", html=_good_html())
                audit_registry.build()
                md.with_suffix(".html").write_text("<html>改了</html>", encoding="utf-8")
                n, problems = audit_registry.check()
                self.assertTrue(any("HTML 指纹失配" in p for p in problems))


# ---------------------------------------------------------------- audit_badge

class TestCovAuditBadge(unittest.TestCase):
    def test_badge_text_format(self):
        text = audit_badge.badge_text("AUD-202611-0001", "2026-11-01T09:00:00",
                                      "sha256:abcdef")
        self.assertIn("AUD-202611-0001", text)
        self.assertIn("2026-11-01", text)
        self.assertIn("sha256:abcdef"[:19], text)
        self.assertIn(audit_badge.SPEC_VERSION, text)

    def test_insert_after_disclaimer(self):
        body = "# 标题\n\n## 免责\n\n> **免责声明**：x\n\n## 正文\n"
        out = audit_badge._insert_after_disclaimer(body, "BADGE\n")
        self.assertLess(out.index("免责声明"), out.index("BADGE"))
        self.assertLess(out.index("BADGE"), out.index("正文"))

    def test_insert_no_title_prepends(self):
        out = audit_badge._insert_after_disclaimer("正文\n", "BADGE\n")
        self.assertTrue(out.startswith("BADGE"))

    def test_strip_badge(self):
        block = audit_badge.badge_text("AUD-X", "2026-11-01T00:00:00", "sha256:abc")
        text, removed = audit_badge._strip_badge("# 标题\n\n" + block + "\n正文\n")
        self.assertTrue(removed)
        self.assertNotIn("已审计", text)
        self.assertFalse(audit_badge._strip_badge("# 标题\n")[1])

    def test_targets_requires_report_or_all(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                _make_topic(root, "01-demo")
                rep = "01-demo/reports/2026-11-demo.md"
                self.assertEqual(audit_badge._targets(False, rep), [rep])
                with self.assertRaises(SystemExit):
                    audit_badge._targets(False, None)
                with self.assertRaises(SystemExit):
                    audit_badge._targets(False, "../escape.md")

    def test_cmd_apply_skip_and_apply(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                plain = _make_topic(root, "01-a")
                rep_plain = _rel(plain, root)
                audited = _make_topic(root, "01-b", html=_good_html())
                rep_audited = _rel(audited, root)
                _drive_audited(root, rep_audited)
                calls = []
                with mock.patch.object(audit_badge, "_regenerate_html",
                                       lambda p: calls.append(p)):
                    rc, out = _capture(audit_badge.cmd_apply, False, rep_plain)
                    self.assertEqual(rc, 0)
                    self.assertIn("不注入标识", out)
                    self.assertNotIn("审计标识", plain.read_text(encoding="utf-8"))

                    audited.write_text(audited.read_text(encoding="utf-8") + "\n改动\n",
                                       encoding="utf-8")
                    rc, out = _capture(audit_badge.cmd_apply, False, rep_audited)
                    self.assertIn("指纹失配", out)

                    fixed = _make_topic(root, "01-c", html=_good_html())
                    rep_fixed = _rel(fixed, root)
                    _drive_audited(root, rep_fixed)
                    _capture(audit_badge.cmd_apply, False, rep_fixed)
                    self.assertIn("已审计", fixed.read_text(encoding="utf-8"))
                    self.assertEqual(calls, [fixed])

    def test_cmd_revoke(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo")
                block = audit_badge.badge_text("AUD-X", "2026-11-01T00:00:00", "sha256:abc")
                md.write_text(md.read_text(encoding="utf-8") + "\n" + block,
                              encoding="utf-8")
                with mock.patch.object(audit_badge, "_regenerate_html", lambda p: None):
                    _capture(audit_badge.cmd_revoke, False, _rel(md, root))
                self.assertNotIn("审计标识", md.read_text(encoding="utf-8"))

    def test_cmd_check_problems(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", html=_good_html())
                rep = _rel(md, root)
                _drive_audited(root, rep)
                rc, out = _capture(audit_badge.cmd_check)
                self.assertEqual(rc, 1)
                self.assertIn("缺少已审计标识", out)

                fp = audit_registry.content_fingerprint(md).removeprefix("sha256:")
                badge = audit_badge.badge_text("AUD-1", "", fp)
                md.write_text(md.read_text(encoding="utf-8") + "\n" + badge + "\n",
                              encoding="utf-8")
                md.with_suffix(".html").write_text("<html>无徽章</html>", encoding="utf-8")
                rc, out = _capture(audit_badge.cmd_check)
                self.assertIn("HTML 标识与 md 标识不一致", out)

    def test_cmd_sync_applies_and_revokes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", html=_good_html())
                rep = _rel(md, root)
                _drive_audited(root, rep)
                with mock.patch.object(audit_badge, "_regenerate_html", lambda p: None):
                    _capture(audit_badge.cmd_sync)
                    self.assertIn("已审计", md.read_text(encoding="utf-8"))
                    md.write_text(md.read_text(encoding="utf-8") + "\n改动\n",
                                   encoding="utf-8")
                    _capture(audit_badge.cmd_sync)
                    self.assertNotIn("已审计", md.read_text(encoding="utf-8"))

    def test_load_status_fallback_invalid_json(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root) as ad:
                ad.mkdir(parents=True, exist_ok=True)
                (ad / "audit-status.json").write_text("{bad", encoding="utf-8")
                with mock.patch.object(audit_pipeline, "load_ledger",
                                       side_effect=Exception("no ledger")):
                    self.assertEqual(audit_badge._load_status(), {})
                (ad / "audit-status.json").write_text(
                    json.dumps({"reports": {"r.md": {"state": "audited"}}}),
                    encoding="utf-8")
                with mock.patch.object(audit_pipeline, "load_ledger",
                                       side_effect=Exception("no ledger")):
                    self.assertEqual(audit_badge._load_status()["r.md"]["state"], "audited")


# ---------------------------------------------------------------- audit_pipeline

class TestCovAuditPipeline(unittest.TestCase):
    def test_canonical_and_hash(self):
        body = {"b": 1, "a": 2}
        self.assertEqual(audit_pipeline._canonical(body), '{"a":2,"b":1}')
        self.assertEqual(
            audit_pipeline._hash("prev", body),
            hashlib.sha256(("prev" + '{"a":2,"b":1}').encode()).hexdigest(),
        )

    def test_validate_l5_evidence_branches(self):
        bad = json.loads(_l5())
        bad["version"] = "0.9"
        ok, probs = audit_pipeline.validate_l5_evidence(json.dumps(bad))
        self.assertFalse(ok)
        self.assertIn("version", probs[0])

        ok, probs = audit_pipeline.validate_l5_evidence(_l5(result="maybe"))
        self.assertIn("result 非法", probs[0])

        bad = json.loads(_l5())
        bad["items"] = bad["items"][:-1]
        ok, probs = audit_pipeline.validate_l5_evidence(json.dumps(bad))
        self.assertIn("须为 6 项", probs[0])

        bad = json.loads(_l5())
        bad["items"][0]["item"] = "错"
        ok, probs = audit_pipeline.validate_l5_evidence(json.dumps(bad))
        self.assertIn("标签不符", probs[0])

        ok, probs = audit_pipeline.validate_l5_evidence(_l5(result="no", basis=""))
        self.assertIn("缺少 basis", probs[0])

    def test_rebuild_status_tolerant(self):
        ledger = [{"seq": 1, "report": "r.md", "event": "submit", "ts": "t",
                   "content_hash": "h", "html_hash": "g", "actor": "a"}]
        st = audit_pipeline.rebuild_status(ledger)
        self.assertEqual(st["r.md"]["state"], "pending_initial")
        self.assertEqual(st["r.md"]["content_hash"], "h")
        st = audit_pipeline.rebuild_status(
            ledger + [{"seq": 2, "report": "r.md", "event": "bogus", "ts": "t"}])
        self.assertEqual(st["r.md"]["state"], "pending_initial")

    def test_next_audit_id(self):
        state = {"a": {"audit_id": "AUD-202611-001"}}
        nxt = audit_pipeline._next_audit_id(state)
        self.assertRegex(nxt, r"^AUD-\d{6}-\d{3}$")
        self.assertNotEqual(nxt, "AUD-202611-001")

    def test_report_arg_validation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                _make_topic(root, "01-demo")
                rep = "01-demo/reports/2026-11-demo.md"
                self.assertEqual(audit_pipeline._report_arg(rep), rep)
                with self.assertRaises(SystemExit):
                    audit_pipeline._report_arg("../x.md")
                (root / "x.txt").write_text("x", encoding="utf-8")
                with self.assertRaises(SystemExit):
                    audit_pipeline._report_arg("x.txt")

    def test_load_ledger_skips_corrupted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                audit_pipeline.LEDGER.parent.mkdir(parents=True, exist_ok=True)
                audit_pipeline.LEDGER.write_text(
                    "not json\n" + json.dumps({"seq": 1, "report": "r", "event": "submit",
                                               "ts": "t"}) + "\n",
                    encoding="utf-8")
                self.assertEqual(len(audit_pipeline.load_ledger()), 1)

    def test_chain_problems_and_audited_hash(self):
        body0 = {"report": "r", "event": "submit", "ts": "t",
                 "content_hash": "h1", "html_hash": "g1"}
        h0 = audit_pipeline._hash("0" * 64, body0)
        ev0 = {"seq": 1, "prev_hash": "0" * 64, "hash": h0, **body0}
        body1 = {"report": "r", "event": "stage_pass", "stage": "initial",
                 "role": "audit_chair", "ts": "t", "content_hash": "h1", "html_hash": "g1"}
        h1 = audit_pipeline._hash(h0, body1)
        ev1 = {"seq": 2, "prev_hash": h0, "hash": h1, **body1}
        ledger = [ev0, ev1]
        self.assertEqual(audit_pipeline._chain_problems(ledger), [])
        self.assertEqual(audit_pipeline._audited_content_hash(ledger, "r"), "h1")
        ledger[1]["prev_hash"] = "broken"
        self.assertTrue(audit_pipeline._chain_problems(ledger))

    def test_l5_status_from_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", html=_good_html())
                rep = _rel(md, root)
                _drive_audited(root, rep)
                self.assertTrue(audit_pipeline.l5_status_from_ledger().get(rep))
                md.write_text(md.read_text(encoding="utf-8") + "\n改动\n", encoding="utf-8")
                self.assertFalse(audit_pipeline.l5_status_from_ledger().get(rep))

    def test_cmd_backfill_l5(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", html=_good_html())
                rep = _rel(md, root)
                _drive_audited(root, rep)
                with self.assertRaises(SystemExit):
                    audit_pipeline.cmd_backfill_l5(rep, False, "{}", "reviewer_l2")
                rc, out = _capture(audit_pipeline.cmd_backfill_l5, rep, False,
                                   _l5(), "reviewer_l2")
                self.assertEqual(rc, 0)
                self.assertIn("SKIP", out)

                md2 = _make_topic(root, "02-other", period="2026-10", html=_good_html())
                rep2 = _rel(md2, root)
                audit_pipeline.cmd_init()
                audit_pipeline.cmd_submit(rep2, False, "generator")
                audit_pipeline.cmd_review("initial", rep2, False, "pass", "", "", None)
                md_h, html_h = audit_pipeline._current_hashes(rep2)
                for stage, role, ev, aid in (
                    ("re_review", "reviewer_l2", "stage_pass", ""),
                    ("final", "audit_chair", "stage_pass", "AUD-1"),
                ):
                    audit_pipeline._append({"report": rep2, "event": ev, "stage": stage,
                                            "role": role, "ts": audit_pipeline._now(),
                                            "result": "pass", "note": "", "evidence": "",
                                            "audit_id": aid, "content_hash": md_h,
                                            "html_hash": html_h})
                audit_pipeline.cmd_backfill_l5(rep2, False, _l5(), "reviewer_l2")
                kinds = [e["event"] for e in audit_pipeline.load_ledger()
                         if e.get("report") == rep2]
                self.assertIn("l5_backfill", kinds)

    def test_cmd_submit_skip_and_status(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo")
                rep = _rel(md, root)
                rc, out = _capture(audit_pipeline.cmd_status)
                self.assertEqual(rc, 0)
                self.assertIn("审计台账为空", out)

                audit_pipeline.cmd_init()
                audit_pipeline.cmd_submit(rep, False, "generator")
                rc, out = _capture(audit_pipeline.cmd_submit, rep, False, "generator")
                self.assertEqual(rc, 0)
                self.assertIn("不可提交", out)
                self.assertEqual(len(audit_pipeline.load_ledger()), 2)

    def test_cmd_review_validation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo")
                rep = _rel(md, root)
                audit_pipeline.cmd_init()
                audit_pipeline.cmd_submit(rep, False, "generator")
                with self.assertRaises(SystemExit):
                    audit_pipeline.cmd_review("bogus", rep, False, "pass", "", "", None)
                with self.assertRaises(SystemExit):
                    audit_pipeline.cmd_review("initial", rep, False, "bogus", "", "", None)

    def test_cmd_review_html_continuity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", html=_good_html())
                rep = _rel(md, root)
                audit_pipeline.cmd_init()
                audit_pipeline.cmd_submit(rep, False, "generator")
                md.with_suffix(".html").write_text("<html>改了</html>", encoding="utf-8")
                rc, out = _capture(audit_pipeline.cmd_review, "initial", rep, False,
                                   "pass", "", "", None)
                self.assertEqual(rc, 1)
                self.assertIn("HTML 已变更", out)

    def test_cmd_final_requires_html(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo")
                rep = _rel(md, root)
                audit_pipeline.cmd_init()
                audit_pipeline.cmd_submit(rep, False, "generator")
                audit_pipeline.cmd_review("initial", rep, False, "pass", "", "", None)
                audit_pipeline.cmd_review("re_review", rep, False, "pass", "", "", _l5())
                rc, out = _capture(audit_pipeline.cmd_review, "final", rep, False,
                                   "pass", "", "", None)
                self.assertEqual(rc, 1)
                self.assertIn("html_hash 为空", out)

    def test_cmd_sync_noop_and_mark_sampling(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", html=_good_html())
                rep = _rel(md, root)
                _drive_audited(root, rep)
                before = len(audit_pipeline.load_ledger())
                rc, _ = _capture(audit_pipeline.cmd_sync)
                self.assertEqual(rc, 0)
                self.assertEqual(len(audit_pipeline.load_ledger()), before)

                n = audit_pipeline.mark_sampling_failures([rep, "other/x.md"])
                self.assertEqual(n, 1)
                self.assertEqual(
                    audit_pipeline.rebuild_status(audit_pipeline.load_ledger())[rep]["state"],
                    "stale",
                )

    def test_changed_report_paths_and_git_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo")
                rep = _rel(md, root)
                changed = root / "changed.txt"
                changed.write_text(
                    f"{rep}\n01-demo/reports/a.html\n"
                    "01-demo/reports/2026-12-gone.md\nREADME.md\n", encoding="utf-8")
                out = audit_pipeline._changed_report_paths("origin/main", changed)
                # 已删除（工作树中不存在）的报告跳过受检；HTML / 非报告不触发
                self.assertEqual(out, [rep])

                fake = subprocess.CompletedProcess([], 0,
                                                   stdout=f"{rep}\n01-demo/reports/b.md\nREADME.md\n",
                                                   stderr="")
                with mock.patch.object(subprocess, "run", return_value=fake):
                    out = audit_pipeline._changed_report_paths("origin/main", None)
                self.assertEqual(out, [rep])

    def test_cmd_gate_strict_unregistered(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                _make_topic(root, "01-demo")
                audit_registry.build()
                rc, out = _capture(audit_pipeline.cmd_gate, None, "origin/main", True)
                self.assertEqual(rc, 1)
                self.assertIn("未登记审计", out)


# ---------------------------------------------------------------- audit_check

class TestAuditStatusGhost(unittest.TestCase):
    """write_status 写回前剔除幽灵状态（报告文件不存在），避免内链门禁误报。"""

    def test_write_status_prunes_ghosts(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "01-x").mkdir()
            (root / "01-x" / "r.md").write_text("# t\n", encoding="utf-8")
            with mock.patch.object(audit_pipeline, "ROOT", root), \
                    mock.patch.object(audit_pipeline, "AUDIT_DIR", root / "audit"), \
                    mock.patch.object(audit_pipeline, "STATUS", root / "audit" / "status.json"):
                state = {"01-x/r.md": {"state": "audited"},
                         "01-x/missing.md": {"state": "audited"}}
                audit_pipeline.write_status(state)
                written = json.loads(
                    (root / "audit" / "status.json").read_text(encoding="utf-8"))
            self.assertIn("01-x/r.md", written["reports"])
            self.assertNotIn("01-x/missing.md", written["reports"])


class TestCovAuditCheck(unittest.TestCase):
    def test_absolute_hits_filters(self):
        text = "不能包过。\n「包过」是引号。\n100% 包过。\n"
        self.assertEqual(audit_check.absolute_hits(text), ["100%", "包过"])

    def test_hash_bytes_normalizes_crlf(self):
        h = hashlib.sha256()
        audit_check._hash_bytes(h, b"a\r\nb")
        self.assertEqual(h.hexdigest(), hashlib.sha256(b"a\nb").hexdigest())

    def test_check_structure_failures(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo",
                                 html="<html><body><h2>一</h2></body></html>")
                rep = _rel(md, root)
                res = audit_check.check_structure(rep, md, md.with_suffix(".html"),
                                                  "employment-research")
                details = " ".join(f.detail for f in res)
                self.assertIn("骨架", details)
                self.assertIn("导航", details)
                self.assertTrue(any(f.severity == "P1" for f in res))

    def test_check_elements_missing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", text="# 标题\n", html=_good_html())
                rep = _rel(md, root)
                res = audit_check.check_elements(rep, md, md.with_suffix(".html"))
                codes = {f.code for f in res}
                self.assertEqual(codes & {"E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"},
                                 {"E2", "E3", "E4", "E6", "E8"})
                self.assertNotIn("E7", codes)

    def test_check_elements_e7(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                text = ("# 标题\n\n## 一、核心结论\n\n结论：123 条，来源：[官方](https://example.com)。\n\n"
                        "## 二、正文\n\n这段文字包含数字 789 但没有任何标注，用于触发 E7 检查逻辑，"
                        "需要写得足够长以满足最小长度阈值。\n")
                md = _make_topic(root, "01-demo", text=text, html=_good_html())
                rep = _rel(md, root)
                res = audit_check.check_elements(rep, md, md.with_suffix(".html"))
                self.assertIn("E7", {f.code for f in res})

    def test_check_local_consistency(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", text="# 标题\n\n包过。\n")
                rep = _rel(md, root)
                res = audit_check.check_local_consistency(rep, md)
                self.assertEqual([f.code for f in res], ["ABS-01"])

    def test_check_report_layers_and_iq(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", text=GOOD_TEXT, html=_good_html())
                rep = _rel(md, root)
                findings = [
                    audit_check.AuditFinding("L3", "C-09", "P2", rep, "溯源", "失效引用", "spec"),
                    audit_check.AuditFinding("L4", "C-02", "P1", rep, "一致性", "重复", "spec"),
                    audit_check.AuditFinding("L5", "C-01", "P2", rep, "语义", "占位", "spec"),
                ]
                res = audit_check.check_report(rep, md, md.with_suffix(".html"),
                                               "employment-research", {rep: findings},
                                               {rep: False})
                self.assertEqual(res.layers["L1"], "pass")
                self.assertEqual(res.layers["L2"], "pass")
                self.assertEqual(res.layers["L3"], "pass")
                self.assertEqual(res.layers["L4"], "fail")
                self.assertEqual(res.layers["L5"], "pending")
                self.assertGreaterEqual(res.severity_counts["P1"], 2)
                self.assertFalse(res.passed)

    def test_check_report_without_l5_status(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", text=GOOD_TEXT, html=_good_html())
                rep = _rel(md, root)
                res = audit_check.check_report(rep, md, md.with_suffix(".html"),
                                               "employment-research", {}, None)
                self.assertEqual(res.layers["L5"], "pass")

    def test_write_pending_p2_corrupt_existing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                audit_check.PENDING_P2.parent.mkdir(parents=True, exist_ok=True)
                audit_check.PENDING_P2.write_text("{bad", encoding="utf-8")
                res = audit_check.ReportResult(
                    "r.md", "01-demo", "2026-11", "", layers={"L2": "fail"},
                    findings=[audit_check.AuditFinding("L2", "E3", "P2", "r.md", "", "缺", "s")])
                audit_check.write_pending_p2([res], "2026-11-30")
                payload = json.loads(audit_check.PENDING_P2.read_text(encoding="utf-8"))
                self.assertEqual(payload["items"][0]["first_seen"], "2026-11-30")

    def test_iq_findings_cache_hit_and_corrupt(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                _make_topic(root, "01-demo")
                key = audit_check._iq_cache_key()
                finding = {"layer": "L4", "code": "C-02", "severity": "P1",
                           "report": "01-demo/reports/2026-11-demo.md",
                           "location": "", "detail": "重复", "spec": "spec"}
                audit_check.IQ_CACHE.parent.mkdir(parents=True, exist_ok=True)
                audit_check.IQ_CACHE.write_text(
                    json.dumps({"version": audit_check.CACHE_VERSION, "key": key,
                                "findings": {"01-demo/reports/2026-11-demo.md": [finding]}}),
                    encoding="utf-8")
                with mock.patch.object(info_quality_check, "scan_topics",
                                       side_effect=AssertionError("不应重算")):
                    out = audit_check.iq_findings_by_path()
                self.assertEqual(out["01-demo/reports/2026-11-demo.md"][0].code, "C-02")

                audit_check.IQ_CACHE.write_text("{bad", encoding="utf-8")
                with mock.patch.object(info_quality_check, "scan_topics", return_value=[]), \
                        mock.patch.object(info_quality_check, "evaluate",
                                          return_value=([], None)):
                    out = audit_check.iq_findings_by_path()
                self.assertEqual(out, {})

    def test_run_all_summary(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                _make_topic(root, "01-demo", text=GOOD_TEXT, html=_good_html())
                with mock.patch.object(audit_check, "_iq_findings_by_path", return_value={}), \
                        mock.patch.object(audit_check, "_l5_status", return_value={}):
                    results, summary = audit_check.run_all()
                self.assertEqual(summary["reports"], 1)
                self.assertIn("L1", summary["by_layer"])
                self.assertEqual(len(results), 1)


# ---------------------------------------------------------------- audit_preflight

class TestCovAuditPreflight(unittest.TestCase):
    def test_check_text_skeleton_and_lint(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", text=GOOD_TEXT, html=_good_html())
                rep = _rel(md, root)
                text = md.read_text(encoding="utf-8")
                self.assertEqual(
                    audit_preflight.check_text(rep, text, html=_good_html(),
                                               type_id="employment-research"), [])

                res = audit_preflight.check_text(
                    rep, text, html="<html><body><h2>一</h2></body></html>",
                    type_id="employment-research")
                self.assertIn("PF-SKELETON", {f.code for f in res})

                res = audit_preflight.check_text(
                    rep, text, html='<html><body><h2>一</h2><img src="x"></body></html>',
                    type_id="")
                self.assertIn("PF-LINT", {f.code for f in res})

    def test_check_text_no_type_and_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", text=GOOD_TEXT, html=_good_html())
                rep = _rel(md, root)
                text = md.read_text(encoding="utf-8")
                res = audit_preflight.check_text(rep, text, html=_good_html(), type_id="")
                self.assertTrue(any("未引用" in f.detail for f in res))
                res = audit_preflight.check_text(rep, text, html=_good_html(),
                                                 type_id="nope")
                self.assertTrue(any("未在 compliance-rules.json 登记" in f.detail for f in res))

    def test_run_all_and_write_report(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                _make_topic(root, "01-demo", text=GOOD_TEXT, html=_good_html())
                results, summary = audit_preflight.run_all()
                self.assertEqual(summary["reports"], 1)
                audit_preflight.write_report(results, summary, "2026-11-30")
                self.assertTrue(audit_preflight.REPORT_MD.is_file())
                self.assertTrue(audit_preflight.REPORT_JSON.is_file())
                self.assertIn("落盘前自检报告",
                              audit_preflight.REPORT_MD.read_text(encoding="utf-8"))

    def test_main_report_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                good = _make_topic(root, "01-demo", text=GOOD_TEXT, html=_good_html())
                bad = _make_topic(root, "02-bad", period="2026-10", text="# 标题\n",
                                  html=_good_html())
                argv = sys.argv
                try:
                    sys.argv = ["audit_preflight.py", "--report", _rel(good, root)]
                    self.assertEqual(audit_preflight.main(), 0)
                    sys.argv = ["audit_preflight.py", "--report", _rel(bad, root)]
                    self.assertEqual(audit_preflight.main(), 1)
                    sys.argv = ["audit_preflight.py", "--report", "none.md"]
                    self.assertEqual(audit_preflight.main(), 1)
                finally:
                    sys.argv = argv


# ---------------------------------------------------------------- audit_sampling

class TestCovAuditSampling(unittest.TestCase):
    def _entries(self, n=10):
        return [{"report": f"01-demo/reports/2026-11-d{i}.md",
                 "topic": "01-demo", "period": "2026-11"} for i in range(n)]

    def _payload(self, **over):
        p = {
            "period": "2026-11", "total_reports": 1, "sample_size": 1,
            "struct_ok": 1, "elem_ok": 1, "consist_ok": 1, "passed": 1, "rate": 1.0,
            "p0": 0, "p1": 0, "p2": 0, "l5_pending": 0, "l5_pending_total": 0,
            "unfinished_verification": 0, "overdue_p2_count": 0,
            "checks": {"struct_100": True, "element_95": True, "consistent_100": True,
                       "pass_95": True, "p0p1_zero": True},
            "ok": True,
            "results": [{"report": "01-demo/reports/2026-11-demo.md", "topic": "01-demo",
                         "period": "2026-11", "passed": True,
                         "layers": {"L1": "pass"}, "severity": {"P0": 0, "P1": 0, "P2": 0},
                         "status_ok": True, "findings": []}],
        }
        p.update(over)
        return p

    def test_select_sample_target_and_rotation(self):
        entries = self._entries(10)
        sample = audit_sampling.select_sample(entries, "2026-11")
        self.assertEqual(len(sample), 5)
        self.assertEqual({e["report"] for e in sample},
                         {f"01-demo/reports/2026-11-d{i}.md" for i in range(5)})
        self.assertEqual(audit_sampling.select_sample(self._entries(3), "2026-11"),
                         self._entries(3))

    def test_run_sample_payload(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo")
                rep = _rel(md, root)
                entry = {"report": rep, "topic": "01-demo", "period": "2026-11",
                         "type_id": "employment-research"}
                res = audit_check.ReportResult(
                    rep, "01-demo", "2026-11", "employment-research",
                    layers={"L1": "pass"},
                    findings=[audit_check.AuditFinding("L2", "E3", "P1", rep, "", "缺", "s")])
                with mock.patch.object(audit_sampling, "discover",
                                       return_value=[entry]), \
                        mock.patch.object(audit_sampling, "select_sample",
                                          return_value=[entry]), \
                        mock.patch.object(audit_sampling, "check_report",
                                          return_value=res), \
                        mock.patch.object(audit_sampling, "iq_findings_by_path",
                                          return_value={}), \
                        mock.patch.object(audit_sampling, "l5_status",
                                          return_value={}), \
                        mock.patch.object(audit_sampling, "audit_state",
                                          return_value={rep: {"state": "audited"}}), \
                        mock.patch.object(audit_sampling, "overdue_p2",
                                          return_value=[]):
                    payload = audit_sampling.run_sample("2026-11")
                self.assertEqual(payload["sample_size"], 1)
                self.assertFalse(payload["checks"]["consistent_100"])
                self.assertFalse(payload["checks"]["pass_95"])
                self.assertFalse(payload["ok"])

    def test_write_report_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                audit_sampling.write_report(self._payload())
                self.assertTrue((audit_sampling.SAMPLING_DIR / "sampling-2026-11.md").is_file())
                self.assertTrue((audit_sampling.SAMPLING_DIR / "sampling-2026-11.json").is_file())
                self.assertIn("验收结论",
                              (audit_sampling.SAMPLING_DIR / "sampling-2026-11.md")
                              .read_text(encoding="utf-8"))

    def test_mark_sampling_failures(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                payload = {"results": [
                    {"report": "a.md", "severity": {"P0": 1, "P1": 0, "P2": 0}},
                    {"report": "b.md", "severity": {"P0": 0, "P1": 2, "P2": 0}},
                    {"report": "c.md", "severity": {"P0": 0, "P1": 0, "P2": 3}},
                ]}
                with mock.patch.object(audit_pipeline, "mark_sampling_failures",
                                       return_value=2) as m:
                    failed = audit_sampling.mark_sampling_failures(payload)
                self.assertEqual(failed, ["a.md", "b.md"])
                m.assert_called_once()

    def test_main_apply_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                argv = sys.argv
                try:
                    sys.argv = ["audit_sampling.py", "--report"]
                    with mock.patch.object(audit_sampling, "run_sample",
                                           return_value=self._payload()):
                        self.assertEqual(audit_sampling.main(), 0)

                    bad = self._payload(checks=dict(self._payload()["checks"],
                                                    pass_95=False), ok=False)
                    sys.argv = ["audit_sampling.py", "--report"]
                    with mock.patch.object(audit_sampling, "run_sample",
                                           return_value=bad):
                        self.assertEqual(audit_sampling.main(), 1)

                    p2 = self._payload(p2=2)
                    sys.argv = ["audit_sampling.py", "--report"]
                    with mock.patch.object(audit_sampling, "run_sample",
                                           return_value=p2):
                        self.assertEqual(audit_sampling.main(), 2)
                finally:
                    sys.argv = argv


# ---------------------------------------------------------------- auto_verify

class TestCovAutoVerify(unittest.TestCase):
    def test_rule_v1_missing_md(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            res, regenerated = auto_verify.rule_v1_deliverables(
                "01-demo/reports/none.md", root / "none.md", root / "none.html")
        self.assertEqual(res.status, "fail")
        self.assertEqual(res.findings[0]["code"], "V1-MD")
        self.assertFalse(regenerated)

    def test_rule_v1_autogen_html(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            md = root / "r.md"
            md.write_text("# 标题\n", encoding="utf-8")
            with mock.patch.object(md2html, "convert", return_value="<html></html>") as conv:
                res, regenerated = auto_verify.rule_v1_deliverables(
                    "01-demo/reports/r.md", md, root / "r.html")
            self.assertTrue(regenerated)
            self.assertTrue((root / "r.html").is_file())
            self.assertIn("V1-HTML", {f["code"] for f in res.findings})
            conv.assert_called_once()

    def test_rule_v1_empty_and_name_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            md = root / "r.md"
            md.write_text("", encoding="utf-8")
            res, _ = auto_verify.rule_v1_deliverables("01-demo/reports/r.md", md,
                                                      root / "r.html")
            self.assertEqual(res.findings[0]["code"], "V1-MD")

            md2 = root / "01-demo" / "reports" / "2026-11-wrong.md"
            md2.parent.mkdir(parents=True)
            md2.write_text("# 标题\n", encoding="utf-8")
            md2.with_suffix(".html").write_text("<html></html>", encoding="utf-8")
            res, _ = auto_verify.rule_v1_deliverables(
                "01-demo/reports/2026-11-wrong.md", md2, md2.with_suffix(".html"))
            self.assertIn("V1-NAME", {f["code"] for f in res.findings})

    def test_rule_v2_fields_codes(self):
        res = auto_verify.rule_v2_fields("r.md", GOOD_TEXT)
        self.assertEqual(res.id, "V2")
        self.assertTrue(set(f["code"] for f in res.findings) <= set(auto_verify.V2_CODES))
        self.assertIn("PF-PAIR", {f["code"] for f in res.findings})

    def test_rule_v3_format_branches(self):
        res = auto_verify.rule_v3_format("r.md", "", "")
        self.assertEqual(res.status, "pass")
        res = auto_verify.rule_v3_format("r.md", _good_html(), "")
        self.assertEqual(res.findings[0]["code"], "V3-SKELETON")
        res = auto_verify.rule_v3_format("r.md", _good_html(), "nope")
        self.assertIn("未登记", res.findings[0]["detail"])
        res = auto_verify.rule_v3_format(
            "r.md", "<html><body><table><tbody></thead></body></html>",
            "employment-research")
        self.assertIn("V3-LINT", {f["code"] for f in res.findings})
        res = auto_verify.rule_v3_format("r.md", _good_html(), "employment-research")
        self.assertEqual(res.status, "pass")

    def test_rule_v4_filters_layers(self):
        rel = "01-demo/reports/2026-11-demo.md"
        findings = [
            audit_check.AuditFinding("L1", "E1", "P1", rel, "", "", "s"),
            audit_check.AuditFinding("L3", "C-09", "P2", rel, "", "", "s"),
            audit_check.AuditFinding("L4", "C-02", "P1", rel, "", "", "s"),
            audit_check.AuditFinding("L2", "C-05", "P2", rel, "", "", "s"),
        ]
        rep = audit_check.ReportResult(rel, "01-demo", "2026-11", "",
                                       layers={"L3": "pass"}, findings=findings)
        with mock.patch.object(audit_check, "check_report", return_value=rep):
            res = auto_verify.rule_v4_consistency(rel, rel, rel, "", {}, {})
        self.assertEqual([f["code"] for f in res.findings], ["C-09", "C-02", "C-05"])

    def test_rule_v5_ranges(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                registry = ("| # | 指标 | 口径 | 最新值 |\n|---|---|---|---|\n"
                            "| 1 | 指标A | 口径A | 123.4 |\n")
                md = _make_topic(root, "01-demo", text=GOOD_TEXT, registry=registry)
                res = auto_verify.rule_v5_ranges(
                    "01-demo/reports/2026-11-demo.md", md.read_text(encoding="utf-8"), None)
                self.assertEqual(res.status, "pass")

                empty_reg = root / "empty_registry.md"
                empty_reg.write_text("# 登记册\n\n无表格。\n", encoding="utf-8")
                res = auto_verify.rule_v5_ranges(
                    "01-demo/reports/2026-11-demo.md", md.read_text(encoding="utf-8"),
                    empty_reg)
                self.assertEqual(res.status, "pass")
                self.assertEqual(res.detail, "登记册无活值表，跳过")

                report = (GOOD_TEXT
                          + "\n## 五、数据变更摘要\n\n| # | 指标 | 活值 |\n|---|---|---|\n"
                            "| 1 | 指标A | 999 |\n")
                res = auto_verify.rule_v5_ranges(
                    "01-demo/reports/2026-11-demo.md", report,
                    md.parents[1] / "data" / "x_indicator_registry.md")
                self.assertEqual(res.status, "fail")
                self.assertEqual(res.findings[0]["code"], "V5-RANGE")

    def test_finding_dict_and_severity_rank(self):
        f = audit_preflight.Finding("PF-X", "P1", "loc", "detail")
        self.assertEqual(auto_verify._finding_dict(f)["code"], "PF-X")
        self.assertEqual(auto_verify._finding_dict(f)["severity"], "P1")
        self.assertEqual(auto_verify._finding_dict({"code": "X", "severity": "P2"})["severity"], "P2")
        self.assertEqual(auto_verify._severity_rank("P0"), 0)
        self.assertEqual(auto_verify._severity_rank("P2"), 2)
        self.assertEqual(auto_verify._severity_rank("??"), 2)

    def test_verify_result_counts_and_log_path(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                r1 = auto_verify.RuleResult("V1", "交付物", "pass", [], "")
                r2 = auto_verify.RuleResult("V2", "字段", "fail",
                                           [{"code": "X", "severity": "P1", "location": "l",
                                             "detail": "d", "spec": "s"}], "")
                result = auto_verify.VerifyResult("r.md", "2026-11-01T00:00:00",
                                                  rules=[r1, r2], actions={})
                self.assertEqual(result.counts()["P0"], 0)
                self.assertEqual(result.counts()["P1"], 1)
                self.assertFalse(result.passed)
                self.assertTrue(result.log_path.is_absolute())

    def test_write_log(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                r = auto_verify.RuleResult("V1", "交付物", "pass", [], "")
                result = auto_verify.VerifyResult("r.md", "2026-11-01T00:00:00",
                                                  rules=[r], actions={})
                auto_verify.write_log(result, "verify/r.json")
                self.assertTrue(result.log_path.is_file())
                payload = json.loads(result.log_path.read_text(encoding="utf-8"))
                self.assertEqual(payload["report"], "r.md")

    def test_submit_audit_mocked(self):
        fake = SimpleNamespace(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(auto_verify, "subprocess",
                               SimpleNamespace(run=mock.Mock(return_value=fake))) as sp:
            ok, out = auto_verify.submit_audit("r.md")
        self.assertTrue(ok)
        self.assertIn("ok", out)
        self.assertEqual(sp.run.call_count, 3)

        fake1 = SimpleNamespace(returncode=1, stdout="", stderr="bad")
        with mock.patch.object(auto_verify, "subprocess",
                               SimpleNamespace(run=mock.Mock(return_value=fake1))):
            ok, out = auto_verify.submit_audit("r.md")
        self.assertFalse(ok)
        self.assertIn("bad", out)

    def test_verify_report_missing_and_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                with mock.patch.object(auto_verify, "write_log") as wl:
                    result = auto_verify.verify_report("01-demo/reports/none.md",
                                                      dry_run=True, do_submit=False)
                self.assertEqual(result.rules[0].id, "V1")
                wl.assert_called_once()

                md = _make_topic(root, "01-demo", text=GOOD_TEXT, html=_good_html())
                rep = _rel(md, root)
                with mock.patch.object(auto_verify, "rule_v1_deliverables",
                                       lambda *a: (auto_verify.RuleResult("V1", "x", "pass", [], ""), False)), \
                        mock.patch.object(auto_verify, "rule_v2_fields",
                                          lambda *a: auto_verify.RuleResult(
                                              "V2", "x", "fail",
                                              [{"code": "PF-E1", "severity": "P1",
                                                "location": "", "detail": "d", "spec": "s"}], "")), \
                        mock.patch.object(auto_verify, "rule_v3_format",
                                          lambda *a: auto_verify.RuleResult("V3", "x", "pass", [], "")), \
                        mock.patch.object(auto_verify, "rule_v4_consistency",
                                          lambda *a: auto_verify.RuleResult("V4", "x", "pass", [], "")), \
                        mock.patch.object(auto_verify, "rule_v5_ranges",
                                          lambda *a: auto_verify.RuleResult("V5", "x", "pass", [], "")), \
                        mock.patch.object(audit_check, "iq_findings_by_path", return_value={}), \
                        mock.patch.object(audit_check, "l5_status", return_value={}), \
                        mock.patch.object(auto_verify, "write_back") as wb, \
                        mock.patch.object(auto_verify, "write_log"):
                    result = auto_verify.verify_report(rep, dry_run=True, do_submit=False)
                self.assertFalse(result.passed)
                self.assertTrue(result.actions["terminated"])
                wb.assert_not_called()

    def test_verify_report_dry_run_and_writeback(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                md = _make_topic(root, "01-demo", text=GOOD_TEXT, html=_good_html())
                rep = _rel(md, root)
                with mock.patch.object(auto_verify, "rule_v1_deliverables",
                                       lambda *a: (auto_verify.RuleResult("V1", "x", "pass", [], ""), False)), \
                        mock.patch.object(auto_verify, "rule_v2_fields",
                                          lambda *a: auto_verify.RuleResult("V2", "x", "pass", [], "")), \
                        mock.patch.object(auto_verify, "rule_v3_format",
                                          lambda *a: auto_verify.RuleResult("V3", "x", "pass", [], "")), \
                        mock.patch.object(auto_verify, "rule_v4_consistency",
                                          lambda *a: auto_verify.RuleResult("V4", "x", "pass", [], "")), \
                        mock.patch.object(auto_verify, "rule_v5_ranges",
                                          lambda *a: auto_verify.RuleResult("V5", "x", "pass", [], "")), \
                        mock.patch.object(audit_check, "iq_findings_by_path", return_value={}), \
                        mock.patch.object(audit_check, "l5_status", return_value={}), \
                        mock.patch.object(auto_verify, "write_log"):
                    result = auto_verify.verify_report(rep, dry_run=True, do_submit=False)
                self.assertTrue(result.passed)
                self.assertTrue(result.actions["dry_run"])
                self.assertNotIn("section_written", result.actions)

                md2 = _make_topic(root, "02-b", period="2026-10", text=GOOD_TEXT,
                                  html=_good_html())
                rep2 = _rel(md2, root)
                with mock.patch.object(auto_verify, "rule_v1_deliverables",
                                       lambda *a: (auto_verify.RuleResult("V1", "x", "pass", [], ""), False)), \
                        mock.patch.object(auto_verify, "rule_v2_fields",
                                          lambda *a: auto_verify.RuleResult("V2", "x", "pass", [], "")), \
                        mock.patch.object(auto_verify, "rule_v3_format",
                                          lambda *a: auto_verify.RuleResult("V3", "x", "pass", [], "")), \
                        mock.patch.object(auto_verify, "rule_v4_consistency",
                                          lambda *a: auto_verify.RuleResult("V4", "x", "pass", [], "")), \
                        mock.patch.object(auto_verify, "rule_v5_ranges",
                                          lambda *a: auto_verify.RuleResult("V5", "x", "pass", [], "")), \
                        mock.patch.object(audit_check, "iq_findings_by_path", return_value={}), \
                        mock.patch.object(audit_check, "l5_status", return_value={}), \
                        mock.patch.object(auto_verify, "write_log"), \
                        mock.patch.object(auto_verify, "submit_audit",
                                          return_value=(True, "ok")), \
                        mock.patch.object(md2html, "convert", return_value="<html></html>"):
                    result = auto_verify.verify_report(rep2, dry_run=False, do_submit=True)
                self.assertTrue(result.passed)
                self.assertTrue(result.actions["section_written"])
                self.assertTrue(result.actions["submitted"])

    def test_main_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with audit_env(root):
                argv = sys.argv
                try:
                    sys.argv = ["auto_verify.py"]
                    self.assertEqual(auto_verify.main(), 2)
                    sys.argv = ["auto_verify.py", "--report", "none.md"]
                    self.assertEqual(auto_verify.main(), 2)
                    md = _make_topic(root, "01-demo")
                    rep = _rel(md, root)
                    sys.argv = ["auto_verify.py", "--report", rep, "--dry-run", "--no-submit"]
                    with mock.patch.object(auto_verify, "verify_report",
                                           return_value=auto_verify.VerifyResult(
                                               rep, "2026-11-01T00:00:00",
                                               rules=[auto_verify.RuleResult("V1", "x", "pass", [], "")],
                                               actions={})):
                        self.assertEqual(auto_verify.main(), 0)
                finally:
                    sys.argv = argv


if __name__ == "__main__":
    unittest.main()
