---
name: compute-variant-research
description: 在相同业务任务下研究 Harness 的质量与资源变化，复用真实 Run、当前业务资产和已有 KEV 数据、训练与部署方法验证优化。
---

# Harness 资源优化研究

沿用明确的业务 Agent、来源、Run 和用户授权。只读策划或 plan_only 不进入编辑、训练、部署或评测；实施从当前首个未完成阶段继续，不重建已有作业。需要判断方法时读取 `research/read-reference {topic:"compute-variants"}`。

## 1. 定位事实与比较范围

用 `business/detail`、`cases/read` 和代表 Run 的 `runs/show`、`runs/report` 核对实际业务输出、模型、工具与结果；必要时读 `runs/trace` 或具体证据。来源使用 `business:<id>`，固定 tag/commit 只读；不同来源各自核对真实内容，不从目录或程序 HEAD 补历史事实。

先判断重复查询、长上下文、子任务、模型或外部等待的实际成本；调用次数多不证明浪费。没有 Run 可给补采计划，不能伪造优化诊断。资源总量应包含可见子 Session、重试和外部调用，未采集值保持未知；Token 不等于硬件算力或费用。

记录本次假设、必须保持的能力、真实 Case、两侧来源、独立运行次数和允许的质量/资源变化。默认保留业务模型与推理档位，只有用户明确选择才改变；管理助手模型不代替业务模型。

## 2. 修改与装载

在授权的业务仓当前工作树修改实际 Harness。按 `harness-evolution` 使用 `edit/read`、`edit/preview`、`edit/apply`，移动通过 edits[].move_to，删除通过 content:null 并提交原摘要；同批更新直接引用，不复制版本目录或整个 Runtime HOME。

确定步骤与参数绑定优先交代码，模型只承担必要语义判断；保留纠错、关键复核和异常。插件开发按 `dsh-business-plugin-development`，用现有公开 SDK 和真实工具合同。装载入口与新增实现集中在所属业务目录，运行数据、日志和模型工件按各自用途保存，不能把监督答案作为业务可读上下文。

依赖和编译通过 `assets/dependencies/prepare`、`assets/build-preview`、`assets/build`，参数使用同一 business 选择器与当前回执。核对实际制品、Preset/Plugin/MCP引用，再通过 `platform_instances` 重载约定实例，验证新 Session。构建成功不表示已装载，不自动创建 Git 提交或 tag。

## 3. 按需处理 KEV 数据、训练与服务

只在任务需要且已授权时进入：
1. `decision-sample-extraction` 和 `kev-trace-pipeline` 基于真实 Run 识别决策前材料，抽取、标注、复核与转换；历史动作不是正确标签，不伪造人工复核。用户委托 AI 复核保留真实 Session、模型与 functional_validation 用途。
2. `kev-dataset-audit` 核对来源与标签，关联样本不跨 train/development/calibration/test；平台数据通过 `datasets/*` 当前工具读取和导出，离线数据保留实际来源。
3. `kev-training` 固定实际 checkpoint、输入构造器、代码与数据，核对执行环境与授权后 prepare、编码检查和执行真实命令卡。保留作业身份、日志、退出状态、模型工件与可恢复依赖；成功回执匹配则复用，不重复训练。
4. 开发集用于迭代，校准集用于拟合；固定模型、阈值、构造器和判据后执行独立测试。按 `kev-deploy` 核对服务与工具合同，将实际模型路由接入同一业务 Harness。
5. 训练脚本请求中沿用的 parent_experiment_id 字段填写实际业务来源身份，parent_ref 填已核对的业务 Git 提交；不能凭空补 Run、固定来源或训练回执。训练材料、模型工件和恢复依赖保留实际文件与摘要，不宣称存在自动归档或冻结平台动作。

数据、编码、训练、服务与业务效果分别取证；缺少实际执行能力只暂停依赖该能力的阶段，不把计划或离线准确率当作业务等效。

## 4. 执行比较与结论

通过 `eval/preview`、`eval/start` 或 `eval/batch-start` 执行独立两侧 Run，按真实引用固定来源，双方保持任务、Case、模型和外部条件一致。使用新请求 ID 开始新一轮，恢复同一请求则保留原 ID，先查询原状态。

concurrency 与 parallel_cases 只用于明确独立的任务；共享资源写入、到期和未知副作用保持必要顺序。Run 内屏障不隔离其他 Run，不能以并行加速为由漏掉计划 Case。

用 `runs/compare {left,right}` 核对真实来源可比性、质量、资源与限制。关键任务退步、双方失败、重复不足、环境变化或成本未知不能宣布等效；保留失败和反例，不修改预期让结果通过。结论限定本次任务与证据，不自动发布、切换其他实例或推送 Git。
