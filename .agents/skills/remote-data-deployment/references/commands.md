# 远端更新命令

执行前阅读程序根 `docs/platform-design/23_离线一键打包与安装.md` 并核对当前 `platform/dsh-deploy --help`。下列变量必须来自本次只读核对，不能原样执行占位值；命令由普通管理会话已提供的原生 Bash 执行，不落成另一套部署脚本。

## 已安装仓库的增量更新

`hep_tool_root` 是受信任程序根；`hep_source_program_root` 是已准备的程序来源。仅更新数据时，后者的 HEAD 必须与目标程序提交一致，预检若仍包含程序变化则停止。`hep_source_data_root` 是待交付的数据仓库；`hep_remote_program_root`、`hep_remote_data_root` 是现场核实的远端绝对路径，`hep_ssh_target` 是授权的 SSH 目标。

先仅执行预检：

```bash
hep_update_args=(update
  --program-root "$hep_source_program_root"
  --data-root "$hep_source_data_root"
  --ssh "$hep_ssh_target"
  --prefix "$hep_remote_program_root"
  --remote-data-root "$hep_remote_data_root")
```

目标为最小数据安装时，先追加这一项；完整安装不追加：

```bash
hep_update_args+=(--minimal-data)
```

```bash
"$hep_tool_root/platform/dsh-deploy" "${hep_update_args[@]}" --dry-run
```

核对预检回执符合本次授权，且执行参数和来源未变化后再应用：

```bash
"$hep_tool_root/platform/dsh-deploy" "${hep_update_args[@]}"
```

不默认追加 `--install-deps` 或 `--start`；确有需要时按工具合同将选项加入同一参数组，重新预检再应用。不能省略远端目标参数后误用本地源码更新入口。整库更新不包含未提交文件；不要用 `--allow-dirty` 或不存在的 `--data-only` 试图改变该合同。

## 指定实例的业务 source 更新

在目标五仓工作区的业务仓保存当前 `business:<agent-id>` 文件，或使用 `platform/hep agent edit/read`、`edit/preview`、`edit/apply`；通过 `--input <JSON文件>` 传入 `source_id`、Agent 根下的相对路径和真实原文件摘要。需要编译的 Managed TypeScript 使用 `assets/build-preview`、`assets/build`，其 `experiment_id` 填业务 selector。保存后以 `platform/hep instance reload <实例名> --dry-run` 获取来源和运行代次摘要，再按同一命令的摘要参数重载，读回实际装载回执并验证行为。固定 `business:<agent-id>@<tag或commit>` 来源只读，新版本须选择新的来源创建或重新创建实例；跨主机完整资产交付使用平台 ZIP 全量更新。
