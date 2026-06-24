import json

import pytest

from app import cli
from app.sub_agent_execution_trace import (
    load_sub_agent_execution_traces,
    summarize_sub_agent_execution_traces,
)
from app.sub_agent_executor import (
    SubAgentExecutionResult,
    execute_sub_agent_plan,
    execute_sub_agent_tool_call,
)
from app.sub_agent_plan import create_sub_agent_execution_plan


def create_plan():
    return create_sub_agent_execution_plan(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": "system architecture"},
        plan_id="plan-1",
    )


def test_execute_sub_agent_plan_with_fake_runner():
    plan = create_plan()

    def fake_runner(input_plan):
        assert input_plan == plan
        return json.dumps(
            {"evidence": "context", "sources": ["data/thesis.pdf"]},
            ensure_ascii=False,
        )

    result = execute_sub_agent_plan(
        plan,
        tool_runner=fake_runner,
    )

    assert isinstance(result, SubAgentExecutionResult)
    assert result.sub_agent_name == "retrieval_agent"
    assert result.tool_name == "search_thesis"
    assert result.success is True
    assert json.loads(result.result_text) == {
        "evidence": "context",
        "sources": ["data/thesis.pdf"],
    }
    assert result.duration_ms >= 0
    assert result.trace_saved is False
    assert result.trace_path is None


def test_execute_sub_agent_plan_wraps_runner_error():
    plan = create_plan()

    def broken_runner(input_plan):
        raise RuntimeError("tool failed")

    result = execute_sub_agent_plan(
        plan,
        tool_runner=broken_runner,
    )

    data = json.loads(result.result_text)

    assert result.success is False
    assert data["success"] is False
    assert data["error_type"] == "RuntimeError"
    assert data["message"] == "tool failed"
    assert data["tool_name"] == "search_thesis"


def test_execute_sub_agent_tool_call_rejects_disallowed_tool():
    with pytest.raises(ValueError, match="not allowed"):
        execute_sub_agent_tool_call(
            sub_agent_name="retrieval_agent",
            tool_name="evaluate_student_answer",
            tool_arguments={"query": "system architecture"},
        )


def test_execute_sub_agent_plan_saves_trace(tmp_path):
    trace_path = tmp_path / "execution_trace.jsonl"
    plan = create_plan()

    result = execute_sub_agent_plan(
        plan,
        tool_runner=lambda input_plan: '{"ok": true}',
        save_trace=True,
        trace_file=str(trace_path),
    )
    records = load_sub_agent_execution_traces(str(trace_path))

    assert result.trace_saved is True
    assert result.trace_path == str(trace_path)
    assert len(records) == 1
    assert records[0]["event_type"] == "sub_agent_tool_executed"
    assert records[0]["audit"]["sub_agent_name"] == "retrieval_agent"
    assert records[0]["audit"]["tool_name"] == "search_thesis"
    assert records[0]["audit"]["success"] is True


def test_summarize_sub_agent_execution_traces(tmp_path):
    trace_path = tmp_path / "execution_trace.jsonl"

    execute_sub_agent_plan(
        create_plan(),
        tool_runner=lambda input_plan: '{"ok": true}',
        save_trace=True,
        trace_file=str(trace_path),
    )

    records = load_sub_agent_execution_traces(str(trace_path))
    summary = summarize_sub_agent_execution_traces(records)

    assert summary == {
        "total": 1,
        "successful": 1,
        "failed": 0,
        "by_sub_agent": {
            "retrieval_agent": 1,
        },
        "by_tool": {
            "search_thesis": 1,
        },
    }


def test_execute_sub_agent_call_cli(monkeypatch, capsys):
    def fake_execute_sub_agent_tool_call(**kwargs):
        return SubAgentExecutionResult(
            sub_agent_name=kwargs["sub_agent_name"],
            tool_name=kwargs["tool_name"],
            success=True,
            plan=create_plan(),
            result_text='{"ok": true}',
            duration_ms=1.2,
            trace_saved=False,
            trace_path=None,
        )

    monkeypatch.setattr(
        "app.cli.execute_sub_agent_tool_call",
        fake_execute_sub_agent_tool_call,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "execute-sub-agent-call",
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

    assert "SUB-AGENT EXECUTION" in output
    assert "SUB_AGENT: retrieval_agent" in output
    assert "TOOL: search_thesis" in output
    assert "SUCCESS: True" in output
    assert "TRACE_SAVED: False" in output
    assert 'RESULT: {"ok": true}' in output


def test_execute_sub_agent_call_cli_reports_error(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "execute-sub-agent-call",
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
    assert "SUB-AGENT EXECUTION ERROR:" in output


def test_analyze_sub_agent_executions_cli(
    monkeypatch,
    capsys,
    tmp_path,
):
    trace_path = tmp_path / "execution_trace.jsonl"

    execute_sub_agent_plan(
        create_plan(),
        tool_runner=lambda input_plan: '{"ok": true}',
        save_trace=True,
        trace_file=str(trace_path),
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "analyze-sub-agent-executions",
            "--file",
            str(trace_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "SUB-AGENT EXECUTION TRACE SUMMARY" in output
    assert "TOTAL: 1" in output
    assert "SUCCESSFUL: 1" in output
    assert "FAILED: 0" in output
