# MCP 与 Sub-Agent 前置概念

本文件用于在接入真实 MCP 服务器或实现 Sub-Agent 之前，先把已有项目中的概念对齐清楚。

当前阶段只做本地学习版概念映射，不接真实 MCP 服务，不做服务器部署，不覆盖现有 `app/agent.py`、`app/task_*` 和 `app/langgraph_workflow/*`。

## 为什么现在学 MCP

当前项目已经具备一套本地 Agent Harness：

```text
Tool Schema
-> Tool Registry
-> Tool Executor
-> Agent Loop
-> Trace
-> Evaluation
```

MCP 的核心价值不是“多一个库”，而是把外部能力标准化成可发现、可描述、可调用、可治理的工具和上下文资源。

也就是说，MCP 要解决的问题和当前项目已经做过的工具治理问题是一脉相承的：

```text
工具从哪里来？
工具如何描述？
工具参数如何约束？
工具是否允许调用？
工具调用结果如何返回？
工具失败如何处理？
工具调用如何审计？
```

## MCP 基本角色

### Host

Host 是承载 Agent 的应用。

在本项目里，可以把以下部分理解为 Host：

```text
app.cli
app.agent
app.session_service
app.task_service
```

它们负责接收用户请求、组织上下文、调用模型、调度工具、保存记录。

### Client

Client 是 Host 中负责连接某个 MCP Server 的组件。

当前项目还没有真实 MCP Client，但类似职责可以类比为：

```text
app.tool_executor
```

它负责把工具调用请求转换成实际函数执行，并处理异常、重试、超时和结果长度限制。

### Server

Server 是提供工具、资源或提示词的一端。

如果未来接入 MCP，可以把不同能力拆成不同 Server：

```text
thesis-rag-server       提供论文检索工具
task-record-server      提供训练记录查询工具
evaluation-server       提供评价与回归测试工具
filesystem-server       提供受控文件读取能力
```

当前项目中还没有独立 Server，所有工具都在本地 Python 模块里。

### Tool

Tool 是模型可以请求调用的动作。

当前项目已有工具：

```text
search_thesis
create_defense_questions
evaluate_student_answer
generate_follow_up
query_training_record
```

对应代码：

```text
app/tools/
app/tool_registry.py
app/tool_executor.py
```

### Resource

Resource 是可读取的上下文资源，不一定是动作。

在本项目中可以类比为：

```text
data/thesis.pdf
data/vector_store.json
data/rag_benchmark.json
data/defense_tasks/*.json
data/traces/*.jsonl
```

Tool 更像“做一件事”，Resource 更像“提供一份资料”。

### Prompt

Prompt 是可复用的提示词模板。

当前项目中可以类比为：

```text
app/prompts.py
app/evaluation.py
app/follow_up.py
app/answer_rewrite.py
app/training_summary.py
```

## 当前项目与 MCP 的概念映射

| MCP 概念 | 当前项目对应物 | 说明 |
| --- | --- | --- |
| Host | `app.cli` / `app.agent` / `app.task_service` | 承载 Agent 运行 |
| Client | `app.tool_executor` | 分发工具调用 |
| Server | 暂无 | 未来可拆为 RAG Server、Task Server |
| Tool | `app/tools/*` | 可调用能力 |
| Tool Schema | `app/tools/definitions.py` | 给 LLM 看的调用格式 |
| Tool Metadata | `app/tool_registry.py` | 给工程系统看的治理信息 |
| Resource | `data/*` | 论文、向量库、任务、trace |
| Prompt | `app/prompts.py` 等 | 可复用提示词 |
| Trace | `data/traces/*.jsonl` / task trace | 工具调用和 Agent 运行审计 |

## MCP 与当前 Tool Registry 的关系

当前项目已经实现：

```text
Tool Schema
Tool Metadata
enabled 开关
permission 白名单
timeout
retry
result length limit
标准化错误
trace
```

这些能力可以理解为 MCP 接入前的本地版工具治理层。

未来接入 MCP 时，不应该绕过这层治理，而应该把远程 MCP 工具也转换成同样的 `RegisteredTool` 或类似结构：

```text
MCP Tool
-> 本地 ToolMetadata
-> Tool Executor
-> Trace / Evaluation
```

这样可以保证：

```text
本地工具和远程工具走同一套权限、超时、重试、审计逻辑。
```

## Sub-Agent 基本概念

Sub-Agent 不是简单的函数，也不是普通工具。

可以先理解为：

```text
有独立职责、独立上下文、可被主 Agent 调度的执行者。
```

它通常具备：

```text
role        它负责什么
input       主 Agent 给它什么任务
context     它能看到哪些上下文
tools       它能调用哪些工具
output      它必须返回什么结构
budget      它最多能花多少 token / 时间
trace       它的执行过程如何记录
```

## 当前项目可拆分的 Sub-Agent 候选

### Retrieval Agent

职责：

```text
根据用户问题检索论文证据。
```

可用工具：

```text
search_thesis
```

输出：

```text
evidence
sources
retrieval_score
```

### Defense Question Agent

职责：

```text
基于论文证据生成答辩问题。
```

可用工具：

```text
create_defense_questions
```

输入必须包含：

```text
retrieved_context
```

### Evaluation Agent

职责：

```text
评价学生回答质量。
```

可用工具：

```text
evaluate_student_answer
```

输出：

```text
score
strengths
weaknesses
suggestions
```

### Follow-Up Agent

职责：

```text
根据回答和评价生成追问。
```

可用工具：

```text
generate_follow_up
```

### Training Summary Agent

职责：

```text
总结整轮训练，提取薄弱点，写入长期记忆。
```

当前可复用：

```text
summarize_training
add_training_summary
add_weakness
```

## Sub-Agent 与普通 Tool 的区别

| 对比项 | Tool | Sub-Agent |
| --- | --- | --- |
| 粒度 | 单个动作 | 一个小型工作流 |
| 是否调用 LLM | 不一定 | 通常会 |
| 是否有独立上下文 | 通常没有 | 有 |
| 是否可调用工具 | 通常自身就是工具 | 可以调用多个工具 |
| 输出 | 函数结果 | 结构化任务结果 |
| 审计 | 工具 trace | 子 Agent trace |

简单说：

```text
Tool 是能力。
Sub-Agent 是带目标、上下文和工具集的小执行者。
```

## 未来不要直接做的事

当前阶段不做：

```text
真实 MCP Server
真实 MCP Client
跨进程工具服务
Docker 部署
数据库部署
多 Agent 并发
自动委派复杂任务
```

这些内容放到后续服务器环境或更成熟阶段。

## 下一步建议

下一步可以先做一个本地版 Sub-Agent 规格定义，不实际调度：

```text
app/sub_agent_specs.py
```

定义：

```python
SubAgentSpec(
    name="retrieval_agent",
    role="检索论文证据",
    allowed_tools=["search_thesis"],
    input_fields=["query"],
    output_fields=["evidence", "sources"],
    max_steps=2,
)
```

这一步的目标是继续学习：

```text
如何限制一个 Agent 能做什么；
如何定义 Agent 的输入输出边界；
如何把工具权限从单工具扩展到子 Agent 级别。
```
