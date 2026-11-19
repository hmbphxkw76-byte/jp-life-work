# 组 B 内容核验 · 收尾评审（closure-b，2026-11-19）

> **范围**：`task/closure-b-93955b6d` worktree（`D:\文档\GitHub\jp-life-work\.worktrees\closure-b`）内「组 B：内容核验」收尾的独立评审。
> **工单**：`n2-portal-url-mismatch` / `n7-vocab-verification-deepen` / `n9-fact-card-references` / `n10-finance-model-refresh` / `n15-vocab-alias-cleanup` / `n17-report-second-issue`（组 B，2026-11-19 补全 slug 留痕，见 `docs/toolchain/specs/align-2026-11-19.md`）
> **基线**：前序子代理留下的 31 处未提交改动 + 本轮收尾新增（14 词库 2 条、复核记录 / 证据包 / 14 证据包）。
> **口径**：只审本任务范围；来源分级、事实 / 推断分离、无法核实须说明，不编造。
> **结论**：**P0 = 0 / P1 = 0**；残留为 P2 与环境限制项，见 §六。

---

## 一、评审对象与改动清单

### 1.1 已有改动（前序子代理，31 处）

| 类别 | 文件 | 性质 |
|---|---|---|
| 事实卡片 | `00-decision-hub/data/fact_cards.md` | FC-016 值 / 日期更新 + v2 版本行 |
| 事实卡片 | `00-decision-hub/data/personal_finance_model.md` | 中介费「待核实（经确认无官方统一口径）」标注 |
| 决策报告 | `00-decision-hub/reports/2026-11-decision-hub.md` | 补 `[@FC-008/009/011/014/015/016]` 引用 |
| 提示词同步 | `17/18/19-*/prompts/business-config.md` | 词库同步版本 / 别名（N15 结果回写） |
| 周期文档 | `docs/报告周期体系.md` | 新增 §七 第二期触发机制（N17） |
| 词库 | `engine/vocabulary/data/{01,02,04,08,12,13,14,17,18,19}-*/terms.md` | N2 / N7 / N15 回写 |
| 词库 | `engine/vocabulary/data/sync-state.json` | 同步版本 / 哈希 |
| 工具 | `engine/vocabulary/script/vocab_tool.py` | 新增 `alias` 子命令（N15 用） |
| 审计 | `engine/report-audits/info-quality/findings-by-path.json` | key 刷新（findings 为空） |
| 新增文档 | `docs/登记册待核实项复核记录-2026-11-19.md`、`docs/门户URL核验深化方案-2026-11-19.md`、`docs/核验证据包-2026-11-19/`（20 份）、8 份 `imports/*.md` | N2 / N7 留痕 |

### 1.2 本轮收尾新增

| 文件 | 性质 |
|---|---|
| `engine/vocabulary/data/14-life-operations/terms.md`（v1.10 / v1.11） | LOP-044 / LOP-073 纠错升级（住宅局页 → 水道局页） |
| `engine/vocabulary/data/14-life-operations/imports/2026-11-19_核验深化抽样.md` | 上述 2 条留痕 |
| `docs/核验证据包-2026-11-19/14-life-operations.md` | D.2 抽样纠错 + E 自检补充 |
| `docs/登记册待核实项复核记录-2026-11-19.md` | §7A.4–7A.6（N7 分类统计 / 抽样 / 保留策略）、§8.6（N2 抽样复测） |

---

## 二、改动审查（破坏性 / 虚构来源）

- **无破坏性改动**：全部为追加 / 回填，无删除词条、无改主体定义、无改置信度标签（N2 部分）与仅限 N7 抽样升级。
- **无虚构来源**：N2 / N7 新增 URL 均为官方域名（`.go.jp` / `gov.cn` / 官方机构），并经本轮抽样 `web_fetch` 复核（见 §三、§四）。
- **事实卡片复核**：FC-016「100 日元中间价 4.1982 元（2026-11-17）」——`chinamoney.com.cn` 首页实取显示 2026-11-19 为 **4.1995**，与 11-17 值差 0.0013，属正常日间波动，**来源与量级一致**；卡片已标日期，旧值冻结存档，合规。
- **工具改动**：`vocab_tool.py` 新增 `alias` 子命令，逻辑与既有 `tag` 同构（读 → 改 → 写 → 版本追加 → 自动同步），`verify` 0E0W。

---

## 三、N2 门户 URL 错配专项（结论：闭环，无 P0/P1）

对 §8.5 六项逐条复核，并独立抽样复测（详见复核记录 §8.6）：

| 项 | 处置 | 复测 |
|---|---|---|
| 13-regional-info 18+2 | 升级 8 / 回落门户 12 | ✅ 8 条升级 URL 全部实取成功且切題 |
| 14 `LOP-034/077` | 回落総務省门户 | ✅ 原 URL 不切題，回落理由成立 |
| 12 格式瑕疵 35 条 | 去「，2026。」 | ✅ 残留 = 0；抽样 3 条实取成功 |
| 04 非门户错配 14 条 | 回落物流政策页 | ✅ 实取成功 |
| 01 / 02 非门户错配 | 回落警察庁门户 | ✅ `npa.go.jp` 403 CloudFront 拦截，标未核实属实 |
| 18 `FAM-018/019` | 纠错至文科省幼児教育页 | 🟡 URL 真实切題（检索快照确认），`web_fetch` 取不到正文，维持未核实 |
| 19 / 20 外務省 CDN | 保留门户 | ✅ `mofa.go.jp` Access Denied（Akamai）属实 |

**结论**：处置无虚构；唯一未核实项系抓取环境限制，非内容问题。

---

## 四、N7 核验闭环深化（结论：策略 + 抽样交付，不凑数）

- **① 统计**：主题分布（20 主题，见复核记录 §7A.1）+ 分类分布（110 类，§7A.4）。全库 **已核验 117 / 部分核验 1423 / 待核实 94**（合计 1634）。
- **② 抽样**：08-visa-immigration 15 条（前序）+ 14-life-operations 2 条（本轮，LOP-044/073 纠错升级）。方法 = 方案 C（仅落地已实取官方页）。
- **③ 保留 + 理由**：按 7 个分类簇给统一保留口径（§7A.6），记录于复核记录，不手改 `terms.md`；「部分核验」本身即诚实状态。
- **纪律**：同批复测 LOP-035 原 URL 切題，**主动回退**，避免无据 churn。

---

## 五、N9 / N15 / N17 结论

| 工单 | 结论 | 证据 |
|---|---|---|
| **N9** fact_card | ✅ 闭环 | `fact_card_check`：16 卡片 / 16 指针，P0/P1/P2 = 0；`[@FC-008/009/011/014/015/016]` 均在 00 报告中被引用 |
| **N15** 别名冗余 | ✅ 闭环 | `vocab_tool verify` 0 错误 / 0 警告；`alias` 子命令留痕，5 条冗余别名（MPC-071、FAM-073/074、SFD-049/071）已清 |
| **N17** 第二期触发 | ✅ 闭环 | `docs/报告周期体系.md` §七：触发条件（时间 / 数据 / 事件 / 人工）+ 当前 0 触发原因（全库仅 2026-11 一期）+ 验证口径；所引工具 `report_cycles.py` / `trigger_watch.py` / `report_diff.py` / `scheduled-report-tasks.yml` 均实测存在 |

---

## 六、回归校验（实测退出码）

| 校验 | 结果 | 退出码 |
|---|---|---|
| `python engine/vocabulary/script/vocab_tool.py verify` | 20 主题：0 错误 / 0 警告 | **0** |
| `python engine/tools/fact_card_check.py` | 16/16，P0/P1/P2 = 0 | **0** |
| `python engine/tools/personal_finance_model.py --check` | 与重算一致 | **0** |
| `python -m unittest discover -s engine/tests -q` | 978 tests，OK（skipped=4） | **0** |
| `python engine/tools/validate.py` | 结构与规范校验通过 | **0** |
| `python engine/tools/md_html_parity.py` | 21 份：OK=20 / MISMATCH=1 | 1（见下） |

> **HTML 一致性说明**：`00-decision-hub/reports/2026-11-decision-hub.md` 因 N9 补 `[@FC-016]` 引用而变更，同名 `.html` 未同步（`md_html_parity` MISMATCH）。按本任务「不重生成 HTML」约束，**未运行 `md2html.py`**；如需闭环可执行 `python engine/tools/md2html.py --changed`（仅转换 git diff 变更的报告，即该 1 份）。

---

## 七、未核实 / 保留清单（不编造）

- **未核实（CDN / 地域拦截）**：01 `SSW-036/037/043/054/057/068/086/092/093/094/095`；02 `CDR-008/024/025/026/027/028/033/082/083/085`；19 `SFD-015/016/018/066/069`；20 `OVC-035/036/069`（`npa.go.jp` / `mofa.go.jp`）。
- **未核实（抓取限制，URL 真实）**：18 `FAM-018` / `FAM-019`（文科省幼児教育页）。
- **保留**：18 `FAM-034`；14 `LOP-033/036/039/041`；13 回落门户 12 条；其余约 1421 条「部分核验」按 §7A.6 分类簇保留。
- **环境限制**：`npa.go.jp` / `mofa.go.jp` 在本网络环境被 CDN 拦截，深链无法实取；已在证据包标注，未补值。

---

## 八、发现（Findings）

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| 1 | P2 | 14 词库版本记录出现 v1.10（3 条）/ v1.11（1 条）两次连续回填，净效果 2 条；系收尾「先改后回退 LOP-035」所致 | 已记录；不影响数据正确性，后续可合并批次减少噪音 |
| 2 | P2 | `npa.go.jp` / `mofa.go.jp` 深链受 CDN 地域限制，长期无法实取 | 保留门户 + 标未核实；如需闭环需换网络环境或人工核验 |
| 3 | 观察 | 14 `LOP-035` 原 URL 为「廃家電や粗大ごみ Q&A」，切題但主题偏廃家電 | 不改；如后续追求更纯粹的一般廃棄物页，可评估 `env.go.jp/recycle/waste/index.html` |
| 4 | P2 | N9 补 `[@FC-016]` 后 00 报告 `.md` 与 `.html` 不一致（parity MISMATCH=1） | 按任务约束未重生成 HTML；建议后续 `md2html.py --changed` 同步 1 份 |

**P0 / P1 = 0。**

---

## 九、版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-19 | 初始评审：组 B 内容核验收尾，N2 / N7 / N9 / N15 / N17 结论与证据，回归退出码，未核实清单 |
