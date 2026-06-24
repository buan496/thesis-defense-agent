from dataclasses import asdict, dataclass
from typing import Any, Callable

from app.config import (
    TOOL_MAX_RETRIES,
    TOOL_RESULT_MAX_CHARACTERS,
    TOOL_TIMEOUT_SECONDS,
)
from app.tools import (
    ANSWER_EVALUATION_TOOL,
    DEFENSE_QUESTION_TOOL,
    FOLLOW_UP_TOOL,
    THESIS_SEARCH_TOOL,
    TRAINING_RECORD_TOOL,
    create_defense_questions,
    evaluate_student_answer,
    generate_follow_up,
    query_training_record,
    search_thesis,
)


@dataclass(frozen=True)
class ToolMetadata:
    name: str
    description: str
    permission: str
    owner: str
    enabled: bool
    timeout_seconds: float | None
    retry_count: int
    result_max_characters: int
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RegisteredTool:
    metadata: ToolMetadata
    function: Callable
    openai_schema: dict[str, Any]


def _metadata_from_openai_schema(
    schema: dict[str, Any],
    permission: str,
    owner: str = "thesis-defense-agent",
    enabled: bool = True,
    timeout_seconds: float | None = TOOL_TIMEOUT_SECONDS,
    retry_count: int = TOOL_MAX_RETRIES,
    result_max_characters: int = TOOL_RESULT_MAX_CHARACTERS,
    output_schema: dict[str, Any] | None = None,
) -> ToolMetadata:
    function_schema = schema["function"]

    return ToolMetadata(
        name=function_schema["name"],
        description=function_schema["description"],
        permission=permission,
        owner=owner,
        enabled=enabled,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
        result_max_characters=result_max_characters,
        input_schema=function_schema["parameters"],
        output_schema=output_schema or {"type": "object"},
    )


REGISTERED_TOOLS: dict[str, RegisteredTool] = {
    "search_thesis": RegisteredTool(
        metadata=_metadata_from_openai_schema(
            THESIS_SEARCH_TOOL,
            permission="read",
        ),
        function=search_thesis,
        openai_schema=THESIS_SEARCH_TOOL,
    ),
    "create_defense_questions": RegisteredTool(
        metadata=_metadata_from_openai_schema(
            DEFENSE_QUESTION_TOOL,
            permission="llm_generate",
        ),
        function=create_defense_questions,
        openai_schema=DEFENSE_QUESTION_TOOL,
    ),
    "evaluate_student_answer": RegisteredTool(
        metadata=_metadata_from_openai_schema(
            ANSWER_EVALUATION_TOOL,
            permission="llm_evaluate",
        ),
        function=evaluate_student_answer,
        openai_schema=ANSWER_EVALUATION_TOOL,
    ),
    "generate_follow_up": RegisteredTool(
        metadata=_metadata_from_openai_schema(
            FOLLOW_UP_TOOL,
            permission="llm_generate",
        ),
        function=generate_follow_up,
        openai_schema=FOLLOW_UP_TOOL,
    ),
    "query_training_record": RegisteredTool(
        metadata=_metadata_from_openai_schema(
            TRAINING_RECORD_TOOL,
            permission="read",
        ),
        function=query_training_record,
        openai_schema=TRAINING_RECORD_TOOL,
    ),
}


def list_registered_tools(
    include_disabled: bool = False,
) -> list[ToolMetadata]:
    tools = [
        registered_tool.metadata
        for registered_tool in REGISTERED_TOOLS.values()
        if include_disabled or registered_tool.metadata.enabled
    ]

    return sorted(
        tools,
        key=lambda metadata: metadata.name,
    )


def get_registered_tool(
    name: str,
) -> RegisteredTool:
    registered_tool = REGISTERED_TOOLS.get(name)

    if registered_tool is None:
        raise ValueError(f"未知工具：{name}")

    return registered_tool


def get_tool_function(
    name: str,
) -> Callable:
    registered_tool = get_registered_tool(name)

    if not registered_tool.metadata.enabled:
        raise ValueError(f"工具已禁用：{name}")

    return registered_tool.function


def build_tool_function_registry() -> dict[str, Callable]:
    return {
        name: registered_tool.function
        for name, registered_tool in REGISTERED_TOOLS.items()
        if registered_tool.metadata.enabled
    }


def build_openai_tool_schemas() -> list[dict[str, Any]]:
    return [
        registered_tool.openai_schema
        for registered_tool in REGISTERED_TOOLS.values()
        if registered_tool.metadata.enabled
    ]
