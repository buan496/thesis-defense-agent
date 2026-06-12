from collections.abc import Callable

from app.faithfulness_benchmark_evaluator import (
    evaluate_faithfulness_benchmark,
)
from app.llm import chat_with_llm


def evaluate_faithfulness_stability(
    benchmark_path: str,
    repeat_count: int = 3,
    llm_fn: Callable[[str], str] = chat_with_llm,
) -> dict:
    if repeat_count < 2:
        raise ValueError("repeat_count 必须至少为 2")

    predictions = {}
    runs = []

    for run_number in range(1, repeat_count + 1):
        report = evaluate_faithfulness_benchmark(
            benchmark_path=benchmark_path,
            llm_fn=llm_fn,
        )
        runs.append(
            {
                "run_number": run_number,
                "accuracy": report["accuracy"],
                "results": report["results"],
            }
        )

        for item in report["results"]:
            predictions.setdefault(
                item["name"],
                {
                    "expected_passed": item["expected_passed"],
                    "values": [],
                },
            )
            predictions[item["name"]]["values"].append(
                item["actual_passed"]
            )

    results = []
    agreement_scores = []
    unanimous_count = 0
    majority_correct_count = 0

    for name, data in predictions.items():
        values = data["values"]
        true_count = values.count(True)
        false_count = values.count(False)

        majority_prediction = true_count > false_count
        agreement_score = max(
            true_count,
            false_count,
        ) / repeat_count
        unanimous = true_count == repeat_count or false_count == repeat_count
        majority_correct = (
            majority_prediction == data["expected_passed"]
        )

        agreement_scores.append(agreement_score)

        if unanimous:
            unanimous_count += 1

        if majority_correct:
            majority_correct_count += 1

        results.append(
            {
                "name": name,
                "expected_passed": data["expected_passed"],
                "predictions": values,
                "majority_prediction": majority_prediction,
                "agreement_score": agreement_score,
                "unanimous": unanimous,
                "majority_correct": majority_correct,
            }
        )

    total = len(results)

    return {
        "benchmark_path": benchmark_path,
        "repeat_count": repeat_count,
        "total": total,
        "average_agreement": sum(agreement_scores) / total,
        "unanimous_rate": unanimous_count / total,
        "majority_accuracy": majority_correct_count / total,
        "results": results,
        "runs": runs,
    }
