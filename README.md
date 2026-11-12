# 平台管理助手 DSH Home

本仓库保存平台管理助手所需的稳定 DSH Profile 与原生目录结构。Session、日志、缓存、附件、凭据、依赖安装目录和平台运行 Overlay 按运行时生成，不进入 Git。

使用时将 `DSH_HOME` 指向本目录，并从匹配版本的程序仓库运行 `platform/dsh-platform prepare`。`prepare` 会按当前程序根和数据根生成被忽略的 `profiles/harness-platform/harness-platform.patch.yml`，因此仓库本身不绑定机器绝对路径。

当前 Profile 要求 DSH `0.2.2-rc.2`，版本以平台程序 `runtime/adapters/dsh-container/source.lock.json` 为准。
