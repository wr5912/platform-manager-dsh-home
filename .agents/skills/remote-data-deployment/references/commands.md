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

旧 Experiment/Candidate 更新入口已移除。业务实例更新必须使用程序仓库当前支持的 `business:<agent-id>@<commit>` source contract，通过平台 pack/update 合同生成并校验完整业务快照；本 Skill 不再构造 `experimentId`、Candidate 相对路径或旧 `agent-update` 清单。
