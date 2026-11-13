# 管理助手 HOME 研发协作

当前任务是在维护 DSH HOME 的开发身份。根 AGENTS.md 是管理助手的运行身份，阅读它是为了理解和编辑资产，不代表开发工具变更身份。本文件供 Codex 原生研发上下文发现，DSH 继续读取 AGENTS.md。

本仓维护管理助手的 AGENTS.md、.agents/skills/、Preset、Profile 和相关方法资料；包括如何配置业务 MCP、开发 MCP 组合编排及配置 MCP 服务。平台程序与 MCP 框架属于 harness-engineering-platform；运行生成的配置、组合和研究记录属于 harness-engineering-platform-data；业务 Harness 及原生 MCP 配置属于 business-agents。Harness 资产使用文件，不存数据库。

保持原生 DSH 文件布局和装载机制。先找到方法的唯一来源，再修改技能及其直接引用；包内资源自包含，跨包通过公开入口交接。这里的运行技能不整体投影为跨仓研发技能。

根据变更检查实际 Profile/Skill 装载，并通过新建的管理会话验证受影响的理解、工具调用与效果。静态检查与真实模型结果分别说明。跨仓事项查阅父工作区 AGENTS.md（存在时）；按用户授权连续完成实现、验证和提交。
