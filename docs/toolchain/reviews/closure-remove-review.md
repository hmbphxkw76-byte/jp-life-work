# 评审：closure-remove-unverified（22 条无法核验词条删除）

> 日期：2026-11-19
> 分支：`task/closure-remove-unverified-93955b6d`
> 范围：删除 01（11）/ 02（11）共 22 条 `npa.go.jp` 门户来源词条；新增 `vocab_tool remove` 命令。

## 一、背景与目标

22 条词条来源为 `https://www.npa.go.jp/`，该域名在本网络被 CloudFront 地域拦截（门户与深链均 403），无法核验。依据「信息质量准确、可靠」原则，无法核验来源的条目不保留为可用内容，执行删除。

## 二、Standards 轴

| 检查项 | 结论 | 证据 |
|---|---|---|
| 工具链规约（TOOLCHAIN-DEV-SPEC） | ✅ | 新增命令走 TDD（先失败后通过）；测试入 `engine/tests/test_tools.py`（3 项）；退出码 0/1 契约清晰；异常不静默 |
| 词库变更走工具 | ✅ | 全程 `vocab_tool remove`，未手改 `terms.md`；版本行留痕「删除 11 条：…」 |
| 单一事实源 / 阈值 | ✅ | 无新增硬编码阈值 |
| 测试覆盖 | ✅ | `TestVocabRemove` 3 项（删除存在 / 多删含未找到 / 全未找到返回 1）；`test_tools.py` 227 项全绿 |
| 静态检查 | ✅ | ruff / mypy 通过（合并前复测） |

## 三、Spec 轴

| 验收判据 | 结论 | 证据 |
|---|---|---|
| 22 条删除 | ✅ | 01: 109→98（v1.10）；02: 104→93（v1.10） |
| business-config 同步 | ✅ | `sync_vocab` 区块替换「删除 11」，各主题 |
| exports 重生成 | ✅ | csv / jsonl 重新导出（98 / 93 条） |
| 记录与证据包更新 | ✅ | 复核记录 §8A.2 状态改「已删除」+ 新增 §8A.5/§8A.6；证据包 01/02 D.2 更新 |
| 报告正文无损 | ✅ | 22 个 ID 在报告正文无引用（引用仅见于记录 / 证据包 / 评审） |
| 校验闭环 | ✅ | vocab verify 0E0W；link_check / structure_check / validate / audit_pipeline --gate --strict 通过 |

## 四、风险与遗留

- **内容缺口**：01/02 各减 11 条（驾照 / 交通类）。词条数仍 98 / 93，高于下限；后续如换网络环境可重新研究并 `import` 增量补回（保留删除前留痕）。
- **未绕过拦截**：未尝试任何反爬绕过，符合来源纪律。
- **缓存**：`findings-by-path.json` 已由 `ignore-iq-cache` 任务移出跟踪并忽略，不再产生噪声。

## 五、结论

P0/P1 = 0；Spec 满足。可合并。
