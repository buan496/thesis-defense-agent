import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from app.tool_executor import (
    ALLOWED_TOOL_PERMISSIONS,
    TOOL_REGISTRY,
    execute_tool_call,
    resolve_tool_execution_config,
    validate_tool_execution_metadata,
)
from app.tool_registry import (
    REGISTERED_TOOLS,
    RegisteredTool,
    get_registered_tool,
)


def create_tool_call(name: str, arguments: str):
    return SimpleNamespace(
        function=SimpleNamespace(
            name=name,
            arguments=arguments,
        )
    )


def test_allowed_tool_permissions_are_explicit():
    assert ALLOWED_TOOL_PERMISSIONS == {
        "read",
        "llm_generate",
        "llm_evaluate",
    }


def test_validate_tool_execution_metadata_rejects_disabled_tool():
    metadata = replace(
        get_registered_tool("search_thesis").metadata,
        enabled=False,
    )

    with pytest.raises(ValueError, match="工具已禁用"):
        validate_tool_execution_metadata(metadata)


def test_validate_tool_execution_metadata_rejects_unknown_permission():
    metadata = replace(
        get_registered_tool("search_thesis").metadata,
        permission="write",
    )

    with pytest.raises(ValueError, match="工具权限不允许"):
        validate_tool_execution_metadata(metadata)


def test_execute_tool_call_rejects_disabled_registered_tool(monkeypatch):
    def disabled_tool():
        return {"ok": True}

    metadata = replace(
        get_registered_tool("search_thesis").metadata,
        name="disabled_tool",
        enabled=False,
    )
    registered_tool = RegisteredTool(
        metadata=metadata,
        function=disabled_tool,
        openai_schema={},
    )

    monkeypatch.setitem(
        REGISTERED_TOOLS,
        "disabled_tool",
        registered_tool,
    )
    monkeypatch.setitem(
        TOOL_REGISTRY,
        "disabled_tool",
        disabled_tool,
    )

    tool_call = create_tool_call(
        name="disabled_tool",
        arguments="{}",
    )

    with pytest.raises(ValueError, match="工具已禁用"):
        execute_tool_call(tool_call)


def test_registered_metadata_overrides_legacy_tool_registry(monkeypatch):
    def disabled_tool():
        return {"ok": True}

    metadata = replace(
        get_registered_tool("search_thesis").metadata,
        name="disabled_tool",
        enabled=False,
    )

    monkeypatch.setitem(
        REGISTERED_TOOLS,
        "disabled_tool",
        RegisteredTool(
            metadata=metadata,
            function=disabled_tool,
            openai_schema={},
        ),
    )
    monkeypatch.setitem(
        TOOL_REGISTRY,
        "disabled_tool",
        disabled_tool,
    )

    with pytest.raises(ValueError, match="工具已禁用"):
        resolve_tool_execution_config("disabled_tool")


def test_resolve_tool_execution_config_uses_registered_metadata(monkeypatch):
    calls = []

    def metadata_tool():
        calls.append("called")

        if len(calls) == 1:
            raise RuntimeError("temporary")

        return {"text": "a" * 50}

    metadata = replace(
        get_registered_tool("search_thesis").metadata,
        name="metadata_tool",
        timeout_seconds=None,
        retry_count=1,
        result_max_characters=12,
    )
    registered_tool = RegisteredTool(
        metadata=metadata,
        function=metadata_tool,
        openai_schema={},
    )

    monkeypatch.setitem(
        REGISTERED_TOOLS,
        "metadata_tool",
        registered_tool,
    )

    execution_config = resolve_tool_execution_config("metadata_tool")

    assert execution_config["function"] is metadata_tool
    assert execution_config["max_retries"] == 1
    assert execution_config["timeout_seconds"] is None
    assert execution_config["result_max_characters"] == 12

    tool_call = create_tool_call(
        name="metadata_tool",
        arguments="{}",
    )

    result_text = execute_tool_call(tool_call)
    data = json.loads(result_text)

    assert calls == ["called", "called"]
    assert data["truncated"] is True
    assert data["max_characters"] == 12
