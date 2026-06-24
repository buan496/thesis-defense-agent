import pytest

from app import cli
from app.sub_agent_permissions import (
    SubAgentToolPermissionResult,
    can_sub_agent_use_tool,
    check_sub_agent_tool_permission,
    validate_sub_agent_tool_call,
)


def test_check_sub_agent_tool_permission_allows_declared_tool():
    result = check_sub_agent_tool_permission(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
    )

    assert isinstance(result, SubAgentToolPermissionResult)
    assert result.sub_agent_name == "retrieval_agent"
    assert result.tool_name == "search_thesis"
    assert result.allowed is True
    assert result.allowed_tools == ["search_thesis"]
    assert "allowed" in result.reason


def test_check_sub_agent_tool_permission_rejects_undeclared_tool():
    result = check_sub_agent_tool_permission(
        sub_agent_name="retrieval_agent",
        tool_name="evaluate_student_answer",
    )

    assert result.allowed is False
    assert result.allowed_tools == ["search_thesis"]
    assert "not allowed" in result.reason


def test_can_sub_agent_use_tool():
    assert can_sub_agent_use_tool(
        "retrieval_agent",
        "search_thesis",
    ) is True
    assert can_sub_agent_use_tool(
        "retrieval_agent",
        "generate_follow_up",
    ) is False


def test_validate_sub_agent_tool_call_allows_declared_tool():
    validate_sub_agent_tool_call(
        "answer_evaluation_agent",
        "evaluate_student_answer",
    )


def test_validate_sub_agent_tool_call_rejects_undeclared_tool():
    with pytest.raises(ValueError, match="not allowed"):
        validate_sub_agent_tool_call(
            "answer_evaluation_agent",
            "search_thesis",
        )


def test_check_sub_agent_tool_permission_rejects_unknown_sub_agent():
    with pytest.raises(ValueError, match="未知 Sub-Agent"):
        check_sub_agent_tool_permission(
            sub_agent_name="unknown_agent",
            tool_name="search_thesis",
        )


def test_permission_result_to_dict():
    result = check_sub_agent_tool_permission(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
    )

    data = result.to_dict()

    assert data["sub_agent_name"] == "retrieval_agent"
    assert data["tool_name"] == "search_thesis"
    assert data["allowed"] is True


def test_check_sub_agent_tool_cli_allows_tool(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "check-sub-agent-tool",
            "--sub-agent",
            "retrieval_agent",
            "--tool",
            "search_thesis",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "SUB-AGENT TOOL CHECK" in output
    assert "SUB_AGENT: retrieval_agent" in output
    assert "TOOL: search_thesis" in output
    assert "ALLOWED: True" in output


def test_check_sub_agent_tool_cli_reports_unknown_sub_agent(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "check-sub-agent-tool",
            "--sub-agent",
            "unknown_agent",
            "--tool",
            "search_thesis",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "SUB-AGENT TOOL CHECK ERROR:" in output
