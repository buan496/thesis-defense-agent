import json

import pytest

from app import cli


def test_replay_agent_trace_command_outputs_trace(
    monkeypatch,
    capsys,
    tmp_path,
):
    trace_path = tmp_path / "agent_trace.jsonl"
    trace = {
        "created_at": "2026-06-23T10:00:00",
        "user_message": "What modules are in the system?",
        "result": {
            "final_output": "The system includes feature and model modules.",
            "steps": 2,
            "tool_traces": [
                {
                    "step": 1,
                    "tool_name": "search_thesis",
                    "arguments": '{"query": "system modules"}',
                    "result": "context",
                    "success": True,
                    "duration_ms": 12.5,
                }
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
    }
    trace_path.write_text(
        json.dumps(trace, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "replay-agent-trace",
            "--file",
            str(trace_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "AGENT TRACE REPLAY" in output
    assert "LINE NUMBER: 1" in output
    assert "What modules are in the system?" in output
    assert "The system includes feature and model modules." in output
    assert "TOOL: search_thesis" in output
    assert "PROMPT TOKENS: 100" in output
    assert "TOTAL COST: 0.003" in output


def test_replay_agent_trace_command_handles_missing_line(
    monkeypatch,
    capsys,
    tmp_path,
):
    trace_path = tmp_path / "agent_trace.jsonl"
    trace_path.write_text(
        json.dumps({"result": {}}, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "replay-agent-trace",
            "--file",
            str(trace_path),
            "--line-number",
            "2",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "TRACE REPLAY ERROR" in output
    assert "line 2 was not found" in output


def test_compare_agent_traces_command_outputs_comparison(
    monkeypatch,
    capsys,
    tmp_path,
):
    baseline_path = tmp_path / "baseline.jsonl"
    current_path = tmp_path / "current.jsonl"

    baseline_trace = {
        "user_message": "question",
        "result": {
            "final_output": "answer",
            "steps": 1,
            "tool_traces": [
                {
                    "step": 1,
                    "tool_name": "search_thesis",
                    "arguments": "{}",
                    "result": "ok",
                    "success": True,
                    "duration_ms": 10,
                }
            ],
            "token_usage": {"total_tokens": 100},
            "cost_estimate": {"total_cost": 0.01},
        },
    }
    current_trace = {
        "user_message": "question",
        "result": {
            "final_output": "",
            "steps": 1,
            "tool_traces": [
                {
                    "step": 1,
                    "tool_name": "generate_follow_up",
                    "arguments": "{}",
                    "result": "error",
                    "success": False,
                    "duration_ms": 12,
                }
            ],
            "token_usage": {"total_tokens": 120},
            "cost_estimate": {"total_cost": 0.02},
        },
    }
    baseline_path.write_text(
        json.dumps(baseline_trace, ensure_ascii=False),
        encoding="utf-8",
    )
    current_path.write_text(
        json.dumps(current_trace, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "compare-agent-traces",
            "--baseline-file",
            str(baseline_path),
            "--current-file",
            str(current_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    assert "AGENT TRACE COMPARISON" in output
    assert "SAME USER MESSAGE: True" in output
    assert "SAME FINAL OUTPUT: False" in output
    assert "SAME TOOL SEQUENCE: False" in output
    assert "FAILED TOOL CALL DELTA: 1" in output
    assert "tool_sequence_changed" in output
    assert "tool_failures_introduced" in output


def test_compare_agent_traces_command_handles_missing_file(
    monkeypatch,
    capsys,
    tmp_path,
):
    existing_path = tmp_path / "existing.jsonl"
    existing_path.write_text(
        json.dumps({"result": {}}, ensure_ascii=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "compare-agent-traces",
            "--baseline-file",
            str(existing_path),
            "--current-file",
            str(tmp_path / "missing.jsonl"),
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "TRACE COMPARISON ERROR" in output
