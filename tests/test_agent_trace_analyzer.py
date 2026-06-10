import json

import pytest

from app.agent_trace_analyzer import analyze_agent_traces


def test_analyze_agent_traces(tmp_path):
    trace_path = tmp_path / "agent_trace.jsonl"

    traces = [
        {
            "result": {
                "tool_traces": [
                    {
                        "tool_name": "search_thesis",
                        "success": True,
                        "duration_ms": 100.0,
                    }
                ]
            }
        },
        {
            "result": {
                "tool_traces": [
                    {
                        "tool_name": "search_thesis",
                        "success": False,
                        "duration_ms": 300.0,
                    }
                ]
            }
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
    
    
def test_analyze_empty_trace_file(tmp_path):
    trace_path = tmp_path / "empty.jsonl"
    trace_path.write_text("", encoding="utf-8")

    report = analyze_agent_traces(str(trace_path))

    assert report["run_count"] == 0
    assert report["tool_call_count"] == 0
    assert report["success_rate"] == 0.0
    assert report["average_duration_ms"] == 0.0
    assert report["tool_counts"] == {}


def test_analyze_invalid_json_line(tmp_path):
    trace_path = tmp_path / "invalid.jsonl"
    trace_path.write_text(
        '{"result": {"tool_traces": []}}\n'
        '{invalid json}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="第 2 行不是合法 JSON"):
        analyze_agent_traces(str(trace_path))