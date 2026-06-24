import json

import pytest

from app import cli
from app.sub_agent_plan import (
    SubAgentExecutionPlan,
    create_sub_agent_execution_plan,
    validate_sub_agent_plan_input,
)


def test_create_sub_agent_execution_plan():
    plan = create_sub_agent_execution_plan(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": "系统架构"},
        plan_id="plan-1",
    )

    assert isinstance(plan, SubAgentExecutionPlan)
    assert plan.plan_id == "plan-1"
    assert plan.sub_agent_name == "retrieval_agent"
    assert plan.tool_name == "search_thesis"
    assert plan.tool_arguments == {"query": "系统架构"}
    assert plan.expected_output_fields == ["evidence", "sources"]
    assert plan.max_steps == 2
    assert plan.status == "planned"


def test_create_sub_agent_execution_plan_generates_plan_id():
    plan = create_sub_agent_execution_plan(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": "系统架构"},
    )

    assert plan.plan_id


def test_create_sub_agent_execution_plan_rejects_non_dict_arguments():
    with pytest.raises(ValueError, match="tool_arguments 必须是 dict"):
        create_sub_agent_execution_plan(
            sub_agent_name="retrieval_agent",
            tool_name="search_thesis",
            tool_arguments="not a dict",
        )


def test_validate_sub_agent_plan_input_rejects_missing_field():
    with pytest.raises(ValueError, match="缺少输入字段"):
        validate_sub_agent_plan_input(
            sub_agent_name="retrieval_agent",
            tool_name="search_thesis",
            tool_arguments={},
        )


def test_create_sub_agent_execution_plan_rejects_disallowed_tool():
    with pytest.raises(ValueError, match="not allowed"):
        create_sub_agent_execution_plan(
            sub_agent_name="retrieval_agent",
            tool_name="evaluate_student_answer",
            tool_arguments={"query": "系统架构"},
        )


def test_sub_agent_execution_plan_to_dict():
    plan = create_sub_agent_execution_plan(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": "系统架构"},
        plan_id="plan-1",
    )

    data = plan.to_dict()

    assert data["plan_id"] == "plan-1"
    assert data["status"] == "planned"
    assert data["tool_arguments"] == {"query": "系统架构"}


def test_plan_sub_agent_call_cli(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "plan-sub-agent-call",
            "--sub-agent",
            "retrieval_agent",
            "--tool",
            "search_thesis",
            "--arguments",
            json.dumps({"query": "系统架构"}, ensure_ascii=False),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "SUB-AGENT EXECUTION PLAN" in output
    assert "SUB_AGENT: retrieval_agent" in output
    assert "TOOL: search_thesis" in output
    assert "EXPECTED_OUTPUT_FIELDS: ['evidence', 'sources']" in output
    assert "STATUS: planned" in output


def test_plan_sub_agent_call_cli_accepts_key_value_argument(
    monkeypatch,
    capsys,
):
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
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "SUB-AGENT EXECUTION PLAN" in output
    assert "SUB_AGENT: retrieval_agent" in output
    assert "TOOL: search_thesis" in output
    assert '"query": "系统架构"' in output


def test_plan_sub_agent_call_cli_requires_arguments(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "plan-sub-agent-call",
            "--sub-agent",
            "retrieval_agent",
            "--tool",
            "search_thesis",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "SUB-AGENT PLAN ERROR:" in output


def test_plan_sub_agent_call_cli_reports_invalid_arguments(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "plan-sub-agent-call",
            "--sub-agent",
            "retrieval_agent",
            "--tool",
            "search_thesis",
            "--arguments",
            "{invalid json}",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "SUB-AGENT PLAN ERROR:" in output
