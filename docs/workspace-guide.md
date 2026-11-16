# 管理助手工作区

管理助手的 DSH home 是本仓库。`AGENTS.md`、`.agents/skills/`、`docs/`、原生 Profile 和业务知识均以文件维护，复用 DSH 的规则、Skill、Cordis 和会话机制。Harness 不写入数据库。

## 默认业务工作区

平台仅登记 `manager-workspace/` 一个原生工作区，普通新建管理会话的初始 cwd 使用该目录。其中 `harness-engineering-platform-data/` 与 `business-agents/` 是真实、独立的 Git 仓库。两个子仓仅作为业务目标，不另行注册工作区；删除其他工作区只撤销登记，保留会话和磁盘文件。数据仓保存来源登记、当前 Run、历史证据和运行配置；业务仓保存需求、设计、验收定义和当前 Harness。`config/assistant-workspace.json` 声明工作目录与业务范围，`config/repositories.json` 登记业务仓位置。

拉取 business-agents 时，真实业务网络地址属于 `172.16.x.x` 则优先使用 GitLab，其他环境优先使用 GitHub；首选源不可达再尝试另一端，仍按固定提交核对来源。传输地址不改变既有登记、研究记录或会话中的来源身份，也不以远端名称 `origin` 判断唯一来源。

`harness-engineering-platform` 只作为平台工具与运行时实现来源，`platform-manager-dsh-home` 只作为管理身份、Skill 和 Profile 的装载来源；二者不登记为业务会话 cwd 或业务目标。该边界约束业务目标和默认工作区，不宣称操作系统级文件权限隔离；DSH 原生工具仍按其自身权限运行。

| 位置 | 内容 |
| --- | --- |
| 程序仓库 `platform/`、`runtime/` | 平台程序、MCP 框架、组合执行能力、Runtime 适配器 |
| 数据仓库 `agents/`、`evolution/` | 来源登记、当前 evolution/runs 与历史记录 |
| 数据仓库 `config/`、`mcp/` | 平台登记的 MCP 服务、组合编排、来源和运行配置 |
| 业务仓库 `agents/<id>/` | 可复用 Harness；DSH 的 workspace、presets、managed 配置和业务 MCP 声明 |
| 本仓库 `.agents/skills/`、`docs/` | 管理助手身份、方法、业务 MCP 配置和组合开发能力 |

业务 Harness 入口为业务仓的 `agents/<id>/harness.yaml`。当前来源为 business:<id>，固定 Git tag/commit 使用 @ 引用且只读；未提交修改允许使用，dirty 只作提示。必要构建后，通过指定实例重载并核对实际装载及新 Session 的业务效果，历史 Run 保持自身冻结事实。

## 启动

在程序仓库运行：

```bash
./platform/hep platform prepare
./platform/hep platform start
```

未显式指定管理助手 HOME 时，平台依次读取匹配当前数据根的部署定位、工作区外侧的 `platform-manager-dsh-home`，最后使用数据根下的 `.local/platform-home`。账号和模型密钥保存在数据仓库忽略的 `.local/credentials/`，不放入 Harness。

本仓库的 `profiles/` 保存 DSH 原生 Profile 声明；依赖由匹配的 DSH 安装与平台 prepare 提供。`node_modules`、构建缓存、原生会话、设置和授权等本地数据遵循 `.gitignore`。部署备份会同时保留管理助手 HOME 与数据状态，业务实例 HOME 独立保存。

## 方法入口

任务从 `.agents/skills/workspace-management/` 进入，按任务读取构建维护、评测改进、Harness 演进、MCP 组合、跨框架迁移或 KEV 技能。方法索引见 [研究方法](harness-research/README.md)。

业务 Harness 保存原生 MCP 服务 ID、分组和工具选择；托管连接参数和凭据动态取平台当前登记，宿主回环服务通过统一 MCP 出口访问。独立实例从现场本地配置取参数，复用同一原生机制。分组 Token 自动生成，保存分组即可连接，不手工改托管 HOME 或将 IP 写死在 Harness。开发组合时使用 [MCP 组合方法](../.agents/skills/mcp-composition/SKILL.md)，业务实现说明见 [安全运营组合](mcp-security-operations.md)。平台登记及组合内容保存在数据仓库文件中。

原生执行工具需要调用公开脚本时，先通过五仓 tools/with-env.sh、业务仓同名入口或程序 platform/tool-env.sh 生效统一环境，不逐条 export 解释器和数据路径；Python 测试使用 pytest。模型、插件或 Profile 变更后，以 DSH 原生装载回执和真实会话确认生效。安装 DSH-Think-zh、Codex Connect 等插件时，把 `DSH_HOME` 指向本仓库，并使用 `harness-platform` Profile；授权文件只保存在忽略的本地目录。远端部署遵循已授权的目标与范围。

验收区分文件保存、实际装载、工具执行和业务结果。外部服务未配置或不可达时记录实际限制，历史记录、模型目录和 Skill 文件不能替代本次执行证据。
