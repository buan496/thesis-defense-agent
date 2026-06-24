import pytest

from app import cli
from app.tool_registry import (
    REGISTERED_TOOLS,
    ToolMetadata,
    build_openai_tool_schemas,
    build_tool_function_registry,
    get_registered_tool,
    get_tool_function,
    list_registered_tools,
)


def test_registered_tools_contain_search_thesis_metadata():
    registered_tool = get_registered_tool("search_thesis")
    metadata = registered_tool.metadata

    assert isinstance(metadata, ToolMetadata)
    assert metadata.name == "search_thesis"
    assert metadata.permission == "read"
    assert metadata.owner == "thesis-defense-agent"
    assert metadata.enabled is True
    assert metadata.timeout_seconds is not None
    assert metadata.retry_count >= 0
    assert metadata.result_max_characters > 0
    assert metadata.input_schema["type"] == "object"
    assert "query" in metadata.input_schema["required"]
    assert metadata.output_schema["type"] == "object"


def test_list_registered_tools_returns_sorted_enabled_metadata():
    tools = list_registered_tools()
    names = [tool.name for tool in tools]

    assert names == sorted(names)
    assert "search_thesis" in names
    assert "create_defense_questions" in names
    assert all(tool.enabled for tool in tools)


def test_get_registered_tool_rejects_unknown_tool():
    with pytest.raises(ValueError, match="未知工具"):
        get_registered_tool("unknown_tool")


def test_get_tool_function_returns_callable():
    tool_function = get_tool_function("search_thesis")

    assert callable(tool_function)


def test_build_tool_function_registry_matches_registered_tools():
    registry = build_tool_function_registry()

    assert set(registry) == {
        name
        for name, registered_tool in REGISTERED_TOOLS.items()
        if registered_tool.metadata.enabled
    }
    assert callable(registry["search_thesis"])


def test_build_openai_tool_schemas_returns_enabled_schemas():
    schemas = build_openai_tool_schemas()
    names = [
        schema["function"]["name"]
        for schema in schemas
    ]

    assert "search_thesis" in names
    assert "generate_follow_up" in names


def test_tool_metadata_to_dict():
    metadata = get_registered_tool("search_thesis").metadata

    data = metadata.to_dict()

    assert data["name"] == "search_thesis"
    assert data["permission"] == "read"
    assert data["input_schema"]["type"] == "object"


def test_list_tools_cli(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "list-tools",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "REGISTERED TOOLS" in output
    assert "COUNT:" in output
    assert "NAME: search_thesis" in output
    assert "PERMISSION: read" in output
    assert "TIMEOUT_SECONDS:" in output
    assert "RETRY_COUNT:" in output
    assert "RESULT_MAX_CHARACTERS:" in output
