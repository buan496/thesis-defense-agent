import json
import sys
from collections.abc import Callable
from typing import Any, TextIO

from app.tool_executor import (
    execute_tool_function_with_retry,
    limit_tool_result_text,
    resolve_tool_execution_config,
)
from app.tool_registry import list_registered_tools


JSON_RPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "thesis-defense-agent"
SERVER_VERSION = "0.1.0"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def build_json_rpc_response(
    request_id: Any,
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "jsonrpc": JSON_RPC_VERSION,
        "id": request_id,
        "result": result,
    }


def build_json_rpc_error(
    request_id: Any,
    code: int,
    message: str,
) -> dict[str, Any]:
    return {
        "jsonrpc": JSON_RPC_VERSION,
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def build_initialize_result() -> dict[str, Any]:
    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {
            "tools": {},
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    }


def build_mcp_tool_schemas() -> list[dict[str, Any]]:
    tools = []

    for metadata in list_registered_tools():
        tools.append(
            {
                "name": metadata.name,
                "description": metadata.description,
                "inputSchema": metadata.input_schema,
            }
        )

    return tools


def build_tool_call_result(
    text: str,
    is_error: bool = False,
) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": text,
            }
        ],
        "isError": is_error,
    }


def call_mcp_tool(
    name: str,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not name.strip():
        raise ValueError("tool name must not be empty")

    execution_config = resolve_tool_execution_config(name)
    result = execute_tool_function_with_retry(
        execution_config["function"],
        arguments or {},
        max_retries=execution_config["max_retries"],
        timeout_seconds=execution_config["timeout_seconds"],
    )
    result_text = json.dumps(
        result,
        ensure_ascii=False,
    )
    limited_result_text = limit_tool_result_text(
        result_text,
        max_characters=execution_config["result_max_characters"],
    )

    return build_tool_call_result(limited_result_text)


def validate_json_rpc_request(
    request: Any,
) -> tuple[Any, str, dict[str, Any]]:
    if not isinstance(request, dict):
        raise ValueError("request must be a JSON object")

    if request.get("jsonrpc") != JSON_RPC_VERSION:
        raise ValueError("jsonrpc must be 2.0")

    method = request.get("method")
    if not isinstance(method, str) or not method:
        raise ValueError("method must be a non-empty string")

    params = request.get("params", {})
    if params is None:
        params = {}

    if not isinstance(params, dict):
        raise ValueError("params must be an object")

    return request.get("id"), method, params


def handle_mcp_request(
    request: Any,
    tool_caller: Callable[[str, dict[str, Any] | None], dict[str, Any]] = call_mcp_tool,
) -> dict[str, Any] | None:
    try:
        request_id, method, params = validate_json_rpc_request(request)
    except ValueError as error:
        return build_json_rpc_error(
            request_id=request.get("id") if isinstance(request, dict) else None,
            code=INVALID_REQUEST,
            message=str(error),
        )

    is_notification = "id" not in request

    if method == "notifications/initialized":
        return None

    if is_notification:
        return None

    try:
        if method == "initialize":
            return build_json_rpc_response(
                request_id,
                build_initialize_result(),
            )

        if method == "tools/list":
            return build_json_rpc_response(
                request_id,
                {
                    "tools": build_mcp_tool_schemas(),
                },
            )

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if not isinstance(tool_name, str) or not tool_name:
                return build_json_rpc_error(
                    request_id,
                    INVALID_PARAMS,
                    "params.name must be a non-empty string",
                )

            if arguments is not None and not isinstance(arguments, dict):
                return build_json_rpc_error(
                    request_id,
                    INVALID_PARAMS,
                    "params.arguments must be an object",
                )

            return build_json_rpc_response(
                request_id,
                tool_caller(tool_name, arguments),
            )

        return build_json_rpc_error(
            request_id,
            METHOD_NOT_FOUND,
            f"unsupported MCP method: {method}",
        )
    except ValueError as error:
        return build_json_rpc_error(
            request_id,
            INVALID_PARAMS,
            str(error),
        )
    except Exception as error:
        return build_json_rpc_error(
            request_id,
            INTERNAL_ERROR,
            str(error),
        )


def handle_mcp_line(
    line: str,
    tool_caller: Callable[[str, dict[str, Any] | None], dict[str, Any]] = call_mcp_tool,
) -> dict[str, Any] | None:
    try:
        request = json.loads(line)
    except json.JSONDecodeError as error:
        return build_json_rpc_error(
            request_id=None,
            code=PARSE_ERROR,
            message=str(error),
        )

    return handle_mcp_request(
        request,
        tool_caller=tool_caller,
    )


def run_stdio_server(
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
    tool_caller: Callable[[str, dict[str, Any] | None], dict[str, Any]] = call_mcp_tool,
) -> None:
    for line in input_stream:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        response = handle_mcp_line(
            stripped_line,
            tool_caller=tool_caller,
        )

        if response is None:
            continue

        output_stream.write(
            json.dumps(
                response,
                ensure_ascii=False,
            )
        )
        output_stream.write("\n")
        output_stream.flush()


def main() -> None:
    run_stdio_server()


if __name__ == "__main__":
    main()
