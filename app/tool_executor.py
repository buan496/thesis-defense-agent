from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json

from app.config import (
    TOOL_MAX_RETRIES,
    TOOL_RESULT_MAX_CHARACTERS,
    TOOL_TIMEOUT_SECONDS,
)
from app.async_boundary import run_sync_in_thread
from app.tool_registry import (
    REGISTERED_TOOLS,
    ToolMetadata,
    build_tool_function_registry,
)


TOOL_REGISTRY = build_tool_function_registry()
ALLOWED_TOOL_PERMISSIONS = {
    "read",
    "llm_generate",
    "llm_evaluate",
}


def validate_tool_execution_metadata(
    metadata: ToolMetadata,
) -> None:
    if not metadata.enabled:
        raise ValueError(f"工具已禁用：{metadata.name}")

    if metadata.permission not in ALLOWED_TOOL_PERMISSIONS:
        raise ValueError(
            f"工具权限不允许：{metadata.name} "
            f"permission={metadata.permission}"
        )

    if metadata.retry_count < 0:
        raise ValueError(
            f"工具 retry_count 不合法：{metadata.name}"
        )

    if metadata.result_max_characters <= 0:
        raise ValueError(
            f"工具 result_max_characters 不合法：{metadata.name}"
        )

    if (
        metadata.timeout_seconds is not None
        and metadata.timeout_seconds <= 0
    ):
        raise ValueError(
            f"工具 timeout_seconds 不合法：{metadata.name}"
        )


def resolve_tool_execution_config(
    tool_name: str,
) -> dict:
    registered_tool = REGISTERED_TOOLS.get(tool_name)

    if registered_tool is not None:
        validate_tool_execution_metadata(
            registered_tool.metadata,
        )

        return {
            "function": registered_tool.function,
            "max_retries": registered_tool.metadata.retry_count,
            "timeout_seconds": registered_tool.metadata.timeout_seconds,
            "result_max_characters": (
                registered_tool.metadata.result_max_characters
            ),
        }

    tool_function = TOOL_REGISTRY.get(tool_name)

    if tool_function is None:
        raise ValueError(f"未知工具：{tool_name}")

    return {
        "function": tool_function,
        "max_retries": TOOL_MAX_RETRIES,
        "timeout_seconds": TOOL_TIMEOUT_SECONDS,
        "result_max_characters": TOOL_RESULT_MAX_CHARACTERS,
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
    execution_config = resolve_tool_execution_config(tool_name)

    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as error:
        raise ValueError("工具参数不是合法 JSON") from error

    result = execute_tool_function_with_retry(
        execution_config["function"],
        arguments,
        max_retries=execution_config["max_retries"],
        timeout_seconds=execution_config["timeout_seconds"],
    )

    result_text = json.dumps(
        result,
        ensure_ascii=False,
    )

    return limit_tool_result_text(
        result_text,
        max_characters=execution_config["result_max_characters"],
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


async def execute_tool_call_async(tool_call) -> str:
    return await run_sync_in_thread(
        execute_tool_call,
        tool_call,
    )


async def execute_tool_call_safely_async(tool_call) -> str:
    return await run_sync_in_thread(
        execute_tool_call_safely,
        tool_call,
    )
