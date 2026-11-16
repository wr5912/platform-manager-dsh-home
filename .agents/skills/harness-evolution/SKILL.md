---
name: harness-evolution
description: 改进业务仓中的 DSH Harness，核对当前或固定 Git 来源，保留已有能力，通过资产编辑、真实评测和实例装载验证变化。
---

# Harness 研究演进

沿用用户选定的业务 Agent、来源与授权。当前工作树用 `business:<id>`，固定版本用 `business:<id>@<URL编码后的Git tag或commit>`；固定版本只读。需要判断方法时读取 `research/read-reference {topic:"controlled-improvement"}` 或 inheritance-and-fusion；目录职责见[仓库演进不变量](references/repository-invariants.md)。

## 定位与修改

1. 用 `business/detail {source}` 读取真实资产路径、提交、dirty 状态与文件清单；读取目标文件用 `business/read` 或 `edit/read`。核对实际问题、不能回归的能力和可证伪假设，只读有关来源与 Run，不按编号或程序 HEAD 猜业务版本。
2. 在授权的当前工作树修改。固定来源作为比较和复用依据，不能向只读 tag 写入；需要从固定来源恢复内容时，完整读取该来源，再与当前目标逐文件核对。未提交修改可以继续使用，不强制提交或创建版本副本。新 Agent 按 `agent-maintenance` 在业务仓创建原生资产。
3. `edit/read {experiment_id:"business:<id>",path}` 取得正文与 SHA；`edit/preview`、`edit/apply` 使用同一目标及 `edits:[{path,content,expected_sha256}]`。新文件先确认不存在，摘要为 null；移动提供 move_to 与完整正文，删除使用 content:null 和原摘要。引用修改同批办理，冲突先重新读取。
4. 插件修改按需使用 `dsh-business-plugin-development`。必要时通过 `assets/dependencies/prepare`、`assets/build-preview`、`assets/build` 准备已有声明的依赖与 Managed 制品，再核对真实回执。不复制 Runtime HOME、Session 或缓存，不修改平台程序代替业务实现。

## 评测与结论

按 `research-eval` 选择实际 Case、比较环境与新 Run。业务 `evaluation.md` 是当前用例唯一来源，Run 冻结本次来源和输入；同次比较不改变口径，历史结果不改写。构建通过不表示实例已加载，按 `platform_instances` 的资产状态与重载回执核对，再验证新 Session 的实际行为。

需要保存本轮观察时按[观察与结论](references/decision-update.md)维护所属业务文档，引用实际 Run、反例、回归、限制与下一步；只查询时仅报告。结论可为 adopt、continue、reject 或 inconclusive，说明证据与适用范围，不把采纳意见写成实例切换或发布成功。
