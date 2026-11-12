# -*- coding: utf-8 -*-
"""提示词治理契约测试：从 schedule.json 读取真实主题文件。"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SCHEDULE = json.loads((ROOT / "prompts/schedule.json").read_text(encoding="utf-8"))
TOPICS = {topic["id"]: topic for topic in SCHEDULE["topics"]}
MONITOR_ID = next(topic_id for topic_id, topic in TOPICS.items() if topic["kind"] == "monitor")

SHARED = {
    "通用基座": ROOT / "prompts/通用基座/prompt-generic-base.md",
    "公共规范": ROOT / "prompts/monitoring-common-spec.md",
    "职业模板": ROOT / "prompts/职业就业调研/prompt-employment-research-template.md",
    "市场模板": ROOT / "prompts/市场指标监测/prompt-monthly-monitor-template.md",
    "知识库模板": ROOT / "prompts/知识库主题更新/prompt-knowledge-topic-update-template.md",
    "职业脚手架": ROOT / "prompts/脚手架/prompt-脚手架-职业就业调研.md",
    "知识库脚手架": ROOT / "prompts/脚手架/prompt-脚手架-知识库主题更新.md",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def topic_path(topic_id: str, key: str = "prompt") -> Path:
    return ROOT / TOPICS[topic_id][key]


def topic_text(topic_id: str, key: str = "prompt") -> str:
    return read(topic_path(topic_id, key))


def section(text: str, start: str, end: str | None = None) -> str:
    if start not in text:
        return ""
    tail = text.split(start, 1)[1]
    return tail.split(end, 1)[0] if end and end in tail else tail


def numbered_rows(text: str) -> dict[int, str]:
    return {
        int(number): name.strip()
        for number, name in re.findall(r"(?m)^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", text)
    }


def normalized_name(value: str) -> str:
    return re.sub(r"\s+", "", value)


def handbook_headings(topic_id: str) -> dict[str, str]:
    return dict(re.findall(r"(?m)^##\s+(\d{2})\s+(.+?)\s*$", topic_text(topic_id, "target")))


def arrow_targets(line: str) -> set[str]:
    match = re.search(r"→\s*(\d{2}(?:\s*[/、,]\s*\d{2})*)", line)
    return set(re.findall(r"\d{2}", match.group(1))) if match else set()


def latest_monitor_report() -> Path:
    report_dir = topic_path(MONITOR_ID, "target")
    versioned = []
    pattern = re.compile(r"_v(\d{4})\.(\d{2})\.(\d{2})(?:_(\d+))?\.md$")
    for path in report_dir.glob("*.md"):
        match = pattern.search(path.name)
        if match:
            year, month, day, sequence = match.groups()
            versioned.append(((int(year), int(month), int(day), int(sequence or 0)), path))
    if not versioned:
        raise AssertionError("01 监测主题没有可解析的版本报告")
    return max(versioned, key=lambda item: item[0])[1]


def lines_linking_to(topic_id: str, target: Path) -> list[str]:
    prompt_path = topic_path(topic_id)
    matches = []
    for line in topic_text(topic_id).splitlines():
        for raw_href in re.findall(r"\]\(([^)]+)\)", line):
            href = raw_href.split()[0].strip("<>").split("#", 1)[0]
            if not href or re.match(r"https?://", href):
                continue
            if (prompt_path.parent / href).resolve() == target.resolve():
                matches.append(line)
                break
    return matches


def version_contract_errors(text: str) -> list[str]:
    errors = []
    if not re.search(r"vYYYY\.MM\.DD(?:\[_N\]|_N)", text):
        errors.append("缺少 vYYYY.MM.DD[_N] 同日序号格式")
    if "跨日运行禁止复用同日版本号" in text:
        errors.append("仍含跨日/同日病句")
    if "同日" not in text or not re.search(r"递增|逐次|加\s*1|不得复用|不可复用|不能复用", text):
        errors.append("未明确同日多次运行递增且不复用")
    if not re.search(r"不覆盖|不得覆盖|禁止覆盖|不可覆盖", text):
        errors.append("未明确禁止覆盖")
    return errors


NEGATIVE_MARKERS = (
    "不得", "禁止", "严禁", "不可", "不要", "避免", "❌", "不再",
    "不存在", "无官方", "虚构",
)


def affirmative_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if not any(marker in line for marker in NEGATIVE_MARKERS)]


def affirmative_clauses(text: str) -> list[str]:
    return [
        clause
        for line in text.splitlines()
        for clause in re.split(r"[。；;]", line)
        if not any(marker in clause for marker in NEGATIVE_MARKERS)
    ]


def load_validate_module():
    path = ROOT / "prompts/tools/validate.py"
    spec = importlib.util.spec_from_file_location("real_prompt_validate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with mock.patch.object(sys, "path", [str(path.parent), *sys.path]):
        spec.loader.exec_module(module)
    return module


VALIDATE = load_validate_module()
READONLY_RE = re.compile(r"只读|不得独立回写|不独立回写|禁止独立回写")
REVIEWS_ASSIGNMENT_RE = re.compile(r"(?m)^\s*\{\{REVIEWS_DIR\}\}\s*=\s*(.*)$")
BROAD_OVERRIDE_RE = re.compile(
    r"与上层冲突时以本文件为准|冲突时以本文件为准|冲突时本文件优先|"
    r"项目/主题专属\s*>\s*类型模板\s*>\s*通用基座"
)

# 仅列行为分组；所有文件路径仍由 schedule.json 派生。
EXTERNAL_SSOT_ITEMS = {
    "02-career-driver": (
        ("薪资", r"薪资|賃金", r"#\s*5\b"),
        ("求人", r"求人", r"#\s*6\b"),
        ("驾照费用", r"(?:免许|驾照|教习).{0,12}费用", r"#\s*14\b"),
    ),
    "05-industry-autonomous": (("L4", r"L4", r"#\s*10\b"),),
    "07-economy-finance": (
        ("运输业工资", r"(?:运输业|運輸業|運输业).{0,8}(?:工资|賃金)", r"#\s*5\b"),
        ("汇率", r"汇率|為替", r"3\.5|交叉验证输入"),
    ),
    "08-visa-immigration": (
        ("受入上限", r"受入上限", r"#\s*2\b"),
        ("在留者数", r"在留者", r"#\s*1\b"),
        ("试验要件", r"试验要件|試験要件", r"#\s*2\b"),
        ("试验费用", r"(?:试验|試験|考试).{0,6}费用", r"#\s*3\b"),
    ),
    "09-politics-law": (("ITJ/GFP 修正事实", r"ITJ|GFP", r"修正清单|已修正事实"),),
    "10-education-qualification": (("驾照费用", r"(?:驾照|免许|教习).{0,8}费用", r"#\s*14\b"),),
    "11-language-japanese": (
        ("考试日程", r"日程", r"#\s*3\b"),
        ("考试费用", r"费用", r"#\s*3\b"),
        ("考位", r"考位|考场", r"#\s*3\b"),
    ),
}


def compact_paragraphs(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", paragraph) for paragraph in re.split(r"\n\s*\n", text)]


def valid_override_scope(paragraph: str) -> bool:
    clauses = re.split(r"[。；]", paragraph)
    allowed = (r"输出结构|输出形态|输出格式", r"路径", r"运行变量", r"更严格|严于", r"类型纪律|类型规范|核验纪律")
    protected = (r"引用", r"编造", r"事实\s*(?:与|/|及)\s*推断", r"SSOT|单一事实源|主责", r"已修正事实")
    allow_ok = any(
        re.search(r"可覆盖(?:范围|事项)?\s*(?:仅限|限于|仅)|覆盖范围\s*(?:仅限|限于|仅)", clause)
        and all(re.search(pattern, clause) for pattern in allowed)
        for clause in clauses
    )
    deny_ok = any(
        re.search(r"不可覆盖|不得覆盖|不可弱化|不得弱化", clause)
        and all(re.search(pattern, clause) for pattern in protected)
        for clause in clauses
    )
    return allow_ok and deny_ok


def override_contract_errors(text: str) -> list[str]:
    paragraphs = compact_paragraphs(text)
    errors = []
    if not any(valid_override_scope(paragraph) for paragraph in paragraphs):
        errors.append("缺少同段可覆盖允许清单及不可覆盖红线清单")
    if any(BROAD_OVERRIDE_RE.search(p) and not valid_override_scope(p) for p in paragraphs):
        errors.append("仍有未绑定完整允许/禁止范围的宽泛优先权")
    return errors


def previous_snapshot_order_errors(text: str) -> list[str]:
    errors = []
    ordered = False
    for paragraph in compact_paragraphs(text):
        if not all(token in paragraph for token in ("{{PREVIOUS_REPORT_PATH}}", "上一版", "快照")):
            continue
        read_step = re.search(r"先.{0,100}读取", paragraph)
        compare_step = re.search(r"差异(?:比较|对比|比对)?|比较差异|比对差异", paragraph)
        write_step = re.search(
            r"再.{0,100}(?:(?:更新|回写).{0,40}(?:\{\{REGISTRY_PATH\}\}|登记册)|"
            r"(?:\{\{REGISTRY_PATH\}\}|登记册).{0,40}(?:更新|回写))",
            paragraph,
        )
        if read_step and compare_step and write_step and read_step.end() <= compare_step.start() < write_step.start():
            ordered = True
            break
    if not ordered:
        errors.append("缺少先读取指定上一版快照并比较、再更新登记册的同段顺序协议")
    for line in text.splitlines():
        if "上次值" in line and "登记册" in line and re.search(r"取自|来自|读取填入|从.*读取", line):
            errors.append("上次值仍取自登记册而非指定上一版快照")
            break
    return errors


def effective_reviews_defaults(text: str) -> list[str]:
    return [
        match.group(0).strip()
        for match in REVIEWS_ASSIGNMENT_RE.finditer(text)
        if "reviews/" in match.group(1).lower()
    ]


def external_item_contract_errors(topic_id: str) -> list[str]:
    paragraphs = compact_paragraphs(topic_text(topic_id))
    errors = []
    for label, item_pattern, anchor_pattern in EXTERNAL_SSOT_ITEMS[topic_id]:
        bound = [
            paragraph for paragraph in paragraphs
            if MONITOR_ID in paragraph
            and re.search(item_pattern, paragraph)
            and re.search(anchor_pattern, paragraph)
        ]
        if not bound:
            errors.append(f"{label}: 未绑定 01 主责项 {anchor_pattern}")
            continue
        if not any(
            READONLY_RE.search(paragraph)
            and "冲突" in paragraph
            and "官方" in paragraph
            and re.search(r"01-ssw-driver.{0,80}主责|主责.{0,80}01-ssw-driver", paragraph)
            and re.search(r"复核|核验", paragraph)
            and re.search(r"更新|回写", paragraph)
            for paragraph in bound
        ):
            errors.append(f"{label}: 绑定段缺少只读、官方复核及 01 主责更新")
    return errors


def registry_write_scope_errors(text: str) -> list[str]:
    errors = []
    paragraphs = [
        paragraph for paragraph in compact_paragraphs(text)
        if "{{REGISTRY_PATH}}" in paragraph and re.search(r"先读后写|运行后回写|已读已写|回写登记册", paragraph)
    ]
    if not paragraphs:
        return ["缺少登记册统一回写协议"]
    for paragraph in paragraphs:
        local_only = re.search(r"(?:仅|只).{0,24}(?:本主题|本地).{0,16}主责", paragraph)
        external_excluded = re.search(
            r"(?:外部|01-ssw-driver).{0,80}(?:排除|除外|只读|不得.{0,16}回写|不.{0,16}回写)",
            paragraph,
        )
        if not local_only or not external_excluded:
            errors.append("统一回写未同时限定本主题主责项并排除外部 SSOT 项")
    return errors


def registry_current_numeric_literals() -> set[str]:
    literals = set()
    for line in topic_text(MONITOR_ID, "registry").splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        current_cell = cells[3]
        for match in VALIDATE.HARDCODED_VALUE_RE.finditer(current_cell):
            number = re.match(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", match.group()).group()
            if re.fullmatch(r"(?:19|20)\d{2}", number):
                continue
            literals.add(number)
        literals.update(re.findall(r"(?<![\d.])\d{1,3}(?:,\d{3})+(?![\d.])", current_cell))
    return literals


class PromptContractTests(unittest.TestCase):
    def test_version_rule_is_unified_with_same_day_sequence_and_no_overwrite(self):
        paths = [SHARED["通用基座"], SHARED["公共规范"], SHARED["职业脚手架"], topic_path(MONITOR_ID)]
        failures = {path.name: errors for path in paths if (errors := version_contract_errors(read(path)))}
        self.assertEqual({}, failures)

    def test_layers_have_explicit_override_allowlist_and_redline_denylist(self):
        failures = {
            name: errors
            for name, path in SHARED.items()
            if (errors := override_contract_errors(read(path)))
        }
        self.assertEqual({}, failures)

    def test_registry_current_values_and_output_snapshots_are_distinct(self):
        failures = {}
        for name in ("通用基座", "知识库模板"):
            text = read(SHARED[name])
            candidates = [
                paragraph for paragraph in compact_paragraphs(text)
                if "登记册" in paragraph and "快照" in paragraph
            ]
            semantics_ok = any(
                re.search(r"当前活值|当前值", paragraph)
                and "截至本次核验" in paragraph
                and "来源日期" in paragraph
                and "基准版本" in paragraph
                and re.search(r"历史值|历史快照", paragraph)
                and re.search(r"区分|不得混用|不可混用", paragraph)
                for paragraph in candidates
            )
            output_ok = any(
                "数据基准日" in paragraph
                and re.search(r"本次输出|本次报告|本次手册", paragraph)
                and re.search(r"新快照|历史快照", paragraph)
                for paragraph in candidates
            )
            missing = []
            if not semantics_ok:
                missing.append("同段以来源日期/基准版本区分当前活值与历史快照")
            if not output_ok:
                missing.append("本次输出须成为带数据基准日的新快照")
            if missing:
                failures[name] = missing
        self.assertEqual({}, failures)

    def test_differences_use_previous_snapshot_without_rewriting_history(self):
        failures = {}
        for name, historical_object in (("通用基座", "旧报告"), ("知识库模板", "更新日志")):
            text = read(SHARED[name])
            missing = [token for token in ("上一版", "差异", historical_object) if token not in text]
            if not re.search(r"不得追溯改写|不追溯改写|禁止追溯改写|不得回溯改写|不得随登记册改写", text):
                missing.append("历史记录不得追溯改写")
            if missing:
                failures[name] = missing
        self.assertEqual({}, failures)

    def test_previous_snapshot_comparison_precedes_registry_write(self):
        failures = {
            name: errors
            for name in ("通用基座", "知识库模板")
            if (errors := previous_snapshot_order_errors(read(SHARED[name])))
        }
        self.assertEqual({}, failures)

    def test_non_monitor_topics_have_no_effective_reviews_default(self):
        failures = {}
        for topic_id in TOPICS:
            if topic_id == MONITOR_ID:
                continue
            text = topic_text(topic_id)
            problems = effective_reviews_defaults(text)
            affirmative_paths = [
                line.strip() for line in affirmative_lines(text)
                if "../reviews/" in line and line.strip() not in problems
            ]
            problems.extend(affirmative_paths)
            if problems:
                failures[topic_id] = problems
        self.assertEqual({}, failures)

    def test_generic_base_reviews_require_explicit_opt_in_and_no_creation(self):
        text = read(SHARED["通用基座"])
        variable_lines = [line for line in text.splitlines() if "{{REVIEWS_DIR}}" in line and "=" in line]
        operational_lines = [
            line for line in text.splitlines()
            if "{{REVIEWS_DIR}}" in line or "运行复盘" in line
        ]
        failures = []
        if not any(
            "显式启用" in line and re.search(r"仅|方可", line)
            and "知识库" in line and re.search(r"默认省略|默认不设置|默认留空", line)
            for line in variable_lines
        ):
            failures.append("变量说明缺少仅显式启用设置、知识库默认省略")
        if not any(
            re.search(r"未设置|未启用|留空", line)
            and re.search(r"不创建|不得创建|不新建", line)
            for line in operational_lines
        ):
            failures.append("执行/自检未明确未设置时不得创建目录")
        self.assertEqual([], failures)

    def test_employment_scaffold_expansion_inherits_version_contract(self):
        text = read(SHARED["职业脚手架"])
        text = text.replace("{{项目名}}", "契约测试项目").replace("{{slug}}", "contract-test")
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp) / "generated-prompt.md"
            generated.write_text(text, encoding="utf-8")
            self.assertEqual([], version_contract_errors(read(generated)))

    def test_knowledge_scaffold_expansion_has_no_reviews_default(self):
        source = read(SHARED["知识库脚手架"])
        problems = [f"默认文本: {line}" for line in effective_reviews_defaults(source)]
        text = REVIEWS_ASSIGNMENT_RE.sub(lambda match: match.group(0).split("=", 1)[0] + "=", source)
        for placeholder, value in {
            "{{主题名}}": "契约测试主题",
            "{{slug}}": "contract-test",
            "{{中文名}}": "契约测试",
            "{{target}}": "anchor",
        }.items():
            text = text.replace(placeholder, value)
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp) / "generated-prompt.md"
            generated.write_text(text, encoding="utf-8")
            expanded = read(generated)
            problems.extend(f"留空展开: {line}" for line in effective_reviews_defaults(expanded))
            affirmative = "\n".join(affirmative_lines(expanded))
            if "../reviews/" in affirmative:
                problems.append("REVIEWS_DIR 显式留空展开后仍有有效 ../reviews/ 路径")
            self.assertFalse((Path(tmp) / "reviews").exists())
        self.assertEqual([], problems)

    def test_driver_license_trigger_targets_real_chapter_01(self):
        text = topic_text("02-career-driver")
        trigger = section(text, "## 四、", "## 五、")
        line = next((line for line in trigger.splitlines() if "免许制度/教习费用变化" in line), "")
        self.assertEqual({"01"}, arrow_targets(line))
        self.assertIn("01", handbook_headings("02-career-driver"))
        chapter_01 = next((line for line in section(text, "## 五、", "## 六、").splitlines() if line.startswith("【01 ")), "")
        self.assertIn("免许", chapter_01)
        self.assertIn("费用", chapter_01)

    def test_management_trigger_distinguishes_local_02_from_topic_10(self):
        text = topic_text("03-career-management")
        trigger = section(text, "## 四、", "## 五、")
        line = next((line for line in trigger.splitlines() if "讲习/资格制度变化" in line), "")
        self.assertEqual({"02"}, arrow_targets(line))
        self.assertNotRegex(line, r"→\s*02/10")
        self.assertRegex(line, r"本手册|本地")
        self.assertIn("10-education-qualification", line)
        self.assertIn("02", handbook_headings("03-career-management"))

    def test_logistics_triggers_target_existing_real_chapters(self):
        text = topic_text("04-industry-logistics")
        headings = handbook_headings("04-industry-logistics")
        self.assertEqual({"01", "02", "03", "04"}, set(headings))
        trigger = section(text, "## 四、", "## 五、")
        expected = {"2024年問題": {"01", "04"}, "自动驾驶/自动化重大政策进展": {"03"}, "SPPI 月次更新": {"04"}}
        actual = {}
        for label in expected:
            line = next((line for line in trigger.splitlines() if label in line), "")
            actual[label] = arrow_targets(line)
        self.assertEqual(expected, actual)
        for targets in actual.values():
            self.assertLessEqual(targets, set(headings))

    def test_logistics_update_blocks_match_real_handbook(self):
        text = topic_text("04-industry-logistics")
        headings = handbook_headings("04-industry-logistics")
        updates = section(text, "## 五、", "## 六、")
        blocks = dict(re.findall(r"【(\d{2})\s+([^】]+)】", updates))
        self.assertEqual(set(headings), set(blocks))
        self.assertIn("自动化", blocks.get("03", ""))
        self.assertIn("行业数据", blocks.get("04", ""))

    def test_logistics_self_check_assigns_technology_to_topic_05(self):
        selfcheck = section(topic_text("04-industry-logistics"), "## 九、")
        self.assertRegex(selfcheck, r"本篇产业面\s*/\s*05\s*技术与制度面")
        self.assertNotIn("06 技术面", selfcheck)

    def test_logistics_registry_link_is_not_mislabeled_as_latest_report(self):
        registry = topic_path(MONITOR_ID, "registry")
        lines = lines_linking_to("04-industry-logistics", registry)
        self.assertTrue(lines, "04 应保留 01 登记册交叉验证链接")
        for line in lines:
            self.assertNotRegex(line, r"\[01-ssw-driver\][^\n]*最新报告")

    def test_economy_prompt_tracks_every_registry_item(self):
        prompt = topic_text("07-economy-finance")
        registry_items = numbered_rows(topic_text("07-economy-finance", "registry"))
        prompt_items = numbered_rows(prompt)
        self.assertEqual(6, len(registry_items))
        self.assertEqual(
            {number: normalized_name(name) for number, name in registry_items.items()},
            {number: normalized_name(name) for number, name in prompt_items.items()},
        )
        declared = re.search(r"(\d+)\s*项指标活值登记册", prompt)
        checked = re.search(r"追踪表\s*(\d+)\s*项均已核对", prompt)
        self.assertTrue(declared and int(declared.group(1)) == len(registry_items))
        self.assertTrue(checked and int(checked.group(1)) == len(registry_items))

    def test_economy_minimum_wage_has_annual_trigger_update_and_selfcheck(self):
        text = topic_text("07-economy-finance")
        trigger = section(text, "## 四、", "## 五、")
        line = next((line for line in trigger.splitlines() if "最低賃金" in line), "")
        self.assertRegex(line, r"年度|每年")
        self.assertEqual({"01"}, arrow_targets(line))
        self.assertIn("01", handbook_headings("07-economy-finance"))
        self.assertIn("最低賃金", section(text, "## 五、", "## 六、"))
        self.assertIn("最低賃金", section(text, "## 九、"))

    def test_economy_minimum_wage_binds_mhlw_official_source(self):
        text = topic_text("07-economy-finance")
        operational = section(text, "## 四、", "## 七、")
        wage_blocks = [block for block in compact_paragraphs(operational) if "最低賃金" in block]
        self.assertTrue(
            any("mhlw.go.jp" in block.lower() for block in wage_blocks),
            "最低賃金触发/更新/追踪块须直接绑定厚労省 mhlw.go.jp 官方来源",
        )

    def test_economy_net_income_model_and_registry_have_distinct_anchors(self):
        latest = latest_monitor_report()
        report_lines = [line for line in lines_linking_to("07-economy-finance", latest) if "3.5" in line or "净收入模型" in line]
        self.assertTrue(report_lines, "3.5 净收入模型应链接 01 最新报告正文")
        registry_lines = lines_linking_to("07-economy-finance", topic_path(MONITOR_ID, "registry"))
        self.assertTrue(registry_lines, "活值应另锚 01 登记册")
        for line in registry_lines:
            self.assertNotIn("3.5", line)

    def test_language_exam_values_and_corrections_use_ssw_ssot(self):
        topic_id = "11-language-japanese"
        text = topic_text(topic_id)
        registry_row = next((line for line in topic_text(MONITOR_ID, "registry").splitlines() if re.match(r"\|\s*3\s*\|", line)), "")
        self.assertIn("日程", registry_row)
        self.assertIn("费用", registry_row)
        self.assertRegex(registry_row, r"考位|考点|考场")
        linked_lines = lines_linking_to(topic_id, topic_path(MONITOR_ID, "registry"))
        missing = []
        for label, pattern in (("日程", r"日程"), ("费用", r"费用"), ("考位", r"考位|考场")):
            if not any("#3" in line and re.search(pattern, line) for line in linked_lines):
                missing.append(f"{label} 未单独显式锚定 01 登记册 #3")
        self.assertEqual([], missing)
        self.assertFalse(lines_linking_to(topic_id, topic_path("08-visa-immigration")))
        self.assertFalse("08-visa-immigration 追踪表" in text, "08 prompt/追踪表不得作为考试活值 SSOT")
        correction_lines = [line for line in lines_linking_to(topic_id, latest_monitor_report()) if "修正" in line]
        self.assertTrue(correction_lines, "考试修正清单应锚 01 最新报告文首")

    def test_language_n3_n2_updates_are_explicit(self):
        updates = section(topic_text("11-language-japanese"), "## 五、", "## 六、")
        for level in ("N3", "N2"):
            line = next((line for line in updates.splitlines() if level in line and line.startswith("【")), "")
            self.assertNotIn("同上", line)
            self.assertIn("更新：", line)
            self.assertIn("保持：", line)

    def test_politics_correction_list_anchors_latest_ssw_report(self):
        lines = [line for line in lines_linking_to("09-politics-law", latest_monitor_report()) if "修正" in line]
        self.assertTrue(lines, "09 的 ITJ/GFP 修正清单必须锚 01 最新报告文首，而非登记册")

    def test_politics_policy_log_links_visa_handbook_09(self):
        visa_headings = handbook_headings("08-visa-immigration")
        self.assertIn("09", visa_headings)
        self.assertIn("政策更新日志", visa_headings["09"])
        self.assertNotIn("09", handbook_headings("09-politics-law"))
        lines = lines_linking_to("09-politics-law", topic_path("08-visa-immigration", "target"))
        self.assertTrue(any("09" in line and "政策更新日志" in line for line in lines))

    def test_cross_topic_items_bind_owner_readonly_and_official_recheck(self):
        failures = {
            topic_id: errors
            for topic_id in EXTERNAL_SSOT_ITEMS
            if (errors := external_item_contract_errors(topic_id))
        }
        self.assertEqual({}, failures)

    def test_cross_topic_ssot_is_never_reverse_written(self):
        forbidden = ("回写监测报告并同步本主题", "冲突时以本文件为准", "冲突时本文件优先")
        failures = {}
        for topic_id in EXTERNAL_SSOT_ITEMS:
            problems = [phrase for phrase in forbidden if phrase in topic_text(topic_id)]
            if problems:
                failures[topic_id] = problems
        self.assertEqual({}, failures)

    def test_unified_registry_writes_exclude_external_ssot_items(self):
        failures = {
            topic_id: errors
            for topic_id in EXTERNAL_SSOT_ITEMS
            if (errors := registry_write_scope_errors(topic_text(topic_id)))
        }
        self.assertEqual({}, failures)

    def test_operational_instructions_have_no_legacy_names_or_placeholder_ditto(self):
        failures = {}
        for topic_id in TOPICS:
            text = topic_text(topic_id)
            operational = "\n".join((
                section(text, "## 五、", "## 六、"),
                section(text, "## 六、", "## 七、"),
                section(text, "## 七、", "## 八、"),
            ))
            problems = []
            for clause in affirmative_clauses(operational):
                if "同上" in clause:
                    problems.append("肯定语境同上")
                problems.extend(re.findall(r"(?<!\d)0[56]\s*文档", clause))
            if problems:
                failures[topic_id] = sorted(set(problems))
        self.assertEqual({}, failures)

    def test_ssw_does_not_restore_disproved_survey_itj_or_gfp(self):
        affirmative = "\n".join(affirmative_lines(topic_text(MONITOR_ID)))
        phrases = ("トラックドライバー不足実態調査", "トラックドライバー不足实态调查", "MLIT 実態調査", "ITJ 联系方式", "GFP 等官方支持机构", "GFP等官方支持机构")
        self.assertEqual([], [phrase for phrase in phrases if phrase in affirmative])

    def test_ssw_does_not_restore_auto_transport_ssw2_path(self):
        text = topic_text(MONITOR_ID)
        affirmative = "\n".join(affirmative_lines(text))
        self.assertIsNone(re.search(r"转特定技能\s*2\s*号", affirmative), "不得恢复自動車運送業转 2 号路径")
        self.assertIsNotNone(re.search(r"本分野.{0,12}(?:无|不得)\s*2\s*号", text), "应明确本分野无 2 号")

    def test_visa_self_check_has_no_current_registry_live_values(self):
        text = topic_text("08-visa-immigration")
        selfcheck = section(text, "## 九、")
        current_literals = registry_current_numeric_literals()
        self.assertTrue({"22,100", "843"}.issubset(current_literals), "01 登记册活值扫描夹具不得为空")
        leaks = [
            value for value in sorted(current_literals)
            if re.search(rf"(?<![\d,.]){re.escape(value)}(?![\d,.])", selfcheck)
        ]
        self.assertEqual([], leaks, "第九节不得复述 01 登记册的任何当前活值")
        corrections = section(text, "## 三、", "## 四、")
        self.assertIn("22,100", corrections, "修正事实清单中的历史修正数值不应被误删")
        self.assertIn("24,500", corrections)
        self.assertIn("OTIT", corrections)
        self.assertGreaterEqual(corrections.count("❌"), 3, "第三节既有修正事实应保留")

    def test_autonomous_industry_responsibility_belongs_to_topic_04(self):
        compact = re.sub(r"[*`\s]", "", topic_text("05-industry-autonomous"))
        self.assertIsNotNone(re.search(r"04(?:-industry-logistics)?写产业面", compact), "产业面主责应写 04")
        self.assertFalse("05写产业面" in compact, "05 不应同时自称产业面主责")

    def test_education_links_and_research_cover_expanded_scope(self):
        text = topic_text("10-education-qualification")
        audience = next((line for line in text.splitlines() if "岗位资格需求联动" in line), "")
        self.assertNotIn("02-career-driver/04", audience)
        self.assertIn("02-career-driver", audience)
        self.assertIn("03-career-management", audience)
        execution = section(text, "## 七、", "## 八、")
        self.assertRegex(execution, r"子女教育|学校教育")
        self.assertIn("高等教育", execution)
        self.assertIn("技人国", execution)

    def test_technology_and_education_keep_visa_chapter_05_links(self):
        headings = handbook_headings("08-visa-immigration")
        self.assertIn("05", headings)
        self.assertIn("特定技能2号", headings["05"])
        for topic_id in ("06-industry-technology", "10-education-qualification"):
            lines = [line for line in topic_text(topic_id).splitlines() if "05 章" in line and ("visa" in line or "08-visa-immigration" in line)]
            self.assertTrue(lines, f"{topic_id} 指向 08 手册 05 章的技人国长期路径链接应保留")

    def test_regional_prompt_keeps_current_bosaicho_name(self):
        text = topic_text("13-regional-info")
        self.assertIn("防災庁", text)
        self.assertIn("bousai.go.jp", text)

    def test_culture_keeps_seven_items_and_covers_rent_and_research(self):
        text = topic_text("12-culture-life")
        registry_items = numbered_rows(topic_text("12-culture-life", "registry"))
        prompt_items = numbered_rows(text)
        self.assertEqual(set(range(1, 8)), set(registry_items))
        self.assertEqual(set(registry_items), set(prompt_items))
        self.assertRegex(text, r"7\s*项指标活值登记册")
        execution = section(text, "## 七、", "## 八、")
        self.assertIn("医疗", execution)
        self.assertRegex(execution, r"住房|UR")
        self.assertIn("防灾", execution)
        rent_lines = [line for line in text.splitlines() if "租金" in line and "登记册" in line]
        self.assertTrue(any(READONLY_RE.search(line) for line in rent_lines), "外部主责租金项须只读，不得由 12 独立回写")


class ValidateHardcodedValueRegressionTests(unittest.TestCase):
    def scan(self, markdown: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompt = root / MONITOR_ID / "prompts/prompt-contract-fixture.md"
            prompt.parent.mkdir(parents=True)
            prompt.write_text(markdown, encoding="utf-8")
            errors, warnings = [], []
            with mock.patch.object(VALIDATE, "ROOT", root):
                VALIDATE.check_no_hardcoded_values(errors, warnings)
            self.assertEqual([], errors)
            return warnings

    def test_validate_flags_current_values_with_limit_and_requirement_context(self):
        warnings = self.scan(
            "- 当前有效值（以 prompt 为准）：受入上限为 22,100 人。\n"
            "- 当前有效值（以 prompt 为准）：技能試験要件费用为 6,500 円。\n"
        )
        self.assertEqual(2, len(warnings))
        self.assertTrue(any("22,100" in warning for warning in warnings))
        self.assertTrue(any("6,500" in warning for warning in warnings))

    def test_validate_flags_only_current_values_in_mixed_corrections(self):
        warnings = self.scan(
            "- ❌ 不得再称旧值 24,500 人；当前有效值为 22,100 人，以 prompt 为准。\n"
            "- 不得再称旧费用为 7,000 円；当前有效考试费为 6,500 円，以 prompt 为准。\n"
        )
        self.assertEqual(2, len(warnings))
        self.assertTrue(any("22,100" in warning for warning in warnings))
        self.assertTrue(any("6,500" in warning for warning in warnings))
        self.assertFalse(any("24,500" in warning or "7,000" in warning for warning in warnings))

    def test_validate_allows_stable_institutional_constants(self):
        warnings = self.scan(
            "- 制度常数（非追踪活值）：特定技能 1 号通算在留上限 5 年。\n"
            "- 制度常数（非追踪活值）：資格外活動許可周 28 時間上限。\n"
        )
        self.assertEqual([], warnings)

    def test_validate_allows_explicitly_negated_old_values(self):
        warnings = self.scan(
            "- ❌ 不得再称旧值 24,500 人为当前有效值。\n"
            "- 修正事实：不得再使用旧值 7,000 円。\n"
        )
        self.assertEqual([], warnings)


if __name__ == "__main__":
    unittest.main()
