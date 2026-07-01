import asyncio
import json
from types import SimpleNamespace

from app.tool_executor import (
    TOOL_REGISTRY,
    execute_tool_call_async,
    execute_tool_call_safely_async,
)


def create_tool_call(name: str, arguments: str):
    return SimpleNamespace(
        function=SimpleNamespace(
            name=name,
            arguments=arguments,
        )
    )


def test_execute_tool_call_async_returns_tool_result(monkeypatch):
    def fake_tool(value):
        return {"value": value}

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "async_fake_tool",
        fake_tool,
    )

    tool_call = create_tool_call(
        name="async_fake_tool",
        arguments='{"value": "ok"}',
    )

    async def scenario():
        result_text = await execute_tool_call_async(tool_call)

        assert json.loads(result_text) == {"value": "ok"}

    asyncio.run(scenario())


def test_execute_tool_call_safely_async_wraps_error(monkeypatch):
    def broken_tool():
        raise RuntimeError("temporary failure")

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "async_broken_tool",
        broken_tool,
    )
    monkeypatch.setattr(
        "app.tool_executor.TOOL_MAX_RETRIES",
        0,
    )

    tool_call = create_tool_call(
        name="async_broken_tool",
        arguments="{}",
    )

    async def scenario():
        result_text = await execute_tool_call_safely_async(tool_call)
        data = json.loads(result_text)

        assert data["success"] is False
        assert data["error_type"] == "RuntimeError"
        assert data["message"] == "temporary failure"
        assert data["tool_name"] == "async_broken_tool"

    asyncio.run(scenario())
