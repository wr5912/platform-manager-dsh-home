---
name: task-builder
description: 根据用户任务复用能力，在业务仓装配原生 DSH Harness，通过固定业务测试、必要修复和真实实例产物完成交付。
---

# 构建并交付任务型智能体

按“明确任务 → 定位业务资产 → 装配 → 初测 → 修复 → 交付”推进。沿用固定 task_context 与已有授权；不确定参数先 describe，已有 Job、Run 或实例先查状态，不重复创建。保持管理身份，模型自评、配置名称或容器运行不能代替业务结果。

## 1. 目标与执行路径

固定目标为 `business:<id>` 当前工作树或只读 Git tag/commit，reference_sources 只作复用来源，不改变写入目标。用 `business/detail`、`business/read` 核对实际文件、模型、工具与必要来源；需要发现其他业务能力时只读取相关 `business/list` 与 MCP 目录，不遍历全部历史。

新 Agent 按 `agent-maintenance` 通过原生文件工具在授权业务仓创建 harness.yaml、evaluation.md 与 dsh 原生资产，并同步 manifest.yaml；先执行该仓统一环境下的 check_agents，再通过现有平台工具构建和验证。已有 Harness 使用 edit/read、edit/preview、edit/apply；固定来源只读，不能直接修改。改变业务行为按 harness-evolution 核对原能力与比较依据，不强制创建版本副本或 Git 提交。

插件开发按需读取 dsh-business-plugin-development；MCP 接入按 mcp-composition。用真实输入、必须调用的工具、完整业务范围与可核对产物定义成功，不用身份测试代替业务任务或靠缩小范围通过。

## 2. 装配与用例

从真实来源读取完整内容，目标用 edit/read 取得摘要。以 `{experiment_id:"business:<id>",edits:[{path,content,expected_sha256}]}` 预览后应用；确认新文件不存在才用 null 摘要，引用和绑定同批更新。保留 Preset、Plugin、模型与工具选择，只有角色说明不算能力装配完成。截断正文、二进制元数据和缺失文件不能当作完整资产。

用 cases/list、cases/read 核对现有场景与必要回归；新增、修改、删除或改号遵循 evaluation-review 和 agent-maintenance。新 Agent 明确创建实际需求与 Case，不假定工具自动补身份或角色用例。仅将业务要求写入 evaluation.md，技术装载由项目检查与实例回执覆盖。

必要的依赖与 Managed 构建使用 assets/dependencies/prepare、assets/build-preview、assets/build；核对当前来源、制品与引用。成功后继续首个未完成阶段，不重复准备有效步骤。

用户给定修复次数、时间或资源限制时，预留失败修复、必要回归与交付验证；失败轮也计数，暂停恢复不重置额度。未指定时按实际结果和停止条件继续，不另设默认额度或把未观测消耗补零。

## 3. 初测与修复

1. eval/preview 核对目标与真实 Case，再沿同一 run_id 和输入 eval/start；mode/executor/review 使用约定值。需要报告时显式传 artifact_export，优先保留同一业务 Session 实际工具回执正文并核对摘要，不能要求模型重复伪造正式报告。
2. eval/status 有界查询，保存真实 job_id/run_id。检查约定 Case、真实工具、完整结果及实际产物；completed 不等于业务 passed。
3. 失败先读冻结输入、轨迹和原始错误，找共同根因；按当前摘要编辑业务资产，复测失败项与约定回归。保留失败 Run，不能改预期、删除失败项或扩大授权。
4. 恢复内容时核对固定来源、当前摘要和本次范围；并行变化先重读，不覆盖。结果未知先查状态，取消用 eval/cancel 并核对收尾。

## 4. 实例与独立交付

用 platform_instances 按约定来源创建、启动或重载实例，再读 detail、url 与 asset_status。需要重新执行业务验收时使用新 Session，并核对真实产物；只有启动或重载回执不能宣布业务通过。停止再启动使用同名实例，保留 HOME、会话、端口、模型与入口，不操作无关实例。

要求独立部署时，通过现有一键打包入口导出同一业务来源；平台和独立包统一交付 ZIP、校验文件与外部 install.sh。目标执行 `./install.sh --archive <安装包.zip>` 完成离线安装与启动，维护使用 standalone_agent_launcher；现场参数在 config/deployment.env，模型与MCP连接使用包内配置入口。包内提供运行依赖，所用模型和外部 MCP 仍须在目标网络可达，不把离线安装当作模型离线。

托管与独立共用 DSH 原生 MCP 机制，托管连接参数由平台动态提供，独立实例使用本地配置；组合执行器与 LFX 仍在平台，不内嵌到业务包。按[独立部署合同](https://github.com/wr5912/harness-engineering-platform/blob/main/docs/platform-design/23_离线一键打包与安装.md)核对真实入口、模型、工具调用、报告下载和重启后的配置/会话保持。

结束时按真实 Case、实例和产物回执报告已完成范围及限制，不用设备数或交付项数替代 Case 数。已有授权内继续修复与复测；Mock、未接入外部系统和未运行部分分别说明，不能升级为完整业务通过。
