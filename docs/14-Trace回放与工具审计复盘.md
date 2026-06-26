# Trace 回放与工具审计复盘

## 阶段定位

本阶段目标是把项目中已经存在的多类 trace 统一到一个审计视角下。

Trace 的价值不是“把日志存下来”，而是让 Agent 的行为可以被回答：

```text
做了什么？
调用了什么工具？
工具是否成功？
耗时多少？
token 和 cost 是多少？
输出是否变化？
是否出现工具选择或执行退化？
```

## 当前实现位置

核心文件：

```text
app/agent_trace_logger.py
app/agent_trace_analyzer.py
app/agent_trace_replayer.py
app/trace_replay.py
app/trace_feedback.py
app/task_trace_analyzer.py
app/sub_agent_plan_trace.py
app/sub_agent_execution_trace.py
app/sub_agent_plan_comparator.py
app/sub_agent_execution_comparator.py
```

相关 CLI：

```text
analyze-traces
replay-agent-trace
replay-trace
trace-feedback
compare-agent-traces
analyze-task
analyze-sub-agent-plans
compare-sub-agent-plans
analyze-sub-agent-executions
compare-sub-agent-executions
```

## Trace 类型

### 1. Agent Trace

Agent trace 记录一次 Agent Loop 的整体运行。

主要内容：

```text
created_at
user_message
final_output
steps
tool_traces
token_usage
cost_estimate
```

它回答的问题是：

- 用户问了什么？
- Agent 最终回答了什么？
- 调用了哪些工具？
- 工具成功还是失败？
- 总 token 和成本是多少？

对应实现：

```text
app/agent_trace_logger.py
app/agent_trace_analyzer.py
app/agent_trace_replayer.py
```

### 2. Task Trace

Task trace 来自 `DefenseTask` 多步骤工作流。

它关注的是任务级状态推进：

```text
retrieve_context
generate_question
wait_for_answer
evaluate_answer
rewrite_answer
generate_follow_up
wait_for_follow_up_answer
evaluate_follow_up_answer
summarize_training
```

它回答的问题是：

- 当前任务执行到哪一步？
- 哪些 step 成功、失败、等待人工输入？
- 每一步的输入输出是什么？
- 证据、工具调用、token/cost 是否被记录？

对应实现：

```text
app/task_trace_analyzer.py
```

### 3. Sub-Agent Plan Trace

Sub-Agent plan trace 记录“计划”，不代表真实执行。

主要内容：

```text
event_type: sub_agent_plan_created
plan
audit:
  sub_agent_name
  tool_name
  status
  max_steps
  expected_output_fields
```

它回答的问题是：

- 计划让哪个 Sub-Agent 调用哪个工具？
- 计划的输入输出边界是什么？
- 是否保存了执行前审计？

对应实现：

```text
app/sub_agent_plan_trace.py
app/sub_agent_plan_comparator.py
```

### 4. Sub-Agent Execution Trace

Sub-Agent execution trace 记录真实执行。

主要内容：

```text
event_type: sub_agent_tool_executed
execution
audit:
  sub_agent_name
  tool_name
  success
  duration_ms
  plan_id
```

它回答的问题是：

- 真实执行了什么？
- 是否成功？
- 耗时多少？
- 对应哪个 plan？
- 输出 schema 是否稳定？

对应实现：

```text
app/sub_agent_execution_trace.py
app/sub_agent_execution_comparator.py
```

## Replay 与 Audit 的区别

### Replay

Replay 是把已有 trace 重新解析成可读摘要。

当前 `app/trace_replay.py` 支持统一回放：

```text
agent
sub_agent_plan
sub_agent_execution
```

它会归一化为：

```text
source_type
source_path
record_index
event_type
status
success
tool_names
tool_call_count
failed_tool_call_count
duration_ms
```

Replay 的目标是“看懂发生了什么”。

### Audit

Audit 是基于 replay / comparison 的结果检查风险。

当前项目里审计关注：

- 空 trace
- 无工具调用
- 工具失败
- trace record 失败
- 工具选择变化
- success sequence 变化
- 输出 schema 变化
- error_type 变化
- duration regression

Audit 的目标是“判断是否存在退化或风险”。

## Agent Trace Replay

`app/agent_trace_replayer.py` 可以：

- 加载 JSONL trace
- 默认回放最新记录
- 指定 line number 回放
- 提取 tool sequence
- 提取 tool success sequence
- 对比 baseline 与 current
- 检测回归：
  - `tool_sequence_changed`
  - `tool_failures_introduced`
  - `tool_success_sequence_changed`
  - `final_output_became_empty`

这使 Agent trace 不只是运行记录，也可以作为 regression gate 的输入。

## Generic Trace Replay

`app/trace_replay.py` 把不同来源的 trace 归一化。

当前支持：

```text
agent
sub_agent_plan
sub_agent_execution
```

统一后可以生成 summary：

```text
record_count
failed_record_count
total_tool_call_count
total_failed_tool_call_count
total_duration_ms
by_source_type
by_tool
```

这一步把不同 trace 统一到一个审计模型里。

## Trace Feedback

`app/trace_feedback.py` 可以把 trace replay 问题转换为 feedback record。

触发标签包括：

```text
empty_trace
failed_trace_records
failed_tool_calls
no_tool_calls
```

这条链路的意义是：

```text
Trace 问题
-> Feedback record
-> Benchmark candidate
-> 后续人工复核
```

也就是把运行时问题沉淀成后续评估数据。

## 工具审计链路

当前项目里的工具审计可以概括为：

```text
Agent run
-> tool trace
-> trace replay
-> trace comparison
-> trace feedback
-> benchmark candidate
```

Sub-Agent 侧可以概括为：

```text
plan
-> plan trace
-> dry-run / execution
-> execution trace
-> plan comparison / execution comparison
```

## 当前边界

当前版本仍然是本地学习版：

- trace 文件是本地 JSONL。
- 没有接 Langfuse。
- 没有 Prometheus 指标。
- 没有服务端 trace 查询接口。
- 没有图形化 trace viewer。
- 没有跨用户、跨 workspace 的审计隔离。

这些放到服务化和服务器部署阶段继续学习。

## 学到的关键点

```text
Trace 是 Agent 工程化的事实来源。
Replay 解决可读性问题。
Comparison 解决回归检测问题。
Feedback 解决数据闭环问题。
Audit 解决风险识别问题。
```

## 简历表达

可以写成：

```text
建设本地 Agent trace 审计链路，支持 Agent trace 回放、工具序列对比、失败工具检测、token/cost 汇总、Sub-Agent plan/execution trace 归一化、执行回归对比和 trace feedback 数据闭环，用于提升多工具 Agent 的可观测性和可回归验证能力。
```

## 后续学习

下一阶段建议进入：

```text
Memory 污染治理复盘：
长期记忆写入、检索、注入、审计、裁剪和上下文压缩的风险边界。
```
