from app.agent_routing_evaluator import evaluate_agent_routing
from app.config import AGENT_ROUTING_BENCHMARK_PATH


report = evaluate_agent_routing(
    benchmark_path=AGENT_ROUTING_BENCHMARK_PATH,
)

for item in report["results"]:
    print("USER MESSAGE:", item["user_message"])
    print("EXPECTED TOOLS:", item["expected_tools"])
    print("ACTUAL TOOLS:", item["actual_tools"])
    print("ROUTING PASSED:", item["routing_passed"])
    print("ARGUMENTS PASSED:", item["arguments_passed"])
    print("COMPLETION PASSED:", item["completion_passed"])
    print("GROUNDING PASSED:", item["grounding_passed"])
    print(
        "COMPLETION ERRORS:",
        item["completion_check"]["errors"],
    )
    print(
        "QUESTION COUNT:",
        item["completion_check"]["question_count"],
    )
    print(
        "GROUNDEDNESS SCORE:",
        item["grounding_check"]["score"],
    )
    print(
        "GROUNDING ERRORS:",
        item["grounding_check"]["errors"],
    )
    print(
        "FAITHFULNESS EVALUATED:",
        item["faithfulness_check"]["evaluated"],
    )
    print(
        "FAITHFULNESS SCORE:",
        item["faithfulness_check"]["score"],
    )
    print(
        "FAITHFULNESS PASSED:",
        item["faithfulness_passed"],
    )
    print(
        "FAITHFULNESS REASON:",
        item["faithfulness_check"]["reason"],
    )
    print(
        "UNSUPPORTED CLAIMS:",
        item["faithfulness_check"]["unsupported_claims"],
    )
    print(
        "CONTRADICTIONS:",
        item["faithfulness_check"]["contradictions"],
    )

    for claim in item["grounding_check"]["claims"]:
        print("GROUNDING CLAIM:", claim["claim"])
        print("CLAIM IN ANSWER:", claim["claim_in_answer"])
        print("EVIDENCE FOUND:", claim["evidence_found"])
        print("SUPPORTED:", claim["supported"])

    for check in item["argument_checks"]:
        print("ARGUMENT TOOL:", check["tool_name"])
        print("ARGUMENTS:", check["arguments"])
        print("ARGUMENT PASSED:", check["passed"])

        if check["errors"]:
            print("ARGUMENT ERRORS:", check["errors"])

    print("PASSED:", item["passed"])

    if item["error"] is not None:
        print("ERROR:", item["error"])

    print("-" * 40)

print("TOTAL:", report["total"])
print("PASSED:", report["passed"])
print("FAILED:", report["failed"])
print("TOOL ROUTING ACCURACY:", report["routing_accuracy"])
print("TOOL ARGUMENT ACCURACY:", report["argument_accuracy"])
print("TASK COMPLETION RATE:", report["completion_rate"])
print(
    "END-TO-END SUCCESS RATE:",
    report["end_to_end_success_rate"],
)
print("GROUNDEDNESS SCORE:", report["groundedness_score"])
print("GROUNDED TASK RATE:", report["grounded_task_rate"])
print(
    "END-TO-END GROUNDED SUCCESS RATE:",
    report["end_to_end_grounded_success_rate"],
)
print("FAITHFULNESS CASES:", report["faithfulness_cases"])
print("FAITHFULNESS SCORE:", report["faithfulness_score"])
print(
    "FAITHFULNESS PASS RATE:",
    report["faithfulness_pass_rate"],
)
print(
    "END-TO-END FAITHFUL SUCCESS RATE:",
    report["end_to_end_faithful_success_rate"],
)
