import json
import time
from dataclasses import asdict, dataclass

from app.config import SUB_AGENT_EXECUTION_TRACE_PATH
from app.sub_agent_permissions import validate_sub_agent_tool_call
from app.sub_agent_plan import (
    SubAgentExecutionPlan,
    create_sub_agent_execution_plan,
)
from app.sub_agent_execution_trace import save_sub_agent_execution_trace
from app.tool_executor import (
    build_tool_error_result,
    execute_tool_function_with_retry,
    limit_tool_result_text,
    resolve_tool_execution_config,
)


@dataclass(frozen=True)
class SubAgentExecutionResult:
    sub_agent_name: str
    tool_name: str
    success: bool
    plan: SubAgentExecutionPlan
    result_text: str
    duration_ms: float
    trace_saved: bool
    trace_path: str | None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["plan"] = self.plan.to_dict()
        return data


def execute_plan_tool(plan: SubAgentExecutionPlan) -> str:
    execution_config = resolve_tool_execution_config(plan.tool_name)

    result = execute_tool_function_with_retry(
        execution_config["function"],
        plan.tool_arguments,
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


def execute_sub_agent_plan(
    plan: SubAgentExecutionPlan,
    tool_runner=None,
    save_trace: bool = False,
    trace_file: str = SUB_AGENT_EXECUTION_TRACE_PATH,
) -> SubAgentExecutionResult:
    validate_sub_agent_tool_call(
        sub_agent_name=plan.sub_agent_name,
        tool_name=plan.tool_name,
    )

    start_time = time.perf_counter()
    runner = tool_runner or execute_plan_tool

    try:
        result_text = runner(plan)
        success = True
    except Exception as error:
        result_text = build_tool_error_result(
            error,
            tool_name=plan.tool_name,
        )
        success = False

    duration_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2,
    )
    trace_path = None

    result = SubAgentExecutionResult(
        sub_agent_name=plan.sub_agent_name,
        tool_name=plan.tool_name,
        success=success,
        plan=plan,
        result_text=result_text,
        duration_ms=duration_ms,
        trace_saved=save_trace,
        trace_path=None,
    )

    if save_trace:
        trace_path = str(
            save_sub_agent_execution_trace(
                result,
                file_path=trace_file,
            )
        )
        result = SubAgentExecutionResult(
            sub_agent_name=result.sub_agent_name,
            tool_name=result.tool_name,
            success=result.success,
            plan=result.plan,
            result_text=result.result_text,
            duration_ms=result.duration_ms,
            trace_saved=True,
            trace_path=trace_path,
        )

    return result


def execute_sub_agent_tool_call(
    sub_agent_name: str,
    tool_name: str,
    tool_arguments: dict,
    tool_runner=None,
    save_trace: bool = False,
    trace_file: str = SUB_AGENT_EXECUTION_TRACE_PATH,
) -> SubAgentExecutionResult:
    plan = create_sub_agent_execution_plan(
        sub_agent_name=sub_agent_name,
        tool_name=tool_name,
        tool_arguments=tool_arguments,
    )

    return execute_sub_agent_plan(
        plan,
        tool_runner=tool_runner,
        save_trace=save_trace,
        trace_file=trace_file,
    )
