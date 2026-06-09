from types import SimpleNamespace

import pytest

from app.tool_executor import execute_tool_call


def create_tool_call(name: str, arguments: str):
    return SimpleNamespace(
        function=SimpleNamespace(
            name=name,
            arguments=arguments,
        )
    )


def test_execute_tool_call_rejects_unknown_tool():
    tool_call = create_tool_call(
        name="delete_all_files",
        arguments="{}",
    )

    with pytest.raises(ValueError, match="未知工具"):
        execute_tool_call(tool_call)


def test_execute_tool_call_rejects_invalid_json():
    tool_call = create_tool_call(
        name="search_thesis",
        arguments="{invalid json}",
    )

    with pytest.raises(ValueError, match="工具参数不是合法 JSON"):
        execute_tool_call(tool_call)