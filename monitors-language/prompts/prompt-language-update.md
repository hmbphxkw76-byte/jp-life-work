# 02 日语学习 · 动态更新提示词

> **层级定位**：本文件 = [通用基座](../../prompts/通用基座/prompt-generic-base.md) × [知识库主题更新类型模板](../../prompts/知识库主题更新/prompt-knowledge-topic-update-template.md) × 本主题专属配置。冲突时本文件优先。

## 运行变量

```
{{TOPIC_DIR}}            = monitors-language（固定）
{{CURRENT_DATE}}         = 本次运行日期 YYYY-MM-DD
{{SOURCE_LANGUAGE_RULE}} = 考试制度类须日/英官方原文；学习方法类不限
```

## 一、主题定位与受众

JLPT N4→N2 分阶段备考 + JFT-Basic 备用方案的学习计划库。与 monitors-visa-immigration（考试制度）、monitors-career-driver（现场日语）联动：考试费用/日程数字以 01 主题追踪表为单一事实源，本主题不重复维护。

## 二、来源优先级实例化

① JLPT 官方（jees.or.jp/jlpt / jlpt.jp）、JFT-Basic（prometric-jp.com / jpf.go.jp）＞ ② 国際交流基金、日本語能力試験公式資料 ＞ ③ 出版社/教材官网（参考书版本信息）＞ ④ 学习门户与社区经验（标注为经验，不作事实）。

## 三、事件触发器表

```
- JLPT/JFT-Basic 报名日程或费用变更（monitors-visa-immigration 触发器联动） → 01/05
- JFT-Basic 考场在中国大陆开设/调整 → 01/05
- 新版教材/题库发布 → 05
- 个人进度里程碑（模考/实考完成） → 06
```

## 四、文档群更新要点

```
【00-index】更新：篇目状态与最近更新日期；保持：篇目结构
【01 总体学习路线与考试选择】动态获取：JLPT vs JFT-Basic 选择前提（费用/考场/频率，锚 monitors-visa-immigration 追踪表）；保持：路线框架
【02 N4 备考计划】更新：周计划完成状态；保持：语法/词汇清单
【03 N3 备考计划】同上
【04 N2 备考计划】同上
【05 资源与工具清单】动态获取：教材版本、App 可用性、官方样题入口 URL 有效性；保持：资源分类
【06 学习进度跟踪】更新：进度表、模考成绩、报考记录（个人数据，注明记录日期）
```

## 五、关键信息追踪表

| # | 信息项 | 优先数据源 | 上次值 | 本次是否更新 |
|---|---|---|---|---|
| 1 | JLPT 下一次考试报名窗口 | jees.or.jp / 各领馆文化中心 | 待基线确立 | ☐ |
| 2 | JFT-Basic 考场次与考位 | prometric-jp.com/ssw | 待基线确立 | ☐ |
| 3 | 当前学习进度（N4/N3/N2） | 自记录（06 文档） | 待基线确立 | ☐ |
| 4 | 主用教材版本 | 出版社页面 | 待基线确立 | ☐ |

## 六、已修正事实清单

```
【考试费用/日程类修正统一记入 monitors-visa-immigration 主题清单；本主题学习计划类修正追加于此：
- ❌（首期为空）】
```
