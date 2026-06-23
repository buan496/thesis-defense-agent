import json

import pytest

from app.feedback_store import (
    create_feedback_record,
    load_feedback_records,
    save_feedback_record,
    summarize_feedback_records,
)


def test_create_feedback_record():
    record = create_feedback_record(
        source_type="agent_trace",
        source_id="line:1",
        rating=5,
        comment="回答有依据。",
        tags=["useful", "grounded"],
        metadata={"query": "系统架构"},
    )

    assert record["id"]
    assert record["created_at"]
    assert record["source_type"] == "agent_trace"
    assert record["source_id"] == "line:1"
    assert record["rating"] == 5
    assert record["comment"] == "回答有依据。"
    assert record["tags"] == ["useful", "grounded"]
    assert record["metadata"] == {"query": "系统架构"}


def test_create_feedback_record_rejects_invalid_rating():
    with pytest.raises(ValueError, match="rating"):
        create_feedback_record(
            source_type="agent_trace",
            source_id="line:1",
            rating=6,
            comment="过高评分",
        )


def test_create_feedback_record_rejects_empty_comment():
    with pytest.raises(ValueError, match="comment"):
        create_feedback_record(
            source_type="agent_trace",
            source_id="line:1",
            rating=3,
            comment=" ",
        )


def test_save_and_load_feedback_records(tmp_path):
    feedback_path = tmp_path / "feedback.jsonl"
    first = create_feedback_record(
        source_type="agent_trace",
        source_id="line:1",
        rating=5,
        comment="好",
    )
    second = create_feedback_record(
        source_type="defense_task",
        source_id="task-1",
        rating=2,
        comment="不完整",
    )

    save_feedback_record(str(feedback_path), first)
    save_feedback_record(str(feedback_path), second)

    records = load_feedback_records(str(feedback_path))

    assert records == [first, second]


def test_load_feedback_records_returns_empty_list_when_missing(tmp_path):
    assert load_feedback_records(str(tmp_path / "missing.jsonl")) == []


def test_load_feedback_records_rejects_invalid_json(tmp_path):
    feedback_path = tmp_path / "feedback.jsonl"
    feedback_path.write_text("{broken json}", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        load_feedback_records(str(feedback_path))


def test_summarize_feedback_records():
    records = [
        {
            "source_type": "agent_trace",
            "rating": 5,
            "tags": ["useful"],
        },
        {
            "source_type": "agent_trace",
            "rating": 3,
            "tags": ["useful", "needs_follow_up"],
        },
        {
            "source_type": "defense_task",
            "rating": 1,
            "tags": [],
        },
    ]

    summary = summarize_feedback_records(records)

    assert summary["count"] == 3
    assert summary["average_rating"] == 3
    assert summary["source_type_counts"] == {
        "agent_trace": 2,
        "defense_task": 1,
    }
    assert summary["tag_counts"] == {
        "useful": 2,
        "needs_follow_up": 1,
    }


def test_save_feedback_record_writes_jsonl(tmp_path):
    feedback_path = tmp_path / "feedback.jsonl"
    record = create_feedback_record(
        source_type="agent_trace",
        source_id="line:1",
        rating=4,
        comment="可以进入 benchmark 候选。",
    )

    save_feedback_record(str(feedback_path), record)

    line = feedback_path.read_text(encoding="utf-8").strip()
    assert json.loads(line) == record
