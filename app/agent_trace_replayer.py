import json

from pathlib import Path
from typing import Any

from app.storage_repositories import TraceRepository


def load_agent_trace_records(
    file_path: str,
    trace_repository: TraceRepository | None = None,
) -> list[dict[str, Any]]:
    if trace_repository is not None:
        return [
            {
                "line_number": index,
                "trace": trace,
            }
            for index, trace in enumerate(
                trace_repository.load_all(),
                start=1,
            )
        ]

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Agent trace file does not exist: {file_path}")

    records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                trace = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Agent trace line {line_number} is not valid JSON"
                ) from error

            records.append(
                {
                    "line_number": line_number,
                    "trace": trace,
                }
            )

    return records


def replay_agent_trace(
    file_path: str,
    line_number: int | None = None,
    trace_repository: TraceRepository | None = None,
) -> dict[str, Any]:
    records = load_agent_trace_records(
        file_path,
        trace_repository=trace_repository,
    )

    if not records:
        raise ValueError("Agent trace file contains no replayable records")

    if line_number is None:
        record = records[-1]
    else:
        if line_number <= 0:
            raise ValueError("line_number must be greater than 0")

        matching_records = [
            record
            for record in records
            if record["line_number"] == line_number
        ]

        if not matching_records:
            raise ValueError(
                f"Agent trace line {line_number} was not found"
            )

        record = matching_records[0]

    trace = record["trace"]
    result = trace.get("result", {})
    tool_traces = result.get("tool_traces", [])
    token_usage = result.get("token_usage", {})
    cost_estimate = result.get("cost_estimate", {})

    successful_tool_calls = sum(
        1
        for tool_trace in tool_traces
        if tool_trace.get("success") is True
    )
    failed_tool_calls = sum(
        1
        for tool_trace in tool_traces
        if tool_trace.get("success") is False
    )
    total_duration_ms = sum(
        float(tool_trace.get("duration_ms", 0.0) or 0.0)
        for tool_trace in tool_traces
    )

    return {
        "line_number": record["line_number"],
        "created_at": trace.get("created_at"),
        "user_message": trace.get("user_message", ""),
        "final_output": result.get("final_output", ""),
        "steps": result.get("steps", 0),
        "tool_traces": tool_traces,
        "tool_call_count": len(tool_traces),
        "successful_tool_calls": successful_tool_calls,
        "failed_tool_calls": failed_tool_calls,
        "total_duration_ms": total_duration_ms,
        "token_usage": {
            "prompt_tokens": token_usage.get("prompt_tokens", 0),
            "completion_tokens": token_usage.get("completion_tokens", 0),
            "total_tokens": token_usage.get("total_tokens", 0),
        },
        "cost_estimate": {
            "input_cost": cost_estimate.get("input_cost", 0),
            "output_cost": cost_estimate.get("output_cost", 0),
            "total_cost": cost_estimate.get("total_cost", 0),
            "currency": cost_estimate.get("currency"),
        },
    }


def compare_agent_trace_replays(
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    baseline_tools = extract_tool_sequence(baseline)
    current_tools = extract_tool_sequence(current)
    baseline_successes = extract_tool_success_sequence(baseline)
    current_successes = extract_tool_success_sequence(current)

    baseline_tokens = baseline["token_usage"]["total_tokens"]
    current_tokens = current["token_usage"]["total_tokens"]
    baseline_cost = baseline["cost_estimate"]["total_cost"]
    current_cost = current["cost_estimate"]["total_cost"]

    return {
        "baseline_line_number": baseline["line_number"],
        "current_line_number": current["line_number"],
        "same_user_message": (
            baseline["user_message"] == current["user_message"]
        ),
        "same_final_output": (
            baseline["final_output"] == current["final_output"]
        ),
        "same_tool_sequence": baseline_tools == current_tools,
        "baseline_tool_sequence": baseline_tools,
        "current_tool_sequence": current_tools,
        "same_tool_success_sequence": baseline_successes == current_successes,
        "baseline_tool_success_sequence": baseline_successes,
        "current_tool_success_sequence": current_successes,
        "tool_call_count_delta": (
            current["tool_call_count"] - baseline["tool_call_count"]
        ),
        "failed_tool_call_delta": (
            current["failed_tool_calls"] - baseline["failed_tool_calls"]
        ),
        "total_tokens_delta": current_tokens - baseline_tokens,
        "total_cost_delta": current_cost - baseline_cost,
        "duration_ms_delta": (
            current["total_duration_ms"] - baseline["total_duration_ms"]
        ),
        "regressions": detect_trace_replay_regressions(
            baseline=baseline,
            current=current,
            baseline_tools=baseline_tools,
            current_tools=current_tools,
            baseline_successes=baseline_successes,
            current_successes=current_successes,
        ),
    }


def compare_agent_trace_records(
    baseline_file_path: str,
    current_file_path: str,
    baseline_line_number: int | None = None,
    current_line_number: int | None = None,
    baseline_trace_repository: TraceRepository | None = None,
    current_trace_repository: TraceRepository | None = None,
) -> dict[str, Any]:
    baseline = replay_agent_trace(
        baseline_file_path,
        line_number=baseline_line_number,
        trace_repository=baseline_trace_repository,
    )
    current = replay_agent_trace(
        current_file_path,
        line_number=current_line_number,
        trace_repository=current_trace_repository,
    )

    return compare_agent_trace_replays(
        baseline=baseline,
        current=current,
    )


def extract_tool_sequence(
    replay: dict[str, Any],
) -> list[str]:
    return [
        tool_trace.get("tool_name", "")
        for tool_trace in replay["tool_traces"]
    ]


def extract_tool_success_sequence(
    replay: dict[str, Any],
) -> list[bool | None]:
    return [
        tool_trace.get("success")
        for tool_trace in replay["tool_traces"]
    ]


def detect_trace_replay_regressions(
    baseline: dict[str, Any],
    current: dict[str, Any],
    baseline_tools: list[str],
    current_tools: list[str],
    baseline_successes: list[bool | None],
    current_successes: list[bool | None],
) -> list[str]:
    regressions = []

    if baseline_tools != current_tools:
        regressions.append("tool_sequence_changed")

    if (
        baseline["failed_tool_calls"] == 0
        and current["failed_tool_calls"] > 0
    ):
        regressions.append("tool_failures_introduced")

    if baseline_successes != current_successes:
        regressions.append("tool_success_sequence_changed")

    if baseline["final_output"] and not current["final_output"]:
        regressions.append("final_output_became_empty")

    return regressions
