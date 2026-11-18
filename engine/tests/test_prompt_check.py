"""``engine/tools/prompt_check.py`` 单元测试。

覆盖：业务提示词命名、继承声明、p3/p4/p5「信息缺口」结构、business-config
槽位与优先级口径、类型模板命名，以及 ``main`` 退出码（0/1/2）。

全部在 ``tempfile`` 临时目录内构造，不触碰真实仓库文件。
"""
from __future__ import annotations

import importlib.util
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


pc = _load("prompt_check", "engine/tools/prompt_check.py")

CONFIG_OK = """# 配置
{{REGION}} {{TOPIC}} {{REGISTRY_PATH}}
冲突时以本文件为准。
"""
BASELINE_OK = """# 基线
> 继承声明：[通用基座](../../engine/report_templates/prompt-generic-base.md)
"""
P3_OK = """# P3
## 信息缺口
- x
"""


class BusinessCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.bdir = self.root / "01-x"
        (self.bdir / "prompts").mkdir(parents=True)

    def _write(self, name: str, text: str) -> None:
        (self.bdir / "prompts" / name).write_text(text, encoding="utf-8")

    def _patch(self):
        return (mock.patch.object(pc, "ROOT", self.root),
                mock.patch.object(_common, "ROOT", self.root),
                mock.patch.object(pc, "iter_business_dirs",
                                  return_value=[_common.Business("01-x")]))

    def test_ok(self) -> None:
        self._write("business-config.md", CONFIG_OK)
        self._write("prompt-baseline-setup.md", BASELINE_OK)
        self._write("prompt-update.md", BASELINE_OK)
        self._write("prompt-p3-evidence-verification.md", P3_OK)
        p1, p2, p3 = self._patch()
        with p1, p2, p3:
            self.assertEqual(pc.check(self.root), [])

    def test_bad_name(self) -> None:
        self._write("business-config.md", CONFIG_OK)
        self._write("prompt_bad.md", BASELINE_OK)
        p1, p2, p3 = self._patch()
        with p1, p2, p3:
            out = pc.check(self.root)
        self.assertTrue(any("命名不符" in x for x in out))

    def test_missing_inherit(self) -> None:
        self._write("business-config.md", CONFIG_OK)
        self._write("prompt-baseline-setup.md", "# 基线\n无继承\n")
        p1, p2, p3 = self._patch()
        with p1, p2, p3:
            out = pc.check(self.root)
        self.assertTrue(any("继承声明" in x for x in out))

    def test_p3_missing_gap(self) -> None:
        self._write("business-config.md", CONFIG_OK)
        self._write("prompt-baseline-setup.md", BASELINE_OK)
        self._write("prompt-p3-evidence-verification.md", "# P3\n无\n")
        p1, p2, p3 = self._patch()
        with p1, p2, p3:
            out = pc.check(self.root)
        self.assertTrue(any("信息缺口" in x for x in out))

    def test_config_missing_slot(self) -> None:
        self._write("business-config.md", "# 配置\n{{REGION}} {{TOPIC}}\n冲突时\n")
        self._write("prompt-baseline-setup.md", BASELINE_OK)
        p1, p2, p3 = self._patch()
        with p1, p2, p3:
            out = pc.check(self.root)
        self.assertTrue(any("{{REGISTRY_PATH}}" in x for x in out))

    def test_config_missing_priority(self) -> None:
        self._write("business-config.md", "# 配置\n{{REGION}} {{TOPIC}} {{REGISTRY_PATH}}\n")
        self._write("prompt-baseline-setup.md", BASELINE_OK)
        p1, p2, p3 = self._patch()
        with p1, p2, p3:
            out = pc.check(self.root)
        self.assertTrue(any("优先级" in x for x in out))

    def test_missing_config(self) -> None:
        self._write("prompt-baseline-setup.md", BASELINE_OK)
        p1, p2, p3 = self._patch()
        with p1, p2, p3:
            out = pc.check(self.root)
        self.assertTrue(any("business-config.md" in x for x in out))


class TemplateCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_template_naming_ok(self) -> None:
        d = self.root / "engine" / "report_templates" / "t"
        d.mkdir(parents=True)
        (d / "prompt-update-template.md").write_text("x", encoding="utf-8")
        self.assertEqual(pc.check_templates(self.root), [])

    def test_template_naming_bad(self) -> None:
        d = self.root / "engine" / "report_templates" / "t"
        d.mkdir(parents=True)
        (d / "prompt_update.md").write_text("x", encoding="utf-8")
        out = pc.check_templates(self.root)
        self.assertTrue(any("prompt-<kebab>-template.md" in x for x in out))

    def test_generic_naming_bad(self) -> None:
        d = self.root / "engine" / "report_templates" / "t" / "prompts"
        d.mkdir(parents=True)
        (d / "prompt-update.md").write_text("x", encoding="utf-8")
        self.assertEqual(pc.check_templates(self.root), [])
        (d / "prompt_update.md").write_text("x", encoding="utf-8")
        out = pc.check_templates(self.root)
        self.assertTrue(any("命名不符" in x for x in out))


class MainCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_main_exit_1(self) -> None:
        with mock.patch.object(pc, "ROOT", self.root), \
                mock.patch.object(pc, "check", return_value=["x"]), \
                mock.patch.object(sys, "argv", ["prompt_check.py"]):
            self.assertEqual(pc.main(), 1)

    def test_main_warn_exit_2(self) -> None:
        with mock.patch.object(pc, "ROOT", self.root), \
                mock.patch.object(pc, "check", return_value=["x"]), \
                mock.patch.object(sys, "argv", ["prompt_check.py", "--warn"]):
            self.assertEqual(pc.main(), 2)

    def test_main_ok_exit_0(self) -> None:
        with mock.patch.object(pc, "ROOT", self.root), \
                mock.patch.object(pc, "check", return_value=[]), \
                mock.patch.object(sys, "argv", ["prompt_check.py"]):
            self.assertEqual(pc.main(), 0)


if __name__ == "__main__":
    unittest.main()
