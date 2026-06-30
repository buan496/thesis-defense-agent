# MCP Client

## Purpose

The project already exposes its local Tool Registry through a minimal stdio MCP
server. This stage adds the opposite side: a minimal MCP client that can talk to
an MCP server over stdio.

```text
McpStdioClient
-> initialize
-> notifications/initialized
-> tools/list
-> tools/call
```

The client is a learning implementation. It is intentionally small and keeps
MCP transport, request parsing, and result parsing visible.

## Files

```text
app/mcp_client.py
tests/test_mcp_client.py
docs/deployment/mcp-client.md
```

## Supported Methods

```text
initialize
notifications/initialized
tools/list
tools/call
```

## Main Objects

```text
McpClientConfig
McpTool
McpClientResult
McpStdioClient
```

## Local Example

Start the local MCP server through the client command:

```python
from app.mcp_client import McpClientConfig, McpStdioClient

config = McpClientConfig(
    command=["uv", "run", "python", "-m", "app.mcp_server"],
)

with McpStdioClient(config) as client:
    client.initialize()
    tools = client.list_tools()
    result = client.call_tool(
        "search_thesis",
        {
            "query": "系统架构",
            "top_k": 3,
        },
    )
    print([tool.name for tool in tools])
    print(result.text)
```

## What This Teaches

```text
JSON-RPC request / response shape
stdio process transport
initialize handshake
tool discovery through tools/list
tool invocation through tools/call
client-side error handling
```

## Boundary

Completed:

```text
JSON-RPC request builder
JSON-RPC response parser
stdio MCP client
initialize handshake
tools/list parsing
tools/call parsing
offline unit tests
```

Not completed:

```text
resource/list
prompt/list
multi-server MCP client manager
MCP tool registration into Agent Tool Registry
remote HTTP MCP transport
authentication
long-running MCP daemon supervision
```
