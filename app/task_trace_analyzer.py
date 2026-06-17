from typing import Any

from app.task_models import DefenseTask


def analyze_task_trace(task: DefenseTask) -> dict[str, Any]:
    completed_step_count = 0
    failed_step_count = 0
    pending_step_count = 0
    running_step_count = 0
    tool_call_count = 0
    successful_tool_call_count = 0
    failed_tool_call_count = 0
    total_duration_ms = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    total_cost = 0.0
    currency = None
    evidence_count = 0
    step_summaries = []

    current_step = task.get_current_step()

    for step in task.steps:
        if step.status == "completed":
            completed_step_count += 1
        elif step.status == "failed":
            failed_step_count += 1
        elif step.status == "pending":
            pending_step_count += 1
        elif step.status == "running":
            running_step_count += 1

        evidence_count += len(step.evidence)

        for tool_trace in step.tool_traces:
            tool_call_count += 1
            total_duration_ms += tool_trace.get("duration_ms", 0.0) or 0.0

            if tool_trace.get("success") is True:
                successful_tool_call_count += 1
            else:
                failed_tool_call_count += 1

        total_prompt_tokens += step.token_usage.get("prompt_tokens", 0)
        total_completion_tokens += step.token_usage.get(
            "completion_tokens",
            0,
        )
        total_tokens += step.token_usage.get("total_tokens", 0)
        total_cost += step.cost_estimate.get("total_cost", 0.0) or 0.0

        if currency is None and step.cost_estimate.get("currency"):
            currency = step.cost_estimate["currency"]

        step_summaries.append(
            {
                "step_id": step.step_id,
                "step_type": step.step_type,
                "status": step.status,
                "tool_call_count": len(step.tool_traces),
                "evidence_count": len(step.evidence),
                "total_tokens": step.token_usage.get("total_tokens", 0),
                "total_cost": step.cost_estimate.get("total_cost", 0.0),
                "error": step.error,
            }
        )

    if currency is None:
        currency = "CNY"

    return {
        "task_id": task.task_id,
        "topic": task.topic,
        "status": task.status,
        "current_step_id": task.current_step_id,
        "current_step_type": (
            current_step.step_type if current_step is not None else None
        ),
        "current_step_status": (
            current_step.status if current_step is not None else None
        ),
        "step_count": len(task.steps),
        "completed_step_count": completed_step_count,
        "failed_step_count": failed_step_count,
        "pending_step_count": pending_step_count,
        "running_step_count": running_step_count,
        "tool_call_count": tool_call_count,
        "successful_tool_call_count": successful_tool_call_count,
        "failed_tool_call_count": failed_tool_call_count,
        "total_duration_ms": total_duration_ms,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "currency": currency,
        "evidence_count": evidence_count,
        "step_summaries": step_summaries,
    }
