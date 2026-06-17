import json

from collections import Counter
from pathlib import Path


def analyze_agent_traces(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Trace 文件不存在：{file_path}")

    run_count = 0
    tool_call_count = 0
    success_count = 0
    failure_count = 0
    total_duration_ms = 0.0
    tool_counts = Counter()

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    total_cost = 0.0
    currency = None

    most_expensive_run = None

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                trace = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Trace 第 {line_number} 行不是合法 JSON"
                ) from error

            run_count += 1

            result = trace.get("result", {})

            tool_traces = result.get("tool_traces", [])

            for tool_trace in tool_traces:
                tool_call_count += 1
                tool_counts[tool_trace["tool_name"]] += 1
                total_duration_ms += tool_trace["duration_ms"]

                if tool_trace["success"]:
                    success_count += 1
                else:
                    failure_count += 1

            token_usage = result.get("token_usage", {})
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get(
                "completion_tokens",
                0,
            )
            run_total_tokens = token_usage.get("total_tokens", 0)

            total_prompt_tokens += prompt_tokens
            total_completion_tokens += completion_tokens
            total_tokens += run_total_tokens

            cost_estimate = result.get("cost_estimate", {})
            run_cost = cost_estimate.get("total_cost", 0.0)
            run_currency = cost_estimate.get("currency")

            total_cost += run_cost

            if currency is None and run_currency:
                currency = run_currency

            if (
                most_expensive_run is None
                or run_cost > most_expensive_run["total_cost"]
            ):
                most_expensive_run = {
                    "line_number": line_number,
                    "created_at": trace.get("created_at"),
                    "user_message": trace.get("user_message"),
                    "total_cost": run_cost,
                    "total_tokens": run_total_tokens,
                    "currency": run_currency,
                }

    if tool_call_count == 0:
        success_rate = 0.0
        average_duration_ms = 0.0
    else:
        success_rate = success_count / tool_call_count
        average_duration_ms = total_duration_ms / tool_call_count

    if run_count == 0:
        average_total_tokens_per_run = 0.0
        average_cost_per_run = 0.0
        most_expensive_run = None
    else:
        average_total_tokens_per_run = total_tokens / run_count
        average_cost_per_run = total_cost / run_count

    return {
        "run_count": run_count,
        "tool_call_count": tool_call_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": success_rate,
        "average_duration_ms": average_duration_ms,
        "tool_counts": dict(tool_counts),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "average_total_tokens_per_run": average_total_tokens_per_run,
        "total_cost": total_cost,
        "average_cost_per_run": average_cost_per_run,
        "currency": currency,
        "most_expensive_run": most_expensive_run,
    }