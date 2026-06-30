# MCP Server

## Purpose

This project now includes a minimal local stdio MCP server. It exposes the
existing Tool Registry through MCP-style JSON-RPC methods instead of creating a
separate tool implementation.

```text
Tool Registry
-> MCP tools/list
-> MCP tools/call
-> stdio JSON-RPC loop
```

The first exposed tool is the existing thesis search capability:

```text
search_thesis
```

## Files

```text
app/mcp_server.py
tests/test_mcp_server.py
```

## Supported Methods

```text
initialize
notifications/initialized
tools/list
tools/call
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
      "tools": {}
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

## Current Boundary

Completed:

```text
stdio JSON-RPC server loop
initialize
tools/list
tools/call
Tool Registry integration
offline tests with fake tool caller
```

Not completed:

```text
remote HTTP MCP transport
authentication
resource/list and prompt/list support
multi-server MCP client
tool marketplace integration
production MCP deployment
```
