import json

import pytest

from app.trace_replay import (
    load_jsonl_trace_records,
    normalize_trace_record,
    replay_trace_file,
    summarize_trace_replay,
)


def write_jsonl(path, records):
    path.write_text(
        "\n".join(
            json.dumps(record, ensure_ascii=False)
            for record in records
        ),
        encoding="utf-8",
    )


def test_load_jsonl_trace_records(tmp_path):
    trace_path = tmp_path / "trace.jsonl"
    write_jsonl(
        trace_path,
        [
            {"created_at": "2026-06-25T10:00:00"},
            {"created_at": "2026-06-25T10:01:00"},
        ],
    )

    records = load_jsonl_trace_records(str(trace_path))

    assert records == [
        {"created_at": "2026-06-25T10:00:00"},
        {"created_at": "2026-06-25T10:01:00"},
    ]


def test_load_jsonl_trace_records_rejects_invalid_json(tmp_path):
    trace_path = tmp_path / "broken.jsonl"
    trace_path.write_text("{broken", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1 is not valid JSON"):
        load_jsonl_trace_records(str(trace_path))


def test_normalize_agent_trace_record():
    record = normalize_trace_record(
        raw={
            "created_at": "2026-06-25T10:00:00",
            "user_message": "系统架构",
            "result": {
                "tool_traces": [
                    {
                        "tool_name": "search_thesis",
                        "success": True,
                        "duration_ms": 10.5,
                    },
                    {
                        "tool_name": "answer_judge",
                        "success": False,
                        "duration_ms": 20,
                    },
                ],
            },
        },
        source_type="agent",
        source_path="data/traces/agent_trace.jsonl",
        record_index=1,
    )

    assert record.source_type == "agent"
    assert record.event_type == "agent_run"
    assert record.success is False
    assert record.tool_names == ["search_thesis", "answer_judge"]
    assert record.tool_call_count == 2
    assert record.failed_tool_call_count == 1
    assert record.duration_ms == 30.5


def test_normalize_sub_agent_plan_trace_record():
    record = normalize_trace_record(
        raw={
            "created_at": "2026-06-25T10:00:00",
            "event_type": "sub_agent_plan_created",
            "audit": {
                "tool_name": "search_thesis",
                "status": "planned",
            },
        },
        source_type="sub_agent_plan",
        source_path="data/traces/sub_agent_plan.jsonl",
        record_index=1,
    )

    assert record.source_type == "sub_agent_plan"
    assert record.event_type == "sub_agent_plan_created"
    assert record.status == "planned"
    assert record.success is None
    assert record.tool_names == ["search_thesis"]
    assert record.tool_call_count == 1


def test_normalize_sub_agent_execution_trace_record():
    record = normalize_trace_record(
        raw={
            "created_at": "2026-06-25T10:00:00",
            "event_type": "sub_agent_tool_executed",
            "audit": {
                "tool_name": "search_thesis",
                "success": False,
                "duration_ms": 12.5,
            },
        },
        source_type="sub_agent_execution",
        source_path="data/traces/sub_agent_execution.jsonl",
        record_index=1,
    )

    assert record.source_type == "sub_agent_execution"
    assert record.event_type == "sub_agent_tool_executed"
    assert record.success is False
    assert record.tool_names == ["search_thesis"]
    assert record.tool_call_count == 1
    assert record.failed_tool_call_count == 1
    assert record.duration_ms == 12.5


def test_summarize_trace_replay():
    records = [
        normalize_trace_record(
            raw={
                "result": {
                    "tool_traces": [
                        {
                            "tool_name": "search_thesis",
                            "success": True,
                            "duration_ms": 10,
                        },
                    ],
                },
            },
            source_type="agent",
            source_path="agent.jsonl",
            record_index=1,
        ),
        normalize_trace_record(
            raw={
                "audit": {
                    "tool_name": "search_thesis",
                    "success": False,
                    "duration_ms": 20,
                },
            },
            source_type="sub_agent_execution",
            source_path="sub_agent_execution.jsonl",
            record_index=1,
        ),
    ]

    summary = summarize_trace_replay(records)

    assert summary["record_count"] == 2
    assert summary["failed_record_count"] == 1
    assert summary["total_tool_call_count"] == 2
    assert summary["total_failed_tool_call_count"] == 1
    assert summary["total_duration_ms"] == 30.0
    assert summary["by_source_type"] == {
        "agent": 1,
        "sub_agent_execution": 1,
    }
    assert summary["by_tool"] == {"search_thesis": 2}
    assert len(summary["records"]) == 2


def test_replay_trace_file(tmp_path):
    trace_path = tmp_path / "sub_agent_execution.jsonl"
    write_jsonl(
        trace_path,
        [
            {
                "audit": {
                    "tool_name": "search_thesis",
                    "success": True,
                    "duration_ms": 10,
                },
            },
            {
                "audit": {
                    "tool_name": "search_thesis",
                    "success": False,
                    "duration_ms": 15,
                },
            },
        ],
    )

    summary = replay_trace_file(
        file_path=str(trace_path),
        source_type="sub_agent_execution",
    )

    assert summary["record_count"] == 2
    assert summary["failed_record_count"] == 1
    assert summary["total_duration_ms"] == 25.0
