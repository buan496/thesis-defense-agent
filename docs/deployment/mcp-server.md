# MCP Server

## Purpose

This project now includes a minimal local stdio MCP server. It exposes the
existing Tool Registry through MCP-style JSON-RPC methods instead of creating a
separate tool implementation.

```text
Tool Registry
-> MCP tools/list
-> MCP tools/call
-> MCP resources/list
-> MCP resources/read
-> MCP prompts/list
-> MCP prompts/get
-> stdio JSON-RPC loop
```

The first exposed tool is the existing thesis search capability:

```text
search_thesis
```

## Files

```text
app/mcp_server.py
app/mcp_resources.py
app/mcp_prompts.py
tests/test_mcp_server.py
```

## Supported Methods

```text
initialize
notifications/initialized
tools/list
tools/call
resources/list
resources/read
prompts/list
prompts/get
```

Unsupported methods return JSON-RPC `METHOD_NOT_FOUND`.

Invalid parameters return JSON-RPC `INVALID_PARAMS`.

## Run Locally

Start the server:

```powershell
uv run python -m app.mcp_server
```

The server reads one JSON-RPC request per line from stdin and writes one
JSON-RPC response per line to stdout.

## Example: Initialize

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
```

Expected response shape:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {},
      "resources": {},
      "prompts": {}
    },
    "serverInfo": {
      "name": "thesis-defense-agent",
      "version": "0.1.0"
    }
  }
}
```

## Example: List Tools

```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

The response includes registered tools such as:

```text
search_thesis
create_defense_questions
evaluate_student_answer
generate_follow_up
query_training_record
```

## Example: Call Tool

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_thesis","arguments":{"query":"系统架构","top_k":3}}}
```

`tools/call` reuses existing tool governance:

```text
enabled flag
permission check
retry count
timeout
result length limit
standardized errors
```

## Example: List Resources

```json
{"jsonrpc":"2.0","id":4,"method":"resources/list","params":{}}
```

Available local resources:

```text
thesis://summary
thesis://readme
thesis://progress
```

## Example: Read Resource

```json
{"jsonrpc":"2.0","id":5,"method":"resources/read","params":{"uri":"thesis://summary"}}
```

## Example: List Prompts

```json
{"jsonrpc":"2.0","id":6,"method":"prompts/list","params":{}}
```

Available local prompts:

```text
defense_question_prompt
answer_evaluation_prompt
follow_up_prompt
```

## Example: Get Prompt

```json
{"jsonrpc":"2.0","id":7,"method":"prompts/get","params":{"name":"defense_question_prompt","arguments":{"thesis_context":"系统架构包括特征处理和模型训练。"}}}
```

## Current Boundary

Completed:

```text
stdio JSON-RPC server loop
initialize
tools/list
tools/call
resources/list
resources/read
prompts/list
prompts/get
Tool Registry integration
local resource registry
local prompt registry
offline tests with fake tool caller
```

Not completed:

```text
remote HTTP MCP transport
authentication
multi-server MCP client
tool marketplace integration
production MCP deployment
```
