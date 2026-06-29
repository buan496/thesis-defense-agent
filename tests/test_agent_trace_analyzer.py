import json

import pytest

from app.agent_trace_analyzer import analyze_agent_traces


class InMemoryTraceRepository:
    def __init__(self, records):
        self.records = records

    def append(self, record):
        self.records.append(record)
        return f"repository:{len(self.records)}"

    def load_all(self):
        return list(self.records)


def test_analyze_agent_traces(tmp_path):
    trace_path = tmp_path / "agent_trace.jsonl"

    traces = [
        {
            "created_at": "2026-06-16T09:00:00",
            "user_message": "第一次运行",
            "result": {
                "tool_traces": [
                    {
                        "tool_name": "search_thesis",
                        "success": True,
                        "duration_ms": 100.0,
                    }
                ],
                "token_usage": {
                    "prompt_tokens": 1000,
                    "completion_tokens": 200,
                    "total_tokens": 1200,
                },
                "cost_estimate": {
                    "input_cost": 0.003,
                    "output_cost": 0.0012,
                    "total_cost": 0.0042,
                    "currency": "CNY",
                },
            },
        },
        {
            "created_at": "2026-06-16T09:01:00",
            "user_message": "第二次运行",
            "result": {
                "tool_traces": [
                    {
                        "tool_name": "search_thesis",
                        "success": False,
                        "duration_ms": 300.0,
                    }
                ],
                "token_usage": {
                    "prompt_tokens": 2000,
                    "completion_tokens": 400,
                    "total_tokens": 2400,
                },
                "cost_estimate": {
                    "input_cost": 0.006,
                    "output_cost": 0.0024,
                    "total_cost": 0.0084,
                    "currency": "CNY",
                },
            },
        },
    ]

    content = "\n".join(
        json.dumps(trace, ensure_ascii=False)
        for trace in traces
    )

    trace_path.write_text(content, encoding="utf-8")

    report = analyze_agent_traces(str(trace_path))

    assert report["run_count"] == 2
    assert report["tool_call_count"] == 2
    assert report["success_count"] == 1
    assert report["failure_count"] == 1
    assert report["success_rate"] == 0.5
    assert report["average_duration_ms"] == 200.0
    assert report["tool_counts"] == {
        "search_thesis": 2,
    }
    assert report["total_prompt_tokens"] == 3000
    assert report["total_completion_tokens"] == 600
    assert report["total_tokens"] == 3600
    assert report["average_total_tokens_per_run"] == 1800
    assert report["total_cost"] == pytest.approx(0.0126)
    assert report["average_cost_per_run"] == pytest.approx(0.0063)
    assert report["currency"] == "CNY"

    assert report["most_expensive_run"] == {
        "line_number": 2,
        "created_at": "2026-06-16T09:01:00",
        "user_message": "第二次运行",
        "total_cost": 0.0084,
        "total_tokens": 2400,
        "currency": "CNY",
    }
    
    
def test_analyze_empty_trace_file(tmp_path):
    trace_path = tmp_path / "empty.jsonl"
    trace_path.write_text("", encoding="utf-8")

    report = analyze_agent_traces(str(trace_path))

    assert report["run_count"] == 0
    assert report["tool_call_count"] == 0
    assert report["success_rate"] == 0.0
    assert report["average_duration_ms"] == 0.0
    assert report["tool_counts"] == {}
    assert report["total_prompt_tokens"] == 0
    assert report["total_completion_tokens"] == 0
    assert report["total_tokens"] == 0
    assert report["average_total_tokens_per_run"] == 0.0
    assert report["total_cost"] == 0.0
    assert report["average_cost_per_run"] == 0.0
    assert report["currency"] is None
    assert report["most_expensive_run"] is None


def test_analyze_agent_traces_can_use_trace_repository(tmp_path):
    repository = InMemoryTraceRepository(
        [
            {
                "created_at": "2026-06-29T10:00:00",
                "user_message": "repository trace",
                "result": {
                    "tool_traces": [
                        {
                            "tool_name": "search_thesis",
                            "success": True,
                            "duration_ms": 25.0,
                        }
                    ],
                    "token_usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    },
                    "cost_estimate": {
                        "total_cost": 0.1,
                        "currency": "CNY",
                    },
                },
            }
        ]
    )

    report = analyze_agent_traces(
        str(tmp_path / "missing.jsonl"),
        trace_repository=repository,
    )

    assert report["run_count"] == 1
    assert report["tool_call_count"] == 1
    assert report["success_count"] == 1
    assert report["tool_counts"] == {"search_thesis": 1}
    assert report["total_tokens"] == 15
    assert report["total_cost"] == 0.1


def test_analyze_invalid_json_line(tmp_path):
    trace_path = tmp_path / "invalid.jsonl"
    trace_path.write_text(
        '{"result": {"tool_traces": []}}\n'
        '{invalid json}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="第 2 行不是合法 JSON"):
        analyze_agent_traces(str(trace_path))
        
def test_analyze_legacy_trace_without_cost_fields(tmp_path):
    trace_path = tmp_path / "legacy.jsonl"

    trace = {
        "created_at": "2026-06-16T09:00:00",
        "user_message": "旧日志",
        "result": {
            "tool_traces": [
                {
                    "tool_name": "search_thesis",
                    "success": True,
                    "duration_ms": 100.0,
                }
            ]
        },
    }

    trace_path.write_text(
        json.dumps(trace, ensure_ascii=False),
        encoding="utf-8",
    )

    report = analyze_agent_traces(str(trace_path))

    assert report["run_count"] == 1
    assert report["tool_call_count"] == 1
    assert report["total_tokens"] == 0
    assert report["total_cost"] == 0.0
    assert report["currency"] is None
    assert report["most_expensive_run"] == {
        "line_number": 1,
        "created_at": "2026-06-16T09:00:00",
        "user_message": "旧日志",
        "total_cost": 0.0,
        "total_tokens": 0,
        "currency": None,
    }
