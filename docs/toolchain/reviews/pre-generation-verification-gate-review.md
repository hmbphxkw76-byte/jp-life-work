# 双轴评审：生成前信息核验（闸0）+ 提交前内容硬门禁

> 任务 slug：`pre-generation-verification-gate`
> 评审日期：2026-11-22
> 评审对象：`engine/tools/generation_gate.py`、`engine/scripts/precommit_content_gate.py`、`engine/scripts/git-hooks/pre-commit`、`engine/report_templates/prompt-generic-base.md`、`.github/workflows/validate.yml`
> 规格：[pre-generation-verification-gate.md](../specs/pre-generation-verification-gate.md)
> 工单：[pre-generation-verification-gate.md](../tickets/pre-generation-verification-gate.md)

## 一、Standards 轴（规约符合性）

| 规约条款 | 结论 | 证据 |
|---|---|---|
| 命名规范（工具 `engine/tools/<snake_case>.py`；脚本 `engine/scripts/`） | 通过 | `generation_gate.py` / `precommit_content_gate.py` 均为 snake_case，位置正确 |
| 退出码契约 `0/1/2` | 通过 | `generation_gate.main` 返回 `1`（P0/P1）/`2`（仅 P2）/`0`；`precommit_content_gate.main` 返回 `1`（命中）/`0` |
| 异常不静默吞掉 | 通过 | 政策加载失败显式产出 `G0-*/PC-POLICY` P1 发现，不静默；`staged_entries` 的 git 失败返回空列表（无暂存即放行，语义明确） |
| 复用既有判定内核，不新写规则 | 通过 | 仅调用 `stage_gate_check` / `source_language_gate` / `verified_content_gate` / `source_check`，未新增判定常量 |
| 单一事实源不变 | 通过 | `source-policy.json` / `verified-content-policy.json` 未改动；全层零容忍口径与 CI 一致 |
| 生成物确定性 | 通过 | 未写时间戳、未写入库状态文件 |
| 测试先行 | 通过 | `test_generation_gate.py` / `test_precommit_content_gate.py` 先红后绿（实现前 ImportError，实现后 17 项通过） |
| 双轴评审 + 合并前检查单 | 通过 | 本报告；S6 检查单见 `engine/scripts/README.md` |

## 二、Spec 轴（规格 ↔ 实现映射）

| 规格条目 | 实现 | 验证 |
|---|---|---|
| 3.1 `generation_gate.py --topic/--all/--json` | `main()` 支持三参数；`check_topic` / `run_all` | `--topic 01-ssw-driver --json` 退出码 0；`--all --json` 含 `summary` |
| 3.1 G0-STRUCT / G0-LANG / G0-CONTENT / G0-SOURCE | 分别复用 `stage_gate_check.check_topic` / `source_language_gate.check_prompts` / `verified_content_gate.scan_text` / `source_check.extract_report` | 合成主题命中「待核实」→ `G0-CONTENT` P1；缺来源章节 → `G0-SOURCE` P1 |
| 3.2 `precommit_content_gate.py` 暂存核验 | `staged_entries()` 读 `git diff --cached`；`gate_entries()` 分类核验 | 含「待核实」暂存报告 → 退出码 1；干净 → 0；无暂存 → 0 |
| 3.3 pre-commit 接线 | `engine/scripts/git-hooks/pre-commit` 新增第 3 道检查；`branch_naming.install` 重装 | `install --check` 通过 |
| 3.4 提示词基座生成前步骤 | `prompt-generic-base.md` §八 新增「生成前信息核验（闸0）」+ §九 自检项 | `prompt_check.py` 全绿 |
| 3.5 CI 闸0 步骤 | `validate.yml` 增「生成前信息核验（闸0）」 | `generation_gate.py --all` 21/21 可生成，退出码 2 |

## 三、运行证据

```
$ python engine/tools/generation_gate.py --all
生成前信息核验（闸0）：21 个主题，可生成 21 / 阻断 0
  P0 0 / P1 0 / P2 1
退出码 2

$ python -m unittest engine.tests.test_generation_gate engine.tests.test_precommit_content_gate
Ran 18 tests ... OK
```

## 四、结论

- **Standards**：无 P0/P1。
- **Spec**：规格三节（接口 / 检查项 / 验收）全部落地，验收标准 1–5 满足。
- **遗留**：`00-decision-hub` 的 `G1-REGISTRY` 为已知 P2 观察项（决策层豁免），不阻断。
