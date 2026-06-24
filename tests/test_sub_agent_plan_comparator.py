from app import cli
from app.sub_agent_plan import create_sub_agent_execution_plan
from app.sub_agent_plan_comparator import compare_sub_agent_plan_records
from app.sub_agent_plan_trace import (
    build_sub_agent_plan_trace_record,
    save_sub_agent_plan_trace,
)


def create_record(
    plan_id: str = "plan-1",
    query: str = "system architecture",
) -> dict:
    plan = create_sub_agent_execution_plan(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": query},
        plan_id=plan_id,
    )

    return build_sub_agent_plan_trace_record(plan)


def test_compare_sub_agent_plan_records_passes_when_stable():
    baseline = [create_record("baseline-plan")]
    candidate = [create_record("candidate-plan")]

    report = compare_sub_agent_plan_records(
        baseline_records=baseline,
        candidate_records=candidate,
    )

    assert report["passed"] is True
    assert report["baseline_count"] == 1
    assert report["candidate_count"] == 1
    assert report["added_count"] == 0
    assert report["removed_count"] == 0
    assert report["changed_count"] == 0
    assert report["stable_count"] == 1


def test_compare_sub_agent_plan_records_detects_added_plan():
    baseline = [create_record("plan-1")]
    candidate = [
        create_record("plan-1"),
        create_record("plan-2", query="training module"),
    ]

    report = compare_sub_agent_plan_records(
        baseline_records=baseline,
        candidate_records=candidate,
    )

    assert report["passed"] is False
    assert report["added_count"] == 1
    assert report["removed_count"] == 0
    assert report["changed_count"] == 0
    assert report["added"][0]["tool_arguments"] == {
        "query": "training module",
    }


def test_compare_sub_agent_plan_records_detects_removed_plan():
    baseline = [
        create_record("plan-1"),
        create_record("plan-2", query="training module"),
    ]
    candidate = [create_record("plan-1")]

    report = compare_sub_agent_plan_records(
        baseline_records=baseline,
        candidate_records=candidate,
    )

    assert report["passed"] is False
    assert report["added_count"] == 0
    assert report["removed_count"] == 1
    assert report["changed_count"] == 0
    assert report["removed"][0]["tool_arguments"] == {
        "query": "training module",
    }


def test_compare_sub_agent_plan_records_detects_changed_fields():
    baseline_record = create_record("plan-1")
    candidate_record = create_record("plan-2")
    candidate_record["plan"]["max_steps"] = 3
    candidate_record["audit"]["max_steps"] = 3

    report = compare_sub_agent_plan_records(
        baseline_records=[baseline_record],
        candidate_records=[candidate_record],
    )

    assert report["passed"] is False
    assert report["added_count"] == 0
    assert report["removed_count"] == 0
    assert report["changed_count"] == 1
    assert report["changed"][0]["changes"] == {
        "max_steps": {
            "baseline": 2,
            "candidate": 3,
        },
    }


def test_compare_sub_agent_plans_cli(
    monkeypatch,
    capsys,
    tmp_path,
):
    baseline_path = tmp_path / "baseline.jsonl"
    candidate_path = tmp_path / "candidate.jsonl"

    save_sub_agent_plan_trace(
        create_sub_agent_execution_plan(
            sub_agent_name="retrieval_agent",
            tool_name="search_thesis",
            tool_arguments={"query": "system architecture"},
            plan_id="baseline-plan",
        ),
        file_path=str(baseline_path),
    )
    save_sub_agent_plan_trace(
        create_sub_agent_execution_plan(
            sub_agent_name="retrieval_agent",
            tool_name="search_thesis",
            tool_arguments={"query": "system architecture"},
            plan_id="candidate-plan",
        ),
        file_path=str(candidate_path),
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "compare-sub-agent-plans",
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(candidate_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "SUB-AGENT PLAN COMPARISON" in output
    assert "BASELINE COUNT: 1" in output
    assert "CANDIDATE COUNT: 1" in output
    assert "PASSED: True" in output
