"""``engine/tools/source_language_gate.py`` 单元测试。

覆盖：政策加载（schema 校验）、business-config 规则逐字一致、
中文来源许可模式识别、域名黑名单匹配、报告 URL 扫描，以及主入口退出码（0/1/2）。

全部在 ``tempfile`` 临时目录内构造，不触碰真实仓库文件。
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "engine" / "tools"))

import _common  # noqa: E402


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


slg = _load("source_language_gate", "engine/tools/source_language_gate.py")

CANON = "仅英文 / 日文来源：① 官方权威；② 主流投资平台 / 顾问机构；③ 主流新闻媒体。杜绝中文来源。"


def _policy(tmp: Path, **over) -> Path:
    data = {
        "schema_version": "1.0",
        "rule_id": "en-ja-official-only",
        "source_language_rule": CANON,
        "allowed_languages": ["en", "ja"],
        "allowed_source_classes": ["官方权威", "主流投资平台", "顾问机构", "主流新闻媒体"],
        "forbidden_permission_patterns": ["中文来源仅作线索", "日 / 中", "中国侧输入"],
        "blocked_domains": ["gov.cn", "sina.com.cn", "qq.com"],
    }
    data.update(over)
    p = tmp / "source-policy.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


class PolicyCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_load_ok(self) -> None:
        p = _policy(self.root)
        with mock.patch.object(slg, "POLICY_PATH", p):
            data = slg.load_policy()
        self.assertEqual(data["source_language_rule"], CANON)

    def test_load_bad_schema(self) -> None:
        p = _policy(self.root, schema_version="9.9")
        with mock.patch.object(slg, "POLICY_PATH", p), self.assertRaises(ValueError):
            slg.load_policy()

    def test_load_missing_field(self) -> None:
        p = _policy(self.root)
        data = json.loads(p.read_text(encoding="utf-8"))
        del data["blocked_domains"]
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        with mock.patch.object(slg, "POLICY_PATH", p), self.assertRaises(ValueError):
            slg.load_policy()


class PromptCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.bdir = self.root / "01-x"
        (self.bdir / "prompts").mkdir(parents=True)
        self.policy = _policy(self.root)

    def _patch(self):
        return (mock.patch.object(slg, "ROOT", self.root),
                mock.patch.object(slg, "POLICY_PATH", self.policy),
                mock.patch.object(_common, "ROOT", self.root),
                mock.patch.object(slg, "iter_business_dirs",
                                  return_value=[_common.Business("01-x")]))

    def _write_config(self, rule_line: str) -> None:
        (self.bdir / "prompts" / "business-config.md").write_text(rule_line, encoding="utf-8")

    def test_ok(self) -> None:
        self._write_config(
            "# 配置\n\n```\n{{SOURCE_LANGUAGE_RULE}} = " + CANON + "\n```\n")
        p1, p2, p3, p4 = self._patch()
        with p1, p2, p3, p4:
            self.assertEqual(slg.check_prompts(slg.load_policy()), [])

    def test_rule_mismatch(self) -> None:
        self._write_config(
            "# 配置\n\n```\n{{SOURCE_LANGUAGE_RULE}} = 中文官方一手优先\n```\n")
        p1, p2, p3, p4 = self._patch()
        with p1, p2, p3, p4:
            problems = slg.check_prompts(slg.load_policy())
        self.assertEqual(len(problems), 1)
        self.assertIn("不一致", problems[0])

    def test_missing_variable(self) -> None:
        self._write_config("# 配置\n无变量\n")
        p1, p2, p3, p4 = self._patch()
        with p1, p2, p3, p4:
            problems = slg.check_prompts(slg.load_policy())
        self.assertTrue(any("缺" in x for x in problems))

    def test_permission_pattern(self) -> None:
        self._write_config(
            "# 配置\n\n```\n{{SOURCE_LANGUAGE_RULE}} = " + CANON + "\n```\n\n"
            "每条数据必须附 URL；中文来源仅作线索。\n")
        p1, p2, p3, p4 = self._patch()
        with p1, p2, p3, p4:
            problems = slg.check_prompts(slg.load_policy())
        self.assertTrue(any("中文来源仅作线索" in x for x in problems))

    def test_canonical_rule_not_flagged(self) -> None:
        """canonical 规则文本本身含「中文来源」，不得被许可模式误伤。"""
        self._write_config(
            "# 配置\n\n```\n{{SOURCE_LANGUAGE_RULE}} = " + CANON + "\n```\n")
        p1, p2, p3, p4 = self._patch()
        with p1, p2, p3, p4:
            self.assertEqual(slg.check_prompts(slg.load_policy()), [])


class DomainCase(unittest.TestCase):
    def test_match(self) -> None:
        domains = ["gov.cn", "sina.com.cn", "qq.com"]
        self.assertEqual(slg.is_blocked("https://www.stats.gov.cn/x.html", domains), "gov.cn")
        self.assertEqual(slg.is_blocked("https://mp.weixin.qq.com/s?x=1", domains), "qq.com")
        self.assertEqual(slg.is_blocked("https://cj.sina.com.cn/a", domains), "sina.com.cn")

    def test_no_match(self) -> None:
        domains = ["gov.cn", "sina.com.cn"]
        self.assertIsNone(slg.is_blocked("https://www.mlit.go.jp/x", domains))
        self.assertIsNone(slg.is_blocked("https://www.reuters.com/x", domains))
        # 子串不得误伤（gov.cn 不等于 notgov.cn）
        self.assertIsNone(slg.is_blocked("https://example.com/gov.cn", domains))


class ReportCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.policy = _policy(self.root)

    def test_report_flag(self) -> None:
        f = self.root / "01-x" / "reports" / "2026-11-x.md"
        f.parent.mkdir(parents=True)
        f.write_text(
            "来源：\n- [机构](https://www.stats.gov.cn/x)\n- [Reuters](https://www.reuters.com/y)\n",
            encoding="utf-8")
        with mock.patch.object(slg, "POLICY_PATH", self.policy), \
                mock.patch.object(slg, "ROOT", self.root):
            problems = slg.check_reports(slg.load_policy(), [f])
        self.assertEqual(len(problems), 1)
        self.assertIn("gov.cn", problems[0])


class MainCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.bdir = self.root / "01-x"
        (self.bdir / "prompts").mkdir(parents=True)
        self.policy = _policy(self.root)

    def _patch(self):
        return (mock.patch.object(slg, "ROOT", self.root),
                mock.patch.object(slg, "POLICY_PATH", self.policy),
                mock.patch.object(_common, "ROOT", self.root),
                mock.patch.object(slg, "iter_business_dirs",
                                  return_value=[_common.Business("01-x")]))

    def test_exit_0(self) -> None:
        (self.bdir / "prompts" / "business-config.md").write_text(
            "{{SOURCE_LANGUAGE_RULE}} = " + CANON + "\n", encoding="utf-8")
        p1, p2, p3, p4 = self._patch()
        with p1, p2, p3, p4:
            self.assertEqual(slg.main([]), 0)

    def test_exit_1(self) -> None:
        (self.bdir / "prompts" / "business-config.md").write_text(
            "{{SOURCE_LANGUAGE_RULE}} = 中文官方一手优先\n", encoding="utf-8")
        p1, p2, p3, p4 = self._patch()
        with p1, p2, p3, p4:
            self.assertEqual(slg.main([]), 1)

    def test_exit_2_warn(self) -> None:
        (self.bdir / "prompts" / "business-config.md").write_text(
            "{{SOURCE_LANGUAGE_RULE}} = 中文官方一手优先\n", encoding="utf-8")
        p1, p2, p3, p4 = self._patch()
        with p1, p2, p3, p4:
            self.assertEqual(slg.main(["--warn"]), 2)


if __name__ == "__main__":
    unittest.main()
