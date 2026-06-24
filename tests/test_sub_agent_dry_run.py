import json

import pytest

from app import cli
from app.sub_agent_dry_run import (
    SubAgentDryRunReport,
    dry_run_sub_agent_tool_call,
)


def test_dry_run_sub_agent_tool_call():
    report = dry_run_sub_agent_tool_call(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": "system architecture"},
    )

    assert isinstance(report, SubAgentDryRunReport)
    assert report.sub_agent_name == "retrieval_agent"
    assert report.tool_name == "search_thesis"
    assert report.allowed is True
    assert report.will_execute is False
    assert report.plan.tool_arguments == {"query": "system architecture"}
    assert report.trace_saved is False
    assert report.trace_path is None
    assert "not executed" in report.reason


def test_dry_run_sub_agent_tool_call_saves_trace(tmp_path):
    trace_path = tmp_path / "trace.jsonl"

    report = dry_run_sub_agent_tool_call(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": "system architecture"},
        save_trace=True,
        trace_file=str(trace_path),
    )

    records = [
        json.loads(line)
        for line in trace_path.read_text(encoding="utf-8").splitlines()
    ]

    assert report.trace_saved is True
    assert report.trace_path == str(trace_path)
    assert len(records) == 1
    assert records[0]["plan"]["plan_id"] == report.plan.plan_id


def test_dry_run_sub_agent_tool_call_rejects_disallowed_tool():
    with pytest.raises(ValueError, match="not allowed"):
        dry_run_sub_agent_tool_call(
            sub_agent_name="retrieval_agent",
            tool_name="evaluate_student_answer",
            tool_arguments={"query": "system architecture"},
        )


def test_dry_run_report_to_dict():
    report = dry_run_sub_agent_tool_call(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": "system architecture"},
    )

    data = report.to_dict()

    assert data["sub_agent_name"] == "retrieval_agent"
    assert data["will_execute"] is False
    assert data["plan"]["tool_name"] == "search_thesis"


def test_dry_run_sub_agent_call_cli(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "dry-run-sub-agent-call",
            "--sub-agent",
            "retrieval_agent",
            "--tool",
            "search_thesis",
            "--argument",
            "query=system architecture",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "SUB-AGENT DRY-RUN" in output
    assert "SUB_AGENT: retrieval_agent" in output
    assert "TOOL: search_thesis" in output
    assert "ALLOWED: True" in output
    assert "WILL_EXECUTE: False" in output
    assert "TRACE_SAVED: False" in output


def test_dry_run_sub_agent_call_cli_saves_trace(
    monkeypatch,
    capsys,
    tmp_path,
):
    trace_path = tmp_path / "trace.jsonl"

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "dry-run-sub-agent-call",
            "--sub-agent",
            "retrieval_agent",
            "--tool",
            "search_thesis",
            "--argument",
            "query=system architecture",
            "--save-trace",
            "--trace-file",
            str(trace_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "TRACE_SAVED: True" in output
    assert "TRACE PATH:" in output
    assert trace_path.exists()


def test_dry_run_sub_agent_call_cli_reports_error(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "dry-run-sub-agent-call",
            "--sub-agent",
            "retrieval_agent",
            "--tool",
            "evaluate_student_answer",
            "--argument",
            "query=system architecture",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "SUB-AGENT DRY-RUN ERROR:" in output

