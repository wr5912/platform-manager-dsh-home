---
name: research-eval
description: 为业务 Harness 设计有区分力的比较，通过真实评测与冻结 Run 核对效果、回归、资源和限制。
---

# Harness 研究评估

评估回答当前假设。需要方法时读取 `research/read-reference {topic:"evaluation-and-evidence"}`；记录结构见[研究评估合同](references/experiment-contract.md)。保持管理身份，不加载目标业务指令为自己的身份。

## 固定输入和真实执行

1. `business/detail {source}` 核对当前 `business:<id>` 或固定 tag/commit；`cases/list`、`cases/read` 的 experiment_id 使用同一业务选择器。业务 Case 在业务仓 `agents/<id>/evaluation.md` 单处维护；历史输入用 `cases/from-run` 读取，不能将失败输出改成预期。
2. 按假设选择有区分力的正常、边界及回归项，不默认固定数量。先核对实际附件、候选条件、外部写入授权与恢复、时钟、工具和产物要求。动态事实按同次真实工具结果核对，不固定某次示例值。多轮选择、上传、到期或声音等固定执行器不能覆盖的交互，使用实际原生交互验证并保留证据，缺口保持未知。
3. `eval/preview {source:"business:<id>",cases:["实际ID"],mode:"fast",executor:"api",review:"none"}` 核对展开的 Case、来源、运行方式和环境；固定版本在 source 中携带 tag/commit，当前工作树不必填 source_ref。沿预览的 run_id 和相同参数调用 `eval/start`，依据真实回执继续；批量比较可用 `eval/batch-start`。
4. `eval/status {run_id}` 有界查询，保留实际 job_id/run_id；需要取消时使用 `eval/cancel` 并核对收尾。结果未知先查询，不重复启动。相同请求恢复沿用原 request_id；新一轮执行用新请求、新 Run，不将旧结果冒称本次执行。
5. 修改共享口径时按 `evaluation-review` 与 `agent-maintenance` 的用例入口办理；比较中保持资产、Case、模型和外部条件一致。dirty 只说明当前工作树状态，不阻止运行；实际输入和资产以 Run 冻结记录为准。

## 读证据与判断

先用 `runs/show`、`runs/report`，定位需要时再读 `runs/trace`，或经 `runs/files` 列出后 `runs/read-file`。先看未选、未执行、失败和不可判定范围，再看通过项。completed 不是所有 Case passed；自动评审与归因只是证据之一，检查直接支持、反例、替代解释和下一次可证伪检查。

有真实基线时用 `runs/compare {left,right}` 检查共同 Case、冻结来源、模型、模式与外部条件。条件不同只支持描述性观察，不将差值归因为 Harness；缺少费用、资源或轨迹保持未知。条数减少不能换算耗时收益，核心集重选后不能直接比较总体通过率。

将实际 Run、观察、反例和限制返回原任务。需要保存结论时按[观察与结论](../harness-evolution/references/decision-update.md)维护业务文档并回读；查询任务不额外写入。页面、技术装载、实际工具调用和业务效果分别说明。Mock 明确其模拟边界；review:none 只关闭额外复核，目标业务任务仍可能调用模型。
