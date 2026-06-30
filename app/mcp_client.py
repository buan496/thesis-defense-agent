import json
import subprocess
from dataclasses import dataclass
from typing import Any, TextIO


JSON_RPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2024-11-05"


class McpClientError(RuntimeError):
    pass


@dataclass
class McpClientConfig:
    command: list[str]
    client_name: str = "thesis-defense-agent-client"
    client_version: str = "0.1.0"
    request_timeout_seconds: float = 30.0


@dataclass
class McpTool:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class McpClientResult:
    content: list[dict[str, Any]]
    is_error: bool = False

    @property
    def text(self) -> str:
        texts = []
        for item in self.content:
            if item.get("type") == "text":
                texts.append(str(item.get("text", "")))
        return "\n".join(texts)


def build_json_rpc_request(
    request_id: int | str,
    method: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "jsonrpc": JSON_RPC_VERSION,
        "id": request_id,
        "method": method,
        "params": params or {},
    }


def build_initialized_notification() -> dict[str, Any]:
    return {
        "jsonrpc": JSON_RPC_VERSION,
        "method": "notifications/initialized",
        "params": {},
    }


def parse_json_rpc_response(
    response: dict[str, Any],
    expected_id: int | str,
) -> dict[str, Any]:
    if response.get("jsonrpc") != JSON_RPC_VERSION:
        raise McpClientError("response jsonrpc must be 2.0")

    if response.get("id") != expected_id:
        raise McpClientError(
            f"unexpected response id: {response.get('id')}"
        )

    if "error" in response:
        error = response["error"]
        if isinstance(error, dict):
            message = error.get("message", "MCP server returned an error")
            code = error.get("code", "unknown")
            raise McpClientError(f"MCP error {code}: {message}")
        raise McpClientError("MCP server returned an invalid error")

    result = response.get("result")
    if not isinstance(result, dict):
        raise McpClientError("response.result must be an object")

    return result


def parse_mcp_tools(result: dict[str, Any]) -> list[McpTool]:
    raw_tools = result.get("tools", [])
    if not isinstance(raw_tools, list):
        raise McpClientError("tools/list result.tools must be a list")

    tools = []
    for raw_tool in raw_tools:
        if not isinstance(raw_tool, dict):
            continue

        name = raw_tool.get("name")
        if not isinstance(name, str) or not name:
            continue

        description = raw_tool.get("description", "")
        input_schema = raw_tool.get("inputSchema", {})
        tools.append(
            McpTool(
                name=name,
                description=description if isinstance(description, str) else "",
                input_schema=input_schema if isinstance(input_schema, dict) else {},
            )
        )

    return tools


def parse_tool_call_result(result: dict[str, Any]) -> McpClientResult:
    content = result.get("content", [])
    if not isinstance(content, list):
        raise McpClientError("tools/call result.content must be a list")

    is_error = result.get("isError", False)
    return McpClientResult(
        content=[
            item for item in content
            if isinstance(item, dict)
        ],
        is_error=bool(is_error),
    )


class McpStdioClient:
    def __init__(
        self,
        config: McpClientConfig,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
        process: subprocess.Popen | None = None,
    ):
        self.config = config
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.process = process
        self._next_request_id = 1

    def __enter__(self) -> "McpStdioClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def start(self) -> None:
        if self.input_stream is not None and self.output_stream is not None:
            return

        self.process = subprocess.Popen(
            self.config.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

        if self.process.stdin is None or self.process.stdout is None:
            raise McpClientError("failed to open MCP stdio streams")

        self.input_stream = self.process.stdout
        self.output_stream = self.process.stdin

    def close(self) -> None:
        if self.output_stream is not None:
            self.output_stream.close()

        if self.process is not None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()

    def _request_id(self) -> int:
        request_id = self._next_request_id
        self._next_request_id += 1
        return request_id

    def send_notification(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        request = {
            "jsonrpc": JSON_RPC_VERSION,
            "method": method,
            "params": params or {},
        }
        self._write_json_line(request)

    def send_request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_id = self._request_id()
        request = build_json_rpc_request(
            request_id=request_id,
            method=method,
            params=params,
        )
        self._write_json_line(request)
        response = self._read_json_line()
        return parse_json_rpc_response(
            response,
            expected_id=request_id,
        )

    def initialize(self) -> dict[str, Any]:
        result = self.send_request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": self.config.client_name,
                    "version": self.config.client_version,
                },
            },
        )
        self.send_notification(
            "notifications/initialized",
            {},
        )
        return result

    def list_tools(self) -> list[McpTool]:
        return parse_mcp_tools(
            self.send_request("tools/list", {})
        )

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> McpClientResult:
        if not name.strip():
            raise ValueError("tool name must not be empty")

        result = self.send_request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments or {},
            },
        )
        return parse_tool_call_result(result)

    def _write_json_line(self, payload: dict[str, Any]) -> None:
        if self.output_stream is None:
            raise McpClientError("MCP output stream is not available")

        self.output_stream.write(
            json.dumps(payload, ensure_ascii=False) + "\n"
        )
        self.output_stream.flush()

    def _read_json_line(self) -> dict[str, Any]:
        if self.input_stream is None:
            raise McpClientError("MCP input stream is not available")

        line = self.input_stream.readline()
        if not line:
            raise McpClientError("MCP server closed stdout")

        try:
            response = json.loads(line)
        except json.JSONDecodeError as error:
            raise McpClientError(f"invalid JSON-RPC response: {error}") from error

        if not isinstance(response, dict):
            raise McpClientError("JSON-RPC response must be an object")

        return response
