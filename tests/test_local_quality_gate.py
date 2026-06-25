import json
from pathlib import Path

import pytest

from app import cli
from app.local_quality_gate import (
    LocalQualityGateCheckResult,
    render_local_quality_gate_markdown,
    run_local_quality_gate,
    save_local_quality_gate_markdown,
    save_local_quality_gate_report,
)
from app.sub_agent_execution_trace import save_sub_agent_execution_trace
from app.sub_agent_executor import SubAgentExecutionResult
from app.sub_agent_plan import create_sub_agent_execution_plan


def create_check_result(
    name: str = "pytest",
    passed: bool = True,
) -> LocalQualityGateCheckResult:
    return LocalQualityGateCheckResult(
        name=name,
        passed=passed,
        summary=f"{name} {'passed' if passed else 'failed'}",
        details={},
    )


def fake_check_runner(command):
    return create_check_result()


def create_execution_result(
    success: bool = True,
    result_text: str = '{"evidence": "context", "sources": []}',
    duration_ms: float = 10.0,
) -> SubAgentExecutionResult:
    plan = create_sub_agent_execution_plan(
        sub_agent_name="retrieval_agent",
        tool_name="search_thesis",
        tool_arguments={"query": "system architecture"},
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


def test_run_local_quality_gate_with_pytest_check():
    report = run_local_quality_gate(
        check_runner=fake_check_runner,
    )

    assert report.passed is True
    assert len(report.checks) == 1
    assert report.checks[0].name == "pytest"


def test_run_local_quality_gate_fails_when_check_fails():
    def failing_runner(command):
        return create_check_result(passed=False)

    report = run_local_quality_gate(
        check_runner=failing_runner,
    )

    assert report.passed is False
    assert report.checks[0].passed is False


def test_run_local_quality_gate_requires_at_least_one_check():
    with pytest.raises(ValueError, match="at least one"):
        run_local_quality_gate(run_pytest=False)


def test_run_local_quality_gate_requires_trace_pair():
    with pytest.raises(ValueError, match="provided together"):
        run_local_quality_gate(
            run_pytest=False,
            sub_agent_execution_baseline="baseline.jsonl",
        )


def test_run_local_quality_gate_with_sub_agent_execution_comparison(
    tmp_path,
):
    baseline_path = tmp_path / "baseline.jsonl"
    candidate_path = tmp_path / "candidate.jsonl"

    save_sub_agent_execution_trace(
        create_execution_result(duration_ms=10),
        file_path=str(baseline_path),
    )
    save_sub_agent_execution_trace(
        create_execution_result(duration_ms=12),
        file_path=str(candidate_path),
    )

    report = run_local_quality_gate(
        run_pytest=False,
        sub_agent_execution_baseline=str(baseline_path),
        sub_agent_execution_candidate=str(candidate_path),
    )

    assert report.passed is True
    assert len(report.checks) == 1
    assert report.checks[0].name == "sub_agent_execution_comparison"


def test_run_local_quality_gate_with_sub_agent_execution_fixtures():
    fixture_dir = Path("tests/fixtures/sub_agent_execution")

    report = run_local_quality_gate(
        run_pytest=False,
        sub_agent_execution_baseline=str(fixture_dir / "baseline.jsonl"),
        sub_agent_execution_candidate=str(fixture_dir / "candidate.jsonl"),
    )

    assert report.passed is True
    assert len(report.checks) == 1
    assert report.checks[0].name == "sub_agent_execution_comparison"
    assert report.checks[0].details["stable_count"] == 1


def test_save_local_quality_gate_report(tmp_path):
    report = run_local_quality_gate(
        check_runner=fake_check_runner,
    )
    output_path = tmp_path / "reports" / "quality_gate.json"

    saved_path = save_local_quality_gate_report(
        report,
        str(output_path),
    )
    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert saved_path == output_path
    assert data["passed"] is True
    assert data["checks"][0]["name"] == "pytest"


def test_render_local_quality_gate_markdown():
    report = run_local_quality_gate(
        check_runner=fake_check_runner,
    )

    markdown = render_local_quality_gate_markdown(report)

    assert "# Local Quality Gate Report" in markdown
    assert "Status: **PASS**" in markdown
    assert "| `pytest` | `True` | pytest passed |" in markdown


def test_save_local_quality_gate_markdown(tmp_path):
    report = run_local_quality_gate(
        check_runner=fake_check_runner,
    )
    output_path = tmp_path / "reports" / "quality_gate.md"

    saved_path = save_local_quality_gate_markdown(
        report,
        str(output_path),
    )
    markdown = output_path.read_text(encoding="utf-8")

    assert saved_path == output_path
    assert "# Local Quality Gate Report" in markdown
    assert "pytest passed" in markdown


def test_run_local_quality_gate_fails_on_sub_agent_regression(
    tmp_path,
):
    baseline_path = tmp_path / "baseline.jsonl"
    candidate_path = tmp_path / "candidate.jsonl"

    save_sub_agent_execution_trace(
        create_execution_result(success=True),
        file_path=str(baseline_path),
    )
    save_sub_agent_execution_trace(
        create_execution_result(success=False),
        file_path=str(candidate_path),
    )

    report = run_local_quality_gate(
        run_pytest=False,
        sub_agent_execution_baseline=str(baseline_path),
        sub_agent_execution_candidate=str(candidate_path),
    )

    assert report.passed is False
    assert report.checks[0].details["changed_count"] == 1


def test_local_quality_gate_cli(monkeypatch, capsys):
    def fake_run_local_quality_gate(**kwargs):
        return type(
            "FakeReport",
            (),
            {
                "passed": True,
                "checks": [create_check_result()],
            },
        )()

    monkeypatch.setattr(
        "app.cli.run_local_quality_gate",
        fake_run_local_quality_gate,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "local-quality-gate",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "LOCAL QUALITY GATE" in output
    assert "PASSED: True" in output
    assert "CHECK: pytest" in output


def test_local_quality_gate_cli_writes_output(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "quality_gate.json"

    def fake_run_local_quality_gate(**kwargs):
        return type(
            "FakeReport",
            (),
            {
                "passed": True,
                "checks": [create_check_result()],
                "to_dict": lambda self: {
                    "passed": self.passed,
                    "checks": [
                        check.to_dict()
                        for check in self.checks
                    ],
                },
            },
        )()

    monkeypatch.setattr(
        "app.cli.run_local_quality_gate",
        fake_run_local_quality_gate,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "local-quality-gate",
            "--output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert "OUTPUT:" in output
    assert data["passed"] is True


def test_local_quality_gate_cli_writes_markdown_output(
    monkeypatch,
    capsys,
    tmp_path,
):
    output_path = tmp_path / "quality_gate.md"

    def fake_run_local_quality_gate(**kwargs):
        return type(
            "FakeReport",
            (),
            {
                "passed": True,
                "checks": [create_check_result()],
                "to_dict": lambda self: {
                    "passed": self.passed,
                    "checks": [
                        check.to_dict()
                        for check in self.checks
                    ],
                },
            },
        )()

    monkeypatch.setattr(
        "app.cli.run_local_quality_gate",
        fake_run_local_quality_gate,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "local-quality-gate",
            "--markdown-output",
            str(output_path),
        ],
    )

    cli.main()

    output = capsys.readouterr().out
    markdown = output_path.read_text(encoding="utf-8")

    assert "MARKDOWN OUTPUT:" in output
    assert "# Local Quality Gate Report" in markdown


def test_local_quality_gate_cli_fails(monkeypatch, capsys):
    def fake_run_local_quality_gate(**kwargs):
        return type(
            "FakeReport",
            (),
            {
                "passed": False,
                "checks": [create_check_result(passed=False)],
            },
        )()

    monkeypatch.setattr(
        "app.cli.run_local_quality_gate",
        fake_run_local_quality_gate,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "local-quality-gate",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "PASSED: False" in output


def test_local_quality_gate_cli_allow_fail(monkeypatch, capsys):
    def fake_run_local_quality_gate(**kwargs):
        return type(
            "FakeReport",
            (),
            {
                "passed": False,
                "checks": [create_check_result(passed=False)],
            },
        )()

    monkeypatch.setattr(
        "app.cli.run_local_quality_gate",
        fake_run_local_quality_gate,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "local-quality-gate",
            "--allow-fail",
        ],
    )

    cli.main()

    output = capsys.readouterr().out

    assert "PASSED: False" in output
