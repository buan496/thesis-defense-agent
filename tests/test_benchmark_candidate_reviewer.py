import pytest

from app.benchmark_candidate_reviewer import (
    find_candidate,
    review_benchmark_candidate,
    summarize_candidate_review_status,
)


def make_candidate_report():
    return {
        "candidates": [
            {
                "candidate_id": "feedback-1",
                "status": "needs_review",
                "comment": "工具选错了",
            },
            {
                "candidate_id": "feedback-2",
                "status": "accepted",
                "comment": "已接受",
            },
        ]
    }


def test_review_benchmark_candidate_accepts_candidate():
    report = make_candidate_report()

    candidate = review_benchmark_candidate(
        candidate_report=report,
        candidate_id="feedback-1",
        status="accepted",
        reviewer="buan496",
        reason="适合作为回归样本",
    )

    assert candidate["status"] == "accepted"
    assert candidate["review"]["reviewer"] == "buan496"
    assert candidate["review"]["reason"] == "适合作为回归样本"
    assert candidate["review"]["reviewed_at"]
    assert find_candidate(report, "feedback-1")["status"] == "accepted"


def test_review_benchmark_candidate_rejects_invalid_status():
    with pytest.raises(ValueError, match="status"):
        review_benchmark_candidate(
            candidate_report=make_candidate_report(),
            candidate_id="feedback-1",
            status="maybe",
            reviewer="buan496",
            reason="非法状态",
        )


def test_review_benchmark_candidate_rejects_missing_candidate():
    with pytest.raises(ValueError, match="candidate not found"):
        review_benchmark_candidate(
            candidate_report=make_candidate_report(),
            candidate_id="missing",
            status="accepted",
            reviewer="buan496",
            reason="不存在",
        )


def test_review_benchmark_candidate_rejects_empty_reason():
    with pytest.raises(ValueError, match="reason"):
        review_benchmark_candidate(
            candidate_report=make_candidate_report(),
            candidate_id="feedback-1",
            status="accepted",
            reviewer="buan496",
            reason=" ",
        )


def test_summarize_candidate_review_status():
    summary = summarize_candidate_review_status(make_candidate_report())

    assert summary["count"] == 2
    assert summary["status_counts"] == {
        "needs_review": 1,
        "accepted": 1,
    }
