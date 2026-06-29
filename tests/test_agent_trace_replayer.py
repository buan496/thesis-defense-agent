import json

import pytest

from app.agent_trace_replayer import (
    compare_agent_trace_records,
    compare_agent_trace_replays,
    load_agent_trace_records,
    replay_agent_trace,
)


def write_trace_file(path, traces):
    path.write_text(
        "\n".join(
            json.dumps(trace, ensure_ascii=False)
            for trace in traces
        ),
        encoding="utf-8",
    )


class InMemoryTraceRepository:
    def __init__(self, records):
        self.records = records

    def append(self, record):
        self.records.append(record)
        return f"repository:{len(self.records)}"

    def load_all(self):
        return list(self.records)


def test_load_agent_trace_records(tmp_path):
    trace_path = tmp_path / "agent_trace.jsonl"
    write_trace_file(
        trace_path,
        [
            {"created_at": "2026-06-23T10:00:00"},
            {"created_at": "2026-06-23T10:01:00"},
        ],
    )

    records = load_agent_trace_records(str(trace_path))

    assert records == [
        {
            "line_number": 1,
            "trace": {"created_at": "2026-06-23T10:00:00"},
        },
        {
            "line_number": 2,
            "trace": {"created_at": "2026-06-23T10:01:00"},
        },
    ]


def test_load_agent_trace_records_can_use_trace_repository(tmp_path):
    repository = InMemoryTraceRepository(
        [
            {"created_at": "2026-06-29T10:00:00"},
            {"created_at": "2026-06-29T10:01:00"},
        ]
    )

    records = load_agent_trace_records(
        str(tmp_path / "missing.jsonl"),
        trace_repository=repository,
    )

    assert records == [
        {
            "line_number": 1,
            "trace": {"created_at": "2026-06-29T10:00:00"},
        },
        {
            "line_number": 2,
            "trace": {"created_at": "2026-06-29T10:01:00"},
        },
    ]


def test_replay_agent_trace_defaults_to_latest_record(tmp_path):
    trace_path = tmp_path / "agent_trace.jsonl"
    write_trace_file(
        trace_path,
        [
            {
                "created_at": "2026-06-23T10:00:00",
                "user_message": "old question",
                "result": {
                    "final_output": "old answer",
                    "steps": 1,
                    "tool_traces": [],
                },
            },
            {
                "created_at": "2026-06-23T10:01:00",
                "user_message": "latest question",
                "result": {
                    "final_output": "latest answer",
                    "steps": 2,
                    "tool_traces": [
                        {
                            "step": 1,
                            "tool_name": "search_thesis",
                            "arguments": '{"query": "system architecture"}',
                            "result": "context",
                            "success": True,
                            "duration_ms": 10.5,
                        },
                        {
                            "step": 2,
                            "tool_name": "generate_follow_up",
                            "arguments": "{}",
                            "result": "follow up",
                            "success": False,
                            "duration_ms": 20,
                        },
                    ],
                    "token_usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 20,
                        "total_tokens": 120,
                    },
                    "cost_estimate": {
                        "input_cost": 0.001,
                        "output_cost": 0.002,
                        "total_cost": 0.003,
                        "currency": "CNY",
                    },
                },
            },
        ],
    )

    replay = replay_agent_trace(str(trace_path))

    assert replay["line_number"] == 2
    assert replay["created_at"] == "2026-06-23T10:01:00"
    assert replay["user_message"] == "latest question"
    assert replay["final_output"] == "latest answer"
    assert replay["steps"] == 2
    assert replay["tool_call_count"] == 2
    assert replay["successful_tool_calls"] == 1
    assert replay["failed_tool_calls"] == 1
    assert replay["total_duration_ms"] == 30.5
    assert replay["token_usage"]["total_tokens"] == 120
    assert replay["cost_estimate"]["total_cost"] == 0.003


def test_replay_agent_trace_can_select_line_number(tmp_path):
    trace_path = tmp_path / "agent_trace.jsonl"
    write_trace_file(
        trace_path,
        [
            {
                "created_at": "2026-06-23T10:00:00",
                "user_message": "first question",
                "result": {"final_output": "first answer"},
            },
            {
                "created_at": "2026-06-23T10:01:00",
                "user_message": "second question",
                "result": {"final_output": "second answer"},
            },
        ],
    )

    replay = replay_agent_trace(
        str(trace_path),
        line_number=1,
    )

    assert replay["line_number"] == 1
    assert replay["user_message"] == "first question"
    assert replay["final_output"] == "first answer"


def test_replay_agent_trace_rejects_empty_file(tmp_path):
    trace_path = tmp_path / "empty.jsonl"
    trace_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="no replayable records"):
        replay_agent_trace(str(trace_path))


def test_replay_agent_trace_rejects_missing_line_number(tmp_path):
    trace_path = tmp_path / "agent_trace.jsonl"
    write_trace_file(
        trace_path,
        [
            {
                "created_at": "2026-06-23T10:00:00",
                "result": {},
            },
        ],
    )

    with pytest.raises(ValueError, match="line 2 was not found"):
        replay_agent_trace(
            str(trace_path),
            line_number=2,
        )


def test_load_agent_trace_records_rejects_invalid_json(tmp_path):
    trace_path = tmp_path / "broken.jsonl"
    trace_path.write_text("{broken json}", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1 is not valid JSON"):
        load_agent_trace_records(str(trace_path))


def test_compare_agent_trace_replays_detects_no_regression():
    baseline = {
        "line_number": 1,
        "user_message": "question",
        "final_output": "answer",
        "tool_traces": [
            {"tool_name": "search_thesis", "success": True},
        ],
        "tool_call_count": 1,
        "failed_tool_calls": 0,
        "total_duration_ms": 10.0,
        "token_usage": {"total_tokens": 100},
        "cost_estimate": {"total_cost": 0.01},
    }
    current = {
        "line_number": 2,
        "user_message": "question",
        "final_output": "answer",
        "tool_traces": [
            {"tool_name": "search_thesis", "success": True},
        ],
        "tool_call_count": 1,
        "failed_tool_calls": 0,
        "total_duration_ms": 12.0,
        "token_usage": {"total_tokens": 120},
        "cost_estimate": {"total_cost": 0.02},
    }

    comparison = compare_agent_trace_replays(
        baseline=baseline,
        current=current,
    )

    assert comparison["same_user_message"] is True
    assert comparison["same_final_output"] is True
    assert comparison["same_tool_sequence"] is True
    assert comparison["same_tool_success_sequence"] is True
    assert comparison["tool_call_count_delta"] == 0
    assert comparison["failed_tool_call_delta"] == 0
    assert comparison["total_tokens_delta"] == 20
    assert comparison["total_cost_delta"] == 0.01
    assert comparison["duration_ms_delta"] == 2.0
    assert comparison["regressions"] == []


def test_compare_agent_trace_replays_detects_regressions():
    baseline = {
        "line_number": 1,
        "user_message": "question",
        "final_output": "answer",
        "tool_traces": [
            {"tool_name": "search_thesis", "success": True},
        ],
        "tool_call_count": 1,
        "failed_tool_calls": 0,
        "total_duration_ms": 10.0,
        "token_usage": {"total_tokens": 100},
        "cost_estimate": {"total_cost": 0.01},
    }
    current = {
        "line_number": 2,
        "user_message": "question",
        "final_output": "",
        "tool_traces": [
            {"tool_name": "generate_follow_up", "success": False},
        ],
        "tool_call_count": 1,
        "failed_tool_calls": 1,
        "total_duration_ms": 15.0,
        "token_usage": {"total_tokens": 90},
        "cost_estimate": {"total_cost": 0.005},
    }

    comparison = compare_agent_trace_replays(
        baseline=baseline,
        current=current,
    )

    assert comparison["same_final_output"] is False
    assert comparison["same_tool_sequence"] is False
    assert comparison["same_tool_success_sequence"] is False
    assert comparison["failed_tool_call_delta"] == 1
    assert comparison["regressions"] == [
        "tool_sequence_changed",
        "tool_failures_introduced",
        "tool_success_sequence_changed",
        "final_output_became_empty",
    ]


def test_compare_agent_trace_records(tmp_path):
    baseline_path = tmp_path / "baseline.jsonl"
    current_path = tmp_path / "current.jsonl"
    write_trace_file(
        baseline_path,
        [
            {
                "user_message": "question",
                "result": {
                    "final_output": "answer",
                    "tool_traces": [],
                },
            },
        ],
    )
    write_trace_file(
        current_path,
        [
            {
                "user_message": "question",
                "result": {
                    "final_output": "answer changed",
                    "tool_traces": [],
                },
            },
        ],
    )

    comparison = compare_agent_trace_records(
        baseline_file_path=str(baseline_path),
        current_file_path=str(current_path),
    )

    assert comparison["same_user_message"] is True
    assert comparison["same_final_output"] is False
