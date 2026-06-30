import io
import json

from app.mcp_server import (
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    SERVER_NAME,
    build_initialize_result,
    build_mcp_tool_schemas,
    build_tool_call_result,
    handle_mcp_line,
    handle_mcp_request,
    run_stdio_server,
)


def fake_tool_caller(name, arguments):
    return build_tool_call_result(
        json.dumps(
            {
                "tool": name,
                "arguments": arguments,
            },
            ensure_ascii=False,
        )
    )


def test_build_initialize_result_exposes_tool_capability():
    result = build_initialize_result()

    assert result["serverInfo"]["name"] == SERVER_NAME
    assert result["capabilities"]["tools"] == {}
    assert result["capabilities"]["resources"] == {}
    assert result["capabilities"]["prompts"] == {}
    assert result["protocolVersion"]


def test_build_mcp_tool_schemas_includes_registered_search_tool():
    tools = build_mcp_tool_schemas()
    names = [tool["name"] for tool in tools]

    assert "search_thesis" in names

    search_tool = next(tool for tool in tools if tool["name"] == "search_thesis")

    assert "description" in search_tool
    assert search_tool["inputSchema"]["type"] == "object"
    assert "query" in search_tool["inputSchema"]["required"]


def test_handle_initialize_request():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        }
    )

    assert response["id"] == 1
    assert response["result"]["serverInfo"]["name"] == SERVER_NAME


def test_handle_tools_list_request():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "tools",
            "method": "tools/list",
            "params": {},
        }
    )

    assert response["id"] == "tools"
    assert "tools" in response["result"]
    assert any(
        tool["name"] == "search_thesis"
        for tool in response["result"]["tools"]
    )


def test_handle_tools_call_request_with_fake_tool_caller():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "call-1",
            "method": "tools/call",
            "params": {
                "name": "search_thesis",
                "arguments": {
                    "query": "系统架构",
                    "top_k": 3,
                },
            },
        },
        tool_caller=fake_tool_caller,
    )

    assert response["id"] == "call-1"
    result = response["result"]
    assert result["isError"] is False
    assert result["content"][0]["type"] == "text"
    assert "search_thesis" in result["content"][0]["text"]
    assert "系统架构" in result["content"][0]["text"]


def test_handle_tools_call_rejects_missing_tool_name():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "arguments": {},
            },
        }
    )

    assert response["error"]["code"] == INVALID_PARAMS
    assert "params.name" in response["error"]["message"]


def test_handle_resources_list_request():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "resources",
            "method": "resources/list",
            "params": {},
        }
    )

    assert response["id"] == "resources"
    assert any(
        resource["uri"] == "thesis://summary"
        for resource in response["result"]["resources"]
    )


def test_handle_resources_read_request():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "read",
            "method": "resources/read",
            "params": {
                "uri": "thesis://summary",
            },
        }
    )

    assert response["id"] == "read"
    assert response["result"]["contents"][0]["uri"] == "thesis://summary"
    assert "Thesis Defense Agent" in response["result"]["contents"][0]["text"]


def test_handle_resources_read_rejects_missing_uri():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "read-error",
            "method": "resources/read",
            "params": {},
        }
    )

    assert response["error"]["code"] == INVALID_PARAMS
    assert "params.uri" in response["error"]["message"]


def test_handle_prompts_list_request():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "prompts",
            "method": "prompts/list",
            "params": {},
        }
    )

    assert response["id"] == "prompts"
    assert any(
        prompt["name"] == "defense_question_prompt"
        for prompt in response["result"]["prompts"]
    )


def test_handle_prompts_get_request():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "prompt-get",
            "method": "prompts/get",
            "params": {
                "name": "defense_question_prompt",
                "arguments": {
                    "thesis_context": "系统架构包括模型训练。",
                },
            },
        }
    )

    assert response["id"] == "prompt-get"
    text = response["result"]["messages"][0]["content"]["text"]
    assert "系统架构包括模型训练" in text


def test_handle_prompts_get_rejects_missing_name():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "prompt-error",
            "method": "prompts/get",
            "params": {},
        }
    )

    assert response["error"]["code"] == INVALID_PARAMS
    assert "params.name" in response["error"]["message"]


def test_handle_unknown_method_returns_method_not_found():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "unknown/method",
            "params": {},
        }
    )

    assert response["error"]["code"] == METHOD_NOT_FOUND
    assert "unsupported MCP method" in response["error"]["message"]


def test_initialized_notification_returns_no_response():
    response = handle_mcp_request(
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
    )

    assert response is None


def test_handle_invalid_json_line_returns_parse_error():
    response = handle_mcp_line("{bad json")

    assert response["error"]["code"] == -32700


def test_run_stdio_server_writes_json_lines():
    input_stream = io.StringIO(
        "\n".join(
            [
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {},
                    }
                ),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                        "params": {},
                    }
                ),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "search_thesis",
                            "arguments": {
                                "query": "系统架构",
                            },
                        },
                    }
                ),
            ]
        )
        + "\n"
    )
    output_stream = io.StringIO()

    run_stdio_server(
        input_stream=input_stream,
        output_stream=output_stream,
        tool_caller=fake_tool_caller,
    )

    lines = [
        json.loads(line)
        for line in output_stream.getvalue().splitlines()
    ]

    assert len(lines) == 2
    assert lines[0]["id"] == 1
    assert lines[1]["id"] == 2
