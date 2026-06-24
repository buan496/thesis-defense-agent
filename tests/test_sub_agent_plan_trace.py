import json

from app import cli
from app.sub_agent_plan import create_sub_agent_execution_plan
from app.sub_agent_plan_trace import (
    build_sub_agent_plan_trace_record,
    load_sub_agent_plan_traces,
    save_sub_agent_plan_trace,
    summarize_sub_agent_plan_traces,
)


def create_plan(plan_id: str = "plan-1"):
    return create_sub_agent_execution_plan(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": "系统架构"},
        plan_id=plan_id,
    )


def test_build_sub_agent_plan_trace_record():
    plan = create_plan()

    record = build_sub_agent_plan_trace_record(plan)

    assert record["created_at"]
    assert record["event_type"] == "sub_agent_plan_created"
    assert record["plan"]["plan_id"] == "plan-1"
    assert record["audit"]["sub_agent_name"] == "retrieval_agent"
    assert record["audit"]["tool_name"] == "search_thesis"
    assert record["audit"]["status"] == "planned"


def test_save_and_load_sub_agent_plan_trace(tmp_path):
    trace_path = tmp_path / "sub_agent_plan_trace.jsonl"
    plan = create_plan()

    saved_path = save_sub_agent_plan_trace(
        plan,
        file_path=str(trace_path),
    )
    records = load_sub_agent_plan_traces(str(saved_path))

    assert saved_path == trace_path
    assert len(records) == 1
    assert records[0]["plan"]["plan_id"] == "plan-1"
    assert records[0]["audit"]["tool_name"] == "search_thesis"


def test_load_sub_agent_plan_traces_missing_file(tmp_path):
    records = load_sub_agent_plan_traces(
        str(tmp_path / "missing.jsonl")
    )

    assert records == []


def test_summarize_sub_agent_plan_traces(tmp_path):
    trace_path = tmp_path / "sub_agent_plan_trace.jsonl"

    save_sub_agent_plan_trace(
        create_plan("plan-1"),
        file_path=str(trace_path),
    )
    save_sub_agent_plan_trace(
        create_plan("plan-2"),
        file_path=str(trace_path),
    )

    records = load_sub_agent_plan_traces(str(trace_path))
    summary = summarize_sub_agent_plan_traces(records)

    assert summary == {
        "total": 2,
        "by_sub_agent": {
            "retrieval_agent": 2,
        },
        "by_tool": {
            "search_thesis": 2,
        },
    }


def test_plan_sub_agent_call_cli_saves_trace(
    monkeypatch,
    capsys,
    tmp_path,
):
    trace_path = tmp_path / "trace.jsonl"

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "plan-sub-agent-call",
            "--sub-agent",
            "retrieval_agent",
            "--tool",
            "search_thesis",
            "--argument",
            "query=系统架构",
            "--save-trace",
            "--trace-file",
            str(trace_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    records = [
        json.loads(line)
        for line in trace_path.read_text(encoding="utf-8").splitlines()
    ]

    assert "TRACE SAVED:" in output
    assert len(records) == 1
    assert records[0]["audit"]["sub_agent_name"] == "retrieval_agent"


def test_analyze_sub_agent_plans_cli(
    monkeypatch,
    capsys,
    tmp_path,
):
    trace_path = tmp_path / "trace.jsonl"
    save_sub_agent_plan_trace(
        create_plan(),
        file_path=str(trace_path),
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "analyze-sub-agent-plans",
            "--file",
            str(trace_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "SUB-AGENT PLAN TRACE SUMMARY" in output
    assert "TOTAL: 1" in output
    assert "retrieval_agent" in output
    assert "search_thesis" in output
