import json

from app.tools import search_thesis


TOOL_REGISTRY = {
    "search_thesis": search_thesis,
}


def execute_tool_call(tool_call) -> str:
    tool_name = tool_call.function.name

    tool_function = TOOL_REGISTRY.get(tool_name)

    if tool_function is None:
        raise ValueError(f"未知工具：{tool_name}")

    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as error:
        raise ValueError("工具参数不是合法 JSON") from error

    result = tool_function(**arguments)

    return json.dumps(
        result,
        ensure_ascii=False,
    )