from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json

from app.config import (
    TOOL_MAX_RETRIES,
    TOOL_RESULT_MAX_CHARACTERS,
    TOOL_TIMEOUT_SECONDS,
)
from app.tools import (
    create_defense_questions,
    evaluate_student_answer,
    generate_follow_up,
    query_training_record,
    search_thesis,
)


TOOL_REGISTRY = {
    "create_defense_questions": create_defense_questions,
    "evaluate_student_answer": evaluate_student_answer,
    "generate_follow_up": generate_follow_up,
    "query_training_record": query_training_record,
    "search_thesis": search_thesis,
}


def build_tool_error_result(
    error: Exception,
    tool_name: str | None = None,
) -> str:
    result = {
        "success": False,
        "error_type": type(error).__name__,
        "message": str(error),
    }

    if tool_name is not None:
        result["tool_name"] = tool_name

    return json.dumps(
        result,
        ensure_ascii=False,
    )


def limit_tool_result_text(
    text: str,
    max_characters: int,
) -> str:
    if max_characters <= 0:
        raise ValueError("max_characters must be greater than 0")

    if len(text) <= max_characters:
        return text

    limited_result = {
        "truncated": True,
        "original_characters": len(text),
        "max_characters": max_characters,
        "content": text[:max_characters],
    }

    return json.dumps(
        limited_result,
        ensure_ascii=False,
    )


def execute_tool_function_with_retry(
    tool_function,
    arguments: dict,
    max_retries: int,
    timeout_seconds: float | None = None,
):
    if max_retries < 0:
        raise ValueError("max_retries must be greater than or equal to 0")

    last_error = None

    for _ in range(max_retries + 1):
        try:
            return execute_tool_function_with_timeout(
                tool_function,
                arguments,
                timeout_seconds=timeout_seconds,
            )
        except Exception as error:
            last_error = error

    raise last_error


def execute_tool_function_with_timeout(
    tool_function,
    arguments: dict,
    timeout_seconds: float | None,
):
    if timeout_seconds is None:
        return tool_function(**arguments)

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0")

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(tool_function, **arguments)

    try:
        return future.result(timeout=timeout_seconds)
    except TimeoutError as error:
        future.cancel()
        raise TimeoutError(
            f"tool execution timed out after {timeout_seconds} seconds"
        ) from error
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def execute_tool_call(tool_call) -> str:
    tool_name = tool_call.function.name

    tool_function = TOOL_REGISTRY.get(tool_name)

    if tool_function is None:
        raise ValueError(f"未知工具：{tool_name}")

    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as error:
        raise ValueError("工具参数不是合法 JSON") from error

    result = execute_tool_function_with_retry(
        tool_function,
        arguments,
        max_retries=TOOL_MAX_RETRIES,
        timeout_seconds=TOOL_TIMEOUT_SECONDS,
    )

    result_text = json.dumps(
        result,
        ensure_ascii=False,
    )

    return limit_tool_result_text(
        result_text,
        max_characters=TOOL_RESULT_MAX_CHARACTERS,
    )


def execute_tool_call_safely(tool_call) -> str:
    tool_name = getattr(
        getattr(tool_call, "function", None),
        "name",
        None,
    )

    try:
        return execute_tool_call(tool_call)
    except Exception as error:
        return build_tool_error_result(
            error,
            tool_name=tool_name,
        )
