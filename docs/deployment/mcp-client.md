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
-> resources/list
-> resources/read
-> prompts/list
-> prompts/get
```

The client is a learning implementation. It is intentionally small and keeps
MCP transport, request parsing, and result parsing visible.

## Files

```text
app/mcp_client.py
tests/test_mcp_client.py
docs/deployment/mcp-client.md
docs/deployment/mcp-resources-prompts.md
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

## Main Objects

```text
McpClientConfig
McpTool
McpResource
McpResourceContent
McpPrompt
McpPromptResult
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
    resources = client.list_resources()
    prompts = client.list_prompts()
    result = client.call_tool(
        "search_thesis",
        {
            "query": "系统架构",
            "top_k": 3,
        },
    )
    print([tool.name for tool in tools])
    print([resource.uri for resource in resources])
    print([prompt.name for prompt in prompts])
    print(result.text)
```

## What This Teaches

```text
JSON-RPC request / response shape
stdio process transport
initialize handshake
tool discovery through tools/list
tool invocation through tools/call
resource discovery through resources/list
resource reading through resources/read
prompt discovery through prompts/list
prompt rendering through prompts/get
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
resources/list parsing
resources/read parsing
prompts/list parsing
prompts/get parsing
offline unit tests
```

Not completed:

```text
multi-server MCP client manager
MCP tool registration into Agent Tool Registry
remote HTTP MCP transport
authentication
long-running MCP daemon supervision
```
