import json

from app import cli


def write_jsonl(path, records):
    path.write_text(
        "\n".join(
            json.dumps(record, ensure_ascii=False)
            for record in records
        ),
        encoding="utf-8",
    )


def test_replay_trace_command_outputs_summary(
    monkeypatch,
    capsys,
    tmp_path,
):
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
                    "duration_ms": 20,
                },
            },
        ],
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "replay-trace",
            "--file",
            str(trace_path),
            "--source-type",
            "sub_agent_execution",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "TRACE REPLAY SUMMARY" in output
    assert "SOURCE TYPE: sub_agent_execution" in output
    assert "RECORD COUNT: 2" in output
    assert "FAILED RECORD COUNT: 1" in output
    assert "TOOL CALL COUNT: 2" in output
    assert "FAILED TOOL CALL COUNT: 1" in output
    assert "TOTAL DURATION MS: 30.0" in output
    assert "search_thesis" in output


def test_trace_feedback_command_records_feedback_for_failed_trace(
    monkeypatch,
    capsys,
    tmp_path,
):
    trace_path = tmp_path / "sub_agent_execution.jsonl"
    feedback_path = tmp_path / "feedback.jsonl"
    write_jsonl(
        trace_path,
        [
            {
                "audit": {
                    "tool_name": "search_thesis",
                    "success": False,
                    "duration_ms": 20,
                },
            },
        ],
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "trace-feedback",
            "--file",
            str(trace_path),
            "--source-type",
            "sub_agent_execution",
            "--source-id",
            "sub-agent-run-1",
            "--feedback-file",
            str(feedback_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    saved_record = json.loads(
        feedback_path.read_text(encoding="utf-8").strip()
    )

    assert "TRACE FEEDBACK RECORDED" in output
    assert "SOURCE ID: sub-agent-run-1" in output
    assert saved_record["source_type"] == "trace_replay"
    assert saved_record["source_id"] == "sub-agent-run-1"
    assert saved_record["rating"] == 1
    assert "failed_tool_calls" in saved_record["tags"]
    assert saved_record["metadata"]["total_failed_tool_call_count"] == 1


def test_trace_feedback_command_skips_clean_trace(
    monkeypatch,
    capsys,
    tmp_path,
):
    trace_path = tmp_path / "sub_agent_execution.jsonl"
    feedback_path = tmp_path / "feedback.jsonl"
    write_jsonl(
        trace_path,
        [
            {
                "audit": {
                    "tool_name": "search_thesis",
                    "success": True,
                    "duration_ms": 20,
                },
            },
        ],
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "trace-feedback",
            "--file",
            str(trace_path),
            "--source-type",
            "sub_agent_execution",
            "--feedback-file",
            str(feedback_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "TRACE FEEDBACK NOT CREATED" in output
    assert not feedback_path.exists()
