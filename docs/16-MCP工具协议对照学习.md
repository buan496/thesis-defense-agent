# MCP 工具协议对照学习

## 阶段定位

本阶段目标不是接入真实 MCP Server，而是把当前项目已有的本地 Tool / Sub-Agent / Trace 能力映射到 MCP 的工具协议思维。

当前项目已经具备本地 Agent Harness：

```text
Tool Schema
Tool Registry
Tool Metadata
Tool Executor
Permission
Retry / Timeout / Result Limit
Trace / Audit
Sub-Agent Plan / Dry-Run / Execution
```

MCP 的价值是把这些能力从“本地 Python 函数”扩展到“外部标准化工具服务”。因此，先做概念对照，比直接启动一个 MCP Server 更重要。

## 当前不做的事情

本阶段明确不做：

```text
不启动 MCP Server
不接外部 MCP 工具市场
不做远程工具调用
不做 OAuth / 用户授权
不做企业级 Workspace 隔离
不做服务器部署
```

这些内容后移到服务器笔记本和服务化阶段。

## MCP 核心概念映射

| MCP 概念 | 当前项目对应物 | 当前实现位置 |
| --- | --- | --- |
| Host | CLI / Agent / Task Service | `app/cli.py`, `app/agent.py`, `app/task_service.py` |
| Client | 工具执行分发层 | `app/tool_executor.py` |
| Server | 暂无，未来外部工具服务 | 后续服务器阶段 |
| Tool | 本地工具函数 | `app/tools/` |
| Tool Schema | OpenAI-compatible tool schema | `app/tools/definitions.py` |
| Tool Metadata | 工程侧工具治理信息 | `app/tool_registry.py` |
| Tool Invocation | 工具调用执行 | `app/tool_executor.py` |
| Resource | 论文、向量库、任务、trace 文件 | `data/*` |
| Prompt | 可复用提示词和评估模板 | `app/prompts.py`, `app/evaluation.py` 等 |
| Audit | trace / comparison / benchmark | `app/*trace*`, `app/*comparator*` |

## Tool Discovery

MCP 中，工具需要可发现。

当前项目中的对应能力是：

```text
REGISTERED_TOOLS
list_registered_tools()
build_openai_tool_schemas()
```

也就是说，当前项目已经能回答：

```text
有哪些工具？
每个工具叫什么？
工具描述是什么？
输入 schema 是什么？
工具是否启用？
```

未来接 MCP 时，远程 MCP tools 应该先转换成本地统一结构，再进入 Agent：

```text
MCP tool list
-> local RegisteredTool-like metadata
-> permission validation
-> execution config
-> trace
```

## Tool Schema

当前项目使用 OpenAI-compatible tool schema：

```text
type=function
function.name
function.description
function.parameters
required
additionalProperties=False
```

这些 schema 位于：

```text
app/tools/definitions.py
```

MCP tool schema 与这里的思想一致：工具必须告诉模型和 Host：

- 工具名称
- 工具用途
- 参数结构
- 参数约束

当前项目已经给 `top_k`、`maxLength`、`required`、`additionalProperties` 等做了约束，这些都是协议化工具必须具备的内容。

## Tool Metadata

MCP schema 主要描述“怎么调用工具”，但工程系统还需要知道“是否应该调用、怎么安全调用”。

当前项目通过 `ToolMetadata` 管理：

```text
name
description
permission
owner
enabled
timeout_seconds
retry_count
result_max_characters
input_schema
output_schema
```

这层 metadata 是接 MCP 前必须保留的治理层。

未来即使工具来自远程 MCP Server，也不应该让模型绕开本地 metadata 直接调用。

## Tool Invocation

当前工具调用链路：

```text
LLM tool call
-> parse JSON arguments
-> resolve registered tool
-> validate metadata
-> execute with timeout
-> retry on failure
-> serialize result
-> limit result length
-> return tool message
-> record trace
```

MCP 接入后，变化主要是执行端：

```text
本地函数调用
```

会变成：

```text
MCP client -> MCP server -> tool result
```

但本地治理链路仍然应该保留：

```text
permission
timeout
retry
result limit
standard error
trace
```

## Permission 与 Allowed Tools

当前项目有两层权限：

### 1. Tool Permission

位于 `app/tool_executor.py`：

```text
read
llm_generate
llm_evaluate
```

### 2. Sub-Agent Allowed Tools

位于 `app/sub_agent_specs.py`：

```text
retrieval_agent -> search_thesis
defense_question_agent -> create_defense_questions
answer_evaluation_agent -> evaluate_student_answer
follow_up_agent -> generate_follow_up
training_record_agent -> query_training_record
```

这两层权限对应 MCP 接入后的两个问题：

```text
这个工具类型是否允许被 Host 执行？
这个角色 / Sub-Agent 是否允许调用该工具？
```

未来接外部 MCP 工具时，也应该先进入这两层权限判断。

## Resource 对照

MCP Resource 是可读取上下文资源。

当前项目中的资源包括：

```text
data/thesis.pdf
data/vector_store.json
data/rag_benchmark.json
data/defense_tasks/*.json
data/traces/*.jsonl
data/long_term_memory.json
```

当前这些资源通过本地文件读取。未来如果接 MCP，可以把其中一部分暴露为资源：

```text
thesis document resource
task record resource
trace resource
memory resource
benchmark resource
```

但资源暴露必须受权限控制，不能直接开放整个文件系统。

## Prompt 对照

MCP Prompt 是可复用的提示词模板。

当前项目里的对应物：

```text
app/prompts.py
app/evaluation.py
app/follow_up.py
app/answer_rewrite.py
app/training_summary.py
```

这些 prompt 当前是代码内模板。未来如果做 MCP Prompt，对应的是把这些模板标准化为可发现、可版本化的 prompt 资源。

## Audit 对照

当前项目已经有多类审计：

```text
Agent trace
Task trace
Sub-Agent plan trace
Sub-Agent execution trace
Evaluation report
Regression comparison
Local quality gate
```

MCP 工具接入后，工具来源变复杂，审计更重要。

必须记录：

- 调用了哪个 MCP Server
- 调用了哪个 tool
- 输入参数是什么
- 输出结果是否被截断
- 是否超时
- 是否重试
- 是否失败
- 耗时多少
- 是否进入 benchmark / feedback

## 当前项目到 MCP 的迁移路径

推荐路径：

```text
1. 保留当前 Tool Registry
2. 新增 MCP client adapter
3. 将 MCP tool 转成本地 RegisteredTool-like 对象
4. 复用 tool_executor 的 permission / retry / timeout / result limit
5. 复用 Agent trace 和 Sub-Agent trace
6. 最后再考虑远程工具市场和审批流
```

不要直接让 LLM 面对外部 MCP tools。必须经过本地治理层。

## 当前边界

当前阶段只是协议对照学习：

- 没有真实 MCP Client
- 没有真实 MCP Server
- 没有网络工具调用
- 没有 OAuth
- 没有远程资源列表
- 没有 MCP prompt registry

这些都留到服务器和服务化阶段。

## 学到的关键点

```text
MCP 不是替代 Agent Harness，而是外部工具协议。
本地 Tool Registry 是接 MCP 前的治理基座。
远程工具必须先转换成本地可治理对象，再进入 Agent Loop。
工具发现、工具授权、工具调用和工具审计必须分层处理。
```

## 简历表达

可以写成：

```text
完成本地 Agent Harness 与 MCP 工具协议的概念映射，梳理 Tool Schema、Tool Registry、Tool Metadata、权限控制、工具调用、资源暴露、Prompt 模板和 trace 审计之间的对应关系，为后续接入远程 MCP Server 和企业工具市场预留统一治理路径。
```

## 后续学习

下一阶段建议进入：

```text
项目阶段总复盘：
汇总本机学习版 Agent Harness 已完成能力、未完成边界、可展示命令、简历表达和下一阶段服务器学习计划。
```
