from app.agent_routing_evaluator import evaluate_agent_routing
from app.config import AGENT_ROUTING_BENCHMARK_PATH


report = evaluate_agent_routing(
    benchmark_path=AGENT_ROUTING_BENCHMARK_PATH,
)

for item in report["results"]:
    print("USER MESSAGE:", item["user_message"])
    print("EXPECTED TOOLS:", item["expected_tools"])
    print("ACTUAL TOOLS:", item["actual_tools"])
    print("PASSED:", item["passed"])

    if item["error"] is not None:
        print("ERROR:", item["error"])

    print("-" * 40)

print("TOTAL:", report["total"])
print("PASSED:", report["passed"])
print("FAILED:", report["failed"])
print("TOOL ROUTING ACCURACY:", report["accuracy"])
