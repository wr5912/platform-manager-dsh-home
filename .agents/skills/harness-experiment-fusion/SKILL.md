---
name: harness-experiment-fusion
description: 核对同一业务智能体的多个固定 Git 来源，保留有效能力、处理内容和依赖冲突，在业务仓当前 Harness 集成并验证。
---

# 多来源 Harness 集成

沿用明确目标与授权。只要求策划时只读来源、能力和有关 Run，交付取舍与验证方法后结束。需要判断方法时读取 `research/read-reference {topic:"inheritance-and-fusion"}`，不为普通集成新建版本目录。

1. 用 `business/detail {source}` 读取用户选定的当前工作树或固定 Git tag/commit，使用 `business/read {source,path}` 核对必要全文。固定版本只读，不能用当前文件补证历史；未取得来源保持未知，不因一次读取失败断言来源不可恢复。
2. 按真实能力明确继承、舍弃和冲突处理理由。核对入口、Preset、Skill、插件、模型、工具选择、直接导入与运行依赖；保留目标已有独有变化。共同祖先未知时逐项明确取舍，不猜 Git 祖先，也不按目录相同推断等效。
3. 目标为授权的 `business:<id>` 当前工作树。用 `edit/read` 获取目标摘要，以完整正文通过 `edit/preview`、`edit/apply` 保存；源内容与目标摘要分别核对，移动和引用变更同批。二进制、截断正文或无法完整处理的文件不能用空内容冒充完成。并行修改发生冲突时重读，不覆盖他人修改。
4. 对真实 Managed 依赖和制品使用 `assets/dependencies/prepare`、`assets/build-preview`、`assets/build`，再通过 `platform_instances` 核对并重载明确目标。构建、当前装载和来源自身测试分别取证，不能互相替代。
5. 按 `research-eval` 执行各来源关键能力和共同场景，读取新的 Run、轨迹、产物与实际装载回执。失败、回归与未覆盖能力保留；仅有文件保存或容器运行不能宣布集成完成。
6. 用[观察与结论](../harness-evolution/references/decision-update.md)保存授权范围内的取舍与实际证据；不改写来源或历史 Run，不自动提交、推送或切换其他实例。

每步以当前返回的来源、ID 和摘要继续。未知写入先查询实际状态，不重复执行；用户取消停止依赖步骤。未核对的来源不作全称结论，资源优化或训练结果也不构成排除其他有效能力的依据。
