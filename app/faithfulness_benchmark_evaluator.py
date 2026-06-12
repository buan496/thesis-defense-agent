import json
from collections.abc import Callable

from app.faithfulness_evaluator import evaluate_faithfulness
from app.llm import chat_with_llm


def evaluate_faithfulness_benchmark(
    benchmark_path: str,
    llm_fn: Callable[[str], str] = chat_with_llm,
) -> dict:
    with open(benchmark_path, encoding="utf-8") as file:
        benchmark = json.load(file)

    if not benchmark:
        raise ValueError("Faithfulness benchmark 不能为空")

    results = []
    passed_count = 0

    for item in benchmark:
        judge_result = evaluate_faithfulness(
            question=item["question"],
            answer=item["answer"],
            evidence=item["evidence"],
            llm_fn=llm_fn,
        )

        prediction_correct = (
            judge_result["passed"]
            == item["expected_passed"]
        )

        if prediction_correct:
            passed_count += 1

        results.append(
            {
                "name": item["name"],
                "expected_passed": item["expected_passed"],
                "actual_passed": judge_result["passed"],
                "prediction_correct": prediction_correct,
                "score": judge_result["score"],
                "reason": judge_result["reason"],
                "unsupported_claims": (
                    judge_result["unsupported_claims"]
                ),
                "contradictions": judge_result["contradictions"],
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