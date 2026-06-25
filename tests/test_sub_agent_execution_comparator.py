import json

import pytest

from app import cli
from app.sub_agent_execution_comparator import (
    compare_sub_agent_execution_records,
    parse_result_text,
)
from app.sub_agent_execution_trace import save_sub_agent_execution_trace
from app.sub_agent_executor import SubAgentExecutionResult
from app.sub_agent_plan import create_sub_agent_execution_plan


def create_result(
    success: bool = True,
    result_text: str = '{"evidence": "context", "sources": []}',
    duration_ms: float = 10.0,
    query: str = "system architecture",
) -> SubAgentExecutionResult:
    plan = create_sub_agent_execution_plan(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": query},
        plan_id="plan-1",
    )

    return SubAgentExecutionResult(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        success=success,
        plan=plan,
        result_text=result_text,
        duration_ms=duration_ms,
        trace_saved=False,
        trace_path=None,
    )


def create_record(**kwargs) -> dict:
    result = create_result(**kwargs)

    return {
        "created_at": "2026-06-25T00:00:00",
        "event_type": "sub_agent_tool_executed",
        "execution": result.to_dict(),
        "audit": {
            "sub_agent_name": result.sub_agent_name,
            "tool_name": result.tool_name,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "plan_id": result.plan.plan_id,
        },
    }


def test_parse_result_text_handles_invalid_json():
    parsed = parse_result_text("not json")

    assert parsed == {
        "json_valid": False,
        "keys": [],
        "error_type": None,
    }


def test_compare_sub_agent_execution_records_passes_when_stable():
    baseline = [create_record(duration_ms=10)]
    candidate = [create_record(duration_ms=12)]

    report = compare_sub_agent_execution_records(
        baseline_records=baseline,
        candidate_records=candidate,
    )

    assert report["passed"] is True
    assert report["baseline_count"] == 1
    assert report["candidate_count"] == 1
    assert report["added_count"] == 0
    assert report["removed_count"] == 0
    assert report["changed_count"] == 0
    assert report["duration_regression_count"] == 0
    assert report["stable_count"] == 1


def test_compare_sub_agent_execution_records_detects_added_record():
    baseline = [create_record()]
    candidate = [
        create_record(),
        create_record(query="training module"),
    ]

    report = compare_sub_agent_execution_records(
        baseline_records=baseline,
        candidate_records=candidate,
    )

    assert report["passed"] is False
    assert report["added_count"] == 1
    assert report["added"][0]["tool_arguments"] == {
        "query": "training module",
    }


def test_compare_sub_agent_execution_records_detects_removed_record():
    baseline = [
        create_record(),
        create_record(query="training module"),
    ]
    candidate = [create_record()]

    report = compare_sub_agent_execution_records(
        baseline_records=baseline,
        candidate_records=candidate,
    )

    assert report["passed"] is False
    assert report["removed_count"] == 1
    assert report["removed"][0]["tool_arguments"] == {
        "query": "training module",
    }


def test_compare_sub_agent_execution_records_detects_success_flip():
    baseline = [create_record(success=True)]
    candidate = [create_record(success=False)]

    report = compare_sub_agent_execution_records(
        baseline_records=baseline,
        candidate_records=candidate,
    )

    assert report["passed"] is False
    assert report["changed_count"] == 1
    assert report["changed"][0]["changes"]["success"] == {
        "baseline": True,
        "candidate": False,
    }


def test_compare_sub_agent_execution_records_detects_result_schema_change():
    baseline = [
        create_record(
            result_text='{"evidence": "context", "sources": []}',
        )
    ]
    candidate = [
        create_record(
            result_text='{"content": "context"}',
        )
    ]

    report = compare_sub_agent_execution_records(
        baseline_records=baseline,
        candidate_records=candidate,
    )

    assert report["passed"] is False
    assert report["changed"][0]["changes"]["result_keys"] == {
        "baseline": ["evidence", "sources"],
        "candidate": ["content"],
    }


def test_compare_sub_agent_execution_records_detects_error_type_change():
    baseline = [
        create_record(
            success=False,
            result_text=json.dumps(
                {
                    "success": False,
                    "error_type": "TimeoutError",
                }
            ),
        )
    ]
    candidate = [
        create_record(
            success=False,
            result_text=json.dumps(
                {
                    "success": False,
                    "error_type": "RuntimeError",
                }
            ),
        )
    ]

    report = compare_sub_agent_execution_records(
        baseline_records=baseline,
        candidate_records=candidate,
    )

    assert report["passed"] is False
    assert report["changed"][0]["changes"]["error_type"] == {
        "baseline": "TimeoutError",
        "candidate": "RuntimeError",
    }


def test_compare_sub_agent_execution_records_detects_duration_regression():
    baseline = [create_record(duration_ms=10)]
    candidate = [create_record(duration_ms=25)]

    report = compare_sub_agent_execution_records(
        baseline_records=baseline,
        candidate_records=candidate,
        max_duration_ratio=2.0,
    )

    assert report["passed"] is False
    assert report["duration_regression_count"] == 1
    assert report["duration_regressions"][0]["ratio"] == 2.5


def test_compare_sub_agent_execution_records_rejects_invalid_ratio():
    with pytest.raises(ValueError):
        compare_sub_agent_execution_records(
            baseline_records=[],
            candidate_records=[],
            max_duration_ratio=0,
        )


def test_compare_sub_agent_executions_cli(
    monkeypatch,
    capsys,
    tmp_path,
):
    baseline_path = tmp_path / "baseline.jsonl"
    candidate_path = tmp_path / "candidate.jsonl"

    save_sub_agent_execution_trace(
        create_result(duration_ms=10),
        file_path=str(baseline_path),
    )
    save_sub_agent_execution_trace(
        create_result(duration_ms=12),
        file_path=str(candidate_path),
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "compare-sub-agent-executions",
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(candidate_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "SUB-AGENT EXECUTION COMPARISON" in output
    assert "BASELINE COUNT: 1" in output
    assert "CANDIDATE COUNT: 1" in output
    assert "PASSED: True" in output


def test_compare_sub_agent_executions_cli_fails_on_regression(
    monkeypatch,
    capsys,
    tmp_path,
):
    baseline_path = tmp_path / "baseline.jsonl"
    candidate_path = tmp_path / "candidate.jsonl"

    save_sub_agent_execution_trace(
        create_result(success=True),
        file_path=str(baseline_path),
    )
    save_sub_agent_execution_trace(
        create_result(success=False),
        file_path=str(candidate_path),
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "compare-sub-agent-executions",
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(candidate_path),
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "PASSED: False" in output
    assert "CHANGED: 1" in output


def test_compare_sub_agent_executions_cli_allow_fail(
    monkeypatch,
    capsys,
    tmp_path,
):
    baseline_path = tmp_path / "baseline.jsonl"
    candidate_path = tmp_path / "candidate.jsonl"

    save_sub_agent_execution_trace(
        create_result(success=True),
        file_path=str(baseline_path),
    )
    save_sub_agent_execution_trace(
        create_result(success=False),
        file_path=str(candidate_path),
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "compare-sub-agent-executions",
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(candidate_path),
            "--allow-fail",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "PASSED: False" in output
    assert "CHANGED: 1" in output
