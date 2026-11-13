# 平台管理助手 DSH Home

本仓库以文件保存平台管理助手的原生 Harness：原则、技能、研究方法和稳定 Profile。Harness 资产不写入数据库。初始化后的目录同时作为实际 DSH HOME；会话、附件、身份、凭据、反馈、工作区登记和生成配置保存在这里，并由 Git 忽略。

从匹配版本的程序仓库运行 `platform/dsh-platform prepare`。`hep-lab` 将本目录登记为管理助手 HOME；可用 `HARNESS_MANAGER_DSH_HOME` 显式选择。独立安装默认使用数据根的 `.local/platform-home`。同一工作区只使用解析出的这一份 HOME。

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
