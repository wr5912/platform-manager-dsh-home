# 管理助手工作区

管理助手的 DSH home 是本仓库。`AGENTS.md`、`.agents/skills/`、`docs/`、原生 Profile 和业务知识均以文件维护，复用 DSH 的规则、Skill、Cordis 和会话机制。Harness 不写入数据库。

## 默认业务工作区

平台管理助手使用数据仓库的 `config/assistant-workspace.json` 固定业务范围：默认会话 cwd 是 `harness-engineering-platform-data`，已登记的 `business-agents` 是唯一额外业务目标。前者保存登记、Experiment、Run、Decision、历史证据和运行配置；后者保存需求、设计、验收定义和当前 Harness。两个仓库保持独立 Git 工作树，不复制或嵌套到新的父目录。

`harness-engineering-platform` 只作为平台工具与运行时实现来源，`platform-manager-dsh-home` 只作为管理身份、Skill 和 Profile 的装载来源；二者不登记为业务会话 cwd 或业务目标。该边界约束业务目标和默认工作区，不宣称操作系统级文件权限隔离；DSH 原生工具仍按其自身权限运行。

| 位置 | 内容 |
| --- | --- |
| 程序仓库 `platform/`、`runtime/` | 平台程序、MCP 框架、组合执行能力、Runtime 适配器 |
| 数据仓库 `agents/`、`evolution/` | 研究版本、Candidate、评测和历史 Run |
| 数据仓库 `config/`、`mcp/` | 平台登记的 MCP 服务、组合编排、来源和运行配置 |
| 业务仓库 `agents/<id>/` | 可复用 Harness；DSH 的 workspace、presets、managed 配置和业务 MCP 声明 |
| 本仓库 `.agents/skills/`、`docs/` | 管理助手身份、方法、业务 MCP 配置和组合开发能力 |

业务主线入口直接是 `agents/security-operations-expert/`。研究版本由数据工作区的 `candidate/harness.yaml` 声明装载资产；固定来源和历史 Run 保持各自身份。主线文件变更后，需要构建新版本并在新实例中核对实际装载及业务效果。

## 启动

在程序仓库运行：

```bash
export HARNESS_ASSET_ROOT="$HOME/hep-lab/harness-engineering-platform-data"
export HARNESS_MANAGER_DSH_HOME="$HOME/hep-lab/platform-manager-dsh-home"
./platform/dsh-platform prepare
./platform/dsh-platform start
```

未显式指定管理助手 HOME 时，平台依次读取匹配当前数据根的部署定位、同级 `platform-manager-dsh-home`，最后使用数据根下的 `.local/platform-home`。账号和模型密钥保存在数据仓库忽略的 `.local/credentials/`，不放入 Harness。

本仓库的 `profiles/` 保存 DSH 原生 Profile 声明；依赖由匹配的 DSH 安装与平台 prepare 提供。`node_modules`、构建缓存、原生会话、设置和授权等本地数据遵循 `.gitignore`。部署备份会同时保留管理助手 HOME 与数据状态，业务实例 HOME 独立保存。

## 方法入口

任务从 `.agents/skills/workspace-management/` 进入，按任务读取构建维护、评测改进、Harness 演进、MCP 组合、跨框架迁移或 KEV 技能。方法索引见 [研究方法](harness-research/README.md)。

配置业务 MCP 时修改对应业务 Harness 的原生 Cordis 配置；服务地址和凭据从当前部署解析。开发组合时使用 [MCP 组合方法](../.agents/skills/mcp-composition/SKILL.md)，业务实现说明见 [安全运营组合](mcp-security-operations.md)。平台登记及组合内容保存在数据仓库文件中。

模型、插件或 Profile 变更后，以 DSH 原生装载回执和真实会话确认生效。安装 DSH-Think-zh、Codex Connect 等插件时，把 `DSH_HOME` 指向本仓库，并使用 `harness-platform` Profile；授权文件只保存在忽略的本地目录。远端部署遵循已授权的目标与范围。

验收区分文件保存、实际装载、工具执行和业务结果。外部服务未配置或不可达时记录实际限制，历史记录、模型目录和 Skill 文件不能替代本次执行证据。
