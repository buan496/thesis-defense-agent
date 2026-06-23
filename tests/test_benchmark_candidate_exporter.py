import json

from app.benchmark_candidate_exporter import (
    build_benchmark_candidate,
    export_feedback_benchmark_candidates,
    should_export_feedback_record,
)


def test_should_export_feedback_record_by_low_rating():
    assert should_export_feedback_record(
        {"rating": 2, "tags": []},
        max_rating=2,
    )


def test_should_export_feedback_record_by_candidate_tag():
    assert should_export_feedback_record(
        {"rating": 5, "tags": ["needs_benchmark"]},
        max_rating=2,
    )


def test_should_not_export_feedback_record_without_match():
    assert not should_export_feedback_record(
        {"rating": 5, "tags": ["useful"]},
        max_rating=2,
    )


def test_build_benchmark_candidate():
    candidate = build_benchmark_candidate(
        {
            "id": "abc",
            "source_type": "agent_trace",
            "source_id": "line:1",
            "rating": 1,
            "comment": "工具选错了",
            "tags": ["routing_error"],
            "metadata": {"query": "系统架构"},
        }
    )

    assert candidate["candidate_id"] == "feedback-abc"
    assert candidate["status"] == "needs_review"
    assert candidate["source_feedback_id"] == "abc"
    assert candidate["recommended_action"] == "add_regression_case"
    assert candidate["metadata"] == {"query": "系统架构"}


def test_export_feedback_benchmark_candidates(tmp_path):
    output_path = tmp_path / "candidates.json"
    records = [
        {
            "id": "low",
            "source_type": "agent_trace",
            "source_id": "line:1",
            "rating": 1,
            "comment": "失败样本",
            "tags": [],
            "metadata": {},
        },
        {
            "id": "tagged",
            "source_type": "defense_task",
            "source_id": "task-1",
            "rating": 5,
            "comment": "值得加入评估集",
            "tags": ["needs_benchmark"],
            "metadata": {},
        },
        {
            "id": "good",
            "source_type": "agent_trace",
            "source_id": "line:2",
            "rating": 5,
            "comment": "正常样本",
            "tags": ["useful"],
            "metadata": {},
        },
    ]

    report = export_feedback_benchmark_candidates(
        feedback_records=records,
        output_file_path=str(output_path),
        max_rating=2,
    )

    assert report["count"] == 2
    assert [
        candidate["source_feedback_id"]
        for candidate in report["candidates"]
    ] == ["low", "tagged"]

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["count"] == 2
    assert saved["candidates"][0]["source_feedback_id"] == "low"
