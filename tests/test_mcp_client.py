import io
import json

import pytest

from app.mcp_client import (
    MCP_PROTOCOL_VERSION,
    JSON_RPC_VERSION,
    McpClientConfig,
    McpClientError,
    McpStdioClient,
    build_initialized_notification,
    build_json_rpc_request,
    parse_json_rpc_response,
    parse_mcp_tools,
    parse_tool_call_result,
)


def make_response(request_id, result):
    return json.dumps(
        {
            "jsonrpc": JSON_RPC_VERSION,
            "id": request_id,
            "result": result,
        },
        ensure_ascii=False,
    )


def test_build_json_rpc_request():
    request = build_json_rpc_request(
        request_id=1,
        method="tools/list",
        params={},
    )

    assert request == {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }


def test_build_initialized_notification():
    notification = build_initialized_notification()

    assert notification["jsonrpc"] == "2.0"
    assert notification["method"] == "notifications/initialized"
    assert "id" not in notification


def test_parse_json_rpc_response_returns_result():
    result = parse_json_rpc_response(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "ok": True,
            },
        },
        expected_id=1,
    )

    assert result == {"ok": True}


def test_parse_json_rpc_response_rejects_error():
    with pytest.raises(McpClientError, match="MCP error"):
        parse_json_rpc_response(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32601,
                    "message": "unsupported",
                },
            },
            expected_id=1,
        )


def test_parse_json_rpc_response_rejects_wrong_id():
    with pytest.raises(McpClientError, match="unexpected response id"):
        parse_json_rpc_response(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "result": {},
            },
            expected_id=1,
        )


def test_parse_mcp_tools():
    tools = parse_mcp_tools(
        {
            "tools": [
                {
                    "name": "search_thesis",
                    "description": "Search thesis",
                    "inputSchema": {
                        "type": "object",
                    },
                },
                "invalid",
            ]
        }
    )

    assert len(tools) == 1
    assert tools[0].name == "search_thesis"
    assert tools[0].description == "Search thesis"
    assert tools[0].input_schema == {"type": "object"}


def test_parse_tool_call_result():
    result = parse_tool_call_result(
        {
            "content": [
                {
                    "type": "text",
                    "text": "hello",
                }
            ],
            "isError": False,
        }
    )

    assert result.is_error is False
    assert result.text == "hello"


def test_mcp_stdio_client_initialize_sends_notification():
    input_stream = io.StringIO(
        make_response(
            1,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "fake",
                    "version": "0.1.0",
                },
            },
        )
        + "\n"
    )
    output_stream = io.StringIO()
    client = McpStdioClient(
        config=McpClientConfig(command=["fake"]),
        input_stream=input_stream,
        output_stream=output_stream,
    )

    result = client.initialize()

    assert result["protocolVersion"] == MCP_PROTOCOL_VERSION
    written = [
        json.loads(line)
        for line in output_stream.getvalue().splitlines()
    ]
    assert written[0]["method"] == "initialize"
    assert written[0]["params"]["clientInfo"]["name"] == "thesis-defense-agent-client"
    assert written[1]["method"] == "notifications/initialized"
    assert "id" not in written[1]


def test_mcp_stdio_client_list_tools():
    input_stream = io.StringIO(
        make_response(
            1,
            {
                "tools": [
                    {
                        "name": "search_thesis",
                        "description": "Search thesis",
                        "inputSchema": {
                            "type": "object",
                        },
                    }
                ]
            },
        )
        + "\n"
    )
    output_stream = io.StringIO()
    client = McpStdioClient(
        config=McpClientConfig(command=["fake"]),
        input_stream=input_stream,
        output_stream=output_stream,
    )

    tools = client.list_tools()

    assert tools[0].name == "search_thesis"
    request = json.loads(output_stream.getvalue().splitlines()[0])
    assert request["method"] == "tools/list"


def test_mcp_stdio_client_call_tool():
    input_stream = io.StringIO(
        make_response(
            1,
            {
                "content": [
                    {
                        "type": "text",
                        "text": "tool result",
                    }
                ],
                "isError": False,
            },
        )
        + "\n"
    )
    output_stream = io.StringIO()
    client = McpStdioClient(
        config=McpClientConfig(command=["fake"]),
        input_stream=input_stream,
        output_stream=output_stream,
    )

    result = client.call_tool(
        "search_thesis",
        {
            "query": "系统架构",
        },
    )

    assert result.text == "tool result"
    request = json.loads(output_stream.getvalue().splitlines()[0])
    assert request["method"] == "tools/call"
    assert request["params"]["name"] == "search_thesis"
    assert request["params"]["arguments"]["query"] == "系统架构"


def test_mcp_stdio_client_rejects_empty_tool_name():
    client = McpStdioClient(
        config=McpClientConfig(command=["fake"]),
        input_stream=io.StringIO(),
        output_stream=io.StringIO(),
    )

    with pytest.raises(ValueError, match="tool name"):
        client.call_tool("")
