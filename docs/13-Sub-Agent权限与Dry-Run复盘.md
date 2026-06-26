# Sub-Agent 权限与 Dry-Run 复盘

## 阶段定位

本阶段目标是复盘本地学习版 Sub-Agent Harness。

这里的 Sub-Agent 不是另一个神秘模型，也不是独立部署的远程进程。当前项目里的 Sub-Agent 是：

```text
受限角色
+ 受限工具集合
+ 明确输入输出契约
+ 可审计执行计划
+ dry-run 预演
+ execution trace
```

它的核心价值不是“让模型更像多个人协作”，而是把复杂 Agent 的能力拆成可控、可检查、可回放的小执行单元。

## 当前实现位置

核心文件：

```text
app/sub_agent_specs.py
app/sub_agent_permissions.py
app/sub_agent_plan.py
app/sub_agent_dry_run.py
app/sub_agent_executor.py
app/sub_agent_plan_trace.py
app/sub_agent_execution_trace.py
app/sub_agent_plan_comparator.py
app/sub_agent_execution_comparator.py
```

相关 CLI：

```text
check-sub-agent-tool
plan-sub-agent-call
dry-run-sub-agent-call
execute-sub-agent-call
analyze-sub-agent-plans
compare-sub-agent-plans
analyze-sub-agent-executions
compare-sub-agent-executions
```

## Sub-Agent Spec

`app/sub_agent_specs.py` 中的 `SubAgentSpec` 定义了一个 Sub-Agent 的边界：

```text
name
role
description
allowed_tools
input_fields
output_fields
max_steps
```

当前已有 Sub-Agent：

```text
retrieval_agent              -> search_thesis
defense_question_agent       -> create_defense_questions
answer_evaluation_agent      -> evaluate_student_answer
follow_up_agent              -> generate_follow_up
training_record_agent        -> query_training_record
```

这一步的关键是：Sub-Agent 不是“想调用什么就调用什么”，而是先在 spec 中声明能力边界。

## 权限检查

`app/sub_agent_permissions.py` 提供：

```text
check_sub_agent_tool_permission()
can_sub_agent_use_tool()
validate_sub_agent_tool_call()
```

权限判断基于：

```text
tool_name in spec.allowed_tools
```

如果某个 Sub-Agent 调用未授权工具，会直接失败，不进入执行阶段。

这让权限问题在“计划阶段”暴露，而不是等工具已经执行后才发现越权。

## Plan First

`app/sub_agent_plan.py` 中的 `create_sub_agent_execution_plan()` 会先生成执行计划：

```text
plan_id
sub_agent_name
role
tool_name
tool_arguments
expected_output_fields
max_steps
status
```

创建计划时会检查：

- Sub-Agent 是否存在
- 工具是否在 allowed_tools 内
- 工具参数是否是 dict
- 是否缺少 spec 声明的 input_fields

这一步体现的是 Agent Harness 的一个基本原则：

```text
先计划，后执行。
```

计划可以被保存、检查、对比，也可以 dry-run。

## Dry-Run

`app/sub_agent_dry_run.py` 提供 `dry_run_sub_agent_tool_call()`。

dry-run 会做：

```text
权限检查
-> 生成执行计划
-> 可选写入 plan trace
-> 明确 will_execute=False
```

它不会真正调用工具。

dry-run 的价值：

- 在执行前检查权限边界。
- 在执行前检查参数结构。
- 给人工审批或调试留出空间。
- 让 CI 或本地测试可以验证计划生成逻辑，而不触发真实工具调用。

## Execution

`app/sub_agent_executor.py` 中的执行链路是：

```text
create plan
-> validate_sub_agent_tool_call
-> resolve_tool_execution_config
-> execute_tool_function_with_retry
-> timeout / retry / result limit
-> standard error result
-> optional execution trace
```

Sub-Agent 执行复用了 `app/tool_executor.py` 的工具治理能力：

- retry
- timeout
- result length limit
- standardized error result

这说明 Sub-Agent 没有绕开主 Agent Harness，而是建立在统一工具治理层之上。

## Plan Trace 与 Execution Trace

### Plan Trace

`app/sub_agent_plan_trace.py` 记录计划创建：

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

```text
计划了什么？
哪个 Sub-Agent 计划调用哪个工具？
有没有保存计划审计记录？
```

### Execution Trace

`app/sub_agent_execution_trace.py` 记录真实执行：

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

```text
执行了什么？
成功还是失败？
耗时多少？
对应哪个计划？
```

## Plan Comparator

`app/sub_agent_plan_comparator.py` 用来对比两组 plan trace。

它关注：

- 新增计划
- 删除计划
- tool arguments 变化
- output fields 变化
- max_steps 变化
- stable plan 数量

这适合检测“计划层退化”。

例如同一个任务，原来由 `retrieval_agent` 调用 `search_thesis`，后来变成调用别的工具，就应该被发现。

## Execution Comparator

`app/sub_agent_execution_comparator.py` 用来对比两组 execution trace。

它关注：

- 新增执行
- 删除执行
- success 翻转
- result JSON schema 变化
- error_type 变化
- duration regression

这适合检测“执行层退化”。

例如同一个 Sub-Agent 调用同一个工具，原来成功，后来失败；或者原来返回 JSON，后来返回非 JSON，都应该被发现。

## 与 MCP 的关系

当前项目没有真正接入 MCP 工具市场，但这套 Sub-Agent 设计已经对应了 MCP 之前必须学会的能力：

```text
工具发现
工具描述
工具权限
工具调用
工具 trace
工具审计
工具回归对比
```

后续接 MCP 时，区别主要是工具来源从本地函数变成外部服务，但治理原则不变。

## 当前边界

当前版本是本地学习版，边界如下：

- 没有真正多进程隔离。
- 没有远程 Sub-Agent 服务。
- 没有人工审批工作台。
- 没有 workspace 级权限隔离。
- 没有 MCP server 接入。

这些内容留到服务化、MCP 和部署阶段继续学习。

## 学到的关键点

```text
Sub-Agent 的重点不是“多一个 Agent”，而是把角色、工具、输入输出和执行边界显式化。
dry-run 是执行前的安全闸门。
plan trace 负责审计计划，execution trace 负责审计真实执行。
回归对比必须同时覆盖计划变化和执行变化。
```

## 简历表达

可以写成：

```text
设计本地学习版 Sub-Agent Harness，支持基于角色的工具权限控制、执行计划生成、dry-run 预演、计划 trace、执行 trace 以及计划/执行回归对比，用于验证多工具 Agent 的权限边界、执行稳定性和可审计性。
```

## 后续学习

下一阶段可以继续推进：

```text
1. Trace 回放与工具审计深化
2. Memory 污染治理复盘
3. MCP 工具协议对照学习
4. 服务化阶段的权限审批和 workspace 隔离
```
