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

            tool_traces = trace["result"]["tool_traces"]

            for tool_trace in tool_traces:
                tool_call_count += 1
                tool_counts[tool_trace["tool_name"]] += 1
                total_duration_ms += tool_trace["duration_ms"]

                if tool_trace["success"]:
                    success_count += 1
                else:
                    failure_count += 1

    if tool_call_count == 0:
        success_rate = 0.0
        average_duration_ms = 0.0
    else:
        success_rate = success_count / tool_call_count
        average_duration_ms = total_duration_ms / tool_call_count

    return {
        "run_count": run_count,
        "tool_call_count": tool_call_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": success_rate,
        "average_duration_ms": average_duration_ms,
        "tool_counts": dict(tool_counts),
    }