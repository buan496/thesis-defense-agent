import pytest

from app.trace_feedback import (
    build_trace_feedback_comment,
    build_trace_feedback_record,
    infer_trace_feedback_rating,
    infer_trace_feedback_tags,
)


def test_infer_trace_feedback_tags_returns_empty_for_clean_summary():
    tags = infer_trace_feedback_tags(
        {
            "record_count": 2,
            "failed_record_count": 0,
            "total_tool_call_count": 2,
            "total_failed_tool_call_count": 0,
        }
    )

    assert tags == []


def test_infer_trace_feedback_tags_detects_failures():
    tags = infer_trace_feedback_tags(
        {
            "record_count": 2,
            "failed_record_count": 1,
            "total_tool_call_count": 2,
            "total_failed_tool_call_count": 1,
        }
    )

    assert tags == [
        "failed_trace_records",
        "failed_tool_calls",
    ]


def test_infer_trace_feedback_tags_detects_empty_trace():
    tags = infer_trace_feedback_tags(
        {
            "record_count": 0,
            "failed_record_count": 0,
            "total_tool_call_count": 0,
            "total_failed_tool_call_count": 0,
        }
    )

    assert tags == [
        "empty_trace",
        "no_tool_calls",
    ]


def test_infer_trace_feedback_rating():
    assert infer_trace_feedback_rating(["failed_tool_calls"]) == 1
    assert infer_trace_feedback_rating(["empty_trace"]) == 2


def test_build_trace_feedback_comment():
    comment = build_trace_feedback_comment(
        replay_summary={
            "record_count": 3,
            "failed_record_count": 1,
            "total_failed_tool_call_count": 2,
        },
        issue_tags=["failed_tool_calls"],
    )

    assert "failed_tool_calls" in comment
    assert "records=3" in comment
    assert "failed_records=1" in comment
    assert "failed_tool_calls=2" in comment


def test_build_trace_feedback_record_returns_none_for_clean_summary():
    record = build_trace_feedback_record(
        replay_summary={
            "record_count": 1,
            "failed_record_count": 0,
            "total_tool_call_count": 1,
            "total_failed_tool_call_count": 0,
        },
        source_id="agent_trace.jsonl:1",
    )

    assert record is None


def test_build_trace_feedback_record_for_failed_trace():
    record = build_trace_feedback_record(
        replay_summary={
            "record_count": 2,
            "failed_record_count": 1,
            "total_tool_call_count": 2,
            "total_failed_tool_call_count": 1,
            "total_duration_ms": 30.5,
            "by_source_type": {"agent": 1, "sub_agent_execution": 1},
            "by_tool": {"search_thesis": 2},
        },
        source_id="agent_trace.jsonl",
    )

    assert record is not None
    assert record["source_type"] == "trace_replay"
    assert record["source_id"] == "agent_trace.jsonl"
    assert record["rating"] == 1
    assert record["tags"] == [
        "trace_replay",
        "needs_benchmark",
        "failed_trace_records",
        "failed_tool_calls",
    ]
    assert record["metadata"]["failed_record_count"] == 1
    assert record["metadata"]["total_failed_tool_call_count"] == 1
    assert record["metadata"]["by_tool"] == {"search_thesis": 2}


def test_build_trace_feedback_record_rejects_empty_source_id():
    with pytest.raises(ValueError, match="source_id must not be empty"):
        build_trace_feedback_record(
            replay_summary={},
            source_id=" ",
        )
