import json

from app.evaluation_report import (
    build_timestamped_report_path,
    create_evaluation_report,
    save_evaluation_report,
)


def test_create_evaluation_report_adds_metadata():
    report = create_evaluation_report(
        evaluation_type="faithfulness",
        model="deepseek-test",
        config={
            "benchmark_path": "data/faithfulness_benchmark.json",
        },
        result={
            "accuracy": 1.0,
            "results": [],
        },
        evaluated_at="2026-06-12T11:00:00",
    )

    assert report["metadata"] == {
        "evaluation_type": "faithfulness",
        "evaluated_at": "2026-06-12T11:00:00",
        "judge_model": "deepseek-test",
        "config": {
            "benchmark_path": "data/faithfulness_benchmark.json",
        },
    }
    assert report["accuracy"] == 1.0


def test_build_timestamped_report_path():
    path = build_timestamped_report_path(
        prefix="faithfulness_eval",
        timestamp="2026-06-12-110000",
    )

    assert path.as_posix() == (
        "data/reports/faithfulness_eval_2026-06-12-110000.json"
    )


def test_save_evaluation_report(tmp_path):
    output_path = tmp_path / "reports" / "result.json"
    saved_path = save_evaluation_report(
        report={
            "metadata": {
                "evaluation_type": "faithfulness",
            },
            "accuracy": 1.0,
        },
        output_path=output_path,
    )

    saved_report = json.loads(
        saved_path.read_text(encoding="utf-8")
    )

    assert saved_path == output_path
    assert saved_report["metadata"]["evaluation_type"] == (
        "faithfulness"
    )
    assert saved_report["accuracy"] == 1.0
