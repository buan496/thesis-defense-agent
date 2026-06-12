import json

import pytest

from app.evaluation_report_comparator import (
    compare_evaluation_report_files,
    compare_evaluation_reports,
    load_evaluation_report,
    render_evaluation_comparison_markdown,
    save_evaluation_comparison_markdown,
)


def _faithfulness_report(
    accuracy: float,
    actual_passed: bool,
    prediction_correct: bool,
    score: float,
) -> dict:
    return {
        "metadata": {
            "evaluation_type": "faithfulness",
            "evaluated_at": "2026-06-12T10:00:00",
            "judge_model": "deepseek-test",
            "config": {
                "benchmark_path": "benchmark.json",
            },
        },
        "accuracy": accuracy,
        "results": [
            {
                "name": "测试案例",
                "actual_passed": actual_passed,
                "prediction_correct": prediction_correct,
                "score": score,
            }
        ],
    }


def _stability_report(
    average_agreement: float,
    unanimous_rate: float,
    majority_accuracy: float,
    majority_prediction: bool,
    agreement_score: float,
    unanimous: bool,
    majority_correct: bool,
) -> dict:
    return {
        "metadata": {
            "evaluation_type": "faithfulness_stability",
            "evaluated_at": "2026-06-12T10:00:00",
            "judge_model": "deepseek-test",
            "config": {
                "benchmark_path": "benchmark.json",
                "repeat_count": 3,
            },
        },
        "average_agreement": average_agreement,
        "unanimous_rate": unanimous_rate,
        "majority_accuracy": majority_accuracy,
        "results": [
            {
                "name": "测试案例",
                "majority_prediction": majority_prediction,
                "agreement_score": agreement_score,
                "unanimous": unanimous,
                "majority_correct": majority_correct,
            }
        ],
    }


def test_compare_faithfulness_detects_metric_and_prediction_regression():
    baseline = _faithfulness_report(
        accuracy=1.0,
        actual_passed=True,
        prediction_correct=True,
        score=1.0,
    )
    current = _faithfulness_report(
        accuracy=0.0,
        actual_passed=False,
        prediction_correct=False,
        score=0.2,
    )

    comparison = compare_evaluation_reports(
        baseline=baseline,
        current=current,
    )

    assert comparison["has_regression"] is True
    assert comparison["regression_count"] == 2
    assert comparison["metric_changes"][0]["delta"] == -1.0
    assert comparison["metric_changes"][0]["regressed"] is True
    assert comparison["prediction_flips"][0]["regression"] is True
    assert comparison["case_score_changes"][0]["delta"] == -0.8


def test_compare_faithfulness_tracks_added_and_removed_cases():
    baseline = _faithfulness_report(1.0, True, True, 1.0)
    current = _faithfulness_report(1.0, True, True, 1.0)
    baseline["results"][0]["name"] = "旧案例"
    current["results"][0]["name"] = "新案例"

    comparison = compare_evaluation_reports(
        baseline=baseline,
        current=current,
    )

    assert comparison["has_regression"] is False
    assert comparison["added_cases"] == ["新案例"]
    assert comparison["removed_cases"] == ["旧案例"]


def test_compare_stability_detects_stability_regression():
    baseline = _stability_report(
        average_agreement=1.0,
        unanimous_rate=1.0,
        majority_accuracy=1.0,
        majority_prediction=True,
        agreement_score=1.0,
        unanimous=True,
        majority_correct=True,
    )
    current = _stability_report(
        average_agreement=2 / 3,
        unanimous_rate=0.0,
        majority_accuracy=1.0,
        majority_prediction=True,
        agreement_score=2 / 3,
        unanimous=False,
        majority_correct=True,
    )

    comparison = compare_evaluation_reports(
        baseline=baseline,
        current=current,
    )

    assert comparison["has_regression"] is True
    assert comparison["regression_count"] == 4
    assert len(comparison["stability_regressions"]) == 2
    assert {
        item["metric"]
        for item in comparison["stability_regressions"]
    } == {"agreement_score", "unanimous"}


def test_compare_reports_rejects_different_evaluation_types():
    baseline = _faithfulness_report(1.0, True, True, 1.0)
    current = _stability_report(
        average_agreement=1.0,
        unanimous_rate=1.0,
        majority_accuracy=1.0,
        majority_prediction=True,
        agreement_score=1.0,
        unanimous=True,
        majority_correct=True,
    )

    with pytest.raises(
        ValueError,
        match="评估类型必须一致",
    ):
        compare_evaluation_reports(
            baseline=baseline,
            current=current,
        )


def test_compare_report_files_and_metadata_changes(tmp_path):
    baseline = _faithfulness_report(1.0, True, True, 1.0)
    current = _faithfulness_report(1.0, True, True, 1.0)
    current["metadata"]["judge_model"] = "new-model"
    baseline_path = tmp_path / "baseline.json"
    current_path = tmp_path / "current.json"
    baseline_path.write_text(
        json.dumps(baseline, ensure_ascii=False),
        encoding="utf-8",
    )
    current_path.write_text(
        json.dumps(current, ensure_ascii=False),
        encoding="utf-8",
    )

    comparison = compare_evaluation_report_files(
        baseline_path=baseline_path,
        current_path=current_path,
    )

    assert comparison["baseline_path"] == str(baseline_path)
    assert comparison["current_path"] == str(current_path)
    assert comparison["metadata_changes"][0]["field"] == (
        "judge_model"
    )


def test_load_evaluation_report_rejects_invalid_report(tmp_path):
    report_path = tmp_path / "invalid.json"
    report_path.write_text("[]", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="JSON 对象",
    ):
        load_evaluation_report(report_path)


def test_load_evaluation_report_accepts_utf8_bom(tmp_path):
    report = _faithfulness_report(1.0, True, True, 1.0)
    report_path = tmp_path / "bom-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False),
        encoding="utf-8-sig",
    )

    loaded = load_evaluation_report(report_path)

    assert loaded["accuracy"] == 1.0


def test_metric_tolerance_allows_small_drop():
    baseline = _faithfulness_report(1.0, True, True, 1.0)
    current = _faithfulness_report(0.98, True, True, 1.0)

    comparison = compare_evaluation_reports(
        baseline=baseline,
        current=current,
        metric_tolerance=0.02,
    )

    assert comparison["has_regression"] is False
    assert comparison["metric_changes"][0]["drop"] == (
        pytest.approx(0.02)
    )
    assert comparison["metric_changes"][0]["regressed"] is False


def test_stability_tolerance_allows_small_case_drop():
    baseline = _stability_report(
        average_agreement=1.0,
        unanimous_rate=1.0,
        majority_accuracy=1.0,
        majority_prediction=True,
        agreement_score=1.0,
        unanimous=True,
        majority_correct=True,
    )
    current = _stability_report(
        average_agreement=0.8,
        unanimous_rate=0.0,
        majority_accuracy=1.0,
        majority_prediction=True,
        agreement_score=0.8,
        unanimous=False,
        majority_correct=True,
    )

    comparison = compare_evaluation_reports(
        baseline=baseline,
        current=current,
        metric_tolerance=1.0,
        stability_tolerance=0.2,
    )

    assert comparison["has_regression"] is False
    assert comparison["stability_regressions"] == []


def test_prediction_regression_is_not_hidden_by_tolerance():
    baseline = _faithfulness_report(1.0, True, True, 1.0)
    current = _faithfulness_report(0.9, False, False, 0.0)

    comparison = compare_evaluation_reports(
        baseline=baseline,
        current=current,
        metric_tolerance=1.0,
    )

    assert comparison["has_regression"] is True
    assert comparison["regression_count"] == 1
    assert comparison["prediction_flips"][0]["regression"] is True


def test_compare_reports_rejects_negative_tolerance():
    baseline = _faithfulness_report(1.0, True, True, 1.0)

    with pytest.raises(
        ValueError,
        match="metric_tolerance 不能小于 0",
    ):
        compare_evaluation_reports(
            baseline=baseline,
            current=baseline,
            metric_tolerance=-0.1,
        )


def test_render_and_save_comparison_markdown(tmp_path):
    baseline = _faithfulness_report(1.0, True, True, 1.0)
    current = _faithfulness_report(0.0, False, False, 0.0)
    comparison = compare_evaluation_reports(
        baseline=baseline,
        current=current,
    )

    markdown = render_evaluation_comparison_markdown(comparison)
    output_path = tmp_path / "reports" / "comparison.md"
    saved_path = save_evaluation_comparison_markdown(
        comparison,
        output_path,
    )

    assert "# 评估回归对比报告" in markdown
    assert "状态：**FAIL**" in markdown
    assert "测试案例" in markdown
    assert saved_path.read_text(encoding="utf-8") == markdown
