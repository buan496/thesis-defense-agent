# MCP Resources and Prompts

## Purpose

Tools execute actions. Resources provide context. Prompts provide reusable
prompt templates.

This stage extends the local MCP server and client beyond tool calling:

```text
resources/list
resources/read
prompts/list
prompts/get
```

## Files

```text
app/mcp_resources.py
app/mcp_prompts.py
app/mcp_server.py
app/mcp_client.py
tests/test_mcp_resources.py
tests/test_mcp_prompts.py
tests/test_mcp_server.py
tests/test_mcp_client.py
```

## Local Resources

```text
thesis://summary
thesis://readme
thesis://progress
```

Resource examples:

```json
{"jsonrpc":"2.0","id":1,"method":"resources/list","params":{}}
```

```json
{"jsonrpc":"2.0","id":2,"method":"resources/read","params":{"uri":"thesis://summary"}}
```

## Local Prompts

```text
defense_question_prompt
answer_evaluation_prompt
follow_up_prompt
```

Prompt examples:

```json
{"jsonrpc":"2.0","id":3,"method":"prompts/list","params":{}}
```

```json
{"jsonrpc":"2.0","id":4,"method":"prompts/get","params":{"name":"defense_question_prompt","arguments":{"thesis_context":"系统架构包括特征处理和模型训练。"}}}
```

## Boundary

Completed:

```text
local resource registry
local prompt registry
MCP Server resources/list
MCP Server resources/read
MCP Server prompts/list
MCP Server prompts/get
MCP Client resource parsing
MCP Client prompt parsing
offline tests
```

Not completed:

```text
dynamic resource subscriptions
resource pagination
remote MCP transport
multi-server MCP resource aggregation
prompt marketplace
automatic prompt injection into Agent runtime
```
