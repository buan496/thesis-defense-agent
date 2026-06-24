from dataclasses import replace

import pytest

from app import cli
from app.sub_agent_specs import (
    SUB_AGENT_SPECS,
    SubAgentSpec,
    get_sub_agent_spec,
    list_sub_agent_specs,
    validate_sub_agent_spec,
)


def test_list_sub_agent_specs_returns_sorted_specs():
    specs = list_sub_agent_specs()
    names = [spec.name for spec in specs]

    assert names == sorted(names)
    assert "retrieval_agent" in names
    assert "answer_evaluation_agent" in names


def test_retrieval_agent_spec():
    spec = get_sub_agent_spec("retrieval_agent")

    assert isinstance(spec, SubAgentSpec)
    assert spec.role == "论文证据检索"
    assert spec.allowed_tools == ["search_thesis"]
    assert spec.input_fields == ["query"]
    assert spec.output_fields == ["evidence", "sources"]
    assert spec.max_steps == 2


def test_get_sub_agent_spec_rejects_unknown_spec():
    with pytest.raises(ValueError, match="未知 Sub-Agent"):
        get_sub_agent_spec("unknown_agent")


def test_validate_sub_agent_spec_rejects_empty_name():
    spec = replace(
        get_sub_agent_spec("retrieval_agent"),
        name=" ",
    )

    with pytest.raises(ValueError, match="name 不能为空"):
        validate_sub_agent_spec(spec)


def test_validate_sub_agent_spec_rejects_empty_allowed_tools():
    spec = replace(
        get_sub_agent_spec("retrieval_agent"),
        allowed_tools=[],
    )

    with pytest.raises(ValueError, match="至少允许一个工具"):
        validate_sub_agent_spec(spec)


def test_validate_sub_agent_spec_rejects_unknown_tool():
    spec = replace(
        get_sub_agent_spec("retrieval_agent"),
        allowed_tools=["unknown_tool"],
    )

    with pytest.raises(ValueError, match="引用了未知工具"):
        validate_sub_agent_spec(spec)


def test_validate_sub_agent_spec_rejects_invalid_max_steps():
    spec = replace(
        get_sub_agent_spec("retrieval_agent"),
        max_steps=0,
    )

    with pytest.raises(ValueError, match="max_steps 必须大于 0"):
        validate_sub_agent_spec(spec)


def test_every_sub_agent_tool_exists_in_registry():
    for spec in SUB_AGENT_SPECS.values():
        validate_sub_agent_spec(spec)


def test_sub_agent_spec_to_dict():
    data = get_sub_agent_spec("retrieval_agent").to_dict()

    assert data["name"] == "retrieval_agent"
    assert data["allowed_tools"] == ["search_thesis"]
    assert data["input_fields"] == ["query"]


def test_list_sub_agents_cli(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "list-sub-agents",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "SUB-AGENT SPECS" in output
    assert "COUNT:" in output
    assert "NAME: retrieval_agent" in output
    assert "ALLOWED_TOOLS: ['search_thesis']" in output
    assert "INPUT_FIELDS: ['query']" in output
    assert "OUTPUT_FIELDS: ['evidence', 'sources']" in output
