# report-audits/ 审计留痕治理说明

> **版本**：v1.1（2026-11-17 迁移后治理）
> **定位**：`engine/report-audits/` 存放审计台账与生成报告。本文件规定其**分层规则**与
> **生成器对照**，避免把生成物当活文档手工维护，也避免误删门禁依赖的台账。
>
> 上位依据：`engine/README.md` 第二节「文档分层」、`docs/审计报告标准化管理体系.md`。

---

## 一、三层分类

### 1. 活台账（人工 / CI 共同维护，删除即破坏门禁）

| 文件 | 写入者 | 用途 |
|---|---|---|
| `audit/audit-ledger.jsonl` | `audit_pipeline.py` | append-only 哈希链台账，门禁与完整性判定根数据 |
| `audit/audit-status.json` | `audit_pipeline` / `audit_badge` / `audit_registry` | 状态派生（多处消费） |
| `audit/report-registry.json` | `audit_registry` / `audit_pipeline` | 报告登记册（`--gate` 受检报告须 audited + 指纹匹配） |
| `audit/pending-p2.json` | `audit_check` / `audit_sampling` | P2 问题闭环台账 |
| `audit/pending-verification.json` | `pending_verification.py` | 待核实闭环（CI 月度刷新） |
| `audit/lint-whitelist.json` | `lint_reports` / `compliance_check` | lint 豁免清单 |
| `info-quality/info-quality.json` | `info_quality_check.py` | 信息质量三清单数据源 |
| `info-quality/rules-notes.md` | 人工 | 判定口径唯一事实源（活文档） |
| `info-quality/repair-history.md` | `info_quality_check.py`（追加式） | 跨运行累计修复日志（json 只含本轮，不可由 json 派生） |
| `toolchain/perf-trend.json` | `perf_snapshot.py`（scheduled-maintenance 月度追加） | 性能趋势快照（规模 + 耗时基线 / 历史，保留最近 36 条，供跨月对比） |
| `report-migration-2026-11.json` / `-paths.json` | `migrate_monthly_reports.py` / 测试夹具 | 迁移清单与路径映射（`test_tools.py::TestHistoricalMigration` 依赖） |

### 2. 生成物（工具渲染，json 为源，可删除重生成）

| 文件 | 写入者 | 数据源 |
|---|---|---|
| `audit/audit-check-report.md` | `audit_check.py` | `audit-check-report.json` |
| `audit/report-registry.md` | `audit_registry.py` | `report-registry.json` |
| `audit/fact-card-report.md` | `fact_card_check.py`（scheduled-maintenance 月度刷新） | 无 json 对应，md 即产物 |
| `info-quality/assessment-ledger.md` | `info_quality_check.py` | `info-quality.json` |
| `info-quality/verification-report.md` | `info_quality_check.py` | `info-quality.json` |
| `info-quality/findings-by-path.json` | `audit_check.py`（内容哈希缓存） | 运行缓存（建议 `.gitignore`） |

> 生成物**不做手工编辑**；正文漂移时删除后由工具重生成。

### 3. 历史归档 / 已清理（无引用即删）

- **一次性留痕**（已完成方案 / 结项验证 / 一次性清理记录）：`cleanup-2026-11-13.md`、`cleanup-2026-11-14.md`、`gap-analysis-2026-11.md`、`execution-plan-2026-11.md`、`audit/verification-report-2026-11.md`、`audit/implementation-status.json`——完成即清理。
- **已清理的生成物**（工具可重生成，**非**历史归档）：`compliance-audit.md`、`audit/preflight-report.md/.json`、`audit/sampling/sampling-2026-11.md/.json`、`info-quality/repair-ledger.md`、`report-migration-2026-11.md`——删除仅因快照过期，再次运行对应工具即重建。

---

## 二、新增 / 删除规则

1. **新增台账**：先确认无同职责既有文件；命名 `<domain>-<state>.json`，并在本文件登记。
2. **新增生成物**：必须由工具渲染，头部注明「自动生成 · 勿手工编辑」；同步在本文件登记数据源。
3. **删除**：先全仓 grep（含 `docs/`、`.github/workflows/`、`engine/tests/`）确认零引用；
   生成物另确认工具可重生成；台账类删除须经人工确认。
4. **运行日志**：`audit/verify/*.json` 为 `auto_verify.py` 运行日志，已 `.gitignore`，不入库。

## 三、CI 接线对照（提交范围）

- `html-sync.yml` / `audit-sampling.yml` / `scheduled-maintenance.yml` / `info-quality.yml`：`automation_status.py` 写**仓库根** `automation-status.json`，由各工作流 `git add` 根文件提交；本目录内 `audit/` 下的台账 / 报告由对应工作流一并 `git add engine/report-audits/audit/` 提交。
- `audit_sampling.py --apply` 产物写 `audit/sampling-<YYYY-MM>.md` + `.json`，已含在上述提交范围内。
- `engine/report-audits/pipeline/`（`status.md` / `state-<period>.json` / `trigger-watch.json`）为运行期生成目录，由 `pipeline-orchestrator.yml` 提交。
- `audit/verify/*.json` 为 `auto_verify.py` 运行日志，已 `.gitignore`，不入库。


## 四、版本记录

| 版本 | 日期 | 变更 | 说明 |
|---|---|---|---|
| v1.0 | 2026-11-17 | 初始版本 | 建立审计留痕分层（活台账 / 生成物 / 历史归档）、生成器对照与新增/删除规则 |
| v1.1 | 2026-11-17 | 迁移后治理 | 第三节改为「CI 接线对照」，移除已失效的「范围外接线问题」描述 |
