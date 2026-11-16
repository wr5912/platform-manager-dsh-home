# 业务资产与研究记录

当前业务执行以所属 Skill 与平台公开合同为准。业务资产、运行配置和冻结事实分别维护，不要求普通编辑先创建研究版本或提交 Git。

## 身份与目录

- Agent ID、Skill 名及普通目录使用小写 kebab-case。
- 业务仓 agents/<id>/harness.yaml 声明唯一当前 Harness，evaluation.md 维护 Case；dsh/workspace、dsh/presets、dsh/managed 保存原生运行资产。
- 当前来源为 business:<id>，固定 Git tag/commit 使用 @ 引用且只读；已保存 dirty 工作树可以使用，实际内容由 Run 与实例回执记录，不能冒称已固定提交。
- 数据仓保存来源登记、运行配置与 evolution/runs/run-<UUIDv4>/，不另建当前 Candidate、versions 或重复 Baseline 树。
- 新 Agent 用原生文件工具在授权业务仓创建完整资产，登记 manifest.yaml；存在 release-manifest.yaml 时同步 active_agent_ids。已有 Harness 通过当前编辑、构建、评测和实例合同维护。
- 程序源码、Runtime、管理 HOME、会话和缓存不复制为业务资产。仅创建本次确有内容的文件，空报告不证明完成。

## Run 与结论

Run 以自身 run.yaml/run.json、inputs.lock.json、结果和真实证据记录来源、用例、模型、环境、执行与判断。历史缺失事实保持未知，不从当前 Harness 或目录反推历史来源。重新执行使用新 Run，封存后不覆盖原记录。

每条结果保留 run_id、trial_id、input_id、execution_status、verdict、observation 与 evidence_ref。execution_status 表示执行完成情况，verdict 表示证据判断；error/skipped 对应 inconclusive，错误需说明实际原因。Run 锁定的全部 Case 完成才可封存为 completed，completed 不等于业务 passed。

需要保存观察时维护所属业务文档，引用实际 Run、反例、回归与限制；adopt、continue、reject、inconclusive 是结论，不代表 Git 合并、实例切换或发布。未知资源不补零，不设固定 Case 数或生产门槛。

## Research Release 历史资产合同

以下保留历史资产的读取与复现约定。当前平台没有 Research Release 创建、发布及 `release:<id>` 运行入口，不能将这些字段视为已可执行的管理动作。

Release 根目录至少包含 `manifest.yaml`、`harness.yaml`、`runtime.yaml`、`artifact-manifest.json` 和 `README.md`。`manifest.yaml` 使用以下字段：

- `schema_version`
- `release_id`
- `agent_id`
- `version`
- `source_experiment`
- `source_commit`
- `evaluation_ref`
- `runtime_compatibility`
- `artifact_digest`

Release 必须自包含实际 Harness 资产，逐文件清单与摘要可复算；不得包含 Session、缓存、附件、LLM API Key 或整个 `$DSH_HOME`。平台和实例凭据保存在 Agent 的实例专用路径，不打包为 Harness Release。README 应说明用途、复现方法、限制以及“不是生产部署批准”。

`artifact-manifest.json` 使用 `schema_version`、`tree_sha256` 和按路径排序的 `files`；每项记录 `path`、`sha256`、`size`。为避免摘要自引用，文件列表只排除根部 `manifest.yaml` 与 `artifact-manifest.json`；`manifest.yaml.artifact_digest` 等于 `sha256:<tree_sha256>`。

## 四项安全底线

- 平台和实例凭据可按任务需要纳入 Git；LLM API Key 只能保存在匹配 `*.llm-api-key` 的本地忽略文件中，禁止提交或推送到远端。
- 不自动执行不可信归档或其中的脚本、Hook、Plugin、Skill、Workflow、配置。
- 不进行未经用户授权的提交、推送、打 Tag、删除、覆盖、发布或外部写入。
- 如实记录结果、失败、未知状态和适用限制。

具体 Harness 的安全约束可以作为研究变量，但不自动变成全仓库的控制平台。
