# 平台管理助手 DSH Home

本仓库以文件保存平台管理助手的原生 Harness：原则、技能、研究方法和稳定 Profile。Harness 资产不写入数据库。初始化后的目录同时作为实际 DSH HOME；会话、附件、身份、反馈、工作区登记和生成配置保存在这里，运行状态由 Git 忽略；凭据可按任务需要随所属配置纳入 Git。用户明确排除的 DeepSeek API Key 保留在 Git 工作树之外，不提交或推送到 GitHub。

运行环境使用 Node.js 24.9+、Python 3.10+。从匹配程序仓运行 `platform/hep platform prepare`；入口统一加载环境，直接脚本使用五仓 `tools/with-env.sh` 或程序 `platform/tool-env.sh`，无需逐条 export 解释器和业务路径。Python 测试使用 pytest。`hep-lab` 将本目录登记为管理助手 HOME，独立安装默认使用数据根 `.local/platform-home`；同一工作区使用统一入口解析出的这一份 HOME。

| Profile | 来源与用途 |
|---|---|
| `harness-platform` | 原生 `dsh-base`、`dsh-web-app` 与平台插件组合，提供管理界面与原生对话 |
| `headless` | 原生 `dsh-base`、`dsh-headless`，用于无界面调用 |
| `studio-dev` | 原生基础组合，供开发扩展 |

原生 bundle 从匹配的 DSH 安装解析；平台插件及路径 Overlay 由 `prepare` 构建，生成文件不绑定源仓。用户自行创建的 `web`、`web-source` Profile 可共存，平台不依赖它们。

含数据的部署包保存现场配置和完整 HOME 状态；更新保留目标现场状态。会话、附件、反馈、身份及凭据需要随包备份和恢复，日志、缓存与依赖可重建。部署包含秘密，应作为私有运行制品保存。

当前 Profile 要求 DSH `0.2.2-rc.2`，版本以平台程序 `runtime/adapters/dsh-container/source.lock.json` 为准。

- [管理助手原则](AGENTS.md)
- [管理技能](.agents/skills/)
- [管理与研究方法](docs/README.md)
