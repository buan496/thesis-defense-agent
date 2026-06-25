import subprocess
from dataclasses import asdict, dataclass

from app.sub_agent_execution_comparator import (
    compare_sub_agent_execution_records,
)
from app.sub_agent_execution_trace import load_sub_agent_execution_traces


@dataclass(frozen=True)
class LocalQualityGateCheckResult:
    name: str
    passed: bool
    summary: str
    details: dict

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LocalQualityGateReport:
    passed: bool
    checks: list[LocalQualityGateCheckResult]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "checks": [
                check.to_dict()
                for check in self.checks
            ],
        }


def run_pytest_check(
    command: list[str] | None = None,
) -> LocalQualityGateCheckResult:
    check_command = command or ["uv", "run", "pytest", "-q"]
    completed = subprocess.run(
        check_command,
        capture_output=True,
        text=True,
    )

    return LocalQualityGateCheckResult(
        name="pytest",
        passed=completed.returncode == 0,
        summary=(
            "pytest passed"
            if completed.returncode == 0
            else "pytest failed"
        ),
        details={
            "command": check_command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
    )


def run_sub_agent_execution_comparison_check(
    baseline_path: str,
    candidate_path: str,
    max_duration_ratio: float = 2.0,
) -> LocalQualityGateCheckResult:
    baseline_records = load_sub_agent_execution_traces(baseline_path)
    candidate_records = load_sub_agent_execution_traces(candidate_path)
    report = compare_sub_agent_execution_records(
        baseline_records=baseline_records,
        candidate_records=candidate_records,
        max_duration_ratio=max_duration_ratio,
    )

    return LocalQualityGateCheckResult(
        name="sub_agent_execution_comparison",
        passed=report["passed"],
        summary=(
            "Sub-Agent execution comparison passed"
            if report["passed"]
            else "Sub-Agent execution comparison failed"
        ),
        details=report,
    )


def run_local_quality_gate(
    run_pytest: bool = True,
    sub_agent_execution_baseline: str | None = None,
    sub_agent_execution_candidate: str | None = None,
    max_duration_ratio: float = 2.0,
    pytest_command: list[str] | None = None,
    check_runner=None,
) -> LocalQualityGateReport:
    checks = []
    runner = check_runner or run_pytest_check

    if run_pytest:
        checks.append(
            runner(pytest_command)
        )

    has_sub_agent_baseline = sub_agent_execution_baseline is not None
    has_sub_agent_candidate = sub_agent_execution_candidate is not None

    if has_sub_agent_baseline != has_sub_agent_candidate:
        raise ValueError(
            "sub-agent execution baseline and candidate must be provided together"
        )

    if has_sub_agent_baseline and has_sub_agent_candidate:
        checks.append(
            run_sub_agent_execution_comparison_check(
                baseline_path=sub_agent_execution_baseline,
                candidate_path=sub_agent_execution_candidate,
                max_duration_ratio=max_duration_ratio,
            )
        )

    if not checks:
        raise ValueError("at least one quality gate check must be enabled")

    return LocalQualityGateReport(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
