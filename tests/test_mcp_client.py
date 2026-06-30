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
    parse_mcp_prompts,
    parse_mcp_resources,
    parse_mcp_tools,
    parse_prompt_get_result,
    parse_resource_read_result,
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


def test_parse_mcp_resources():
    resources = parse_mcp_resources(
        {
            "resources": [
                {
                    "uri": "thesis://summary",
                    "name": "Summary",
                    "description": "Project summary",
                    "mimeType": "text/plain",
                }
            ]
        }
    )

    assert resources[0].uri == "thesis://summary"
    assert resources[0].name == "Summary"
    assert resources[0].mime_type == "text/plain"


def test_parse_resource_read_result():
    contents = parse_resource_read_result(
        {
            "contents": [
                {
                    "uri": "thesis://summary",
                    "mimeType": "text/plain",
                    "text": "summary text",
                }
            ]
        }
    )

    assert contents[0].uri == "thesis://summary"
    assert contents[0].text == "summary text"


def test_parse_mcp_prompts():
    prompts = parse_mcp_prompts(
        {
            "prompts": [
                {
                    "name": "defense_question_prompt",
                    "description": "Generate questions",
                    "arguments": [
                        {
                            "name": "thesis_context",
                            "description": "context",
                            "required": True,
                        }
                    ],
                }
            ]
        }
    )

    assert prompts[0].name == "defense_question_prompt"
    assert prompts[0].arguments[0].name == "thesis_context"
    assert prompts[0].arguments[0].required is True


def test_parse_prompt_get_result():
    result = parse_prompt_get_result(
        {
            "description": "Generate questions",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": "prompt text",
                    },
                }
            ],
        }
    )

    assert result.description == "Generate questions"
    assert result.messages[0].role == "user"
    assert result.messages[0].text == "prompt text"


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


def test_mcp_stdio_client_list_resources():
    input_stream = io.StringIO(
        make_response(
            1,
            {
                "resources": [
                    {
                        "uri": "thesis://summary",
                        "name": "Summary",
                        "description": "Project summary",
                        "mimeType": "text/plain",
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

    resources = client.list_resources()

    assert resources[0].uri == "thesis://summary"
    request = json.loads(output_stream.getvalue().splitlines()[0])
    assert request["method"] == "resources/list"


def test_mcp_stdio_client_read_resource():
    input_stream = io.StringIO(
        make_response(
            1,
            {
                "contents": [
                    {
                        "uri": "thesis://summary",
                        "mimeType": "text/plain",
                        "text": "summary text",
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

    contents = client.read_resource("thesis://summary")

    assert contents[0].text == "summary text"
    request = json.loads(output_stream.getvalue().splitlines()[0])
    assert request["method"] == "resources/read"
    assert request["params"]["uri"] == "thesis://summary"


def test_mcp_stdio_client_list_prompts():
    input_stream = io.StringIO(
        make_response(
            1,
            {
                "prompts": [
                    {
                        "name": "defense_question_prompt",
                        "description": "Generate questions",
                        "arguments": [],
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

    prompts = client.list_prompts()

    assert prompts[0].name == "defense_question_prompt"
    request = json.loads(output_stream.getvalue().splitlines()[0])
    assert request["method"] == "prompts/list"


def test_mcp_stdio_client_get_prompt():
    input_stream = io.StringIO(
        make_response(
            1,
            {
                "description": "Generate questions",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": "prompt text",
                        },
                    }
                ],
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

    result = client.get_prompt(
        "defense_question_prompt",
        {
            "thesis_context": "context",
        },
    )

    assert result.messages[0].text == "prompt text"
    request = json.loads(output_stream.getvalue().splitlines()[0])
    assert request["method"] == "prompts/get"
    assert request["params"]["name"] == "defense_question_prompt"
    assert request["params"]["arguments"]["thesis_context"] == "context"


def test_mcp_stdio_client_rejects_empty_resource_uri_and_prompt_name():
    client = McpStdioClient(
        config=McpClientConfig(command=["fake"]),
        input_stream=io.StringIO(),
        output_stream=io.StringIO(),
    )

    with pytest.raises(ValueError, match="resource uri"):
        client.read_resource("")

    with pytest.raises(ValueError, match="prompt name"):
        client.get_prompt("")
