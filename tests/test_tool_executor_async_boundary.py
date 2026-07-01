import asyncio
import json
from types import SimpleNamespace

from app.tool_executor import (
    TOOL_REGISTRY,
    execute_tool_call,
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


def test_execute_tool_call_async_awaits_async_tool(monkeypatch):
    calls = []

    async def native_async_tool(value):
        await asyncio.sleep(0)
        calls.append(value)
        return {"value": value, "mode": "async"}

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "native_async_tool",
        native_async_tool,
    )

    tool_call = create_tool_call(
        name="native_async_tool",
        arguments='{"value": "ok"}',
    )

    async def scenario():
        result_text = await execute_tool_call_async(tool_call)

        assert json.loads(result_text) == {
            "value": "ok",
            "mode": "async",
        }
        assert calls == ["ok"]

    asyncio.run(scenario())


def test_execute_tool_call_async_times_out_async_tool(monkeypatch):
    async def slow_async_tool():
        await asyncio.sleep(1)
        return {"ok": True}

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "slow_async_tool",
        slow_async_tool,
    )
    monkeypatch.setattr(
        "app.tool_executor.TOOL_TIMEOUT_SECONDS",
        0.01,
    )
    monkeypatch.setattr(
        "app.tool_executor.TOOL_MAX_RETRIES",
        0,
    )

    tool_call = create_tool_call(
        name="slow_async_tool",
        arguments="{}",
    )

    async def scenario():
        result_text = await execute_tool_call_safely_async(tool_call)
        data = json.loads(result_text)

        assert data["success"] is False
        assert data["error_type"] == "TimeoutError"
        assert "timed out" in data["message"]
        assert data["tool_name"] == "slow_async_tool"

    asyncio.run(scenario())


def test_execute_tool_call_rejects_async_tool_in_sync_entry(monkeypatch):
    async def native_async_tool():
        return {"ok": True}

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "sync_entry_async_tool",
        native_async_tool,
    )

    tool_call = create_tool_call(
        name="sync_entry_async_tool",
        arguments="{}",
    )

    try:
        execute_tool_call(tool_call)
    except TypeError as error:
        assert "execute_tool_call_async" in str(error)
    else:
        raise AssertionError("sync entry accepted async tool")


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
