import json
from collections.abc import Callable

from app.agent import run_agent
from app.agent_models import AgentResult


def evaluate_agent_routing(
    benchmark_path: str,
    agent_fn: Callable[[str], AgentResult] = run_agent,
) -> dict:
    with open(benchmark_path, encoding="utf-8") as file:
        benchmark = json.load(file)

    if not benchmark:
        raise ValueError("Agent 路由 benchmark 不能为空")

    results = []
    passed_count = 0

    for item in benchmark:
        user_message = item["user_message"]
        expected_tools = item["expected_tools"]

        try:
            agent_result = agent_fn(user_message)
            actual_tools = [
                trace.tool_name
                for trace in agent_result.tool_traces
            ]
            error = None
        except Exception as exception:
            actual_tools = []
            error = f"{type(exception).__name__}: {exception}"

        passed = actual_tools == expected_tools

        if passed:
            passed_count += 1

        results.append(
            {
                "user_message": user_message,
                "expected_tools": expected_tools,
                "actual_tools": actual_tools,
                "passed": passed,
                "error": error,
            }
        )

    total = len(results)

    return {
        "benchmark_path": benchmark_path,
        "total": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "accuracy": passed_count / total,
        "results": results,
    }
