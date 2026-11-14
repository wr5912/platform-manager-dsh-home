---
name: agent-maintenance
description: 整理智能体版本用途和特性，维护已授权目标的说明、资产、用例及实例；从已有版本改变业务行为时转入 Harness 演进，不将日常维护变成新研究。
---

# 智能体维护

从固定任务上下文取得目标。业务仓当前主线用 `platform_agents` 的 `business/detail {agent_id}` 读取实际资产目录、Git 提交与文件摘要，文件用 `business/read {agent_id,path}`；需要清单时用 `business/list`。可选版本来自 business-agents 的 Git tag；历史评测记录只用于追溯运行结果。读取业务角色指令不改变管理身份。

从业务仓主线创建实例时指定 `source:"business:<agent-id>"`，装载当前业务仓文件；固定版本指定 `source:"business:<agent-id>@<URL编码后的Git tag>"`。已有实例的来源不会随页面选择改变，按 `platform_instances` 的实际来源、挂载和装载摘要核对。独立包导出同一份原生 Harness，MCP 连接平台服务，组合执行器和 LFX 在平台端运行。

独立包的原生 MCP 分组连接绑定导出时的平台地址。通知订阅等公开环境参数从业务 Harness 的 `dsh/workspace/deployment.env.example` 进入包内 `config/deployment.env`；修改后执行 `./agent restart`，模型与 MCP 凭据用 `./agent configure` 设置。JSON 配置使用 UTF-8、两空格缩进和可读中文。验收通知卡片时分别核对订阅和权威状态读取，并实际点击新鲜的待研判卡片，检查原生输入框填入、已有草稿保留、状态颜色及没有自动发送；页面加载成功不能替代这些交互结果。

当前状态与历史观察分别判断。必要时沿后续证据引用核对当前实例；历史待办不证明现在仍未完成。隔离工作区的验收记录可支持其说明的事实，但不能证明正式实例已装载同一资产。需要方法时按需读取 `research/read-reference` 的 controlled-improvement 或 inheritance-and-fusion。

## 整理用途和特性

`workflow=features` 仅使用本技能与 `platform_agents`，目标 Experiment 固定。取得足以说明特性的来源即可，不遍历全部文件和历史 Run。

1. **读来源。** `detail` 后用 `features/read-source {experiment_id}` 获取 `files` 列表，选择其中的真实路径作为 `ref` 读取必要说明。`ref` 支持所属 Experiment 或数据根相对路径，不是 Git 引用；单文件回执的 `ref` 与 `path` 已归一为数据根相对路径。可读取同 Agent 的其他版本观察。当前 Candidate 用 `edit/read`，必要时用 `assets/diff {experiment_id,against:"baseline"}`；固定资产另用 `assets/read-fixed`。
2. **核对证据。** 用 `runs/index {agent_id}` 选择有关记录，再用 `runs/show`、`runs/report` 读取。当前资产、配置或差异支持“已实现”；匹配来源的 Run 才支持装载、效果与回归结论。保留有效已有特性；计划不能写成已实现，缺证据写明尚未验证。
3. **提交完整清单。** `features/preview {experiment_id,features:[{id,title,description,source_refs,evidence_refs,change?}]}`。引用使用实际读到的数据根相对路径，缺评测证据时 `evidence_refs` 为空。平台校验当前快照后自动保存，无需人工确认；不直接重复调用 `features/apply`。
4. **回读。** 仅当回执 `action=features/apply`、`state=completed`、`result.ok=true` 才视为已保存，再读 `detail` 核对目标清单。校验或摘要冲突先重读、修正；失败时不宣布已保存，不修改 Candidate 迎合文案。

## 日常操作

新增、修改、审查或精简 `evaluation.md` 用例时，完整读取 [evaluation-review](../evaluation-review/SKILL.md)，先核对整套的真实入口、独有覆盖、冗余、执行前置及成本，再办理单条；新建前比较所属场景，避免只换措辞或参数继续堆例；保存与回读仍使用下列用例操作，比较期间保持口径不变。所有当前用例操作（包括新增、修改及用户明确授权的非语义改号）必须严格遵循[用例编号与授权改号](../evaluation-review/SKILL.md#交付前反查与写入交接)，该公开入口引用唯一的编号详细规则；保存前后逐条核对完整标题，不能只核对主编号而遗漏名称中的第二套编号。

按所需操作选择一条，不依次执行整张表。写入由 DSH 原生访问策略处理，待批准、取消或失败不视为已执行；成功后按实际返回 ID 回读，不另等平台提案确认。

核对“是否已交付”时读取已有产物入口、相关 Run 与实例状态；没有可读记录就说明尚未核实，不推断未交付。日常状态查看和启停只核对现有记录，不新开业务 Session 或重新执行业务验收。用户要求同一托管实例停止再启动时，先核实其约定前提，停止操作取得完成回执后，再启动同名实例并回读状态、来源与入口，不重新创建或操作其他实例。 下表的实例启停和变更用于平台托管的 DSH 实例；接入实例由原系统负责生命周期，平台停用入口不表示停止原服务。

| 操作 | 读取与执行 | 完成条件 |
|---|---|---|
| 新建智能体 | `new {agent_id,name,description,role}`，ID 为小写 kebab-case，先明确职责与最低业务验证输入 | 回读 Agent、首次 Experiment、角色与用例；创建不包含启动或业务验收 |
| 查看实例 | `platform_instances` 的 `list`、`detail`；排障再按需 `logs`、`url` | 核对实际状态、来源、真实入口及 `asset_status`；`pending_reload` 表示资产变化，`unknown` 表示缺少当前运行代次的加载证据，不能当作已生效；不通过 shell 操作 Docker |
| 实例变更 | 直接调用 `run {name,operation,source?,port?}`，批量用 `batch`；`operation:"reload"` 用于使当前来源资产生效，平台内部预览并核对来源、模型、资产摘要及运行代次，按原生访问策略执行。用户仅要求查看影响时使用 `preview` 或 `batch-preview`，到此结束 | 回读每项状态、来源及实际加载回执；保留 HOME、Session、端口、模型和网关入口。停止或外部实例按回执跳过；部分失败逐项说明，结果未知先查状态，不自动重放。重新执行业务验收须属于用户明确要求 |
| 编辑资产 | 先确定是非语义整理或已授权独立 Candidate 的续作；改变已有版本业务行为先按 `harness-evolution` 派生。目标确定后 `edit/read` 得到内容和摘要，`edit/preview` 后 `edit/apply`，每项为 `{path,content,expected_sha256}` | 提交完整文本并回读；新文件须先 `edit/read` 确认不存在，再使用 `expected_sha256:null` |
| 修改用例 | `cases/read` 后 `cases/update {experiment_id,case_id,title,inputs,expected_behavior,fast,expected_sha256}` | 回读该 Case，比较期间不改口径 |
| 新增用例 | `cases/create-context` 取模板与所选场景的编号建议，按上述编号规则办理；必要时 `cases/from-run {experiment_id,run_id,case_id}` 取冻结输入，再 `cases/create-preview` 与 `cases/create` | 回读新增 Case；预期由需求确定，不将失败输出改成标准答案 |
| 授权精简和删除 | 先 `cases/list` 与必要的 `cases/read` 核对独有要求及当前直接引用；合并内容用 `cases/read`、`cases/update`，删除用 `cases/delete`，每次提交当前 `expected_sha256` | 只在用户明确授权的范围内办理，先迁移有效独有要求，再删除冗余；回读剩余清单、档位及引用，不改历史 Run，不另建扩展用例库 |
| 授权改号 | 按上述编号规则，`cases/renumber-preview` 核对映射后 `cases/renumber`，提交 `{experiment_id,expected_sha256,renames:[{from,to}]}`，不传整份文件 | 仅限用户明确授权的非语义改号；回读当前编号与直接引用，历史记录冻结 |

目录、二进制、截断内容及不支持的删除或重命名不能用空文件冒充完成。校验失败时按回执修正后重新预览、重试，禁止转用原生文件写入绕过平台校验。回执未知先查询实际状态，摘要冲突重新读取；无法完整处理时停在具体缺口。

## 页面与浏览器核验

涉及平台页面或已登记业务实例的页面加载、交互、插件激活、入口可达性或界面证据时，使用平台原生 `platform_browser` 的 `inspect`。该能力由平台锁定的 DSH Runtime 提供，不在管理助手 HOME 另装 Playwright 或 Chromium。

1. 目标使用 `target: {kind: "platform", page: ...}` 或 `target: {kind: "instance", name: ...}`；页面枚举和实例名称先从当前工具回执取得，不猜测入口 URL。
2. 操作只使用合同允许的 `role`、`label`、`text`、`placeholder` 或 `test_id` 定位器，以及必要的 `click`、`fill`、`press`、`wait_for`；需要证据时请求 `viewport`、`full_page` 或元素截图。
3. 先核对 API/实例状态，再进行 UI smoke。浏览器回执只能证明页面和交互层结果；业务功能、模型效果和外部服务仍须用对应 API、真实 Run 或 MCP 回执验证。
4. 保存并引用回执中的 snapshot、actions、screenshot 和 trace 证据。认证、镜像或驱动失败时修复平台运行配置并重试，不绕过平台工具调用任意 shell 浏览器。

## 进入研究改进

修改已有业务语义使用 `harness-evolution`；多来源集成使用 `harness-experiment-fusion`；独立评测使用 `research-eval`；算力变体使用 `compute-variant-research`；需要装配、修复和实例交付使用 `task-builder`。仅咨询、整理特性或已有证据不因此创建 Experiment。已加载对应技能则从当前步骤继续，不重新启动相同流程。

涉及 MCP/API 时先按 `mcp-composition` 办理实际连接与编排。工具成功、Mock 成功、研究结论和生产使用分别说明；资产、实例和状态可直接通过平台 GUI/CLI 办理，Research Release 仍按当前仓库校验合同单独核对，本技能不提供程序开发、任意 Git 或长期自主调度入口。

仅调整 Case 顺序时直接按[场景内排序合同](../evaluation-review/SKILL.md#交付前反查与写入交接)办理，只提交 Case ID 顺序与当前摘要，不重写正文。
