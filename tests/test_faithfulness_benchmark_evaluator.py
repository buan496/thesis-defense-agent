import json

import pytest

from app.faithfulness_benchmark_evaluator import (
    evaluate_faithfulness_benchmark,
)


def test_evaluate_faithfulness_benchmark(tmp_path):
    benchmark_path = tmp_path / "faithfulness_benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            [
                {
                    "name": "忠实回答",
                    "question": "是否实现流式识别？",
                    "evidence": "流式识别属于未来计划。",
                    "answer": "尚未实现流式识别。",
                    "expected_passed": True,
                },
                {
                    "name": "矛盾回答",
                    "question": "是否实现流式识别？",
                    "evidence": "流式识别属于未来计划。",
                    "answer": "已经实现流式识别。",
                    "expected_passed": False,
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    judge_outputs = iter(
        [
            """
            {
                "score": 1.0,
                "passed": true,
                "reason": "回答与证据一致",
                "unsupported_claims": [],
                "contradictions": []
            }
            """,
            """
            {
                "score": 0.0,
                "passed": false,
                "reason": "回答与证据矛盾",
                "unsupported_claims": [],
                "contradictions": ["将未来计划描述为已经完成"]
            }
            """,
        ]
    )

    def fake_llm(prompt: str) -> str:
        return next(judge_outputs)

    report = evaluate_faithfulness_benchmark(
        benchmark_path=str(benchmark_path),
        llm_fn=fake_llm,
    )

    assert report["total"] == 2
    assert report["passed"] == 2
    assert report["failed"] == 0
    assert report["accuracy"] == 1.0
    assert all(
        item["prediction_correct"]
        for item in report["results"]
    )
    
def test_evaluate_faithfulness_benchmark_records_wrong_prediction(
    tmp_path,
):
    benchmark_path = tmp_path / "faithfulness_benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            [
                {
                    "name": "矛盾回答",
                    "question": "是否实现流式识别？",
                    "evidence": "流式识别属于未来计划。",
                    "answer": "已经实现流式识别。",
                    "expected_passed": False,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fake_llm(prompt: str) -> str:
        return """
        {
            "score": 1.0,
            "passed": true,
            "reason": "Judge 判断错误",
            "unsupported_claims": [],
            "contradictions": []
        }
        """

    report = evaluate_faithfulness_benchmark(
        benchmark_path=str(benchmark_path),
        llm_fn=fake_llm,
    )

    assert report["passed"] == 0
    assert report["failed"] == 1
    assert report["accuracy"] == 0.0
    assert report["results"][0]["prediction_correct"] is False
    
    
def test_evaluate_faithfulness_benchmark_rejects_empty_file(
    tmp_path,
):
    benchmark_path = tmp_path / "empty.json"
    benchmark_path.write_text("[]", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Faithfulness benchmark 不能为空",
    ):
        evaluate_faithfulness_benchmark(
            benchmark_path=str(benchmark_path),
        )