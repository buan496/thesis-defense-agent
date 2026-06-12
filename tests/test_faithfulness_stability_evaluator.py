import json

import pytest

from app.faithfulness_stability_evaluator import (
    evaluate_faithfulness_stability,
)


def _write_benchmark(tmp_path, expected_passed: bool):
    benchmark_path = tmp_path / "faithfulness_benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            [
                {
                    "name": "流式识别判断",
                    "question": "系统是否已经实现流式识别？",
                    "evidence": "流式识别属于后续改进方向。",
                    "answer": "当前系统尚未实现流式识别。",
                    "expected_passed": expected_passed,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return benchmark_path


def _judge_output(passed: bool) -> str:
    return json.dumps(
        {
            "score": 1.0 if passed else 0.0,
            "passed": passed,
            "reason": "测试 Judge 输出",
            "unsupported_claims": [],
            "contradictions": [],
        },
        ensure_ascii=False,
    )


def test_evaluate_faithfulness_stability_uses_majority_vote(
    tmp_path,
):
    benchmark_path = _write_benchmark(
        tmp_path,
        expected_passed=True,
    )
    outputs = iter(
        [
            _judge_output(True),
            _judge_output(False),
            _judge_output(True),
        ]
    )

    def fake_llm(prompt: str) -> str:
        return next(outputs)

    report = evaluate_faithfulness_stability(
        benchmark_path=str(benchmark_path),
        repeat_count=3,
        llm_fn=fake_llm,
    )

    result = report["results"][0]

    assert report["repeat_count"] == 3
    assert report["total"] == 1
    assert report["average_agreement"] == pytest.approx(2 / 3)
    assert report["unanimous_rate"] == 0.0
    assert report["majority_accuracy"] == 1.0
    assert len(report["runs"]) == 3
    assert report["runs"][0]["run_number"] == 1
    assert report["runs"][0]["accuracy"] == 1.0
    assert report["runs"][1]["accuracy"] == 0.0
    assert report["runs"][2]["accuracy"] == 1.0
    assert result["predictions"] == [True, False, True]
    assert result["majority_prediction"] is True
    assert result["agreement_score"] == pytest.approx(2 / 3)
    assert result["unanimous"] is False
    assert result["majority_correct"] is True


def test_evaluate_faithfulness_stability_detects_unanimous_result(
    tmp_path,
):
    benchmark_path = _write_benchmark(
        tmp_path,
        expected_passed=False,
    )

    def fake_llm(prompt: str) -> str:
        return _judge_output(False)

    report = evaluate_faithfulness_stability(
        benchmark_path=str(benchmark_path),
        repeat_count=3,
        llm_fn=fake_llm,
    )

    result = report["results"][0]

    assert report["average_agreement"] == 1.0
    assert report["unanimous_rate"] == 1.0
    assert report["majority_accuracy"] == 1.0
    assert result["predictions"] == [False, False, False]
    assert result["majority_prediction"] is False
    assert result["unanimous"] is True
    assert result["majority_correct"] is True


def test_evaluate_faithfulness_stability_rejects_small_repeat_count(
    tmp_path,
):
    benchmark_path = _write_benchmark(
        tmp_path,
        expected_passed=True,
    )

    with pytest.raises(
        ValueError,
        match="repeat_count 必须至少为 2",
    ):
        evaluate_faithfulness_stability(
            benchmark_path=str(benchmark_path),
            repeat_count=1,
        )
