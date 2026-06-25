# Sub-Agent 阶段复盘

## 阶段定位

本阶段目标不是直接实现复杂多 Agent 协作，而是先完成本地学习版 Sub-Agent Harness 的基础治理链路。

当前项目已经具备：

```text
角色定义
工具权限
执行计划
dry-run
trace audit
replay / comparison
quality gate
CI artifact
```

这条线的核心价值是：在允许 Sub-Agent 执行工具之前，先把角色边界、工具边界、计划边界、执行边界和审计边界固定下来。

## 已完成能力

### 1. SubAgentSpec

位置：

```text
app/sub_agent_specs.py
```

完成内容：

- 定义 Sub-Agent 名称
- 定义角色说明
- 定义允许使用的工具
- 定义输入字段
- 定义输出字段
- 定义最大步骤数

意义：

```text
Sub-Agent 不能只是一个 prompt。
它必须有明确的角色边界、输入边界、输出边界和工具边界。
```

### 2. Permission Guard

位置：

```text
app/sub_agent_permissions.py
```

完成内容：

- 判断某个 Sub-Agent 是否允许调用某个工具
- 对非法工具调用抛出错误
- 提供 CLI 检查入口

意义：

```text
多 Agent 系统必须先有权限边界，再考虑自动调度。
否则工具能力越多，系统风险越高。
```

### 3. Execution Plan

位置：

```text
app/sub_agent_plan.py
```

完成内容：

- 生成 `SubAgentExecutionPlan`
- 固化 sub_agent、tool、arguments、expected_output_fields、max_steps
- 校验输入字段
- 支持 CLI 生成计划

意义：

```text
先有计划，再有执行。
执行计划是 trace、审计、回放、比较和人工复核的稳定载体。
```

### 4. Plan Trace / Audit

位置：

```text
app/sub_agent_plan_trace.py
```

完成内容：

- 将执行计划保存为 JSONL
- 读取计划 trace
- 按 Sub-Agent 和工具汇总计划 trace
- 支持 CLI 分析计划 trace

意义：

```text
计划本身也需要被审计。
系统不只要知道“执行了什么”，还要知道“执行前准备做什么”。
```

### 5. Dry-Run

位置：

```text
app/sub_agent_dry_run.py
```

完成内容：

- 生成计划
- 校验权限
- 可选保存计划 trace
- 不执行真实工具
- 支持 CLI dry-run

意义：

```text
dry-run 是真实执行前的安全演练。
它适合人工复核、权限审计和执行前回归检查。
```

### 6. Plan Comparison

位置：

```text
app/sub_agent_plan_comparator.py
```

完成内容：

- 对比 baseline / candidate 两份 plan trace
- 检测新增计划
- 检测删除计划
- 检测稳定字段变化
- 忽略每次都会变化的 `plan_id` 和 `created_at`

意义：

```text
计划稳定不等于结果正确，但计划不稳定通常意味着调度层发生了变化。
计划级 comparison 是执行前回归检测。
```

### 7. Single-Step Executor

位置：

```text
app/sub_agent_executor.py
```

完成内容：

- 执行单个 Sub-Agent 的单个工具调用
- 执行前复用 permission guard
- 执行前复用 execution plan
- 执行过程复用统一 tool executor
- 继承工具 timeout、retry、结果截断和错误标准化能力

意义：

```text
真正执行 Sub-Agent 时，不能绕过已有治理层。
执行链路必须经过 Spec -> Permission -> Plan -> Tool Executor -> Trace。
```

### 8. Execution Trace

位置：

```text
app/sub_agent_execution_trace.py
```

完成内容：

- 保存 Sub-Agent 执行结果 trace
- 读取执行 trace
- 汇总成功数、失败数、Sub-Agent 分布、工具分布

意义：

```text
执行结果需要独立审计。
计划 trace 说明准备做什么，execution trace 说明实际做了什么。
```

### 9. Execution Comparison

位置：

```text
app/sub_agent_execution_comparator.py
```

完成内容：

- 对比两份 execution trace
- 检测新增执行记录
- 检测删除执行记录
- 检测 success 翻转
- 检测 result JSON 结构变化
- 检测 error_type 变化
- 检测 duration 退化

意义：

```text
执行稳定性要从成功率、错误类型、输出结构和耗时四个维度评估。
```

### 10. Quality Gate

位置：

```text
app/local_quality_gate.py
```

完成内容：

- 本地质量门禁统一入口
- 默认支持 pytest
- 可选接入 Sub-Agent execution comparison
- 失败时返回非 0 退出码
- 支持 JSON 报告
- 支持 Markdown 报告

意义：

```text
评估报告只有影响退出码，才能成为质量门禁。
质量门禁只有输出 artifact，才方便排查失败原因。
```

### 11. Offline Fixture

位置：

```text
tests/fixtures/sub_agent_execution/
```

完成内容：

- `baseline.jsonl`
- `candidate.jsonl`

意义：

```text
CI 中不能依赖真实工具、在线 RAG 或 LLM。
稳定 fixture 是离线回归测试的基础。
```

### 12. CI Artifact

位置：

```text
.github/workflows/ci.yml
```

完成内容：

- CI 接入 `local-quality-gate`
- 使用离线 Sub-Agent execution fixture
- 输出 JSON 报告
- 输出 Markdown 报告
- 上传到 `offline-quality-reports` artifact

意义：

```text
CI 不只要给出 pass/fail，还要留下结构化证据。
JSON 给机器看，Markdown 给人看。
```

## 当前执行链路

当前 Sub-Agent 执行链路是：

```text
SubAgentSpec
-> Permission Guard
-> Execution Plan
-> Tool Executor
-> Execution Result
-> Execution Trace
-> Execution Comparison
-> Quality Gate
-> CI Artifact
```

这已经形成一个最小可审计 Sub-Agent Harness。

## 当前边界

当前明确不做：

- 不做复杂多 Agent 自动协作
- 不做并行 Sub-Agent
- 不做 Sub-Agent 间消息传递
- 不做自动任务拆解
- 不让 LLM 自主选择任意工具
- 不替换 `app/agent.py`
- 不替换 `app/task_*`
- 不接入服务器部署
- 不接入数据库
- 不接入在线评估默认 CI

当前只支持：

```text
单 Sub-Agent
单工具
单步执行
本地 trace
离线 fixture
本地/CI 质量门禁
```

这个边界是有意保留的。当前目标是学习 Agent Harness 的治理链路，不是追求复杂调度。

## 已学到的核心概念

### 角色边界

Sub-Agent 必须明确自己是谁、能做什么、不能做什么。

### 工具权限

工具能力不能默认开放，必须按角色白名单授权。

### 执行计划

执行前要把工具、参数、预期输出和最大步骤固化为计划对象。

### Dry-Run

真实执行前可以先演练计划和权限，避免直接产生副作用。

### Trace Audit

计划和执行都要记录。只记录最终答案不足以审计 Agent 行为。

### Replay / Comparison

同样输入下，计划和执行结果都应该可比较。比较结果用于发现调度退化、输出结构变化和性能退化。

### Quality Gate

质量门禁必须能影响退出码，并能输出报告供本地和 CI 使用。

### CI Artifact

自动化检查失败时，artifact 是排查依据。JSON 和 Markdown 应同时保留。

## 未完成能力

仍未完成：

- 多 Sub-Agent 调度
- 并行工具调用
- Sub-Agent 间消息协议
- 自动任务拆解
- 更复杂 planning
- 基于 Memory 的 Sub-Agent 调度
- LangGraph 旁路复刻 Sub-Agent 流程
- Trace replay 的完整反馈闭环
- 用户反馈自动进入 benchmark 候选

这些不应在当前阶段一次性推进。

## 下一阶段建议

建议下一阶段进入：

```text
Trace Replay / Feedback 闭环
```

理由：

1. 项目已经有 Agent trace、Task trace、Sub-Agent plan trace、Sub-Agent execution trace。
2. 项目已经有 benchmark、comparison、quality gate。
3. 下一步最自然的是让 trace 和用户反馈形成闭环，而不是继续堆更多工具。

建议顺序：

```text
1. 统一 trace replay 文档
2. 对比 Agent trace / Task trace / Sub-Agent trace 的差异
3. 将失败 trace 转成 feedback record
4. 将 feedback record 转成 benchmark candidate
5. 将 accepted candidate 转成正式 benchmark draft
6. 接入质量门禁
```

Memory 阶段可以放在 Trace Replay / Feedback 闭环之后。

原因：

```text
Memory 如果没有反馈闭环支撑，容易变成“把信息写进去”，但不知道哪些信息值得记。
先做反馈闭环，再做 Memory，工程上更稳。
```
